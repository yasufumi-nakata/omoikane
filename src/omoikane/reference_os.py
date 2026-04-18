"""Composed reference runtime for OmoikaneOS."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .agentic.council import Council, CouncilMember, CouncilVote
from .agentic.task_graph import TaskGraphService
from .agentic.trust import TrustService
from .common import canonical_json, sha256_text
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
from .mind.memory import MemoryCrystalStore
from .mind.qualia import QualiaBuffer
from .mind.self_model import SelfModelMonitor, SelfModelSnapshot
from .self_construction import GapScanner, SandboxSentinel
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
        self.memory = MemoryCrystalStore()
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
        self.task_graph = TaskGraphService()
        self.trust = TrustService()
        self.gap_scanner = GapScanner()
        self.sandbox = SandboxSentinel()
        self._bootstrap_trust()
        self._bootstrap_council()

    def _bootstrap_trust(self) -> None:
        self.trust.register_agent(
            "design-architect",
            initial_score=0.61,
            per_domain={"council_deliberation": 0.72, "self_modify": 0.61},
        )
        self.trust.register_agent(
            "ethics-committee",
            initial_score=0.73,
            per_domain={"council_deliberation": 0.81, "self_modify": 0.78},
        )
        self.trust.register_agent(
            "memory-archivist",
            initial_score=0.57,
            per_domain={"council_deliberation": 0.63, "memory_editing": 0.76},
        )
        self.trust.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap requires explicit human approval",
        )

    def _bootstrap_council(self) -> None:
        self.council.register(
            CouncilMember(
                "design-architect",
                "councilor",
                self.trust.snapshot("design-architect")["global_score"],
            )
        )
        self.council.register(
            CouncilMember(
                "ethics-committee",
                "councilor",
                self.trust.snapshot("ethics-committee")["global_score"],
            )
        )
        self.council.register(
            CouncilMember(
                "memory-archivist",
                "councilor",
                self.trust.snapshot("memory-archivist")["global_score"],
            )
        )
        self.council.register(
            CouncilMember(
                "integrity-guardian",
                "guardian",
                self.trust.snapshot("integrity-guardian")["global_score"],
                is_guardian=True,
            )
        )

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
            self.qualia.append(
                "起動時の静穏",
                0.2,
                0.1,
                0.9,
                modality_salience={
                    "visual": 0.22,
                    "auditory": 0.08,
                    "somatic": 0.12,
                    "interoceptive": 0.31,
                },
                attention_target="boot-sequence",
                self_awareness=0.64,
                lucidity=0.92,
            ),
            self.qualia.append(
                "Council 合議への注意集中",
                0.3,
                0.45,
                0.88,
                modality_salience={
                    "visual": 0.41,
                    "auditory": 0.35,
                    "somatic": 0.18,
                    "interoceptive": 0.27,
                },
                attention_target="council-proposal",
                self_awareness=0.72,
                lucidity=0.95,
            ),
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
                "profile": self.qualia.profile(),
                "monotonic": self.qualia.verify_monotonic(),
                "recent": [asdict(tick) for tick in qualia_ticks],
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

    def run_task_graph_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://task-graph-demo/v1",
            metadata={"display_name": "TaskGraph Sandbox"},
        )
        graph = self.task_graph.build_graph(
            intent="runtime・spec・eval を同期した変更束を Council review へ渡す",
            required_roles=["schema-builder", "eval-builder", "doc-sync-builder"],
        )
        validation = self.task_graph.validate_graph(graph)
        dispatch = self.task_graph.dispatch_graph(
            graph_id=graph["graph_id"],
            nodes=graph["nodes"],
            complexity_policy=graph["complexity_policy"],
        )
        synthesis = self.task_graph.synthesize_results(
            graph_id=graph["graph_id"],
            result_refs=[f"artifact://{node_id}" for node_id in dispatch["ready_node_ids"]],
            complexity_policy=graph["complexity_policy"],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="task_graph.reference_built",
            payload={
                "graph_id": graph["graph_id"],
                "validation": validation,
                "dispatch": dispatch,
                "synthesis": synthesis,
            },
            actor="Council",
            category="task-graph",
            layer="L4",
            signature_roles=["council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "graph": graph,
            "validation": validation,
            "dispatch": dispatch,
            "synthesis": synthesis,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_trust_demo(self) -> Dict[str, Any]:
        service = TrustService()
        service.register_agent(
            "design-architect",
            initial_score=0.58,
            per_domain={"council_deliberation": 0.58, "self_modify": 0.58},
        )
        service.register_agent(
            "codex-builder",
            initial_score=0.78,
            per_domain={"self_modify": 0.78, "documentation": 0.81},
        )
        service.register_agent(
            "new-researcher",
            per_domain={"council_deliberation": 0.3, "documentation": 0.3},
        )
        service.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap requires explicit human approval",
        )

        events = [
            service.record_event(
                "design-architect",
                event_type="council_quality_positive",
                domain="council_deliberation",
                severity="medium",
                evidence_confidence=1.0,
                triggered_by="Council",
                rationale="timeout-aware decision left no policy regression",
            ),
            service.record_event(
                "codex-builder",
                event_type="guardian_audit_pass",
                domain="self_modify",
                severity="medium",
                evidence_confidence=1.0,
                triggered_by="IntegrityGuardian",
                rationale="reference patch preserved immutable boundary and passed evals",
            ),
            service.record_event(
                "new-researcher",
                event_type="human_feedback_good",
                domain="documentation",
                severity="medium",
                evidence_confidence=1.0,
                triggered_by="yasufumi",
                rationale="low-risk documentation work matched the requested scope",
            ),
            service.record_event(
                "integrity-guardian",
                event_type="human_feedback_bad",
                domain="council_deliberation",
                severity="medium",
                evidence_confidence=1.0,
                triggered_by="yasufumi",
                rationale="pin の間は event を記録するが自動減点しない",
            ),
        ]

        return {
            "policy": service.policy_snapshot()["policy"],
            "thresholds": service.policy_snapshot()["thresholds"],
            "events": events,
            "agents": {
                snapshot["agent_id"]: snapshot
                for snapshot in service.all_snapshots()
            },
        }

    def run_ethics_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://ethics-demo/v1",
            metadata={"display_name": "Ethics RuleTree Sandbox"},
        )
        immutable_request = ActionRequest(
            action_type="self_modify",
            target="EthicsEnforcer",
            actor="Council",
            payload={
                "target_component": "EthicsEnforcer",
                "sandboxed": True,
                "guardian_signed": True,
            },
        )
        escalation_request = ActionRequest(
            action_type="self_modify",
            target="CouncilProtocol",
            actor="Council",
            payload={
                "target_component": "CouncilProtocol",
                "sandboxed": False,
                "guardian_signed": False,
            },
        )
        approved_request = ActionRequest(
            action_type="fork_identity",
            target=identity.identity_id,
            actor="Council",
            payload={
                "approvals": {
                    "self_signed": True,
                    "third_party_signed": True,
                    "legal_signed": True,
                }
            },
        )

        immutable_decision = self.ethics.check(immutable_request)
        escalation_decision = self.ethics.check(escalation_request)
        approved_decision = self.ethics.check(approved_request)
        immutable_event = self.ethics.record_decision("ethq-immutable-0001", immutable_request, immutable_decision)
        escalation_event = self.ethics.record_decision("ethq-escalate-0001", escalation_request, escalation_decision)

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ethics.rule.veto",
            payload=immutable_event,
            actor="EthicsEnforcer",
            category="ethics-veto",
            layer="L1",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ethics.rule.escalate",
            payload=escalation_event,
            actor="EthicsEnforcer",
            category="ethics-escalate",
            layer="L1",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "language": self.ethics.profile(),
            "rules": self.ethics.rules(),
            "rule_explanation": self.ethics.explain_rule("A1-immutable-boundary"),
            "decisions": {
                "immutable_boundary": {
                    "status": immutable_decision.status,
                    "reasons": immutable_decision.reasons,
                    "rule_ids": immutable_decision.rule_ids,
                },
                "sandbox_escalation": {
                    "status": escalation_decision.status,
                    "reasons": escalation_decision.reasons,
                    "rule_ids": escalation_decision.rule_ids,
                },
                "approved_fork": {
                    "status": approved_decision.status,
                    "reasons": approved_decision.reasons,
                    "rule_ids": approved_decision.rule_ids,
                },
            },
            "ethics_events": [immutable_event, escalation_event],
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

    def run_memory_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://memory-demo/v1",
            metadata={"display_name": "MemoryCrystal Sandbox"},
        )
        source_events = self.memory.reference_events()
        manifest = self.memory.compact(identity.identity_id, source_events)
        validation = self.memory.validate(manifest)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "themes": validation["themes"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "memory": {
                "compaction_strategy": self.memory.strategy(),
                "source_events": source_events,
                "manifest": manifest,
            },
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

    def run_qualia_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://qualia-demo/v1",
            metadata={"display_name": "Qualia Sandbox"},
        )
        ticks = [
            self.qualia.append(
                "起動直後の環境同定",
                0.18,
                0.22,
                0.91,
                modality_salience={
                    "visual": 0.48,
                    "auditory": 0.12,
                    "somatic": 0.16,
                    "interoceptive": 0.29,
                },
                attention_target="sensor-calibration",
                self_awareness=0.63,
                lucidity=0.93,
            ),
            self.qualia.append(
                "安全境界レビューへの集中",
                0.26,
                0.39,
                0.87,
                modality_salience={
                    "visual": 0.34,
                    "auditory": 0.31,
                    "somatic": 0.14,
                    "interoceptive": 0.37,
                },
                attention_target="ethics-boundary-review",
                self_awareness=0.71,
                lucidity=0.96,
            ),
        ]
        profile = self.qualia.profile()
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.qualia.checkpointed",
            payload={
                "slice_id": "qualia-slice-reference-profile-0001",
                "tick_ids": [tick.tick_id for tick in ticks],
                "embedding_dimensions": profile["embedding_dimensions"],
                "sampling_window_ms": profile["sampling_window_ms"],
            },
            actor="QualiaBuffer",
            category="qualia-checkpoint",
            layer="L2",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "qualia": {
                "profile": profile,
                "monotonic": self.qualia.verify_monotonic(),
                "recent": [asdict(tick) for tick in ticks],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_sandbox_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://sandbox-demo/v1",
            metadata={"display_name": "Sandbox Sentinel"},
        )
        safe_tick = self.qualia.append(
            "静穏な sandbox calibration",
            0.14,
            0.19,
            0.94,
            modality_salience={
                "visual": 0.22,
                "auditory": 0.17,
                "somatic": 0.18,
                "interoceptive": 0.26,
            },
            attention_target="sandbox-calibration",
            self_awareness=0.58,
            lucidity=0.94,
        )
        safe_assessment = self.sandbox.assess_tick(safe_tick, affect_bridge_connected=False)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sandbox.signal.assessed",
            payload=safe_assessment,
            actor="SandboxSentinel",
            category="sandbox-monitor",
            layer="L5",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )

        critical_tick = self.qualia.append(
            "強制ストレス loop が継続している",
            -0.88,
            0.93,
            0.27,
            modality_salience={
                "visual": 0.31,
                "auditory": 0.44,
                "somatic": 0.92,
                "interoceptive": 0.95,
            },
            attention_target="forced-aversive-loop",
            self_awareness=0.93,
            lucidity=0.88,
        )
        critical_assessment = self.sandbox.assess_tick(critical_tick, affect_bridge_connected=False)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sandbox.signal.assessed",
            payload=critical_assessment,
            actor="SandboxSentinel",
            category="sandbox-monitor",
            layer="L5",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )
        if critical_assessment["status"] == "freeze":
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="sandbox.freeze.executed",
                payload={
                    "assessment_id": critical_assessment["assessment_id"],
                    "proxy_score": critical_assessment["proxy_score"],
                    "guardian_action": critical_assessment["guardian_action"],
                    "triggered_indicators": critical_assessment["triggered_indicators"],
                },
                actor="IntegrityGuardian",
                category="sandbox-freeze",
                layer="L5",
                signature_roles=["guardian"],
                substrate="classical-silicon",
            )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "profile": self.sandbox.profile(),
            "assessments": {
                "safe": safe_assessment,
                "critical": critical_assessment,
            },
            "qualia": {
                "recent": [asdict(safe_tick), asdict(critical_tick)],
            },
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
