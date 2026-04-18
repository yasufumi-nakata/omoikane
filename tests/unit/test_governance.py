from __future__ import annotations

import unittest

from omoikane.governance import AmendmentService, AmendmentSignatures, OversightService
from omoikane.agentic.trust import TrustService


class AmendmentServiceTests(unittest.TestCase):
    def test_t_core_always_freezes(self) -> None:
        service = AmendmentService()
        proposal = service.propose(
            tier="T-Core",
            target_clauses=["ethics.A1"],
            draft_text_ref="meta/decision-log/core.md",
            rationale="core clauses remain outside runtime apply",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="unanimous",
                self_consent=True,
                guardian_attested=True,
                human_reviewers=3,
                design_architect_attested=True,
            ),
        )

        updated, decision = service.decide(proposal, continuity_event_ref="entry-1")

        self.assertEqual("frozen", updated.status)
        self.assertFalse(decision["allow_apply"])
        self.assertEqual("none", decision["applied_stage"])

    def test_t_kernel_requires_two_human_reviewers(self) -> None:
        service = AmendmentService()
        proposal = service.propose(
            tier="T-Kernel",
            target_clauses=["continuity.profile"],
            draft_text_ref="meta/decision-log/kernel.md",
            rationale="kernel changes require external review",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="unanimous",
                self_consent=True,
                guardian_attested=True,
                human_reviewers=1,
                design_architect_attested=True,
            ),
        )

        updated, decision = service.decide(proposal, continuity_event_ref="entry-2")

        self.assertEqual("pending-human-review", updated.status)
        self.assertFalse(decision["allow_apply"])
        self.assertTrue(any("2 名以上" in reason for reason in decision["reasons"]))

    def test_t_operational_accepts_majority_plus_guardian(self) -> None:
        service = AmendmentService()
        proposal = service.propose(
            tier="T-Operational",
            target_clauses=["council.timeout"],
            draft_text_ref="meta/decision-log/operational.md",
            rationale="operational rules can progress via guarded rollout",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="majority",
                guardian_attested=True,
                design_architect_attested=True,
            ),
        )

        updated, decision = service.decide(proposal, continuity_event_ref="entry-3")

        self.assertEqual("applied", updated.status)
        self.assertTrue(decision["allow_apply"])
        self.assertEqual("5pct", decision["applied_stage"])


class OversightServiceTests(unittest.TestCase):
    def test_veto_event_satisfies_quorum_after_one_attestation(self) -> None:
        service = OversightService()

        event = service.record(
            guardian_role="integrity",
            category="veto",
            payload_ref="entry-1",
            escalation_path=["human-reviewer-pool-A"],
        )
        updated = service.attest(event["event_id"], reviewer_id="reviewer-1")

        self.assertEqual(1, updated["human_attestation"]["required_quorum"])
        self.assertEqual(1, updated["human_attestation"]["received_quorum"])
        self.assertEqual("satisfied", updated["human_attestation"]["status"])

    def test_pin_breach_unpins_guardian_role(self) -> None:
        trust = TrustService()
        trust.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        service = OversightService(trust_service=trust)

        event = service.record(
            guardian_role="integrity",
            category="pin-renewal",
            payload_ref="entry-2",
            escalation_path=["human-reviewer-pool-A", "external-ethics-board"],
        )
        breached = service.breach(event["event_id"])
        snapshot = trust.snapshot("integrity-guardian")

        self.assertEqual("breached", breached["human_attestation"]["status"])
        self.assertTrue(breached["pin_breach_propagated"])
        self.assertFalse(snapshot["pinned_by_human"])
        self.assertFalse(snapshot["eligibility"]["guardian_role"])


if __name__ == "__main__":
    unittest.main()
