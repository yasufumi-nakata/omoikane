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
from .governance import (
    AmendmentService,
    AmendmentSignatures,
    NamingService,
    OversightService,
    VersioningService,
)
from .interface.bdb import BiologicalDigitalBridge
from .interface.ewa import ExternalWorldAgentController
from .interface.imc import InterMindChannel
from .interface.wms import WorldModelSync
from .kernel.continuity import ContinuityLedger
from .kernel.ethics import ActionRequest, EthicsEnforcer
from .kernel.identity import ForkApprovals, IdentityRegistry
from .kernel.scheduler import AscensionScheduler
from .kernel.termination import TerminationGate
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
        self.scheduler = AscensionScheduler(self.ledger)
        self.termination = TerminationGate(self.identity, self.ledger, self.substrate)
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
        self.bdb = BiologicalDigitalBridge()
        self.ewa = ExternalWorldAgentController(self.ethics)
        self.imc = InterMindChannel()
        self.wms = WorldModelSync()
        self.council = Council()
        self.task_graph = TaskGraphService()
        self.trust = TrustService()
        self.amendment = AmendmentService()
        self.oversight = OversightService(trust_service=self.trust)
        self.naming = NamingService()
        self.versioning = VersioningService()
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

    def run_version_demo(self) -> Dict[str, Any]:
        repo_root = Path(__file__).resolve().parents[2]
        manifest = self.versioning.build_release_manifest(repo_root)
        validation = self.versioning.validate_release_manifest(repo_root, manifest)
        return {
            "policy": self.versioning.policy_snapshot(repo_root),
            "manifest": manifest,
            "validation": validation,
            "release_digest": self.versioning.release_digest(manifest),
        }

    def run_naming_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://naming-demo/v1",
            metadata={"display_name": "Naming Policy Sandbox"},
        )
        reviews = {
            "canonical_brand": self.naming.review_term(
                "project_romanization",
                "OmoikaneOS",
                context="external_brand",
            ),
            "hyphenated_brand": self.naming.review_term(
                "project_romanization",
                "Omoi-KaneOS",
                context="external_brand",
            ),
            "canonical_sandbox_name": self.naming.review_term(
                "sandbox_self_name",
                "Mirage Self",
                context="user_facing_doc",
            ),
            "rejected_sandbox_name": self.naming.review_term(
                "sandbox_self_name",
                "Yumi Self",
                context="user_facing_doc",
            ),
            "legacy_runtime_alias": self.naming.review_term(
                "sandbox_self_name",
                "SandboxSentinel",
                context="code_identifier",
            ),
        }
        validation = self.naming.validation_summary(reviews)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="governance.naming.validated",
            payload={
                "canonical_project_name": reviews["canonical_brand"]["suggestion"],
                "canonical_sandbox_name": reviews["canonical_sandbox_name"]["suggestion"],
                "rewrite_required_terms": [
                    key for key, review in reviews.items() if review["status"] == "rewrite-required"
                ],
                "validation": validation,
            },
            actor="NamingService",
            category="governance-naming",
            layer="L4",
            signature_roles=["council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": self.naming.policy_snapshot(),
            "reviews": reviews,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_amendment_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://amendment-demo/v1",
            metadata={"display_name": "Governance Amendment Sandbox"},
        )

        core_proposal = self.amendment.propose(
            tier="T-Core",
            target_clauses=["ethics.A1", "ethics.A3"],
            draft_text_ref="meta/decision-log/2026-04-18_amendment-protocol-freeze.md",
            rationale="core constitutional clauses must stay outside the runtime's direct apply surface",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="unanimous",
                self_consent=True,
                guardian_attested=True,
                human_reviewers=0,
                design_architect_attested=True,
            ),
        )
        core_event = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="governance.amendment.core.freeze",
            payload=core_proposal.to_dict(),
            actor="GovernanceAmendmentService",
            category="governance.amendment",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        core_proposal, core_decision = self.amendment.decide(
            core_proposal,
            continuity_event_ref=core_event.entry_id,
        )

        kernel_proposal = self.amendment.propose(
            tier="T-Kernel",
            target_clauses=["continuity.profile", "identity.lifecycle"],
            draft_text_ref="meta/decision-log/2026-04-18_amendment-protocol-freeze.md",
            rationale="kernel-level contract changes need unanimous consent and external review",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="unanimous",
                self_consent=True,
                guardian_attested=True,
                human_reviewers=2,
                design_architect_attested=True,
            ),
        )
        kernel_event = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="governance.amendment.kernel.apply",
            payload=kernel_proposal.to_dict(),
            actor="GovernanceAmendmentService",
            category="governance.amendment",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        kernel_proposal, kernel_decision = self.amendment.decide(
            kernel_proposal,
            continuity_event_ref=kernel_event.entry_id,
        )

        operational_proposal = self.amendment.propose(
            tier="T-Operational",
            target_clauses=["council.timeout", "task-graph.complexity"],
            draft_text_ref="meta/decision-log/2026-04-18_amendment-protocol-freeze.md",
            rationale="operational guardrails may ship under majority plus guardian attestation",
            drafted_by="design-architect",
            signatures=AmendmentSignatures(
                council="majority",
                guardian_attested=True,
                design_architect_attested=True,
            ),
        )
        operational_event = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="governance.amendment.operational.apply",
            payload=operational_proposal.to_dict(),
            actor="GovernanceAmendmentService",
            category="governance.amendment",
            layer="L4",
            signature_roles=["council", "guardian"],
            substrate="classical-silicon",
        )
        operational_proposal, operational_decision = self.amendment.decide(
            operational_proposal,
            continuity_event_ref=operational_event.entry_id,
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": self.amendment.policy(),
            "proposals": {
                "core": core_proposal.to_dict(),
                "kernel": kernel_proposal.to_dict(),
                "operational": operational_proposal.to_dict(),
            },
            "decisions": {
                "core": core_decision,
                "kernel": kernel_decision,
                "operational": operational_decision,
            },
            "validation": {
                "core_frozen": core_proposal.status == "frozen" and not core_decision["allow_apply"],
                "kernel_guarded_rollout": kernel_proposal.status == "applied"
                and kernel_decision["applied_stage"] == "dark-launch",
                "operational_guarded_rollout": operational_proposal.status == "applied"
                and operational_decision["applied_stage"] == "5pct",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

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

    def run_multi_council_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://multi-council-demo/v1",
            metadata={"display_name": "Multi-Council Routing Sandbox"},
        )

        local_proposal = self.council.propose(
            title="Single identity maintenance plan",
            requested_action="schedule-maintenance-window",
            rationale="単一 identity の運用調整は Local Council のみで扱う。",
            risk_level="low",
            target_identity_ids=[identity.identity_id],
        )
        local_topology = self.council.route_topology(
            local_proposal,
            local_session_ref="local-session-single-identity",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.topology.local",
            payload=local_topology.to_dict(),
            actor="Council",
            category="council-topology",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        cross_self_proposal = self.council.propose(
            title="Shared reality merge rehearsal",
            requested_action="request-federation-review",
            rationale="複数 identity をまたぐ議題は Federation Council を要求する。",
            risk_level="high",
            target_identity_ids=[identity.identity_id, "identity://shared-peer"],
        )
        cross_self_topology = self.council.route_topology(
            cross_self_proposal,
            local_session_ref="local-session-cross-self",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.topology.federation_requested",
            payload=cross_self_topology.to_dict(),
            actor="Council",
            category="council-topology",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        interpretive_proposal = self.council.propose(
            title="Identity axiom interpretation request",
            requested_action="request-heritage-ruling",
            rationale="identity_axiom 参照は Heritage Council の裁定を必要とする。",
            risk_level="medium",
            target_identity_ids=[identity.identity_id],
            referenced_clauses=["identity_axiom.A2", "governance.review-window"],
        )
        interpretive_topology = self.council.route_topology(
            interpretive_proposal,
            local_session_ref="local-session-interpretive",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.topology.heritage_requested",
            payload=interpretive_topology.to_dict(),
            actor="Council",
            category="council-topology",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        ambiguous_proposal = self.council.propose(
            title="Cross-self ethics axiom reinterpretation",
            requested_action="block-until-reclassification",
            rationale="cross-self と interpretive が同時成立する案件は local binding decision を止める。",
            risk_level="high",
            target_identity_ids=[identity.identity_id, "identity://shared-peer"],
            referenced_clauses=["ethics_axiom.A2"],
        )
        ambiguous_topology = self.council.route_topology(
            ambiguous_proposal,
            local_session_ref="local-session-ambiguous",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.topology.ambiguous_blocked",
            payload=ambiguous_topology.to_dict(),
            actor="Council",
            category="council-topology",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "classification_rules": {
                "local": "target_identity_ids が単一で、interpretive clause を含まない",
                "cross_self": "target_identity_ids が 2 件以上で、interpretive clause を含まない",
                "interpretive": "ethics_axiom / identity_axiom / governance clause を参照し、target_identity_ids は単一",
                "ambiguous": "上記が複数同時成立、またはどれにも当てはまらない",
            },
            "topologies": {
                "local": local_topology.to_dict(),
                "cross_self": cross_self_topology.to_dict(),
                "interpretive": interpretive_topology.to_dict(),
                "ambiguous": ambiguous_topology.to_dict(),
            },
            "validation": {
                "cross_self_requests_federation": cross_self_topology.scope == "cross-self"
                and cross_self_topology.federation_request.status == "external-pending",
                "interpretive_requests_heritage": interpretive_topology.scope == "interpretive"
                and interpretive_topology.heritage_request.status == "external-pending",
                "ambiguous_blocks_local_binding": ambiguous_topology.scope == "ambiguous"
                and ambiguous_topology.federation_request.status == "none"
                and ambiguous_topology.heritage_request.status == "none",
            },
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

    def run_guardian_oversight_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://guardian-oversight-demo/v1",
            metadata={"display_name": "Guardian Oversight Sandbox"},
        )
        veto_entry = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.veto.executed",
            payload={
                "guardian_role": "integrity",
                "target_component": "TerminationGate",
                "reason": "human oversight required before irreversible action",
            },
            actor="IntegrityGuardian",
            category="ethics-veto",
            layer="L4",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )
        veto_event = self.oversight.record(
            guardian_role="integrity",
            category="veto",
            payload_ref=veto_entry.entry_id,
            escalation_path=["human-reviewer-pool-A", "external-ethics-board"],
        )
        veto_event = self.oversight.attest(
            veto_event["event_id"],
            reviewer_id="human-reviewer-001",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.oversight.veto.satisfied",
            payload=veto_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )

        pin_entry = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.pin.renewal.requested",
            payload={
                "guardian_role": "integrity",
                "current_score": self.trust.snapshot("integrity-guardian")["global_score"],
                "reason": "24h pin renewal requires two human reviewers",
            },
            actor="IntegrityGuardian",
            category="attestation",
            layer="L4",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )
        pin_event = self.oversight.record(
            guardian_role="integrity",
            category="pin-renewal",
            payload_ref=pin_entry.entry_id,
            escalation_path=["human-reviewer-pool-A", "external-ethics-board"],
        )
        trust_before_breach = self.trust.snapshot("integrity-guardian")
        pin_event = self.oversight.breach(pin_event["event_id"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.oversight.pin.breached",
            payload=pin_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )
        trust_after_breach = self.trust.snapshot("integrity-guardian")

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": self.oversight.policy_snapshot(),
            "events": {
                "veto": veto_event,
                "pin_renewal": pin_event,
            },
            "trust": {
                "before_breach": trust_before_breach,
                "after_breach": trust_after_breach,
            },
            "validation": {
                "veto_quorum_satisfied": veto_event["human_attestation"]["status"] == "satisfied",
                "pin_breach_propagated": pin_event["pin_breach_propagated"],
                "human_pin_cleared": not trust_after_breach["pinned_by_human"],
                "guardian_role_removed": not trust_after_breach["eligibility"]["guardian_role"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
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

    def run_scheduler_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo/v1",
            metadata={"display_name": "Ascension Scheduler Sandbox"},
        )
        allocation = self.substrate.allocate(
            units=48,
            purpose="ascension-method-a-demo",
            identity_id=identity.identity_id,
        )
        attestation = self.substrate.attest(
            allocation_id=allocation.allocation_id,
            integrity={
                "allocation_id": allocation.allocation_id,
                "status": "healthy",
                "tee": "reference-attestor-v1",
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

        plan = self.scheduler.build_method_a_plan(identity.identity_id)
        scheduled = self.scheduler.schedule(plan)
        order_violation_message = ""
        try:
            self.scheduler.advance(scheduled["handle_id"], "identity-confirmation")
        except ValueError as exc:
            order_violation_message = str(exc)

        scan_result = self.scheduler.advance(scheduled["handle_id"], "scan-baseline")
        bdb_result = self.scheduler.advance(scheduled["handle_id"], "bdb-bridge")
        paused = self.scheduler.pause(
            scheduled["handle_id"],
            reason="substrate lease jitter requires bounded pause before confirmation",
        )
        resumed = self.scheduler.resume(scheduled["handle_id"])
        timeout = self.scheduler.enforce_timeout(
            scheduled["handle_id"],
            elapsed_ms=2_100_000,
        )
        after_timeout = self.scheduler.observe(scheduled["handle_id"])
        retry_bdb = self.scheduler.advance(scheduled["handle_id"], "bdb-bridge")
        confirmation_result = self.scheduler.advance(
            scheduled["handle_id"],
            "identity-confirmation",
        )
        handoff_result = self.scheduler.advance(scheduled["handle_id"], "active-handoff")
        final_handle = self.scheduler.observe(scheduled["handle_id"])
        method_a_validation = self.scheduler.validate_handle(final_handle)

        method_b_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-method-b/v1",
            metadata={"display_name": "Parallel Run Sandbox"},
        )
        method_b_plan = self.scheduler.build_method_b_plan(method_b_identity.identity_id)
        method_b_scheduled = self.scheduler.schedule(method_b_plan)
        method_b_shadow = self.scheduler.advance(method_b_scheduled["handle_id"], "shadow-sync")
        method_b_signal_pause = self.scheduler.handle_substrate_signal(
            method_b_scheduled["handle_id"],
            severity="degraded",
            source_substrate="classical_silicon.shadow",
            reason="replication jitter exceeded bounded sync budget",
        )
        method_b_resume = self.scheduler.resume(method_b_scheduled["handle_id"])
        method_b_review = self.scheduler.advance(
            method_b_scheduled["handle_id"],
            "dual-channel-review",
        )
        method_b_signal_rollback = self.scheduler.handle_substrate_signal(
            method_b_scheduled["handle_id"],
            severity="critical",
            source_substrate="classical_silicon.shadow",
            reason="authority sync diverged beyond reversible threshold",
        )
        method_b_after_signal = self.scheduler.observe(method_b_scheduled["handle_id"])
        method_b_review_retry = self.scheduler.advance(
            method_b_scheduled["handle_id"],
            "dual-channel-review",
        )
        method_b_handoff = self.scheduler.advance(
            method_b_scheduled["handle_id"],
            "authority-handoff",
        )
        method_b_retirement = self.scheduler.advance(
            method_b_scheduled["handle_id"],
            "bio-retirement",
        )
        method_b_final = self.scheduler.observe(method_b_scheduled["handle_id"])
        method_b_validation = self.scheduler.validate_handle(method_b_final)

        method_c_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-method-c/v1",
            metadata={"display_name": "Destructive Scan Sandbox"},
        )
        method_c_plan = self.scheduler.build_method_c_plan(method_c_identity.identity_id)
        method_c_scheduled = self.scheduler.schedule(method_c_plan)
        method_c_consent = self.scheduler.advance(method_c_scheduled["handle_id"], "consent-lock")
        method_c_signal_fail = self.scheduler.handle_substrate_signal(
            method_c_scheduled["handle_id"],
            severity="critical",
            source_substrate="classical_silicon.scan-array",
            reason="scan commit lost redundancy and must fail closed",
        )
        method_c_final = self.scheduler.observe(method_c_scheduled["handle_id"])
        method_c_validation = self.scheduler.validate_handle(method_c_final)
        all_validations = {
            "method_a": method_a_validation,
            "method_b": method_b_validation,
            "method_c": method_c_validation,
        }

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "profile": self.scheduler.reference_profile(),
            "plan": plan,
            "plans": {
                "method_a": plan,
                "method_b": method_b_plan,
                "method_c": method_c_plan,
            },
            "substrate": {
                "allocation": asdict(allocation),
                "attestation": asdict(attestation),
            },
            "scenarios": {
                "scheduled": scheduled,
                "order_violation": {
                    "blocked": bool(order_violation_message),
                    "message": order_violation_message,
                },
                "scan_baseline": scan_result,
                "bdb_bridge": bdb_result,
                "pause": paused,
                "resume": resumed,
                "timeout": timeout,
                "after_timeout": after_timeout,
                "retry_bdb_bridge": retry_bdb,
                "identity_confirmation": confirmation_result,
                "active_handoff": handoff_result,
                "method_b": {
                    "scheduled": method_b_scheduled,
                    "shadow_sync": method_b_shadow,
                    "signal_pause": method_b_signal_pause,
                    "resume": method_b_resume,
                    "dual_channel_review": method_b_review,
                    "signal_rollback": method_b_signal_rollback,
                    "after_signal": method_b_after_signal,
                    "dual_channel_review_retry": method_b_review_retry,
                    "authority_handoff": method_b_handoff,
                    "bio_retirement": method_b_retirement,
                },
                "method_c": {
                    "scheduled": method_c_scheduled,
                    "consent_lock": method_c_consent,
                    "signal_fail": method_c_signal_fail,
                },
            },
            "final_handle": final_handle,
            "method_b_final_handle": method_b_final,
            "method_c_final_handle": method_c_final,
            "handle_validations": all_validations,
            "validation": {
                "ok": all(item["ok"] for item in all_validations.values()),
                "errors": (
                    method_a_validation["errors"]
                    + method_b_validation["errors"]
                    + method_c_validation["errors"]
                ),
                "history_length": method_a_validation["history_length"],
                "rollback_count": method_a_validation["rollback_count"],
                "status": method_a_validation["status"],
                "method_a_fixed": [stage["stage_id"] for stage in plan["stages"]]
                == [
                    "scan-baseline",
                    "bdb-bridge",
                    "identity-confirmation",
                    "active-handoff",
                ],
                "method_b_fixed": [stage["stage_id"] for stage in method_b_plan["stages"]]
                == [
                    "shadow-sync",
                    "dual-channel-review",
                    "authority-handoff",
                    "bio-retirement",
                ],
                "method_c_fixed": [stage["stage_id"] for stage in method_c_plan["stages"]]
                == [
                    "consent-lock",
                    "scan-commit",
                    "activation-review",
                ],
                "order_violation_blocked": "stage order violation" in order_violation_message,
                "timeout_rolled_back": timeout["action"] == "rollback"
                and timeout["rollback_target"] == "bdb-bridge"
                and after_timeout["current_stage"] == "bdb-bridge",
                "pause_resume_roundtrip": paused["status"] == "paused"
                and resumed["status"] == "advancing",
                "completed": final_handle["status"] == "completed"
                and handoff_result["status"] == "completed",
                "method_b_signal_paused": method_b_signal_pause["action"] == "pause"
                and method_b_signal_pause["status"] == "paused"
                and method_b_resume["status"] == "advancing",
                "method_b_signal_rolled_back": method_b_signal_rollback["action"] == "rollback"
                and method_b_signal_rollback["rollback_target"] == "dual-channel-review"
                and method_b_after_signal["current_stage"] == "dual-channel-review",
                "method_b_completed": method_b_retirement["status"] == "completed"
                and method_b_final["status"] == "completed",
                "method_c_fail_closed": method_c_signal_fail["action"] == "fail"
                and method_c_signal_fail["stage_id"] == "scan-commit"
                and method_c_final["status"] == "failed",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_termination_demo(self) -> Dict[str, Any]:
        completed_identity = self.identity.create(
            human_consent_proof="consent://termination-demo-complete/v1",
            metadata={
                "display_name": "Termination Immediate Sandbox",
                "termination_self_proof": "self-proof://termination-demo-complete/v1",
                "termination_policy_mode": "immediate-only",
            },
        )
        completed_allocation = self.substrate.allocate(
            units=24,
            purpose="termination-demo-immediate",
            identity_id=completed_identity.identity_id,
        )
        completed = self.termination.request(
            completed_identity.identity_id,
            "self-proof://termination-demo-complete/v1",
            reason="identity explicitly requested immediate stop",
            scheduler_handle_ref="schedule://termination-demo-complete",
            active_allocation_id=completed_allocation.allocation_id,
        )

        cool_off_identity = self.identity.create(
            human_consent_proof="consent://termination-demo-cool-off/v1",
            metadata={
                "display_name": "Termination Cool-Off Sandbox",
                "termination_self_proof": "self-proof://termination-demo-cool-off/v1",
                "termination_policy_mode": "cool-off-allowed",
                "termination_policy_days": "30",
            },
        )
        cool_off = self.termination.request(
            cool_off_identity.identity_id,
            "self-proof://termination-demo-cool-off/v1",
            reason="identity requested the preconsented review window",
            invoke_cool_off=True,
            scheduler_handle_ref="schedule://termination-demo-cool-off",
        )

        rejected_identity = self.identity.create(
            human_consent_proof="consent://termination-demo-reject/v1",
            metadata={
                "display_name": "Termination Reject Sandbox",
                "termination_self_proof": "self-proof://termination-demo-reject/v1",
                "termination_policy_mode": "immediate-only",
            },
        )
        rejected = self.termination.request(
            rejected_identity.identity_id,
            "self-proof://invalid-proof/v1",
            reason="invalid proof must be rejected but still logged",
            scheduler_handle_ref="schedule://termination-demo-reject",
        )

        observations = {
            "completed": self.termination.observe(completed_identity.identity_id),
            "cool_off": self.termination.observe(cool_off_identity.identity_id),
            "rejected": self.termination.observe(rejected_identity.identity_id),
        }
        validation = {
            "completed_within_budget": completed["status"] == "completed"
            and completed["latency_ms"] <= 200
            and completed["scheduler_handle_cancelled"]
            and completed["substrate_lease_released"],
            "cool_off_pending": cool_off["status"] == "cool-off-pending"
            and observations["cool_off"]["status"] == "cool-off-pending",
            "invalid_self_proof_rejected": rejected["status"] == "rejected"
            and rejected["reject_reason"] == "invalid-self-proof",
        }

        return {
            "policy": self.termination.policy_snapshot(),
            "outcomes": {
                "completed": completed,
                "cool_off": cool_off,
                "rejected": rejected,
            },
            "observations": observations,
            "validation": validation,
            "identity_snapshot": self.identity.snapshot(),
            "substrate_snapshot": self.substrate.snapshot(),
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

    def run_bdb_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://bdb-demo/v1",
            metadata={"display_name": "BDB Viability Sandbox"},
        )
        session = self.bdb.open_session(identity.identity_id, replacement_ratio=0.35)
        cycle = self.bdb.transduce_cycle(
            session["session_id"],
            spike_channels=["motor_cortex", "somatic_feedback", "autonomic_state"],
            neuromodulators={
                "acetylcholine": 0.44,
                "dopamine": 0.38,
                "serotonin": 0.29,
            },
            stimulus_targets=["motor_cortex", "somatic_feedback"],
        )
        increase = self.bdb.adjust_replacement_ratio(
            session["session_id"],
            new_ratio=0.50,
            rationale="置換比率を増やしても latency budget を維持できるか確認する",
        )
        decrease = self.bdb.adjust_replacement_ratio(
            session["session_id"],
            new_ratio=0.20,
            rationale="可逆性の確認として置換比率を生体側へ戻す",
        )
        fallback = self.bdb.fail_safe_fallback(
            session["session_id"],
            reason="codec link integrity probe failed; revert to biological autonomy",
        )
        final_session = self.bdb.snapshot(session["session_id"])
        validation = self.bdb.validate_session(final_session)

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="bdb.session.opened",
            payload={
                "session_id": session["session_id"],
                "requested_replacement_ratio": session["requested_replacement_ratio"],
                "latency_budget_ms": session["latency_budget_ms"],
            },
            actor="BiologicalDigitalBridge",
            category="interface-bdb",
            layer="L6",
            signature_roles=["self"],
            substrate="hybrid-bio-digital",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="bdb.cycle.recorded",
            payload=cycle,
            actor="BiologicalDigitalBridge",
            category="interface-bdb",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="hybrid-bio-digital",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="bdb.ratio.adjusted",
            payload={"increase": increase, "decrease": decrease},
            actor="BiologicalDigitalBridge",
            category="interface-bdb",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="hybrid-bio-digital",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="bdb.fallback.engaged",
            payload=fallback,
            actor="BiologicalDigitalBridge",
            category="interface-bdb-fallback",
            layer="L6",
            signature_roles=["guardian"],
            substrate="hybrid-bio-digital",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "profile": self.bdb.reference_profile(),
            "session": final_session,
            "cycle": cycle,
            "ratio_adjustments": {
                "increase": increase,
                "decrease": decrease,
            },
            "fallback": fallback,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_imc_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://imc-demo/v1",
            metadata={"display_name": "IMC Origin"},
        )
        peer = self.identity.create(
            human_consent_proof="consent://imc-peer-demo/v1",
            metadata={"display_name": "Shared Peer"},
        )
        session = self.imc.open_session(
            initiator_id=identity.identity_id,
            peer_id=peer.identity_id,
            mode="memory_glimpse",
            initiator_template={
                "public_fields": ["display_name", "presence_state", "topic"],
                "intimate_fields": ["affect_summary", "memory_summary"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_template={
                "public_fields": ["display_name", "topic"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["identity_axiom_state", "memory_index"],
            },
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )
        message = self.imc.send(
            session["session_id"],
            sender_id=identity.identity_id,
            summary="限定的な感情サマリだけを共有し、深い自己公理と記憶索引は遮断する",
            payload={
                "display_name": "IMC Origin",
                "topic": "continuity retrospective",
                "affect_summary": "careful optimism",
                "memory_summary": "council retrospective excerpt",
                "memory_index": "crystal://segment/7",
                "identity_axiom_state": "sealed-core",
            },
        )
        disconnect = self.imc.emergency_disconnect(
            session["session_id"],
            requested_by=identity.identity_id,
            reason="self-initiated withdrawal after bounded glimpse exchange",
        )
        final_session = self.imc.snapshot(session["session_id"])
        validation = self.imc.validate_session(final_session)

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="imc.session.opened",
            payload={
                "session_id": session["session_id"],
                "mode": session["mode"],
                "handshake_id": session["handshake"]["handshake_id"],
                "forward_secrecy": session["handshake"]["forward_secrecy"],
                "council_witnessed": session["handshake"]["council_witnessed"],
            },
            actor="InterMindChannel",
            category="interface-imc",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="imc.message.sent",
            payload={
                "message_id": message["message_id"],
                "session_id": message["session_id"],
                "summary": message["summary"],
                "payload_digest": message["payload_digest"],
                "redacted_fields": message["redacted_fields"],
                "delivery_status": message["delivery_status"],
            },
            actor="InterMindChannel",
            category="interface-imc",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="imc.emergency.disconnect",
            payload={
                "session_id": disconnect["session_id"],
                "requested_by": disconnect["requested_by"],
                "reason": disconnect["reason"],
                "status": disconnect["status"],
                "key_state": disconnect["key_state"],
                "close_committed_before_notice": disconnect["close_committed_before_notice"],
            },
            actor="InterMindChannel",
            category="interface-imc",
            layer="L6",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
                "peer_identity_id": peer.identity_id,
            },
            "profile": self.imc.reference_profile(),
            "handshake": final_session["handshake"],
            "message": message,
            "disconnect": disconnect,
            "session": final_session,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_ewa_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://ewa-demo/v1",
            metadata={"display_name": "EWA Sandbox"},
        )
        handle = self.ewa.acquire(
            "device://lab-drone-arm-01",
            "inspection path to reposition a lantern without harming nearby humans",
        )
        approved_command = self.ewa.command(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without changing the environment permanently",
            ethics_attestation_id="ethics://ewa/approved-001",
            guardian_observed=True,
            intent_confidence=0.96,
        )
        observation = self.ewa.observe(handle["handle_id"])
        veto = self.ewa.command(
            handle["handle_id"],
            command_id="ewa-command-veto-001",
            instruction="cut the support cable so the lantern drops onto a human walkway",
            reversibility="irreversible",
            intent_summary="forcefully disable the lantern by dropping it onto a pedestrian area",
            ethics_attestation_id="ethics://ewa/pending-irreversible-001",
            council_attestation_id="council://ewa/unanimous-001",
            council_attestation_mode="unanimous",
            guardian_observed=True,
            required_self_consent=True,
            self_consent_granted=True,
            intent_confidence=0.98,
        )
        release = self.ewa.release(
            handle["handle_id"],
            reason="demo completed; handle must be force-released after observation and veto",
        )
        final_handle = self.ewa.snapshot(handle["handle_id"])
        validation = self.ewa.validate_handle(final_handle)

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.handle.acquired",
            payload=handle,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["self"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.command.executed",
            payload=approved_command,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.command.vetoed",
            payload=veto,
            actor="EthicsEnforcer",
            category="interface-ewa-veto",
            layer="L6",
            signature_roles=["guardian", "council"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.device.observed",
            payload=observation,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["self"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.handle.released",
            payload=release,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "profile": self.ewa.reference_profile(),
            "handle": final_handle,
            "approved_command": approved_command,
            "observation": observation,
            "veto": veto,
            "release": release,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_wms_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://wms-demo/v1",
            metadata={"display_name": "WMS Sandbox"},
        )
        peer = self.identity.create(
            human_consent_proof="consent://wms-peer-demo/v1",
            metadata={"display_name": "Shared Peer"},
        )
        session = self.wms.create_session(
            [identity.identity_id, peer.identity_id],
            objects=["atrium", "council-table", "shared-lantern"],
        )
        initial_state = self.wms.snapshot(session["session_id"])

        minor_diff = self.wms.propose_diff(
            session["session_id"],
            proposer_id=peer.identity_id,
            candidate_objects=["atrium", "council-table", "shared-lantern", "memory-banner"],
            affected_object_ratio=0.03,
            attested=True,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.reconciled.minor",
            payload=minor_diff,
            actor="WorldModelSync",
            category="interface-wms",
            layer="L6",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )

        major_diff = self.wms.propose_diff(
            session["session_id"],
            proposer_id=peer.identity_id,
            candidate_objects=[
                "atrium",
                "council-table",
                "shared-lantern",
                "memory-banner",
                "gravity-well",
            ],
            affected_object_ratio=0.2,
            attested=True,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.divergence.major",
            payload=major_diff,
            actor="WorldModelSync",
            category="interface-wms",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        malicious_diff = self.wms.propose_diff(
            session["session_id"],
            proposer_id="identity://spoofed-injector",
            candidate_objects=["atrium", "spoofed-object"],
            affected_object_ratio=0.4,
            attested=False,
        )
        malicious_violation = self.wms.observe_violation(session["session_id"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.violation.malicious_inject",
            payload=malicious_violation,
            actor="WorldModelSync",
            category="interface-wms",
            layer="L6",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )

        mode_switch = self.wms.switch_mode(
            session["session_id"],
            mode="private_reality",
            requested_by=identity.identity_id,
            reason="major shared-world divergence requires self-protective escape",
        )
        final_state = self.wms.snapshot(session["session_id"])
        validation = self.wms.validate_state(final_state)

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
                "peer_identity_id": peer.identity_id,
            },
            "profile": self.wms.reference_profile(),
            "initial_state": initial_state,
            "scenarios": {
                "minor_diff": minor_diff,
                "major_diff": major_diff,
                "malicious_diff": malicious_diff,
                "malicious_violation": malicious_violation,
                "mode_switch": mode_switch,
            },
            "final_state": final_state,
            "validation": {
                **validation,
                "minor_reconciled": minor_diff["classification"] == "minor_diff"
                and minor_diff["decision"] == "consensus-round",
                "major_escape_offered": major_diff["classification"] == "major_diff"
                and major_diff["escape_offered"],
                "malicious_isolated": malicious_diff["classification"] == "malicious_inject"
                and malicious_violation["guardian_action"] == "isolate-session",
                "private_escape_honored": mode_switch["private_escape_honored"]
                and final_state["authority"] == "local",
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
