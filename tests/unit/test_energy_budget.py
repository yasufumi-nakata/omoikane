from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest

from omoikane.kernel.energy_budget import EnergyBudgetService
from omoikane.substrate.adapter import ClassicalSiliconAdapter


@contextmanager
def live_verifier_endpoint(payload: dict[str, object]):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self) -> None:  # noqa: N802
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
        yield f"http://127.0.0.1:{server.server_address[1]}/signer-roster"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


def attach_signed_response_envelope(
    service: EnergyBudgetService,
    payload: dict[str, object],
    endpoint: str,
) -> None:
    preview_receipt = service.build_subsidy_signer_roster_verifier_receipt(
        signer_roster_ref=str(payload["signer_roster_ref"]),
        signer_roster_digest=str(payload["signer_roster_digest"]),
        signer_key_ref=str(payload["signer_key_ref"]),
        signer_jurisdiction=str(payload["signer_jurisdiction"]),
        external_funding_policy_digest=str(payload["external_funding_policy_digest"]),
        funding_policy_signature_digest=str(payload["funding_policy_signature_digest"]),
        verifier_ref=str(payload["verifier_ref"]),
        challenge_ref=str(payload["challenge_ref"]),
        verifier_endpoint_ref=endpoint,
        verifier_authority_ref=str(payload["verifier_authority_ref"]),
        verifier_jurisdiction=str(payload["verifier_jurisdiction"]),
        verifier_route_ref=str(payload["verifier_route_ref"]),
        authority_chain_ref=str(payload["authority_chain_ref"]),
        trust_root_ref=str(payload["trust_root_ref"]),
        trust_root_digest=str(payload["trust_root_digest"]),
        verifier_transport_profile="live-http-json-energy-subsidy-signer-roster-verifier-v1",
        request_timeout_ms=500,
        network_response_digest="0" * 64,
        network_probe_status="reachable",
        checked_at=str(payload["checked_at"]),
    )
    payload.update(
        {
            "response_envelope_profile": preview_receipt["response_envelope_profile"],
            "response_signing_key_ref": preview_receipt["response_signing_key_ref"],
            "response_signature_digest": preview_receipt["response_signature_digest"],
            "raw_response_signature_payload_stored": False,
        }
    )


def build_live_subsidy_verifier_quorum(
    service: EnergyBudgetService,
    draft_receipt: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    draft_verifier = draft_receipt["signer_roster_verifier_receipt"]
    assert isinstance(draft_verifier, dict)
    primary_authority_ref = (
        "authority://energy-budget.jp/subsidy-signer-roster/verifier-primary"
    )
    primary_jurisdiction = "JP-13"
    primary_route_ref = "route://energy-budget.jp/signer-roster/live-primary"
    backup_verifier_ref = "verifier://energy-budget.sg/signer-roster"
    backup_challenge_ref = "challenge://energy-budget-subsidy/signer-roster/sg-backup/v1"
    backup_authority_ref = (
        "authority://energy-budget.sg/subsidy-signer-roster/verifier-backup"
    )
    backup_jurisdiction = "SG-01"
    backup_route_ref = "route://energy-budget.sg/signer-roster/live-backup"
    backup_authority_chain_ref = "authority://energy-budget.sg/subsidy-signer-roster"
    backup_trust_root_ref = "root://energy-budget.sg/subsidy-signer-roster-pki"
    backup_trust_root_digest = "sha256:energy-budget-sg-subsidy-signer-roster-pki-v1"
    common_payload = {
        "signer_roster_ref": draft_receipt["funding_policy_signer_roster_ref"],
        "signer_roster_digest": draft_receipt["funding_policy_signer_roster_digest"],
        "signer_key_ref": draft_receipt["funding_policy_signer_key_ref"],
        "signer_jurisdiction": draft_receipt["funding_policy_signer_jurisdiction"],
        "external_funding_policy_digest": draft_receipt["external_funding_policy_digest"],
        "funding_policy_signature_digest": draft_receipt[
            "funding_policy_signature_digest"
        ],
    }
    primary_payload = {
        "checked_at": "2026-04-26T00:00:00Z",
        "verifier_ref": draft_verifier["verifier_ref"],
        "challenge_ref": draft_verifier["challenge_ref"],
        "verifier_authority_ref": primary_authority_ref,
        "verifier_jurisdiction": primary_jurisdiction,
        "verifier_route_ref": primary_route_ref,
        "authority_chain_ref": draft_verifier["authority_chain_ref"],
        "trust_root_ref": draft_verifier["trust_root_ref"],
        "trust_root_digest": draft_verifier["trust_root_digest"],
        **common_payload,
    }
    backup_payload = {
        "checked_at": "2026-04-26T00:00:01Z",
        "verifier_ref": backup_verifier_ref,
        "challenge_ref": backup_challenge_ref,
        "verifier_authority_ref": backup_authority_ref,
        "verifier_jurisdiction": backup_jurisdiction,
        "verifier_route_ref": backup_route_ref,
        "authority_chain_ref": backup_authority_chain_ref,
        "trust_root_ref": backup_trust_root_ref,
        "trust_root_digest": backup_trust_root_digest,
        **common_payload,
    }
    with live_verifier_endpoint(primary_payload) as endpoint:
        attach_signed_response_envelope(service, primary_payload, endpoint)
        primary_receipt = service.probe_subsidy_signer_roster_verifier_endpoint(
            verifier_endpoint=endpoint,
            signer_roster_ref=str(common_payload["signer_roster_ref"]),
            signer_roster_digest=str(common_payload["signer_roster_digest"]),
            signer_key_ref=str(common_payload["signer_key_ref"]),
            signer_jurisdiction=str(common_payload["signer_jurisdiction"]),
            external_funding_policy_digest=str(
                common_payload["external_funding_policy_digest"]
            ),
            funding_policy_signature_digest=str(
                common_payload["funding_policy_signature_digest"]
            ),
            verifier_ref=str(draft_verifier["verifier_ref"]),
            challenge_ref=str(draft_verifier["challenge_ref"]),
            verifier_authority_ref=primary_authority_ref,
            verifier_jurisdiction=primary_jurisdiction,
            verifier_route_ref=primary_route_ref,
            authority_chain_ref=str(draft_verifier["authority_chain_ref"]),
            trust_root_ref=str(draft_verifier["trust_root_ref"]),
            trust_root_digest=str(draft_verifier["trust_root_digest"]),
            request_timeout_ms=500,
        )
    with live_verifier_endpoint(backup_payload) as endpoint:
        attach_signed_response_envelope(service, backup_payload, endpoint)
        backup_receipt = service.probe_subsidy_signer_roster_verifier_endpoint(
            verifier_endpoint=endpoint,
            signer_roster_ref=str(common_payload["signer_roster_ref"]),
            signer_roster_digest=str(common_payload["signer_roster_digest"]),
            signer_key_ref=str(common_payload["signer_key_ref"]),
            signer_jurisdiction=str(common_payload["signer_jurisdiction"]),
            external_funding_policy_digest=str(
                common_payload["external_funding_policy_digest"]
            ),
            funding_policy_signature_digest=str(
                common_payload["funding_policy_signature_digest"]
            ),
            verifier_ref=backup_verifier_ref,
            challenge_ref=backup_challenge_ref,
            verifier_authority_ref=backup_authority_ref,
            verifier_jurisdiction=backup_jurisdiction,
            verifier_route_ref=backup_route_ref,
            authority_chain_ref=backup_authority_chain_ref,
            trust_root_ref=backup_trust_root_ref,
            trust_root_digest=backup_trust_root_digest,
            request_timeout_ms=500,
        )
    quorum_receipt = service.build_subsidy_signer_roster_verifier_quorum_receipt(
        verifier_receipts=[primary_receipt, backup_receipt],
        primary_verifier_receipt_digest=primary_receipt["digest"],
    )
    return primary_receipt, backup_receipt, quorum_receipt


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

        draft_receipt = service.evaluate_voluntary_subsidy(
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
        primary_verifier, _backup_verifier, verifier_quorum = (
            build_live_subsidy_verifier_quorum(service, draft_receipt)
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
            signer_roster_verifier_receipt=primary_verifier,
            signer_roster_verifier_quorum_receipt=verifier_quorum,
        )
        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(receipt["voluntary_subsidy_allowed"])
        self.assertEqual("accepted", receipt["subsidy_status"])
        self.assertTrue(receipt["floor_protection_preserved"])
        self.assertTrue(receipt["donor_floor_preserved"])
        self.assertTrue(receipt["all_consent_digests_valid"])
        self.assertTrue(receipt["funding_policy_signature_bound"])
        self.assertTrue(receipt["signer_roster_verifier_bound"])
        self.assertTrue(receipt["signer_roster_verifier_quorum_bound"])
        self.assertEqual(
            "verified",
            receipt["signer_roster_verifier_receipt"]["verifier_receipt_status"],
        )
        self.assertEqual(
            "complete",
            receipt["signer_roster_verifier_quorum_receipt"]["quorum_status"],
        )
        self.assertEqual(
            receipt["signer_roster_verifier_receipt"]["digest"],
            receipt["signer_roster_verifier_receipt_digest"],
        )
        self.assertTrue(receipt["revocation_registry_bound"])
        self.assertTrue(receipt["audit_authority_bound"])
        self.assertTrue(receipt["jurisdiction_authority_bound"])
        self.assertEqual("verified", receipt["authority_binding_status"])
        self.assertFalse(receipt["cross_identity_offset_used"])
        self.assertFalse(receipt["raw_funding_payload_stored"])
        self.assertFalse(receipt["raw_authority_payload_stored"])
        self.assertEqual(8, receipt["total_accepted_jps"])

    def test_live_subsidy_verifier_endpoint_binds_network_response_digest(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://subsidy-live-verifier",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/subsidy-live-a",
                    "workload_class": "migration",
                    "requested_budget_jps": 22,
                    "observed_capacity_jps": 30,
                },
                {
                    "identity_id": "identity://energy-budget/subsidy-live-b",
                    "workload_class": "council",
                    "requested_budget_jps": 38,
                    "observed_capacity_jps": 32,
                },
            ],
        )
        subsidy_offers = [
            {
                "donor_identity_id": "identity://energy-budget/subsidy-live-b",
                "recipient_identity_id": "identity://energy-budget/subsidy-live-a",
                "offered_jps": 8,
                "consent_ref": "consent://energy-budget/live-b-to-a/v1",
                "revocation_ref": "revocation://energy-budget/live-b-to-a/v1",
            }
        ]
        draft_receipt = service.evaluate_voluntary_subsidy(
            pool_receipt=pool_receipt,
            subsidy_offers=subsidy_offers,
            external_funding_policy_ref="funding-policy://energy-budget/live-subsidy/v1",
            funding_policy_signature_ref="signature://energy-budget/live-subsidy/v1",
        )
        live_verifier_receipt, _backup_verifier, verifier_quorum = (
            build_live_subsidy_verifier_quorum(service, draft_receipt)
        )

        verifier_validation = service.validate_subsidy_signer_roster_verifier_receipt(
            live_verifier_receipt
        )
        self.assertTrue(verifier_validation["ok"])
        self.assertTrue(verifier_validation["network_probe_bound"])
        self.assertTrue(verifier_validation["signed_response_envelope_bound"])
        self.assertEqual(
            "live-http-json-energy-subsidy-signer-roster-verifier-v1",
            live_verifier_receipt["verifier_transport_profile"],
        )
        self.assertEqual(
            "signed-energy-subsidy-verifier-response-envelope-v1",
            live_verifier_receipt["response_envelope_profile"],
        )
        self.assertTrue(
            live_verifier_receipt["response_signing_key_ref"].startswith(
                "verifier-key://"
            )
        )
        self.assertEqual(64, len(live_verifier_receipt["response_signature_digest"]))
        self.assertTrue(live_verifier_receipt["signed_response_envelope_bound"])
        self.assertFalse(
            live_verifier_receipt["raw_response_signature_payload_stored"]
        )
        self.assertTrue(live_verifier_receipt["verifier_endpoint_ref"].startswith("http://"))
        self.assertEqual(64, len(live_verifier_receipt["network_response_digest"]))

        receipt = service.evaluate_voluntary_subsidy(
            pool_receipt=pool_receipt,
            subsidy_offers=subsidy_offers,
            external_funding_policy_ref="funding-policy://energy-budget/live-subsidy/v1",
            funding_policy_signature_ref="signature://energy-budget/live-subsidy/v1",
            signer_roster_verifier_receipt=live_verifier_receipt,
            signer_roster_verifier_quorum_receipt=verifier_quorum,
        )
        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(receipt["signer_roster_verifier_bound"])
        self.assertTrue(receipt["signer_roster_verifier_quorum_bound"])
        self.assertTrue(
            receipt["signer_roster_verifier_quorum_receipt"][
                "signed_response_envelope_quorum_bound"
            ]
        )
        self.assertEqual(
            [
                live_verifier_receipt["response_signature_digest"],
                verifier_quorum["verifier_receipts"][1]["response_signature_digest"],
            ],
            receipt["signer_roster_verifier_quorum_receipt"][
                "accepted_verifier_response_signature_digests"
            ],
        )
        self.assertEqual(
            "complete",
            receipt["signer_roster_verifier_quorum_receipt"]["quorum_status"],
        )
        self.assertTrue(
            receipt["signer_roster_verifier_receipt"]["network_probe_bound"]
        )
        self.assertFalse(
            receipt["signer_roster_verifier_receipt"]["raw_verifier_payload_stored"]
        )

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

    def test_voluntary_subsidy_validation_rejects_tampered_signer_roster_digest(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://subsidy-authority-tamper",
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
        receipt["funding_policy_signer_roster_digest"] = "0" * 64

        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertIn("funding_policy_signer_roster_digest mismatch", validation["errors"])
        self.assertIn("digest must match voluntary subsidy receipt payload", validation["errors"])

    def test_voluntary_subsidy_validation_rejects_tampered_verifier_receipt(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://subsidy-verifier-tamper",
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
        draft_receipt = service.evaluate_voluntary_subsidy(
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
        primary_verifier, _backup_verifier, verifier_quorum = (
            build_live_subsidy_verifier_quorum(service, draft_receipt)
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
            signer_roster_verifier_receipt=primary_verifier,
            signer_roster_verifier_quorum_receipt=verifier_quorum,
        )
        receipt["signer_roster_verifier_receipt"]["response_digest"] = "0" * 64

        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["signer_roster_verifier_bound"])
        self.assertIn("signer_roster_verifier_bound mismatch", validation["errors"])
        self.assertIn(
            "signer_roster_verifier_receipt: response_digest mismatch",
            validation["errors"],
        )
        self.assertIn("authority_binding_status mismatch", validation["errors"])

    def test_voluntary_subsidy_validation_rejects_tampered_response_signature(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://subsidy-signature-tamper",
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
        draft_receipt = service.evaluate_voluntary_subsidy(
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
        primary_verifier, _backup_verifier, verifier_quorum = (
            build_live_subsidy_verifier_quorum(service, draft_receipt)
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
            signer_roster_verifier_receipt=primary_verifier,
            signer_roster_verifier_quorum_receipt=verifier_quorum,
        )
        receipt["signer_roster_verifier_receipt"]["response_signature_digest"] = (
            "0" * 64
        )

        validation = service.validate_voluntary_subsidy_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["signer_roster_verifier_bound"])
        self.assertIn("signer_roster_verifier_bound mismatch", validation["errors"])
        self.assertIn(
            "signer_roster_verifier_receipt: response_signature_digest mismatch",
            validation["errors"],
        )
        self.assertIn(
            "signer_roster_verifier_receipt: signed_response_envelope_bound mismatch",
            validation["errors"],
        )

    def test_shared_fabric_capacity_derives_member_shortfalls(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://fabric",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/fabric-a",
                    "workload_class": "migration",
                    "requested_budget_jps": 30,
                    "observed_capacity_jps": 30,
                },
                {
                    "identity_id": "identity://energy-budget/fabric-b",
                    "workload_class": "council",
                    "requested_budget_jps": 24,
                    "observed_capacity_jps": 24,
                },
            ],
        )
        draft_receipt = service.allocate_shared_fabric_capacity(
            pool_receipt=pool_receipt,
            fabric_id="shared-fabric://unit",
            observed_shared_capacity_jps=50,
        )
        signals = [
            {
                "signal_id": f"broker-signal-{allocation['identity_id'].rsplit('/', 1)[-1]}",
                "identity_id": allocation["identity_id"],
                "minimum_joules_per_second": allocation["required_floor_jps"],
                "current_joules_per_second": allocation["allocated_capacity_jps"],
                "severity": "critical",
                "recommended_action": "migrate-standby",
            }
            for allocation in draft_receipt["member_allocations"]
        ]

        receipt = service.allocate_shared_fabric_capacity(
            pool_receipt=pool_receipt,
            fabric_id="shared-fabric://unit",
            observed_shared_capacity_jps=50,
            shared_fabric_observation_ref="fabric-observation://unit/shared/v1",
            member_broker_signals=signals,
        )
        validation = service.validate_shared_fabric_allocation_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertFalse(receipt["shared_capacity_floor_preserved"])
        self.assertFalse(receipt["all_member_floors_preserved"])
        self.assertEqual(4, receipt["fabric_capacity_deficit_jps"])
        self.assertEqual(2, receipt["impacted_member_count"])
        self.assertEqual("fabric-capacity-deficit-protected", receipt["budget_status"])
        self.assertFalse(receipt["degradation_allowed"])
        self.assertTrue(receipt["broker_signal_bound"])
        self.assertFalse(receipt["raw_capacity_payload_stored"])
        self.assertEqual(
            {
                "identity://energy-budget/fabric-a": 28,
                "identity://energy-budget/fabric-b": 22,
            },
            {
                allocation["identity_id"]: allocation["allocated_capacity_jps"]
                for allocation in receipt["member_allocations"]
            },
        )

    def test_shared_fabric_validation_rejects_tampered_allocation(self) -> None:
        service = EnergyBudgetService()
        pool_receipt = service.evaluate_pool_floor(
            pool_id="energy-pool://fabric-tamper",
            member_requests=[
                {
                    "identity_id": "identity://energy-budget/fabric-a",
                    "workload_class": "migration",
                    "requested_budget_jps": 30,
                    "observed_capacity_jps": 30,
                },
                {
                    "identity_id": "identity://energy-budget/fabric-b",
                    "workload_class": "council",
                    "requested_budget_jps": 24,
                    "observed_capacity_jps": 24,
                },
            ],
        )
        draft_receipt = service.allocate_shared_fabric_capacity(
            pool_receipt=pool_receipt,
            fabric_id="shared-fabric://tamper",
            observed_shared_capacity_jps=50,
        )
        signals = [
            {
                "signal_id": f"broker-signal-{allocation['identity_id'].rsplit('/', 1)[-1]}",
                "identity_id": allocation["identity_id"],
                "minimum_joules_per_second": allocation["required_floor_jps"],
                "current_joules_per_second": allocation["allocated_capacity_jps"],
                "severity": "critical",
                "recommended_action": "migrate-standby",
            }
            for allocation in draft_receipt["member_allocations"]
        ]
        receipt = service.allocate_shared_fabric_capacity(
            pool_receipt=pool_receipt,
            fabric_id="shared-fabric://tamper",
            observed_shared_capacity_jps=50,
            member_broker_signals=signals,
        )
        receipt["member_allocations"][0]["allocated_capacity_jps"] = 29

        validation = service.validate_shared_fabric_allocation_receipt(receipt)

        self.assertFalse(validation["ok"])
        self.assertIn(
            "allocated_capacity_jps must match allocation strategy",
            validation["errors"],
        )
        self.assertIn("capacity_shortfall_jps mismatch", validation["errors"])
        self.assertIn(
            "digest must match shared fabric allocation receipt payload",
            validation["errors"],
        )


if __name__ == "__main__":
    unittest.main()
