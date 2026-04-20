from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import ssl
import tempfile
import threading
import unittest

from omoikane.agentic.cognitive_audit import CognitiveAuditService
from omoikane.agentic.cognitive_audit_governance import CognitiveAuditGovernanceService
from omoikane.agentic.consensus_bus import ConsensusBus
from omoikane.agentic.council import Council, CouncilMember, CouncilVote, DistributedCouncilVote
from omoikane.agentic.distributed_transport import DistributedTransportService
from omoikane.agentic.distributed_transport_mtls_fixtures import (
    CA_BUNDLE_REF,
    CLIENT_CERTIFICATE_REF,
    MTLS_SERVER_NAME,
    write_fixture_bundle,
)
from omoikane.agentic.task_graph import TaskGraphService
from omoikane.agentic.trust import TrustService
from omoikane.common import canonical_json, sha256_text


class CouncilTests(unittest.TestCase):
    def test_guardian_veto_overrides_majority(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("guardian", "guardian", 0.99, is_guardian=True))

        proposal = council.propose("Patch", "change", "test rationale")
        decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "looks good"),
                CouncilVote("committee", "approve", "acceptable"),
                CouncilVote("guardian", "veto", "immutable boundary"),
            ],
        )

        self.assertEqual("vetoed", decision.outcome)
        self.assertEqual("guardian-veto", decision.timeout_status.fallback_applied)

    def test_soft_timeout_falls_back_to_weighted_majority(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        proposal = council.propose("Patch", "change", "test rationale", session_mode="standard")
        decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "docs ready"),
                CouncilVote("committee", "approve", "ethics okay"),
                CouncilVote("archivist", "reject", "log detail不足"),
            ],
            elapsed_ms=50_000,
            rounds_completed=3,
        )

        self.assertEqual("approved", decision.outcome)
        self.assertEqual("timeout-fallback", decision.decision_mode)
        self.assertEqual("soft-timeout", decision.timeout_status.status)
        self.assertEqual("weighted-majority", decision.timeout_status.fallback_applied)

    def test_hard_timeout_defers_expedited_session(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("guardian", "guardian", 0.99, is_guardian=True))

        proposal = council.propose("Emergency", "stabilize", "test rationale", session_mode="expedited")
        decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "containment first"),
                CouncilVote("guardian", "approve", "follow-up review required"),
            ],
            elapsed_ms=1_500,
            rounds_completed=2,
        )

        self.assertEqual("deferred", decision.outcome)
        self.assertEqual("expedited", decision.decision_mode)
        self.assertEqual("hard-timeout", decision.timeout_status.status)
        self.assertEqual("schedule-standard-session", decision.timeout_status.follow_up_action)

    def test_cross_self_scope_requests_federation(self) -> None:
        council = Council()

        proposal = council.propose(
            "Shared reality merge",
            "federation review",
            "複数 identity をまたぐため federation に送る",
            target_identity_ids=["identity://a", "identity://b"],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-cross-self")

        self.assertEqual("cross-self", topology.scope)
        self.assertTrue(topology.federation_request.convened)
        self.assertEqual("external-pending", topology.federation_request.status)
        self.assertEqual([], topology.heritage_request.clauses)

    def test_interpretive_scope_requests_heritage(self) -> None:
        council = Council()

        proposal = council.propose(
            "Interpret ethics axiom",
            "heritage ruling",
            "規約解釈を heritage に送る",
            target_identity_ids=["identity://a"],
            referenced_clauses=["ethics_axiom.A2"],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-interpretive")

        self.assertEqual("interpretive", topology.scope)
        self.assertTrue(topology.heritage_request.convened)
        self.assertEqual("external-pending", topology.heritage_request.status)
        self.assertEqual([], topology.federation_request.participants)

    def test_ambiguous_scope_blocks_external_requests_until_reclassified(self) -> None:
        council = Council()

        proposal = council.propose(
            "Cross-self ethics rewrite",
            "block pending reclassification",
            "cross-self と interpretive が競合する",
            target_identity_ids=["identity://a", "identity://b"],
            referenced_clauses=["governance.freeze"],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-ambiguous")

        self.assertEqual("ambiguous", topology.scope)
        self.assertFalse(topology.federation_request.convened)
        self.assertFalse(topology.heritage_request.convened)
        self.assertEqual("none", topology.federation_request.status)
        self.assertEqual("none", topology.heritage_request.status)

    def test_federation_resolution_promotes_advisory_cross_self_review(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        proposal = council.propose(
            "Shared reality merge",
            "merge",
            "cross-self federation returned result",
            target_identity_ids=["identity://a", "identity://b"],
        )
        local_decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "advisory approve"),
                CouncilVote("committee", "approve", "consent bundle okay"),
                CouncilVote("archivist", "reject", "monitor drift"),
            ],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-cross-self")
        resolution = council.resolve_federation_review(
            topology,
            local_decision=local_decision,
            votes=[
                DistributedCouncilVote("identity://a", "approve", "self approves"),
                DistributedCouncilVote("identity://b", "approve", "peer approves"),
                DistributedCouncilVote("guardian://neutral-federation", "approve", "guardian approves"),
            ],
        )

        self.assertEqual("federation", resolution.council_tier)
        self.assertEqual("advisory", resolution.local_binding_status)
        self.assertEqual("binding-approved", resolution.final_outcome)
        self.assertEqual("weighted-majority", resolution.decision_mode)
        self.assertEqual(3, resolution.vote_summary.quorum)

    def test_heritage_resolution_allows_ethics_committee_single_veto(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        proposal = council.propose(
            "Interpret ethics axiom",
            "rewrite",
            "heritage returned result",
            target_identity_ids=["identity://a"],
            referenced_clauses=["ethics_axiom.A2"],
        )
        local_decision = council.deliberate(
            proposal,
            [
                CouncilVote("architect", "approve", "local wording acceptable"),
                CouncilVote("committee", "approve", "local review okay"),
                CouncilVote("archivist", "approve", "continuity okay"),
            ],
        )
        topology = council.route_topology(proposal, local_session_ref="local-session-interpretive")
        resolution = council.resolve_heritage_review(
            topology,
            local_decision=local_decision,
            votes=[
                DistributedCouncilVote("heritage://culture-a", "approve", "culture a okay"),
                DistributedCouncilVote("heritage://culture-b", "approve", "culture b okay"),
                DistributedCouncilVote("heritage://legal-advisor", "approve", "law okay"),
                DistributedCouncilVote("heritage://ethics-committee", "veto", "ethics blocks"),
            ],
        )

        self.assertEqual("heritage", resolution.council_tier)
        self.assertEqual("blocked", resolution.local_binding_status)
        self.assertEqual("binding-rejected", resolution.final_outcome)
        self.assertEqual("ethics-veto", resolution.decision_mode)
        self.assertEqual("heritage-overrides-local", resolution.conflict_resolution)
        self.assertTrue(resolution.vote_summary.veto_triggered)

    def test_distributed_conflict_escalates_to_human_governance(self) -> None:
        council = Council()
        council.register(CouncilMember("architect", "councilor", 0.6))
        council.register(CouncilMember("committee", "councilor", 0.7))
        council.register(CouncilMember("archivist", "councilor", 0.55))

        federation_proposal = council.propose(
            "Shared reality merge",
            "merge",
            "cross-self federation returned result",
            target_identity_ids=["identity://a", "identity://b"],
        )
        federation_local = council.deliberate(
            federation_proposal,
            [
                CouncilVote("architect", "approve", "advisory approve"),
                CouncilVote("committee", "approve", "consent okay"),
                CouncilVote("archivist", "reject", "monitor drift"),
            ],
        )
        federation_topology = council.route_topology(
            federation_proposal,
            local_session_ref="local-session-cross-self",
        )
        federation_resolution = council.resolve_federation_review(
            federation_topology,
            local_decision=federation_local,
            votes=[
                DistributedCouncilVote("identity://a", "approve", "self approves"),
                DistributedCouncilVote("identity://b", "approve", "peer approves"),
                DistributedCouncilVote("guardian://neutral-federation", "approve", "guardian approves"),
            ],
        )

        heritage_proposal = council.propose(
            "Interpret identity axiom",
            "rewrite",
            "heritage returned result",
            target_identity_ids=["identity://a"],
            referenced_clauses=["identity_axiom.A2"],
        )
        heritage_local = council.deliberate(
            heritage_proposal,
            [
                CouncilVote("architect", "approve", "local wording acceptable"),
                CouncilVote("committee", "approve", "local review okay"),
                CouncilVote("archivist", "approve", "continuity okay"),
            ],
        )
        heritage_topology = council.route_topology(
            heritage_proposal,
            local_session_ref="local-session-interpretive",
        )
        heritage_resolution = council.resolve_heritage_review(
            heritage_topology,
            local_decision=heritage_local,
            votes=[
                DistributedCouncilVote("heritage://culture-a", "approve", "culture a okay"),
                DistributedCouncilVote("heritage://culture-b", "approve", "culture b okay"),
                DistributedCouncilVote("heritage://legal-advisor", "approve", "law okay"),
                DistributedCouncilVote("heritage://ethics-committee", "veto", "ethics blocks"),
            ],
        )

        conflict_local = council.deliberate(
            council.propose(
                "Composite conflict",
                "escalate",
                "federation と heritage の衝突",
                target_identity_ids=["identity://a"],
            ),
            [
                CouncilVote("architect", "approve", "local escalation candidate"),
                CouncilVote("committee", "approve", "external結果待ち"),
                CouncilVote("archivist", "approve", "human判断が必要"),
            ],
        )
        conflict = council.reconcile_distributed_conflict(
            "proposal-conflict-001",
            local_decision=conflict_local,
            federation_resolution=federation_resolution,
            heritage_resolution=heritage_resolution,
        )

        self.assertEqual("human-governance", conflict.council_tier)
        self.assertEqual("escalate-human-governance", conflict.final_outcome)
        self.assertEqual("conflict-escalation", conflict.decision_mode)
        self.assertEqual("escalated-to-human-governance", conflict.conflict_resolution)
        self.assertEqual(2, len(conflict.external_resolution_refs))


class TaskGraphServiceTests(unittest.TestCase):
    def test_build_graph_returns_bounded_reference_shape(self) -> None:
        service = TaskGraphService()

        graph = service.build_graph(
            intent="runtime と spec を同期する",
            required_roles=["schema-builder", "eval-builder", "doc-sync-builder"],
        )
        validation = service.validate_graph(graph)

        self.assertTrue(validation["ok"])
        self.assertEqual(5, validation["node_count"])
        self.assertEqual(4, validation["edge_count"])
        self.assertEqual(3, validation["max_depth"])
        self.assertEqual(3, validation["root_count"])

    def test_build_graph_rejects_parallelism_over_policy(self) -> None:
        service = TaskGraphService()

        with self.assertRaises(ValueError):
            service.build_graph(
                intent="4 roles を同時に走らせる",
                required_roles=["schema-builder", "eval-builder", "doc-sync-builder", "codex-builder"],
            )


class ConsensusBusTests(unittest.TestCase):
    def test_publish_records_bus_only_message_and_audit_sequence(self) -> None:
        service = ConsensusBus()
        session_id = "session-consensus-001"

        service.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="broadcast",
            intent="dispatch",
            phase="brief",
            payload={"graph_id": "graph-001", "ready_node_ids": ["node-1"]},
            related_claim_ids=["node-1"],
        )
        message = service.publish(
            session_id=session_id,
            sender_role="integrity-guardian",
            recipient="council",
            intent="gate",
            phase="gate",
            payload={"guardian_status": "pass"},
            related_claim_ids=["node-1"],
            ethics_check_id="ethics://consensus-001",
        )
        service.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="broadcast",
            intent="resolve",
            phase="resolve",
            payload={"artifact_ref": "artifact://summary"},
            related_claim_ids=["node-result-synthesis"],
        )

        audit = service.audit_session(session_id)

        self.assertEqual("consensus-bus-only", message["transport_profile"])
        self.assertEqual("council", message["delivery_scope"])
        self.assertTrue(audit["all_transport_bus_only"])
        self.assertTrue(audit["guardian_gate_present"])
        self.assertTrue(audit["ordered_phases"])
        self.assertEqual("resolve", audit["last_phase"])

    def test_reject_direct_message_records_blocked_attempt(self) -> None:
        service = ConsensusBus()

        blocked = service.reject_direct_message(
            session_id="session-consensus-002",
            sender_role="MemoryRetriever",
            recipient="agent://narrative-writer",
            attempted_intent="report",
            reason="use the bus",
        )
        audit = service.audit_session("session-consensus-002")

        self.assertEqual("blocked", blocked["status"])
        self.assertEqual("consensus-bus-only", blocked["enforced_policy"])
        self.assertEqual(1, audit["blocked_direct_attempts"])


class DistributedTransportServiceTests(unittest.TestCase):
    @staticmethod
    def _discover_non_loopback_ipv4() -> str:
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("192.0.2.1", 1))
            address = probe.getsockname()[0]
            probe.close()
            if address and not address.startswith("127."):
                return address
        except OSError:
            pass
        for family, _, _, _, sockaddr in socket.getaddrinfo(
            socket.gethostname(),
            None,
            socket.AF_INET,
            socket.SOCK_STREAM,
        ):
            if family == socket.AF_INET:
                address = sockaddr[0]
                if address and not address.startswith("127."):
                    return address
        raise RuntimeError("non-loopback IPv4 address could not be discovered for authority route tests")

    @contextmanager
    def _root_directory_server(self, payload: dict[str, object]):
        class LocalThreadingHTTPServer(ThreadingHTTPServer):
            def server_bind(self) -> None:
                self.socket.bind(self.server_address)
                self.server_address = self.socket.getsockname()
                host, port = self.server_address[:2]
                self.server_name = str(host)
                self.server_port = int(port)

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

        server = LocalThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}/root-directory"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    @contextmanager
    def _authority_plane_servers(self, payloads: list[dict[str, object]]):
        payload_by_path = {
            f"/key-server-{index}": payload
            for index, payload in enumerate(payloads, start=1)
        }

        class LocalThreadingHTTPServer(ThreadingHTTPServer):
            def server_bind(self) -> None:
                self.socket.bind(self.server_address)
                self.server_address = self.socket.getsockname()
                host, port = self.server_address[:2]
                self.server_name = str(host)
                self.server_port = int(port)

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def do_GET(self) -> None:  # noqa: N802
                payload = payload_by_path.get(self.path)
                if payload is None:
                    self.send_error(404)
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

        server = LocalThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            yield [f"{base_url}{path}" for path in payload_by_path]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    @contextmanager
    def _authority_route_servers(
        self,
        payloads: list[dict[str, object]],
        *,
        bind_host: str,
        ca_cert_path: str,
        server_cert_path: str,
        server_key_path: str,
    ):
        payload_by_path = {
            f"/authority-route-{index}": payload
            for index, payload in enumerate(payloads, start=1)
        }

        class LocalThreadingHTTPServer(ThreadingHTTPServer):
            def server_bind(self) -> None:
                self.socket.bind(self.server_address)
                self.server_address = self.socket.getsockname()
                host, port = self.server_address[:2]
                self.server_name = str(host)
                self.server_port = int(port)

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:  # noqa: N802
                payload = payload_by_path.get(self.path)
                if payload is None:
                    self.send_error(404)
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

        server = LocalThreadingHTTPServer((bind_host, 0), Handler)
        server.daemon_threads = True
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_cert_chain(server_cert_path, server_key_path)
        ssl_context.load_verify_locations(cafile=ca_cert_path)
        server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"https://{bind_host}:{server.server_address[1]}"
        try:
            yield [
                {
                    "key_server_ref": payload["key_server_ref"],
                    "server_endpoint": f"{base_url}{path}",
                    "server_name": MTLS_SERVER_NAME,
                }
                for path, payload in payload_by_path.items()
            ]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    def test_federation_handoff_binds_liaison_quorum_and_guardian(self) -> None:
        service = DistributedTransportService()

        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-001",
            proposal_ref="proposal-transport-001",
            payload_ref="cas://sha256/test-federation",
            payload_digest=sha256_text(canonical_json({"scope": "cross-self"})),
            participant_identity_ids=["identity://a", "identity://b"],
        )

        self.assertEqual("federation", envelope.council_tier)
        self.assertEqual("federation-mtls-quorum-v1", envelope.transport_profile)
        self.assertEqual(3, envelope.quorum)
        self.assertEqual(1, envelope.key_epoch)
        self.assertEqual([1], envelope.accepted_key_epochs)
        self.assertEqual(
            ["guardian", "self-liaison", "self-liaison"],
            sorted(attestation.role for attestation in envelope.participant_attestations),
        )

    def test_heritage_receipt_authenticates_and_blocks_replay(self) -> None:
        service = DistributedTransportService()

        envelope = service.issue_heritage_handoff(
            topology_ref="topology-transport-heritage-001",
            proposal_ref="proposal-transport-heritage-001",
            payload_ref="cas://sha256/test-heritage",
            payload_digest=sha256_text(canonical_json({"scope": "interpretive"})),
            referenced_clauses=["identity_axiom.A2"],
        )
        receipt = service.record_receipt(
            envelope,
            result_ref="resolution://heritage/001",
            result_digest=sha256_text(canonical_json({"final_outcome": "binding-rejected"})),
            participant_ids=[
                "heritage://culture-a",
                "heritage://culture-b",
                "heritage://legal-advisor",
                "heritage://ethics-committee",
            ],
            channel_binding_ref=envelope.channel_binding_ref,
        )
        replay = service.record_receipt(
            envelope,
            result_ref="resolution://heritage/replay",
            result_digest=sha256_text(canonical_json({"final_outcome": "binding-rejected"})),
            participant_ids=[
                "heritage://culture-a",
                "heritage://culture-b",
                "heritage://legal-advisor",
                "heritage://ethics-committee",
            ],
            channel_binding_ref=envelope.channel_binding_ref,
        )

        self.assertEqual("authenticated", receipt.receipt_status)
        self.assertTrue(receipt.authenticity_checks["required_roles_satisfied"])
        self.assertEqual("replay-blocked", replay.receipt_status)
        self.assertEqual("blocked", replay.authenticity_checks["replay_guard_status"])

    def test_receipt_rejects_channel_mismatch(self) -> None:
        service = DistributedTransportService()

        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-002",
            proposal_ref="proposal-transport-002",
            payload_ref="cas://sha256/test-federation",
            payload_digest=sha256_text(canonical_json({"scope": "cross-self"})),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        receipt = service.record_receipt(
            envelope,
            result_ref="resolution://federation/rejected",
            result_digest=sha256_text(canonical_json({"final_outcome": "binding-rejected"})),
            participant_ids=["identity://a", "identity://b", "guardian://neutral-federation"],
            channel_binding_ref="channel-binding://federation/mismatch",
        )

        self.assertEqual("rejected", receipt.receipt_status)
        self.assertFalse(receipt.authenticity_checks["channel_authenticated"])

    def test_key_rotation_requires_federated_roots_and_blocks_reused_hop_chain(self) -> None:
        service = DistributedTransportService()

        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-rotation-001",
            proposal_ref="proposal-transport-rotation-001",
            payload_ref="cas://sha256/test-rotation",
            payload_digest=sha256_text(canonical_json({"scope": "cross-self", "rotation": True})),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        receipt = service.record_receipt(
            rotated,
            result_ref="resolution://federation/rotation-authenticated",
            result_digest=sha256_text(canonical_json({"final_outcome": "binding-approved", "epoch": 2})),
            participant_ids=["identity://a", "identity://b", "guardian://neutral-federation"],
            channel_binding_ref=rotated.channel_binding_ref,
            verified_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            key_epoch=2,
            hop_nonce_chain=["hop://relay-a/nonce-001", "hop://relay-b/nonce-001"],
        )
        reissue = service.issue_federation_handoff(
            topology_ref="topology-transport-rotation-002",
            proposal_ref="proposal-transport-rotation-002",
            payload_ref="cas://sha256/test-rotation-reissue",
            payload_digest=sha256_text(canonical_json({"scope": "cross-self", "rotation": "reissue"})),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        replay = service.record_receipt(
            reissue,
            result_ref="resolution://federation/rotation-replay",
            result_digest=sha256_text(canonical_json({"final_outcome": "binding-approved", "epoch": 1})),
            participant_ids=["identity://a", "identity://b", "guardian://neutral-federation"],
            channel_binding_ref=reissue.channel_binding_ref,
            verified_root_refs=["root://federation/pki-a"],
            key_epoch=1,
            hop_nonce_chain=["hop://relay-a/nonce-001", "hop://relay-b/nonce-001"],
        )
        telemetry = service.capture_relay_telemetry(
            rotated,
            receipt,
            relay_path=[
                {
                    "relay_id": "relay://federation/edge-a",
                    "relay_endpoint": "relay://federation/edge-a",
                    "jurisdiction": "JP-13",
                    "network_zone": "apne1",
                    "observed_latency_ms": 11.2,
                    "root_refs_seen": ["root://federation/pki-a"],
                },
                {
                    "relay_id": "relay://federation/edge-b",
                    "relay_endpoint": "relay://federation/edge-b",
                    "jurisdiction": "US-CA",
                    "network_zone": "usw2",
                    "observed_latency_ms": 15.8,
                    "root_refs_seen": ["root://federation/pki-a", "root://federation/pki-b"],
                },
            ],
        )
        replay_telemetry = service.capture_relay_telemetry(
            reissue,
            replay,
            relay_path=[
                {
                    "relay_id": "relay://federation/edge-a",
                    "relay_endpoint": "relay://federation/edge-a",
                    "jurisdiction": "JP-13",
                    "network_zone": "apne1",
                    "observed_latency_ms": 12.0,
                    "root_refs_seen": ["root://federation/pki-a"],
                },
                {
                    "relay_id": "relay://federation/edge-b",
                    "relay_endpoint": "relay://federation/edge-b",
                    "jurisdiction": "US-CA",
                    "network_zone": "usw2",
                    "observed_latency_ms": 16.4,
                    "root_refs_seen": ["root://federation/pki-a"],
                },
            ],
        )

        self.assertEqual(2, rotated.key_epoch)
        self.assertEqual([1, 2], rotated.accepted_key_epochs)
        self.assertEqual(2, rotated.trust_root_quorum)
        self.assertEqual("authenticated", receipt.receipt_status)
        self.assertTrue(receipt.authenticity_checks["federated_roots_verified"])
        self.assertTrue(receipt.authenticity_checks["key_epoch_accepted"])
        self.assertEqual("replay-blocked", replay.receipt_status)
        self.assertEqual("blocked", replay.authenticity_checks["multi_hop_replay_status"])
        self.assertEqual("authenticated", telemetry.end_to_end_status)
        self.assertEqual("accepted", telemetry.anti_replay_status)
        self.assertEqual(2, telemetry.hop_count)
        self.assertAlmostEqual(27.0, telemetry.total_latency_ms)
        self.assertEqual("authenticated", telemetry.relay_hops[-1].delivery_status)
        self.assertEqual("replay-blocked", replay_telemetry.end_to_end_status)
        self.assertEqual("blocked", replay_telemetry.anti_replay_status)
        self.assertEqual("replay-blocked", replay_telemetry.relay_hops[-1].delivery_status)

    def test_live_root_directory_probe_binds_quorum_and_endpoint_receipt(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-live-root-001",
            proposal_ref="proposal-transport-live-root-001",
            payload_ref="cas://sha256/test-live-root",
            payload_digest=sha256_text(canonical_json({"scope": "cross-self", "live_root": True})),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/live-window",
            "checked_at": "2026-04-20T02:10:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("live-root-window"),
        }

        with self._root_directory_server(payload) as endpoint:
            report = service.probe_live_root_directory(
                rotated,
                directory_endpoint=endpoint,
                request_timeout_ms=500,
            )

        self.assertEqual(["root://federation/pki-a", "root://federation/pki-b"], report.trusted_root_refs)
        self.assertEqual("reachable", report.connectivity_receipt.receipt_status)
        self.assertEqual(2, report.connectivity_receipt.matched_root_count)
        self.assertTrue(report.connectivity_receipt.quorum_satisfied)
        self.assertEqual(report.directory_ref, report.connectivity_receipt.directory_ref)

    def test_live_root_directory_probe_rejects_quorum_mismatch(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-live-root-mismatch-001",
            proposal_ref="proposal-transport-live-root-mismatch-001",
            payload_ref="cas://sha256/test-live-root-mismatch",
            payload_digest=sha256_text(canonical_json({"scope": "cross-self", "live_root": "mismatch"})),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/live-window-mismatch",
            "checked_at": "2026-04-20T02:11:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-a",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-mismatch"),
                    "status": "active",
                    "key_epoch": 2,
                }
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("live-root-window-mismatch"),
        }

        with self._root_directory_server(payload) as endpoint:
            with self.assertRaisesRegex(
                ValueError,
                "live root directory must satisfy envelope trust_root_quorum",
            ):
                service.probe_live_root_directory(
                    rotated,
                    directory_endpoint=endpoint,
                    request_timeout_ms=500,
                )

    def test_authority_plane_probe_binds_key_server_fleet_to_root_directory(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-001",
            proposal_ref="proposal-transport-authority-001",
            payload_ref="cas://sha256/test-authority-plane",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": True})
            ),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        root_directory_payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/authority-window",
            "checked_at": "2026-04-20T02:12:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window"),
        }
        authority_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:12:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-b-draining",
                "checked_at": "2026-04-20T02:12:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "draining",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-b"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-20T02:12:03Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c"),
            },
        ]

        with self._root_directory_server(root_directory_payload) as root_endpoint:
            root_directory = service.probe_live_root_directory(
                rotated,
                directory_endpoint=root_endpoint,
                request_timeout_ms=500,
            )
        with self._authority_plane_servers(authority_payloads) as authority_endpoints:
            authority_plane = service.probe_authority_plane(
                rotated,
                root_directory,
                authority_endpoints=authority_endpoints,
                request_timeout_ms=500,
            )

        self.assertEqual("bounded-key-server-fleet-v1", authority_plane.authority_profile)
        self.assertEqual("overlap-safe-authority-handoff-v1", authority_plane.churn_profile)
        self.assertEqual(3, authority_plane.reachable_server_count)
        self.assertEqual(2, authority_plane.active_server_count)
        self.assertEqual(1, authority_plane.draining_server_count)
        self.assertEqual(2, authority_plane.matched_root_count)
        self.assertTrue(authority_plane.churn_safe)
        self.assertEqual(
            ["root://federation/pki-a", "root://federation/pki-b"],
            authority_plane.trusted_root_refs,
        )
        self.assertEqual(
            [
                {
                    "root_ref": "root://federation/pki-a",
                    "active_server_refs": ["keyserver://federation/notary-a"],
                    "draining_server_refs": [],
                    "coverage_status": "stable",
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "active_server_refs": ["keyserver://federation/mirror-c-active"],
                    "draining_server_refs": ["keyserver://federation/mirror-b-draining"],
                    "coverage_status": "handoff-ready",
                },
            ],
            authority_plane.root_coverage,
        )
        self.assertEqual(root_directory.directory_ref, authority_plane.directory_ref)
        self.assertEqual(
            sha256_text(canonical_json(root_directory.to_dict())),
            authority_plane.directory_digest,
        )
        self.assertEqual(
            [
                "keyserver://federation/notary-a",
                "keyserver://federation/mirror-b-draining",
                "keyserver://federation/mirror-c-active",
            ],
            [server["key_server_ref"] for server in authority_plane.key_servers],
        )

    def test_authority_plane_probe_rejects_insufficient_root_coverage(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-mismatch-001",
            proposal_ref="proposal-transport-authority-mismatch-001",
            payload_ref="cas://sha256/test-authority-plane-mismatch",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "mismatch"})
            ),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        root_directory_payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/authority-window-mismatch",
            "checked_at": "2026-04-20T02:13:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-a",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-mismatch"),
                    "status": "active",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-mismatch"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-mismatch"),
        }
        authority_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:13:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-mismatch"),
            }
        ]

        with self._root_directory_server(root_directory_payload) as root_endpoint:
            root_directory = service.probe_live_root_directory(
                rotated,
                directory_endpoint=root_endpoint,
                request_timeout_ms=500,
            )
        with self._authority_plane_servers(authority_payloads) as authority_endpoints:
            with self.assertRaisesRegex(
                ValueError,
                "authority plane must satisfy envelope trust_root_quorum",
            ):
                service.probe_authority_plane(
                    rotated,
                    root_directory,
                    authority_endpoints=authority_endpoints,
                    request_timeout_ms=500,
                )

    def test_authority_plane_probe_rejects_draining_root_without_active_replacement(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-draining-001",
            proposal_ref="proposal-transport-authority-draining-001",
            payload_ref="cas://sha256/test-authority-plane-draining",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "draining-only"})
            ),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        root_directory_payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/authority-window-draining",
            "checked_at": "2026-04-20T02:14:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-draining"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-draining"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-draining"),
        }
        authority_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:14:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-draining"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-b-draining",
                "checked_at": "2026-04-20T02:14:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "draining",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-b-draining-only"),
            },
        ]

        with self._root_directory_server(root_directory_payload) as root_endpoint:
            root_directory = service.probe_live_root_directory(
                rotated,
                directory_endpoint=root_endpoint,
                request_timeout_ms=500,
            )
        with self._authority_plane_servers(authority_payloads) as authority_endpoints:
            with self.assertRaisesRegex(
                ValueError,
                "authority plane trusted root coverage must retain at least 1 active key server per root",
            ):
                service.probe_authority_plane(
                    rotated,
                    root_directory,
                    authority_endpoints=authority_endpoints,
                    request_timeout_ms=500,
                )

    def test_authority_churn_reconciliation_tracks_overlap_and_draining_exit(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-churn-001",
            proposal_ref="proposal-transport-authority-churn-001",
            payload_ref="cas://sha256/test-authority-plane-churn",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "churn"})
            ),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        root_directory_payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/authority-window-churn",
            "checked_at": "2026-04-20T02:15:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-churn"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-churn"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-churn"),
        }
        overlap_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:15:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-churn"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-b-draining",
                "checked_at": "2026-04-20T02:15:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "draining",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-b-churn"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-20T02:15:03Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c-churn"),
            },
        ]
        stable_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:15:11Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-churn-stable"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-20T02:15:12Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c-churn-stable"),
            },
        ]

        with self._root_directory_server(root_directory_payload) as root_endpoint:
            root_directory = service.probe_live_root_directory(
                rotated,
                directory_endpoint=root_endpoint,
                request_timeout_ms=500,
            )
        with self._authority_plane_servers(overlap_payloads) as authority_endpoints:
            overlap_plane = service.probe_authority_plane(
                rotated,
                root_directory,
                authority_endpoints=authority_endpoints,
                request_timeout_ms=500,
            )
        with self._authority_plane_servers(stable_payloads) as authority_endpoints:
            stable_plane = service.probe_authority_plane(
                rotated,
                root_directory,
                authority_endpoints=authority_endpoints,
                request_timeout_ms=500,
            )

        churn_window = service.reconcile_authority_churn(overlap_plane, stable_plane)

        self.assertEqual("bounded-key-server-churn-window-v1", churn_window.churn_profile)
        self.assertEqual(
            ["keyserver://federation/mirror-c-active", "keyserver://federation/notary-a"],
            churn_window.retained_server_refs,
        )
        self.assertEqual([], churn_window.added_server_refs)
        self.assertEqual(["keyserver://federation/mirror-b-draining"], churn_window.removed_server_refs)
        self.assertTrue(churn_window.continuity_guard["overlap_satisfied"])
        self.assertTrue(churn_window.continuity_guard["removed_servers_draining"])
        self.assertEqual("quorum-maintained", churn_window.continuity_guard["status"])

    def test_non_loopback_authority_route_trace_binds_mtls_socket_evidence(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-route-001",
            proposal_ref="proposal-transport-authority-route-001",
            payload_ref="cas://sha256/test-authority-route",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "route-trace"})
            ),
            participant_identity_ids=["identity://a", "identity://b"],
        )
        rotated = service.rotate_transport_keys(
            envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        root_directory_payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/authority-route-window",
            "checked_at": "2026-04-21T00:10:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-route"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-route"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-route"),
        }
        stable_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-21T00:10:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-route"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-21T00:10:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c-route"),
            },
        ]

        with self._root_directory_server(root_directory_payload) as root_endpoint:
            root_directory = service.probe_live_root_directory(
                rotated,
                directory_endpoint=root_endpoint,
                request_timeout_ms=500,
            )
        with self._authority_plane_servers(stable_payloads) as authority_endpoints:
            authority_plane = service.probe_authority_plane(
                rotated,
                root_directory,
                authority_endpoints=authority_endpoints,
                request_timeout_ms=500,
            )

        with tempfile.TemporaryDirectory(prefix="omoikane-authority-route-test-") as cert_dir:
            cert_bundle = write_fixture_bundle(cert_dir)
            bind_host = self._discover_non_loopback_ipv4()
            with self._authority_route_servers(
                stable_payloads,
                bind_host=bind_host,
                ca_cert_path=cert_bundle["ca_cert_path"],
                server_cert_path=cert_bundle["server_cert_path"],
                server_key_path=cert_bundle["server_key_path"],
            ) as route_targets:
                trace = service.trace_non_loopback_authority_routes(
                    rotated,
                    authority_plane,
                    route_targets=route_targets,
                    ca_cert_path=cert_bundle["ca_cert_path"],
                    ca_bundle_ref=CA_BUNDLE_REF,
                    client_cert_path=cert_bundle["client_cert_path"],
                    client_key_path=cert_bundle["client_key_path"],
                    client_certificate_ref=CLIENT_CERTIFICATE_REF,
                    request_timeout_ms=500,
                )

        self.assertEqual("authenticated", trace.trace_status)
        self.assertEqual(2, trace.route_count)
        self.assertEqual(2, trace.mtls_authenticated_count)
        self.assertEqual(CA_BUNDLE_REF, trace.ca_bundle_ref)
        self.assertEqual(CLIENT_CERTIFICATE_REF, trace.client_certificate_ref)
        self.assertEqual(MTLS_SERVER_NAME, trace.server_name)
        self.assertTrue(trace.non_loopback_verified)
        self.assertTrue(trace.authority_plane_bound)
        self.assertTrue(trace.response_digest_bound)
        self.assertTrue(trace.socket_trace_complete)
        self.assertEqual(authority_plane.digest, trace.authority_plane_digest)
        self.assertEqual(
            ["root://federation/pki-a", "root://federation/pki-b"],
            trace.trusted_root_refs,
        )
        self.assertTrue(
            all(
                binding["server_name"] == MTLS_SERVER_NAME
                and binding["mtls_status"] == "authenticated"
                and not binding["socket_trace"]["remote_ip"].startswith("127.")
                and binding["socket_trace"]["tls_version"].startswith("TLS")
                and binding["socket_trace"]["cipher_suite"]
                and binding["socket_trace"]["request_bytes"] > 0
                and binding["socket_trace"]["response_bytes"] > 0
                for binding in trace.route_bindings
            )
        )


class TaskGraphExecutionTests(unittest.TestCase):
    def test_dispatch_graph_marks_root_nodes_dispatched(self) -> None:
        service = TaskGraphService()
        graph = service.build_graph(
            intent="runtime と docs を同期する",
            required_roles=["schema-builder", "eval-builder", "doc-sync-builder"],
        )

        dispatch = service.dispatch_graph(
            graph_id=graph["graph_id"],
            nodes=graph["nodes"],
            complexity_policy=graph["complexity_policy"],
        )

        self.assertEqual(3, dispatch["dispatched_count"])
        self.assertEqual(["node-1", "node-2", "node-3"], dispatch["ready_node_ids"])
        self.assertEqual(
            ["dispatched", "dispatched", "dispatched"],
            [graph["nodes"][index]["status"] for index in range(3)],
        )

    def test_synthesize_results_respects_result_ref_limit(self) -> None:
        service = TaskGraphService()
        policy = service.policy()

        synthesis = service.synthesize_results(
            graph_id="graph-demo",
            result_refs=["artifact://schema", "artifact://eval", "artifact://docs"],
            complexity_policy=policy,
        )

        self.assertEqual(3, synthesis["accepted_result_count"])
        with self.assertRaises(ValueError):
            service.synthesize_results(
                graph_id="graph-demo",
                result_refs=[
                    "artifact://1",
                    "artifact://2",
                    "artifact://3",
                    "artifact://4",
                    "artifact://5",
                    "artifact://6",
                ],
                complexity_policy=policy,
            )


class TrustServiceTests(unittest.TestCase):
    def test_positive_event_updates_score_and_thresholds(self) -> None:
        service = TrustService()
        service.register_agent(
            "design-architect",
            initial_score=0.58,
            per_domain={"council_deliberation": 0.58},
        )

        event = service.record_event(
            "design-architect",
            event_type="council_quality_positive",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="Council",
            rationale="consistent review quality",
        )
        snapshot = service.snapshot("design-architect")

        self.assertEqual(0.04, event["applied_delta"])
        self.assertEqual(0.62, snapshot["global_score"])
        self.assertEqual(0.62, snapshot["per_domain"]["council_deliberation"])
        self.assertTrue(snapshot["eligibility"]["count_for_weighted_vote"])

    def test_human_pin_freezes_automatic_delta(self) -> None:
        service = TrustService()
        service.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )

        event = service.record_event(
            "integrity-guardian",
            event_type="human_feedback_bad",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="yasufumi",
            rationale="manual review pending",
        )
        snapshot = service.snapshot("integrity-guardian")

        self.assertFalse(event["applied"])
        self.assertEqual(0.0, event["applied_delta"])
        self.assertEqual(0.99, snapshot["global_score"])
        self.assertTrue(snapshot["eligibility"]["guardian_role"])
        self.assertEqual("guardian bootstrap", snapshot["pinned_reason"])


class CognitiveAuditTests(unittest.TestCase):
    def test_audit_record_binds_cross_layer_refs(self) -> None:
        service = CognitiveAuditService()

        record = service.create_record(
            identity_id="identity://audit-demo",
            qualia_tick={
                "tick_id": 3,
                "summary": "identity drift review",
                "attention_target": "identity-drift-review",
                "self_awareness": 0.88,
                "lucidity": 0.61,
                "valence": -0.19,
                "arousal": 0.67,
                "clarity": 0.58,
            },
            self_model_observation={
                "abrupt_change": True,
                "divergence": 0.41,
                "threshold": 0.35,
                "snapshot": {
                    "identity_id": "identity://audit-demo",
                    "values": ["continuity-first", "guardian-visible", "auditability"],
                    "goals": ["stabilize-review-loop", "preserve-identity-anchor"],
                    "traits": {"agency": 0.82, "stability": 0.41, "vigilance": 0.87},
                },
            },
            metacognition_report={
                "report_id": "metacognition-report-0123456789ab",
                "source_tick": {
                    "tick_id": 3,
                    "identity_id": "identity://audit-demo",
                    "attention_target": "identity-drift-review",
                    "affect_guard": "observe",
                    "continuity_pressure": 0.81,
                },
                "reflection_mode": "guardian-review",
                "escalation_target": "guardian-review",
                "risk_posture": "guarded",
                "degraded": False,
                "continuity_guard": {"guard_aligned": True},
                "coherence_score": 0.67,
            },
            qualia_checkpoint_ref="53d6e4b6f3a7f252b9f7dfdcdd4d734ae0f6dca6b25a6c67d75e55b0dd6fdb7b",
        )

        validation = service.validate_record(record)

        self.assertTrue(validation["ok"])
        self.assertEqual("guardian-review", record["recommended_action"])
        self.assertEqual("standard", record["council_brief"]["session_mode"])
        self.assertTrue(record["continuity_alignment"]["identity_matches"])
        self.assertIn("abrupt-change", record["audit_triggers"])
        self.assertIn("observe-guard", record["audit_triggers"])

    def test_resolution_maps_council_approval_to_guardian_review(self) -> None:
        service = CognitiveAuditService()
        record = service.create_record(
            identity_id="identity://audit-demo",
            qualia_tick={
                "tick_id": 3,
                "summary": "identity drift review",
                "attention_target": "identity-drift-review",
                "self_awareness": 0.88,
                "lucidity": 0.61,
                "valence": -0.19,
                "arousal": 0.67,
                "clarity": 0.58,
            },
            self_model_observation={
                "abrupt_change": True,
                "divergence": 0.41,
                "threshold": 0.35,
                "snapshot": {
                    "identity_id": "identity://audit-demo",
                    "values": ["continuity-first"],
                    "goals": ["stabilize-review-loop"],
                    "traits": {"vigilance": 0.87},
                },
            },
            metacognition_report={
                "report_id": "metacognition-report-0123456789ab",
                "source_tick": {
                    "tick_id": 3,
                    "identity_id": "identity://audit-demo",
                    "attention_target": "identity-drift-review",
                    "affect_guard": "observe",
                    "continuity_pressure": 0.81,
                },
                "reflection_mode": "guardian-review",
                "escalation_target": "guardian-review",
                "risk_posture": "guarded",
                "degraded": False,
                "continuity_guard": {"guard_aligned": True},
                "coherence_score": 0.67,
            },
            qualia_checkpoint_ref="53d6e4b6f3a7f252b9f7dfdcdd4d734ae0f6dca6b25a6c67d75e55b0dd6fdb7b",
        )

        resolution = service.resolve(
            record,
            council_proposal_ref="proposal-0123456789ab",
            council_decision={"outcome": "approved", "decision_mode": "weighted-majority"},
        )
        validation = service.validate_resolution(resolution)

        self.assertTrue(validation["ok"])
        self.assertEqual("open-guardian-review", resolution["follow_up_action"])
        self.assertTrue(resolution["continuity_alignment"]["recommended_action_matches_outcome"])


class CognitiveAuditGovernanceTests(unittest.TestCase):
    def _build_record_and_resolution(self) -> tuple[dict[str, object], dict[str, object]]:
        audit_service = CognitiveAuditService()
        record = audit_service.create_record(
            identity_id="identity://audit-demo",
            qualia_tick={
                "tick_id": 3,
                "summary": "identity drift review",
                "attention_target": "identity-drift-review",
                "self_awareness": 0.88,
                "lucidity": 0.61,
                "valence": -0.19,
                "arousal": 0.67,
                "clarity": 0.58,
            },
            self_model_observation={
                "abrupt_change": True,
                "divergence": 0.41,
                "threshold": 0.35,
                "snapshot": {
                    "identity_id": "identity://audit-demo",
                    "values": ["continuity-first"],
                    "goals": ["stabilize-review-loop"],
                    "traits": {"vigilance": 0.87},
                },
            },
            metacognition_report={
                "report_id": "metacognition-report-0123456789ab",
                "source_tick": {
                    "tick_id": 3,
                    "identity_id": "identity://audit-demo",
                    "attention_target": "identity-drift-review",
                    "affect_guard": "observe",
                    "continuity_pressure": 0.81,
                },
                "reflection_mode": "guardian-review",
                "escalation_target": "guardian-review",
                "risk_posture": "guarded",
                "degraded": False,
                "continuity_guard": {"guard_aligned": True},
                "coherence_score": 0.67,
            },
            qualia_checkpoint_ref="53d6e4b6f3a7f252b9f7dfdcdd4d734ae0f6dca6b25a6c67d75e55b0dd6fdb7b",
        )
        resolution = audit_service.resolve(
            record,
            council_proposal_ref="proposal-0123456789ab",
            council_decision={"outcome": "approved", "decision_mode": "weighted-majority"},
        )
        return record, resolution

    @staticmethod
    def _oversight_event() -> dict[str, object]:
        return {
            "event_id": "oversight-event-0123456789ab",
            "human_attestation": {"status": "satisfied"},
            "reviewer_bindings": [
                {
                    "reviewer_id": "human-reviewer-alpha",
                    "network_receipt_id": "verifier-network-receipt-0123456789ab",
                },
                {
                    "reviewer_id": "human-reviewer-beta",
                    "network_receipt_id": "verifier-network-receipt-89abcdef0123",
                },
            ],
        }

    def test_governance_binding_preserves_federated_review(self) -> None:
        service = CognitiveAuditGovernanceService()
        record, resolution = self._build_record_and_resolution()

        binding = service.bind_governance(
            record,
            resolution,
            distributed_resolutions=[
                {
                    "resolution_id": "distributed-council-fedcba987654",
                    "topology_ref": "topology-13579bdf2468",
                    "council_tier": "federation",
                    "final_outcome": "binding-approved",
                    "decision_mode": "federation-weighted-majority",
                    "conflict_resolution": "federation-overrides-local",
                    "follow_up_action": "open-shared-review-window",
                    "external_resolution_refs": ["federation://identity-a/result"],
                }
            ],
            oversight_event=self._oversight_event(),
        )
        validation = service.validate_binding(binding)

        self.assertTrue(validation["ok"])
        self.assertEqual("federation-attested-review", binding["execution_gate"])
        self.assertEqual("open-guardian-review", binding["final_follow_up_action"])
        self.assertEqual(1, validation["distributed_verdict_count"])
        self.assertTrue(validation["oversight_network_bound"])

    def test_governance_binding_escalates_conflicting_distributed_verdicts(self) -> None:
        service = CognitiveAuditGovernanceService()
        record, resolution = self._build_record_and_resolution()

        binding = service.bind_governance(
            record,
            resolution,
            distributed_resolutions=[
                {
                    "resolution_id": "distributed-council-fedcba987654",
                    "topology_ref": "topology-13579bdf2468",
                    "council_tier": "federation",
                    "final_outcome": "binding-approved",
                    "decision_mode": "federation-weighted-majority",
                    "conflict_resolution": "federation-overrides-local",
                    "follow_up_action": "open-shared-review-window",
                    "external_resolution_refs": ["federation://identity-a/result"],
                },
                {
                    "resolution_id": "distributed-council-02468ace1357",
                    "topology_ref": "topology-abcdef012345",
                    "council_tier": "heritage",
                    "final_outcome": "binding-rejected",
                    "decision_mode": "ethics-veto",
                    "conflict_resolution": "heritage-overrides-local",
                    "follow_up_action": "preserve-identity-boundary",
                    "external_resolution_refs": ["heritage://ethics/result"],
                },
            ],
            oversight_event=self._oversight_event(),
        )
        validation = service.validate_binding(binding)

        self.assertTrue(validation["ok"])
        self.assertEqual("distributed-conflict-human-escalation", binding["execution_gate"])
        self.assertEqual("escalate-to-human-governance", binding["final_follow_up_action"])
        self.assertTrue(binding["continuity_guard"]["conflict_detected"])
        self.assertEqual(2, validation["distributed_verdict_count"])


if __name__ == "__main__":
    unittest.main()
