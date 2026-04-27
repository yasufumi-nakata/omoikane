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


if __name__ == "__main__":
    unittest.main()
