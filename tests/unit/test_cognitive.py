from __future__ import annotations

import unittest

from omoikane.cognitive import (
    AffectCue,
    AffectRequest,
    AffectService,
    BackendUnavailableError,
    CognitiveProfile,
    HomeostaticAffectBackend,
    NarrativeReasoningBackend,
    ReasoningService,
    StabilityGuardAffectBackend,
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


class AffectServiceTests(unittest.TestCase):
    def test_failover_smooths_transition_without_unconsented_dampening(self) -> None:
        service = AffectService(
            profile=CognitiveProfile(primary="homeostatic_v1", fallback=["stability_guard_v1"]),
            backends=[
                HomeostaticAffectBackend("homeostatic_v1", healthy=False),
                StabilityGuardAffectBackend("stability_guard_v1"),
            ],
        )
        healthy_service = AffectService(
            profile=CognitiveProfile(primary="homeostatic_v1", fallback=["stability_guard_v1"]),
            backends=[
                HomeostaticAffectBackend("homeostatic_v1"),
                StabilityGuardAffectBackend("stability_guard_v1"),
            ],
        )
        baseline = healthy_service.run(
            AffectRequest(
                tick_id=0,
                summary="baseline",
                valence=0.1,
                arousal=0.34,
                clarity=0.92,
                self_awareness=0.7,
                lucidity=0.95,
                memory_cues=[AffectCue("continuity-first", 0.08, -0.05)],
            )
        )["state"]

        result = service.run(
            AffectRequest(
                tick_id=1,
                summary="failover 直後の緊張",
                valence=-0.36,
                arousal=0.81,
                clarity=0.74,
                self_awareness=0.73,
                lucidity=0.88,
                memory_cues=[
                    AffectCue("continuity-first", 0.08, -0.05),
                    AffectCue("fallback-risk", -0.09, 0.11),
                ],
                allow_artificial_dampening=False,
            ),
            previous_state=baseline,
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("stability_guard_v1", result["selected_backend"])
        self.assertTrue(result["transition"]["smoothed"])
        self.assertFalse(result["transition"]["dampening_applied"])
        self.assertTrue(result["transition"]["consent_preserved"])
        self.assertEqual("observe", result["state"]["recommended_guard"])

    def test_consented_dampening_can_apply_in_fallback(self) -> None:
        service = AffectService(
            profile=CognitiveProfile(primary="homeostatic_v1", fallback=["stability_guard_v1"]),
            backends=[
                HomeostaticAffectBackend("homeostatic_v1", healthy=False),
                StabilityGuardAffectBackend("stability_guard_v1"),
            ],
        )

        result = service.run(
            AffectRequest(
                tick_id=2,
                summary="consented stabilization",
                valence=-0.44,
                arousal=0.84,
                clarity=0.7,
                self_awareness=0.68,
                lucidity=0.83,
                memory_cues=[AffectCue("guardian-observe", 0.03, -0.04)],
                allow_artificial_dampening=True,
            )
        )

        self.assertTrue(result["transition"]["dampening_applied"])
        self.assertTrue(result["transition"]["consent_preserved"])
        self.assertLess(result["state"]["arousal"], 0.84)


if __name__ == "__main__":
    unittest.main()
