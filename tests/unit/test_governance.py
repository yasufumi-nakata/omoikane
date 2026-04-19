from __future__ import annotations

import unittest

from omoikane.governance import AmendmentService, AmendmentSignatures, NamingService, OversightService
from omoikane.agentic.trust import TrustService


class AmendmentServiceTests(unittest.TestCase):
    def test_t_core_always_freezes(self) -> None:
        service = AmendmentService()
        proposal = service.propose(
            tier="T-Core",
            target_clauses=["ethics.A1"],
            draft_text_ref="meta/decision-log/core.md",
            rationale="core clauses remain outside runtime apply",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="unanimous",
                self_consent=True,
                guardian_attested=True,
                human_reviewers=3,
                design_architect_attested=True,
            ),
        )

        updated, decision = service.decide(proposal, continuity_event_ref="entry-1")

        self.assertEqual("frozen", updated.status)
        self.assertFalse(decision["allow_apply"])
        self.assertEqual("none", decision["applied_stage"])

    def test_t_kernel_requires_two_human_reviewers(self) -> None:
        service = AmendmentService()
        proposal = service.propose(
            tier="T-Kernel",
            target_clauses=["continuity.profile"],
            draft_text_ref="meta/decision-log/kernel.md",
            rationale="kernel changes require external review",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="unanimous",
                self_consent=True,
                guardian_attested=True,
                human_reviewers=1,
                design_architect_attested=True,
            ),
        )

        updated, decision = service.decide(proposal, continuity_event_ref="entry-2")

        self.assertEqual("pending-human-review", updated.status)
        self.assertFalse(decision["allow_apply"])
        self.assertTrue(any("2 名以上" in reason for reason in decision["reasons"]))

    def test_t_operational_accepts_majority_plus_guardian(self) -> None:
        service = AmendmentService()
        proposal = service.propose(
            tier="T-Operational",
            target_clauses=["council.timeout"],
            draft_text_ref="meta/decision-log/operational.md",
            rationale="operational rules can progress via guarded rollout",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="majority",
                guardian_attested=True,
                design_architect_attested=True,
            ),
        )

        updated, decision = service.decide(proposal, continuity_event_ref="entry-3")

        self.assertEqual("applied", updated.status)
        self.assertTrue(decision["allow_apply"])
        self.assertEqual("5pct", decision["applied_stage"])


class OversightServiceTests(unittest.TestCase):
    def test_network_verification_binds_verifier_receipt(self) -> None:
        service = OversightService()
        service.register_reviewer(
            reviewer_id="reviewer-network",
            display_name="Reviewer Network",
            credential_id="credential-network",
            attestation_type="institutional-badge",
            proof_ref="proof://oversight/reviewer-network",
            jurisdiction="JP-13",
            valid_until="2027-01-01T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://oversight/reviewer-network",
            escalation_contact="mailto:reviewer-network@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )

        verified = service.verify_reviewer_from_network(
            "reviewer-network",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-network",
            challenge_ref="challenge://guardian-oversight/reviewer-network/2026-04-20T02:00:00Z",
            challenge_digest="sha256:reviewer-network-live-proof",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-20T02:00:00+00:00",
            valid_until="2026-10-20T00:00:00+00:00",
        )

        network_receipt = verified["credential_verification"]["network_receipt"]
        self.assertEqual("guardian-reviewer-remote-attestation-v1", network_receipt["network_profile_id"])
        self.assertEqual("verifier://guardian-oversight.jp", network_receipt["verifier_endpoint"])
        self.assertEqual(
            "root://guardian-oversight.jp/reviewer-live-pki",
            network_receipt["trust_root_ref"],
        )
        self.assertLessEqual(network_receipt["observed_latency_ms"], 250.0)

    def test_network_verification_rejects_unknown_endpoint(self) -> None:
        service = OversightService()
        service.register_reviewer(
            reviewer_id="reviewer-unknown-endpoint",
            display_name="Reviewer Unknown Endpoint",
            credential_id="credential-unknown-endpoint",
            attestation_type="institutional-badge",
            proof_ref="proof://oversight/reviewer-unknown-endpoint",
            jurisdiction="JP-13",
            valid_until="2027-01-01T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://oversight/reviewer-unknown-endpoint",
            escalation_contact="mailto:reviewer-unknown-endpoint@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )

        with self.assertRaisesRegex(ValueError, "unsupported verifier network endpoint"):
            service.verify_reviewer_from_network(
                "reviewer-unknown-endpoint",
                verifier_ref="verifier://guardian-oversight.us/reviewer-unknown-endpoint",
                challenge_ref="challenge://guardian-oversight/reviewer-unknown-endpoint/2026-04-20T02:10:00Z",
                challenge_digest="sha256:reviewer-unknown-endpoint-live-proof",
                jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
                jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
                verified_at="2026-04-20T02:10:00+00:00",
                valid_until="2026-10-20T00:00:00+00:00",
            )

    def test_attestation_requires_live_credential_verification(self) -> None:
        service = OversightService()
        service.register_reviewer(
            reviewer_id="reviewer-unverified",
            display_name="Reviewer Unverified",
            credential_id="credential-unverified",
            attestation_type="government-id",
            proof_ref="proof://oversight/reviewer-unverified",
            jurisdiction="JP-13",
            valid_until="2027-01-01T00:00:00+00:00",
            liability_mode="individual",
            legal_ack_ref="legal://oversight/reviewer-unverified",
            escalation_contact="mailto:reviewer-unverified@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )

        event = service.record(
            guardian_role="integrity",
            category="veto",
            payload_ref="entry-unverified",
            escalation_path=["human-reviewer-pool-A"],
        )

        with self.assertRaisesRegex(PermissionError, "lacks live credential verification"):
            service.attest(event["event_id"], reviewer_id="reviewer-unverified")

    def test_veto_event_satisfies_quorum_after_one_attestation(self) -> None:
        service = OversightService()
        service.register_reviewer(
            reviewer_id="reviewer-1",
            display_name="Reviewer One",
            credential_id="credential-1",
            attestation_type="government-id",
            proof_ref="proof://oversight/reviewer-1",
            jurisdiction="JP-13",
            valid_until="2027-01-01T00:00:00+00:00",
            liability_mode="individual",
            legal_ack_ref="legal://oversight/reviewer-1",
            escalation_contact="mailto:reviewer-1@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )
        service.verify_reviewer(
            "reviewer-1",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-1",
            challenge_ref="challenge://guardian-oversight/reviewer-1/2026-04-19T13:00:00Z",
            challenge_digest="sha256:reviewer-1-live-proof",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-19T13:00:00+00:00",
            valid_until="2026-10-19T00:00:00+00:00",
        )

        event = service.record(
            guardian_role="integrity",
            category="veto",
            payload_ref="entry-1",
            escalation_path=["human-reviewer-pool-A"],
        )
        updated = service.attest(event["event_id"], reviewer_id="reviewer-1")

        self.assertEqual(1, updated["human_attestation"]["required_quorum"])
        self.assertEqual(1, updated["human_attestation"]["received_quorum"])
        self.assertEqual("satisfied", updated["human_attestation"]["status"])
        self.assertEqual(1, len(updated["reviewer_bindings"]))
        self.assertEqual("credential-1", updated["reviewer_bindings"][0]["credential_id"])
        self.assertEqual("individual", updated["reviewer_bindings"][0]["liability_mode"])
        self.assertEqual(
            "reviewer-live-proof-bridge-v1",
            updated["reviewer_bindings"][0]["transport_profile"],
        )
        self.assertEqual(
            "legal://jp-13/guardian-oversight/v1",
            updated["reviewer_bindings"][0]["jurisdiction_bundle_ref"],
        )
        self.assertIsNone(updated["reviewer_bindings"][0]["network_receipt_id"])

    def test_attestation_rejects_reviewer_outside_scope(self) -> None:
        service = OversightService()
        service.register_reviewer(
            reviewer_id="reviewer-2",
            display_name="Reviewer Two",
            credential_id="credential-2",
            attestation_type="institutional-badge",
            proof_ref="proof://oversight/reviewer-2",
            jurisdiction="JP-13",
            valid_until="2027-01-01T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://oversight/reviewer-2",
            escalation_contact="mailto:reviewer-2@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )
        service.verify_reviewer(
            "reviewer-2",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-2",
            challenge_ref="challenge://guardian-oversight/reviewer-2/2026-04-19T13:05:00Z",
            challenge_digest="sha256:reviewer-2-live-proof",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-19T13:05:00+00:00",
            valid_until="2026-10-19T00:00:00+00:00",
        )

        event = service.record(
            guardian_role="integrity",
            category="pin-renewal",
            payload_ref="entry-unauthorized",
            escalation_path=["human-reviewer-pool-A"],
        )

        with self.assertRaisesRegex(PermissionError, "pin-renewal"):
            service.attest(event["event_id"], reviewer_id="reviewer-2")

    def test_pin_breach_unpins_guardian_role(self) -> None:
        trust = TrustService()
        trust.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap",
        )
        service = OversightService(trust_service=trust)
        service.register_reviewer(
            reviewer_id="reviewer-3",
            display_name="Reviewer Three",
            credential_id="credential-3",
            attestation_type="institutional-badge",
            proof_ref="proof://oversight/reviewer-3",
            jurisdiction="JP-13",
            valid_until="2027-01-01T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://oversight/reviewer-3",
            escalation_contact="mailto:reviewer-3@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["pin-renewal"],
        )
        verified = service.verify_reviewer(
            "reviewer-3",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-3",
            challenge_ref="challenge://guardian-oversight/reviewer-3/2026-04-19T13:10:00Z",
            challenge_digest="sha256:reviewer-3-live-proof",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-19T13:10:00+00:00",
            valid_until="2026-10-19T00:00:00+00:00",
        )

        event = service.record(
            guardian_role="integrity",
            category="pin-renewal",
            payload_ref="entry-2",
            escalation_path=["human-reviewer-pool-A", "external-ethics-board"],
        )
        breached = service.breach(event["event_id"])
        snapshot = trust.snapshot("integrity-guardian")

        self.assertEqual("verified", verified["credential_verification"]["status"])
        self.assertEqual("breached", breached["human_attestation"]["status"])
        self.assertTrue(breached["pin_breach_propagated"])
        self.assertFalse(snapshot["pinned_by_human"])
        self.assertFalse(snapshot["eligibility"]["guardian_role"])


class NamingServiceTests(unittest.TestCase):
    def test_policy_snapshot_emits_fixed_canonical_names(self) -> None:
        service = NamingService()

        policy = service.policy_snapshot()

        self.assertEqual("naming_policy", policy["kind"])
        self.assertEqual("Omoikane", policy["rules"]["project_romanization"]["canonical"])
        self.assertEqual("Mirage Self", policy["rules"]["sandbox_self_name"]["canonical"])
        self.assertFalse(policy["enforcement"]["abbreviations_allowed"])

    def test_review_term_rejects_hyphenated_brand(self) -> None:
        service = NamingService()

        result = service.review_term(
            "project_romanization",
            "Omoi-KaneOS",
            context="external_brand",
        )

        self.assertEqual("rewrite-required", result["status"])
        self.assertEqual("OmoikaneOS", result["suggestion"])
        self.assertFalse(result["allowed_in_context"])

    def test_review_term_allows_runtime_alias_only_in_code_context(self) -> None:
        service = NamingService()

        result = service.review_term(
            "sandbox_self_name",
            "SandboxSentinel",
            context="code_identifier",
        )

        self.assertEqual("allowed-alias", result["status"])
        self.assertTrue(result["allowed_in_context"])
        self.assertEqual("Mirage Self", result["suggestion"])


if __name__ == "__main__":
    unittest.main()
