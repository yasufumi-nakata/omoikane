from __future__ import annotations

import unittest

from omoikane.agentic.council import Council, CouncilMember, CouncilVote


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


if __name__ == "__main__":
    unittest.main()
