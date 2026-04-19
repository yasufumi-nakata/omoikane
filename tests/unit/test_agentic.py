from __future__ import annotations

import unittest

from omoikane.agentic.cognitive_audit import CognitiveAuditService
from omoikane.agentic.council import Council, CouncilMember, CouncilVote, DistributedCouncilVote
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

    def test_cross_self_scope_requests_federation(self) -> None:
        council = Council()

        proposal = council.propose(
            "Shared reality merge",
            "federation review",
            "複数 identity をまたぐため federation に送る",
            target_identity_ids=["identity://a", "identity://b"],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-cross-self")

        self.assertEqual("cross-self", topology.scope)
        self.assertTrue(topology.federation_request.convened)
        self.assertEqual("external-pending", topology.federation_request.status)
        self.assertEqual([], topology.heritage_request.clauses)

    def test_interpretive_scope_requests_heritage(self) -> None:
        council = Council()

        proposal = council.propose(
            "Interpret ethics axiom",
            "heritage ruling",
            "規約解釈を heritage に送る",
            target_identity_ids=["identity://a"],
            referenced_clauses=["ethics_axiom.A2"],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-interpretive")

        self.assertEqual("interpretive", topology.scope)
        self.assertTrue(topology.heritage_request.convened)
        self.assertEqual("external-pending", topology.heritage_request.status)
        self.assertEqual([], topology.federation_request.participants)

    def test_ambiguous_scope_blocks_external_requests_until_reclassified(self) -> None:
        council = Council()

        proposal = council.propose(
            "Cross-self ethics rewrite",
            "block pending reclassification",
            "cross-self と interpretive が競合する",
            target_identity_ids=["identity://a", "identity://b"],
            referenced_clauses=["governance.freeze"],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-ambiguous")

        self.assertEqual("ambiguous", topology.scope)
        self.assertFalse(topology.federation_request.convened)
        self.assertFalse(topology.heritage_request.convened)
        self.assertEqual("none", topology.federation_request.status)
        self.assertEqual("none", topology.heritage_request.status)

    def test_federation_resolution_promotes_advisory_cross_self_review(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        proposal = council.propose(
            "Shared reality merge",
            "merge",
            "cross-self federation returned result",
            target_identity_ids=["identity://a", "identity://b"],
        )
        local_decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "advisory approve"),
                CouncilVote("committee", "approve", "consent bundle okay"),
                CouncilVote("archivist", "reject", "monitor drift"),
            ],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-cross-self")
        resolution = council.resolve_federation_review(
            topology,
            local_decision=local_decision,
            votes=[
                DistributedCouncilVote("identity://a", "approve", "self approves"),
                DistributedCouncilVote("identity://b", "approve", "peer approves"),
                DistributedCouncilVote("guardian://neutral-federation", "approve", "guardian approves"),
            ],
        )

        self.assertEqual("federation", resolution.council_tier)
        self.assertEqual("advisory", resolution.local_binding_status)
        self.assertEqual("binding-approved", resolution.final_outcome)
        self.assertEqual("weighted-majority", resolution.decision_mode)
        self.assertEqual(3, resolution.vote_summary.quorum)

    def test_heritage_resolution_allows_ethics_committee_single_veto(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        proposal = council.propose(
            "Interpret ethics axiom",
            "rewrite",
            "heritage returned result",
            target_identity_ids=["identity://a"],
            referenced_clauses=["ethics_axiom.A2"],
        )
        local_decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "local wording acceptable"),
                CouncilVote("committee", "approve", "local review okay"),
                CouncilVote("archivist", "approve", "continuity okay"),
            ],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-interpretive")
        resolution = council.resolve_heritage_review(
            topology,
            local_decision=local_decision,
            votes=[
                DistributedCouncilVote("heritage://culture-a", "approve", "culture a okay"),
                DistributedCouncilVote("heritage://culture-b", "approve", "culture b okay"),
                DistributedCouncilVote("heritage://legal-advisor", "approve", "law okay"),
                DistributedCouncilVote("heritage://ethics-committee", "veto", "ethics blocks"),
            ],
        )

        self.assertEqual("heritage", resolution.council_tier)
        self.assertEqual("blocked", resolution.local_binding_status)
        self.assertEqual("binding-rejected", resolution.final_outcome)
        self.assertEqual("ethics-veto", resolution.decision_mode)
        self.assertEqual("heritage-overrides-local", resolution.conflict_resolution)
        self.assertTrue(resolution.vote_summary.veto_triggered)

    def test_distributed_conflict_escalates_to_human_governance(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        federation_proposal = council.propose(
            "Shared reality merge",
            "merge",
            "cross-self federation returned result",
            target_identity_ids=["identity://a", "identity://b"],
        )
        federation_local = council.deliberate(
            federation_proposal,
            [
                CouncilVote("architect", "approve", "advisory approve"),
                CouncilVote("committee", "approve", "consent okay"),
                CouncilVote("archivist", "reject", "monitor drift"),
            ],
        )
        federation_topology = council.route_topology(
            federation_proposal,
            local_session_ref="local-session-cross-self",
        )
        federation_resolution = council.resolve_federation_review(
            federation_topology,
            local_decision=federation_local,
            votes=[
                DistributedCouncilVote("identity://a", "approve", "self approves"),
                DistributedCouncilVote("identity://b", "approve", "peer approves"),
                DistributedCouncilVote("guardian://neutral-federation", "approve", "guardian approves"),
            ],
        )

        heritage_proposal = council.propose(
            "Interpret identity axiom",
            "rewrite",
            "heritage returned result",
            target_identity_ids=["identity://a"],
            referenced_clauses=["identity_axiom.A2"],
        )
        heritage_local = council.deliberate(
            heritage_proposal,
            [
                CouncilVote("architect", "approve", "local wording acceptable"),
                CouncilVote("committee", "approve", "local review okay"),
                CouncilVote("archivist", "approve", "continuity okay"),
            ],
        )
        heritage_topology = council.route_topology(
            heritage_proposal,
            local_session_ref="local-session-interpretive",
        )
        heritage_resolution = council.resolve_heritage_review(
            heritage_topology,
            local_decision=heritage_local,
            votes=[
                DistributedCouncilVote("heritage://culture-a", "approve", "culture a okay"),
                DistributedCouncilVote("heritage://culture-b", "approve", "culture b okay"),
                DistributedCouncilVote("heritage://legal-advisor", "approve", "law okay"),
                DistributedCouncilVote("heritage://ethics-committee", "veto", "ethics blocks"),
            ],
        )

        conflict_local = council.deliberate(
            council.propose(
                "Composite conflict",
                "escalate",
                "federation と heritage の衝突",
                target_identity_ids=["identity://a"],
            ),
            [
                CouncilVote("architect", "approve", "local escalation candidate"),
                CouncilVote("committee", "approve", "external結果待ち"),
                CouncilVote("archivist", "approve", "human判断が必要"),
            ],
        )
        conflict = council.reconcile_distributed_conflict(
            "proposal-conflict-001",
            local_decision=conflict_local,
            federation_resolution=federation_resolution,
            heritage_resolution=heritage_resolution,
        )

        self.assertEqual("human-governance", conflict.council_tier)
        self.assertEqual("escalate-human-governance", conflict.final_outcome)
        self.assertEqual("conflict-escalation", conflict.decision_mode)
        self.assertEqual("escalated-to-human-governance", conflict.conflict_resolution)
        self.assertEqual(2, len(conflict.external_resolution_refs))


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


class CognitiveAuditTests(unittest.TestCase):
    def test_audit_record_binds_cross_layer_refs(self) -> None:
        service = CognitiveAuditService()

        record = service.create_record(
            identity_id="identity://audit-demo",
            qualia_tick={
                "tick_id": 3,
                "summary": "identity drift review",
                "attention_target": "identity-drift-review",
                "self_awareness": 0.88,
                "lucidity": 0.61,
                "valence": -0.19,
                "arousal": 0.67,
                "clarity": 0.58,
            },
            self_model_observation={
                "abrupt_change": True,
                "divergence": 0.41,
                "threshold": 0.35,
                "snapshot": {
                    "identity_id": "identity://audit-demo",
                    "values": ["continuity-first", "guardian-visible", "auditability"],
                    "goals": ["stabilize-review-loop", "preserve-identity-anchor"],
                    "traits": {"agency": 0.82, "stability": 0.41, "vigilance": 0.87},
                },
            },
            metacognition_report={
                "report_id": "metacognition-report-0123456789ab",
                "source_tick": {
                    "tick_id": 3,
                    "identity_id": "identity://audit-demo",
                    "attention_target": "identity-drift-review",
                    "affect_guard": "observe",
                    "continuity_pressure": 0.81,
                },
                "reflection_mode": "guardian-review",
                "escalation_target": "guardian-review",
                "risk_posture": "guarded",
                "degraded": False,
                "continuity_guard": {"guard_aligned": True},
                "coherence_score": 0.67,
            },
            qualia_checkpoint_ref="53d6e4b6f3a7f252b9f7dfdcdd4d734ae0f6dca6b25a6c67d75e55b0dd6fdb7b",
        )

        validation = service.validate_record(record)

        self.assertTrue(validation["ok"])
        self.assertEqual("guardian-review", record["recommended_action"])
        self.assertEqual("standard", record["council_brief"]["session_mode"])
        self.assertTrue(record["continuity_alignment"]["identity_matches"])
        self.assertIn("abrupt-change", record["audit_triggers"])
        self.assertIn("observe-guard", record["audit_triggers"])

    def test_resolution_maps_council_approval_to_guardian_review(self) -> None:
        service = CognitiveAuditService()
        record = service.create_record(
            identity_id="identity://audit-demo",
            qualia_tick={
                "tick_id": 3,
                "summary": "identity drift review",
                "attention_target": "identity-drift-review",
                "self_awareness": 0.88,
                "lucidity": 0.61,
                "valence": -0.19,
                "arousal": 0.67,
                "clarity": 0.58,
            },
            self_model_observation={
                "abrupt_change": True,
                "divergence": 0.41,
                "threshold": 0.35,
                "snapshot": {
                    "identity_id": "identity://audit-demo",
                    "values": ["continuity-first"],
                    "goals": ["stabilize-review-loop"],
                    "traits": {"vigilance": 0.87},
                },
            },
            metacognition_report={
                "report_id": "metacognition-report-0123456789ab",
                "source_tick": {
                    "tick_id": 3,
                    "identity_id": "identity://audit-demo",
                    "attention_target": "identity-drift-review",
                    "affect_guard": "observe",
                    "continuity_pressure": 0.81,
                },
                "reflection_mode": "guardian-review",
                "escalation_target": "guardian-review",
                "risk_posture": "guarded",
                "degraded": False,
                "continuity_guard": {"guard_aligned": True},
                "coherence_score": 0.67,
            },
            qualia_checkpoint_ref="53d6e4b6f3a7f252b9f7dfdcdd4d734ae0f6dca6b25a6c67d75e55b0dd6fdb7b",
        )

        resolution = service.resolve(
            record,
            council_proposal_ref="proposal-0123456789ab",
            council_decision={"outcome": "approved", "decision_mode": "weighted-majority"},
        )
        validation = service.validate_resolution(resolution)

        self.assertTrue(validation["ok"])
        self.assertEqual("open-guardian-review", resolution["follow_up_action"])
        self.assertTrue(resolution["continuity_alignment"]["recommended_action_matches_outcome"])


if __name__ == "__main__":
    unittest.main()
