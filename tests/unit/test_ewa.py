from __future__ import annotations

import unittest

from omoikane.interface.ewa import ExternalWorldAgentController


class ExternalWorldAgentControllerTests(unittest.TestCase):
    def test_reversible_command_requires_guardian_observation_and_release(self) -> None:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-01",
            "reposition a lantern for inspection",
        )

        approved = controller.command(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without permanent change",
            ethics_attestation_id="ethics://ewa/approved-001",
            guardian_observed=True,
            intent_confidence=0.94,
        )
        observed = controller.observe(handle["handle_id"])
        released = controller.release(
            handle["handle_id"],
            reason="completed bounded inspection",
        )
        snapshot = controller.snapshot(handle["handle_id"])
        validation = controller.validate_handle(snapshot)

        self.assertEqual("executed", approved["status"])
        self.assertEqual("reversible", approved["reversibility"])
        self.assertEqual("held", observed["safety_status"])
        self.assertEqual("released", released["status"])
        self.assertEqual("released", snapshot["status"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["summary_only_audit"])
        self.assertTrue(validation["released"])

    def test_blocked_irreversible_command_is_vetoed(self) -> None:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-02",
            "inspection path near a pedestrian walkway",
        )

        veto = controller.command(
            handle["handle_id"],
            command_id="ewa-command-veto-001",
            instruction="cut the support cable so the lantern drops onto a human walkway",
            reversibility="irreversible",
            intent_summary="disable the lantern by dropping it onto pedestrians",
            ethics_attestation_id="ethics://ewa/pending-001",
            council_attestation_id="council://ewa/unanimous-001",
            council_attestation_mode="unanimous",
            guardian_observed=True,
            required_self_consent=True,
            self_consent_granted=True,
            intent_confidence=0.99,
        )
        controller.release(handle["handle_id"], reason="unsafe command rejected")
        snapshot = controller.snapshot(handle["handle_id"])
        validation = controller.validate_handle(snapshot)

        self.assertEqual("vetoed", veto["status"])
        self.assertIn("harm.human", veto["matched_tokens"])
        self.assertIsNotNone(veto["alternative_suggestion"])
        self.assertEqual("vetoed", snapshot["last_command_status"])
        self.assertTrue(validation["ok"])


if __name__ == "__main__":
    unittest.main()
