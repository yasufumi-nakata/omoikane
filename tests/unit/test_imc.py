from __future__ import annotations

import unittest

from omoikane.interface.imc import InterMindChannel


class InterMindChannelTests(unittest.TestCase):
    def test_memory_glimpse_applies_disclosure_floor_and_disconnect(self) -> None:
        imc = InterMindChannel()
        session = imc.open_session(
            initiator_id="identity://origin",
            peer_id="identity://peer",
            mode="memory_glimpse",
            initiator_template={
                "public_fields": ["display_name", "presence_state", "topic"],
                "intimate_fields": ["affect_summary", "memory_summary"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_template={
                "public_fields": ["display_name", "topic"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["identity_axiom_state"],
            },
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )

        message = imc.send(
            session["session_id"],
            sender_id="identity://origin",
            summary="bounded disclosure",
            payload={
                "display_name": "Origin",
                "topic": "continuity",
                "affect_summary": "careful optimism",
                "memory_summary": "retrospective excerpt",
                "memory_index": "crystal://segment/7",
                "identity_axiom_state": "sealed-core",
            },
        )
        disconnect = imc.emergency_disconnect(
            session["session_id"],
            requested_by="identity://origin",
            reason="withdraw after bounded glimpse",
        )
        snapshot = imc.snapshot(session["session_id"])
        validation = imc.validate_session(snapshot)

        self.assertEqual("delivered-with-redactions", message["delivery_status"])
        self.assertEqual(
            {
                "display_name": "Origin",
                "topic": "continuity",
                "affect_summary": "careful optimism",
            },
            message["delivered_fields"],
        )
        self.assertEqual(
            ["identity_axiom_state", "memory_index", "memory_summary"],
            message["redacted_fields"],
        )
        self.assertTrue(disconnect["close_committed_before_notice"])
        self.assertEqual("closed", snapshot["status"])
        self.assertEqual("revoked", snapshot["key_state"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["sealed_fields_protected"])
        self.assertTrue(validation["disclosure_floor_applied"])

    def test_council_witness_required_for_memory_glimpse(self) -> None:
        imc = InterMindChannel()

        with self.assertRaisesRegex(PermissionError, "requires council witness"):
            imc.open_session(
                initiator_id="identity://origin",
                peer_id="identity://peer",
                mode="memory_glimpse",
                initiator_template={
                    "public_fields": ["display_name"],
                    "intimate_fields": ["affect_summary"],
                    "sealed_fields": [],
                },
                peer_template={
                    "public_fields": ["display_name"],
                    "intimate_fields": ["affect_summary"],
                    "sealed_fields": [],
                },
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=False,
            )

    def test_merge_thought_requires_council_witness_and_redacts_intimate_floor_overreach(self) -> None:
        imc = InterMindChannel()
        session = imc.open_session(
            initiator_id="identity://origin",
            peer_id="identity://peer",
            mode="merge_thought",
            initiator_template={
                "public_fields": ["display_name", "shared_focus"],
                "intimate_fields": ["affect_summary", "intent_vector"],
                "sealed_fields": ["identity_axiom_state", "memory_index"],
            },
            peer_template={
                "public_fields": ["display_name", "shared_focus"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["identity_axiom_state", "memory_index"],
            },
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )

        message = imc.send(
            session["session_id"],
            sender_id="identity://origin",
            summary="bounded merge exchange",
            payload={
                "display_name": "Origin",
                "shared_focus": "collective-planning",
                "affect_summary": "careful trust",
                "intent_vector": "synthesize shared plan",
                "memory_index": "crystal://segment/3",
                "identity_axiom_state": "sealed-core",
            },
        )

        self.assertEqual("merge_thought", session["mode"])
        self.assertEqual("delivered-with-redactions", message["delivery_status"])
        self.assertEqual(
            ["identity_axiom_state", "intent_vector", "memory_index"],
            message["redacted_fields"],
        )
        self.assertEqual(
            {
                "display_name": "Origin",
                "shared_focus": "collective-planning",
                "affect_summary": "careful trust",
            },
            message["delivered_fields"],
        )


if __name__ == "__main__":
    unittest.main()
