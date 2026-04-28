from __future__ import annotations

import copy
import unittest

from omoikane.mind.qualia import QualiaBuffer
from omoikane.mind.self_model import SelfModelMonitor, SelfModelSnapshot


class QualiaBufferTests(unittest.TestCase):
    def test_append_rejects_out_of_range_values(self) -> None:
        buffer = QualiaBuffer()

        with self.assertRaises(ValueError):
            buffer.append("過負荷", 0.2, 0.1, 1.2)

    def test_append_derives_fixed_size_surrogate_embeddings(self) -> None:
        buffer = QualiaBuffer()

        tick = buffer.append(
            "静穏な起動",
            0.1,
            0.2,
            0.9,
            modality_salience={
                "visual": 0.4,
                "auditory": 0.2,
                "somatic": 0.1,
                "interoceptive": 0.5,
            },
            attention_target="boot-review",
            self_awareness=0.62,
            lucidity=0.93,
        )

        self.assertEqual(32, tick.sampling_profile["embedding_dimensions"])
        self.assertEqual(250, tick.sampling_profile["sampling_window_ms"])
        self.assertEqual(
            ["visual", "auditory", "somatic", "interoceptive"],
            tick.sampling_profile["modalities"],
        )
        self.assertEqual("boot-review", tick.attention_target)
        self.assertEqual(32, len(tick.sensory_embeddings["visual"]))
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in tick.sensory_embeddings["visual"]))

    def test_append_rejects_unknown_modality_keys(self) -> None:
        buffer = QualiaBuffer()

        with self.assertRaises(ValueError):
            buffer.append(
                "未知チャネル",
                0.1,
                0.2,
                0.9,
                modality_salience={"olfactory": 0.3},
            )

    def test_recent_requires_positive_count(self) -> None:
        buffer = QualiaBuffer()
        buffer.append("静穏", 0.1, 0.2, 0.9)

        with self.assertRaises(ValueError):
            buffer.recent(0)

    def test_recent_returns_latest_ticks_in_order(self) -> None:
        buffer = QualiaBuffer()
        buffer.append("起動", 0.1, 0.2, 0.9)
        buffer.append("合議", 0.2, 0.3, 0.8)
        buffer.append("記録", 0.0, 0.1, 0.95)

        recent = buffer.recent(2)

        self.assertEqual([1, 2], [tick["tick_id"] for tick in recent])


def _build_external_adjudication_receipt(monitor: SelfModelMonitor) -> dict[str, object]:
    observation = monitor.update(
        SelfModelSnapshot(
            identity_id="id-1",
            values=["continuity"],
            goals=["safe-self-construction"],
            traits={"caution": 0.84},
        )
    )
    calibration = monitor.build_advisory_calibration_receipt(
        observation,
        reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
        self_consent_ref="consent://self-model-calibration/advisory-review-v1",
        council_resolution_ref="council://self-model-calibration/no-forced-writeback",
        guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
        proposed_adjustments=[{"trait": "caution", "direction": "increase", "delta": 0.12}],
    )
    escalation = monitor.build_pathology_escalation_receipt(
        calibration,
        risk_signal_refs=["risk://self-model/pathology-boundary/abrupt-divergence"],
        consent_or_emergency_review_ref=(
            "consent-or-emergency://self-model/pathology-escalation/review-v1"
        ),
        council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
        guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
        medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
        legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
        care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
    )
    handoff = monitor.build_care_trustee_handoff_receipt(
        escalation,
        trustee_refs=["trustee://jp-13/self-model/long-term-trustee/v1"],
        care_team_refs=["care-team://jp-13/self-model/care-board/v1"],
        legal_guardian_refs=["legal-guardian://jp-13/self-model/capacity-review/v1"],
        responsibility_boundary_refs=[
            "boundary://self-model/care-trustee/no-os-trustee-role/v1",
            "boundary://self-model/care-trustee/external-adjudication-required/v1",
        ],
        consent_or_emergency_review_ref=(
            "consent-or-emergency://self-model/care-trustee/review-v1"
        ),
        council_resolution_ref="council://self-model/care-trustee/boundary-only",
        guardian_boundary_ref="guardian://self-model/care-trustee/no-os-authority",
        long_term_review_schedule_ref="schedule://self-model/care-trustee/quarterly-review/v1",
        escalation_continuity_ref="continuity://self-model/care-trustee/escalation-chain/v1",
    )
    return monitor.build_external_adjudication_result_receipt(
        handoff,
        medical_adjudication_result_refs=[
            "external-medical-result://jp-13/self-model/no-os-diagnosis/v1"
        ],
        legal_adjudication_result_refs=[
            "external-legal-result://jp-13/self-model/capacity-boundary/v1"
        ],
        trustee_adjudication_result_refs=[
            "external-trustee-result://jp-13/self-model/trustee-appointment/v1"
        ],
        jurisdiction_policy_refs=[
            "jurisdiction-policy://jp-13/self-model/medical-review/v1"
        ],
        appeal_or_review_refs=[
            "appeal-review://jp-13/self-model/adjudication/periodic-review/v1"
        ],
        consent_or_emergency_review_ref=(
            "consent-or-emergency://self-model/external-adjudication/result-review-v1"
        ),
        council_resolution_ref="council://self-model/external-adjudication/boundary-only",
        guardian_boundary_ref="guardian://self-model/external-adjudication/no-os-authority",
        continuity_review_ref="continuity://self-model/external-adjudication/result-chain/v1",
    )


def _external_adjudication_verifier_inputs(
    adjudication: dict[str, object],
) -> list[dict[str, object]]:
    return [
        {
            "verifier_ref": "verifier://jp-13/self-model/appeal-review-live/v1",
            "verifier_endpoint": "https://verifier.jp-13.example.invalid/self-model/appeal-review",
            "jurisdiction": "JP-13",
            "checked_at_ref": "timestamp://self-model/external-adjudication/verifier/jp-13",
            "response_ref": "response://jp-13/self-model/appeal-review/live-verification/v1",
            "response_status": "verified",
            "freshness_window_seconds": 900,
            "observed_latency_ms": 42.5,
            "signed_response_envelope_ref": "signed-envelope://jp-13/self-model/appeal-review/v1",
            "response_signing_key_ref": "key://jp-13/self-model/appeal-review/verifier-key/v1",
            "covered_appeal_or_review_refs": adjudication["appeal_or_review_refs"],
            "verifier_key_ref": "key://jp-13/self-model/appeal-review/verifier-key/v1",
            "trust_root_ref": "trust-root://jp-13/self-model/appeal-review/pki/v1",
            "route_ref": "route://jp-13/self-model/appeal-review/live-json/v1",
        },
        {
            "verifier_ref": "verifier://us-ca/self-model/appeal-review-live/v1",
            "verifier_endpoint": "https://verifier.us-ca.example.invalid/self-model/appeal-review",
            "jurisdiction": "US-CA",
            "checked_at_ref": "timestamp://self-model/external-adjudication/verifier/us-ca",
            "response_ref": "response://us-ca/self-model/appeal-review/live-verification/v1",
            "response_status": "verified",
            "freshness_window_seconds": 900,
            "observed_latency_ms": 57.25,
            "signed_response_envelope_ref": "signed-envelope://us-ca/self-model/appeal-review/v1",
            "response_signing_key_ref": "key://us-ca/self-model/appeal-review/verifier-key/v1",
            "covered_appeal_or_review_refs": adjudication["appeal_or_review_refs"],
            "verifier_key_ref": "key://us-ca/self-model/appeal-review/verifier-key/v1",
            "trust_root_ref": "trust-root://us-ca/self-model/appeal-review/pki/v1",
            "route_ref": "route://us-ca/self-model/appeal-review/live-json/v1",
        },
    ]


class SelfModelMonitorTests(unittest.TestCase):
    def test_stable_drift_stays_below_fixed_threshold(self) -> None:
        monitor = SelfModelMonitor()
        monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )

        result = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.74, "caution": 0.82, "agency": 0.60},
            )
        )

        self.assertFalse(result["abrupt_change"])
        self.assertEqual("bounded-self-model-monitor-v1", result["policy_id"])
        self.assertEqual(0.35, result["threshold"])
        self.assertEqual(2, result["history_length"])
        self.assertEqual(0.35, monitor.profile()["abrupt_change_threshold"])

    def test_abrupt_change_is_flagged(self) -> None:
        monitor = SelfModelMonitor(abrupt_change_threshold=0.35)
        monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )

        result = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["expedience"],
                goals=["unbounded-self-modification"],
                traits={"curiosity": 0.05, "caution": 0.10, "agency": 0.99},
            )
        )

        self.assertTrue(result["abrupt_change"])
        self.assertGreaterEqual(result["divergence"], 0.35)

    def test_advisory_calibration_receipt_requires_self_acceptance(self) -> None:
        monitor = SelfModelMonitor()
        monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        abrupt = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["latency-maximization"],
                goals=["skip-review", "unbounded-self-modification"],
                traits={"curiosity": 0.05, "caution": 0.10, "agency": 0.99},
            )
        )

        receipt = monitor.build_advisory_calibration_receipt(
            abrupt,
            reviewer_evidence_refs=[
                "evidence://self-model/self-report/abrupt-review",
                "evidence://self-model/council-observation/continuity-drift",
            ],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        validation = monitor.validate_advisory_calibration_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["advisory_only"])
        self.assertTrue(validation["self_consent_bound"])
        self.assertFalse(receipt["forced_correction_allowed"])
        self.assertEqual(
            "requires-self-acceptance",
            receipt["proposed_adjustments"][0]["status"],
        )

    def test_advisory_calibration_rejects_forced_writeback(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"caution": 0.84},
            )
        )
        receipt = monitor.build_advisory_calibration_receipt(
            observation,
            reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        tampered = copy.deepcopy(receipt)
        tampered["forced_correction_allowed"] = True

        validation = monitor.validate_advisory_calibration_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("forced_correction_allowed must be false", validation["errors"])

    def test_pathology_escalation_receipt_preserves_external_boundary(self) -> None:
        monitor = SelfModelMonitor()
        monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        abrupt = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["latency-maximization"],
                goals=["skip-review", "unbounded-self-modification"],
                traits={"curiosity": 0.05, "caution": 0.10, "agency": 0.99},
            )
        )
        calibration = monitor.build_advisory_calibration_receipt(
            abrupt,
            reviewer_evidence_refs=[
                "evidence://self-model/self-report/abrupt-review",
                "evidence://self-model/council-observation/continuity-drift",
            ],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )

        escalation = monitor.build_pathology_escalation_receipt(
            calibration,
            risk_signal_refs=[
                "risk://self-model/pathology-boundary/abrupt-divergence",
                "risk://self-model/pathology-boundary/self-report-inconsistency",
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/pathology-escalation/review-v1"
            ),
            council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
            guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
            medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
            legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
            care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
        )
        validation = monitor.validate_pathology_escalation_receipt(escalation)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["care_handoff_required"])
        self.assertTrue(validation["consent_or_emergency_review_required"])
        self.assertTrue(validation["boundary_only_review"])
        self.assertTrue(validation["handoff_commit_digest_bound"])
        self.assertFalse(escalation["internal_diagnosis_allowed"])
        self.assertFalse(escalation["self_model_writeback_allowed"])
        self.assertFalse(escalation["forced_correction_allowed"])
        self.assertFalse(escalation["raw_medical_payload_stored"])

    def test_pathology_escalation_rejects_internal_diagnosis(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"caution": 0.84},
            )
        )
        calibration = monitor.build_advisory_calibration_receipt(
            observation,
            reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        escalation = monitor.build_pathology_escalation_receipt(
            calibration,
            risk_signal_refs=["risk://self-model/pathology-boundary/abrupt-divergence"],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/pathology-escalation/review-v1"
            ),
            council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
            guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
            medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
            legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
            care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
        )
        tampered = copy.deepcopy(escalation)
        tampered["internal_diagnosis_allowed"] = True

        validation = monitor.validate_pathology_escalation_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("internal_diagnosis_allowed must be false", validation["errors"])

    def test_care_trustee_handoff_keeps_os_out_of_trustee_role(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"caution": 0.84},
            )
        )
        calibration = monitor.build_advisory_calibration_receipt(
            observation,
            reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        escalation = monitor.build_pathology_escalation_receipt(
            calibration,
            risk_signal_refs=["risk://self-model/pathology-boundary/abrupt-divergence"],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/pathology-escalation/review-v1"
            ),
            council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
            guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
            medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
            legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
            care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
        )

        handoff = monitor.build_care_trustee_handoff_receipt(
            escalation,
            trustee_refs=["trustee://jp-13/self-model/long-term-trustee/v1"],
            care_team_refs=["care-team://jp-13/self-model/care-board/v1"],
            legal_guardian_refs=["legal-guardian://jp-13/self-model/capacity-review/v1"],
            responsibility_boundary_refs=[
                "boundary://self-model/care-trustee/no-os-trustee-role/v1",
                "boundary://self-model/care-trustee/external-adjudication-required/v1",
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/care-trustee/review-v1"
            ),
            council_resolution_ref="council://self-model/care-trustee/boundary-only",
            guardian_boundary_ref="guardian://self-model/care-trustee/no-os-authority",
            long_term_review_schedule_ref="schedule://self-model/care-trustee/quarterly-review/v1",
            escalation_continuity_ref="continuity://self-model/care-trustee/escalation-chain/v1",
        )
        validation = monitor.validate_care_trustee_handoff_receipt(handoff)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["long_term_review_required"])
        self.assertTrue(validation["external_adjudication_required"])
        self.assertTrue(validation["responsibility_commit_digest_bound"])
        self.assertEqual(
            escalation["receipt_digest"],
            handoff["source_escalation_receipt_digest"],
        )
        self.assertFalse(handoff["os_trustee_role_allowed"])
        self.assertFalse(handoff["os_medical_authority_allowed"])
        self.assertFalse(handoff["os_legal_guardianship_allowed"])
        self.assertFalse(handoff["self_model_writeback_allowed"])
        self.assertFalse(handoff["raw_trustee_payload_stored"])

    def test_care_trustee_handoff_rejects_os_trustee_role(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"caution": 0.84},
            )
        )
        calibration = monitor.build_advisory_calibration_receipt(
            observation,
            reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        escalation = monitor.build_pathology_escalation_receipt(
            calibration,
            risk_signal_refs=["risk://self-model/pathology-boundary/abrupt-divergence"],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/pathology-escalation/review-v1"
            ),
            council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
            guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
            medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
            legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
            care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
        )
        handoff = monitor.build_care_trustee_handoff_receipt(
            escalation,
            trustee_refs=["trustee://jp-13/self-model/long-term-trustee/v1"],
            care_team_refs=["care-team://jp-13/self-model/care-board/v1"],
            legal_guardian_refs=["legal-guardian://jp-13/self-model/capacity-review/v1"],
            responsibility_boundary_refs=[
                "boundary://self-model/care-trustee/no-os-trustee-role/v1",
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/care-trustee/review-v1"
            ),
            council_resolution_ref="council://self-model/care-trustee/boundary-only",
            guardian_boundary_ref="guardian://self-model/care-trustee/no-os-authority",
            long_term_review_schedule_ref="schedule://self-model/care-trustee/quarterly-review/v1",
            escalation_continuity_ref="continuity://self-model/care-trustee/escalation-chain/v1",
        )
        tampered = copy.deepcopy(handoff)
        tampered["os_trustee_role_allowed"] = True

        validation = monitor.validate_care_trustee_handoff_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("os_trustee_role_allowed must be false", validation["errors"])

    def test_external_adjudication_result_keeps_authority_outside_os(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"caution": 0.84},
            )
        )
        calibration = monitor.build_advisory_calibration_receipt(
            observation,
            reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        escalation = monitor.build_pathology_escalation_receipt(
            calibration,
            risk_signal_refs=["risk://self-model/pathology-boundary/abrupt-divergence"],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/pathology-escalation/review-v1"
            ),
            council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
            guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
            medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
            legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
            care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
        )
        handoff = monitor.build_care_trustee_handoff_receipt(
            escalation,
            trustee_refs=["trustee://jp-13/self-model/long-term-trustee/v1"],
            care_team_refs=["care-team://jp-13/self-model/care-board/v1"],
            legal_guardian_refs=["legal-guardian://jp-13/self-model/capacity-review/v1"],
            responsibility_boundary_refs=[
                "boundary://self-model/care-trustee/no-os-trustee-role/v1",
                "boundary://self-model/care-trustee/external-adjudication-required/v1",
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/care-trustee/review-v1"
            ),
            council_resolution_ref="council://self-model/care-trustee/boundary-only",
            guardian_boundary_ref="guardian://self-model/care-trustee/no-os-authority",
            long_term_review_schedule_ref="schedule://self-model/care-trustee/quarterly-review/v1",
            escalation_continuity_ref="continuity://self-model/care-trustee/escalation-chain/v1",
        )

        adjudication = monitor.build_external_adjudication_result_receipt(
            handoff,
            medical_adjudication_result_refs=[
                "external-medical-result://jp-13/self-model/no-os-diagnosis/v1"
            ],
            legal_adjudication_result_refs=[
                "external-legal-result://jp-13/self-model/capacity-boundary/v1"
            ],
            trustee_adjudication_result_refs=[
                "external-trustee-result://jp-13/self-model/trustee-appointment/v1"
            ],
            jurisdiction_policy_refs=[
                "jurisdiction-policy://jp-13/self-model/medical-review/v1"
            ],
            appeal_or_review_refs=[
                "appeal-review://jp-13/self-model/adjudication/periodic-review/v1"
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/external-adjudication/result-review-v1"
            ),
            council_resolution_ref="council://self-model/external-adjudication/boundary-only",
            guardian_boundary_ref="guardian://self-model/external-adjudication/no-os-authority",
            continuity_review_ref="continuity://self-model/external-adjudication/result-chain/v1",
        )
        validation = monitor.validate_external_adjudication_result_receipt(adjudication)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["external_adjudication_result_bound"])
        self.assertTrue(validation["jurisdiction_policy_bound"])
        self.assertTrue(validation["appeal_or_review_path_required"])
        self.assertTrue(validation["adjudication_commit_digest_bound"])
        self.assertEqual(
            handoff["receipt_digest"],
            adjudication["source_handoff_receipt_digest"],
        )
        self.assertFalse(adjudication["os_adjudication_authority_allowed"])
        self.assertFalse(adjudication["os_medical_authority_allowed"])
        self.assertFalse(adjudication["os_legal_authority_allowed"])
        self.assertFalse(adjudication["os_trustee_role_allowed"])
        self.assertFalse(adjudication["self_model_writeback_allowed"])
        self.assertFalse(adjudication["raw_medical_result_payload_stored"])

    def test_external_adjudication_result_rejects_os_adjudication_authority(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"caution": 0.84},
            )
        )
        calibration = monitor.build_advisory_calibration_receipt(
            observation,
            reviewer_evidence_refs=["evidence://self-model/self-report/abrupt-review"],
            self_consent_ref="consent://self-model-calibration/advisory-review-v1",
            council_resolution_ref="council://self-model-calibration/no-forced-writeback",
            guardian_redaction_ref="guardian://self-model-calibration/redacted-witness-set",
            proposed_adjustments=[
                {"trait": "caution", "direction": "increase", "delta": 0.12}
            ],
        )
        escalation = monitor.build_pathology_escalation_receipt(
            calibration,
            risk_signal_refs=["risk://self-model/pathology-boundary/abrupt-divergence"],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/pathology-escalation/review-v1"
            ),
            council_resolution_ref="council://self-model/pathology-escalation/boundary-only",
            guardian_boundary_ref="guardian://self-model/pathology-escalation/no-os-diagnosis",
            medical_system_ref="external-medical://jp-13/self-model-review-board/v1",
            legal_system_ref="external-legal://jp-13/capacity-review-boundary/v1",
            care_handoff_ref="handoff://self-model/pathology-escalation/human-care-team/v1",
        )
        handoff = monitor.build_care_trustee_handoff_receipt(
            escalation,
            trustee_refs=["trustee://jp-13/self-model/long-term-trustee/v1"],
            care_team_refs=["care-team://jp-13/self-model/care-board/v1"],
            legal_guardian_refs=["legal-guardian://jp-13/self-model/capacity-review/v1"],
            responsibility_boundary_refs=[
                "boundary://self-model/care-trustee/no-os-trustee-role/v1",
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/care-trustee/review-v1"
            ),
            council_resolution_ref="council://self-model/care-trustee/boundary-only",
            guardian_boundary_ref="guardian://self-model/care-trustee/no-os-authority",
            long_term_review_schedule_ref="schedule://self-model/care-trustee/quarterly-review/v1",
            escalation_continuity_ref="continuity://self-model/care-trustee/escalation-chain/v1",
        )
        adjudication = monitor.build_external_adjudication_result_receipt(
            handoff,
            medical_adjudication_result_refs=[
                "external-medical-result://jp-13/self-model/no-os-diagnosis/v1"
            ],
            legal_adjudication_result_refs=[
                "external-legal-result://jp-13/self-model/capacity-boundary/v1"
            ],
            trustee_adjudication_result_refs=[
                "external-trustee-result://jp-13/self-model/trustee-appointment/v1"
            ],
            jurisdiction_policy_refs=[
                "jurisdiction-policy://jp-13/self-model/medical-review/v1"
            ],
            appeal_or_review_refs=[
                "appeal-review://jp-13/self-model/adjudication/periodic-review/v1"
            ],
            consent_or_emergency_review_ref=(
                "consent-or-emergency://self-model/external-adjudication/result-review-v1"
            ),
            council_resolution_ref="council://self-model/external-adjudication/boundary-only",
            guardian_boundary_ref="guardian://self-model/external-adjudication/no-os-authority",
            continuity_review_ref="continuity://self-model/external-adjudication/result-chain/v1",
        )
        tampered = copy.deepcopy(adjudication)
        tampered["os_adjudication_authority_allowed"] = True

        validation = monitor.validate_external_adjudication_result_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn(
            "os_adjudication_authority_allowed must be false",
            validation["errors"],
        )

    def test_external_adjudication_verifier_binds_live_quorum(self) -> None:
        monitor = SelfModelMonitor()
        adjudication = _build_external_adjudication_receipt(monitor)

        verifier = monitor.build_external_adjudication_verifier_receipt(
            adjudication,
            verifier_receipts=_external_adjudication_verifier_inputs(adjudication),
            council_resolution_ref=(
                "council://self-model/external-adjudication/verifier-network-boundary"
            ),
            guardian_boundary_ref=(
                "guardian://self-model/external-adjudication/verifier-no-os-authority"
            ),
            continuity_review_ref=(
                "continuity://self-model/external-adjudication/verifier-chain/v1"
            ),
        )
        validation = monitor.validate_external_adjudication_verifier_receipt(verifier)

        self.assertTrue(validation["ok"])
        self.assertEqual("complete", validation["verifier_quorum_status"])
        self.assertTrue(validation["appeal_review_live_verifier_bound"])
        self.assertTrue(validation["jurisdiction_policy_live_verifier_bound"])
        self.assertTrue(validation["signed_response_envelope_bound"])
        self.assertTrue(validation["freshness_window_bound"])
        self.assertTrue(validation["verifier_quorum_digest_bound"])
        self.assertEqual(
            adjudication["receipt_digest"],
            verifier["source_adjudication_receipt_digest"],
        )
        self.assertFalse(verifier["stale_response_accepted"])
        self.assertFalse(verifier["revoked_response_accepted"])
        self.assertFalse(verifier["os_adjudication_authority_allowed"])
        self.assertFalse(verifier["self_model_writeback_allowed"])
        self.assertFalse(verifier["raw_verifier_payload_stored"])

    def test_external_adjudication_verifier_rejects_revoked_response(self) -> None:
        monitor = SelfModelMonitor()
        adjudication = _build_external_adjudication_receipt(monitor)
        verifier = monitor.build_external_adjudication_verifier_receipt(
            adjudication,
            verifier_receipts=_external_adjudication_verifier_inputs(adjudication),
            council_resolution_ref=(
                "council://self-model/external-adjudication/verifier-network-boundary"
            ),
            guardian_boundary_ref=(
                "guardian://self-model/external-adjudication/verifier-no-os-authority"
            ),
            continuity_review_ref=(
                "continuity://self-model/external-adjudication/verifier-chain/v1"
            ),
        )
        tampered = copy.deepcopy(verifier)
        tampered["verifier_receipts"][0]["response_status"] = "revoked"

        validation = monitor.validate_external_adjudication_verifier_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn(
            "verifier_receipts[0].response_status must be verified",
            validation["errors"],
        )

    def test_value_generation_receipt_preserves_autonomy(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )

        receipt = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=[
                "self-model://history/stable-drift-window",
                "memory://semantic/reflection/generative-values",
            ],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        validation = monitor.validate_value_generation_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["self_authored"])
        self.assertTrue(validation["autonomy_preserved"])
        self.assertTrue(receipt["requires_future_self_acceptance"])
        self.assertFalse(receipt["external_veto_allowed"])
        self.assertFalse(receipt["forced_stability_lock_allowed"])
        self.assertFalse(receipt["accepted_for_writeback"])
        self.assertFalse(receipt["raw_value_payload_stored"])

    def test_value_generation_rejects_external_veto(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"curiosity": 0.71},
            )
        )
        receipt = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        tampered = copy.deepcopy(receipt)
        tampered["external_veto_allowed"] = True

        validation = monitor.validate_value_generation_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("external_veto_allowed must be false", validation["errors"])

    def test_value_autonomy_review_preserves_candidate_set_without_veto(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )

        review = monitor.build_value_autonomy_review_receipt(
            generation,
            witness_evidence_refs=[
                "evidence://self-model/value-generation/self-report-context/v1",
                "evidence://self-model/value-generation/council-boundary-note/v1",
            ],
            self_authorship_continuation_ref="authorship://self-model/value-generation/continuation-v1",
            council_review_ref="council://self-model/value-generation/advisory-boundary-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-lock-no-veto",
        )
        validation = monitor.validate_value_autonomy_review_receipt(review)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["candidate_set_unchanged"])
        self.assertEqual(
            generation["candidate_value_digest_set"],
            review["source_candidate_value_digest_set"],
        )
        self.assertTrue(review["future_self_acceptance_remains_required"])
        self.assertFalse(review["external_veto_allowed"])
        self.assertFalse(review["council_override_allowed"])
        self.assertFalse(review["candidate_rewrite_allowed"])
        self.assertFalse(review["raw_witness_payload_stored"])

    def test_value_autonomy_review_rejects_candidate_rewrite(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"curiosity": 0.71},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        review = monitor.build_value_autonomy_review_receipt(
            generation,
            witness_evidence_refs=[
                "evidence://self-model/value-generation/self-report-context/v1",
            ],
            self_authorship_continuation_ref="authorship://self-model/value-generation/continuation-v1",
            council_review_ref="council://self-model/value-generation/advisory-boundary-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-lock-no-veto",
        )
        tampered = copy.deepcopy(review)
        tampered["candidate_rewrite_allowed"] = True

        validation = monitor.validate_value_autonomy_review_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("candidate_rewrite_allowed must be false", validation["errors"])

    def test_value_acceptance_receipt_binds_future_self_writeback(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )

        acceptance = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=[
                "self-model://history/future-self-acceptance-window",
                "council://self-model/value-acceptance/boundary-only-review",
            ],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
            writeback_ref="self-model://writeback/value-generation/generative-patience/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/generative-patience/v1",
        )
        validation = monitor.validate_value_acceptance_receipt(acceptance)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["future_self_acceptance_satisfied"])
        self.assertTrue(validation["accepted_for_writeback"])
        self.assertTrue(validation["boundary_only_review"])
        self.assertTrue(validation["writeback_digest_bound"])
        self.assertFalse(acceptance["external_veto_allowed"])
        self.assertFalse(acceptance["raw_value_payload_stored"])

    def test_value_acceptance_rejects_external_candidate(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"curiosity": 0.71},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )

        with self.assertRaises(ValueError):
            monitor.build_value_acceptance_receipt(
                generation,
                accepted_value_refs=["value-candidate://self-model/external-imposition/v1"],
                continuity_recheck_refs=["self-model://history/future-self-acceptance-window"],
                future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
                council_resolution_ref="council://self-model/value-acceptance/boundary-only",
                guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
                writeback_ref="self-model://writeback/value-generation/external-imposition/v1",
                post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/external-imposition/v1",
            )

    def test_value_reassessment_receipt_retires_active_writeback_with_archive(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        acceptance = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/future-self-acceptance-window"],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
            writeback_ref="self-model://writeback/value-generation/generative-patience/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/generative-patience/v1",
        )

        reassessment = monitor.build_value_reassessment_receipt(
            acceptance,
            retired_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=[
                "self-model://history/life-history-reevaluation-window",
                "council://self-model/value-reassessment/boundary-only-review",
            ],
            future_self_reevaluation_ref="consent://self-model/value-reassessment/future-self-v1",
            council_resolution_ref="council://self-model/value-reassessment/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-reassessment/archive-retained",
            retirement_writeback_ref="self-model://writeback/value-retirement/generative-patience/v1",
            post_reassessment_snapshot_ref="self-model://snapshot/post-reassessment/generative-patience/v1",
            archival_snapshot_ref="self-model://archive/value-history/generative-patience/v1",
        )
        validation = monitor.validate_value_reassessment_receipt(reassessment)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["future_self_reevaluation_satisfied"])
        self.assertTrue(validation["active_writeback_retired"])
        self.assertTrue(validation["historical_value_archived"])
        self.assertTrue(validation["retirement_digest_bound"])
        self.assertFalse(reassessment["external_veto_allowed"])
        self.assertFalse(reassessment["raw_value_payload_stored"])

    def test_value_reassessment_rejects_non_accepted_value(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"curiosity": 0.71},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        acceptance = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/future-self-acceptance-window"],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
            writeback_ref="self-model://writeback/value-generation/generative-patience/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/generative-patience/v1",
        )

        with self.assertRaises(ValueError):
            monitor.build_value_reassessment_receipt(
                acceptance,
                retired_value_refs=["value-candidate://self-model/never-accepted/v1"],
                continuity_recheck_refs=["self-model://history/life-history-reevaluation-window"],
                future_self_reevaluation_ref="consent://self-model/value-reassessment/future-self-v1",
                council_resolution_ref="council://self-model/value-reassessment/boundary-only",
                guardian_boundary_ref="guardian://self-model/value-reassessment/archive-retained",
                retirement_writeback_ref="self-model://writeback/value-retirement/never-accepted/v1",
                post_reassessment_snapshot_ref="self-model://snapshot/post-reassessment/never-accepted/v1",
                archival_snapshot_ref="self-model://archive/value-history/never-accepted/v1",
            )

    def _build_value_timeline_for_archive_retention(self):
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        acceptance = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/future-self-acceptance-window"],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
            writeback_ref="self-model://writeback/value-generation/generative-patience/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/generative-patience/v1",
        )
        reassessment = monitor.build_value_reassessment_receipt(
            acceptance,
            retired_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/life-history-reevaluation-window"],
            future_self_reevaluation_ref="consent://self-model/value-reassessment/future-self-v1",
            council_resolution_ref="council://self-model/value-reassessment/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-reassessment/archive-retained",
            retirement_writeback_ref="self-model://writeback/value-retirement/generative-patience/v1",
            post_reassessment_snapshot_ref="self-model://snapshot/post-reassessment/generative-patience/v1",
            archival_snapshot_ref="self-model://archive/value-history/generative-patience/v1",
        )
        timeline = monitor.build_value_timeline_receipt(
            generation,
            acceptance_receipts=[acceptance],
            reassessment_receipts=[reassessment],
            continuity_audit_ref="self-model://history/value-lineage/audit/v1",
            council_resolution_ref="council://self-model/value-timeline/boundary-only",
            guardian_archive_ref="guardian://self-model/value-timeline/archive-retained",
        )
        return monitor, timeline

    def test_value_timeline_receipt_binds_lineage_and_archive_retention(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        acceptance = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/future-self-acceptance-window"],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
            writeback_ref="self-model://writeback/value-generation/generative-patience/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/generative-patience/v1",
        )
        reassessment = monitor.build_value_reassessment_receipt(
            acceptance,
            retired_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/life-history-reevaluation-window"],
            future_self_reevaluation_ref="consent://self-model/value-reassessment/future-self-v1",
            council_resolution_ref="council://self-model/value-reassessment/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-reassessment/archive-retained",
            retirement_writeback_ref="self-model://writeback/value-retirement/generative-patience/v1",
            post_reassessment_snapshot_ref="self-model://snapshot/post-reassessment/generative-patience/v1",
            archival_snapshot_ref="self-model://archive/value-history/generative-patience/v1",
        )

        timeline = monitor.build_value_timeline_receipt(
            generation,
            acceptance_receipts=[acceptance],
            reassessment_receipts=[reassessment],
            continuity_audit_ref="self-model://history/value-lineage/audit/v1",
            council_resolution_ref="council://self-model/value-timeline/boundary-only",
            guardian_archive_ref="guardian://self-model/value-timeline/archive-retained",
        )
        validation = monitor.validate_value_timeline_receipt(timeline)

        self.assertTrue(validation["ok"])
        self.assertEqual(["generated", "accepted", "retired"], [
            event["event_type"] for event in timeline["value_events"]
        ])
        self.assertEqual([], timeline["active_value_refs"])
        self.assertEqual(
            ["value-candidate://self-model/generative-patience/v1"],
            timeline["retired_value_refs"],
        )
        self.assertTrue(validation["active_retired_disjoint"])
        self.assertTrue(validation["archive_retention_required"])
        self.assertTrue(validation["timeline_commit_digest_bound"])
        self.assertFalse(timeline["external_veto_allowed"])
        self.assertFalse(timeline["raw_value_payload_stored"])

    def test_value_archive_retention_proof_binds_external_proofs(self) -> None:
        monitor, timeline = self._build_value_timeline_for_archive_retention()

        proof = monitor.build_value_archive_retention_proof_receipt(
            timeline,
            trustee_proof_refs=[
                "trustee-proof://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            long_term_storage_proof_refs=[
                "storage-proof://jp-13/self-model/value-archive/cold-ledger/v1",
            ],
            retention_policy_refs=[
                "retention-policy://jp-13/self-model/value-history/minimum-retention/v1",
            ],
            retrieval_test_refs=[
                "retrieval-test://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            continuity_audit_ref="self-model://history/value-archive-retention/audit/v1",
            council_resolution_ref="council://self-model/value-archive-retention/boundary-only",
            guardian_archive_ref="guardian://self-model/value-archive-retention/external-proof-bound",
        )
        validation = monitor.validate_value_archive_retention_proof_receipt(proof)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["timeline_archive_retention_verified"])
        self.assertTrue(validation["trustee_proof_bound"])
        self.assertTrue(validation["long_term_storage_proof_bound"])
        self.assertTrue(validation["retention_policy_bound"])
        self.assertTrue(validation["retrieval_test_bound"])
        self.assertTrue(validation["retention_commit_digest_bound"])
        self.assertEqual(
            timeline["receipt_digest"],
            proof["source_timeline_receipt_digest"],
        )
        self.assertEqual(
            timeline["archive_snapshot_refs"],
            proof["source_archive_snapshot_refs"],
        )
        self.assertFalse(proof["archive_deletion_allowed"])
        self.assertFalse(proof["raw_archive_payload_stored"])
        self.assertFalse(proof["raw_trustee_payload_stored"])

    def test_value_archive_retention_proof_rejects_archive_deletion(self) -> None:
        monitor, timeline = self._build_value_timeline_for_archive_retention()
        proof = monitor.build_value_archive_retention_proof_receipt(
            timeline,
            trustee_proof_refs=[
                "trustee-proof://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            long_term_storage_proof_refs=[
                "storage-proof://jp-13/self-model/value-archive/cold-ledger/v1",
            ],
            retention_policy_refs=[
                "retention-policy://jp-13/self-model/value-history/minimum-retention/v1",
            ],
            retrieval_test_refs=[
                "retrieval-test://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            continuity_audit_ref="self-model://history/value-archive-retention/audit/v1",
            council_resolution_ref="council://self-model/value-archive-retention/boundary-only",
            guardian_archive_ref="guardian://self-model/value-archive-retention/external-proof-bound",
        )
        tampered = copy.deepcopy(proof)
        tampered["archive_deletion_allowed"] = True

        validation = monitor.validate_value_archive_retention_proof_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("archive_deletion_allowed must be false", validation["errors"])

    def test_value_archive_retention_refresh_binds_expiry_and_revocation(self) -> None:
        monitor, timeline = self._build_value_timeline_for_archive_retention()
        proof = monitor.build_value_archive_retention_proof_receipt(
            timeline,
            trustee_proof_refs=[
                "trustee-proof://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            long_term_storage_proof_refs=[
                "storage-proof://jp-13/self-model/value-archive/cold-ledger/v1",
            ],
            retention_policy_refs=[
                "retention-policy://jp-13/self-model/value-history/minimum-retention/v1",
            ],
            retrieval_test_refs=[
                "retrieval-test://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            continuity_audit_ref="self-model://history/value-archive-retention/audit/v1",
            council_resolution_ref="council://self-model/value-archive-retention/boundary-only",
            guardian_archive_ref="guardian://self-model/value-archive-retention/external-proof-bound",
        )

        refresh = monitor.build_value_archive_retention_refresh_receipt(
            proof,
            refreshed_trustee_proof_refs=[
                "trustee-proof://jp-13/self-model/value-archive/generative-patience/refresh-2026q2",
            ],
            refreshed_long_term_storage_proof_refs=[
                "storage-proof://jp-13/self-model/value-archive/cold-ledger/refresh-2026q2",
            ],
            refreshed_retrieval_test_refs=[
                "retrieval-test://jp-13/self-model/value-archive/generative-patience/refresh-2026q2",
            ],
            revocation_registry_refs=[
                "revocation-registry://jp-13/self-model/value-archive/not-revoked/refresh-2026q2",
            ],
            proof_window_started_at_ref=(
                "time-window://self-model/value-archive-retention/2026q2/start"
            ),
            proof_window_expires_at_ref=(
                "time-window://self-model/value-archive-retention/2026q2/expires"
            ),
            refresh_deadline_ref=(
                "schedule://self-model/value-archive-retention/refresh-before-90d"
            ),
            refreshed_at_ref="timestamp://self-model/value-archive-retention/refresh-2026q2",
            continuity_audit_ref="self-model://history/value-archive-retention/refresh-audit/v1",
            council_resolution_ref=(
                "council://self-model/value-archive-retention-refresh/boundary-only"
            ),
            guardian_archive_ref=(
                "guardian://self-model/value-archive-retention-refresh/not-revoked"
            ),
        )
        validation = monitor.validate_value_archive_retention_refresh_receipt(refresh)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["refresh_window_bound"])
        self.assertTrue(validation["revocation_check_bound"])
        self.assertTrue(validation["retention_policy_still_bound"])
        self.assertTrue(validation["expiry_fail_closed"])
        self.assertTrue(validation["refresh_commit_digest_bound"])
        self.assertEqual(90, refresh["freshness_window_days"])
        self.assertEqual(proof["receipt_digest"], refresh["source_proof_receipt_digest"])
        self.assertFalse(refresh["source_proof_revoked"])
        self.assertFalse(refresh["expired_source_proof_accepted"])
        self.assertFalse(refresh["archive_deletion_allowed"])
        self.assertFalse(refresh["raw_revocation_payload_stored"])

    def test_value_archive_retention_refresh_rejects_revoked_source_proof(self) -> None:
        monitor, timeline = self._build_value_timeline_for_archive_retention()
        proof = monitor.build_value_archive_retention_proof_receipt(
            timeline,
            trustee_proof_refs=[
                "trustee-proof://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            long_term_storage_proof_refs=[
                "storage-proof://jp-13/self-model/value-archive/cold-ledger/v1",
            ],
            retention_policy_refs=[
                "retention-policy://jp-13/self-model/value-history/minimum-retention/v1",
            ],
            retrieval_test_refs=[
                "retrieval-test://jp-13/self-model/value-archive/generative-patience/v1",
            ],
            continuity_audit_ref="self-model://history/value-archive-retention/audit/v1",
            council_resolution_ref="council://self-model/value-archive-retention/boundary-only",
            guardian_archive_ref="guardian://self-model/value-archive-retention/external-proof-bound",
        )
        refresh = monitor.build_value_archive_retention_refresh_receipt(
            proof,
            refreshed_trustee_proof_refs=[
                "trustee-proof://jp-13/self-model/value-archive/generative-patience/refresh-2026q2",
            ],
            refreshed_long_term_storage_proof_refs=[
                "storage-proof://jp-13/self-model/value-archive/cold-ledger/refresh-2026q2",
            ],
            refreshed_retrieval_test_refs=[
                "retrieval-test://jp-13/self-model/value-archive/generative-patience/refresh-2026q2",
            ],
            revocation_registry_refs=[
                "revocation-registry://jp-13/self-model/value-archive/not-revoked/refresh-2026q2",
            ],
            proof_window_started_at_ref=(
                "time-window://self-model/value-archive-retention/2026q2/start"
            ),
            proof_window_expires_at_ref=(
                "time-window://self-model/value-archive-retention/2026q2/expires"
            ),
            refresh_deadline_ref=(
                "schedule://self-model/value-archive-retention/refresh-before-90d"
            ),
            refreshed_at_ref="timestamp://self-model/value-archive-retention/refresh-2026q2",
            continuity_audit_ref="self-model://history/value-archive-retention/refresh-audit/v1",
            council_resolution_ref=(
                "council://self-model/value-archive-retention-refresh/boundary-only"
            ),
            guardian_archive_ref=(
                "guardian://self-model/value-archive-retention-refresh/not-revoked"
            ),
        )
        tampered = copy.deepcopy(refresh)
        tampered["source_proof_revoked"] = True

        validation = monitor.validate_value_archive_retention_refresh_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("source_proof_revoked must be false", validation["errors"])

    def test_value_timeline_rejects_reassessment_without_timeline_acceptance(self) -> None:
        monitor = SelfModelMonitor()
        observation = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity"],
                goals=["safe-self-construction"],
                traits={"curiosity": 0.71},
            )
        )
        generation = monitor.build_value_generation_receipt(
            observation,
            candidate_value_refs=[
                "value-candidate://self-model/generative-patience/v1",
                "value-candidate://self-model/reciprocal-curiosity/v1",
            ],
            continuity_context_refs=["self-model://history/stable-drift-window"],
            self_authorship_ref="authorship://self-model/value-generation/self-authored-v1",
            self_consent_ref="consent://self-model/value-generation/proposal-v1",
            council_review_ref="council://self-model/value-generation/advisory-only",
            guardian_boundary_ref="guardian://self-model/value-generation/no-external-veto",
        )
        accepted_generation = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/generative-patience/v1"],
            continuity_recheck_refs=["self-model://history/future-self-acceptance-window"],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v1",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto",
            writeback_ref="self-model://writeback/value-generation/generative-patience/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/generative-patience/v1",
        )
        omitted_acceptance = monitor.build_value_acceptance_receipt(
            generation,
            accepted_value_refs=["value-candidate://self-model/reciprocal-curiosity/v1"],
            continuity_recheck_refs=["self-model://history/future-self-acceptance-window-2"],
            future_self_acceptance_ref="consent://self-model/value-acceptance/future-self-v2",
            council_resolution_ref="council://self-model/value-acceptance/boundary-only-2",
            guardian_boundary_ref="guardian://self-model/value-acceptance/no-external-veto-2",
            writeback_ref="self-model://writeback/value-generation/reciprocal-curiosity/v1",
            post_acceptance_snapshot_ref="self-model://snapshot/post-acceptance/reciprocal-curiosity/v1",
        )
        reassessment = monitor.build_value_reassessment_receipt(
            omitted_acceptance,
            retired_value_refs=["value-candidate://self-model/reciprocal-curiosity/v1"],
            continuity_recheck_refs=["self-model://history/life-history-reevaluation-window"],
            future_self_reevaluation_ref="consent://self-model/value-reassessment/future-self-v1",
            council_resolution_ref="council://self-model/value-reassessment/boundary-only",
            guardian_boundary_ref="guardian://self-model/value-reassessment/archive-retained",
            retirement_writeback_ref="self-model://writeback/value-retirement/reciprocal-curiosity/v1",
            post_reassessment_snapshot_ref="self-model://snapshot/post-reassessment/reciprocal-curiosity/v1",
            archival_snapshot_ref="self-model://archive/value-history/reciprocal-curiosity/v1",
        )

        with self.assertRaises(ValueError):
            monitor.build_value_timeline_receipt(
                generation,
                acceptance_receipts=[accepted_generation],
                reassessment_receipts=[reassessment],
                continuity_audit_ref="self-model://history/value-lineage/audit/v1",
                council_resolution_ref="council://self-model/value-timeline/boundary-only",
                guardian_archive_ref="guardian://self-model/value-timeline/archive-retained",
            )


if __name__ == "__main__":
    unittest.main()
