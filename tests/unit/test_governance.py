from __future__ import annotations

import unittest

from omoikane.governance import AmendmentService, AmendmentSignatures


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


if __name__ == "__main__":
    unittest.main()
