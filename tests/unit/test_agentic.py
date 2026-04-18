from __future__ import annotations

import unittest

from omoikane.agentic.council import Council, CouncilMember, CouncilVote
from omoikane.agentic.task_graph import TaskGraphService
from omoikane.agentic.trust import TrustService


class CouncilTests(unittest.TestCase):
    def test_guardian_veto_overrides_majority(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("guardian", "guardian", 0.99, is_guardian=True))

        proposal = council.propose("Patch", "change", "test rationale")
        decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "looks good"),
                CouncilVote("committee", "approve", "acceptable"),
                CouncilVote("guardian", "veto", "immutable boundary"),
            ],
        )

        self.assertEqual("vetoed", decision.outcome)
        self.assertEqual("guardian-veto", decision.timeout_status.fallback_applied)

    def test_soft_timeout_falls_back_to_weighted_majority(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        proposal = council.propose("Patch", "change", "test rationale", session_mode="standard")
        decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "docs ready"),
                CouncilVote("committee", "approve", "ethics okay"),
                CouncilVote("archivist", "reject", "log detail不足"),
            ],
            elapsed_ms=50_000,
            rounds_completed=3,
        )

        self.assertEqual("approved", decision.outcome)
        self.assertEqual("timeout-fallback", decision.decision_mode)
        self.assertEqual("soft-timeout", decision.timeout_status.status)
        self.assertEqual("weighted-majority", decision.timeout_status.fallback_applied)

    def test_hard_timeout_defers_expedited_session(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("guardian", "guardian", 0.99, is_guardian=True))

        proposal = council.propose("Emergency", "stabilize", "test rationale", session_mode="expedited")
        decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "containment first"),
                CouncilVote("guardian", "approve", "follow-up review required"),
            ],
            elapsed_ms=1_500,
            rounds_completed=2,
        )

        self.assertEqual("deferred", decision.outcome)
        self.assertEqual("expedited", decision.decision_mode)
        self.assertEqual("hard-timeout", decision.timeout_status.status)
        self.assertEqual("schedule-standard-session", decision.timeout_status.follow_up_action)


class TaskGraphServiceTests(unittest.TestCase):
    def test_build_graph_returns_bounded_reference_shape(self) -> None:
        service = TaskGraphService()

        graph = service.build_graph(
            intent="runtime と spec を同期する",
            required_roles=["schema-builder", "eval-builder", "doc-sync-builder"],
        )
        validation = service.validate_graph(graph)

        self.assertTrue(validation["ok"])
        self.assertEqual(5, validation["node_count"])
        self.assertEqual(4, validation["edge_count"])
        self.assertEqual(3, validation["max_depth"])
        self.assertEqual(3, validation["root_count"])

    def test_build_graph_rejects_parallelism_over_policy(self) -> None:
        service = TaskGraphService()

        with self.assertRaises(ValueError):
            service.build_graph(
                intent="4 roles を同時に走らせる",
                required_roles=["schema-builder", "eval-builder", "doc-sync-builder", "codex-builder"],
            )

    def test_dispatch_graph_marks_root_nodes_dispatched(self) -> None:
        service = TaskGraphService()
        graph = service.build_graph(
            intent="runtime と docs を同期する",
            required_roles=["schema-builder", "eval-builder", "doc-sync-builder"],
        )

        dispatch = service.dispatch_graph(
            graph_id=graph["graph_id"],
            nodes=graph["nodes"],
            complexity_policy=graph["complexity_policy"],
        )

        self.assertEqual(3, dispatch["dispatched_count"])
        self.assertEqual(["node-1", "node-2", "node-3"], dispatch["ready_node_ids"])
        self.assertEqual(
            ["dispatched", "dispatched", "dispatched"],
            [graph["nodes"][index]["status"] for index in range(3)],
        )

    def test_synthesize_results_respects_result_ref_limit(self) -> None:
        service = TaskGraphService()
        policy = service.policy()

        synthesis = service.synthesize_results(
            graph_id="graph-demo",
            result_refs=["artifact://schema", "artifact://eval", "artifact://docs"],
            complexity_policy=policy,
        )

        self.assertEqual(3, synthesis["accepted_result_count"])
        with self.assertRaises(ValueError):
            service.synthesize_results(
                graph_id="graph-demo",
                result_refs=[
                    "artifact://1",
                    "artifact://2",
                    "artifact://3",
                    "artifact://4",
                    "artifact://5",
                    "artifact://6",
                ],
                complexity_policy=policy,
            )


class TrustServiceTests(unittest.TestCase):
    def test_positive_event_updates_score_and_thresholds(self) -> None:
        service = TrustService()
        service.register_agent(
            "design-architect",
            initial_score=0.58,
            per_domain={"council_deliberation": 0.58},
        )

        event = service.record_event(
            "design-architect",
            event_type="council_quality_positive",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="Council",
            rationale="consistent review quality",
        )
        snapshot = service.snapshot("design-architect")

        self.assertEqual(0.04, event["applied_delta"])
        self.assertEqual(0.62, snapshot["global_score"])
        self.assertEqual(0.62, snapshot["per_domain"]["council_deliberation"])
        self.assertTrue(snapshot["eligibility"]["count_for_weighted_vote"])

    def test_human_pin_freezes_automatic_delta(self) -> None:
        service = TrustService()
        service.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )

        event = service.record_event(
            "integrity-guardian",
            event_type="human_feedback_bad",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="yasufumi",
            rationale="manual review pending",
        )
        snapshot = service.snapshot("integrity-guardian")

        self.assertFalse(event["applied"])
        self.assertEqual(0.0, event["applied_delta"])
        self.assertEqual(0.99, snapshot["global_score"])
        self.assertTrue(snapshot["eligibility"]["guardian_role"])
        self.assertEqual("guardian bootstrap", snapshot["pinned_reason"])


if __name__ == "__main__":
    unittest.main()
