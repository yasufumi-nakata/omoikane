from __future__ import annotations

import unittest

from omoikane.kernel.continuity import ContinuityLedger
from omoikane.kernel.ethics import ActionRequest, EthicsEnforcer
from omoikane.kernel.identity import ForkApprovals, IdentityRegistry


class KernelTests(unittest.TestCase):
    def test_continuity_ledger_detects_tamper(self) -> None:
        ledger = ContinuityLedger()
        ledger.append("id-1", "identity.created", {"name": "yasufumi"}, "IdentityRegistry")
        ledger.append("id-1", "qualia.recorded", {"tick": 1}, "QualiaBuffer")
        ledger.entries()[1].payload["tick"] = 99

        verification = ledger.verify()

        self.assertFalse(verification["ok"])
        self.assertTrue(any("entry_hash mismatch" in item for item in verification["errors"]))

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

    def test_identity_fork_requires_triple_approval(self) -> None:
        registry = IdentityRegistry()
        identity = registry.create("consent://root")

        with self.assertRaises(PermissionError):
            registry.fork(identity.identity_id, "unsafe", ForkApprovals(True, False, False))


if __name__ == "__main__":
    unittest.main()

