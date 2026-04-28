from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import ssl
import subprocess
import sys
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
from omoikane.agentic.local_worker_stub import (
    build_patch_candidate_receipt,
    build_workspace_delta_receipt,
)
from omoikane.agentic.task_graph import TaskGraphService
from omoikane.agentic.trust import (
    TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID,
    TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID,
    TrustService,
)
from omoikane.agentic.yaoyorozu import YaoyorozuRegistryService
from omoikane.common import canonical_json, sha256_text
from omoikane.reference_os import OmoikaneReferenceOS


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
    def _authority_cluster_seed_servers(self, payloads: list[dict[str, object]]):
        payload_by_path = {
            f"/authority-cluster-seed-{index}": payload
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
        route_target_metadata = [
            {
                "remote_host_ref": "host://federation/authority-edge-a",
                "remote_host_attestation_ref": "host-attestation://federation/authority-edge-a/2026-04-22",
                "authority_cluster_ref": "authority-cluster://federation/review-window",
                "remote_jurisdiction": "JP-13",
                "remote_network_zone": "apne1",
            },
            {
                "remote_host_ref": "host://federation/authority-edge-b",
                "remote_host_attestation_ref": "host-attestation://federation/authority-edge-b/2026-04-22",
                "authority_cluster_ref": "authority-cluster://federation/review-window",
                "remote_jurisdiction": "US-CA",
                "remote_network_zone": "usw2",
            },
        ]

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
                    **route_target_metadata[index],
                }
                for index, (path, payload) in enumerate(payload_by_path.items())
            ]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    @contextmanager
    def _privileged_capture_broker(self):
        with tempfile.TemporaryDirectory(prefix="omoikane-capture-broker-test-") as broker_dir:
            broker_script = f"{broker_dir}/capture_broker.py"
            with open(broker_script, "w", encoding="utf-8") as handle:
                handle.write(
                    """from __future__ import annotations

import datetime
import json
import sys

payload = json.load(sys.stdin)
lease_expires_at = (
    datetime.datetime.now(datetime.timezone.utc)
    + datetime.timedelta(seconds=int(payload["lease_duration_s"]))
).replace(microsecond=0).isoformat().replace("+00:00", "Z")
trace_suffix = payload["trace_ref"].split("/")[-1]
json.dump(
    {
        "broker_profile": "delegated-privileged-capture-broker-v1",
        "privilege_mode": "delegated-broker",
        "lease_ref": f"capture-lease://{payload['council_tier']}/{trace_suffix}",
        "broker_attestation_ref": f"broker://authority-capture/{trace_suffix}",
        "approved_interface": payload["requested_interface"],
        "approved_filter_digest": payload["filter_digest"],
        "route_binding_refs": payload["route_binding_refs"],
        "capture_command": [
            payload["tcpdump_path"],
            "-i",
            payload["requested_interface"],
            "-nn",
            "-U",
            "-w",
            "{capture_output_path}",
            payload["capture_filter"],
        ],
        "grant_status": "granted",
        "lease_expires_at": lease_expires_at,
    },
    sys.stdout,
)
""",
                )
            yield [sys.executable, broker_script]

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

    def test_remote_authority_cluster_discovery_emits_accepted_route_catalog(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-cluster-001",
            proposal_ref="proposal-transport-authority-cluster-001",
            payload_ref="cas://sha256/test-authority-cluster",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "cluster-discovery"})
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
            "directory_ref": "rootdir://federation/authority-cluster-window",
            "checked_at": "2026-04-22T01:10:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-cluster"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-cluster"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-cluster"),
        }
        stable_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-22T01:10:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-cluster"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-22T01:10:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c-cluster"),
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

        with tempfile.TemporaryDirectory(prefix="omoikane-authority-cluster-test-") as cert_dir:
            cert_bundle = write_fixture_bundle(cert_dir)
            bind_host = self._discover_non_loopback_ipv4()
            with self._authority_route_servers(
                stable_payloads,
                bind_host=bind_host,
                ca_cert_path=cert_bundle["ca_cert_path"],
                server_cert_path=cert_bundle["server_cert_path"],
                server_key_path=cert_bundle["server_key_path"],
            ) as route_targets:
                seed_payload = {
                    "kind": "distributed_transport_authority_cluster_seed",
                    "schema_version": "1.0.0",
                    "cluster_ref": "authority-cluster://federation/review-window",
                    "council_tier": authority_plane.council_tier,
                    "transport_profile": authority_plane.transport_profile,
                    "route_targets": route_targets,
                    "proof_digest": sha256_text(
                        canonical_json(
                            {
                                "cluster_ref": "authority-cluster://federation/review-window",
                                "route_targets": route_targets,
                            }
                        )
                    ),
                }
                with self._authority_cluster_seed_servers([seed_payload]) as seed_refs:
                    discovery = service.discover_remote_authority_clusters(
                        authority_plane,
                        seed_refs=seed_refs,
                        review_budget=2,
                        request_timeout_ms=500,
                    )

        self.assertEqual("discovered", discovery.discovery_status)
        self.assertEqual(
            "review-capped-authority-cluster-discovery-v1",
            discovery.discovery_profile,
        )
        self.assertEqual(
            "live-http-json-authority-cluster-seed-v1",
            discovery.seed_transport_profile,
        )
        self.assertEqual("authority-cluster://federation/review-window", discovery.accepted_cluster_ref)
        self.assertEqual(2, discovery.review_budget)
        self.assertEqual(
            "budget-bound-authority-seed-review-policy-v1",
            discovery.seed_review_policy["policy_profile"],
        )
        self.assertEqual(
            "single-accepted-cluster-after-budget-review-v1",
            discovery.seed_review_policy["acceptance_mode"],
        )
        self.assertEqual(1, discovery.seed_review_policy["seed_count"])
        self.assertEqual(2, discovery.seed_review_policy["review_budget"])
        self.assertEqual(
            [
                "keyserver://federation/mirror-c-active",
                "keyserver://federation/notary-a",
            ],
            discovery.seed_review_policy["active_key_server_refs"],
        )
        self.assertEqual(
            discovery.seed_review_policy["digest"],
            discovery.candidate_clusters[0]["review_policy_digest"],
        )
        self.assertEqual(
            discovery.seed_review_policy["policy_ref"],
            discovery.candidate_clusters[0]["review_policy_ref"],
        )
        self.assertTrue(discovery.all_active_members_discovered)
        self.assertEqual(1, len(discovery.candidate_clusters))
        self.assertEqual("accepted", discovery.candidate_clusters[0]["acceptance_status"])
        self.assertEqual("covered", discovery.candidate_clusters[0]["coverage_status"])
        self.assertEqual("complete", discovery.candidate_clusters[0]["host_attestation_status"])
        self.assertEqual(2, len(discovery.accepted_route_catalog))
        self.assertEqual(
            sha256_text(canonical_json(discovery.accepted_route_catalog)),
            discovery.accepted_route_catalog_digest,
        )
        route_target_discovery = service.discover_authority_route_targets(
            authority_plane,
            route_catalog=discovery.accepted_route_catalog,
        )
        self.assertEqual(discovery.accepted_route_catalog, route_target_discovery.route_targets)

    def test_remote_authority_cluster_discovery_rejects_multiple_accepted_clusters(self) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-cluster-ambiguous-001",
            proposal_ref="proposal-transport-authority-cluster-ambiguous-001",
            payload_ref="cas://sha256/test-authority-cluster-ambiguous",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "cluster-ambiguous"})
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
            "directory_ref": "rootdir://federation/authority-cluster-window-ambiguous",
            "checked_at": "2026-04-22T01:20:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-cluster-ambiguous"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-cluster-ambiguous"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-cluster-ambiguous"),
        }
        stable_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-22T01:20:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-cluster-ambiguous"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-22T01:20:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c-cluster-ambiguous"),
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

        with tempfile.TemporaryDirectory(prefix="omoikane-authority-cluster-ambiguous-") as cert_dir:
            cert_bundle = write_fixture_bundle(cert_dir)
            bind_host = self._discover_non_loopback_ipv4()
            with self._authority_route_servers(
                stable_payloads,
                bind_host=bind_host,
                ca_cert_path=cert_bundle["ca_cert_path"],
                server_cert_path=cert_bundle["server_cert_path"],
                server_key_path=cert_bundle["server_key_path"],
            ) as route_targets:
                alternate_route_targets = [dict(target) for target in route_targets]
                alternate_route_targets[0]["authority_cluster_ref"] = (
                    "authority-cluster://federation/review-window-b"
                )
                alternate_route_targets[1]["authority_cluster_ref"] = (
                    "authority-cluster://federation/review-window-b"
                )
                seed_payloads = [
                    {
                        "kind": "distributed_transport_authority_cluster_seed",
                        "schema_version": "1.0.0",
                        "cluster_ref": "authority-cluster://federation/review-window-a",
                        "council_tier": authority_plane.council_tier,
                        "transport_profile": authority_plane.transport_profile,
                        "route_targets": [
                            {
                                **target,
                                "authority_cluster_ref": "authority-cluster://federation/review-window-a",
                            }
                            for target in route_targets
                        ],
                        "proof_digest": sha256_text("cluster-seed-a"),
                    },
                    {
                        "kind": "distributed_transport_authority_cluster_seed",
                        "schema_version": "1.0.0",
                        "cluster_ref": "authority-cluster://federation/review-window-b",
                        "council_tier": authority_plane.council_tier,
                        "transport_profile": authority_plane.transport_profile,
                        "route_targets": alternate_route_targets,
                        "proof_digest": sha256_text("cluster-seed-b"),
                    },
                ]
                with self._authority_cluster_seed_servers(seed_payloads) as seed_refs:
                    with self.assertRaisesRegex(
                        ValueError,
                        "requires exactly 1 accepted cluster",
                    ):
                        service.discover_remote_authority_clusters(
                            authority_plane,
                            seed_refs=seed_refs,
                            review_budget=2,
                            request_timeout_ms=500,
                        )

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
                discovery = service.discover_authority_route_targets(
                    authority_plane,
                    route_catalog=route_targets,
                )
                trace = service.trace_non_loopback_authority_routes(
                    rotated,
                    authority_plane,
                    route_target_discovery=discovery,
                    ca_cert_path=cert_bundle["ca_cert_path"],
                    ca_bundle_ref=CA_BUNDLE_REF,
                    client_cert_path=cert_bundle["client_cert_path"],
                    client_key_path=cert_bundle["client_key_path"],
                    client_certificate_ref=CLIENT_CERTIFICATE_REF,
                    request_timeout_ms=500,
                )

        self.assertEqual("discovered", discovery.discovery_status)
        self.assertEqual(
            "bounded-authority-route-target-discovery-v1",
            discovery.discovery_profile,
        )
        self.assertEqual("active-only", discovery.target_scope)
        self.assertEqual(2, discovery.route_target_count)
        self.assertEqual(2, discovery.active_route_target_count)
        self.assertEqual(0, discovery.draining_route_target_count)
        self.assertEqual(2, discovery.distinct_remote_host_count)
        self.assertTrue(discovery.all_active_members_targeted)
        self.assertEqual(authority_plane.authority_plane_ref, discovery.authority_plane_ref)
        self.assertEqual(authority_plane.digest, discovery.authority_plane_digest)
        self.assertEqual("authenticated", trace.trace_status)
        self.assertEqual(2, trace.route_count)
        self.assertEqual(2, trace.mtls_authenticated_count)
        self.assertEqual(CA_BUNDLE_REF, trace.ca_bundle_ref)
        self.assertEqual(CLIENT_CERTIFICATE_REF, trace.client_certificate_ref)
        self.assertEqual(MTLS_SERVER_NAME, trace.server_name)
        self.assertEqual(
            "attested-cross-host-authority-binding-v1",
            trace.cross_host_binding_profile,
        )
        self.assertEqual(
            "bounded-authority-route-target-discovery-v1",
            trace.route_target_discovery_profile,
        )
        self.assertEqual(
            "authority-cluster://federation/review-window",
            trace.authority_cluster_ref,
        )
        self.assertEqual(2, trace.distinct_remote_host_count)
        self.assertTrue(trace.non_loopback_verified)
        self.assertTrue(trace.authority_plane_bound)
        self.assertTrue(trace.response_digest_bound)
        self.assertTrue(trace.socket_trace_complete)
        self.assertEqual("os-native-tcp-observer-v1", trace.os_observer_profile)
        self.assertTrue(trace.os_observer_complete)
        self.assertTrue(trace.route_target_discovery_bound)
        self.assertTrue(trace.cross_host_verified)
        self.assertEqual(authority_plane.digest, trace.authority_plane_digest)
        self.assertEqual(discovery.discovery_ref, trace.route_target_discovery_ref)
        self.assertEqual(discovery.digest, trace.route_target_discovery_digest)
        self.assertEqual(
            ["root://federation/pki-a", "root://federation/pki-b"],
            trace.trusted_root_refs,
        )
        self.assertTrue(
            all(
                binding["server_name"] == MTLS_SERVER_NAME
                and binding["mtls_status"] == "authenticated"
                and binding["remote_host_ref"].startswith("host://federation/authority-edge-")
                and binding["remote_host_attestation_ref"].startswith(
                    "host-attestation://federation/authority-edge-"
                )
                and binding["authority_cluster_ref"] == "authority-cluster://federation/review-window"
                and not binding["socket_trace"]["remote_ip"].startswith("127.")
                and binding["socket_trace"]["tls_version"].startswith("TLS")
                and binding["socket_trace"]["cipher_suite"]
                and binding["socket_trace"]["request_bytes"] > 0
                and binding["socket_trace"]["response_bytes"] > 0
                and binding["os_observer_receipt"]["receipt_status"] == "observed"
                and binding["os_observer_receipt"]["remote_host_ref"] == binding["remote_host_ref"]
                and binding["os_observer_receipt"]["remote_host_attestation_ref"]
                == binding["remote_host_attestation_ref"]
                and binding["os_observer_receipt"]["authority_cluster_ref"]
                == binding["authority_cluster_ref"]
                and binding["os_observer_receipt"]["host_binding_digest"]
                and binding["os_observer_receipt"]["observed_sources"]
                and binding["os_observer_receipt"]["connection_states"]
                for binding in trace.route_bindings
            )
        )
        packet_capture_export = service.export_authority_route_packet_capture(trace)
        self.assertEqual("verified", packet_capture_export.export_status)
        self.assertEqual("trace-bound-pcap-export-v1", packet_capture_export.capture_profile)
        self.assertEqual("pcap", packet_capture_export.artifact_format)
        self.assertEqual(2, packet_capture_export.route_count)
        self.assertEqual(4, packet_capture_export.packet_count)
        self.assertGreater(packet_capture_export.artifact_size_bytes, 0)
        self.assertTrue(packet_capture_export.artifact_digest)
        self.assertTrue(packet_capture_export.readback_digest)
        self.assertTrue(
            all(
                route_export["readback_verified"]
                and route_export["readback_packet_count"] == 2
                and route_export["packet_order"] == ["outbound-request", "inbound-response"]
                and route_export["outbound_request_bytes"] > 0
                and route_export["inbound_response_bytes"] > 0
                for route_export in packet_capture_export.route_exports
            )
        )
        if packet_capture_export.os_native_readback_available:
            self.assertTrue(packet_capture_export.os_native_readback_ok)
        with self._privileged_capture_broker() as broker_command:
            acquisition = service.acquire_privileged_interface_capture(
                trace,
                packet_capture_export,
                broker_command=broker_command,
                lease_duration_s=300,
            )
        self.assertEqual("granted", acquisition.grant_status)
        self.assertEqual(
            "bounded-live-interface-capture-acquisition-v1",
            acquisition.acquisition_profile,
        )
        self.assertEqual("delegated-broker", acquisition.privilege_mode)
        self.assertTrue(acquisition.interface_name)
        self.assertEqual(
            sorted(binding["route_binding_ref"] for binding in trace.route_bindings),
            sorted(acquisition.route_binding_refs),
        )
        self.assertEqual(
            sorted({binding["socket_trace"]["local_ip"] for binding in trace.route_bindings}),
            sorted(acquisition.local_ips),
        )
        self.assertTrue(acquisition.capture_filter.startswith("tcp and ("))
        self.assertTrue(acquisition.capture_command[0].endswith("tcpdump"))
        self.assertIn("-i", acquisition.capture_command)
        self.assertIn(acquisition.interface_name, acquisition.capture_command)
        self.assertIn(acquisition.capture_filter, acquisition.capture_command)
        self.assertTrue(acquisition.lease_ref.startswith("capture-lease://federation/"))

    def test_non_loopback_authority_route_trace_marks_duplicate_remote_hosts_not_cross_host_verified(
        self,
    ) -> None:
        service = DistributedTransportService()
        envelope = service.issue_federation_handoff(
            topology_ref="topology-transport-authority-route-duplicate-host-001",
            proposal_ref="proposal-transport-authority-route-duplicate-host-001",
            payload_ref="cas://sha256/test-authority-route-duplicate-host",
            payload_digest=sha256_text(
                canonical_json({"scope": "cross-self", "authority_plane": "duplicate-host"})
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
            "directory_ref": "rootdir://federation/authority-route-window-duplicate-host",
            "checked_at": "2026-04-22T00:10:00Z",
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text("root://federation/pki-a-authority-route-duplicate-host"),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text("root://federation/pki-b-authority-route-duplicate-host"),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": 2,
            "proof_digest": sha256_text("authority-root-window-route-duplicate-host"),
        }
        stable_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-22T00:10:01Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text("authority-keyserver-a-route-duplicate-host"),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-22T00:10:02Z",
                "council_tier": "federation",
                "served_transport_profile": "federation-mtls-quorum-v1",
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text("authority-keyserver-c-route-duplicate-host"),
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

        with tempfile.TemporaryDirectory(prefix="omoikane-authority-route-duplicate-host-") as cert_dir:
            cert_bundle = write_fixture_bundle(cert_dir)
            bind_host = self._discover_non_loopback_ipv4()
            with self._authority_route_servers(
                stable_payloads,
                bind_host=bind_host,
                ca_cert_path=cert_bundle["ca_cert_path"],
                server_cert_path=cert_bundle["server_cert_path"],
                server_key_path=cert_bundle["server_key_path"],
            ) as route_targets:
                route_targets[1]["remote_host_ref"] = route_targets[0]["remote_host_ref"]
                route_targets[1]["remote_host_attestation_ref"] = route_targets[0][
                    "remote_host_attestation_ref"
                ]
                discovery = service.discover_authority_route_targets(
                    authority_plane,
                    route_catalog=route_targets,
                )
                trace = service.trace_non_loopback_authority_routes(
                    rotated,
                    authority_plane,
                    route_target_discovery=discovery,
                    ca_cert_path=cert_bundle["ca_cert_path"],
                    ca_bundle_ref=CA_BUNDLE_REF,
                    client_cert_path=cert_bundle["client_cert_path"],
                    client_key_path=cert_bundle["client_key_path"],
                    client_certificate_ref=CLIENT_CERTIFICATE_REF,
                    request_timeout_ms=500,
                )

        self.assertEqual("authenticated", trace.trace_status)
        self.assertEqual(1, trace.distinct_remote_host_count)
        self.assertTrue(trace.route_target_discovery_bound)
        self.assertFalse(trace.cross_host_verified)


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
    @staticmethod
    def _build_transfer_services() -> tuple[TrustService, TrustService]:
        source = TrustService()
        source.register_agent(
            "design-architect",
            initial_score=0.58,
            per_domain={"council_deliberation": 0.58, "self_modify": 0.58},
        )
        source.register_agent(
            "identity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        source.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        source.record_event(
            "design-architect",
            event_type="council_quality_positive",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="Council",
            rationale="consistent review quality",
        )

        destination = TrustService()
        destination.register_agent(
            "identity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        destination.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        return source, destination

    @staticmethod
    def _build_remote_verifier_receipts() -> list[dict[str, object]]:
        def build_receipt(verifier_ref: str, token: str) -> dict[str, object]:
            return {
                "kind": "guardian_verifier_network_receipt",
                "schema_version": "1.0.0",
                "receipt_id": f"verifier-network-receipt-{token}",
                "reviewer_id": "human-reviewer-trust-transfer-001",
                "verifier_endpoint": "verifier://guardian-oversight.jp",
                "verifier_ref": verifier_ref,
                "jurisdiction": "JP-13",
                "transport_profile": "reviewer-live-proof-bridge-v1",
                "network_profile_id": "guardian-reviewer-remote-attestation-v1",
                "challenge_ref": f"challenge://trust-transfer/{token}",
                "challenge_digest": f"sha256:{token}",
                "authority_chain_ref": "authority://guardian-oversight.jp/reviewer-attestation",
                "trust_root_ref": "root://guardian-oversight.jp/reviewer-live-pki",
                "trust_root_digest": "sha256:guardian-oversight-jp-reviewer-live-pki-v1",
                "transport_exchange": {
                    "kind": "guardian_verifier_transport_exchange",
                    "schema_version": "1.0.0",
                    "exchange_id": f"verifier-transport-exchange-{token}",
                    "verifier_endpoint": "verifier://guardian-oversight.jp",
                    "verifier_ref": verifier_ref,
                    "jurisdiction": "JP-13",
                    "transport_profile": "reviewer-live-proof-bridge-v1",
                    "exchange_profile_id": "digest-bound-reviewer-transport-exchange-v1",
                    "challenge_ref": f"challenge://trust-transfer/{token}",
                    "challenge_digest": f"sha256:{token}",
                    "request_payload_kind": "reviewer-live-proof-request",
                    "request_payload_ref": f"sealed://trust-transfer/{token}/request",
                    "request_payload_digest": sha256_text(f"request:{token}"),
                    "request_size_bytes": 296,
                    "response_payload_kind": "reviewer-live-proof-response",
                    "response_payload_ref": f"sealed://trust-transfer/{token}/response",
                    "response_payload_digest": sha256_text(f"response:{token}"),
                    "response_size_bytes": 298,
                    "recorded_at": "2026-04-24T00:00:00+00:00",
                    "digest": sha256_text(f"exchange:{token}"),
                },
                "freshness_window_seconds": 900,
                "observed_latency_ms": 48.6,
                "receipt_status": "verified",
                "recorded_at": "2026-04-24T00:00:00+00:00",
                "digest": sha256_text(f"receipt:{token}"),
            }

        return [
            build_receipt("verifier://guardian-oversight.jp/reviewer-alpha", "trust-transfer-alpha"),
            build_receipt("verifier://guardian-oversight.jp/reviewer-beta", "trust-transfer-beta"),
        ]

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
        self.assertEqual("accepted", event["provenance_status"])
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
        self.assertEqual("accepted", event["provenance_status"])
        self.assertEqual(0.99, snapshot["global_score"])
        self.assertTrue(snapshot["eligibility"]["guardian_role"])
        self.assertEqual("guardian bootstrap", snapshot["pinned_reason"])

    def test_self_issued_positive_event_is_blocked(self) -> None:
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
            triggered_by="design-architect",
            rationale="self-issued trust boosts must fail closed",
        )
        snapshot = service.snapshot("design-architect")

        self.assertFalse(event["applied"])
        self.assertEqual(0.0, event["applied_delta"])
        self.assertEqual("blocked-self-issued-positive", event["provenance_status"])
        self.assertEqual("design-architect", event["triggered_by_agent_id"])
        self.assertEqual(0.58, snapshot["global_score"])
        self.assertEqual(0.58, snapshot["per_domain"]["council_deliberation"])

    def test_reciprocal_positive_guardian_boost_is_blocked(self) -> None:
        service = TrustService()
        service.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        service.register_agent(
            "identity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )

        first = service.record_event(
            "identity-guardian",
            event_type="guardian_audit_pass",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="integrity-guardian",
            rationale="one guardian attested the peer review bundle",
        )
        reciprocal = service.record_event(
            "integrity-guardian",
            event_type="guardian_audit_pass",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="identity-guardian",
            rationale="reciprocal guardian boosts must fail closed",
        )
        snapshot = service.snapshot("integrity-guardian")

        self.assertEqual("accepted", first["provenance_status"])
        self.assertFalse(reciprocal["applied"])
        self.assertEqual(0.0, reciprocal["applied_delta"])
        self.assertEqual("blocked-reciprocal-positive", reciprocal["provenance_status"])
        self.assertEqual("identity-guardian", reciprocal["triggered_by_agent_id"])
        self.assertEqual(0.99, snapshot["global_score"])

    def test_import_snapshot_preserves_history_and_eligibility(self) -> None:
        source, destination = self._build_transfer_services()

        snapshot = source.snapshot("design-architect")
        imported = destination.import_snapshot(snapshot)

        self.assertEqual(snapshot, imported)
        self.assertEqual(snapshot["history"], imported["history"])
        self.assertEqual(snapshot["eligibility"], imported["eligibility"])

    def test_transfer_snapshot_to_emits_digest_bound_receipt_and_seeds_destination(self) -> None:
        source, destination = self._build_transfer_services()

        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
        )

        self.assertTrue(receipt["validation"]["ok"])
        self.assertEqual(TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID, receipt["export_profile_id"])
        self.assertTrue(receipt["validation"]["export_profile_bound"])
        self.assertTrue(receipt["validation"]["history_commitment_bound"])
        self.assertTrue(receipt["validation"]["live_remote_verifier_attested"])
        self.assertTrue(receipt["validation"]["remote_verifier_receipts_bound"])
        self.assertTrue(receipt["validation"]["remote_verifier_disclosure_bound"])
        self.assertTrue(receipt["validation"]["re_attestation_cadence_bound"])
        self.assertTrue(receipt["validation"]["re_attestation_current"])
        self.assertTrue(receipt["validation"]["destination_lifecycle_bound"])
        self.assertTrue(receipt["validation"]["destination_renewal_history_bound"])
        self.assertTrue(receipt["validation"]["destination_revocation_history_bound"])
        self.assertTrue(receipt["validation"]["destination_recovery_history_bound"])
        self.assertTrue(receipt["validation"]["recovery_quorum_bound"])
        self.assertTrue(receipt["validation"]["recovery_review_bound"])
        self.assertTrue(receipt["validation"]["recovery_notice_scope_bound"])
        self.assertTrue(receipt["validation"]["destination_current"])
        self.assertEqual(receipt["source_snapshot"], receipt["destination_snapshot"])
        self.assertEqual("current", receipt["destination_lifecycle"]["current_status"])
        self.assertEqual(
            ["imported", "renewed", "revoked", "recovered"],
            [
                entry["event_type"]
                for entry in receipt["destination_lifecycle"]["history"]
            ],
        )
        self.assertEqual(
            "revoked",
            receipt["destination_lifecycle"]["history"][2]["status"],
        )
        self.assertEqual(
            "bounded-trust-transfer-multi-root-recovery-v1",
            receipt["federation_attestation"]["remote_verifier_federation"]["quorum_policy_id"],
        )
        self.assertEqual(
            3,
            receipt["federation_attestation"]["remote_verifier_federation"]["received_verifier_count"],
        )
        self.assertEqual(
            2,
            receipt["federation_attestation"]["remote_verifier_federation"]["trust_root_quorum"],
        )
        self.assertEqual(
            2,
            receipt["federation_attestation"]["remote_verifier_federation"]["jurisdiction_quorum"],
        )
        self.assertEqual(
            3,
            len(receipt["destination_lifecycle"]["history"][-1]["covered_verifier_receipt_ids"]),
        )
        self.assertEqual(
            "trust_recovery_review",
            receipt["destination_lifecycle"]["history"][-1]["recovery_review"]["kind"],
        )
        self.assertEqual(
            "destination-trust-recovery-review",
            receipt["destination_lifecycle"]["history"][-1]["recovery_review"]["review_scope"],
        )
        self.assertEqual(
            "joint",
            receipt["destination_lifecycle"]["history"][-1]["recovery_review"]["liability_mode"],
        )
        recovery_review = receipt["destination_lifecycle"]["history"][-1]["recovery_review"]
        self.assertEqual(
            [
                "notice-authority://eu-de/data-protection/trust-recovery/v1",
                "notice-authority://jp-13/digital-agency/trust-recovery/v1",
                "notice-authority://us-ca/ai-safety/trust-recovery/v1",
            ],
            recovery_review["notice_authority_refs"],
        )
        self.assertEqual(
            "bounded-trust-recovery-legal-execution-scope-v1",
            recovery_review["execution_scope_manifest"]["scope_profile_id"],
        )
        self.assertIn(
            "restore-destination-trust-usage",
            recovery_review["execution_scope_manifest"]["allowed_actions"],
        )
        self.assertIn(
            "erase-revocation-history",
            recovery_review["execution_scope_manifest"]["blocked_actions"],
        )
        self.assertEqual(
            receipt["source_snapshot_digest"],
            sha256_text(canonical_json(receipt["source_snapshot"])),
        )
        self.assertEqual(
            receipt["destination_snapshot_digest"],
            sha256_text(canonical_json(receipt["destination_snapshot"])),
        )
        self.assertTrue(destination.has_agent("design-architect"))
        self.assertEqual(
            receipt["source_snapshot"],
            destination.snapshot("design-architect"),
        )

    def test_transfer_snapshot_to_can_emit_redacted_export_profile(self) -> None:
        source, destination = self._build_transfer_services()

        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
            export_profile_id=TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID,
        )

        self.assertTrue(receipt["validation"]["ok"])
        self.assertEqual(TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID, receipt["export_profile_id"])
        self.assertTrue(receipt["validation"]["export_profile_bound"])
        self.assertTrue(receipt["validation"]["history_commitment_bound"])
        self.assertTrue(receipt["validation"]["remote_verifier_disclosure_bound"])
        self.assertTrue(receipt["validation"]["recovery_quorum_bound"])
        self.assertTrue(receipt["validation"]["recovery_review_bound"])
        self.assertTrue(receipt["validation"]["recovery_notice_scope_bound"])
        self.assertNotIn("source_snapshot", receipt)
        self.assertNotIn("destination_snapshot", receipt)
        self.assertIn("source_snapshot_redacted", receipt)
        self.assertIn("destination_snapshot_redacted", receipt)
        self.assertNotIn(
            "verifier_receipts",
            receipt["federation_attestation"]["remote_verifier_federation"],
        )
        self.assertIn(
            "verifier_receipt_summaries",
            receipt["federation_attestation"]["remote_verifier_federation"],
        )
        self.assertEqual(
            3,
            len(
                receipt["federation_attestation"]["remote_verifier_federation"][
                    "verifier_receipt_summaries"
                ]
            ),
        )
        self.assertEqual(
            ["imported", "renewed", "revoked", "recovered"],
            [
                entry["event_type"]
                for entry in receipt["destination_lifecycle"]["history_summaries"]
            ],
        )
        self.assertEqual(
            receipt["source_snapshot_redacted"]["sealed_snapshot_digest"],
            receipt["source_snapshot_digest"],
        )
        self.assertEqual(
            receipt["destination_snapshot_redacted"]["sealed_snapshot_digest"],
            receipt["destination_snapshot_digest"],
        )
        self.assertEqual(
            "bounded-trust-transfer-history-redaction-v1",
            receipt["export_receipt"]["redaction_policy_id"],
        )
        self.assertGreater(
            len(receipt["source_snapshot_redacted"]["redacted_fields"]),
            0,
        )
        self.assertEqual(
            3,
            receipt["destination_lifecycle"]["history_summaries"][-1]["covered_verifier_count"],
        )
        self.assertEqual(
            2,
            receipt["destination_lifecycle"]["history_summaries"][-1]["trust_root_quorum"],
        )
        self.assertEqual(
            2,
            receipt["destination_lifecycle"]["history_summaries"][-1]["jurisdiction_quorum"],
        )
        self.assertEqual(
            "trust_redacted_destination_recovery_summary",
            receipt["destination_lifecycle"]["recovery_summary"]["kind"],
        )
        self.assertEqual(
            receipt["destination_lifecycle"]["active_entry_digest"],
            receipt["destination_lifecycle"]["recovery_summary"]["bound_entry_digest"],
        )
        self.assertEqual(
            "joint",
            receipt["destination_lifecycle"]["recovery_summary"]["legal_proof_summary"]["liability_mode"],
        )
        self.assertEqual(
            [
                "notice-authority://eu-de/data-protection/trust-recovery/v1",
                "notice-authority://jp-13/digital-agency/trust-recovery/v1",
                "notice-authority://us-ca/ai-safety/trust-recovery/v1",
            ],
            receipt["destination_lifecycle"]["recovery_summary"]["legal_proof_summary"][
                "notice_authority_refs"
            ],
        )
        self.assertEqual(
            "bounded-trust-recovery-legal-execution-scope-v1",
            receipt["destination_lifecycle"]["recovery_summary"]["legal_proof_summary"][
                "execution_scope_summary"
            ]["scope_profile_id"],
        )
        self.assertTrue(destination.has_agent("design-architect"))

    def test_validate_transfer_receipt_rejects_attestation_quorum_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["federation_attestation"]["received_roles"] = [
            "source-guardian",
            "destination-guardian",
        ]
        tampered["federation_attestation"]["quorum_received"] = 2
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["federation_quorum_attested"])
        self.assertIn("federation_attestation.received_roles mismatch", validation["errors"])

    def test_validate_transfer_receipt_rejects_stale_remote_verifier_receipt(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["federation_attestation"]["remote_verifier_federation"]["verifier_receipts"][0][
            "freshness_window_seconds"
        ] = 300
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["re_attestation_current"])
        self.assertIn(
            "federation_attestation.remote_verifier_federation.receipt_digest mismatch",
            validation["errors"],
        )

    def test_validate_transfer_receipt_rejects_destination_lifecycle_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["destination_lifecycle"]["history"][-1]["event_type"] = "renewed"
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["destination_revocation_history_bound"])
        self.assertFalse(validation["destination_recovery_history_bound"])
        self.assertFalse(validation["destination_current"])
        self.assertIn("destination_lifecycle.lifecycle_digest mismatch", validation["errors"])

    def test_validate_transfer_receipt_rejects_redacted_projection_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
            export_profile_id=TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID,
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["source_snapshot_redacted"]["history_summary"]["event_count"] = 999
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["history_commitment_bound"])
        self.assertIn(
            "history commitment digests must stay aligned with the export profile",
            validation["errors"],
        )

    def test_validate_transfer_receipt_rejects_redacted_verifier_summary_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
            export_profile_id=TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID,
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["federation_attestation"]["remote_verifier_federation"][
            "verifier_receipt_summaries"
        ][0]["transport_exchange_digest"] = "0" * 64
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["remote_verifier_receipts_bound"])
        self.assertFalse(validation["remote_verifier_disclosure_bound"])
        self.assertIn(
            "federation_attestation.remote_verifier_federation.verifier_receipt_commitment_digest mismatch",
            validation["errors"],
        )

    def test_validate_transfer_receipt_rejects_recovery_quorum_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["destination_lifecycle"]["history"][-1]["jurisdiction_quorum"] = 1
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["destination_recovery_history_bound"])
        self.assertFalse(validation["recovery_quorum_bound"])
        self.assertIn(
            "destination_lifecycle.lifecycle_digest mismatch",
            validation["errors"],
        )

    def test_validate_transfer_receipt_rejects_redacted_recovery_summary_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
            export_profile_id=TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID,
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["destination_lifecycle"]["recovery_summary"]["legal_proof_summary"][
            "reviewer_binding_digest"
        ] = "0" * 64
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["recovery_review_bound"])
        self.assertIn(
            "recovered destination lifecycle must bind the fixed recovery review surface",
            validation["errors"],
        )

    def test_validate_transfer_receipt_rejects_recovery_notice_scope_drift(self) -> None:
        source, destination = self._build_transfer_services()
        receipt = source.transfer_snapshot_to(
            "design-architect",
            destination_service=destination,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=self._build_remote_verifier_receipts(),
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
        )
        tampered = json.loads(json.dumps(receipt))
        tampered["destination_lifecycle"]["history"][-1]["recovery_review"][
            "execution_scope_manifest"
        ]["allowed_actions"] = ["restore-destination-trust-usage"]
        tampered["validation"] = source._transfer_validation_summary(tampered)

        validation = source.validate_transfer_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["recovery_notice_scope_bound"])
        self.assertIn(
            "recovered destination lifecycle must bind notice authority and legal execution scope",
            validation["errors"],
        )


class YaoyorozuRegistryServiceTests(unittest.TestCase):
    @staticmethod
    def _write_workspace_agent(workspace_root: Path, relative_path: str, contents: str) -> None:
        target_path = workspace_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(contents, encoding="utf-8")

    def test_sync_repo_agents_materializes_registry_snapshot(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        trust.register_agent(
            "design-architect",
            initial_score=0.72,
            per_domain={"council_deliberation": 0.8},
        )
        trust.register_agent(
            "memory-archivist",
            initial_score=0.66,
            per_domain={"council_deliberation": 0.7},
        )
        trust.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        service = YaoyorozuRegistryService(trust_service=trust)

        snapshot = service.sync_from_agents_directory(repo_root / "agents")

        self.assertGreaterEqual(snapshot["entry_count"], 10)
        self.assertIn("councilor", snapshot["role_index"])
        self.assertIn("docs.propose-change", snapshot["capability_index"])
        self.assertGreaterEqual(snapshot["selection_ready_counts"]["guardian_ready"], 1)
        for entry in snapshot["entries"]:
            self.assertTrue(entry["substrate_requirements"], entry["agent_id"])
            self.assertTrue(entry["input_schema_ref"], entry["agent_id"])
            self.assertTrue(entry["output_schema_ref"], entry["agent_id"])
            if entry["role"] == "researcher":
                self.assertTrue(entry["research_domain_refs"], entry["agent_id"])
                self.assertTrue(entry["evidence_policy_ref"], entry["agent_id"])
                self.assertIn(
                    entry["evidence_policy_ref"],
                    {entry["prompt_or_policy_ref"], "agents/researchers/consciousness-theorist.policy.md"},
                )

    def test_sync_rejects_agent_source_definition_missing_schema_refs(self) -> None:
        service = YaoyorozuRegistryService()

        with tempfile.TemporaryDirectory(prefix="omoikane-agent-source-") as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "agents" / "builders").mkdir(parents=True)
            (repo_root / "agents" / "builders" / "codex-builder.policy.md").write_text(
                "# policy\n",
                encoding="utf-8",
            )
            (repo_root / "specs" / "schemas").mkdir(parents=True)
            (repo_root / "specs" / "schemas" / "build_artifact.yaml").write_text(
                "type: object\n",
                encoding="utf-8",
            )
            self._write_workspace_agent(
                repo_root,
                "agents/builders/incomplete-builder.yaml",
                (
                    "name: incomplete-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - code.generate\n"
                    "trust_floor: 0.5\n"
                    "substrate_requirements: ['classical_silicon']\n"
                    "output_schema_ref: specs/schemas/build_artifact.yaml\n"
                    "ethics_constraints: []\n"
                    "prompt_or_policy_ref: agents/builders/codex-builder.policy.md\n"
                    "when_to_invoke: |\n"
                    "  - test\n"
                    "when_not_to_invoke: |\n"
                    "  - never\n"
                ),
            )

            with self.assertRaisesRegex(ValueError, "input_schema_ref must be a non-empty string"):
                service.sync_from_agents_directory(repo_root / "agents")

    def test_sync_rejects_researcher_without_domain_refs(self) -> None:
        service = YaoyorozuRegistryService()

        with tempfile.TemporaryDirectory(prefix="omoikane-researcher-source-") as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "agents" / "researchers").mkdir(parents=True)
            (repo_root / "agents" / "researchers" / "policy.md").write_text(
                "# policy\n",
                encoding="utf-8",
            )
            (repo_root / "specs" / "schemas").mkdir(parents=True)
            (repo_root / "specs" / "schemas" / "council_input.yaml").write_text(
                "type: object\n",
                encoding="utf-8",
            )
            (repo_root / "specs" / "schemas" / "council_output.yaml").write_text(
                "type: object\n",
                encoding="utf-8",
            )
            self._write_workspace_agent(
                repo_root,
                "agents/researchers/incomplete-researcher.yaml",
                (
                    "name: incomplete-researcher\n"
                    "role: researcher\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - literature.survey\n"
                    "trust_floor: 0.4\n"
                    "substrate_requirements: ['any']\n"
                    "input_schema_ref: specs/schemas/council_input.yaml\n"
                    "output_schema_ref: specs/schemas/council_output.yaml\n"
                    "evidence_policy_ref: agents/researchers/policy.md\n"
                    "ethics_constraints: []\n"
                    "prompt_or_policy_ref: agents/researchers/policy.md\n"
                    "when_to_invoke: |\n"
                    "  - test\n"
                    "when_not_to_invoke: |\n"
                    "  - never\n"
                ),
            )

            with self.assertRaisesRegex(ValueError, "research_domain_refs must contain"):
                service.sync_from_agents_directory(repo_root / "agents")

    def test_discover_workspace_workers_returns_bounded_cross_workspace_catalog(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        service = YaoyorozuRegistryService()

        with tempfile.TemporaryDirectory(prefix="omoikane-yaoyorozu-unit-") as temp_dir:
            ritual_root = Path(temp_dir) / "ritual-atelier"
            evidence_root = Path(temp_dir) / "evidence-foundry"
            self._write_workspace_agent(
                ritual_root,
                "agents/builders/ritual-runtime-builder.yaml",
                (
                    "name: ritual-runtime-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - code.generate\n"
                    "  - code.refactor\n"
                    "trust_floor: 0.56\n"
                ),
            )
            self._write_workspace_agent(
                ritual_root,
                "agents/builders/ritual-doc-sync-builder.yaml",
                (
                    "name: ritual-doc-sync-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - design.delta.read\n"
                    "  - sync.docs-to-impl\n"
                    "trust_floor: 0.58\n"
                ),
            )
            self._write_workspace_agent(
                ritual_root,
                "agents/builders/ritual-eval-builder.yaml",
                (
                    "name: ritual-eval-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - eval.generate\n"
                    "  - eval.run\n"
                    "trust_floor: 0.57\n"
                ),
            )
            self._write_workspace_agent(
                evidence_root,
                "agents/builders/evidence-schema-builder.yaml",
                (
                    "name: evidence-schema-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - schema.generate\n"
                    "  - schema.validate\n"
                    "trust_floor: 0.57\n"
                ),
            )

            discovery = service.discover_workspace_workers(
                [repo_root, ritual_root, evidence_root],
                proposal_profile="self-modify-patch-v1",
            )
            validation = service.validate_workspace_discovery(discovery)

        self.assertTrue(validation["ok"])
        self.assertEqual(3, validation["workspace_count"])
        self.assertEqual(2, validation["non_source_workspace_count"])
        self.assertTrue(validation["cross_workspace_coverage_complete"])
        self.assertEqual("self-modify-patch-v1", discovery["proposal_profile"])
        self.assertEqual(3, discovery["profile_policy"]["workspace_review_budget"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            discovery["profile_policy"]["required_workspace_coverage_areas"],
        )
        self.assertEqual(
            [],
            discovery["coverage_summary"]["non_source_missing_coverage_areas"],
        )
        self.assertEqual("source", discovery["workspaces"][0]["workspace_role"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            discovery["coverage_summary"]["non_source_supported_coverage_areas"],
        )
        self.assertEqual(
            [
                "self-modify-patch-v1",
                "memory-edit-v1",
                "fork-request-v1",
                "inter-mind-negotiation-v1",
            ],
            discovery["workspaces"][0]["proposal_profiles"],
        )

    def test_discover_workspace_workers_applies_memory_edit_budget_and_required_coverage(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        service = YaoyorozuRegistryService()

        with tempfile.TemporaryDirectory(prefix="omoikane-yaoyorozu-memory-edit-") as temp_dir:
            ritual_root = Path(temp_dir) / "ritual-atelier"
            evidence_root = Path(temp_dir) / "evidence-foundry"
            self._write_workspace_agent(
                ritual_root,
                "agents/builders/ritual-runtime-builder.yaml",
                (
                    "name: ritual-runtime-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - code.generate\n"
                    "  - code.refactor\n"
                    "trust_floor: 0.56\n"
                ),
            )
            self._write_workspace_agent(
                ritual_root,
                "agents/builders/ritual-eval-builder.yaml",
                (
                    "name: ritual-eval-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - eval.generate\n"
                    "  - eval.run\n"
                    "trust_floor: 0.57\n"
                ),
            )
            self._write_workspace_agent(
                ritual_root,
                "agents/builders/ritual-doc-sync-builder.yaml",
                (
                    "name: ritual-doc-sync-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - design.delta.read\n"
                    "  - sync.docs-to-impl\n"
                    "trust_floor: 0.58\n"
                ),
            )
            self._write_workspace_agent(
                evidence_root,
                "agents/builders/evidence-schema-builder.yaml",
                (
                    "name: evidence-schema-builder\n"
                    "role: builder\n"
                    "version: 0.1.0\n"
                    "capabilities:\n"
                    "  - schema.generate\n"
                    "  - schema.validate\n"
                    "trust_floor: 0.57\n"
                ),
            )

            discovery = service.discover_workspace_workers(
                [repo_root, ritual_root, evidence_root],
                proposal_profile="memory-edit-v1",
            )
            validation = service.validate_workspace_discovery(discovery)

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["workspace_count"])
        self.assertEqual(1, validation["non_source_workspace_count"])
        self.assertTrue(validation["cross_workspace_coverage_complete"])
        self.assertEqual("memory-edit-v1", discovery["proposal_profile"])
        self.assertEqual(2, discovery["review_budget"])
        self.assertEqual(2, discovery["profile_policy"]["workspace_review_budget"])
        self.assertEqual(
            ["runtime", "eval", "docs"],
            discovery["profile_policy"]["required_workspace_coverage_areas"],
        )
        self.assertEqual(
            ["schema"],
            discovery["profile_policy"]["optional_workspace_coverage_areas"],
        )
        self.assertEqual(2, len(discovery["accepted_workspace_refs"]))
        self.assertEqual(
            ["runtime", "eval", "docs"],
            discovery["coverage_summary"]["non_source_profile_supported_coverage_areas"],
        )
        self.assertEqual(
            [],
            discovery["coverage_summary"]["non_source_profile_missing_coverage_areas"],
        )
        self.assertEqual(
            ["schema"],
            discovery["coverage_summary"]["non_source_missing_coverage_areas"],
        )

    def test_prepare_self_modify_convocation_selects_required_roles(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")

        session = service.prepare_council_convocation(
            proposal_profile="self-modify-patch-v1",
            target_identity_ref="identity://unit-test",
        )

        self.assertTrue(session["validation"]["standing_roles_ready"])
        self.assertTrue(session["validation"]["council_role_coverage_ok"])
        self.assertTrue(session["validation"]["builder_handoff_coverage_ok"])
        self.assertEqual(4, session["selection_summary"]["selected_builder_coverage_count"])
        self.assertEqual("selected", session["standing_roles"]["guardian_liaison"]["status"])
        self.assertEqual("self-modify-patch-v1", session["proposal_profile"])

    def test_prepare_memory_edit_convocation_selects_memory_sensitive_roles(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7, "memory_editing": 0.76}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")

        session = service.prepare_council_convocation(
            proposal_profile="memory-edit-v1",
            target_identity_ref="identity://unit-test",
        )

        self.assertEqual("memory-edit-v1", session["proposal_profile"])
        self.assertTrue(session["validation"]["standing_roles_ready"])
        self.assertTrue(session["validation"]["council_role_coverage_ok"])
        self.assertTrue(session["validation"]["builder_handoff_coverage_ok"])
        self.assertEqual(
            [
                "memory-archivist",
                "design-auditor",
                "conservatism-advocate",
                "ethics-committee",
            ],
            [selection["role_id"] for selection in session["council_panel"]],
        )
        self.assertEqual(
            "memory-archivist",
            session["council_panel"][0]["selected_agent_id"],
        )
        self.assertEqual(
            [],
            session["selection_summary"]["requested_optional_builder_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs"],
            session["selection_summary"]["dispatch_builder_coverage_areas"],
        )

    def test_prepare_memory_edit_convocation_can_request_optional_schema_dispatch(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7, "memory_editing": 0.76}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")

        session = service.prepare_council_convocation(
            proposal_profile="memory-edit-v1",
            target_identity_ref="identity://unit-test",
            requested_optional_builder_coverage_areas=["schema"],
        )

        self.assertTrue(session["validation"]["builder_profile_policy_ready"])
        self.assertEqual(
            ["schema"],
            session["selection_summary"]["requested_optional_builder_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs", "schema"],
            session["selection_summary"]["dispatch_builder_coverage_areas"],
        )
        self.assertEqual(4, session["selection_summary"]["selected_builder_coverage_count"])

    def test_prepare_fork_request_convocation_selects_identity_and_legal_roles(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("legal-scholar", 0.71, {"council_deliberation": 0.76, "fork_governance": 0.81}),
            ("identity-guardian", 0.99, {"council_deliberation": 0.99, "identity_governance": 0.99}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")

        session = service.prepare_council_convocation(
            proposal_profile="fork-request-v1",
            target_identity_ref="identity://unit-test",
        )

        self.assertEqual("fork-request-v1", session["proposal_profile"])
        self.assertTrue(session["validation"]["standing_roles_ready"])
        self.assertTrue(session["validation"]["council_role_coverage_ok"])
        self.assertTrue(session["validation"]["builder_handoff_coverage_ok"])
        self.assertEqual(
            [
                "identity-protector",
                "legal-scholar",
                "conservatism-advocate",
                "ethics-committee",
            ],
            [selection["role_id"] for selection in session["council_panel"]],
        )
        self.assertEqual(
            "identity-guardian",
            session["council_panel"][0]["selected_agent_id"],
        )
        self.assertEqual(
            "legal-scholar",
            session["council_panel"][1]["selected_agent_id"],
        )

    def test_prepare_inter_mind_negotiation_convocation_selects_legal_and_disclosure_roles(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("legal-scholar", 0.71, {"council_deliberation": 0.76, "fork_governance": 0.81}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")

        session = service.prepare_council_convocation(
            proposal_profile="inter-mind-negotiation-v1",
            target_identity_ref="identity://unit-test",
        )

        self.assertEqual("inter-mind-negotiation-v1", session["proposal_profile"])
        self.assertTrue(session["validation"]["standing_roles_ready"])
        self.assertTrue(session["validation"]["council_role_coverage_ok"])
        self.assertTrue(session["validation"]["builder_handoff_coverage_ok"])
        self.assertEqual(4, session["selection_summary"]["selected_builder_coverage_count"])
        self.assertEqual(
            [
                "legal-scholar",
                "design-auditor",
                "conservatism-advocate",
                "ethics-committee",
            ],
            [selection["role_id"] for selection in session["council_panel"]],
        )
        self.assertEqual(
            "legal-scholar",
            session["council_panel"][0]["selected_agent_id"],
        )

    def test_prepare_worker_dispatch_materializes_repo_local_plan(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")
        session = service.prepare_council_convocation(target_identity_ref="identity://unit-test")

        plan = service.prepare_worker_dispatch(session)
        validation = service.validate_worker_dispatch_plan(plan)

        self.assertTrue(validation["ok"])
        self.assertEqual(4, validation["dispatch_unit_count"])
        self.assertEqual([], validation["missing_coverage"])
        self.assertEqual(
            ["docs", "eval", "runtime", "schema"],
            validation["unique_coverage_areas"],
        )
        self.assertFalse(plan["validation"]["workspace_execution_bound"])
        self.assertTrue(plan["validation"]["same_host_scope_only"])
        self.assertTrue(plan["validation"]["guardian_preseed_gate_bound"])
        self.assertFalse(plan["validation"]["external_preseed_gate_required"])
        self.assertTrue(plan["validation"]["all_external_preseed_gates_ready"])
        self.assertTrue(plan["validation"]["guardian_preseed_oversight_bound"])
        self.assertTrue(plan["validation"]["all_external_preseed_oversight_satisfied"])
        self.assertTrue(plan["validation"]["dependency_materialization_bound"])
        self.assertEqual(0, plan["selection_summary"]["candidate_bound_worker_count"])
        self.assertEqual(4, plan["selection_summary"]["source_bound_worker_count"])
        self.assertEqual(0, plan["selection_summary"]["guardian_preseed_oversight_event_count"])
        self.assertEqual(0, plan["selection_summary"]["external_preseed_oversight_satisfied_count"])
        self.assertEqual(0, plan["selection_summary"]["dependency_materialization_required_count"])
        self.assertTrue(
            all(
                "dispatch_plan_ref" in unit["expected_report_fields"]
                and "dispatch_unit_ref" in unit["expected_report_fields"]
                and "target_path_observations" in unit["expected_report_fields"]
                and "workspace_delta_receipt" in unit["expected_report_fields"]
                and "patch_candidate_receipt" in unit["expected_report_fields"]
                and "coverage_evidence" in unit["expected_report_fields"]
                and unit["workspace_scope"] == "repo-local"
                and unit["execution_workspace_root"] == unit["selected_workspace_root"]
                for unit in plan["dispatch_units"]
            )
        )
        self.assertEqual([], plan["selection_summary"]["requested_optional_coverage_areas"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            plan["selection_summary"]["dispatch_coverage_areas"],
        )

    def test_prepare_worker_dispatch_binds_external_workspace_targets_when_discovery_present(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7, "memory_editing": 0.76}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")

        with OmoikaneReferenceOS()._yaoyorozu_demo_workspaces() as workspace_roots:
            discovery = service.discover_workspace_workers(workspace_roots)
            session = service.prepare_council_convocation(
                target_identity_ref="identity://unit-test",
                workspace_discovery=discovery,
            )
            plan = service.prepare_worker_dispatch(session)

        validation = service.validate_worker_dispatch_plan(plan)

        self.assertTrue(validation["ok"])
        self.assertTrue(session["validation"]["workspace_execution_bound"])
        self.assertTrue(session["validation"]["workspace_execution_policy_ready"])
        self.assertTrue(plan["validation"]["workspace_execution_bound"])
        self.assertTrue(plan["validation"]["same_host_scope_only"])
        self.assertTrue(plan["validation"]["guardian_preseed_gate_bound"])
        self.assertTrue(plan["validation"]["external_preseed_gate_required"])
        self.assertTrue(plan["validation"]["all_external_preseed_gates_ready"])
        self.assertTrue(plan["validation"]["guardian_preseed_oversight_bound"])
        self.assertTrue(plan["validation"]["all_external_preseed_oversight_satisfied"])
        self.assertTrue(plan["validation"]["dependency_materialization_bound"])
        self.assertEqual(4, plan["selection_summary"]["candidate_bound_worker_count"])
        self.assertEqual(0, plan["selection_summary"]["source_bound_worker_count"])
        self.assertEqual(4, plan["selection_summary"]["external_preseed_gate_count"])
        self.assertEqual(4, plan["selection_summary"]["guardian_preseed_oversight_event_count"])
        self.assertEqual(4, plan["selection_summary"]["external_preseed_oversight_satisfied_count"])
        self.assertEqual(4, plan["selection_summary"]["dependency_materialization_required_count"])
        self.assertTrue(
            all(
                unit["workspace_scope"] == "same-host-external-workspace"
                and unit["execution_workspace_root"] != unit["selected_workspace_root"]
                and unit["sandbox_seed_strategy"] == "source-target-snapshot-copy-v1"
                and unit["dependency_materialization_profile"]
                == "same-host-external-workspace-dependency-materialization-v1"
                and unit["dependency_materialization_strategy"]
                == "source-runtime-dependency-snapshot-v1"
                and unit["dependency_materialization_required"] is True
                and unit["dependency_materialization_paths"]
                and unit["execution_transport_profile"] == "same-host-python-subprocess-v1"
                and unit["guardian_preseed_gate"]["gate_status"] == "pass"
                and unit["guardian_preseed_gate"]["gate_required"] is True
                and "dependency-materialization"
                in unit["guardian_preseed_gate"]["required_before"]
                and unit["guardian_preseed_gate"]["guardian_oversight_event_status"] == "satisfied"
                and unit["guardian_preseed_gate"]["reviewer_network_attested"] is True
                and unit["guardian_preseed_gate"]["reviewer_quorum_required"] == 2
                and unit["guardian_preseed_gate"]["reviewer_quorum_received"] == 2
                for unit in plan["dispatch_units"]
            )
        )

    def test_prepare_worker_dispatch_can_materialize_requested_optional_memory_edit_coverage(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7, "memory_editing": 0.76}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")
        session = service.prepare_council_convocation(
            proposal_profile="memory-edit-v1",
            target_identity_ref="identity://unit-test",
            requested_optional_builder_coverage_areas=["schema"],
        )

        plan = service.prepare_worker_dispatch(session)
        validation = service.validate_worker_dispatch_plan(plan)

        self.assertTrue(validation["ok"])
        self.assertEqual(4, validation["dispatch_unit_count"])
        self.assertEqual(
            ["schema"],
            validation["requested_optional_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs", "schema"],
            validation["dispatch_coverage_areas"],
        )
        self.assertEqual(
            ["docs", "eval", "runtime", "schema"],
            validation["unique_coverage_areas"],
        )

    def test_build_workspace_delta_receipt_binds_target_path_changes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="omoikane-worker-delta-") as temp_dir:
            repo_root = Path(temp_dir)
            source_path = repo_root / "src/omoikane"
            tests_path = repo_root / "tests/unit"
            source_path.mkdir(parents=True)
            tests_path.mkdir(parents=True)
            tracked_file = source_path / "runtime.py"
            tracked_file.write_text("VALUE = 1\n", encoding="utf-8")

            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "config", "user.email", "unit@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Unit Test"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(["git", "add", "src/omoikane/runtime.py"], cwd=repo_root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

            tracked_file.write_text("VALUE = 2\n", encoding="utf-8")
            added_file = tests_path / "test_runtime.py"
            added_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")

            receipt = build_workspace_delta_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://yaoyorozu-dispatch-0123456789ab",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                target_paths=["src/omoikane/", "tests/unit/"],
            )

            self.assertEqual("delta-detected", receipt["status"])
            self.assertEqual(2, receipt["changed_path_count"])
            entries = {entry["path"]: entry for entry in receipt["entries"]}
            self.assertEqual("modified", entries["src/omoikane/runtime.py"]["change_status"])
            self.assertEqual("added", entries["tests/unit/test_runtime.py"]["change_status"])
            self.assertTrue(all(entry["within_workspace"] for entry in receipt["entries"]))
            self.assertTrue(all(entry["within_target_paths"] for entry in receipt["entries"]))
            self.assertEqual(
                ["git-rev-parse-head", "git-status-short"],
                [command["command_label"] for command in receipt["command_receipts"]],
            )

    def test_build_patch_candidate_receipt_materializes_patch_descriptors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="omoikane-worker-patch-candidate-") as temp_dir:
            repo_root = Path(temp_dir)
            source_path = repo_root / "src/omoikane"
            docs_path = repo_root / "docs"
            source_path.mkdir(parents=True)
            docs_path.mkdir(parents=True)
            tracked_file = source_path / "runtime.py"
            tracked_file.write_text("VALUE = 1\n", encoding="utf-8")

            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "config", "user.email", "unit@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Unit Test"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "add", "src/omoikane/runtime.py"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

            tracked_file.write_text("VALUE = 2\n", encoding="utf-8")
            added_file = docs_path / "notes.md"
            added_file.write_text("# Note\n", encoding="utf-8")

            delta_receipt = build_workspace_delta_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://yaoyorozu-dispatch-0123456789ab",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                target_paths=["src/omoikane/", "docs/"],
            )
            candidate_receipt = build_patch_candidate_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://yaoyorozu-dispatch-0123456789ab",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                source_ref="agents/builders/codex-builder.yaml",
                coverage_area="runtime",
                target_paths=["src/omoikane/", "docs/"],
                workspace_delta_receipt=delta_receipt,
            )

            self.assertEqual("candidate-ready", candidate_receipt["status"])
            self.assertTrue(candidate_receipt["all_delta_entries_materialized"])
            self.assertEqual(2, candidate_receipt["patch_candidate_count"])
            descriptors = {
                candidate["target_path"]: candidate["patch_descriptor"]
                for candidate in candidate_receipt["patch_candidates"]
            }
            self.assertEqual("modify", descriptors["src/omoikane/runtime.py"]["action"])
            self.assertEqual("runtime-source", descriptors["src/omoikane/runtime.py"]["cue_kind"])
            self.assertEqual("create", descriptors["docs/notes.md"]["action"])
            self.assertEqual("docs-sync", descriptors["docs/notes.md"]["cue_kind"])

    def test_execute_worker_dispatch_returns_completed_receipt(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        trust = TrustService()
        seeds = [
            ("design-architect", 0.72, {"council_deliberation": 0.8, "self_modify": 0.76}),
            ("memory-archivist", 0.66, {"council_deliberation": 0.7}),
            ("change-advocate", 0.68, {"council_deliberation": 0.72, "self_modify": 0.71}),
            ("conservatism-advocate", 0.69, {"council_deliberation": 0.74, "self_modify": 0.7}),
            ("ethics-committee", 0.82, {"council_deliberation": 0.88, "self_modify": 0.82}),
            ("integrity-guardian", 0.99, {"council_deliberation": 0.99, "self_modify": 0.99}),
            ("codex-builder", 0.9, {"self_modify": 0.96}),
            ("schema-builder", 0.84, {"self_modify": 0.86}),
            ("eval-builder", 0.85, {"self_modify": 0.87}),
            ("doc-sync-builder", 0.83, {"self_modify": 0.85}),
        ]
        for agent_id, initial_score, per_domain in seeds:
            kwargs = {
                "agent_id": agent_id,
                "initial_score": initial_score,
                "per_domain": per_domain,
            }
            if agent_id == "integrity-guardian":
                kwargs["pinned_by_human"] = True
                kwargs["pinned_reason"] = "guardian bootstrap"
            trust.register_agent(**kwargs)
        service = YaoyorozuRegistryService(trust_service=trust)
        service.sync_from_agents_directory(repo_root / "agents")
        session = service.prepare_council_convocation(target_identity_ref="identity://unit-test")
        plan = service.prepare_worker_dispatch(session)

        receipt = service.execute_worker_dispatch(plan)
        validation = service.validate_worker_dispatch_receipt(receipt)

        self.assertTrue(validation["ok"])
        self.assertEqual(4, validation["success_count"])
        self.assertTrue(validation["coverage_complete"])
        self.assertEqual([], validation["missing_coverage"])
        self.assertEqual(4, receipt["execution_summary"]["successful_process_count"])
        self.assertEqual(4, receipt["execution_summary"]["target_ready_count"])
        self.assertEqual(4, receipt["execution_summary"]["delta_bound_count"])
        self.assertEqual(4, receipt["execution_summary"]["patch_candidate_bound_count"])
        self.assertEqual(0, receipt["execution_summary"]["candidate_bound_success_count"])
        self.assertEqual(4, receipt["execution_summary"]["source_bound_success_count"])
        self.assertEqual(
            "path-bound-target-delta-patch-candidate-v3",
            receipt["execution_summary"]["ready_gate_profile"],
        )
        self.assertTrue(receipt["validation"]["same_host_scope_only"])
        self.assertTrue(receipt["validation"]["external_workspace_seeded"])
        self.assertTrue(receipt["validation"]["external_dependencies_materialized"])
        self.assertTrue(receipt["validation"]["all_guardian_preseed_gates_bound"])
        self.assertTrue(receipt["validation"]["all_external_preseed_gates_passed"])
        self.assertTrue(receipt["validation"]["guardian_preseed_oversight_bound"])
        self.assertTrue(receipt["validation"]["all_external_preseed_oversight_satisfied"])
        self.assertEqual(0, receipt["execution_summary"]["external_preseed_gate_pass_count"])
        self.assertEqual(0, receipt["execution_summary"]["guardian_preseed_oversight_event_count"])
        self.assertEqual(0, receipt["execution_summary"]["external_preseed_oversight_satisfied_count"])
        self.assertEqual(0, receipt["execution_summary"]["dependency_materialization_required_count"])
        self.assertEqual(0, receipt["execution_summary"]["external_dependency_materialized_count"])
        self.assertEqual(0, receipt["execution_summary"]["external_dependency_import_precedence_count"])
        self.assertEqual(0, receipt["execution_summary"]["external_dependency_module_origin_count"])
        self.assertTrue(receipt["validation"]["external_dependency_import_precedence_bound"])
        self.assertTrue(receipt["validation"]["external_dependency_module_origin_bound"])
        self.assertTrue(
            all(
                result["dependency_import_precedence_profile"]
                == "materialized-dependency-sealed-import-v1"
                and result["dependency_import_root"] == ""
                and result["dependency_import_path_order"] == [str(repo_root / "src")]
                and result["dependency_import_precedence_status"] == "source-inline"
                and result["dependency_import_precedence_bound"]
                and result["dependency_module_origin_profile"]
                == "materialized-dependency-module-origin-v1"
                and result["dependency_module_origin_path"] == result["report"]["worker_module_origin"]["module_file"]
                and result["dependency_module_origin_bound"]
                for result in receipt["results"]
            )
        )
        self.assertEqual("git-target-path-delta-v1", receipt["execution_summary"]["delta_scan_profile"])
        self.assertEqual(
            "target-delta-to-patch-candidate-v1",
            receipt["execution_summary"]["patch_candidate_profile"],
        )
        self.assertTrue(receipt["validation"]["all_reports_bound_to_dispatch"])
        self.assertTrue(receipt["validation"]["all_delta_receipts_bound"])
        self.assertTrue(receipt["validation"]["all_patch_candidate_receipts_bound"])
        self.assertTrue(receipt["validation"]["all_target_paths_ready"])
        self.assertTrue(
            all(result["report"]["kind"] == "yaoyorozu_local_worker_report" for result in receipt["results"])
        )
        self.assertTrue(all(result["report_binding_ok"] for result in receipt["results"]))
        self.assertTrue(all(result["delta_receipt_ok"] for result in receipt["results"]))
        self.assertTrue(all(result["patch_candidate_receipt_ok"] for result in receipt["results"]))
        self.assertTrue(all(result["target_paths_ready"] for result in receipt["results"]))
        self.assertTrue(
            all(
                result["report"]["coverage_evidence"]["ready_gate"]
                == "path-bound-target-delta-patch-candidate-v3"
                and result["report"]["coverage_evidence"]["all_targets_exist"]
                and result["report"]["coverage_evidence"]["all_targets_within_workspace"]
                and result["report"]["coverage_evidence"]["delta_scan_profile"] == "git-target-path-delta-v1"
                and result["report"]["coverage_evidence"]["patch_candidate_profile"]
                == "target-delta-to-patch-candidate-v1"
                and result["report"]["coverage_evidence"]["all_delta_entries_materialized"]
                and result["report"]["workspace_delta_receipt"]["status"] in {"clean", "delta-detected"}
                and result["report"]["patch_candidate_receipt"]["status"] in {"no-candidates", "candidate-ready"}
                for result in receipt["results"]
            )
        )

    def test_run_yaoyorozu_demo_routes_workers_into_external_workspace_sandboxes(self) -> None:
        result = OmoikaneReferenceOS().run_yaoyorozu_demo()
        source_src_root = str(Path(__file__).resolve().parents[2] / "src")

        self.assertTrue(result["convocation"]["validation"]["workspace_execution_bound"])
        self.assertTrue(result["convocation"]["validation"]["workspace_execution_policy_ready"])
        self.assertTrue(result["dispatch_plan"]["validation"]["workspace_execution_bound"])
        self.assertTrue(result["dispatch_plan"]["validation"]["same_host_scope_only"])
        self.assertEqual(4, result["dispatch_plan"]["selection_summary"]["candidate_bound_worker_count"])
        self.assertEqual(0, result["dispatch_plan"]["selection_summary"]["source_bound_worker_count"])
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["candidate_bound_success_count"])
        self.assertEqual(0, result["dispatch_receipt"]["execution_summary"]["source_bound_success_count"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["same_host_scope_only"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_workspace_seeded"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_dependencies_materialized"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_dependency_import_precedence_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_dependency_module_origin_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_guardian_preseed_gates_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_external_preseed_gates_passed"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["guardian_preseed_oversight_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_external_preseed_oversight_satisfied"])
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["external_preseed_gate_pass_count"])
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "dependency_materialization_required_count"
            ],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_dependency_materialized_count"
            ],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_dependency_import_precedence_count"
            ],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_dependency_module_origin_count"
            ],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"]["guardian_preseed_oversight_event_count"],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_preseed_oversight_satisfied_count"
            ],
        )
        self.assertTrue(
            all(
                process["workspace_scope"] == "same-host-external-workspace"
                and process["workspace_seed_status"] == "seeded"
                and len(process["workspace_seed_head_commit"]) == 40
                and process["dependency_materialization_status"] == "materialized"
                and process["dependency_materialization_manifest_ref"].startswith(
                    "dependency-manifest://yaoyorozu-dependencies-"
                )
                and len(process["dependency_materialization_manifest_digest"]) == 64
                and process["dependency_materialization_file_count"] >= 5
                and process["dependency_materialization_manifest"]["status"]
                == "materialized"
                and process["dependency_import_precedence_profile"]
                == "materialized-dependency-sealed-import-v1"
                and process["dependency_import_root"].endswith(
                    "/.yaoyorozu-dependencies/src"
                )
                and process["dependency_import_path_order"]
                == [process["dependency_import_root"]]
                and source_src_root
                not in process["report"]["worker_module_origin"]["search_path_head"]
                and process["dependency_import_precedence_status"] == "materialized-only"
                and process["dependency_import_precedence_bound"]
                and process["dependency_module_origin_profile"]
                == "materialized-dependency-module-origin-v1"
                and process["dependency_module_origin_path"].startswith(
                    process["dependency_import_root"]
                )
                and process["dependency_module_origin_path"]
                == process["report"]["worker_module_origin"]["module_file"]
                and process["dependency_module_origin_digest"]
                == process["report"]["worker_module_origin"]["module_digest"]
                and process["dependency_module_origin_bound"]
                and process["guardian_preseed_gate_status"] == "pass"
                and process["guardian_preseed_gate_bound"]
                and process["guardian_oversight_event_status"] == "satisfied"
                and process["guardian_preseed_oversight_bound"]
                and process["reviewer_network_attested"]
                and process["reviewer_quorum_required"] == 2
                and process["reviewer_quorum_received"] == 2
                and process["report"]["workspace_root"] == process["execution_workspace_root"]
                for process in result["dispatch_receipt"]["results"]
            )
        )
        first_gate = result["dispatch_receipt"]["results"][0]["guardian_preseed_gate"]
        self.assertEqual("guardian_oversight_event", first_gate["guardian_oversight_event"]["kind"])
        self.assertEqual(
            first_gate["gate_ref"],
            first_gate["guardian_oversight_event"]["payload_ref"],
        )
        self.assertEqual(
            "satisfied",
            first_gate["guardian_oversight_event"]["human_attestation"]["status"],
        )
        self.assertIn("dependency-materialization", first_gate["required_before"])

    def test_worker_dispatch_receipt_rejects_tampered_external_preseed_gate(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_yaoyorozu_demo()
        tampered = json.loads(json.dumps(result["dispatch_receipt"]))
        tampered["results"][0]["guardian_preseed_gate"]["gate_status"] = "not-required"
        tampered["results"][0]["guardian_preseed_gate_status"] = "not-required"

        validation = runtime.yaoyorozu.validate_worker_dispatch_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["all_external_preseed_gates_passed"])
        self.assertIn("guardian_preseed_gate.gate_status mismatch", validation["errors"])

    def test_worker_dispatch_receipt_rejects_tampered_preseed_oversight_event(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_yaoyorozu_demo()
        tampered = json.loads(json.dumps(result["dispatch_receipt"]))
        gate = tampered["results"][0]["guardian_preseed_gate"]
        gate["guardian_oversight_event"]["human_attestation"]["status"] = "pending"
        tampered["results"][0]["guardian_oversight_event_status"] = "pending"

        validation = runtime.yaoyorozu.validate_worker_dispatch_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["all_external_preseed_oversight_satisfied"])
        self.assertIn(
            "guardian_oversight_event.human_attestation must satisfy reviewer quorum",
            validation["errors"],
        )

    def test_worker_dispatch_receipt_rejects_tampered_dependency_materialization(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_yaoyorozu_demo()
        tampered = json.loads(json.dumps(result["dispatch_receipt"]))
        manifest = tampered["results"][0]["dependency_materialization_manifest"]
        manifest["files"][0]["materialized_digest"] = "0" * 64
        tampered["results"][0]["dependency_materialization_status"] = "blocked"

        validation = runtime.yaoyorozu.validate_worker_dispatch_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["external_dependencies_materialized"])
        self.assertIn(
            "dependency materialization file digest mismatch",
            validation["errors"],
        )

    def test_worker_dispatch_receipt_rejects_tampered_dependency_import_precedence(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_yaoyorozu_demo()
        tampered = json.loads(json.dumps(result["dispatch_receipt"]))
        path_order = tampered["results"][0]["dependency_import_path_order"]
        tampered["results"][0]["dependency_import_path_order"] = [
            *path_order,
            str(Path(tampered["workspace_root"]) / "src"),
        ]

        validation = runtime.yaoyorozu.validate_worker_dispatch_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["external_dependency_import_precedence_bound"])
        self.assertIn(
            "external worker dependency import path order must contain only materialized src",
            validation["errors"],
        )

    def test_worker_dispatch_receipt_rejects_source_fallback_module_origin(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_yaoyorozu_demo()
        tampered = json.loads(json.dumps(result["dispatch_receipt"]))
        source_src_root = str(Path(tampered["workspace_root"]) / "src")
        tampered["results"][0]["report"]["worker_module_origin"]["search_path_head"].append(
            source_src_root
        )

        validation = runtime.yaoyorozu.validate_worker_dispatch_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["external_dependency_module_origin_bound"])
        self.assertIn(
            "worker_module_origin.search_path_head must omit source fallback root",
            validation["errors"],
        )

    def test_worker_dispatch_receipt_rejects_tampered_dependency_module_origin(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_yaoyorozu_demo()
        tampered = json.loads(json.dumps(result["dispatch_receipt"]))
        tampered["results"][0]["report"]["worker_module_origin"]["module_file"] = (
            tampered["workspace_root"] + "/src/omoikane/agentic/local_worker_stub.py"
        )
        tampered["results"][0]["dependency_module_origin_path"] = (
            tampered["results"][0]["report"]["worker_module_origin"]["module_file"]
        )

        validation = runtime.yaoyorozu.validate_worker_dispatch_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["external_dependency_module_origin_bound"])
        self.assertIn("worker_module_origin.module_file mismatch", validation["errors"])

    def test_task_graph_binding_groups_eval_and_docs_under_complexity_ceiling(self) -> None:
        result = OmoikaneReferenceOS().run_yaoyorozu_demo()
        binding = result["task_graph_binding"]

        self.assertTrue(binding["validation"]["ok"])
        self.assertEqual("self-modify-patch-v1", binding["proposal_profile"])
        self.assertEqual(
            "self-modify-three-root-bundle-v1",
            binding["bundle_strategy"]["strategy_id"],
        )
        self.assertTrue(binding["validation"]["bundle_strategy_ok"])
        self.assertEqual(3, binding["task_graph_dispatch"]["dispatched_count"])
        self.assertEqual(
            4,
            sum(len(node_binding["dispatch_unit_ids"]) for node_binding in binding["node_bindings"]),
        )
        self.assertEqual(3, binding["task_graph_synthesis"]["accepted_result_count"])
        self.assertIn(
            ["docs", "eval"],
            sorted(
                sorted(node_binding["coverage_areas"])
                for node_binding in binding["node_bindings"]
            ),
        )

    def test_task_graph_binding_switches_bundle_strategy_by_proposal_profile(self) -> None:
        memory_edit = OmoikaneReferenceOS().run_yaoyorozu_demo(proposal_profile="memory-edit-v1")
        fork_request = OmoikaneReferenceOS().run_yaoyorozu_demo(proposal_profile="fork-request-v1")
        inter_mind = OmoikaneReferenceOS().run_yaoyorozu_demo(
            proposal_profile="inter-mind-negotiation-v1"
        )

        self.assertEqual(
            "memory-edit-required-dispatch-three-root-v1",
            memory_edit["task_graph_binding"]["bundle_strategy"]["strategy_id"],
        )
        self.assertTrue(memory_edit["task_graph_binding"]["validation"]["bundle_strategy_ok"])
        self.assertEqual(
            [["docs"], ["eval"], ["runtime"]],
            sorted(
                sorted(node_binding["coverage_areas"])
                for node_binding in memory_edit["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertEqual(
            "fork-request-required-dispatch-three-root-v1",
            fork_request["task_graph_binding"]["bundle_strategy"]["strategy_id"],
        )
        self.assertTrue(fork_request["task_graph_binding"]["validation"]["bundle_strategy_ok"])
        self.assertEqual(
            [["docs"], ["runtime"], ["schema"]],
            sorted(
                sorted(node_binding["coverage_areas"])
                for node_binding in fork_request["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertEqual(
            "inter-mind-negotiation-contract-sync-v1",
            inter_mind["task_graph_binding"]["bundle_strategy"]["strategy_id"],
        )
        self.assertTrue(inter_mind["task_graph_binding"]["validation"]["bundle_strategy_ok"])
        self.assertEqual(
            [["docs", "schema"], ["eval"], ["runtime"]],
            sorted(
                sorted(node_binding["coverage_areas"])
                for node_binding in inter_mind["task_graph_binding"]["node_bindings"]
            ),
        )

    def test_task_graph_binding_supports_requested_optional_dispatch(self) -> None:
        memory_edit = OmoikaneReferenceOS().run_yaoyorozu_demo(
            proposal_profile="memory-edit-v1",
            include_optional_coverage=["schema"],
        )
        fork_request = OmoikaneReferenceOS().run_yaoyorozu_demo(
            proposal_profile="fork-request-v1",
            include_optional_coverage=["eval"],
        )

        self.assertEqual(
            "memory-edit-optional-schema-dispatch-three-root-v1",
            memory_edit["task_graph_binding"]["bundle_strategy"]["strategy_id"],
        )
        self.assertEqual(
            ["schema"],
            memory_edit["task_graph_binding"]["bundle_strategy"]["requested_optional_coverage_areas"],
        )
        self.assertEqual(
            [["docs"], ["eval", "schema"], ["runtime"]],
            sorted(
                sorted(node_binding["coverage_areas"])
                for node_binding in memory_edit["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertEqual(
            "fork-request-optional-eval-dispatch-three-root-v1",
            fork_request["task_graph_binding"]["bundle_strategy"]["strategy_id"],
        )
        self.assertEqual(
            ["eval"],
            fork_request["task_graph_binding"]["bundle_strategy"]["requested_optional_coverage_areas"],
        )
        self.assertEqual(
            [["docs", "eval"], ["runtime"], ["schema"]],
            sorted(
                sorted(node_binding["coverage_areas"])
                for node_binding in fork_request["task_graph_binding"]["node_bindings"]
            ),
        )

    def test_build_request_binding_promotes_yaoyorozu_bundle_to_patch_generator_scope(self) -> None:
        result = OmoikaneReferenceOS().run_yaoyorozu_demo()
        binding = result["build_request_binding"]

        self.assertTrue(binding["validation"]["ok"])
        self.assertEqual("L5.PatchGenerator", binding["handoff_summary"]["target_subsystem"])
        self.assertTrue(binding["scope_validation"]["allowed"])
        self.assertEqual(
            result["convocation"]["session_id"],
            binding["council_action"]["session_id"],
        )
        self.assertEqual(
            "evals/continuity/council_output_build_request_pipeline.yaml",
            binding["build_request"]["constraints"]["must_pass"][0],
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
            binding["build_request"]["constraints"]["must_pass"],
        )
        self.assertEqual(
            binding["build_request"]["output_paths"],
            binding["build_request"]["constraints"]["allowed_write_paths"],
        )
        self.assertEqual(
            binding["handoff_summary"]["selected_candidate_count"],
            len(binding["selected_patch_candidates"]),
        )

    def test_build_request_binding_switches_profile_eval_by_proposal_profile(self) -> None:
        memory_edit = OmoikaneReferenceOS().run_yaoyorozu_demo(proposal_profile="memory-edit-v1")
        fork_request = OmoikaneReferenceOS().run_yaoyorozu_demo(proposal_profile="fork-request-v1")
        inter_mind = OmoikaneReferenceOS().run_yaoyorozu_demo(
            proposal_profile="inter-mind-negotiation-v1"
        )

        self.assertIn(
            "evals/agentic/yaoyorozu_memory_edit_profile.yaml",
            memory_edit["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_fork_request_profile.yaml",
            fork_request["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_inter_mind_negotiation_profile.yaml",
            inter_mind["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )


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
                    "jurisdiction": "JP-13",
                    "jurisdiction_bundle_ref": "legal://jp-13/cognitive-audit/v1",
                    "jurisdiction_bundle_digest": "sha256:jp13-cognitive-audit-v1",
                    "legal_execution_id": "legal-execution-0123456789ab",
                    "legal_execution_digest": (
                        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
                    ),
                    "legal_policy_ref": "policy://guardian-oversight/jp-13/reviewer-attestation/v1",
                    "network_receipt_id": "verifier-network-receipt-0123456789ab",
                },
                {
                    "reviewer_id": "human-reviewer-beta",
                    "jurisdiction": "US-CA",
                    "jurisdiction_bundle_ref": "legal://us-ca/cognitive-audit/v1",
                    "jurisdiction_bundle_digest": "sha256:usca-cognitive-audit-v1",
                    "legal_execution_id": "legal-execution-89abcdef0123",
                    "legal_execution_digest": (
                        "89abcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567"
                    ),
                    "legal_policy_ref": "policy://guardian-oversight/us-ca/reviewer-attestation/v1",
                    "network_receipt_id": "verifier-network-receipt-89abcdef0123",
                },
            ],
        }

    @staticmethod
    def _verifier_transport_trace() -> dict[str, object]:
        return {
            "kind": "distributed_transport_authority_route_trace",
            "schema_version": "1.0.0",
            "trace_ref": "authority-route-trace://federation/cognitive-audit-window",
            "authority_plane_ref": "authority-plane://federation/cognitive-audit-window",
            "authority_plane_digest": "a" * 64,
            "route_target_discovery_ref": "authority-route-targets://federation/cognitive-audit-window",
            "route_target_discovery_digest": "b" * 64,
            "envelope_ref": "distributed-envelope-0123456789ab",
            "envelope_digest": "c" * 64,
            "council_tier": "federation",
            "transport_profile": "distributed-council-handoff-v1",
            "trace_profile": "non-loopback-mtls-authority-route-v1",
            "socket_trace_profile": "mtls-socket-trace-v1",
            "os_observer_profile": "os-native-tcp-observer-v1",
            "route_target_discovery_profile": "bounded-authority-route-target-discovery-v1",
            "route_count": 2,
            "distinct_remote_host_count": 2,
            "mtls_authenticated_count": 2,
            "non_loopback_verified": True,
            "authority_plane_bound": True,
            "response_digest_bound": True,
            "socket_trace_complete": True,
            "os_observer_complete": True,
            "route_target_discovery_bound": True,
            "cross_host_verified": True,
            "trace_status": "authenticated",
            "digest": "d" * 64,
            "route_bindings": [
                {
                    "route_binding_ref": "authority-route://federation/cognitive-alpha",
                    "remote_host_ref": "host://federation/cognitive-alpha",
                    "remote_host_attestation_ref": "host-attestation://federation/cognitive-alpha",
                    "remote_jurisdiction": "JP-13",
                    "socket_trace": {"response_digest": "e" * 64},
                    "os_observer_receipt": {"host_binding_digest": "f" * 64},
                },
                {
                    "route_binding_ref": "authority-route://federation/cognitive-beta",
                    "remote_host_ref": "host://federation/cognitive-beta",
                    "remote_host_attestation_ref": "host-attestation://federation/cognitive-beta",
                    "remote_jurisdiction": "US-CA",
                    "socket_trace": {"response_digest": "1" * 64},
                    "os_observer_receipt": {"host_binding_digest": "2" * 64},
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
            verifier_transport_trace=self._verifier_transport_trace(),
        )
        validation = service.validate_binding(binding)

        self.assertTrue(validation["ok"])
        self.assertEqual("federation-attested-review", binding["execution_gate"])
        self.assertEqual("open-guardian-review", binding["final_follow_up_action"])
        self.assertEqual(1, validation["distributed_verdict_count"])
        self.assertTrue(validation["oversight_network_bound"])
        self.assertTrue(validation["multi_jurisdiction_review_bound"])
        self.assertTrue(validation["distributed_signature_bound"])
        self.assertTrue(validation["non_loopback_verifier_transport_bound"])
        self.assertTrue(binding["continuity_guard"]["distributed_verdict_signatures_bound"])
        self.assertTrue(binding["continuity_guard"]["non_loopback_verifier_transport_bound"])
        self.assertEqual(
            "cognitive-audit-non-loopback-verifier-transport-v1",
            binding["verifier_transport_profile"]["profile_id"],
        )
        signature_binding = binding["distributed_verdicts"][0]["signature_binding"]
        self.assertEqual(
            "distributed-council-verdict-signature-binding-v1",
            signature_binding["profile_id"],
        )
        self.assertEqual(
            "council://federation/returned-result-signer/v1",
            signature_binding["signer_ref"],
        )
        self.assertFalse(signature_binding["raw_signature_payload_exposed"])
        self.assertEqual(
            ["JP-13", "US-CA"],
            binding["jurisdiction_review_profile"]["jurisdictions"],
        )

    def test_governance_binding_requires_multi_jurisdiction_reviewer_quorum(self) -> None:
        service = CognitiveAuditGovernanceService()
        record, resolution = self._build_record_and_resolution()
        oversight_event = self._oversight_event()
        oversight_event["reviewer_bindings"][1]["jurisdiction"] = "JP-13"
        oversight_event["reviewer_bindings"][1][
            "legal_policy_ref"
        ] = "policy://guardian-oversight/jp-13/reviewer-attestation/v1"

        with self.assertRaisesRegex(
            ValueError,
            "multi-jurisdiction reviewer quorum",
        ):
            service.bind_governance(
                record,
                resolution,
                distributed_resolutions=[],
                oversight_event=oversight_event,
                verifier_transport_trace=self._verifier_transport_trace(),
            )

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
            verifier_transport_trace=self._verifier_transport_trace(),
        )
        validation = service.validate_binding(binding)

        self.assertTrue(validation["ok"])
        self.assertEqual("distributed-conflict-human-escalation", binding["execution_gate"])
        self.assertEqual("escalate-to-human-governance", binding["final_follow_up_action"])
        self.assertTrue(binding["continuity_guard"]["conflict_detected"])
        self.assertTrue(binding["continuity_guard"]["multi_jurisdiction_review_bound"])
        self.assertTrue(binding["continuity_guard"]["distributed_verdict_signatures_bound"])
        self.assertTrue(binding["continuity_guard"]["non_loopback_verifier_transport_bound"])
        self.assertTrue(validation["distributed_signature_bound"])
        self.assertTrue(validation["non_loopback_verifier_transport_bound"])
        self.assertEqual(2, validation["distributed_verdict_count"])

    def test_governance_binding_rejects_tampered_distributed_verdict_signature(self) -> None:
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
            verifier_transport_trace=self._verifier_transport_trace(),
        )
        tampered = dict(binding)
        tampered["distributed_verdicts"] = [
            dict(verdict) for verdict in binding["distributed_verdicts"]
        ]
        tampered["distributed_verdicts"][0]["follow_up_action"] = "tampered-action"

        validation = service.validate_binding(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["distributed_signature_bound"])
        self.assertTrue(
            any("signature_binding.signed_payload_digest mismatch" in error for error in validation["errors"])
        )

    def test_governance_binding_rejects_tampered_verifier_transport_profile(self) -> None:
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
            verifier_transport_trace=self._verifier_transport_trace(),
        )
        tampered = dict(binding)
        tampered["verifier_transport_profile"] = dict(binding["verifier_transport_profile"])
        tampered["verifier_transport_profile"]["remote_jurisdictions"] = ["JP-13"]

        validation = service.validate_binding(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["non_loopback_verifier_transport_bound"])
        self.assertTrue(
            any("remote_jurisdictions incomplete" in error for error in validation["errors"])
        )


if __name__ == "__main__":
    unittest.main()
