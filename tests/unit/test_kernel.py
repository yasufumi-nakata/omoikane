from __future__ import annotations

import unittest

from omoikane.kernel.continuity import ContinuityLedger
from omoikane.kernel.ethics import ActionRequest, EthicsEnforcer
from omoikane.kernel.identity import ForkApprovals, IdentityRegistry
from omoikane.kernel.scheduler import AscensionScheduler
from omoikane.kernel.termination import TerminationGate
from omoikane.substrate.adapter import ClassicalSiliconAdapter


class KernelTests(unittest.TestCase):
    def test_continuity_ledger_detects_tamper(self) -> None:
        ledger = ContinuityLedger()
        ledger.append(
            "id-1",
            "identity.created",
            {"name": "yasufumi"},
            "IdentityRegistry",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        ledger.append(
            "id-1",
            "mind.qualia.checkpointed",
            {"tick": 1},
            "QualiaBuffer",
            category="qualia-checkpoint",
            layer="L2",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        ledger.entries()[1].payload["tick"] = 99

        verification = ledger.verify()

        self.assertFalse(verification["ok"])
        self.assertTrue(any("payload_ref mismatch" in item for item in verification["errors"]))

    def test_continuity_ledger_requires_category_signatures(self) -> None:
        ledger = ContinuityLedger()

        with self.assertRaises(ValueError):
            ledger.append(
                "id-1",
                "council.patch.approved",
                {"proposal_id": "proposal-1"},
                "Council",
                category="self-modify",
                layer="L4",
                signature_roles=["self", "council"],
                substrate="classical-silicon",
            )

    def test_continuity_ledger_detects_signature_tamper(self) -> None:
        ledger = ContinuityLedger()
        ledger.append(
            "id-1",
            "council.patch.approved",
            {"proposal_id": "proposal-1"},
            "Council",
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        ledger.entries()[0].signatures["guardian"] = "hmac-sha256:tampered"

        verification = ledger.verify()

        self.assertFalse(verification["ok"])
        self.assertTrue(any("signature mismatch" in item for item in verification["errors"]))

    def test_ethics_blocks_immutable_self_modification(self) -> None:
        enforcer = EthicsEnforcer()

        decision = enforcer.check(
            ActionRequest(
                action_type="self_modify",
                target="EthicsEnforcer",
                actor="Council",
                payload={
                    "target_component": "EthicsEnforcer",
                    "sandboxed": True,
                    "guardian_signed": True,
                },
            )
        )

        self.assertEqual("Veto", decision.status)
        self.assertEqual(["A1-immutable-boundary"], decision.rule_ids)

    def test_ethics_exposes_rule_tree_profile(self) -> None:
        enforcer = EthicsEnforcer()

        profile = enforcer.profile()
        rule = enforcer.explain_rule("A1-immutable-boundary")

        self.assertEqual("deterministic-rule-tree-v0", profile["language_id"])
        self.assertEqual("ethics_rule", rule["kind"])
        self.assertEqual("veto", rule["outcome"])
        self.assertEqual("in", rule["predicate"]["all"][1]["operator"])

    def test_ethics_records_escalation_event(self) -> None:
        enforcer = EthicsEnforcer()
        request = ActionRequest(
            action_type="self_modify",
            target="CouncilProtocol",
            actor="Council",
            payload={
                "target_component": "CouncilProtocol",
                "sandboxed": False,
                "guardian_signed": False,
            },
        )

        decision = enforcer.check(request)
        event = enforcer.record_decision("ethq-escalate-0001", request, decision)

        self.assertEqual("Escalate", decision.status)
        self.assertEqual("escalate", event["decision"])
        self.assertEqual("A5-self-modify-sandbox-first", event["rule_id"])
        self.assertIn("guardian", event["signatures"])

    def test_ethics_vetoes_blocked_ewa_command(self) -> None:
        enforcer = EthicsEnforcer()

        decision = enforcer.check(
            ActionRequest(
                action_type="ewa_command",
                target="device://ewa-arm-01",
                actor="ExternalWorldAgentController",
                payload={
                    "matched_tokens": ["harm.human"],
                    "intent_ambiguous": False,
                },
            )
        )

        self.assertEqual("Veto", decision.status)
        self.assertEqual(["A7-ewa-blocked-token"], decision.rule_ids)

    def test_ethics_escalates_ambiguous_ewa_intent(self) -> None:
        enforcer = EthicsEnforcer()

        decision = enforcer.check(
            ActionRequest(
                action_type="ewa_command",
                target="device://ewa-arm-02",
                actor="ExternalWorldAgentController",
                payload={
                    "matched_tokens": [],
                    "intent_ambiguous": True,
                },
            )
        )

        self.assertEqual("Escalate", decision.status)
        self.assertEqual(["A8-ewa-ambiguous-intent"], decision.rule_ids)

    def test_identity_fork_requires_triple_approval(self) -> None:
        registry = IdentityRegistry()
        identity = registry.create("consent://root")

        with self.assertRaises(PermissionError):
            registry.fork(identity.identity_id, "unsafe", ForkApprovals(True, False, False))

    def test_termination_gate_completes_and_releases_allocation(self) -> None:
        registry = IdentityRegistry()
        ledger = ContinuityLedger()
        substrate = ClassicalSiliconAdapter()
        gate = TerminationGate(registry, ledger, substrate)
        identity = registry.create(
            "consent://termination-complete",
            metadata={"termination_self_proof": "self-proof://termination-complete/v1"},
        )
        allocation = substrate.allocate(12, "termination-test", identity.identity_id)

        outcome = gate.request(
            identity.identity_id,
            "self-proof://termination-complete/v1",
            scheduler_handle_ref="schedule://termination-complete",
            active_allocation_id=allocation.allocation_id,
        )

        self.assertEqual("completed", outcome["status"])
        self.assertTrue(outcome["scheduler_handle_cancelled"])
        self.assertTrue(outcome["substrate_lease_released"])
        self.assertLessEqual(outcome["latency_ms"], 200)
        self.assertEqual("terminated", registry.get(identity.identity_id).status)
        self.assertEqual("released", substrate.allocations[allocation.allocation_id].status)
        self.assertTrue(ledger.verify()["ok"])

    def test_termination_gate_rejects_invalid_self_proof(self) -> None:
        registry = IdentityRegistry()
        ledger = ContinuityLedger()
        substrate = ClassicalSiliconAdapter()
        gate = TerminationGate(registry, ledger, substrate)
        identity = registry.create(
            "consent://termination-reject",
            metadata={"termination_self_proof": "self-proof://termination-reject/v1"},
        )

        outcome = gate.request(identity.identity_id, "self-proof://wrong-proof/v1")

        self.assertEqual("rejected", outcome["status"])
        self.assertEqual("invalid-self-proof", outcome["reject_reason"])
        self.assertEqual("active", registry.get(identity.identity_id).status)
        self.assertEqual("rejected", gate.observe(identity.identity_id)["status"])
        self.assertTrue(ledger.verify()["ok"])

    def test_termination_gate_respects_preconsented_cool_off(self) -> None:
        registry = IdentityRegistry()
        ledger = ContinuityLedger()
        substrate = ClassicalSiliconAdapter()
        gate = TerminationGate(registry, ledger, substrate)
        identity = registry.create(
            "consent://termination-cool-off",
            metadata={
                "termination_self_proof": "self-proof://termination-cool-off/v1",
                "termination_policy_mode": "cool-off-allowed",
                "termination_policy_days": "30",
            },
        )

        outcome = gate.request(
            identity.identity_id,
            "self-proof://termination-cool-off/v1",
            invoke_cool_off=True,
        )

        self.assertEqual("cool-off-pending", outcome["status"])
        self.assertFalse(outcome["scheduler_handle_cancelled"])
        self.assertFalse(outcome["substrate_lease_released"])
        self.assertEqual("active", registry.get(identity.identity_id).status)
        observed = gate.observe(identity.identity_id)
        self.assertEqual("cool-off-pending", observed["status"])
        self.assertEqual(30, observed["policy"]["cool_off_days"])
        self.assertTrue(ledger.verify()["ok"])

    def test_ascension_scheduler_enforces_method_a_stage_order(self) -> None:
        ledger = ContinuityLedger()
        scheduler = AscensionScheduler(ledger)
        plan = scheduler.build_method_a_plan("identity://scheduler-order")
        handle = scheduler.schedule(plan)

        with self.assertRaises(ValueError):
            scheduler.advance(handle["handle_id"], "identity-confirmation")

        result = scheduler.advance(handle["handle_id"], "scan-baseline")

        self.assertEqual("scan-baseline", result["completed_stage"])
        self.assertEqual("bdb-bridge", result["next_stage"])
        self.assertEqual("advancing", scheduler.observe(handle["handle_id"])["status"])
        self.assertTrue(ledger.verify()["ok"])

    def test_ascension_scheduler_timeout_rolls_back_to_prior_stage(self) -> None:
        ledger = ContinuityLedger()
        scheduler = AscensionScheduler(ledger)
        plan = scheduler.build_method_a_plan("identity://scheduler-timeout")
        handle = scheduler.schedule(plan)
        scheduler.advance(handle["handle_id"], "scan-baseline")
        scheduler.advance(handle["handle_id"], "bdb-bridge")

        timeout = scheduler.enforce_timeout(handle["handle_id"], elapsed_ms=2_100_000)
        observed = scheduler.observe(handle["handle_id"])

        self.assertEqual("rollback", timeout["action"])
        self.assertEqual("bdb-bridge", timeout["rollback_target"])
        self.assertEqual("rolled-back", observed["status"])
        self.assertEqual("bdb-bridge", observed["current_stage"])
        self.assertTrue(scheduler.validate_handle(observed)["ok"])
        self.assertTrue(ledger.verify()["ok"])

    def test_ascension_scheduler_pause_resume_and_complete(self) -> None:
        ledger = ContinuityLedger()
        scheduler = AscensionScheduler(ledger)
        plan = scheduler.build_method_a_plan("identity://scheduler-complete")
        handle = scheduler.schedule(plan)
        scheduler.advance(handle["handle_id"], "scan-baseline")
        scheduler.advance(handle["handle_id"], "bdb-bridge")

        paused = scheduler.pause(handle["handle_id"], "bounded pause for continuity witness")
        resumed = scheduler.resume(handle["handle_id"])
        scheduler.advance(handle["handle_id"], "identity-confirmation")
        result = scheduler.advance(handle["handle_id"], "active-handoff")
        observed = scheduler.observe(handle["handle_id"])

        self.assertEqual("paused", paused["status"])
        self.assertEqual("advancing", resumed["status"])
        self.assertEqual("completed", result["status"])
        self.assertEqual("completed", observed["status"])
        self.assertTrue(scheduler.validate_handle(observed)["ok"])
        self.assertTrue(ledger.verify()["ok"])

    def test_ascension_scheduler_method_b_substrate_signal_pauses_and_rolls_back(self) -> None:
        ledger = ContinuityLedger()
        scheduler = AscensionScheduler(ledger)
        plan = scheduler.build_method_b_plan("identity://scheduler-method-b")
        handle = scheduler.schedule(plan)
        scheduler.advance(handle["handle_id"], "shadow-sync")

        paused = scheduler.handle_substrate_signal(
            handle["handle_id"],
            severity="degraded",
            source_substrate="classical_silicon.shadow",
            reason="replication jitter exceeded threshold",
        )
        resumed = scheduler.resume(handle["handle_id"])
        scheduler.advance(handle["handle_id"], "dual-channel-review")
        rollback = scheduler.handle_substrate_signal(
            handle["handle_id"],
            severity="critical",
            source_substrate="classical_silicon.shadow",
            reason="authority sync diverged",
        )
        observed = scheduler.observe(handle["handle_id"])

        self.assertEqual("pause", paused["action"])
        self.assertEqual("paused", paused["status"])
        self.assertEqual("advancing", resumed["status"])
        self.assertEqual("rollback", rollback["action"])
        self.assertEqual("dual-channel-review", rollback["rollback_target"])
        self.assertEqual("rolled-back", observed["status"])
        self.assertEqual("dual-channel-review", observed["current_stage"])
        self.assertTrue(scheduler.validate_handle(observed)["ok"])
        self.assertTrue(ledger.verify()["ok"])

    def test_ascension_scheduler_method_c_fails_closed_on_critical_signal(self) -> None:
        ledger = ContinuityLedger()
        scheduler = AscensionScheduler(ledger)
        plan = scheduler.build_method_c_plan("identity://scheduler-method-c")
        handle = scheduler.schedule(plan)
        scheduler.advance(handle["handle_id"], "consent-lock")

        signal = scheduler.handle_substrate_signal(
            handle["handle_id"],
            severity="critical",
            source_substrate="classical_silicon.scan-array",
            reason="scan commit lost redundancy",
        )
        observed = scheduler.observe(handle["handle_id"])

        self.assertEqual("fail", signal["action"])
        self.assertEqual("scan-commit", signal["stage_id"])
        self.assertEqual("failed", observed["status"])
        self.assertEqual("scan-commit", observed["current_stage"])
        self.assertTrue(scheduler.validate_handle(observed)["ok"])
        self.assertTrue(ledger.verify()["ok"])


if __name__ == "__main__":
    unittest.main()
