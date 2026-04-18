from __future__ import annotations

import unittest

from omoikane.kernel.continuity import ContinuityLedger
from omoikane.kernel.ethics import ActionRequest, EthicsEnforcer
from omoikane.kernel.identity import ForkApprovals, IdentityRegistry


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

    def test_identity_fork_requires_triple_approval(self) -> None:
        registry = IdentityRegistry()
        identity = registry.create("consent://root")

        with self.assertRaises(PermissionError):
            registry.fork(identity.identity_id, "unsafe", ForkApprovals(True, False, False))


if __name__ == "__main__":
    unittest.main()
