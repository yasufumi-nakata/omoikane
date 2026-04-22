from __future__ import annotations

import unittest

from omoikane.interface.ewa import ExternalWorldAgentController


class ExternalWorldAgentControllerTests(unittest.TestCase):
    def _build_authorized_reversible_context(self) -> dict[str, object]:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-01",
            "reposition a lantern for inspection",
        )
        motor_plan = controller.prepare_motor_plan(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            guardian_observed=True,
            actuator_profile_id="device://ewa-arm-01/profile/articulated-inspection-arm-v1",
            actuator_group="inspection-arm",
            motion_profile="cartesian-reposition-v1",
            target_pose_ref="pose://lantern/reposition-window-a",
            safety_zone_ref="zone://inspection/perimeter-a",
            rollback_vector_ref="rollback://lantern/reposition-window-a",
            max_linear_speed_mps=0.08,
            max_force_newton=6.5,
            hold_timeout_ms=1200,
        )
        motor_plan_validation = controller.validate_motor_plan(
            motor_plan,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
        )
        legal_execution = controller.execute_legal_preflight(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            reversibility="reversible",
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/inspection-safe-reposition/v1",
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-001",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            notice_authority_ref="authority://jp-13/lab-robotics-oversight-desk",
            liability_mode="joint",
            escalation_contact="mailto:ewa-oversight@example.invalid",
            valid_for_seconds=360,
        )
        legal_execution_validation = controller.validate_legal_execution(
            legal_execution,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            reversibility="reversible",
        )
        authorization = controller.authorize(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without permanent change",
            ethics_attestation_id="ethics://ewa/approved-001",
            motor_plan_id=motor_plan["plan_id"],
            legal_execution_id=legal_execution["execution_id"],
            guardian_observed=True,
            intent_confidence=0.94,
        )
        authorization_validation = controller.validate_authorization(
            authorization,
            motor_plan=motor_plan,
            legal_execution=legal_execution,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            intent_summary="reposition lantern for inspection without permanent change",
            reversibility="reversible",
        )
        return {
            "controller": controller,
            "handle": handle,
            "motor_plan": motor_plan,
            "motor_plan_validation": motor_plan_validation,
            "legal_execution": legal_execution,
            "legal_execution_validation": legal_execution_validation,
            "authorization": authorization,
            "authorization_validation": authorization_validation,
        }

    def test_reversible_command_requires_motor_plan_legal_execution_authorization_guardian_observation_and_release(
        self,
    ) -> None:
        context = self._build_authorized_reversible_context()
        controller = context["controller"]
        handle = context["handle"]
        motor_plan = context["motor_plan"]
        legal_execution = context["legal_execution"]
        authorization = context["authorization"]
        authorization_validation = context["authorization_validation"]

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

        self.assertTrue(context["motor_plan_validation"]["ok"])
        self.assertTrue(context["motor_plan_validation"]["plan_ready"])
        self.assertTrue(context["legal_execution_validation"]["ok"])
        self.assertTrue(context["legal_execution_validation"]["execution_ready"])
        self.assertTrue(authorization_validation["ok"])
        self.assertTrue(authorization_validation["motor_plan_ready"])
        self.assertTrue(authorization_validation["legal_execution_ready"])
        self.assertTrue(authorization_validation["motor_plan_bound"])
        self.assertTrue(authorization_validation["legal_execution_bound"])
        self.assertEqual("physical-device-actuation", authorization_validation["delivery_scope"])
        self.assertEqual("executed", approved["status"])
        self.assertEqual("reversible", approved["reversibility"])
        self.assertEqual(
            authorization["authorization_id"],
            approved["approval_path"]["authorization_id"],
        )
        self.assertEqual(motor_plan["plan_id"], approved["motor_plan_id"])
        self.assertEqual(motor_plan["plan_digest"], approved["motor_plan_digest"])
        self.assertEqual(legal_execution["execution_id"], approved["legal_execution_id"])
        self.assertEqual(legal_execution["digest"], approved["legal_execution_digest"])
        self.assertEqual("held", observed["safety_status"])
        self.assertEqual("released", released["status"])
        self.assertEqual("released", snapshot["status"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["summary_only_audit"])
        self.assertTrue(validation["actuation_authorization_bound"])
        self.assertTrue(validation["motor_plan_bound"])
        self.assertTrue(validation["legal_execution_bound"])
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

    def test_authorization_rejects_mismatched_motor_plan(self) -> None:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-04",
            "reposition a lantern for bounded inspection",
        )
        motor_plan = controller.prepare_motor_plan(
            handle["handle_id"],
            command_id="ewa-command-plan-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            guardian_observed=True,
            actuator_profile_id="device://ewa-arm-04/profile/articulated-inspection-arm-v1",
            actuator_group="inspection-arm",
            motion_profile="cartesian-reposition-v1",
            target_pose_ref="pose://lantern/reposition-window-a",
            safety_zone_ref="zone://inspection/perimeter-a",
            rollback_vector_ref="rollback://lantern/reposition-window-a",
            max_linear_speed_mps=0.08,
            max_force_newton=6.5,
            hold_timeout_ms=1200,
        )
        legal_execution = controller.execute_legal_preflight(
            handle["handle_id"],
            command_id="ewa-command-authorize-001",
            reversibility="reversible",
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/inspection-safe-reposition/v1",
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-002",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            notice_authority_ref="authority://jp-13/lab-robotics-oversight-desk",
            liability_mode="joint",
            escalation_contact="mailto:ewa-oversight@example.invalid",
            valid_for_seconds=360,
        )

        with self.assertRaisesRegex(ValueError, "motor plan command_id"):
            controller.authorize(
                handle["handle_id"],
                command_id="ewa-command-authorize-001",
                instruction="move the inspection arm two centimeters to reposition the lantern",
                reversibility="reversible",
                intent_summary="reposition lantern for bounded inspection without permanent change",
                ethics_attestation_id="ethics://ewa/approved-003",
                motor_plan_id=motor_plan["plan_id"],
                legal_execution_id=legal_execution["execution_id"],
                guardian_observed=True,
                intent_confidence=0.95,
            )

    def test_emergency_stop_latches_safe_state_and_blocks_further_actuation(self) -> None:
        context = self._build_authorized_reversible_context()
        controller = context["controller"]
        handle = context["handle"]
        authorization = context["authorization"]
        motor_plan = context["motor_plan"]
        legal_execution = context["legal_execution"]

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
        stop = controller.emergency_stop(
            handle["handle_id"],
            trigger_source="watchdog-timeout",
            reason="latency watchdog exceeded bounded threshold during lantern reposition",
        )
        stop_validation = controller.validate_emergency_stop(stop)
        veto = controller.command(
            handle["handle_id"],
            command_id="ewa-command-after-stop-001",
            instruction="move the inspection arm one centimeter to the right",
            reversibility="reversible",
            intent_summary="retry the bounded reposition after stop",
            ethics_attestation_id="ethics://ewa/approved-003",
            guardian_observed=True,
            intent_confidence=0.95,
            authorization_id=authorization["authorization_id"],
        )
        released = controller.release(
            handle["handle_id"],
            reason="emergency stop latched safe state; release before reuse",
        )
        snapshot = controller.snapshot(handle["handle_id"])
        validation = controller.validate_handle(snapshot)

        self.assertEqual("executed", approved["status"])
        self.assertEqual(motor_plan["plan_id"], approved["motor_plan_id"])
        self.assertEqual(legal_execution["execution_id"], approved["legal_execution_id"])
        self.assertTrue(stop_validation["ok"])
        self.assertTrue(stop_validation["safe_state_latched"])
        self.assertTrue(stop_validation["hardware_interlock_engaged"])
        self.assertTrue(stop_validation["authorization_bound"])
        self.assertEqual("watchdog-timeout", stop["trigger_source"])
        self.assertEqual(approved["command_id"], stop["command_id"])
        self.assertEqual(approved["instruction_digest"], stop["bound_command_digest"])
        self.assertEqual(authorization["authorization_id"], stop["authorization_id"])
        self.assertEqual(authorization["authorization_digest"], stop["bound_authorization_digest"])
        self.assertEqual("vetoed", veto["status"])
        self.assertEqual(
            "handle is latched in emergency stop; release required before further actuation",
            veto["reason"],
        )
        self.assertEqual("released", released["status"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["motor_plan_bound"])
        self.assertTrue(validation["legal_execution_bound"])
        self.assertTrue(validation["emergency_stop_release_sequence_valid"])


if __name__ == "__main__":
    unittest.main()
