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


if __name__ == "__main__":
    unittest.main()
