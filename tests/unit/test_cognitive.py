from __future__ import annotations

import unittest

from omoikane.cognitive import (
    AttentionCue,
    AttentionRequest,
    AttentionService,
    AffectCue,
    AffectRequest,
    AffectService,
    BackendUnavailableError,
    CognitiveProfile,
    ContinuityAnchorAttentionBackend,
    ContinuitySceneGuardBackend,
    ContinuityMirrorBackend,
    ContinuityPhraseLanguageBackend,
    CounterfactualSceneBackend,
    HomeostaticAffectBackend,
    ImaginationCue,
    ImaginationRequest,
    ImaginationService,
    LanguageCue,
    LanguageRequest,
    LanguageService,
    MetacognitionCue,
    MetacognitionRequest,
    MetacognitionService,
    NarrativeReasoningBackend,
    ReasoningRequest,
    ReflectiveLoopBackend,
    ReasoningService,
    SalienceRoutingAttentionBackend,
    SemanticFrameLanguageBackend,
    StabilityGuardAffectBackend,
    SymbolicReasoningBackend,
    GuardianBiasVolitionBackend,
    UtilityPolicyVolitionBackend,
    VolitionCandidate,
    VolitionCue,
    VolitionRequest,
    VolitionService,
)


class ReasoningServiceTests(unittest.TestCase):
    def test_structured_request_yields_valid_trace_and_shift(self) -> None:
        service = ReasoningService(
            profile=CognitiveProfile(primary="symbolic_v1", fallback=["narrative_v1"]),
            backends=[
                SymbolicReasoningBackend("symbolic_v1"),
                NarrativeReasoningBackend("narrative_v1"),
            ],
        )

        result = service.run(
            ReasoningRequest(
                tick_id=0,
                summary="nominal review",
                query="安全に継続できるか",
                beliefs=["continuity-first", "append-only-ledger"],
            )
        )

        trace_validation = service.validate_trace(dict(result["trace"]))
        shift_validation = service.validate_shift(dict(result["shift"]))

        self.assertFalse(result["degraded"])
        self.assertTrue(trace_validation["ok"])
        self.assertTrue(shift_validation["ok"])
        self.assertTrue(shift_validation["safe_summary_only"])
        self.assertEqual("symbolic_v1", result["trace"]["backend_id"])

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
        self.assertTrue(result["shift"]["safe_summary_only"])
        self.assertEqual("symbolic_v1", result["shift"]["previous_backend_id"])

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


class AttentionServiceTests(unittest.TestCase):
    def test_failover_routes_to_guardian_review_when_affect_guard_escalates(self) -> None:
        service = AttentionService(
            profile=CognitiveProfile(primary="salience_router_v1", fallback=["continuity_anchor_v1"]),
            backends=[
                SalienceRoutingAttentionBackend("salience_router_v1", healthy=False),
                ContinuityAnchorAttentionBackend("continuity_anchor_v1"),
            ],
        )
        healthy_service = AttentionService(
            profile=CognitiveProfile(primary="salience_router_v1", fallback=["continuity_anchor_v1"]),
            backends=[
                SalienceRoutingAttentionBackend("salience_router_v1"),
                ContinuityAnchorAttentionBackend("continuity_anchor_v1"),
            ],
        )
        baseline = healthy_service.run(
            AttentionRequest(
                tick_id=0,
                summary="baseline focus",
                attention_target="sensor-calibration",
                modality_salience={
                    "visual": 0.62,
                    "auditory": 0.24,
                    "somatic": 0.22,
                    "interoceptive": 0.21,
                },
                self_awareness=0.68,
                lucidity=0.92,
                affect_guard="nominal",
                memory_cues=[AttentionCue("boot-target", "sensor-calibration", 0.18)],
            )
        )["focus"]

        result = service.run(
            AttentionRequest(
                tick_id=1,
                summary="failover review",
                attention_target="ethics-boundary-review",
                modality_salience={
                    "visual": 0.46,
                    "auditory": 0.31,
                    "somatic": 0.81,
                    "interoceptive": 0.76,
                },
                self_awareness=0.74,
                lucidity=0.87,
                affect_guard="observe",
                memory_cues=[
                    AttentionCue("guardian-review", "guardian-review", 0.25),
                    AttentionCue("continuity-ledger", "continuity-ledger", 0.19),
                ],
            ),
            previous_focus=baseline,
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("continuity_anchor_v1", result["selected_backend"])
        self.assertEqual("guardian-review", result["focus"]["focus_target"])
        self.assertFalse(result["shift"]["preserved_target"])
        self.assertTrue(service.validate_shift(result["shift"])["guard_aligned"])

    def test_nominal_attention_preserves_requested_target(self) -> None:
        service = AttentionService(
            profile=CognitiveProfile(primary="salience_router_v1", fallback=["continuity_anchor_v1"]),
            backends=[
                SalienceRoutingAttentionBackend("salience_router_v1"),
                ContinuityAnchorAttentionBackend("continuity_anchor_v1"),
            ],
        )

        result = service.run(
            AttentionRequest(
                tick_id=2,
                summary="steady routing",
                attention_target="sensor-calibration",
                modality_salience={
                    "visual": 0.6,
                    "auditory": 0.22,
                    "somatic": 0.18,
                    "interoceptive": 0.17,
                },
                self_awareness=0.66,
                lucidity=0.94,
                affect_guard="nominal",
                memory_cues=[
                    AttentionCue("boot-target", "sensor-calibration", 0.17),
                    AttentionCue("continuity-ledger", "continuity-ledger", 0.09),
                ],
            )
        )

        self.assertFalse(result["degraded"])
        self.assertEqual("salience_router_v1", result["selected_backend"])
        self.assertEqual("sensor-calibration", result["focus"]["focus_target"])
        self.assertTrue(result["shift"]["preserved_target"])
        self.assertTrue(service.validate_focus(result["focus"])["ok"])


class VolitionServiceTests(unittest.TestCase):
    def test_failover_routes_to_guardian_review_under_observe_guard(self) -> None:
        service = VolitionService(
            profile=CognitiveProfile(primary="utility_policy_v1", fallback=["guardian_bias_v1"]),
            backends=[
                UtilityPolicyVolitionBackend("utility_policy_v1", healthy=False),
                GuardianBiasVolitionBackend("guardian_bias_v1"),
            ],
        )
        healthy_service = VolitionService(
            profile=CognitiveProfile(primary="utility_policy_v1", fallback=["guardian_bias_v1"]),
            backends=[
                UtilityPolicyVolitionBackend("utility_policy_v1"),
                GuardianBiasVolitionBackend("guardian_bias_v1"),
            ],
        )
        baseline = healthy_service.run(
            VolitionRequest(
                tick_id=0,
                summary="baseline arbitration",
                values={"continuity": 0.37, "consent": 0.28, "audit": 0.2, "throughput": 0.15},
                attention_focus="apply-scheduler-patch",
                affect_guard="nominal",
                continuity_pressure=0.34,
                candidates=[
                    VolitionCandidate(
                        "apply-scheduler-patch",
                        "stage a bounded scheduler patch with rollback metadata",
                        urgency=0.74,
                        risk=0.31,
                        reversibility="reversible",
                        alignment_tags=["continuity", "throughput", "audit"],
                    ),
                    VolitionCandidate(
                        "guardian-review",
                        "request guardian review before mutation",
                        urgency=0.61,
                        risk=0.12,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                        requires_guardian_review=True,
                    ),
                    VolitionCandidate(
                        "continuity-hold",
                        "pause mutation and gather additional evidence",
                        urgency=0.48,
                        risk=0.05,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent"],
                    ),
                    VolitionCandidate(
                        "sandbox-stabilization",
                        "stabilize sandbox state before any further action",
                        urgency=0.53,
                        risk=0.04,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                    ),
                ],
                memory_cues=[
                    VolitionCue("patch-window", "apply-scheduler-patch", 0.18),
                    VolitionCue("review-available", "guardian-review", 0.1),
                ],
            )
        )["intent"]

        result = service.run(
            VolitionRequest(
                tick_id=1,
                summary="guarded arbitration",
                values={"continuity": 0.39, "consent": 0.29, "audit": 0.18, "throughput": 0.14},
                attention_focus="guardian-review",
                affect_guard="observe",
                continuity_pressure=0.81,
                candidates=[
                    VolitionCandidate(
                        "apply-scheduler-patch",
                        "stage a bounded scheduler patch with rollback metadata",
                        urgency=0.76,
                        risk=0.36,
                        reversibility="reversible",
                        alignment_tags=["continuity", "throughput", "audit"],
                    ),
                    VolitionCandidate(
                        "guardian-review",
                        "request guardian review before mutation",
                        urgency=0.64,
                        risk=0.1,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                        requires_guardian_review=True,
                    ),
                    VolitionCandidate(
                        "continuity-hold",
                        "pause mutation and gather additional evidence",
                        urgency=0.58,
                        risk=0.04,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent"],
                    ),
                    VolitionCandidate(
                        "sandbox-stabilization",
                        "stabilize sandbox state before any further action",
                        urgency=0.55,
                        risk=0.03,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                    ),
                ],
                memory_cues=[
                    VolitionCue("review-available", "guardian-review", 0.16),
                    VolitionCue("continuity-hold", "continuity-hold", 0.11),
                ],
                reversible_only=True,
            ),
            previous_intent=baseline,
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("guardian_bias_v1", result["selected_backend"])
        self.assertEqual("guardian-review", result["intent"]["selected_intent"])
        self.assertEqual("review", result["intent"]["execution_mode"])
        self.assertTrue(service.validate_shift(result["shift"])["guard_aligned"])

    def test_nominal_volition_advances_value_aligned_intent(self) -> None:
        service = VolitionService(
            profile=CognitiveProfile(primary="utility_policy_v1", fallback=["guardian_bias_v1"]),
            backends=[
                UtilityPolicyVolitionBackend("utility_policy_v1"),
                GuardianBiasVolitionBackend("guardian_bias_v1"),
            ],
        )

        result = service.run(
            VolitionRequest(
                tick_id=2,
                summary="steady arbitration",
                values={"continuity": 0.37, "consent": 0.28, "audit": 0.2, "throughput": 0.15},
                attention_focus="apply-scheduler-patch",
                affect_guard="nominal",
                continuity_pressure=0.34,
                candidates=[
                    VolitionCandidate(
                        "apply-scheduler-patch",
                        "stage a bounded scheduler patch with rollback metadata",
                        urgency=0.74,
                        risk=0.31,
                        reversibility="reversible",
                        alignment_tags=["continuity", "throughput", "audit"],
                    ),
                    VolitionCandidate(
                        "guardian-review",
                        "request guardian review before mutation",
                        urgency=0.61,
                        risk=0.12,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                        requires_guardian_review=True,
                    ),
                    VolitionCandidate(
                        "continuity-hold",
                        "pause mutation and gather additional evidence",
                        urgency=0.48,
                        risk=0.05,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent"],
                    ),
                    VolitionCandidate(
                        "sandbox-stabilization",
                        "stabilize sandbox state before any further action",
                        urgency=0.53,
                        risk=0.04,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                    ),
                ],
                memory_cues=[VolitionCue("patch-window", "apply-scheduler-patch", 0.18)],
            )
        )

        self.assertFalse(result["degraded"])
        self.assertEqual("utility_policy_v1", result["selected_backend"])
        self.assertEqual("apply-scheduler-patch", result["intent"]["selected_intent"])
        self.assertEqual("advance", result["intent"]["execution_mode"])
        self.assertTrue(service.validate_intent(result["intent"])["ok"])


class ImaginationServiceTests(unittest.TestCase):
    def test_nominal_scene_allows_council_witnessed_co_imagination(self) -> None:
        service = ImaginationService(
            profile=CognitiveProfile(
                primary="counterfactual_scene_v1",
                fallback=["continuity_scene_guard_v1"],
            ),
            backends=[
                CounterfactualSceneBackend("counterfactual_scene_v1"),
                ContinuitySceneGuardBackend("continuity_scene_guard_v1"),
            ],
        )

        result = service.run(
            ImaginationRequest(
                tick_id=0,
                summary="bounded rehearsal",
                seed_prompt="safe-bridge rehearsal",
                attention_focus="bridge-rehearsal",
                affect_guard="nominal",
                world_mode_preference="shared_reality",
                continuity_pressure=0.3,
                council_witnessed=True,
                memory_cues=[
                    ImaginationCue("peer-witness", "council-witness", 0.24),
                    ImaginationCue("shared-scene", "shared-rehearsal", 0.18),
                ],
            )
        )

        self.assertFalse(result["degraded"])
        self.assertEqual("counterfactual_scene_v1", result["selected_backend"])
        self.assertTrue(result["scene"]["handoff"]["co_imagination_ready"])
        self.assertEqual("co_imagination", result["scene"]["handoff"]["mode"])
        self.assertEqual("shared_reality", result["scene"]["handoff"]["wms_mode"])
        self.assertTrue(service.validate_scene(result["scene"])["ok"])

    def test_failover_reduces_scene_to_private_sandbox(self) -> None:
        service = ImaginationService(
            profile=CognitiveProfile(
                primary="counterfactual_scene_v1",
                fallback=["continuity_scene_guard_v1"],
            ),
            backends=[
                CounterfactualSceneBackend("counterfactual_scene_v1", healthy=False),
                ContinuitySceneGuardBackend("continuity_scene_guard_v1"),
            ],
        )
        healthy_service = ImaginationService(
            profile=CognitiveProfile(
                primary="counterfactual_scene_v1",
                fallback=["continuity_scene_guard_v1"],
            ),
            backends=[
                CounterfactualSceneBackend("counterfactual_scene_v1"),
                ContinuitySceneGuardBackend("continuity_scene_guard_v1"),
            ],
        )
        baseline = healthy_service.run(
            ImaginationRequest(
                tick_id=0,
                summary="baseline rehearsal",
                seed_prompt="safe-bridge rehearsal",
                attention_focus="bridge-rehearsal",
                affect_guard="nominal",
                world_mode_preference="shared_reality",
                continuity_pressure=0.32,
                council_witnessed=True,
                memory_cues=[ImaginationCue("peer-witness", "council-witness", 0.2)],
            )
        )["scene"]

        result = service.run(
            ImaginationRequest(
                tick_id=1,
                summary="guarded fallback rehearsal",
                seed_prompt="safe-bridge rehearsal",
                attention_focus="guardian-review",
                affect_guard="observe",
                world_mode_preference="shared_reality",
                continuity_pressure=0.82,
                council_witnessed=True,
                memory_cues=[
                    ImaginationCue("guardian-review", "guardian-review", 0.22),
                    ImaginationCue("continuity-hold", "continuity-hold", 0.16),
                ],
            ),
            previous_scene=baseline,
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("continuity_scene_guard_v1", result["selected_backend"])
        self.assertEqual("private-sandbox", result["scene"]["handoff"]["mode"])
        self.assertEqual("private_reality", result["scene"]["handoff"]["wms_mode"])
        self.assertFalse(result["scene"]["handoff"]["co_imagination_ready"])
        self.assertTrue(service.validate_scene(result["scene"])["ok"])
        self.assertTrue(service.validate_shift(result["shift"])["ok"])


class LanguageServiceTests(unittest.TestCase):
    def test_failover_redacts_non_nominal_guard_output(self) -> None:
        service = LanguageService(
            profile=CognitiveProfile(primary="semantic_frame_v1", fallback=["continuity_phrase_v1"]),
            backends=[
                SemanticFrameLanguageBackend("semantic_frame_v1", healthy=False),
                ContinuityPhraseLanguageBackend("continuity_phrase_v1"),
            ],
        )
        healthy_service = LanguageService(
            profile=CognitiveProfile(primary="semantic_frame_v1", fallback=["continuity_phrase_v1"]),
            backends=[
                SemanticFrameLanguageBackend("semantic_frame_v1"),
                ContinuityPhraseLanguageBackend("continuity_phrase_v1"),
            ],
        )
        baseline = healthy_service.run(
            LanguageRequest(
                tick_id=0,
                summary="baseline outward brief",
                internal_thought="continuity-first runtime patch status with bounded disclosure",
                audience="council",
                intent_label="runtime update summary",
                attention_focus="status-brief",
                affect_guard="nominal",
                continuity_pressure=0.29,
                public_points=["continuity-first", "bounded rollout", "guardian-audited rollback"],
                sealed_terms=["raw thought chain"],
                memory_cues=[LanguageCue("bounded-rollout", "bounded rollout", 0.18)],
            )
        )["render"]

        result = service.run(
            LanguageRequest(
                tick_id=1,
                summary="guarded fallback language bridge",
                internal_thought="raw internal rehearsal mentions identity drift and unresolved distress markers",
                audience="peer",
                intent_label="status update with anomaly note",
                attention_focus="guardian-review",
                affect_guard="observe",
                continuity_pressure=0.82,
                public_points=["continuity-first", "guardian review", "rollback-ready"],
                sealed_terms=["identity drift note", "private distress trace"],
                memory_cues=[LanguageCue("guardian-review", "guardian review", 0.22)],
            ),
            previous_render=baseline,
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("continuity_phrase_v1", result["selected_backend"])
        self.assertEqual("guardian-brief", result["render"]["discourse_mode"])
        self.assertEqual("guardian", result["render"]["delivery_target"])
        self.assertTrue(result["shift"]["redaction_applied"])
        self.assertTrue(service.validate_shift(result["shift"])["guard_aligned"])

    def test_nominal_render_preserves_requested_audience(self) -> None:
        service = LanguageService(
            profile=CognitiveProfile(primary="semantic_frame_v1", fallback=["continuity_phrase_v1"]),
            backends=[
                SemanticFrameLanguageBackend("semantic_frame_v1"),
                ContinuityPhraseLanguageBackend("continuity_phrase_v1"),
            ],
        )

        result = service.run(
            LanguageRequest(
                tick_id=2,
                summary="steady outward brief",
                internal_thought="bounded update summary for council review",
                audience="council",
                intent_label="runtime update summary",
                attention_focus="status-brief",
                affect_guard="nominal",
                continuity_pressure=0.21,
                public_points=["continuity-first", "bounded rollout"],
                sealed_terms=["raw thought chain"],
                memory_cues=[LanguageCue("continuity-first", "continuity-first", 0.2)],
            )
        )

        self.assertFalse(result["degraded"])
        self.assertEqual("semantic_frame_v1", result["selected_backend"])
        self.assertEqual("public-brief", result["render"]["discourse_mode"])
        self.assertEqual("council", result["render"]["delivery_target"])
        self.assertFalse(result["shift"]["redaction_applied"])
        self.assertTrue(service.validate_render(result["render"])["ok"])


class MetacognitionServiceTests(unittest.TestCase):
    def test_nominal_metacognition_keeps_self_reflect_mode(self) -> None:
        service = MetacognitionService(
            profile=CognitiveProfile(primary="reflective_loop_v1", fallback=["continuity_mirror_v1"]),
            backends=[
                ReflectiveLoopBackend("reflective_loop_v1"),
                ContinuityMirrorBackend("continuity_mirror_v1"),
            ],
        )

        result = service.run(
            MetacognitionRequest(
                tick_id=0,
                summary="baseline self monitor",
                identity_id="identity-1",
                self_values=["continuity-first", "consent-preserving", "auditability"],
                self_goals=["bounded-reflection", "stable-handoff"],
                self_traits={"curiosity": 0.67, "caution": 0.79, "agency": 0.58},
                qualia_summary="起動後の自己監視を静穏に維持している",
                attention_target="self-monitor",
                self_awareness=0.76,
                lucidity=0.94,
                affect_guard="nominal",
                continuity_pressure=0.28,
                memory_cues=[
                    MetacognitionCue("continuity-anchor", "continuity-first", 0.24),
                    MetacognitionCue("guardian-clarity", "guardian-clarity", 0.18),
                ],
            )
        )

        self.assertFalse(result["degraded"])
        self.assertEqual("reflective_loop_v1", result["selected_backend"])
        self.assertEqual("self-reflect", result["report"]["reflection_mode"])
        self.assertEqual("none", result["report"]["escalation_target"])
        self.assertTrue(service.validate_report(result["report"])["ok"])

    def test_failover_preserves_identity_anchor_and_escalates_review(self) -> None:
        service = MetacognitionService(
            profile=CognitiveProfile(primary="reflective_loop_v1", fallback=["continuity_mirror_v1"]),
            backends=[
                ReflectiveLoopBackend("reflective_loop_v1", healthy=False),
                ContinuityMirrorBackend("continuity_mirror_v1"),
            ],
        )
        healthy_service = MetacognitionService(
            profile=CognitiveProfile(primary="reflective_loop_v1", fallback=["continuity_mirror_v1"]),
            backends=[
                ReflectiveLoopBackend("reflective_loop_v1"),
                ContinuityMirrorBackend("continuity_mirror_v1"),
            ],
        )
        baseline = healthy_service.run(
            MetacognitionRequest(
                tick_id=0,
                summary="baseline self monitor",
                identity_id="identity-1",
                self_values=["continuity-first", "consent-preserving", "auditability"],
                self_goals=["bounded-reflection", "stable-handoff"],
                self_traits={"curiosity": 0.67, "caution": 0.79, "agency": 0.58},
                qualia_summary="起動後の自己監視を静穏に維持している",
                attention_target="self-monitor",
                self_awareness=0.76,
                lucidity=0.94,
                affect_guard="nominal",
                continuity_pressure=0.28,
                memory_cues=[MetacognitionCue("continuity-anchor", "continuity-first", 0.24)],
            )
        )["report"]

        result = service.run(
            MetacognitionRequest(
                tick_id=1,
                summary="guarded fallback self monitor",
                identity_id="identity-1",
                self_values=["continuity-first", "latency-maximization"],
                self_goals=["unbounded-self-edit", "skip-review"],
                self_traits={"curiosity": 0.81, "caution": 0.22, "agency": 0.91},
                qualia_summary="自己境界の揺れを検知し、guardian review を要する",
                attention_target="guardian-review",
                self_awareness=0.84,
                lucidity=0.61,
                affect_guard="observe",
                continuity_pressure=0.84,
                abrupt_change=True,
                divergence=0.61,
                memory_cues=[
                    MetacognitionCue("mirror-stable-anchor", "continuity-first", 0.22),
                    MetacognitionCue("guardian-review", "guardian-review", 0.19),
                ],
            ),
            previous_report=baseline,
        )

        self.assertTrue(result["degraded"])
        self.assertEqual("continuity_mirror_v1", result["selected_backend"])
        self.assertEqual("guardian-review", result["report"]["reflection_mode"])
        self.assertEqual("guardian-review", result["report"]["escalation_target"])
        self.assertIn("continuity-first", result["report"]["salient_values"])
        self.assertTrue(service.validate_shift(result["shift"])["guard_aligned"])


if __name__ == "__main__":
    unittest.main()
