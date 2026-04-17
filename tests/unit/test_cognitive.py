from __future__ import annotations

import unittest

from omoikane.cognitive import (
    BackendUnavailableError,
    CognitiveProfile,
    NarrativeReasoningBackend,
    ReasoningService,
    SymbolicReasoningBackend,
)


class ReasoningServiceTests(unittest.TestCase):
    def test_failover_uses_fallback_backend(self) -> None:
        service = ReasoningService(
            profile=CognitiveProfile(primary="symbolic_v1", fallback=["narrative_v1"]),
            backends=[
                SymbolicReasoningBackend("symbolic_v1", healthy=False),
                NarrativeReasoningBackend("narrative_v1"),
            ],
        )

        result = service.run(
            query="安全に継続できるか",
            beliefs=["continuity-first", "append-only-ledger"],
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("narrative_v1", result["selected_backend"])
        self.assertEqual(["symbolic_v1", "narrative_v1"], result["attempted_backends"])

    def test_failover_raises_when_all_backends_unavailable(self) -> None:
        service = ReasoningService(
            profile=CognitiveProfile(primary="symbolic_v1", fallback=["narrative_v1"]),
            backends=[
                SymbolicReasoningBackend("symbolic_v1", healthy=False),
                NarrativeReasoningBackend("narrative_v1", healthy=False),
            ],
        )

        with self.assertRaises(BackendUnavailableError):
            service.run(
                query="安全に継続できるか",
                beliefs=["continuity-first"],
            )


if __name__ == "__main__":
    unittest.main()
