from __future__ import annotations

import unittest

from omoikane.agentic.distributed_transport import DistributedTransportService
from omoikane.interface.imc import InterMindChannel
from omoikane.interface.wms import WorldModelSync


class WorldModelSyncTests(unittest.TestCase):
    def _time_rate_attestation_receipts(
        self,
        sync: WorldModelSync,
        session: dict,
        *,
        proposer_id: str,
        requested_time_rate: float,
    ) -> tuple[dict, list[dict]]:
        participants = session["current_state"]["participants"]
        subject = sync.build_time_rate_attestation_subject(
            session["session_id"],
            proposer_id=proposer_id,
            requested_time_rate=requested_time_rate,
        )
        imc = InterMindChannel()
        template = {
            "public_fields": [
                "time_rate_attestation_subject_digest",
                "participant_id",
                "baseline_time_rate",
                "requested_time_rate",
                "attestation_decision",
            ],
            "intimate_fields": [],
            "sealed_fields": [],
        }
        receipts = []
        for participant_id in participants:
            counterparty = participants[1] if participant_id == participants[0] else participants[0]
            imc_session = imc.open_session(
                initiator_id=counterparty,
                peer_id=participant_id,
                mode="text",
                initiator_template=template,
                peer_template=template,
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=True,
            )
            message = imc.send(
                imc_session["session_id"],
                sender_id=participant_id,
                summary="subjective time-rate attestation for WMS private escape",
                payload={
                    "time_rate_attestation_subject_digest": subject["digest"],
                    "participant_id": participant_id,
                    "baseline_time_rate": subject["baseline_time_rate"],
                    "requested_time_rate": subject["requested_time_rate"],
                    "attestation_decision": "attest",
                },
            )
            receipts.append(
                sync.build_time_rate_attestation_receipt(
                    session["session_id"],
                    participant_id=participant_id,
                    time_rate_attestation_subject_digest=subject["digest"],
                    baseline_time_rate=subject["baseline_time_rate"],
                    requested_time_rate=subject["requested_time_rate"],
                    imc_session=imc_session,
                    imc_message=message,
                )
            )
        return subject, receipts

    def _approval_transport_receipts(
        self,
        sync: WorldModelSync,
        session: dict,
        *,
        requested_by: str,
        proposed_physics_rules_ref: str,
        rationale: str,
    ) -> list[dict]:
        participants = session["current_state"]["participants"]
        subject = sync.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by=requested_by,
            proposed_physics_rules_ref=proposed_physics_rules_ref,
            rationale=rationale,
        )
        imc = InterMindChannel()
        template = {
            "public_fields": [
                "approval_subject_digest",
                "participant_id",
                "approval_decision",
            ],
            "intimate_fields": [],
            "sealed_fields": [],
        }
        receipts = []
        for participant_id in participants:
            counterparty = participants[1] if participant_id == participants[0] else participants[0]
            imc_session = imc.open_session(
                initiator_id=counterparty,
                peer_id=participant_id,
                mode="text",
                initiator_template=template,
                peer_template=template,
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=True,
            )
            message = imc.send(
                imc_session["session_id"],
                sender_id=participant_id,
                summary="approval for reversible WMS physics rules change",
                payload={
                    "approval_subject_digest": subject["digest"],
                    "participant_id": participant_id,
                    "approval_decision": "approve",
                },
            )
            receipts.append(
                sync.build_participant_approval_transport_receipt(
                    session["session_id"],
                    participant_id=participant_id,
                    approval_subject_digest=subject["digest"],
                    imc_session=imc_session,
                    imc_message=message,
                )
            )
        return receipts

    def test_minor_diff_reconciles_via_consensus_round(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table", "shared-lantern"],
            affected_object_ratio=0.03,
            attested=True,
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("minor_diff", outcome["classification"])
        self.assertEqual("consensus-round", outcome["decision"])
        self.assertFalse(outcome["escape_offered"])
        self.assertIn("shared-lantern", snapshot["objects"])

    def test_major_diff_offers_private_reality_escape(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table", "gravity-well"],
            affected_object_ratio=0.22,
            attested=True,
        )
        switched = sync.switch_mode(
            session["session_id"],
            mode="private_reality",
            requested_by="identity://primary",
            reason="major shared-world divergence",
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("major_diff", outcome["classification"])
        self.assertTrue(outcome["escape_offered"])
        self.assertTrue(switched["private_escape_honored"])
        self.assertEqual("local", snapshot["authority"])

    def test_time_rate_deviation_offers_escape_without_mutating_state(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        subject, attestations = self._time_rate_attestation_receipts(
            sync,
            session,
            proposer_id="identity://peer",
            requested_time_rate=1.25,
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table"],
            affected_object_ratio=0.01,
            attested=True,
            requested_time_rate=1.25,
            time_rate_attestation_receipts=attestations,
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("major_diff", outcome["classification"])
        self.assertEqual("offer-private-reality", outcome["decision"])
        self.assertTrue(outcome["escape_offered"])
        self.assertEqual("fixed-time-rate-private-escape-v1", outcome["time_rate_policy_id"])
        self.assertEqual(1.0, outcome["baseline_time_rate"])
        self.assertEqual(1.25, outcome["requested_time_rate"])
        self.assertEqual(0.25, outcome["time_rate_delta"])
        self.assertTrue(outcome["time_rate_deviation_detected"])
        self.assertTrue(outcome["time_rate_escape_required"])
        self.assertTrue(outcome["time_rate_state_locked"])
        self.assertEqual("baseline-requested-time-rate-delta-v1", outcome["time_rate_deviation_digest_profile"])
        self.assertEqual(64, len(outcome["time_rate_deviation_digest"]))
        self.assertEqual("subjective-time-attestation-transport-v1", outcome["time_rate_attestation_policy_id"])
        self.assertEqual(subject["digest"], outcome["time_rate_attestation_subject_digest"])
        self.assertTrue(outcome["time_rate_attestation_required"])
        self.assertTrue(outcome["time_rate_attestation_quorum_met"])
        self.assertTrue(outcome["time_rate_attestation_participant_order_bound"])
        self.assertEqual(2, len(outcome["time_rate_attestation_receipts"]))
        self.assertTrue(
            all(
                sync.validate_time_rate_attestation_receipt(
                    receipt,
                    time_rate_attestation_subject_digest=subject["digest"],
                )["ok"]
                for receipt in outcome["time_rate_attestation_receipts"]
            )
        )
        self.assertEqual(1.0, snapshot["time_rate"])

    def test_time_rate_deviation_without_transport_attestation_fails_quorum(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table"],
            affected_object_ratio=0.01,
            attested=True,
            requested_time_rate=1.25,
        )

        self.assertTrue(outcome["time_rate_attestation_required"])
        self.assertFalse(outcome["time_rate_attestation_quorum_met"])
        self.assertEqual(
            ["identity://primary", "identity://peer"],
            outcome["time_rate_attestation_missing_participants"],
        )

    def test_unauthorized_diff_isolated_as_malicious_inject(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://spoof",
            candidate_objects=["atrium", "spoofed-object"],
            affected_object_ratio=0.4,
            attested=False,
        )
        violation = sync.observe_violation(session["session_id"])

        self.assertEqual("malicious_inject", outcome["classification"])
        self.assertEqual("guardian-veto", outcome["decision"])
        self.assertEqual("isolate-session", violation["guardian_action"])
        self.assertTrue(violation["violation_detected"])

    def test_physics_rules_change_requires_unanimous_reversible_receipt(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        baseline = sync.snapshot(session["session_id"])
        proposed_ref = "physics://shared-atrium/low-gravity-v1"
        rationale = "bounded rehearsal"
        approval_transport_receipts = self._approval_transport_receipts(
            sync,
            session,
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )

        receipt = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
            participant_approvals=["identity://primary", "identity://peer"],
            guardian_attested=True,
            approval_transport_receipts=approval_transport_receipts,
        )
        changed = sync.snapshot(session["session_id"])
        validation = sync.validate_physics_rules_change(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["approval_quorum_met"])
        self.assertTrue(validation["approval_transport_quorum_met"])
        self.assertTrue(validation["approval_transport_digest_bound"])
        self.assertTrue(validation["approval_collection_complete"])
        self.assertTrue(validation["approval_collection_digest_bound"])
        self.assertTrue(validation["revert_bound"])
        self.assertTrue(validation["digest_bound"])
        self.assertEqual("applied", receipt["decision"])
        self.assertEqual(
            "physics://shared-atrium/low-gravity-v1",
            changed["physics_rules_ref"],
        )
        self.assertEqual(baseline["physics_rules_ref"], receipt["rollback_physics_rules_ref"])

        reverted = sync.revert_physics_rules_change(
            session["session_id"],
            change_id=receipt["change_id"],
            requested_by="identity://primary",
            reason="rehearsal complete",
            guardian_attested=True,
        )
        reverted_state = sync.snapshot(session["session_id"])
        revert_validation = sync.validate_physics_rules_change(reverted)

        self.assertTrue(revert_validation["ok"])
        self.assertEqual("reverted", reverted["decision"])
        self.assertEqual(receipt["change_id"], reverted["revert_of_change_id"])
        self.assertEqual(baseline["physics_rules_ref"], reverted_state["physics_rules_ref"])
        self.assertEqual(receipt["rollback_token_ref"], reverted["rollback_token_ref"])

    def test_approval_collection_batches_participant_receipts(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer", "identity://observer"],
            objects=["atrium", "council-table"],
        )
        proposed_ref = "physics://shared-atrium/low-gravity-v1"
        rationale = "bounded rehearsal"
        receipts = self._approval_transport_receipts(
            sync,
            session,
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )
        subject = sync.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )

        collection = sync.build_approval_collection_receipt(
            session["session_id"],
            approval_subject_digest=subject["digest"],
            approval_transport_receipts=receipts,
            max_batch_size=2,
        )
        validation = sync.validate_approval_collection_receipt(
            collection,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=subject["digest"],
            approval_transport_receipts=receipts,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["collection_complete"])
        self.assertTrue(validation["participant_order_bound"])
        self.assertTrue(validation["receipt_set_digest_bound"])
        self.assertTrue(validation["batches_within_limit"])
        self.assertEqual(2, collection["batch_count"])
        self.assertEqual(
            ["identity://primary", "identity://peer", "identity://observer"],
            collection["covered_participants"],
        )

    def test_distributed_approval_fanout_binds_transport_results(self) -> None:
        sync = WorldModelSync()
        transport = DistributedTransportService()
        session = sync.create_session(
            ["identity://primary", "identity://peer", "identity://observer"],
            objects=["atrium", "council-table"],
        )
        proposed_ref = "physics://shared-atrium/low-gravity-v1"
        rationale = "bounded rehearsal"
        receipts = self._approval_transport_receipts(
            sync,
            session,
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )
        subject = sync.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )
        collection = sync.build_approval_collection_receipt(
            session["session_id"],
            approval_subject_digest=subject["digest"],
            approval_transport_receipts=receipts,
            max_batch_size=2,
        )
        fanout_results = []
        for index, participant_id in enumerate(session["current_state"]["participants"], start=1):
            participant_pair = (
                ["identity://primary", "identity://peer"]
                if participant_id == "identity://primary"
                else ["identity://primary", participant_id]
            )
            result_digest = sync.build_distributed_approval_result_digest(
                approval_subject_digest=subject["digest"],
                participant_id=participant_id,
                approval_collection_digest=collection["digest"],
            )
            envelope = transport.issue_federation_handoff(
                topology_ref=f"topology://wms-test/{index}",
                proposal_ref=f"wms-approval://{index}",
                payload_ref=f"cas://sha256/{subject['digest']}",
                payload_digest=subject["digest"],
                participant_identity_ids=participant_pair,
            )
            transport_receipt = transport.record_receipt(
                envelope,
                result_ref=f"resolution://wms-test/{index}",
                result_digest=result_digest,
                participant_ids=[
                    attestation.participant_id
                    for attestation in envelope.participant_attestations
                ],
                channel_binding_ref=envelope.channel_binding_ref,
                verified_root_refs=["root://federation/pki-a"],
                key_epoch=1,
                hop_nonce_chain=[f"hop://wms-test/{index}/relay-a"],
            )
            fanout_results.append(
                {
                    "participant_id": participant_id,
                    "approval_result_ref": f"resolution://wms-test/{index}",
                    "approval_result_digest": result_digest,
                    "transport_envelope": envelope.to_dict(),
                    "transport_receipt": transport_receipt.to_dict(),
                }
            )

        fanout = sync.build_distributed_approval_fanout_receipt(
            session["session_id"],
            approval_subject_digest=subject["digest"],
            approval_collection_receipt=collection,
            participant_fanout_results=fanout_results,
        )
        validation = sync.validate_distributed_approval_fanout_receipt(
            fanout,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=subject["digest"],
            approval_collection_digest=collection["digest"],
        )
        physics_change = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
            participant_approvals=session["current_state"]["participants"],
            guardian_attested=True,
            approval_transport_receipts=receipts,
            approval_collection_receipt=collection,
            approval_fanout_receipt=fanout,
        )
        physics_validation = sync.validate_physics_rules_change(physics_change)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["fanout_complete"])
        self.assertTrue(validation["transport_receipt_set_authenticated"])
        self.assertTrue(validation["result_digest_bound"])
        self.assertTrue(physics_validation["ok"])
        self.assertTrue(physics_validation["approval_fanout_complete"])
        self.assertTrue(physics_validation["approval_fanout_digest_bound"])
        self.assertEqual("complete", fanout["fanout_status"])
        self.assertEqual(3, fanout["result_count"])

    def test_physics_rules_change_rejects_missing_peer_approval(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        baseline = sync.snapshot(session["session_id"])

        receipt = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref="physics://shared-atrium/low-gravity-v1",
            rationale="bounded rehearsal",
            participant_approvals=["identity://primary"],
            guardian_attested=True,
        )
        unchanged = sync.snapshot(session["session_id"])

        self.assertEqual("rejected", receipt["decision"])
        self.assertFalse(receipt["approval_quorum_met"])
        self.assertFalse(receipt["approval_transport_quorum_met"])
        self.assertEqual(baseline["physics_rules_ref"], unchanged["physics_rules_ref"])

    def test_physics_rules_change_rejects_static_approval_without_transport(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        baseline = sync.snapshot(session["session_id"])

        receipt = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref="physics://shared-atrium/low-gravity-v1",
            rationale="bounded rehearsal",
            participant_approvals=["identity://primary", "identity://peer"],
            guardian_attested=True,
        )
        unchanged = sync.snapshot(session["session_id"])

        self.assertEqual("rejected", receipt["decision"])
        self.assertTrue(receipt["approval_quorum_met"])
        self.assertFalse(receipt["approval_transport_quorum_met"])
        self.assertEqual(baseline["physics_rules_ref"], unchanged["physics_rules_ref"])


if __name__ == "__main__":
    unittest.main()
