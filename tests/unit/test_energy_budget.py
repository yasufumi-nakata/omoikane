from __future__ import annotations

import unittest

from omoikane.kernel.energy_budget import EnergyBudgetService
from omoikane.substrate.adapter import ClassicalSiliconAdapter


class EnergyBudgetTests(unittest.TestCase):
    def test_economic_pressure_cannot_lower_floor(self) -> None:
        service = EnergyBudgetService()
        floor = {
            "identity_id": "identity://energy-budget/unit",
            "minimum_joules_per_second": 30,
            "workload_class": "migration",
            "evaluated_at": "2026-04-25T00:00:00+00:00",
        }
        broker_signal = {
            "signal_id": "broker-signal-unit",
            "identity_id": "identity://energy-budget/unit",
            "minimum_joules_per_second": 30,
            "severity": "critical",
            "recommended_action": "migrate-standby",
        }

        receipt = service.evaluate_floor(
            identity_id="identity://energy-budget/unit",
            workload_class="migration",
            requested_budget_jps=22,
            observed_capacity_jps=28,
            energy_floor=floor,
            broker_signal=broker_signal,
        )
        validation = service.validate_floor_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(receipt["economic_pressure_detected"])
        self.assertTrue(receipt["floor_preserved"])
        self.assertEqual(30, receipt["granted_budget_jps"])
        self.assertFalse(receipt["degradation_allowed"])
        self.assertTrue(receipt["scheduler_signal_required"])
        self.assertEqual("migrate-standby", receipt["broker_recommended_action"])
        self.assertTrue(receipt["broker_signal_bound"])
        self.assertFalse(receipt["raw_economic_payload_stored"])

    def test_accepts_budget_above_floor_without_broker_signal(self) -> None:
        service = EnergyBudgetService()
        receipt = service.evaluate_floor(
            identity_id="identity://energy-budget/above-floor",
            workload_class="baseline",
            requested_budget_jps=ClassicalSiliconAdapter.minimum_energy_floor_for("baseline") + 4,
            observed_capacity_jps=24,
        )
        validation = service.validate_floor_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertFalse(receipt["economic_pressure_detected"])
        self.assertEqual("accepted", receipt["budget_status"])
        self.assertTrue(receipt["degradation_allowed"])
        self.assertFalse(receipt["scheduler_signal_required"])
        self.assertIsNone(receipt["broker_signal_ref"])

    def test_validation_rejects_tampered_floor(self) -> None:
        service = EnergyBudgetService()
        receipt = service.evaluate_floor(
            identity_id="identity://energy-budget/tamper",
            workload_class="migration",
            requested_budget_jps=22,
            observed_capacity_jps=32,
        )
        receipt["granted_budget_jps"] = 12

        validation = service.validate_floor_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertIn(
            "granted_budget_jps must never fall below the energy floor",
            validation["errors"],
        )
        self.assertIn("digest must match receipt payload", validation["errors"])

    def test_pool_blocks_cross_identity_floor_offset(self) -> None:
        service = EnergyBudgetService()
        pressured_signal = {
            "signal_id": "broker-signal-pool-a",
            "identity_id": "identity://energy-budget/pool-a",
            "minimum_joules_per_second": 30,
            "severity": "critical",
            "recommended_action": "migrate-standby",
        }

        receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://unit",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/pool-a",
                    "workload_class": "migration",
                    "requested_budget_jps": 22,
                    "observed_capacity_jps": 28,
                    "broker_signal": pressured_signal,
                },
                {
                    "identity_id": "identity://energy-budget/pool-b",
                    "workload_class": "council",
                    "requested_budget_jps": 38,
                    "observed_capacity_jps": 32,
                },
            ],
        )
        validation = service.validate_pool_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertEqual(2, receipt["member_count"])
        self.assertTrue(receipt["aggregate_requested_covers_floor"])
        self.assertEqual(1, receipt["member_economic_pressure_count"])
        self.assertTrue(receipt["pool_economic_pressure_detected"])
        self.assertTrue(receipt["per_identity_floor_preserved"])
        self.assertTrue(receipt["pool_floor_preserved"])
        self.assertFalse(receipt["cross_identity_subsidy_allowed"])
        self.assertTrue(receipt["cross_identity_floor_offset_blocked"])
        self.assertEqual("floor-protected", receipt["pool_budget_status"])
        self.assertFalse(receipt["degradation_allowed"])
        self.assertTrue(receipt["broker_signal_bound"])
        self.assertEqual(
            receipt["receipt_member_digests"],
            [member["digest"] for member in receipt["member_receipts"]],
        )

    def test_pool_validation_rejects_tampered_member_digest_set(self) -> None:
        service = EnergyBudgetService()
        receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://tamper",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/pool-a",
                    "workload_class": "baseline",
                    "requested_budget_jps": 16,
                    "observed_capacity_jps": 16,
                }
            ],
        )
        receipt["receipt_member_digest_set"] = "0" * 64

        validation = service.validate_pool_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertIn(
            "receipt_member_digest_set must match ordered member digests",
            validation["errors"],
        )
        self.assertIn("digest must match pool receipt payload", validation["errors"])

    def test_voluntary_subsidy_accepts_consent_bound_surplus_after_floor_guard(self) -> None:
        service = EnergyBudgetService()
        pressured_signal = {
            "signal_id": "broker-signal-subsidy-a",
            "identity_id": "identity://energy-budget/subsidy-a",
            "minimum_joules_per_second": 30,
            "severity": "critical",
            "recommended_action": "migrate-standby",
        }
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://subsidy",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/subsidy-a",
                    "workload_class": "migration",
                    "requested_budget_jps": 22,
                    "observed_capacity_jps": 28,
                    "broker_signal": pressured_signal,
                },
                {
                    "identity_id": "identity://energy-budget/subsidy-b",
                    "workload_class": "council",
                    "requested_budget_jps": 38,
                    "observed_capacity_jps": 32,
                },
            ],
        )

        receipt = service.evaluate_voluntary_subsidy(
            pool_receipt=pool_receipt,
            subsidy_offers=[
                {
                    "donor_identity_id": "identity://energy-budget/subsidy-b",
                    "recipient_identity_id": "identity://energy-budget/subsidy-a",
                    "offered_jps": 8,
                    "consent_ref": "consent://energy-budget/subsidy-b-to-a/v1",
                    "revocation_ref": "revocation://energy-budget/subsidy-b-to-a/v1",
                    "max_duration_ms": 60_000,
                }
            ],
            external_funding_policy_ref="funding-policy://energy-budget/unit-subsidy/v1",
            funding_policy_signature_ref="signature://energy-budget/unit-subsidy/v1",
        )
        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(receipt["voluntary_subsidy_allowed"])
        self.assertEqual("accepted", receipt["subsidy_status"])
        self.assertTrue(receipt["floor_protection_preserved"])
        self.assertTrue(receipt["donor_floor_preserved"])
        self.assertTrue(receipt["all_consent_digests_valid"])
        self.assertFalse(receipt["cross_identity_offset_used"])
        self.assertFalse(receipt["raw_funding_payload_stored"])
        self.assertEqual(8, receipt["total_accepted_jps"])

    def test_voluntary_subsidy_validation_rejects_tampered_consent_digest(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://subsidy-tamper",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/subsidy-a",
                    "workload_class": "migration",
                    "requested_budget_jps": 22,
                    "observed_capacity_jps": 30,
                },
                {
                    "identity_id": "identity://energy-budget/subsidy-b",
                    "workload_class": "council",
                    "requested_budget_jps": 38,
                    "observed_capacity_jps": 32,
                },
            ],
        )
        receipt = service.evaluate_voluntary_subsidy(
            pool_receipt=pool_receipt,
            subsidy_offers=[
                {
                    "donor_identity_id": "identity://energy-budget/subsidy-b",
                    "recipient_identity_id": "identity://energy-budget/subsidy-a",
                    "offered_jps": 8,
                    "consent_ref": "consent://energy-budget/subsidy-b-to-a/v1",
                    "revocation_ref": "revocation://energy-budget/subsidy-b-to-a/v1",
                }
            ],
        )
        receipt["subsidy_offers"][0]["consent_digest"] = "0" * 64

        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertIn("offer consent_digest_valid mismatch", validation["errors"])
        self.assertIn("all_consent_digests_valid mismatch", validation["errors"])
        self.assertIn("digest must match voluntary subsidy receipt payload", validation["errors"])


if __name__ == "__main__":
    unittest.main()
