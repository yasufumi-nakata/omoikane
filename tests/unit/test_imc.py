from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

from omoikane.common import sha256_text
from omoikane.interface.imc import (
    IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS,
    InterMindChannel,
)


@contextmanager
def live_window_policy_endpoint(payloads: dict[str, dict[str, object]]):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self) -> None:  # noqa: N802
            payload = payloads.get(self.path)
            if payload is None:
                self.send_response(404)
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                return
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            self.close_connection = True

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


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
        source_manifest = {
            "identity_id": "identity://origin",
            "segments": [
                {
                    "segment_id": "segment-council-review",
                    "digest": sha256_text("segment-council-review"),
                    "source_event_ids": ["episode-0001", "episode-0002"],
                    "source_refs": ["ledger://entry/council-review-0001"],
                }
            ],
        }
        receipt = imc.seal_memory_glimpse_receipt(
            session["session_id"],
            message=message,
            source_manifest=source_manifest,
            selected_segment_ids=["segment-council-review"],
            council_session_ref="council://imc-memory-glimpse/test",
            council_resolution_ref="council://resolution/imc-memory-glimpse/test",
            guardian_attestation_ref="guardian://integrity/imc-memory-glimpse/test",
        )
        receipt_validation = imc.validate_memory_glimpse_receipt(receipt)
        disconnect = imc.emergency_disconnect(
            session["session_id"],
            requested_by="identity://origin",
            reason="withdraw after bounded glimpse",
        )
        reconsent = imc.seal_memory_glimpse_reconsent_receipt(
            session["session_id"],
            memory_glimpse_receipt=receipt,
            requested_by="identity://origin",
            expires_after_seconds=3600,
            revoke_after_event_ref=disconnect["audit_event_ref"],
            council_reconsent_ref="council://resolution/imc-memory-glimpse-reconsent/test",
            guardian_attestation_ref="guardian://integrity/imc-memory-glimpse-reconsent/test",
        )
        reconsent_validation = imc.validate_memory_glimpse_reconsent_receipt(reconsent)
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
        self.assertTrue(receipt_validation["ok"])
        self.assertTrue(receipt_validation["source_bound"])
        self.assertTrue(receipt_validation["disclosure_bound"])
        self.assertTrue(receipt_validation["witness_bound"])
        self.assertTrue(receipt_validation["digest_bound"])
        self.assertFalse(receipt_validation["raw_memory_payload_stored"])
        self.assertFalse(receipt_validation["raw_message_payload_stored"])
        self.assertEqual("council-witnessed-memory-glimpse-receipt-v1", receipt["profile_id"])
        self.assertEqual(["segment-council-review"], receipt["memory_source"]["selected_segment_ids"])
        self.assertEqual(
            ["affect_summary", "display_name", "topic"],
            receipt["disclosure_binding"]["delivered_field_names"],
        )
        self.assertEqual(
            "timeboxed-memory-glimpse-reconsent-receipt-v1",
            reconsent["profile_id"],
        )
        self.assertEqual("revoked-pending-reconsent", reconsent["status"])
        self.assertEqual(
            receipt["digest"],
            reconsent["memory_glimpse_receipt_digest"],
        )
        self.assertEqual(
            disconnect["audit_event_ref"],
            reconsent["revocation_binding"]["revoke_after_event_ref"],
        )
        self.assertTrue(reconsent_validation["ok"])
        self.assertTrue(reconsent_validation["source_receipt_bound"])
        self.assertTrue(reconsent_validation["consent_window_bound"])
        self.assertTrue(reconsent_validation["revocation_bound"])
        self.assertTrue(reconsent_validation["reconsent_bound"])
        self.assertTrue(reconsent_validation["digest_bound"])
        self.assertFalse(reconsent_validation["raw_reconsent_payload_stored"])
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

    def test_memory_glimpse_receipt_rejects_wrong_mode_session(self) -> None:
        imc = InterMindChannel()
        session = imc.open_session(
            initiator_id="identity://origin",
            peer_id="identity://peer",
            mode="text",
            initiator_template={
                "public_fields": ["display_name"],
                "intimate_fields": [],
                "sealed_fields": [],
            },
            peer_template={
                "public_fields": ["display_name"],
                "intimate_fields": [],
                "sealed_fields": [],
            },
            peer_attested=True,
            forward_secrecy=True,
        )
        message = imc.send(
            session["session_id"],
            sender_id="identity://origin",
            summary="plain text",
            payload={"display_name": "Origin"},
        )

        with self.assertRaisesRegex(ValueError, "memory_glimpse"):
            imc.seal_memory_glimpse_receipt(
                session["session_id"],
                message=message,
                source_manifest={"identity_id": "identity://origin", "segments": []},
                selected_segment_ids=["segment-missing"],
                council_session_ref="council://imc-memory-glimpse/test",
                council_resolution_ref="council://resolution/imc-memory-glimpse/test",
                guardian_attestation_ref="guardian://integrity/imc-memory-glimpse/test",
            )

    def test_memory_glimpse_reconsent_rejects_unbounded_window(self) -> None:
        imc = InterMindChannel()
        session = imc.open_session(
            initiator_id="identity://origin",
            peer_id="identity://peer",
            mode="memory_glimpse",
            initiator_template={
                "public_fields": ["display_name", "topic"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["memory_index"],
            },
            peer_template={
                "public_fields": ["display_name", "topic"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["memory_index"],
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
                "affect_summary": "careful",
                "memory_index": "crystal://segment/7",
            },
        )
        source_manifest = {
            "identity_id": "identity://origin",
            "segments": [
                {
                    "segment_id": "segment-council-review",
                    "digest": sha256_text("segment-council-review"),
                    "source_event_ids": ["episode-0001"],
                    "source_refs": ["ledger://entry/council-review-0001"],
                }
            ],
        }
        receipt = imc.seal_memory_glimpse_receipt(
            session["session_id"],
            message=message,
            source_manifest=source_manifest,
            selected_segment_ids=["segment-council-review"],
            council_session_ref="council://imc-memory-glimpse/test",
            council_resolution_ref="council://resolution/imc-memory-glimpse/test",
            guardian_attestation_ref="guardian://integrity/imc-memory-glimpse/test",
        )
        disconnect = imc.emergency_disconnect(
            session["session_id"],
            requested_by="identity://origin",
            reason="withdraw after bounded glimpse",
        )

        with self.assertRaisesRegex(ValueError, "expires_after_seconds"):
            imc.seal_memory_glimpse_reconsent_receipt(
                session["session_id"],
                memory_glimpse_receipt=receipt,
                requested_by="identity://origin",
                expires_after_seconds=86401,
                revoke_after_event_ref=disconnect["audit_event_ref"],
                council_reconsent_ref="council://resolution/imc-memory-glimpse-reconsent/test",
                guardian_attestation_ref="guardian://integrity/imc-memory-glimpse-reconsent/test",
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
        window_policy_payloads = {
            "/jp-13": imc.build_merge_thought_window_policy_verifier_payload(
                verifier_ref=IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS[0],
                verifier_authority_ref=(
                    "authority://imc-window-policy/jp-13/live-verifier"
                ),
                jurisdiction="JP-13",
            ),
            "/us-ca": imc.build_merge_thought_window_policy_verifier_payload(
                verifier_ref=IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS[1],
                verifier_authority_ref=(
                    "authority://imc-window-policy/us-ca/live-verifier"
                ),
                jurisdiction="US-CA",
            ),
        }
        with live_window_policy_endpoint(window_policy_payloads) as base_url:
            window_policy_verifier_receipts = [
                imc.probe_merge_thought_window_policy_verifier_endpoint(
                    verifier_endpoint=f"{base_url}/jp-13",
                    verifier_ref=IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS[0],
                    verifier_authority_ref=(
                        "authority://imc-window-policy/jp-13/live-verifier"
                    ),
                    jurisdiction="JP-13",
                ),
                imc.probe_merge_thought_window_policy_verifier_endpoint(
                    verifier_endpoint=f"{base_url}/us-ca",
                    verifier_ref=IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS[1],
                    verifier_authority_ref=(
                        "authority://imc-window-policy/us-ca/live-verifier"
                    ),
                    jurisdiction="US-CA",
                ),
            ]
        receipt = imc.seal_merge_thought_ethics_receipt(
            session["session_id"],
            message=message,
            collective_ref="collective://bounded-merge/test",
            council_session_ref="council://imc-merge-thought/test",
            federation_council_ref="federation-council://imc-merge-thought/test",
            ethics_decision_ref="ethics://imc-merge-thought/approved",
            guardian_attestation_ref="guardian://integrity/imc-merge-thought/test",
            requested_merge_window_seconds=10,
            window_policy_verifier_receipts=window_policy_verifier_receipts,
        )
        receipt_validation = imc.validate_merge_thought_ethics_receipt(receipt)

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
        self.assertEqual(
            "federation-council-merge-thought-ethics-gate-v1",
            receipt["profile_id"],
        )
        self.assertEqual("approved", receipt["status"])
        self.assertEqual(10, receipt["risk_boundary"]["max_merge_window_seconds"])
        self.assertEqual(
            "merge-thought-window-policy-authority-v1",
            receipt["risk_boundary"]["merge_window_policy_authority"][
                "policy_profile"
            ],
        )
        self.assertEqual(
            "verified",
            receipt["risk_boundary"]["merge_window_policy_authority"][
                "policy_authority_status"
            ],
        )
        self.assertTrue(
            receipt["risk_boundary"]["merge_window_policy_authority"][
                "live_verifier_quorum_bound"
            ]
        )
        self.assertEqual(
            2,
            len(
                receipt["risk_boundary"]["merge_window_policy_authority"][
                    "live_verifier_receipts"
                ]
            ),
        )
        self.assertFalse(
            receipt["risk_boundary"]["merge_window_policy_authority"][
                "raw_policy_payload_stored"
            ]
        )
        self.assertFalse(
            receipt["risk_boundary"]["merge_window_policy_authority"][
                "raw_verifier_payload_stored"
            ]
        )
        self.assertFalse(
            receipt["risk_boundary"]["merge_window_policy_authority"][
                "raw_response_signature_payload_stored"
            ]
        )
        self.assertTrue(
            receipt["risk_boundary"]["post_disconnect_identity_confirmation_required"]
        )
        self.assertTrue(receipt["risk_boundary"]["emergency_disconnect_required"])
        self.assertTrue(receipt["risk_boundary"]["private_recovery_mode_required"])
        self.assertEqual(
            "distinct-collective-merge-thought-binding-v1",
            receipt["collective_binding"]["binding_profile"],
        )
        self.assertTrue(receipt_validation["ok"])
        self.assertTrue(receipt_validation["risk_bound"])
        self.assertTrue(receipt_validation["window_policy_authority_bound"])
        self.assertTrue(receipt_validation["window_policy_live_verifier_bound"])
        self.assertTrue(receipt_validation["collective_bound"])
        self.assertTrue(receipt_validation["disclosure_bound"])
        self.assertTrue(receipt_validation["gate_bound"])
        self.assertTrue(receipt_validation["digest_bound"])
        self.assertFalse(receipt_validation["raw_window_policy_payload_stored"])
        self.assertFalse(receipt_validation["raw_window_policy_verifier_payload_stored"])
        self.assertFalse(
            receipt_validation["raw_window_policy_response_signature_payload_stored"]
        )
        self.assertFalse(receipt_validation["raw_thought_payload_stored"])
        self.assertFalse(receipt_validation["raw_message_payload_stored"])

        tampered = deepcopy(receipt)
        tampered["risk_boundary"]["merge_window_policy_authority"][
            "policy_authority_digest"
        ] = "0" * 64
        tampered_validation = imc.validate_merge_thought_ethics_receipt(tampered)
        self.assertFalse(tampered_validation["ok"])
        self.assertFalse(tampered_validation["risk_bound"])
        self.assertFalse(tampered_validation["window_policy_authority_bound"])

        tampered_live = deepcopy(receipt)
        tampered_live["risk_boundary"]["merge_window_policy_authority"][
            "live_verifier_receipts"
        ][0]["network_response_digest"] = "0" * 64
        tampered_live_validation = imc.validate_merge_thought_ethics_receipt(
            tampered_live
        )
        self.assertFalse(tampered_live_validation["ok"])
        self.assertFalse(tampered_live_validation["window_policy_live_verifier_bound"])

    def test_merge_thought_ethics_receipt_rejects_unbounded_window(self) -> None:
        imc = InterMindChannel()
        session = imc.open_session(
            initiator_id="identity://origin",
            peer_id="identity://peer",
            mode="merge_thought",
            initiator_template={
                "public_fields": ["display_name", "shared_focus"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["identity_axiom_state"],
            },
            peer_template={
                "public_fields": ["display_name", "shared_focus"],
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
            summary="bounded merge exchange",
            payload={
                "display_name": "Origin",
                "shared_focus": "collective-planning",
                "affect_summary": "careful trust",
                "identity_axiom_state": "sealed-core",
            },
        )

        with self.assertRaisesRegex(ValueError, "requested_merge_window_seconds"):
            imc.seal_merge_thought_ethics_receipt(
                session["session_id"],
                message=message,
                collective_ref="collective://bounded-merge/test",
                council_session_ref="council://imc-merge-thought/test",
                federation_council_ref="federation-council://imc-merge-thought/test",
                ethics_decision_ref="ethics://imc-merge-thought/approved",
                guardian_attestation_ref="guardian://integrity/imc-merge-thought/test",
                requested_merge_window_seconds=11,
            )


if __name__ == "__main__":
    unittest.main()
