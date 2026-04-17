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


if __name__ == "__main__":
    unittest.main()

