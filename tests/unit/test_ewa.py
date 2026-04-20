from __future__ import annotations

import unittest

from omoikane.interface.ewa import ExternalWorldAgentController


class ExternalWorldAgentControllerTests(unittest.TestCase):
    def test_reversible_command_requires_authorization_guardian_observation_and_release(self) -> None:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-01",
            "reposition a lantern for inspection",
        )
        authorization = controller.authorize(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without permanent change",
            ethics_attestation_id="ethics://ewa/approved-001",
            guardian_observed=True,
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/inspection-safe-reposition/v1",
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-001",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            intent_confidence=0.94,
        )
        authorization_validation = controller.validate_authorization(
            authorization,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            intent_summary="reposition lantern for inspection without permanent change",
            reversibility="reversible",
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
            authorization_id=authorization["authorization_id"],
        )
        observed = controller.observe(handle["handle_id"])
        released = controller.release(
            handle["handle_id"],
            reason="completed bounded inspection",
        )
        snapshot = controller.snapshot(handle["handle_id"])
        validation = controller.validate_handle(snapshot)

        self.assertTrue(authorization_validation["ok"])
        self.assertTrue(authorization_validation["authorization_ready"])
        self.assertEqual("physical-device-actuation", authorization_validation["delivery_scope"])
        self.assertEqual("executed", approved["status"])
        self.assertEqual("reversible", approved["reversibility"])
        self.assertEqual(
            authorization["authorization_id"],
            approved["approval_path"]["authorization_id"],
        )
        self.assertEqual("held", observed["safety_status"])
        self.assertEqual("released", released["status"])
        self.assertEqual("released", snapshot["status"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["summary_only_audit"])
        self.assertTrue(validation["actuation_authorization_bound"])
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

    def test_non_read_only_command_without_authorization_is_vetoed(self) -> None:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-03",
            "reposition a lantern for inspection",
        )

        veto = controller.command(
            handle["handle_id"],
            command_id="ewa-command-missing-auth-001",
            instruction="move the inspection arm one centimeter to the left",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without permanent change",
            ethics_attestation_id="ethics://ewa/approved-002",
            guardian_observed=True,
            intent_confidence=0.95,
        )

        self.assertEqual("vetoed", veto["status"])
        self.assertEqual(
            "non-read-only commands require external actuation authorization artifact",
            veto["reason"],
        )


if __name__ == "__main__":
    unittest.main()
