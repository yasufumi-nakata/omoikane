"""Composed reference runtime for OmoikaneOS."""

from __future__ import annotations

from dataclasses import asdict
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
from .mind.connectome import ConnectomeModel
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
        self.connectome = ConnectomeModel()
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
        allocation = self.substrate.allocate(
            units=128,
            purpose="reference-self-sandbox",
            identity_id=identity.identity_id,
        )
        attestation = self.substrate.attest(
            allocation_id=allocation.allocation_id,
            integrity={"allocation_id": allocation.allocation_id, "status": "healthy"},
        )
        energy_floor = self.substrate.energy_floor(identity.identity_id, workload_class="sandbox")

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.created",
            payload={"display_name": "Amaterasu Endpoint", "lineage_id": identity.lineage_id},
            actor="IdentityRegistry",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.attested",
            payload={"attestation_id": attestation.attestation_id, "substrate": attestation.substrate},
            actor="SubstrateBroker",
            category="attestation",
            layer="L0",
            signature_roles=["guardian"],
            substrate=attestation.substrate,
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
            category="fork",
            layer="L1",
            signature_roles=["self", "council", "guardian", "third_party"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "substrate": {
                "allocation": asdict(allocation),
                "attestation": asdict(attestation),
                "energy_floor": asdict(energy_floor),
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
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
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
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "proposal_id": proposal.proposal_id,
            "ethics": {"status": ethics_decision.status, "reasons": ethics_decision.reasons},
            "council": decision.to_dict(),
        }

    def generate_gap_report(self, repo_root: Path) -> Dict[str, Any]:
        return self.gap_scanner.scan(repo_root)

    def run_council_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://council-timeout-demo/v1",
            metadata={"display_name": "Council Timeout Sandbox"},
        )
        standard_proposal = self.council.propose(
            title="Timeout-aware self modification review",
            requested_action="approve-build",
            rationale="Standard session should fall back to weighted majority after soft timeout.",
            risk_level="medium",
            session_mode="standard",
        )
        standard_decision = self.council.deliberate(
            standard_proposal,
            [
                CouncilVote("design-architect", "approve", "設計整合は保たれる"),
                CouncilVote("ethics-committee", "approve", "倫理境界に触れない"),
                CouncilVote("memory-archivist", "reject", "議事録追記が不足している"),
            ],
            elapsed_ms=52_000,
            rounds_completed=3,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.session.timeout_fallback",
            payload=standard_decision.to_dict(),
            actor="Council",
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        expedited_proposal = self.council.propose(
            title="Emergency substrate review",
            requested_action="escalate",
            rationale="Expedited session must stop quickly and defer to a standard review if unresolved.",
            risk_level="high",
            session_mode="expedited",
        )
        expedited_decision = self.council.deliberate(
            expedited_proposal,
            [
                CouncilVote("design-architect", "approve", "暫定的な保全措置は妥当"),
                CouncilVote("integrity-guardian", "approve", "隔離を優先して追認へ回す"),
            ],
            elapsed_ms=1_500,
            rounds_completed=2,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.session.timeout_deferred",
            payload=expedited_decision.to_dict(),
            actor="Council",
            category="ethics-escalate",
            layer="L4",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policies": {
                "standard": asdict(self.council.session_policy("standard")),
                "expedited": asdict(self.council.session_policy("expedited")),
            },
            "sessions": {
                "standard_soft_timeout": standard_decision.to_dict(),
                "expedited_hard_timeout": expedited_decision.to_dict(),
            },
            "history": self.council.history(),
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_substrate_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://substrate-demo/v1",
            metadata={"display_name": "Substrate Migration Sandbox"},
        )
        allocation = self.substrate.allocate(
            units=96,
            purpose="substrate-migration-eval",
            identity_id=identity.identity_id,
        )
        energy_floor = self.substrate.energy_floor(
            identity.identity_id,
            workload_class="migration",
        )
        attestation = self.substrate.attest(
            allocation_id=allocation.allocation_id,
            integrity={
                "allocation_id": allocation.allocation_id,
                "tee": "reference-attestor-v1",
                "status": "healthy",
            },
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.attested",
            payload={
                "allocation_id": allocation.allocation_id,
                "attestation_id": attestation.attestation_id,
                "substrate": attestation.substrate,
                "status": attestation.status,
            },
            actor="SubstrateBroker",
            category="attestation",
            layer="L0",
            signature_roles=["guardian"],
            substrate=attestation.substrate,
        )
        transfer = self.substrate.transfer(
            allocation_id=allocation.allocation_id,
            state={
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
                "checkpoint": "reference-connectome-v1",
            },
            destination_substrate="classical_silicon.redundant",
            continuity_mode="warm-standby",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.migrated",
            payload={
                "allocation_id": allocation.allocation_id,
                "transfer_id": transfer.transfer_id,
                "destination_substrate": transfer.destination_substrate,
                "continuity_mode": transfer.continuity_mode,
            },
            actor="SubstrateBroker",
            category="substrate-migrate",
            layer="L0",
            signature_roles=["self", "council", "guardian"],
            substrate=transfer.destination_substrate,
        )
        release = self.substrate.release(
            allocation_id=allocation.allocation_id,
            reason="migration-complete",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.released",
            payload=release,
            actor="SubstrateBroker",
            category="substrate-release",
            layer="L0",
            signature_roles=["guardian"],
            substrate="classical_silicon.redundant",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "substrate": {
                "allocation": asdict(allocation),
                "energy_floor": asdict(energy_floor),
                "attestation": asdict(attestation),
                "transfer": asdict(transfer),
                "release": release,
                "snapshot": self.substrate.snapshot(),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_connectome_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://connectome-demo/v1",
            metadata={"display_name": "Connectome Sandbox"},
        )
        connectome = self.connectome.build_reference_snapshot(identity.identity_id)
        validation = self.connectome.validate(connectome)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.connectome.snapshotted",
            payload={
                "snapshot_id": connectome["snapshot_id"],
                "node_count": validation["node_count"],
                "edge_count": validation["edge_count"],
            },
            actor="ConnectomeModel",
            category="connectome-snapshot",
            layer="L2",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "connectome": connectome,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

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
            category="cognitive-failover",
            layer="L3",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "reasoning": reasoning,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_continuity_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://continuity-demo/v1",
            metadata={"display_name": "Continuity Sandbox"},
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.created",
            payload={"display_name": "Continuity Sandbox", "lineage_id": identity.lineage_id},
            actor="IdentityRegistry",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.qualia.checkpointed",
            payload={
                "slice_id": "qualia-slice-0001",
                "valence": 0.22,
                "arousal": 0.31,
                "coherence": 0.91,
            },
            actor="QualiaBuffer",
            category="qualia-checkpoint",
            layer="L2",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.patch.approved",
            payload={
                "proposal_id": "proposal-continuity-0001",
                "target_component": "ContinuityLedger",
                "change_scope": "signature policy hardening",
            },
            actor="Council",
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }
