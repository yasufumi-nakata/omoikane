from __future__ import annotations

import unittest

from omoikane.interface.imc import InterMindChannel
from omoikane.interface.wms import WorldModelSync


class WorldModelSyncTests(unittest.TestCase):
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
        imc_session = imc.open_session(
            initiator_id=participants[0],
            peer_id=participants[1],
            mode="text",
            initiator_template=template,
            peer_template=template,
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )
        receipts = []
        for participant_id in participants:
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
