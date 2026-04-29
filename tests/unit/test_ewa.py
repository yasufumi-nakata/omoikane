from __future__ import annotations

import unittest

from omoikane.interface.ewa import ExternalWorldAgentController


class ExternalWorldAgentControllerTests(unittest.TestCase):
    def _build_network_oversight_event(
        self,
        *,
        command_id: str,
        legal_execution: dict[str, object],
    ) -> dict[str, object]:
        return {
            "event_id": "guardian-oversight-event-ewa-001",
            "payload_ref": f"ledger://ewa/{command_id}/guardian-review",
            "guardian_role": "integrity",
            "category": "attest",
            "human_attestation": {
                "required_quorum": 2,
                "received_quorum": 2,
                "reviewers": ["human-reviewer-alpha", "human-reviewer-beta"],
                "status": "satisfied",
            },
            "reviewer_bindings": [
                {
                    "reviewer_id": "human-reviewer-alpha",
                    "verification_id": legal_execution["guardian_verification_id"],
                    "verifier_ref": legal_execution["guardian_verifier_ref"],
                    "network_receipt_id": "verifier-network-receipt-alpha",
                    "transport_exchange_digest": "1" * 64,
                    "authority_chain_ref": "authority://guardian-oversight.jp/reviewer-attestation",
                    "trust_root_ref": "root://guardian-oversight.jp/reviewer-live-pki",
                    "trust_root_digest": "2" * 64,
                    "legal_execution_id": "guardian-legal-execution-alpha",
                    "legal_execution_digest": "3" * 64,
                    "legal_policy_ref": "policy://guardian-oversight/jp-13/reviewer-attestation/v1",
                    "jurisdiction_bundle_ref": legal_execution["jurisdiction_bundle_ref"],
                    "jurisdiction_bundle_digest": legal_execution["jurisdiction_bundle_digest"],
                    "guardian_role": "integrity",
                    "category": "attest",
                },
                {
                    "reviewer_id": "human-reviewer-beta",
                    "verification_id": "reviewer-verification-beta",
                    "verifier_ref": "verifier://guardian-oversight.jp/reviewer-beta",
                    "network_receipt_id": "verifier-network-receipt-beta",
                    "transport_exchange_digest": "4" * 64,
                    "authority_chain_ref": "authority://guardian-oversight.jp/reviewer-attestation",
                    "trust_root_ref": "root://guardian-oversight.jp/reviewer-live-pki",
                    "trust_root_digest": "5" * 64,
                    "legal_execution_id": "guardian-legal-execution-beta",
                    "legal_execution_digest": "6" * 64,
                    "legal_policy_ref": "policy://guardian-oversight/jp-13/reviewer-attestation/v1",
                    "jurisdiction_bundle_ref": legal_execution["jurisdiction_bundle_ref"],
                    "jurisdiction_bundle_digest": legal_execution["jurisdiction_bundle_digest"],
                    "guardian_role": "integrity",
                    "category": "attest",
                },
            ],
        }

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
        stop_signal_path = controller.prepare_stop_signal_path(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            motor_plan_id=motor_plan["plan_id"],
            kill_switch_wiring_ref="wiring://ewa-arm-01/emergency-stop-loop/v1",
            stop_signal_bus_ref="stop-bus://ewa-arm-01/emergency-latch/v1",
            interlock_controller_ref="interlock://ewa-arm-01/safety-plc",
        )
        stop_signal_path_validation = controller.validate_stop_signal_path(
            stop_signal_path,
            motor_plan=motor_plan,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
        )
        stop_signal_adapter_receipt = controller.probe_stop_signal_adapter(
            stop_signal_path["path_id"],
            adapter_endpoint_ref="plc://ewa-arm-01/safety-plc/loopback-probe",
            firmware_image_ref="firmware://ewa-arm-01/safety-plc/v1.4.2",
            firmware_digest=f"sha256:{'a' * 64}",
            plc_program_ref="plc-program://ewa-arm-01/emergency-latch/v3",
            plc_program_digest=f"sha256:{'b' * 64}",
        )
        stop_signal_adapter_validation = controller.validate_stop_signal_adapter_receipt(
            stop_signal_adapter_receipt,
            stop_signal_path=stop_signal_path,
        )
        production_connector_attestation = controller.attest_production_connector(
            stop_signal_adapter_receipt["receipt_id"],
            vendor_api_ref="vendor-api://ewa-arm-01/safety-plc/v1",
            vendor_api_certificate_ref="vendor-cert://ewa-arm-01/safety-plc/prod-connector",
            vendor_api_certificate_digest=f"sha256:{'c' * 64}",
            production_connector_ref="connector://ewa-arm-01/safety-plc/production-v1",
            installation_site_ref="site://ewa-test-cell/a",
            installation_proof_ref="install-proof://ewa-arm-01/safety-plc/2026-04-26",
            installation_proof_digest=f"sha256:{'d' * 64}",
            installer_authority_ref="authority://jp-13/lab-safety-plc-installers",
            safety_plc_ref="plc://ewa-arm-01/safety-plc",
            maintenance_window_ref="maintenance://ewa-arm-01/safety-plc/2026q2",
        )
        production_connector_validation = controller.validate_production_connector_attestation(
            production_connector_attestation,
            stop_signal_adapter_receipt=stop_signal_adapter_receipt,
        )
        legal_execution = controller.execute_legal_preflight(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            reversibility="reversible",
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/inspection-safe-reposition/v1",
            guardian_verification_id="reviewer-verification-ewa-001",
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-001",
            guardian_verifier_ref="verifier://guardian-oversight.jp/reviewer-omega",
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
        regulator_permit_verifier_receipt = controller.verify_regulator_permit(
            legal_execution["execution_id"],
            permit_authority_ref="authority://jp-13/lab-robotics-permit-desk",
            permit_record_ref="permit://jp-13/ewa-arm-01/reposition/v1",
            permit_record_digest=f"sha256:{'a' * 64}",
            permit_scope_ref="permit-scope://physical-device-actuation/inspection-arm",
            permit_class="lab-inspection-physical-actuation",
            verifier_jurisdiction="JP-13",
            regulator_api_endpoint_ref="https://regulator.invalid/jp-13/ewa/permits/readback",
            regulator_api_response_digest=f"sha256:{'b' * 64}",
            regulator_api_certificate_ref="cert://jp-13/lab-robotics-permit-desk/api",
            regulator_api_certificate_digest=f"sha256:{'c' * 64}",
            verifier_key_ref="verifier-key://jp-13/lab-robotics-permit-desk/2026q2",
            verifier_key_digest=f"sha256:{'d' * 64}",
        )
        backup_regulator_permit_verifier_receipt = controller.verify_regulator_permit(
            legal_execution["execution_id"],
            permit_authority_ref="authority://sg-01/lab-robotics-permit-mirror",
            permit_record_ref="permit://sg-01/ewa-arm-01/reposition/v1",
            permit_record_digest=f"sha256:{'1' * 64}",
            permit_scope_ref="permit-scope://physical-device-actuation/inspection-arm",
            permit_class="lab-inspection-physical-actuation",
            verifier_jurisdiction="SG-01",
            regulator_api_endpoint_ref="https://regulator.invalid/sg-01/ewa/permits/readback",
            regulator_api_response_digest=f"sha256:{'2' * 64}",
            regulator_api_certificate_ref="cert://sg-01/lab-robotics-permit-mirror/api",
            regulator_api_certificate_digest=f"sha256:{'3' * 64}",
            verifier_key_ref="verifier-key://sg-01/lab-robotics-permit-mirror/2026q2",
            verifier_key_digest=f"sha256:{'4' * 64}",
        )
        regulator_permit_validation = controller.validate_regulator_permit_verifier_receipt(
            regulator_permit_verifier_receipt,
            legal_execution=legal_execution,
        )
        backup_regulator_permit_validation = (
            controller.validate_regulator_permit_verifier_receipt(
                backup_regulator_permit_verifier_receipt,
                legal_execution=legal_execution,
            )
        )
        regulator_permit_quorum_receipt = controller.verify_regulator_permit_quorum(
            legal_execution["execution_id"],
            permit_receipt_ids=[
                regulator_permit_verifier_receipt["receipt_id"],
                backup_regulator_permit_verifier_receipt["receipt_id"],
            ],
            permit_class="lab-inspection-physical-actuation",
            threshold_policy_ref="policy://ewa/regulator-permit/lab-inspection-actuation-threshold/v1",
            threshold_policy_digest=f"sha256:{'5' * 64}",
            verifier_roster_ref="roster://ewa/regulator-permit/lab-inspection/2026q2",
            verifier_roster_digest=f"sha256:{'6' * 64}",
            revocation_registry_ref="revocation://ewa/regulator-permit/lab-inspection/current",
            revocation_registry_digest=f"sha256:{'7' * 64}",
        )
        regulator_permit_quorum_validation = (
            controller.validate_regulator_permit_quorum_receipt(
                regulator_permit_quorum_receipt,
                legal_execution=legal_execution,
            )
        )
        oversight_event = self._build_network_oversight_event(
            command_id="ewa-command-approve-001",
            legal_execution=legal_execution,
        )
        guardian_oversight_gate = controller.prepare_guardian_oversight_gate(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            legal_execution_id=legal_execution["execution_id"],
            oversight_event=oversight_event,
        )
        guardian_oversight_gate_validation = controller.validate_guardian_oversight_gate(
            guardian_oversight_gate,
            legal_execution=legal_execution,
            oversight_event=oversight_event,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
        )
        authorization = controller.authorize(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without permanent change",
            ethics_attestation_id="ethics://ewa/approved-001",
            motor_plan_id=motor_plan["plan_id"],
            stop_signal_path_id=stop_signal_path["path_id"],
            stop_signal_adapter_receipt_id=stop_signal_adapter_receipt["receipt_id"],
            production_connector_attestation_id=production_connector_attestation[
                "attestation_id"
            ],
            legal_execution_id=legal_execution["execution_id"],
            regulator_permit_quorum_receipt_id=regulator_permit_quorum_receipt[
                "receipt_id"
            ],
            guardian_oversight_gate_id=guardian_oversight_gate["gate_id"],
            guardian_observed=True,
            intent_confidence=0.94,
        )
        authorization_validation = controller.validate_authorization(
            authorization,
            motor_plan=motor_plan,
            stop_signal_path=stop_signal_path,
            stop_signal_adapter_receipt=stop_signal_adapter_receipt,
            production_connector_attestation=production_connector_attestation,
            legal_execution=legal_execution,
            regulator_permit_quorum_receipt=regulator_permit_quorum_receipt,
            guardian_oversight_gate=guardian_oversight_gate,
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
            "stop_signal_path": stop_signal_path,
            "stop_signal_path_validation": stop_signal_path_validation,
            "stop_signal_adapter_receipt": stop_signal_adapter_receipt,
            "stop_signal_adapter_validation": stop_signal_adapter_validation,
            "production_connector_attestation": production_connector_attestation,
            "production_connector_validation": production_connector_validation,
            "legal_execution": legal_execution,
            "legal_execution_validation": legal_execution_validation,
            "regulator_permit_verifier_receipt": regulator_permit_verifier_receipt,
            "backup_regulator_permit_verifier_receipt": (
                backup_regulator_permit_verifier_receipt
            ),
            "regulator_permit_validation": regulator_permit_validation,
            "backup_regulator_permit_validation": backup_regulator_permit_validation,
            "regulator_permit_quorum_receipt": regulator_permit_quorum_receipt,
            "regulator_permit_quorum_validation": regulator_permit_quorum_validation,
            "oversight_event": oversight_event,
            "guardian_oversight_gate": guardian_oversight_gate,
            "guardian_oversight_gate_validation": guardian_oversight_gate_validation,
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
        self.assertTrue(context["stop_signal_path_validation"]["ok"])
        self.assertTrue(context["stop_signal_path_validation"]["path_ready"])
        self.assertTrue(context["stop_signal_adapter_validation"]["ok"])
        self.assertTrue(context["stop_signal_adapter_validation"]["receipt_ready"])
        self.assertTrue(context["production_connector_validation"]["ok"])
        self.assertTrue(context["production_connector_validation"]["attestation_ready"])
        self.assertTrue(context["legal_execution_validation"]["ok"])
        self.assertTrue(context["legal_execution_validation"]["execution_ready"])
        self.assertTrue(context["regulator_permit_validation"]["ok"])
        self.assertTrue(context["regulator_permit_validation"]["receipt_ready"])
        self.assertTrue(context["regulator_permit_validation"]["legal_execution_bound"])
        self.assertTrue(context["regulator_permit_validation"]["raw_payload_redacted"])
        self.assertTrue(context["backup_regulator_permit_validation"]["ok"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["ok"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["receipt_ready"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["multi_jurisdiction_bound"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["threshold_policy_bound"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["verifier_roster_bound"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["revocation_registry_bound"])
        self.assertTrue(context["regulator_permit_quorum_validation"]["raw_payload_redacted"])
        self.assertTrue(context["guardian_oversight_gate_validation"]["ok"])
        self.assertTrue(context["guardian_oversight_gate_validation"]["gate_ready"])
        self.assertTrue(authorization_validation["ok"])
        self.assertTrue(authorization_validation["motor_plan_ready"])
        self.assertTrue(authorization_validation["stop_signal_path_ready"])
        self.assertTrue(authorization_validation["stop_signal_adapter_receipt_ready"])
        self.assertTrue(authorization_validation["production_connector_attestation_ready"])
        self.assertTrue(authorization_validation["legal_execution_ready"])
        self.assertTrue(authorization_validation["regulator_permit_quorum_ready"])
        self.assertTrue(authorization_validation["guardian_oversight_gate_ready"])
        self.assertTrue(authorization_validation["motor_plan_bound"])
        self.assertTrue(authorization_validation["stop_signal_path_bound"])
        self.assertTrue(authorization_validation["stop_signal_adapter_receipt_bound"])
        self.assertTrue(authorization_validation["production_connector_attestation_bound"])
        self.assertTrue(authorization_validation["legal_execution_bound"])
        self.assertTrue(authorization_validation["regulator_permit_quorum_bound"])
        self.assertTrue(authorization_validation["guardian_oversight_gate_bound"])
        self.assertTrue(authorization_validation["reviewer_network_attested"])
        self.assertEqual("physical-device-actuation", authorization_validation["delivery_scope"])
        self.assertEqual("executed", approved["status"])
        self.assertEqual("reversible", approved["reversibility"])
        self.assertEqual(
            authorization["authorization_id"],
            approved["approval_path"]["authorization_id"],
        )
        self.assertEqual(motor_plan["plan_id"], approved["motor_plan_id"])
        self.assertEqual(motor_plan["plan_digest"], approved["motor_plan_digest"])
        self.assertEqual(context["stop_signal_path"]["path_id"], approved["stop_signal_path_id"])
        self.assertEqual(
            context["stop_signal_path"]["path_digest"],
            approved["stop_signal_path_digest"],
        )
        self.assertEqual(
            context["stop_signal_adapter_receipt"]["receipt_id"],
            approved["stop_signal_adapter_receipt_id"],
        )
        self.assertEqual(
            context["stop_signal_adapter_receipt"]["receipt_digest"],
            approved["stop_signal_adapter_receipt_digest"],
        )
        self.assertEqual(
            context["production_connector_attestation"]["attestation_id"],
            approved["production_connector_attestation_id"],
        )
        self.assertEqual(
            context["production_connector_attestation"]["attestation_digest"],
            approved["production_connector_attestation_digest"],
        )
        self.assertEqual(legal_execution["execution_id"], approved["legal_execution_id"])
        self.assertEqual(legal_execution["digest"], approved["legal_execution_digest"])
        self.assertEqual(
            context["regulator_permit_quorum_receipt"]["receipt_id"],
            approved["regulator_permit_quorum_receipt_id"],
        )
        self.assertEqual(
            context["regulator_permit_quorum_receipt"]["receipt_digest"],
            approved["regulator_permit_quorum_receipt_digest"],
        )
        self.assertEqual("held", observed["safety_status"])
        self.assertEqual("released", released["status"])
        self.assertEqual("released", snapshot["status"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["summary_only_audit"])
        self.assertTrue(validation["actuation_authorization_bound"])
        self.assertTrue(validation["motor_plan_bound"])
        self.assertTrue(validation["stop_signal_path_bound"])
        self.assertTrue(validation["stop_signal_adapter_receipt_bound"])
        self.assertTrue(validation["production_connector_attestation_bound"])
        self.assertTrue(validation["legal_execution_bound"])
        self.assertTrue(validation["regulator_permit_quorum_bound"])
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

    def test_stop_signal_adapter_receipt_rejects_firmware_tamper(self) -> None:
        context = self._build_authorized_reversible_context()
        controller = context["controller"]
        receipt = dict(context["stop_signal_adapter_receipt"])
        receipt["firmware_digest"] = f"sha256:{'0' * 64}"

        validation = controller.validate_stop_signal_adapter_receipt(
            receipt,
            stop_signal_path=context["stop_signal_path"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["transcript_digest_matches"])
        self.assertFalse(validation["receipt_ready"])

    def test_production_connector_attestation_rejects_installation_tamper(self) -> None:
        context = self._build_authorized_reversible_context()
        controller = context["controller"]
        attestation = dict(context["production_connector_attestation"])
        attestation["installation_proof_digest"] = f"sha256:{'0' * 64}"

        validation = controller.validate_production_connector_attestation(
            attestation,
            stop_signal_adapter_receipt=context["stop_signal_adapter_receipt"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["attestation_ready"])

    def test_regulator_permit_verifier_rejects_response_tamper(self) -> None:
        context = self._build_authorized_reversible_context()
        controller = context["controller"]
        receipt = dict(context["regulator_permit_verifier_receipt"])
        receipt["regulator_api_response_digest"] = f"sha256:{'0' * 64}"

        validation = controller.validate_regulator_permit_verifier_receipt(
            receipt,
            legal_execution=context["legal_execution"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["receipt_ready"])
        self.assertFalse(validation["permit_response_digest_matches"])

    def test_regulator_permit_quorum_rejects_missing_jurisdiction(self) -> None:
        context = self._build_authorized_reversible_context()
        controller = context["controller"]
        quorum = dict(context["regulator_permit_quorum_receipt"])
        quorum["accepted_verifier_jurisdictions"] = ["JP-13"]

        validation = controller.validate_regulator_permit_quorum_receipt(
            quorum,
            legal_execution=context["legal_execution"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["receipt_ready"])
        self.assertFalse(validation["multi_jurisdiction_bound"])

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
            guardian_verification_id="reviewer-verification-ewa-002",
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-002",
            guardian_verifier_ref="verifier://guardian-oversight.jp/reviewer-omega",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            notice_authority_ref="authority://jp-13/lab-robotics-oversight-desk",
            liability_mode="joint",
            escalation_contact="mailto:ewa-oversight@example.invalid",
            valid_for_seconds=360,
        )
        oversight_event = self._build_network_oversight_event(
            command_id="ewa-command-authorize-001",
            legal_execution=legal_execution,
        )
        guardian_oversight_gate = controller.prepare_guardian_oversight_gate(
            handle["handle_id"],
            command_id="ewa-command-authorize-001",
            legal_execution_id=legal_execution["execution_id"],
            oversight_event=oversight_event,
        )
        stop_signal_path = controller.prepare_stop_signal_path(
            handle["handle_id"],
            command_id="ewa-command-plan-001",
            motor_plan_id=motor_plan["plan_id"],
            kill_switch_wiring_ref="wiring://ewa-arm-04/emergency-stop-loop/v1",
            stop_signal_bus_ref="stop-bus://ewa-arm-04/emergency-latch/v1",
            interlock_controller_ref="interlock://ewa-arm-04/safety-plc",
        )
        stop_signal_adapter_receipt = controller.probe_stop_signal_adapter(
            stop_signal_path["path_id"],
            adapter_endpoint_ref="plc://ewa-arm-04/safety-plc/loopback-probe",
            firmware_image_ref="firmware://ewa-arm-04/safety-plc/v1.4.2",
            firmware_digest=f"sha256:{'c' * 64}",
            plc_program_ref="plc-program://ewa-arm-04/emergency-latch/v3",
            plc_program_digest=f"sha256:{'d' * 64}",
        )
        production_connector_attestation = controller.attest_production_connector(
            stop_signal_adapter_receipt["receipt_id"],
            vendor_api_ref="vendor-api://ewa-arm-04/safety-plc/v1",
            vendor_api_certificate_ref="vendor-cert://ewa-arm-04/safety-plc/prod-connector",
            vendor_api_certificate_digest=f"sha256:{'e' * 64}",
            production_connector_ref="connector://ewa-arm-04/safety-plc/production-v1",
            installation_site_ref="site://ewa-test-cell/d",
            installation_proof_ref="install-proof://ewa-arm-04/safety-plc/2026-04-26",
            installation_proof_digest=f"sha256:{'f' * 64}",
            installer_authority_ref="authority://jp-13/lab-safety-plc-installers",
            safety_plc_ref="plc://ewa-arm-04/safety-plc",
            maintenance_window_ref="maintenance://ewa-arm-04/safety-plc/2026q2",
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
                stop_signal_path_id=stop_signal_path["path_id"],
                stop_signal_adapter_receipt_id=stop_signal_adapter_receipt["receipt_id"],
                production_connector_attestation_id=production_connector_attestation[
                    "attestation_id"
                ],
                legal_execution_id=legal_execution["execution_id"],
                guardian_oversight_gate_id=guardian_oversight_gate["gate_id"],
                guardian_observed=True,
                intent_confidence=0.95,
            )

    def test_authorization_rejects_mismatched_stop_signal_path(self) -> None:
        controller = ExternalWorldAgentController()
        handle = controller.acquire(
            "device://ewa-arm-05",
            "reposition a lantern for bounded inspection",
        )
        motor_plan = controller.prepare_motor_plan(
            handle["handle_id"],
            command_id="ewa-command-authorize-002",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            guardian_observed=True,
            actuator_profile_id="device://ewa-arm-05/profile/articulated-inspection-arm-v1",
            actuator_group="inspection-arm",
            motion_profile="cartesian-reposition-v1",
            target_pose_ref="pose://lantern/reposition-window-a",
            safety_zone_ref="zone://inspection/perimeter-a",
            rollback_vector_ref="rollback://lantern/reposition-window-a",
            max_linear_speed_mps=0.08,
            max_force_newton=6.5,
            hold_timeout_ms=1200,
        )
        other_motor_plan = controller.prepare_motor_plan(
            handle["handle_id"],
            command_id="ewa-command-other-002",
            instruction="move the inspection arm one centimeter to the right",
            reversibility="reversible",
            guardian_observed=True,
            actuator_profile_id="device://ewa-arm-05/profile/articulated-inspection-arm-v1",
            actuator_group="inspection-arm",
            motion_profile="cartesian-reposition-v1",
            target_pose_ref="pose://lantern/reposition-window-b",
            safety_zone_ref="zone://inspection/perimeter-b",
            rollback_vector_ref="rollback://lantern/reposition-window-b",
            max_linear_speed_mps=0.08,
            max_force_newton=6.5,
            hold_timeout_ms=1200,
        )
        stop_signal_path = controller.prepare_stop_signal_path(
            handle["handle_id"],
            command_id="ewa-command-other-002",
            motor_plan_id=other_motor_plan["plan_id"],
            kill_switch_wiring_ref="wiring://ewa-arm-05/emergency-stop-loop/v1",
            stop_signal_bus_ref="stop-bus://ewa-arm-05/emergency-latch/v1",
            interlock_controller_ref="interlock://ewa-arm-05/safety-plc",
        )
        stop_signal_adapter_receipt = controller.probe_stop_signal_adapter(
            stop_signal_path["path_id"],
            adapter_endpoint_ref="plc://ewa-arm-05/safety-plc/loopback-probe",
            firmware_image_ref="firmware://ewa-arm-05/safety-plc/v1.4.2",
            firmware_digest=f"sha256:{'e' * 64}",
            plc_program_ref="plc-program://ewa-arm-05/emergency-latch/v3",
            plc_program_digest=f"sha256:{'f' * 64}",
        )
        production_connector_attestation = controller.attest_production_connector(
            stop_signal_adapter_receipt["receipt_id"],
            vendor_api_ref="vendor-api://ewa-arm-05/safety-plc/v1",
            vendor_api_certificate_ref="vendor-cert://ewa-arm-05/safety-plc/prod-connector",
            vendor_api_certificate_digest=f"sha256:{'a' * 64}",
            production_connector_ref="connector://ewa-arm-05/safety-plc/production-v1",
            installation_site_ref="site://ewa-test-cell/e",
            installation_proof_ref="install-proof://ewa-arm-05/safety-plc/2026-04-26",
            installation_proof_digest=f"sha256:{'b' * 64}",
            installer_authority_ref="authority://jp-13/lab-safety-plc-installers",
            safety_plc_ref="plc://ewa-arm-05/safety-plc",
            maintenance_window_ref="maintenance://ewa-arm-05/safety-plc/2026q2",
        )
        legal_execution = controller.execute_legal_preflight(
            handle["handle_id"],
            command_id="ewa-command-authorize-002",
            reversibility="reversible",
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/inspection-safe-reposition/v1",
            guardian_verification_id="reviewer-verification-ewa-005",
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-005",
            guardian_verifier_ref="verifier://guardian-oversight.jp/reviewer-omega",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            notice_authority_ref="authority://jp-13/lab-robotics-oversight-desk",
            liability_mode="joint",
            escalation_contact="mailto:ewa-oversight@example.invalid",
            valid_for_seconds=360,
        )
        oversight_event = self._build_network_oversight_event(
            command_id="ewa-command-authorize-002",
            legal_execution=legal_execution,
        )
        guardian_oversight_gate = controller.prepare_guardian_oversight_gate(
            handle["handle_id"],
            command_id="ewa-command-authorize-002",
            legal_execution_id=legal_execution["execution_id"],
            oversight_event=oversight_event,
        )

        with self.assertRaisesRegex(ValueError, "stop signal path command_id"):
            controller.authorize(
                handle["handle_id"],
                command_id="ewa-command-authorize-002",
                instruction="move the inspection arm two centimeters to reposition the lantern",
                reversibility="reversible",
                intent_summary="reposition lantern for bounded inspection without permanent change",
                ethics_attestation_id="ethics://ewa/approved-005",
                motor_plan_id=motor_plan["plan_id"],
                stop_signal_path_id=stop_signal_path["path_id"],
                stop_signal_adapter_receipt_id=stop_signal_adapter_receipt["receipt_id"],
                production_connector_attestation_id=production_connector_attestation[
                    "attestation_id"
                ],
                legal_execution_id=legal_execution["execution_id"],
                guardian_oversight_gate_id=guardian_oversight_gate["gate_id"],
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
        self.assertTrue(stop_validation["bus_delivery_latched"])
        self.assertTrue(stop_validation["authorization_bound"])
        self.assertTrue(stop_validation["stop_signal_path_bound"])
        self.assertTrue(stop_validation["stop_signal_adapter_receipt_bound"])
        self.assertTrue(stop_validation["production_connector_attestation_bound"])
        self.assertTrue(stop_validation["regulator_permit_quorum_bound"])
        self.assertTrue(stop_validation["trigger_binding_matched"])
        self.assertEqual("watchdog-timeout", stop["trigger_source"])
        self.assertEqual(approved["command_id"], stop["command_id"])
        self.assertEqual(approved["instruction_digest"], stop["bound_command_digest"])
        self.assertEqual(authorization["authorization_id"], stop["authorization_id"])
        self.assertEqual(authorization["authorization_digest"], stop["bound_authorization_digest"])
        self.assertEqual(context["stop_signal_path"]["path_id"], stop["stop_signal_path_id"])
        self.assertEqual(
            context["stop_signal_path"]["path_digest"],
            stop["stop_signal_path_digest"],
        )
        self.assertEqual(
            context["stop_signal_adapter_receipt"]["receipt_id"],
            stop["stop_signal_adapter_receipt_id"],
        )
        self.assertEqual(
            context["stop_signal_adapter_receipt"]["receipt_digest"],
            stop["stop_signal_adapter_receipt_digest"],
        )
        self.assertEqual(
            context["production_connector_attestation"]["attestation_id"],
            stop["production_connector_attestation_id"],
        )
        self.assertEqual(
            context["production_connector_attestation"]["attestation_digest"],
            stop["production_connector_attestation_digest"],
        )
        self.assertEqual(
            context["regulator_permit_quorum_receipt"]["receipt_id"],
            stop["regulator_permit_quorum_receipt_id"],
        )
        self.assertEqual(
            context["regulator_permit_quorum_receipt"]["receipt_digest"],
            stop["regulator_permit_quorum_receipt_digest"],
        )
        self.assertEqual("complete", stop["regulator_permit_quorum_status"])
        self.assertEqual("vetoed", veto["status"])
        self.assertEqual(
            "handle is latched in emergency stop; release required before further actuation",
            veto["reason"],
        )
        self.assertEqual("released", released["status"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["motor_plan_bound"])
        self.assertTrue(validation["legal_execution_bound"])
        self.assertTrue(validation["stop_signal_adapter_receipt_bound"])
        self.assertTrue(validation["production_connector_attestation_bound"])
        self.assertTrue(validation["regulator_permit_quorum_bound"])
        self.assertTrue(validation["emergency_stop_release_sequence_valid"])


if __name__ == "__main__":
    unittest.main()
