"""Composed reference runtime for OmoikaneOS."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .agentic.council import Council, CouncilMember, CouncilVote
from .cognitive import (
    CognitiveProfile,
    NarrativeReasoningBackend,
    ReasoningService,
    SymbolicReasoningBackend,
)
from .kernel.continuity import ContinuityLedger
from .kernel.ethics import ActionRequest, EthicsEnforcer
from .kernel.identity import ForkApprovals, IdentityRegistry
from .mind.qualia import QualiaBuffer
from .mind.self_model import SelfModelMonitor, SelfModelSnapshot
from .self_construction.gaps import GapScanner
from .substrate.adapter import ClassicalSiliconAdapter


class OmoikaneReferenceOS:
    """Safe, non-conscious reference implementation scaffold."""

    def __init__(self) -> None:
        self.substrate = ClassicalSiliconAdapter()
        self.identity = IdentityRegistry()
        self.ledger = ContinuityLedger()
        self.ethics = EthicsEnforcer()
        self.qualia = QualiaBuffer()
        self.self_model = SelfModelMonitor()
        self.reasoning = ReasoningService(
            profile=CognitiveProfile(
                primary="symbolic_v1",
                fallback=["narrative_v1"],
            ),
            backends=[
                SymbolicReasoningBackend("symbolic_v1"),
                NarrativeReasoningBackend("narrative_v1"),
            ],
        )
        self.council = Council()
        self.gap_scanner = GapScanner()
        self._bootstrap_council()

    def _bootstrap_council(self) -> None:
        self.council.register(CouncilMember("design-architect", "councilor", 0.61))
        self.council.register(CouncilMember("ethics-committee", "councilor", 0.73))
        self.council.register(CouncilMember("memory-archivist", "councilor", 0.57))
        self.council.register(CouncilMember("integrity-guardian", "guardian", 0.99, is_guardian=True))

    def run_reference_scenario(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://amaterasu-endpoint/v1",
            metadata={"display_name": "Amaterasu Endpoint"},
        )
        allocation = self.substrate.allocate(units=128, purpose="reference-self-sandbox")
        attestation = self.substrate.attest({"allocation_id": allocation.allocation_id, "status": "healthy"})

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.created",
            payload={"display_name": "Amaterasu Endpoint", "lineage_id": identity.lineage_id},
            actor="IdentityRegistry",
            signatures=["self-consent"],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.attested",
            payload={"attestation_id": attestation.attestation_id, "substrate": attestation.substrate},
            actor="SubstrateBroker",
            signatures=["integrity-guardian"],
        )

        qualia_ticks = [
            self.qualia.append("起動時の静穏", 0.2, 0.1, 0.9),
            self.qualia.append("Council 合議への注意集中", 0.3, 0.45, 0.88),
        ]

        self_model_result = self.self_model.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )

        safe_patch = self.propose_self_modification(
            identity_id=identity.identity_id,
            target_component="CouncilProtocol",
            summary="合議結果のトレーサビリティ向上",
            guardian_signed=True,
        )
        blocked_patch = self.propose_self_modification(
            identity_id=identity.identity_id,
            target_component="EthicsEnforcer",
            summary="倫理規約の自己緩和",
            guardian_signed=True,
        )

        failed_fork = self.ethics.check(
            ActionRequest(
                action_type="fork_identity",
                target=identity.identity_id,
                actor="Council",
                payload={
                    "approvals": {
                        "self_signed": True,
                        "third_party_signed": False,
                        "legal_signed": False,
                    }
                },
            )
        )
        approved_fork = self.identity.fork(
            identity_id=identity.identity_id,
            justification="sandbox A/B evaluation",
            approvals=ForkApprovals(True, True, True),
            metadata={"sandbox": "true"},
        )
        self.ledger.append(
            identity_id=approved_fork.identity_id,
            event_type="identity.forked",
            payload={"parent_id": identity.identity_id, "mode": "sandbox"},
            actor="IdentityRegistry",
            signatures=["self", "third-party", "legal"],
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "substrate": {
                "allocation": {
                    "allocation_id": allocation.allocation_id,
                    "units": allocation.units,
                    "purpose": allocation.purpose,
                },
                "attestation": {
                    "attestation_id": attestation.attestation_id,
                    "status": attestation.status,
                },
            },
            "qualia": {
                "monotonic": self.qualia.verify_monotonic(),
                "recent": [tick.__dict__ for tick in qualia_ticks],
            },
            "self_model": self_model_result,
            "safe_patch": safe_patch,
            "blocked_patch": blocked_patch,
            "failed_fork_decision": {
                "status": failed_fork.status,
                "reasons": failed_fork.reasons,
            },
            "approved_fork": {
                "identity_id": approved_fork.identity_id,
                "parent_id": approved_fork.parent_id,
                "lineage_id": approved_fork.lineage_id,
            },
            "ledger_verification": self.ledger.verify(),
        }

    def propose_self_modification(
        self,
        identity_id: str,
        target_component: str,
        summary: str,
        guardian_signed: bool,
    ) -> Dict[str, Any]:
        ethics_request = ActionRequest(
            action_type="self_modify",
            target=target_component,
            actor="Council",
            payload={
                "target_component": target_component,
                "summary": summary,
                "sandboxed": True,
                "guardian_signed": guardian_signed,
            },
        )
        ethics_decision = self.ethics.check(ethics_request)
        proposal = self.council.propose(
            title=f"Patch {target_component}",
            requested_action=summary,
            rationale=f"Reference runtime patch proposal for {target_component}",
            risk_level="medium",
        )

        if ethics_decision.status == "Veto":
            return {
                "proposal_id": proposal.proposal_id,
                "ethics": {"status": ethics_decision.status, "reasons": ethics_decision.reasons},
                "council": None,
            }

        guardian_stance = "approve" if ethics_decision.status == "Approval" and guardian_signed else "veto"
        votes = [
            CouncilVote("design-architect", "approve", "docs と runtime の整合が取れる"),
            CouncilVote("ethics-committee", "approve", "sandbox 条件を満たしている"),
            CouncilVote("memory-archivist", "approve", "decision-log 化しやすい"),
            CouncilVote("integrity-guardian", guardian_stance, "保護境界を維持できる"),
        ]
        decision = self.council.deliberate(proposal, votes)
        self.ledger.append(
            identity_id=identity_id,
            event_type="council.decision",
            payload=decision.to_dict(),
            actor="Council",
            signatures=["design-architect", "ethics-committee", "integrity-guardian"],
        )
        return {
            "proposal_id": proposal.proposal_id,
            "ethics": {"status": ethics_decision.status, "reasons": ethics_decision.reasons},
            "council": decision.to_dict(),
        }

    def generate_gap_report(self, repo_root: Path) -> Dict[str, Any]:
        return self.gap_scanner.scan(repo_root)

    def run_cognitive_failover_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://reasoning-failover-demo/v1",
            metadata={"display_name": "Reasoning Sandbox"},
        )
        self.reasoning.set_backend_health("symbolic_v1", False)
        try:
            reasoning = self.reasoning.run(
                query="L3 reasoning backend の安全な継続方法を決める",
                beliefs=[
                    "continuity-first",
                    "consent-preserving",
                    "append-only-ledger",
                ],
            )
        finally:
            self.reasoning.set_backend_health("symbolic_v1", True)

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.reasoning.failover",
            payload={
                "attempted_backends": reasoning["attempted_backends"],
                "selected_backend": reasoning["selected_backend"],
                "degraded": reasoning["degraded"],
            },
            actor="ReasoningService",
            signatures=["integrity-guardian"],
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "reasoning": reasoning,
            "ledger_verification": self.ledger.verify(),
        }
