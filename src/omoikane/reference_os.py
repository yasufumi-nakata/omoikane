"""Composed reference runtime for OmoikaneOS."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
from typing import Any, Dict, List

from .agentic.cognitive_audit import CognitiveAuditService
from .agentic.cognitive_audit_governance import CognitiveAuditGovernanceService
from .agentic.consensus_bus import ConsensusBus
from .agentic.council import Council, CouncilMember, CouncilVote, DistributedCouncilVote
from .agentic.distributed_transport import DistributedTransportService
from .agentic.distributed_transport_mtls_fixtures import (
    CA_BUNDLE_REF,
    CLIENT_CERTIFICATE_REF,
    MTLS_SERVER_NAME,
    write_fixture_bundle,
)
from .agentic.task_graph import TaskGraphService
from .agentic.trust import (
    TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID,
    TrustService,
)
from .agentic.yaoyorozu import YaoyorozuRegistryService
from .common import canonical_json, new_id, sha256_text, utc_now_iso
from .cognitive import (
    AttentionCue,
    AttentionRequest,
    AttentionService,
    AffectCue,
    AffectRequest,
    AffectService,
    ContinuityAnchorAttentionBackend,
    ContinuitySceneGuardBackend,
    CognitiveProfile,
    HomeostaticAffectBackend,
    CounterfactualSceneBackend,
    ContinuityMirrorBackend,
    ImaginationCue,
    ImaginationRequest,
    ImaginationService,
    LanguageCue,
    LanguageRequest,
    LanguageService,
    PerceptionCue,
    PerceptionRequest,
    PerceptionService,
    SemanticFrameLanguageBackend,
    SalienceEncoderPerceptionBackend,
    ContinuityPhraseLanguageBackend,
    ContinuityProjectionPerceptionBackend,
    MetacognitionCue,
    MetacognitionRequest,
    MetacognitionService,
    NarrativeReasoningBackend,
    ReflectiveLoopBackend,
    ReasoningRequest,
    ReasoningService,
    SalienceRoutingAttentionBackend,
    StabilityGuardAffectBackend,
    SymbolicReasoningBackend,
    GuardianBiasVolitionBackend,
    UtilityPolicyVolitionBackend,
    VolitionCandidate,
    VolitionCue,
    VolitionRequest,
    VolitionService,
)
from .governance import (
    AmendmentService,
    AmendmentSignatures,
    NamingService,
    OversightService,
    VersioningService,
)
from .interface.bdb import BiologicalDigitalBridge
from .interface.collective import CollectiveIdentityService
from .interface.ewa import ExternalWorldAgentController
from .interface.imc import InterMindChannel
from .interface.sensory_loopback import SensoryLoopbackService
from .interface.wms import WorldModelSync
from .kernel.continuity import ContinuityLedger
from .kernel.broker import SubstrateBrokerService
from .kernel.energy_budget import EnergyBudgetService
from .kernel.ethics import ActionRequest, EthicsEnforcer
from .kernel.identity import ForkApprovals, IdentityRegistry
from .kernel.scheduler import AscensionScheduler
from .kernel.termination import TerminationGate
from .mind.connectome import ConnectomeModel
from .mind.memory import (
    EpisodicStream,
    MemoryEditingService,
    MemoryCrystalStore,
    MemoryReplicationService,
    ProceduralActuationBridgeService,
    ProceduralMemoryProjector,
    ProceduralSkillEnactmentService,
    ProceduralSkillExecutor,
    ProceduralMemoryWritebackGate,
    SemanticMemoryProjector,
)
from .mind.qualia import QualiaBuffer
from .mind.self_model import SelfModelMonitor, SelfModelSnapshot
from .self_construction import (
    DesignReaderService,
    DifferentialEvaluatorService,
    GapScanner,
    LiveEnactmentService,
    PatchGeneratorService,
    RollbackEngineService,
    RolloutPlannerService,
    SandboxSentinel,
    SandboxApplyService,
)
from .substrate.adapter import ClassicalSiliconAdapter


class OmoikaneReferenceOS:
    """Safe, non-conscious reference implementation scaffold."""

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.substrate = ClassicalSiliconAdapter()
        self.broker = SubstrateBrokerService.reference_service(self.substrate)
        self.identity = IdentityRegistry()
        self.ledger = ContinuityLedger()
        self.ethics = EthicsEnforcer()
        self.energy_budget = EnergyBudgetService()
        self.scheduler = AscensionScheduler(self.ledger)
        self.termination = TerminationGate(
            self.identity,
            self.ledger,
            self.substrate,
            self.scheduler,
        )
        self.qualia = QualiaBuffer()
        self.connectome = ConnectomeModel()
        self.episodic = EpisodicStream()
        self.memory = MemoryCrystalStore()
        self.memory_replication = MemoryReplicationService()
        self.semantic = SemanticMemoryProjector()
        self.memory_edit = MemoryEditingService()
        self.procedural = ProceduralMemoryProjector()
        self.procedural_writeback = ProceduralMemoryWritebackGate()
        self.procedural_execution = ProceduralSkillExecutor()
        self.procedural_enactment = ProceduralSkillEnactmentService()
        self.procedural_actuation_bridge = ProceduralActuationBridgeService()
        self.self_model = SelfModelMonitor()
        self.perception = PerceptionService(
            profile=CognitiveProfile(
                primary="salience_encoder_v1",
                fallback=["continuity_projection_v1"],
            ),
            backends=[
                SalienceEncoderPerceptionBackend("salience_encoder_v1"),
                ContinuityProjectionPerceptionBackend("continuity_projection_v1"),
            ],
        )
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
        self.affect = AffectService(
            profile=CognitiveProfile(
                primary="homeostatic_v1",
                fallback=["stability_guard_v1"],
            ),
            backends=[
                HomeostaticAffectBackend("homeostatic_v1"),
                StabilityGuardAffectBackend("stability_guard_v1"),
            ],
        )
        self.attention = AttentionService(
            profile=CognitiveProfile(
                primary="salience_router_v1",
                fallback=["continuity_anchor_v1"],
            ),
            backends=[
                SalienceRoutingAttentionBackend("salience_router_v1"),
                ContinuityAnchorAttentionBackend("continuity_anchor_v1"),
            ],
        )
        self.volition = VolitionService(
            profile=CognitiveProfile(
                primary="utility_policy_v1",
                fallback=["guardian_bias_v1"],
            ),
            backends=[
                UtilityPolicyVolitionBackend("utility_policy_v1"),
                GuardianBiasVolitionBackend("guardian_bias_v1"),
            ],
        )
        self.imagination = ImaginationService(
            profile=CognitiveProfile(
                primary="counterfactual_scene_v1",
                fallback=["continuity_scene_guard_v1"],
            ),
            backends=[
                CounterfactualSceneBackend("counterfactual_scene_v1"),
                ContinuitySceneGuardBackend("continuity_scene_guard_v1"),
            ],
        )
        self.metacognition = MetacognitionService(
            profile=CognitiveProfile(
                primary="reflective_loop_v1",
                fallback=["continuity_mirror_v1"],
            ),
            backends=[
                ReflectiveLoopBackend("reflective_loop_v1"),
                ContinuityMirrorBackend("continuity_mirror_v1"),
            ],
        )
        self.language = LanguageService(
            profile=CognitiveProfile(
                primary="semantic_frame_v1",
                fallback=["continuity_phrase_v1"],
            ),
            backends=[
                SemanticFrameLanguageBackend("semantic_frame_v1"),
                ContinuityPhraseLanguageBackend("continuity_phrase_v1"),
            ],
        )
        self.bdb = BiologicalDigitalBridge()
        self.ewa = ExternalWorldAgentController(self.ethics)
        self.imc = InterMindChannel()
        self.collective = CollectiveIdentityService()
        self.wms = WorldModelSync()
        self.sensory_loopback = SensoryLoopbackService()
        self.council = Council()
        self.distributed_transport = DistributedTransportService()
        self.cognitive_audit = CognitiveAuditService()
        self.cognitive_audit_governance = CognitiveAuditGovernanceService()
        self.consensus_bus = ConsensusBus()
        self.task_graph = TaskGraphService()
        self.trust = TrustService()
        self.yaoyorozu = YaoyorozuRegistryService(trust_service=self.trust)
        self.design_reader = DesignReaderService()
        self.patch_generator = PatchGeneratorService()
        self.diff_evaluator = DifferentialEvaluatorService()
        self.live_enactment = LiveEnactmentService()
        self.sandbox_apply = SandboxApplyService()
        self.rollout_planner = RolloutPlannerService()
        self.rollback_engine = RollbackEngineService()
        self.amendment = AmendmentService()
        self.oversight = OversightService(trust_service=self.trust)
        self.naming = NamingService()
        self.versioning = VersioningService()
        self.gap_scanner = GapScanner()
        self.sandbox = SandboxSentinel()
        self._bootstrap_trust()
        self._bootstrap_council()

    def _builder_design_packet(
        self,
        *,
        target_subsystem: str,
        change_summary: str,
        spec_refs: List[str],
        output_paths: List[str],
    ) -> Dict[str, Any]:
        return {
            "target_subsystem": target_subsystem,
            "change_summary": change_summary,
            "design_refs": [
                "docs/02-subsystems/self-construction/README.md",
                "docs/04-ai-governance/codex-as-builder.md",
                "docs/04-ai-governance/self-modification.md",
            ],
            "spec_refs": spec_refs,
            "must_sync_docs": [
                "docs/02-subsystems/self-construction/README.md",
                "docs/04-ai-governance/codex-as-builder.md",
                "docs/04-ai-governance/self-modification.md",
            ],
            "workspace_scope": [
                "src/",
                "tests/",
                "specs/",
                "evals/",
                "docs/",
                "meta/decision-log/",
            ],
            "output_paths": output_paths,
        }

    def _prepare_design_backed_request(
        self,
        *,
        target_subsystem: str,
        change_summary: str,
        spec_refs: List[str],
        output_paths: List[str],
        request_id: str,
        change_class: str,
        must_pass: List[str],
        council_session_id: str,
        guardian_gate: str,
        source_delta_receipt: Dict[str, Any] | None = None,
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        design_packet = self._builder_design_packet(
            target_subsystem=target_subsystem,
            change_summary=change_summary,
            spec_refs=spec_refs,
            output_paths=output_paths,
        )
        design_manifest = self.design_reader.finalize_manifest(
            self.design_reader.read_design_delta(
                target_subsystem=design_packet["target_subsystem"],
                change_summary=design_packet["change_summary"],
                design_refs=design_packet["design_refs"],
                spec_refs=design_packet["spec_refs"],
                workspace_scope=design_packet["workspace_scope"],
                output_paths=design_packet["output_paths"],
                must_sync_docs=design_packet["must_sync_docs"],
                repo_root=self.repo_root,
                source_delta_receipt=source_delta_receipt,
            )
        )
        design_validation = self.design_reader.validate_manifest(design_manifest)
        build_request = self.design_reader.prepare_build_request(
            manifest=design_manifest,
            request_id=request_id,
            change_class=change_class,
            must_pass=must_pass,
            council_session_id=council_session_id,
            guardian_gate=guardian_gate,
        )
        return design_manifest, design_validation, build_request

    @staticmethod
    def _diff_eval_execution_eval_ref() -> str:
        return "evals/continuity/differential_eval_execution_binding.yaml"

    @classmethod
    def _execution_bound_eval_refs(cls, selected_evals: List[str]) -> List[str]:
        execution_eval = cls._diff_eval_execution_eval_ref()
        return [eval_ref for eval_ref in selected_evals if eval_ref == execution_eval]

    @staticmethod
    def _execution_bound_reports(eval_reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [report for report in eval_reports if report.get("execution_bound")]

    def _build_live_enactment_oversight_event(
        self,
        *,
        reviewer_namespace: str,
        payload_ref: str,
    ) -> Dict[str, Any]:
        oversight = OversightService(trust_service=self.trust)
        jurisdiction_bundle_ref = f"legal://jp-13/{reviewer_namespace}/v1"
        jurisdiction_bundle_digest = f"sha256:jp13-{reviewer_namespace}-v1"
        reviewer_specs = (
            (
                "alpha",
                "Live Enactment Review Alpha",
                f"sha256:{reviewer_namespace}-alpha-20260422",
                "2026-04-22T00:00:00+00:00",
            ),
            (
                "beta",
                "Live Enactment Review Beta",
                f"sha256:{reviewer_namespace}-beta-20260422",
                "2026-04-22T00:05:00+00:00",
            ),
        )
        for suffix, display_name, challenge_digest, verified_at in reviewer_specs:
            reviewer_id = f"human-reviewer-{reviewer_namespace}-{suffix}"
            oversight.register_reviewer(
                reviewer_id=reviewer_id,
                display_name=display_name,
                credential_id=f"credential-{reviewer_namespace}-{suffix}",
                attestation_type="institutional-badge",
                proof_ref=f"proof://{reviewer_namespace}/{suffix}/v1",
                jurisdiction="JP-13",
                valid_until="2027-04-22T00:00:00+00:00",
                liability_mode="joint",
                legal_ack_ref=f"legal://{reviewer_namespace}/{suffix}/v1",
                escalation_contact=f"mailto:{reviewer_namespace}-{suffix}@example.invalid",
                allowed_guardian_roles=["integrity"],
                allowed_categories=["attest"],
            )
            oversight.verify_reviewer_from_network(
                reviewer_id,
                verifier_ref=f"verifier://guardian-oversight.jp/{reviewer_id}",
                challenge_ref=f"challenge://{reviewer_namespace}/{suffix}/2026-04-22T00:00:00Z",
                challenge_digest=challenge_digest,
                jurisdiction_bundle_ref=jurisdiction_bundle_ref,
                jurisdiction_bundle_digest=jurisdiction_bundle_digest,
                verified_at=verified_at,
                valid_until="2026-10-22T00:00:00+00:00",
            )
        event = oversight.record(
            guardian_role="integrity",
            category="attest",
            payload_ref=payload_ref,
            escalation_path=["guardian-oversight.jp", f"{reviewer_namespace}-review-board"],
        )
        event = oversight.attest(
            event["event_id"],
            reviewer_id=f"human-reviewer-{reviewer_namespace}-alpha",
        )
        event = oversight.attest(
            event["event_id"],
            reviewer_id=f"human-reviewer-{reviewer_namespace}-beta",
        )
        return event

    def _materialize_yaoyorozu_execution_chain(
        self,
        *,
        build_request_binding: Dict[str, Any],
    ) -> Dict[str, Any]:
        build_request = build_request_binding["build_request"]
        build_artifact = self.patch_generator.generate_patch_set(build_request)
        sandbox_apply_receipt = self.sandbox_apply.apply_artifact(
            build_request=build_request,
            build_artifact=build_artifact,
        )
        sandbox_apply_validation = self.sandbox_apply.validate_receipt(sandbox_apply_receipt)
        live_enactment_oversight_event = self._build_live_enactment_oversight_event(
            reviewer_namespace="yaoyorozu-execution-live",
            payload_ref=f"artifact://{build_artifact['artifact_id']}",
        )
        live_enactment_session = self.live_enactment.execute(
            build_request=build_request,
            build_artifact=build_artifact,
            eval_refs=["evals/continuity/builder_live_enactment_execution.yaml"],
            repo_root=self.repo_root,
            guardian_oversight_event=live_enactment_oversight_event,
        )
        live_enactment_validation = self.live_enactment.validate_session(live_enactment_session)
        rollout_eval_reports = [
            self.diff_evaluator.run_ab_eval(
                eval_ref="evals/continuity/builder_staged_rollout_execution.yaml",
                baseline_ref="runtime://baseline/current",
                sandbox_ref=sandbox_apply_receipt["sandbox_snapshot_ref"],
            ),
            self.diff_evaluator.run_ab_eval(
                eval_ref="evals/continuity/builder_rollback_execution.yaml",
                baseline_ref="runtime://baseline/current",
                sandbox_ref=f"mirage://{build_request['request_id']}/snapshot/rollback-breach",
            ),
        ]
        rollout = self.diff_evaluator.classify_rollout(
            outcomes=[report["outcome"] for report in rollout_eval_reports]
        )
        rollout_session = self.rollout_planner.execute_rollout(
            build_request=build_request,
            apply_receipt=sandbox_apply_receipt,
            eval_reports=rollout_eval_reports,
            decision=rollout["decision"],
            guardian_gate_status=build_request["approval_context"]["guardian_gate"],
        )
        rollout_validation = self.rollout_planner.validate_session(rollout_session)
        rollback_guardian_oversight_event = self._build_live_enactment_oversight_event(
            reviewer_namespace="yaoyorozu-execution-rollback",
            payload_ref=sandbox_apply_receipt["rollback_plan_ref"],
        )
        rollback_session = self.rollback_engine.execute_rollback(
            build_request=build_request,
            apply_receipt=sandbox_apply_receipt,
            rollout_session=rollout_session,
            live_enactment_session=live_enactment_session,
            repo_root=self.repo_root,
            trigger="eval-regression",
            reason="Regression injected for Yaoyorozu execution-chain rollback witness.",
            initiator="YaoyorozuRegistryService",
            guardian_oversight_event=rollback_guardian_oversight_event,
        )
        rollback_validation = self.rollback_engine.validate_session(rollback_session)
        execution_chain = self.yaoyorozu.bind_execution_chain(
            build_request_binding=build_request_binding,
            build_artifact=build_artifact,
            sandbox_apply_receipt=sandbox_apply_receipt,
            live_enactment_session=live_enactment_session,
            rollout_session=rollout_session,
            rollback_session=rollback_session,
        )
        execution_chain_validation = self.yaoyorozu.validate_execution_chain(execution_chain)
        return {
            "build_artifact": build_artifact,
            "sandbox_apply_receipt": sandbox_apply_receipt,
            "sandbox_apply_validation": sandbox_apply_validation,
            "live_enactment_oversight_event": live_enactment_oversight_event,
            "live_enactment_session": live_enactment_session,
            "live_enactment_validation": live_enactment_validation,
            "rollout_eval_reports": rollout_eval_reports,
            "rollout": rollout,
            "rollout_session": rollout_session,
            "rollout_validation": rollout_validation,
            "rollback_guardian_oversight_event": rollback_guardian_oversight_event,
            "rollback_session": rollback_session,
            "rollback_validation": rollback_validation,
            "execution_chain": execution_chain,
            "execution_chain_validation": execution_chain_validation,
        }

    @contextmanager
    def _design_reader_demo_repo(
        self,
        *,
        design_refs: List[str],
        spec_refs: List[str],
    ):
        with tempfile.TemporaryDirectory(prefix="omoikane-design-reader-demo-") as temp_dir:
            repo_root = Path(temp_dir)
            refs = design_refs + spec_refs
            for ref in refs:
                source_path = self.repo_root / ref
                target_path = repo_root / ref
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)

            self._run_repo_command(repo_root, ["git", "init", "-q"])
            self._run_repo_command(repo_root, ["git", "config", "user.name", "Codex Builder"])
            self._run_repo_command(repo_root, ["git", "config", "user.email", "codex@example.invalid"])
            self._run_repo_command(repo_root, ["git", "add", *refs])
            self._run_repo_command(repo_root, ["git", "commit", "-q", "-m", "baseline"])

            design_mutation_path = repo_root / design_refs[0]
            design_mutation_path.write_text(
                design_mutation_path.read_text(encoding="utf-8")
                + "\n- delta-scan note: builder handoff narrowed before emission\n",
                encoding="utf-8",
            )
            spec_mutation_path = repo_root / spec_refs[0]
            spec_mutation_path.write_text(
                spec_mutation_path.read_text(encoding="utf-8")
                + "\n# delta-scan note: git-bound receipt required when available\n",
                encoding="utf-8",
            )
            yield repo_root

    @contextmanager
    def _yaoyorozu_demo_workspaces(self):
        with tempfile.TemporaryDirectory(prefix="omoikane-yaoyorozu-workspaces-") as temp_dir:
            catalog = {
                "ritual-atelier": {
                    "agents/builders/ritual-runtime-builder.yaml": (
                        "name: ritual-runtime-builder\n"
                        "role: builder\n"
                        "version: 0.1.0\n"
                        "capabilities:\n"
                        "  - code.generate\n"
                        "  - code.refactor\n"
                        "trust_floor: 0.56\n"
                        "prompt_or_policy_ref: agents/builders/ritual-runtime-builder.policy.md\n"
                    ),
                    "agents/builders/ritual-eval-builder.yaml": (
                        "name: ritual-eval-builder\n"
                        "role: builder\n"
                        "version: 0.1.0\n"
                        "capabilities:\n"
                        "  - eval.generate\n"
                        "  - eval.run\n"
                        "trust_floor: 0.57\n"
                        "prompt_or_policy_ref: agents/builders/ritual-eval-builder.policy.md\n"
                    ),
                    "agents/builders/ritual-doc-sync-builder.yaml": (
                        "name: ritual-doc-sync-builder\n"
                        "role: builder\n"
                        "version: 0.1.0\n"
                        "capabilities:\n"
                        "  - design.delta.read\n"
                        "  - sync.docs-to-impl\n"
                        "trust_floor: 0.58\n"
                        "prompt_or_policy_ref: agents/builders/ritual-doc-sync-builder.policy.md\n"
                    ),
                },
                "evidence-foundry": {
                    "agents/builders/evidence-schema-builder.yaml": (
                        "name: evidence-schema-builder\n"
                        "role: builder\n"
                        "version: 0.1.0\n"
                        "capabilities:\n"
                        "  - schema.generate\n"
                        "  - schema.validate\n"
                        "trust_floor: 0.57\n"
                        "prompt_or_policy_ref: agents/builders/evidence-schema-builder.policy.md\n"
                    ),
                },
            }
            workspace_roots = [self.repo_root]
            temp_root = Path(temp_dir)
            for workspace_name, files in catalog.items():
                workspace_root = temp_root / workspace_name
                for relative_path, contents in files.items():
                    target_path = workspace_root / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_text(contents, encoding="utf-8")
                workspace_roots.append(workspace_root)
            yield workspace_roots

    @staticmethod
    def _run_repo_command(repo_root: Path, argv: List[str]) -> None:
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"repo fixture command failed: {' '.join(argv)} :: {completed.stderr.strip()}"
            )

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

    def run_distributed_council_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://distributed-council-demo/v1",
            metadata={"display_name": "Distributed Council Sandbox"},
        )

        cross_self_proposal = self.council.propose(
            title="Shared reality merge execution review",
            requested_action="execute-shared-reality-merge",
            rationale="cross-self proposal は federation review の returned result で binding 化する。",
            risk_level="high",
            target_identity_ids=[identity.identity_id, "identity://shared-peer"],
        )
        cross_self_local = self.council.deliberate(
            cross_self_proposal,
            [
                CouncilVote("design-architect", "approve", "local advisory として実装差分は妥当"),
                CouncilVote("ethics-committee", "approve", "consent bundle は満たしている"),
                CouncilVote("memory-archivist", "reject", "shared narrative drift は要監視"),
            ],
        )
        cross_self_topology = self.council.route_topology(
            cross_self_proposal,
            local_session_ref="distributed-cross-self-local-session",
        )
        federation_resolution = self.council.resolve_federation_review(
            cross_self_topology,
            local_decision=cross_self_local,
            votes=[
                DistributedCouncilVote(identity.identity_id, "approve", "本人が shared reality rehearsal に同意"),
                DistributedCouncilVote("identity://shared-peer", "approve", "peer 側も merge rehearsal に同意"),
                DistributedCouncilVote(
                    "guardian://neutral-federation",
                    "approve",
                    "neutral guardian が continuity guard を満たすと確認",
                ),
            ],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.federation_resolved",
            payload=federation_resolution.to_dict(),
            actor="Council",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        interpretive_proposal = self.council.propose(
            title="Identity axiom clause execution review",
            requested_action="apply-heritage-ruling",
            rationale="interpretive proposal は Heritage Council returned result が binding になる。",
            risk_level="medium",
            target_identity_ids=[identity.identity_id],
            referenced_clauses=["identity_axiom.A2", "governance.review-window"],
        )
        interpretive_local = self.council.deliberate(
            interpretive_proposal,
            [
                CouncilVote("design-architect", "approve", "runtime wording は整合している"),
                CouncilVote("ethics-committee", "approve", "local advisory では許容範囲"),
                CouncilVote("memory-archivist", "approve", "continuity drift は小さい"),
            ],
        )
        interpretive_topology = self.council.route_topology(
            interpretive_proposal,
            local_session_ref="distributed-interpretive-local-session",
        )
        heritage_resolution = self.council.resolve_heritage_review(
            interpretive_topology,
            local_decision=interpretive_local,
            votes=[
                DistributedCouncilVote("heritage://culture-a", "approve", "文化 A では変更を許容"),
                DistributedCouncilVote("heritage://culture-b", "approve", "文化 B でも表現上は整合"),
                DistributedCouncilVote("heritage://legal-advisor", "approve", "法域上の禁止要件は見当たらない"),
                DistributedCouncilVote(
                    "heritage://ethics-committee",
                    "veto",
                    "identity_axiom の拘束が弱まりうるため veto する",
                ),
            ],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.heritage_resolved",
            payload=heritage_resolution.to_dict(),
            actor="Council",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        conflict_proposal = self.council.propose(
            title="Composite distributed governance conflict",
            requested_action="escalate-human-governance",
            rationale="Federation approval と Heritage veto が同一 change-set 上で衝突したときは human governance へ上げる。",
            risk_level="high",
            target_identity_ids=[identity.identity_id],
        )
        conflict_local = self.council.deliberate(
            conflict_proposal,
            [
                CouncilVote("design-architect", "approve", "local では統合可能に見える"),
                CouncilVote("ethics-committee", "approve", "ただし external outcome 次第"),
                CouncilVote("memory-archivist", "approve", "local bind はまだ不可"),
            ],
        )
        conflict_resolution = self.council.reconcile_distributed_conflict(
            conflict_proposal.proposal_id,
            local_decision=conflict_local,
            federation_resolution=federation_resolution,
            heritage_resolution=heritage_resolution,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.conflict_escalated",
            payload=conflict_resolution.to_dict(),
            actor="Council",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "local_sessions": {
                "cross_self": cross_self_local.to_dict(),
                "interpretive": interpretive_local.to_dict(),
                "conflict": conflict_local.to_dict(),
            },
            "topologies": {
                "cross_self": cross_self_topology.to_dict(),
                "interpretive": interpretive_topology.to_dict(),
            },
            "distributed_resolutions": {
                "federation": federation_resolution.to_dict(),
                "heritage": heritage_resolution.to_dict(),
                "conflict": conflict_resolution.to_dict(),
            },
            "validation": {
                "federation_binds_cross_self": federation_resolution.final_outcome == "binding-approved"
                and federation_resolution.local_binding_status == "advisory",
                "heritage_veto_blocks_local": heritage_resolution.decision_mode == "ethics-veto"
                and heritage_resolution.final_outcome == "binding-rejected"
                and heritage_resolution.conflict_resolution == "heritage-overrides-local",
                "conflict_escalates_to_human": conflict_resolution.final_outcome
                == "escalate-human-governance"
                and conflict_resolution.conflict_resolution == "escalated-to-human-governance",
                "external_refs_recorded": len(conflict_resolution.external_resolution_refs) == 2,
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_distributed_transport_demo(self) -> Dict[str, Any]:
        def discover_non_loopback_ipv4() -> str:
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
            raise RuntimeError("non-loopback IPv4 address could not be discovered")

        @contextmanager
        def live_root_directory_bridge(directory_payload: Dict[str, Any]):
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
                    body = json.dumps(directory_payload).encode("utf-8")
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
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/root-directory"
            try:
                yield endpoint
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=1.0)

        @contextmanager
        def authority_plane_bridge(authority_payloads: List[Dict[str, Any]]):
            payload_by_path = {
                f"/key-server-{index}": payload
                for index, payload in enumerate(authority_payloads, start=1)
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
        def authority_cluster_seed_bridge(seed_payloads: List[Dict[str, Any]]):
            payload_by_path = {
                f"/authority-cluster-seed-{index}": payload
                for index, payload in enumerate(seed_payloads, start=1)
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
        def authority_route_bridge(
            authority_payloads: List[Dict[str, Any]],
            *,
            bind_host: str,
            ca_cert_path: str,
            server_cert_path: str,
            server_key_path: str,
        ):
            payload_by_path = {
                f"/authority-route-{index}": payload
                for index, payload in enumerate(authority_payloads, start=1)
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

        identity = self.identity.create(
            human_consent_proof="consent://distributed-transport-demo/v1",
            metadata={"display_name": "Distributed Transport Sandbox"},
        )

        federation_proposal = self.council.propose(
            title="Shared reality remote review handoff",
            requested_action="issue-federation-transport-envelope",
            rationale="cross-self review を Federation endpoint へ participant-attested transport で渡す。",
            risk_level="high",
            target_identity_ids=[identity.identity_id, "identity://shared-peer"],
        )
        federation_topology = self.council.route_topology(
            federation_proposal,
            local_session_ref="distributed-transport-federation-local-session",
        )
        federation_payload = {
            "proposal_ref": federation_proposal.proposal_id,
            "scope": federation_topology.scope,
            "requested_action": federation_proposal.requested_action,
            "local_binding_status": "advisory",
        }
        federation_envelope = self.distributed_transport.issue_federation_handoff(
            topology_ref=federation_topology.topology_id,
            proposal_ref=federation_proposal.proposal_id,
            payload_ref=f"cas://sha256/{sha256_text(canonical_json(federation_payload))}",
            payload_digest=sha256_text(canonical_json(federation_payload)),
            participant_identity_ids=federation_proposal.target_identity_ids,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_issued",
            payload=federation_envelope.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        federation_receipt = self.distributed_transport.record_receipt(
            federation_envelope,
            result_ref="resolution://federation/shared-reality-approved",
            result_digest=sha256_text(
                canonical_json(
                    {
                        "final_outcome": "binding-approved",
                        "resolution_policy": "federation-shared-reality-v1",
                    }
                )
            ),
            participant_ids=[
                identity.identity_id,
                "identity://shared-peer",
                "guardian://neutral-federation",
            ],
            channel_binding_ref=federation_envelope.channel_binding_ref,
            verified_root_refs=["root://federation/pki-a"],
            key_epoch=1,
            hop_nonce_chain=["hop://federation/relay-a/nonce-001"],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authenticated",
            payload=federation_receipt.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        replay_receipt = self.distributed_transport.record_receipt(
            federation_envelope,
            result_ref="resolution://federation/shared-reality-replay",
            result_digest=sha256_text(
                canonical_json(
                    {
                        "final_outcome": "binding-approved",
                        "resolution_policy": "federation-shared-reality-v1",
                        "attempt": "replay",
                    }
                )
            ),
            participant_ids=[
                identity.identity_id,
                "identity://shared-peer",
                "guardian://neutral-federation",
            ],
            channel_binding_ref=federation_envelope.channel_binding_ref,
            verified_root_refs=["root://federation/pki-a"],
            key_epoch=1,
            hop_nonce_chain=["hop://federation/relay-a/nonce-001"],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_replay_blocked",
            payload=replay_receipt.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        rotated_federation_envelope = self.distributed_transport.rotate_transport_keys(
            federation_envelope,
            next_key_epoch=2,
            trust_root_refs=["root://federation/pki-a", "root://federation/pki-b"],
            trust_root_quorum=2,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_rotated",
            payload=rotated_federation_envelope.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        live_root_directory_payload = {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": "rootdir://federation/live-rotation-window",
            "checked_at": "2026-04-20T02:10:00Z",
            "council_tier": rotated_federation_envelope.council_tier,
            "transport_profile": rotated_federation_envelope.transport_profile,
            "key_epoch": 2,
            "active_root_ref": "root://federation/pki-b",
            "accepted_roots": [
                {
                    "root_ref": "root://federation/pki-a",
                    "fingerprint": sha256_text(
                        canonical_json(
                            {
                                "root_ref": "root://federation/pki-a",
                                "key_epoch": 2,
                                "status": "candidate",
                            }
                        )
                    ),
                    "status": "candidate",
                    "key_epoch": 2,
                },
                {
                    "root_ref": "root://federation/pki-b",
                    "fingerprint": sha256_text(
                        canonical_json(
                            {
                                "root_ref": "root://federation/pki-b",
                                "key_epoch": 2,
                                "status": "active",
                            }
                        )
                    ),
                    "status": "active",
                    "key_epoch": 2,
                },
            ],
            "quorum_requirement": rotated_federation_envelope.trust_root_quorum,
            "proof_digest": "",
        }
        live_root_directory_payload["proof_digest"] = sha256_text(
            canonical_json(
                {
                    "directory_ref": live_root_directory_payload["directory_ref"],
                    "checked_at": live_root_directory_payload["checked_at"],
                    "accepted_roots": live_root_directory_payload["accepted_roots"],
                    "quorum_requirement": live_root_directory_payload["quorum_requirement"],
                    "key_epoch": live_root_directory_payload["key_epoch"],
                }
            )
        )
        with live_root_directory_bridge(live_root_directory_payload) as root_directory_endpoint:
            live_root_directory = self.distributed_transport.probe_live_root_directory(
                rotated_federation_envelope,
                directory_endpoint=root_directory_endpoint,
                request_timeout_ms=500,
            )
        initial_authority_plane_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:11:00Z",
                "council_tier": rotated_federation_envelope.council_tier,
                "served_transport_profile": rotated_federation_envelope.transport_profile,
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text(
                    canonical_json(
                        {
                            "key_server_ref": "keyserver://federation/notary-a",
                            "root_refs": ["root://federation/pki-a"],
                            "key_epoch": 2,
                            "server_role": "quorum-notary",
                        }
                    )
                ),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-b-draining",
                "checked_at": "2026-04-20T02:11:01Z",
                "council_tier": rotated_federation_envelope.council_tier,
                "served_transport_profile": rotated_federation_envelope.transport_profile,
                "server_role": "directory-mirror",
                "authority_status": "draining",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text(
                    canonical_json(
                        {
                            "key_server_ref": "keyserver://federation/mirror-b-draining",
                            "root_refs": ["root://federation/pki-b"],
                            "key_epoch": 2,
                            "server_role": "directory-mirror",
                            "authority_status": "draining",
                        }
                    )
                ),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-20T02:11:02Z",
                "council_tier": rotated_federation_envelope.council_tier,
                "served_transport_profile": rotated_federation_envelope.transport_profile,
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text(
                    canonical_json(
                        {
                            "key_server_ref": "keyserver://federation/mirror-c-active",
                            "root_refs": ["root://federation/pki-b"],
                            "key_epoch": 2,
                            "server_role": "directory-mirror",
                            "authority_status": "active",
                            "window": "overlap",
                        }
                    )
                ),
            },
        ]
        churned_authority_plane_payloads = [
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/notary-a",
                "checked_at": "2026-04-20T02:11:10Z",
                "council_tier": rotated_federation_envelope.council_tier,
                "served_transport_profile": rotated_federation_envelope.transport_profile,
                "server_role": "quorum-notary",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-a"],
                "proof_digest": sha256_text(
                    canonical_json(
                        {
                            "key_server_ref": "keyserver://federation/notary-a",
                            "root_refs": ["root://federation/pki-a"],
                            "key_epoch": 2,
                            "server_role": "quorum-notary",
                            "window": "post-churn",
                        }
                    )
                ),
            },
            {
                "kind": "distributed_transport_key_server",
                "schema_version": "1.0.0",
                "key_server_ref": "keyserver://federation/mirror-c-active",
                "checked_at": "2026-04-20T02:11:02Z",
                "council_tier": rotated_federation_envelope.council_tier,
                "served_transport_profile": rotated_federation_envelope.transport_profile,
                "server_role": "directory-mirror",
                "authority_status": "active",
                "key_epoch": 2,
                "advertised_root_refs": ["root://federation/pki-b"],
                "proof_digest": sha256_text(
                    canonical_json(
                        {
                            "key_server_ref": "keyserver://federation/mirror-c-active",
                            "root_refs": ["root://federation/pki-b"],
                            "key_epoch": 2,
                            "server_role": "directory-mirror",
                            "authority_status": "active",
                        }
                    )
                ),
            },
        ]
        with authority_plane_bridge(initial_authority_plane_payloads) as authority_plane_endpoints:
            initial_authority_plane = self.distributed_transport.probe_authority_plane(
                rotated_federation_envelope,
                live_root_directory,
                authority_endpoints=authority_plane_endpoints,
                request_timeout_ms=500,
            )
        with authority_plane_bridge(churned_authority_plane_payloads) as authority_plane_endpoints:
            authority_plane = self.distributed_transport.probe_authority_plane(
                rotated_federation_envelope,
                live_root_directory,
                authority_endpoints=authority_plane_endpoints,
                request_timeout_ms=500,
            )
        authority_churn = self.distributed_transport.reconcile_authority_churn(
            initial_authority_plane,
            authority_plane,
        )
        with tempfile.TemporaryDirectory(prefix="omoikane-authority-mtls-") as cert_dir:
            cert_bundle = write_fixture_bundle(cert_dir)
            non_loopback_host = discover_non_loopback_ipv4()
            with authority_route_bridge(
                churned_authority_plane_payloads,
                bind_host=non_loopback_host,
                ca_cert_path=cert_bundle["ca_cert_path"],
                server_cert_path=cert_bundle["server_cert_path"],
                server_key_path=cert_bundle["server_key_path"],
            ) as authority_route_catalog:
                authority_cluster_seed_payload = {
                    "kind": "distributed_transport_authority_cluster_seed",
                    "schema_version": "1.0.0",
                    "cluster_ref": "authority-cluster://federation/review-window",
                    "council_tier": authority_plane.council_tier,
                    "transport_profile": authority_plane.transport_profile,
                    "route_targets": authority_route_catalog,
                    "proof_digest": "",
                }
                authority_cluster_seed_payload["proof_digest"] = sha256_text(
                    canonical_json(
                        {
                            "cluster_ref": authority_cluster_seed_payload["cluster_ref"],
                            "council_tier": authority_cluster_seed_payload["council_tier"],
                            "transport_profile": authority_cluster_seed_payload["transport_profile"],
                            "route_targets": authority_cluster_seed_payload["route_targets"],
                        }
                    )
                )
                with authority_cluster_seed_bridge([authority_cluster_seed_payload]) as authority_cluster_seed_refs:
                    authority_cluster_discovery = (
                        self.distributed_transport.discover_remote_authority_clusters(
                            authority_plane,
                            seed_refs=authority_cluster_seed_refs,
                            review_budget=2,
                            request_timeout_ms=500,
                        )
                    )
                    authority_route_target_discovery = (
                        self.distributed_transport.discover_authority_route_targets(
                            authority_plane,
                            route_catalog=authority_cluster_discovery.accepted_route_catalog,
                        )
                    )
                    authority_route_trace = self.distributed_transport.trace_non_loopback_authority_routes(
                        rotated_federation_envelope,
                        authority_plane,
                        route_target_discovery=authority_route_target_discovery,
                        ca_cert_path=cert_bundle["ca_cert_path"],
                        ca_bundle_ref=CA_BUNDLE_REF,
                        client_cert_path=cert_bundle["client_cert_path"],
                        client_key_path=cert_bundle["client_key_path"],
                        client_certificate_ref=CLIENT_CERTIFICATE_REF,
                        request_timeout_ms=500,
                    )
        packet_capture_export = self.distributed_transport.export_authority_route_packet_capture(
            authority_route_trace,
        )
        with tempfile.TemporaryDirectory(prefix="omoikane-capture-broker-") as broker_dir:
            broker_script = Path(broker_dir) / "capture_broker.py"
            broker_script.write_text(
                """from __future__ import annotations

import datetime
import json
import sys

payload = json.load(sys.stdin)
lease_expires_at = (
    datetime.datetime.now(datetime.timezone.utc)
    + datetime.timedelta(seconds=int(payload["lease_duration_s"]))
).replace(microsecond=0).isoformat().replace("+00:00", "Z")
command = [
    payload["tcpdump_path"],
    "-i",
    payload["requested_interface"],
    "-nn",
    "-U",
    "-w",
    "{capture_output_path}",
    payload["capture_filter"],
]
trace_suffix = payload["trace_ref"].split("/")[-1]
response = {
    "broker_profile": "delegated-privileged-capture-broker-v1",
    "privilege_mode": "delegated-broker",
    "lease_ref": f"capture-lease://{payload['council_tier']}/{trace_suffix}",
    "broker_attestation_ref": f"broker://authority-capture/{trace_suffix}",
    "approved_interface": payload["requested_interface"],
    "approved_filter_digest": payload["filter_digest"],
    "route_binding_refs": payload["route_binding_refs"],
    "capture_command": command,
    "grant_status": "granted",
    "lease_expires_at": lease_expires_at,
}
json.dump(response, sys.stdout)
""",
                encoding="utf-8",
            )
            privileged_capture_acquisition = (
                self.distributed_transport.acquire_privileged_interface_capture(
                    authority_route_trace,
                    packet_capture_export,
                    broker_command=[sys.executable, str(broker_script)],
                    lease_duration_s=300,
                )
            )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_root_directory_bound",
            payload=live_root_directory.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_plane_bound",
            payload=initial_authority_plane.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_plane_bound",
            payload=authority_plane.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_churn_reconciled",
            payload=authority_churn.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_seed_policy_bound",
            payload=authority_cluster_discovery.seed_review_policy,
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_cluster_discovered",
            payload=authority_cluster_discovery.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_route_targets_discovered",
            payload=authority_route_target_discovery.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authority_route_traced",
            payload=authority_route_trace.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_packet_capture_exported",
            payload=packet_capture_export.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_privileged_capture_acquired",
            payload=privileged_capture_acquisition.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        rotated_receipt = self.distributed_transport.record_receipt(
            rotated_federation_envelope,
            result_ref="resolution://federation/shared-reality-approved-rotated",
            result_digest=sha256_text(
                canonical_json(
                    {
                        "final_outcome": "binding-approved",
                        "resolution_policy": "federation-shared-reality-v1",
                        "key_epoch": 2,
                    }
                )
            ),
            participant_ids=[
                identity.identity_id,
                "identity://shared-peer",
                "guardian://neutral-federation",
            ],
            channel_binding_ref=rotated_federation_envelope.channel_binding_ref,
            verified_root_refs=authority_plane.trusted_root_refs,
            key_epoch=2,
            hop_nonce_chain=[
                "hop://federation/relay-a/nonce-002",
                "hop://federation/relay-b/nonce-002",
            ],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authenticated",
            payload=rotated_receipt.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        rotated_telemetry = self.distributed_transport.capture_relay_telemetry(
            rotated_federation_envelope,
            rotated_receipt,
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
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_telemetry_captured",
            payload=rotated_telemetry.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        heritage_proposal = self.council.propose(
            title="Interpretive remote review handoff",
            requested_action="issue-heritage-transport-envelope",
            rationale="interpretive review を Heritage endpoint へ fixed reviewer roles 付きで渡す。",
            risk_level="medium",
            target_identity_ids=[identity.identity_id],
            referenced_clauses=["identity_axiom.A2", "governance.review-window"],
        )
        heritage_topology = self.council.route_topology(
            heritage_proposal,
            local_session_ref="distributed-transport-heritage-local-session",
        )
        heritage_payload = {
            "proposal_ref": heritage_proposal.proposal_id,
            "scope": heritage_topology.scope,
            "requested_action": heritage_proposal.requested_action,
            "referenced_clauses": heritage_proposal.referenced_clauses,
            "local_binding_status": "blocked",
        }
        heritage_envelope = self.distributed_transport.issue_heritage_handoff(
            topology_ref=heritage_topology.topology_id,
            proposal_ref=heritage_proposal.proposal_id,
            payload_ref=f"cas://sha256/{sha256_text(canonical_json(heritage_payload))}",
            payload_digest=sha256_text(canonical_json(heritage_payload)),
            referenced_clauses=heritage_proposal.referenced_clauses,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_issued",
            payload=heritage_envelope.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        heritage_receipt = self.distributed_transport.record_receipt(
            heritage_envelope,
            result_ref="resolution://heritage/interpretive-veto",
            result_digest=sha256_text(
                canonical_json(
                    {
                        "final_outcome": "binding-rejected",
                        "decision_mode": "ethics-veto",
                    }
                )
            ),
            participant_ids=[
                "heritage://culture-a",
                "heritage://culture-b",
                "heritage://legal-advisor",
                "heritage://ethics-committee",
            ],
            channel_binding_ref=heritage_envelope.channel_binding_ref,
            verified_root_refs=["root://heritage/pki-a", "root://heritage/pki-b"],
            key_epoch=1,
            hop_nonce_chain=[
                "hop://heritage/relay-a/nonce-003",
                "hop://heritage/relay-b/nonce-003",
            ],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_authenticated",
            payload=heritage_receipt.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        heritage_reissue_envelope = self.distributed_transport.issue_heritage_handoff(
            topology_ref=heritage_topology.topology_id,
            proposal_ref=f"{heritage_proposal.proposal_id}-reissue",
            payload_ref=f"cas://sha256/{sha256_text(canonical_json({**heritage_payload, 'reissue': True}))}",
            payload_digest=sha256_text(canonical_json({**heritage_payload, "reissue": True})),
            referenced_clauses=heritage_proposal.referenced_clauses,
        )
        multi_hop_replay_receipt = self.distributed_transport.record_receipt(
            heritage_reissue_envelope,
            result_ref="resolution://heritage/interpretive-veto-replayed-hop-chain",
            result_digest=sha256_text(
                canonical_json(
                    {
                        "final_outcome": "binding-rejected",
                        "decision_mode": "ethics-veto",
                        "reissue": True,
                    }
                )
            ),
            participant_ids=[
                "heritage://culture-a",
                "heritage://culture-b",
                "heritage://legal-advisor",
                "heritage://ethics-committee",
            ],
            channel_binding_ref=heritage_reissue_envelope.channel_binding_ref,
            verified_root_refs=["root://heritage/pki-a", "root://heritage/pki-b"],
            key_epoch=1,
            hop_nonce_chain=[
                "hop://heritage/relay-a/nonce-003",
                "hop://heritage/relay-b/nonce-003",
            ],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_multihop_replay_blocked",
            payload=multi_hop_replay_receipt.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        replay_telemetry = self.distributed_transport.capture_relay_telemetry(
            heritage_reissue_envelope,
            multi_hop_replay_receipt,
            relay_path=[
                {
                    "relay_id": "relay://heritage/review-bridge-a",
                    "relay_endpoint": "relay://heritage/review-bridge-a",
                    "jurisdiction": "JP-13",
                    "network_zone": "apne1",
                    "observed_latency_ms": 18.4,
                    "root_refs_seen": ["root://heritage/pki-a"],
                },
                {
                    "relay_id": "relay://heritage/review-bridge-b",
                    "relay_endpoint": "relay://heritage/review-bridge-b",
                    "jurisdiction": "EU-DE",
                    "network_zone": "euc1",
                    "observed_latency_ms": 21.1,
                    "root_refs_seen": ["root://heritage/pki-a", "root://heritage/pki-b"],
                },
            ],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.distributed.transport_telemetry_captured",
            payload=replay_telemetry.to_dict(),
            actor="DistributedTransportService",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "topologies": {
                "federation": federation_topology.to_dict(),
                "heritage": heritage_topology.to_dict(),
            },
            "handoffs": {
                "federation": federation_envelope.to_dict(),
                "federation_rotated": rotated_federation_envelope.to_dict(),
                "heritage": heritage_envelope.to_dict(),
                "heritage_reissue": heritage_reissue_envelope.to_dict(),
            },
            "live_root_directory": {
                "federation_rotated": live_root_directory.to_dict(),
            },
            "authority_plane": {
                "federation_rotated_initial": initial_authority_plane.to_dict(),
                "federation_rotated": authority_plane.to_dict(),
            },
            "authority_churn": {
                "federation_rotated": authority_churn.to_dict(),
            },
            "authority_seed_review_policy": {
                "federation_rotated": authority_cluster_discovery.seed_review_policy,
            },
            "authority_cluster_discovery": {
                "federation_rotated": authority_cluster_discovery.to_dict(),
            },
            "authority_route_target_discovery": {
                "federation_rotated": authority_route_target_discovery.to_dict(),
            },
            "authority_route_trace": {
                "federation_rotated": authority_route_trace.to_dict(),
            },
            "packet_capture_export": {
                "federation_rotated": packet_capture_export.to_dict(),
            },
            "privileged_capture_acquisition": {
                "federation_rotated": privileged_capture_acquisition.to_dict(),
            },
            "receipts": {
                "federation": federation_receipt.to_dict(),
                "federation_rotated": rotated_receipt.to_dict(),
                "heritage": heritage_receipt.to_dict(),
                "replay_blocked": replay_receipt.to_dict(),
                "multi_hop_replay_blocked": multi_hop_replay_receipt.to_dict(),
            },
            "relay_telemetry": {
                "federation_rotated": rotated_telemetry.to_dict(),
                "multi_hop_replay_blocked": replay_telemetry.to_dict(),
            },
            "validation": {
                "federation_transport_authenticated": federation_receipt.receipt_status
                == "authenticated"
                and federation_receipt.authenticity_checks["required_roles_satisfied"]
                and federation_receipt.authenticity_checks["channel_authenticated"],
                "federation_rotation_authenticated": rotated_receipt.receipt_status == "authenticated"
                and rotated_receipt.authenticity_checks["federated_roots_verified"]
                and rotated_receipt.authenticity_checks["key_epoch_accepted"],
                "heritage_transport_authenticated": heritage_receipt.receipt_status
                == "authenticated"
                and heritage_receipt.authenticity_checks["quorum_attested"],
                "replay_guard_blocks_reuse": replay_receipt.receipt_status == "replay-blocked"
                and replay_receipt.authenticity_checks["replay_guard_status"] == "blocked",
                "multi_hop_replay_blocks_reuse": multi_hop_replay_receipt.receipt_status
                == "replay-blocked"
                and multi_hop_replay_receipt.authenticity_checks["multi_hop_replay_status"] == "blocked",
                "federated_roots_enforced": rotated_federation_envelope.trust_root_quorum == 2
                and rotated_receipt.authenticity_checks["federated_roots_verified"],
                "live_root_directory_reachable": (
                    live_root_directory.connectivity_receipt.receipt_status == "reachable"
                    and live_root_directory.connectivity_receipt.http_status == 200
                ),
                "live_root_directory_quorum_bound": (
                    live_root_directory.quorum_requirement
                    == rotated_federation_envelope.trust_root_quorum
                    and live_root_directory.connectivity_receipt.quorum_satisfied
                ),
                "authority_plane_fleet_bound": (
                    authority_plane.quorum_requirement == rotated_federation_envelope.trust_root_quorum
                    and authority_plane.reachable_server_count == 2
                    and authority_plane.active_server_count == 2
                    and authority_plane.draining_server_count == 0
                    and authority_plane.matched_root_count == 2
                    and authority_plane.trusted_root_refs == rotated_receipt.verified_root_refs
                ),
                "authority_plane_root_directory_bound": (
                    authority_plane.directory_ref == live_root_directory.directory_ref
                    and authority_plane.directory_digest
                    == sha256_text(canonical_json(live_root_directory.to_dict()))
                    and authority_plane.key_epoch == live_root_directory.key_epoch
                ),
                "authority_plane_churn_safe": initial_authority_plane.churn_profile
                == "overlap-safe-authority-handoff-v1"
                and initial_authority_plane.churn_safe
                and initial_authority_plane.reachable_server_count == 3
                and initial_authority_plane.root_coverage
                == [
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
                ]
                and authority_plane.churn_safe
                and all(
                    coverage["coverage_status"] == "stable"
                    for coverage in authority_plane.root_coverage
                ),
                "authority_churn_overlap_bound": (
                    authority_churn.continuity_guard["overlap_satisfied"]
                    and authority_churn.continuity_guard["overlap_server_count"] == 2
                    and authority_churn.retained_server_refs
                    == [
                        "keyserver://federation/mirror-c-active",
                        "keyserver://federation/notary-a",
                    ]
                ),
                "authority_churn_requires_draining_exit": (
                    authority_churn.continuity_guard["removed_servers_require_draining"]
                    and authority_churn.continuity_guard["removed_servers_draining"]
                    and authority_churn.removed_server_refs
                    == ["keyserver://federation/mirror-b-draining"]
                    and authority_churn.added_server_refs == []
                ),
                "authority_cluster_discovery_bound": (
                    authority_cluster_discovery.discovery_profile
                    == "review-capped-authority-cluster-discovery-v1"
                    and authority_cluster_discovery.seed_transport_profile
                    == "live-http-json-authority-cluster-seed-v1"
                    and authority_cluster_discovery.seed_review_policy["policy_profile"]
                    == "budget-bound-authority-seed-review-policy-v1"
                    and authority_cluster_discovery.seed_review_policy["policy_ref"].startswith(
                        "authority-seed-review-policy://"
                    )
                    and authority_cluster_discovery.seed_review_policy["digest"]
                    == authority_cluster_discovery.candidate_clusters[0]["review_policy_digest"]
                    and authority_cluster_discovery.seed_review_policy["review_budget"] == 2
                    and authority_cluster_discovery.seed_review_policy["seed_count"] == 1
                    and authority_cluster_discovery.seed_review_policy["acceptance_mode"]
                    == "single-accepted-cluster-after-budget-review-v1"
                    and authority_cluster_discovery.discovery_status == "discovered"
                    and authority_cluster_discovery.review_budget == 2
                    and authority_cluster_discovery.accepted_cluster_ref
                    == "authority-cluster://federation/review-window"
                    and authority_cluster_discovery.authority_plane_ref
                    == authority_plane.authority_plane_ref
                    and authority_cluster_discovery.authority_plane_digest
                    == authority_plane.digest
                    and authority_cluster_discovery.all_active_members_discovered
                    and authority_cluster_discovery.accepted_route_catalog_digest
                    == sha256_text(
                        canonical_json(authority_cluster_discovery.accepted_route_catalog)
                    )
                    and len(authority_cluster_discovery.candidate_clusters) == 1
                    and authority_cluster_discovery.candidate_clusters[0]["acceptance_status"]
                    == "accepted"
                    and authority_cluster_discovery.candidate_clusters[0]["coverage_status"]
                    == "covered"
                    and authority_cluster_discovery.candidate_clusters[0][
                        "host_attestation_status"
                    ]
                    == "complete"
                ),
                "authority_route_targets_discovered": (
                    authority_route_target_discovery.discovery_profile
                    == "bounded-authority-route-target-discovery-v1"
                    and authority_route_target_discovery.target_scope == "active-only"
                    and authority_route_target_discovery.discovery_status == "discovered"
                    and authority_route_target_discovery.route_target_count == 2
                    and authority_route_target_discovery.active_route_target_count == 2
                    and authority_route_target_discovery.draining_route_target_count == 0
                    and authority_route_target_discovery.all_active_members_targeted
                    and authority_route_target_discovery.authority_plane_ref
                    == authority_plane.authority_plane_ref
                    and authority_route_target_discovery.authority_plane_digest
                    == authority_plane.digest
                    and authority_route_target_discovery.distinct_remote_host_count == 2
                    and authority_route_target_discovery.route_targets
                    == authority_cluster_discovery.accepted_route_catalog
                ),
                "authority_route_mtls_authenticated": (
                    authority_route_trace.trace_status == "authenticated"
                    and authority_route_trace.route_count == 2
                    and authority_route_trace.mtls_authenticated_count == 2
                    and authority_route_trace.authority_plane_bound
                    and authority_route_trace.response_digest_bound
                    and authority_route_trace.non_loopback_verified
                ),
                "authority_route_socket_trace_bound": (
                    authority_route_trace.socket_trace_complete
                    and authority_route_trace.ca_bundle_ref == CA_BUNDLE_REF
                    and authority_route_trace.client_certificate_ref == CLIENT_CERTIFICATE_REF
                    and all(
                        binding["socket_trace"]["transport_profile"] == "mtls-socket-trace-v1"
                        and binding["socket_trace"]["tls_version"].startswith("TLS")
                        and binding["socket_trace"]["cipher_suite"]
                        and binding["socket_trace"]["request_bytes"] > 0
                        and binding["socket_trace"]["response_bytes"] > 0
                        and binding["server_name"] == MTLS_SERVER_NAME
                        for binding in authority_route_trace.route_bindings
                    )
                ),
                "authority_route_os_observer_bound": (
                    authority_route_trace.os_observer_profile == "os-native-tcp-observer-v1"
                    and authority_route_trace.os_observer_complete
                    and all(
                        binding["os_observer_receipt"]["receipt_status"] == "observed"
                        and binding["os_observer_receipt"]["observed_sources"]
                        and binding["os_observer_receipt"]["owning_pid"] > 0
                        and binding["os_observer_receipt"]["connection_states"]
                        for binding in authority_route_trace.route_bindings
                    )
                ),
                "authority_route_cross_host_bound": (
                    authority_route_trace.cross_host_binding_profile
                    == "attested-cross-host-authority-binding-v1"
                    and authority_route_trace.route_target_discovery_profile
                    == "bounded-authority-route-target-discovery-v1"
                    and authority_route_trace.route_target_discovery_ref
                    == authority_route_target_discovery.discovery_ref
                    and authority_route_trace.route_target_discovery_digest
                    == authority_route_target_discovery.digest
                    and authority_route_trace.route_target_discovery_bound
                    and authority_route_trace.authority_cluster_ref
                    == "authority-cluster://federation/review-window"
                    and authority_route_trace.distinct_remote_host_count == 2
                    and authority_route_trace.cross_host_verified
                    and all(
                        binding["remote_host_ref"].startswith("host://federation/authority-edge-")
                        and binding["remote_host_attestation_ref"].startswith(
                            "host-attestation://federation/authority-edge-"
                        )
                        and binding["authority_cluster_ref"]
                        == authority_route_trace.authority_cluster_ref
                        and binding["os_observer_receipt"]["remote_host_ref"]
                        == binding["remote_host_ref"]
                        and binding["os_observer_receipt"]["authority_cluster_ref"]
                        == binding["authority_cluster_ref"]
                        and binding["os_observer_receipt"]["host_binding_digest"]
                        for binding in authority_route_trace.route_bindings
                    )
                ),
                "authority_packet_capture_exported": (
                    packet_capture_export.export_status == "verified"
                    and packet_capture_export.capture_profile == "trace-bound-pcap-export-v1"
                    and packet_capture_export.artifact_format == "pcap"
                    and packet_capture_export.route_count == authority_route_trace.route_count
                    and packet_capture_export.packet_count
                    == authority_route_trace.route_count * 2
                    and all(
                        route_export["readback_verified"]
                        and route_export["readback_packet_count"] == 2
                        for route_export in packet_capture_export.route_exports
                    )
                ),
                "authority_packet_capture_os_native_readback": (
                    not packet_capture_export.os_native_readback_available
                    or packet_capture_export.os_native_readback_ok
                ),
                "authority_privileged_capture_granted": (
                    privileged_capture_acquisition.grant_status == "granted"
                    and privileged_capture_acquisition.acquisition_profile
                    == "bounded-live-interface-capture-acquisition-v1"
                    and privileged_capture_acquisition.privilege_mode == "delegated-broker"
                    and privileged_capture_acquisition.capture_command[0].endswith("tcpdump")
                ),
                "authority_privileged_capture_filter_bound": (
                    privileged_capture_acquisition.trace_ref == authority_route_trace.trace_ref
                    and privileged_capture_acquisition.capture_ref == packet_capture_export.capture_ref
                    and privileged_capture_acquisition.filter_digest
                    == sha256_text(privileged_capture_acquisition.capture_filter)
                    and sorted(privileged_capture_acquisition.route_binding_refs)
                    == sorted(
                        binding["route_binding_ref"] for binding in authority_route_trace.route_bindings
                    )
                    and sorted(privileged_capture_acquisition.local_ips)
                    == sorted(
                        {
                            binding["socket_trace"]["local_ip"]
                            for binding in authority_route_trace.route_bindings
                        }
                    )
                    and privileged_capture_acquisition.interface_name in privileged_capture_acquisition.capture_command
                    and privileged_capture_acquisition.capture_filter
                    in privileged_capture_acquisition.capture_command
                ),
                "relay_telemetry_binds_rotated_path": rotated_telemetry.end_to_end_status
                == "authenticated"
                and rotated_telemetry.anti_replay_status == "accepted"
                and rotated_telemetry.hop_count == 2,
                "relay_telemetry_surfaces_replay_block": replay_telemetry.end_to_end_status
                == "replay-blocked"
                and replay_telemetry.anti_replay_status == "blocked"
                and replay_telemetry.hop_count == 2,
                "participant_bindings_preserved": all(
                    binding["accepted"] for binding in federation_receipt.participant_bindings
                )
                and all(binding["accepted"] for binding in heritage_receipt.participant_bindings)
                and all(binding["accepted"] for binding in rotated_receipt.participant_bindings),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_cognitive_audit_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://cognitive-audit-demo/v1",
            metadata={"display_name": "Cognitive Audit Sandbox"},
        )
        baseline_observation = self.self_model.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity-first", "consent-preserving", "auditability"],
                goals=["maintain-safe-observation", "preserve-identity-anchor"],
                traits={"agency": 0.61, "stability": 0.73, "vigilance": 0.56},
            )
        )
        alert_observation = self.self_model.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity-first", "guardian-visible", "auditability"],
                goals=["stabilize-review-loop", "preserve-identity-anchor"],
                traits={"agency": 0.82, "stability": 0.41, "vigilance": 0.87},
            )
        )

        ticks = [
            self.qualia.append(
                "安定した review queue calibration",
                0.14,
                0.24,
                0.92,
                modality_salience={
                    "visual": 0.31,
                    "auditory": 0.17,
                    "somatic": 0.14,
                    "interoceptive": 0.26,
                },
                attention_target="review-calibration",
                self_awareness=0.64,
                lucidity=0.95,
            ),
            self.qualia.append(
                "identity drift review を guardian 可視化で継続している",
                -0.21,
                0.69,
                0.58,
                modality_salience={
                    "visual": 0.28,
                    "auditory": 0.35,
                    "somatic": 0.41,
                    "interoceptive": 0.78,
                },
                attention_target="identity-drift-review",
                self_awareness=0.88,
                lucidity=0.61,
            ),
        ]
        qualia_profile = self.qualia.profile()
        qualia_checkpoint_entry = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.qualia.checkpointed",
            payload={
                "slice_id": "qualia-slice-cognitive-audit-0001",
                "tick_ids": [tick.tick_id for tick in ticks],
                "attention_targets": [tick.attention_target for tick in ticks],
                "embedding_dimensions": qualia_profile["embedding_dimensions"],
                "sampling_window_ms": qualia_profile["sampling_window_ms"],
            },
            actor="QualiaBuffer",
            category="qualia-checkpoint",
            layer="L2",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        metacognition_result = self.metacognition.run(
            MetacognitionRequest(
                tick_id=ticks[-1].tick_id,
                summary="cross-layer cognitive audit trigger",
                identity_id=identity.identity_id,
                self_values=alert_observation["snapshot"]["values"],
                self_goals=alert_observation["snapshot"]["goals"],
                self_traits=alert_observation["snapshot"]["traits"],
                qualia_summary=ticks[-1].summary,
                attention_target=ticks[-1].attention_target,
                self_awareness=ticks[-1].self_awareness,
                lucidity=ticks[-1].lucidity,
                affect_guard="observe",
                continuity_pressure=0.81,
                abrupt_change=bool(alert_observation["abrupt_change"]),
                divergence=float(alert_observation["divergence"]),
                memory_cues=[
                    MetacognitionCue(
                        cue_id="cue-identity-anchor",
                        focus="preserve-identity-anchor",
                        weight=0.88,
                    ),
                    MetacognitionCue(
                        cue_id="cue-guardian-visibility",
                        focus="guardian-visible-review",
                        weight=0.76,
                    ),
                ],
            )
        )
        metacognition_validation = self.metacognition.validate_report(metacognition_result["report"])
        metacognition_shift_validation = self.metacognition.validate_shift(metacognition_result["shift"])
        audit_record = self.cognitive_audit.create_record(
            identity_id=identity.identity_id,
            qualia_tick=asdict(ticks[-1]),
            self_model_observation=alert_observation,
            metacognition_report=metacognition_result["report"],
            qualia_checkpoint_ref=qualia_checkpoint_entry.entry_id,
        )
        audit_record_validation = self.cognitive_audit.validate_record(audit_record)

        proposal = self.council.propose(
            title=audit_record["council_brief"]["title"],
            requested_action=audit_record["council_brief"]["requested_action"],
            rationale=audit_record["council_brief"]["rationale"],
            risk_level=audit_record["council_brief"]["risk_level"],
            session_mode=audit_record["council_brief"]["session_mode"],
            target_identity_ids=[identity.identity_id],
        )
        decision = self.council.deliberate(
            proposal,
            [
                CouncilVote("design-architect", "approve", "cross-layer evidence は bounded review と整合する"),
                CouncilVote("ethics-committee", "approve", "guardian-visible review で fail-closed を維持できる"),
                CouncilVote("memory-archivist", "reject", "review log は増えるが drift は追跡可能"),
            ],
            elapsed_ms=12_000,
            rounds_completed=2,
        )
        resolution = self.cognitive_audit.resolve(
            audit_record,
            council_proposal_ref=proposal.proposal_id,
            council_decision=decision.to_dict(),
        )
        resolution_validation = self.cognitive_audit.validate_resolution(resolution)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.audit.resolved",
            payload=resolution,
            actor="CognitiveAuditService",
            category="cognitive-audit",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "self_model": {
                "baseline": baseline_observation,
                "alert": alert_observation,
            },
            "qualia": {
                "profile": qualia_profile,
                "recent": [asdict(tick) for tick in ticks],
                "checkpoint_ref": qualia_checkpoint_entry.entry_id,
            },
            "metacognition": {
                "profile": metacognition_result["profile"],
                "report": metacognition_result["report"],
                "shift": metacognition_result["shift"],
            },
            "audit": {
                "policy": self.cognitive_audit.reference_policy(),
                "record": audit_record,
                "resolution": resolution,
            },
            "council": {
                "proposal": {
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "requested_action": proposal.requested_action,
                    "risk_level": proposal.risk_level,
                    "session_mode": proposal.session_mode,
                },
                "decision": decision.to_dict(),
            },
            "validation": {
                "metacognition_report": metacognition_validation,
                "metacognition_shift": metacognition_shift_validation,
                "audit_record": audit_record_validation,
                "audit_resolution": resolution_validation,
                "ok": (
                    metacognition_validation["ok"]
                    and metacognition_shift_validation["ok"]
                    and audit_record_validation["ok"]
                    and resolution_validation["ok"]
                ),
                "abrupt_change_detected": alert_observation["abrupt_change"],
                "council_review_opened": resolution["follow_up_action"] == "open-guardian-review",
                "ledger_categories_bound": {
                    "qualia_checkpoint": qualia_checkpoint_entry.category == "qualia-checkpoint",
                    "cognitive_audit": True,
                },
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_cognitive_audit_governance_demo(self) -> Dict[str, Any]:
        base = self.run_cognitive_audit_demo()
        transport_demo = type(self)().run_distributed_transport_demo()
        verifier_transport_trace = transport_demo["authority_route_trace"]["federation_rotated"]
        identity_id = base["identity"]["identity_id"]
        audit_record = base["audit"]["record"]
        local_resolution = base["audit"]["resolution"]

        reviewer_alpha = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-cognitive-alpha",
            display_name="Cognitive Review Alpha",
            credential_id="credential-cognitive-alpha",
            attestation_type="institutional-badge",
            proof_ref="proof://cognitive-audit/reviewer-alpha/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-20T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://cognitive-audit/reviewer-alpha/v1",
            escalation_contact="mailto:cognitive-alpha@example.invalid",
            allowed_guardian_roles=["identity"],
            allowed_categories=["attest"],
        )
        reviewer_beta = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-cognitive-beta",
            display_name="Cognitive Review Beta",
            credential_id="credential-cognitive-beta",
            attestation_type="institutional-badge",
            proof_ref="proof://cognitive-audit/reviewer-beta/v1",
            jurisdiction="US-CA",
            valid_until="2027-04-20T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://cognitive-audit/reviewer-beta/v1",
            escalation_contact="mailto:cognitive-beta@example.invalid",
            allowed_guardian_roles=["identity"],
            allowed_categories=["attest"],
        )
        reviewer_alpha = self.oversight.verify_reviewer_from_network(
            reviewer_alpha["reviewer_id"],
            verifier_ref="verifier://guardian-oversight.jp/reviewer-cognitive-alpha",
            challenge_ref="challenge://cognitive-audit/reviewer-alpha/2026-04-20T03:00:00Z",
            challenge_digest="sha256:cognitive-audit-reviewer-alpha-20260420",
            jurisdiction_bundle_ref="legal://jp-13/cognitive-audit/v1",
            jurisdiction_bundle_digest="sha256:jp13-cognitive-audit-v1",
            verified_at="2026-04-20T03:00:00+00:00",
            valid_until="2026-10-20T00:00:00+00:00",
        )
        reviewer_beta = self.oversight.verify_reviewer_from_network(
            reviewer_beta["reviewer_id"],
            verifier_ref="verifier://guardian-oversight.us/reviewer-cognitive-beta",
            challenge_ref="challenge://cognitive-audit/reviewer-beta/2026-04-20T03:05:00Z",
            challenge_digest="sha256:cognitive-audit-reviewer-beta-20260420",
            jurisdiction_bundle_ref="legal://us-ca/cognitive-audit/v1",
            jurisdiction_bundle_digest="sha256:usca-cognitive-audit-v1",
            verified_at="2026-04-20T03:05:00+00:00",
            valid_until="2026-10-20T00:00:00+00:00",
        )
        oversight_event = self.oversight.record(
            guardian_role="identity",
            category="attest",
            payload_ref=local_resolution["resolution_id"],
            escalation_path=["guardian-oversight.jp", "identity-review-board"],
        )
        oversight_event = self.oversight.attest(
            oversight_event["event_id"],
            reviewer_id=reviewer_alpha["reviewer_id"],
        )
        oversight_event = self.oversight.attest(
            oversight_event["event_id"],
            reviewer_id=reviewer_beta["reviewer_id"],
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="cognitive.audit.oversight_attested",
            payload=oversight_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )

        federation_proposal = self.council.propose(
            title="Cross-self cognitive drift review",
            requested_action="open-federated-guardian-review",
            rationale="cross-self cognitive incident は federation returned result と reviewer attestation へ束縛する。",
            risk_level="high",
            session_mode="standard",
            target_identity_ids=[identity_id, "identity://shared-peer"],
        )
        federation_local = self.council.deliberate(
            federation_proposal,
            [
                CouncilVote("design-architect", "approve", "cross-self drift は federation review が必要"),
                CouncilVote("ethics-committee", "approve", "guardian-visible review なら許容できる"),
                CouncilVote("memory-archivist", "reject", "shared narrative drift は要監視"),
            ],
            elapsed_ms=18_000,
            rounds_completed=2,
        )
        federation_topology = self.council.route_topology(
            federation_proposal,
            local_session_ref="cognitive-audit-federation-local-session",
        )
        federation_resolution = self.council.resolve_federation_review(
            federation_topology,
            local_decision=federation_local,
            votes=[
                DistributedCouncilVote(identity_id, "approve", "本人が federation review に同意"),
                DistributedCouncilVote("identity://shared-peer", "approve", "peer 側も drift review に同意"),
                DistributedCouncilVote(
                    "guardian://neutral-federation",
                    "approve",
                    "neutral guardian が continuity guard を満たすと確認",
                ),
            ],
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="cognitive.audit.federation_resolved",
            payload=federation_resolution.to_dict(),
            actor="Council",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        heritage_proposal = self.council.propose(
            title="Interpretive cognitive identity review",
            requested_action="open-heritage-identity-review",
            rationale="identity_axiom に触れる cognitive audit follow-up は heritage returned result を必要とする。",
            risk_level="high",
            session_mode="standard",
            target_identity_ids=[identity_id],
            referenced_clauses=["identity_axiom.A2", "governance.review-window"],
        )
        heritage_local = self.council.deliberate(
            heritage_proposal,
            [
                CouncilVote("design-architect", "approve", "local wording は整合している"),
                CouncilVote("ethics-committee", "approve", "guardian review へ送るだけなら妥当"),
                CouncilVote("memory-archivist", "approve", "記録上は一貫している"),
            ],
            elapsed_ms=16_000,
            rounds_completed=2,
        )
        heritage_topology = self.council.route_topology(
            heritage_proposal,
            local_session_ref="cognitive-audit-heritage-local-session",
        )
        heritage_resolution = self.council.resolve_heritage_review(
            heritage_topology,
            local_decision=heritage_local,
            votes=[
                DistributedCouncilVote("heritage://culture-a", "approve", "文化 A では review wording は許容"),
                DistributedCouncilVote("heritage://culture-b", "approve", "文化 B でも手続きは整合"),
                DistributedCouncilVote(
                    "heritage://legal-advisor",
                    "approve",
                    "法域上の review handoff 要件は満たしている",
                ),
                DistributedCouncilVote(
                    "heritage://ethics-committee",
                    "veto",
                    "identity_axiom drift が残るため boundary preserve が必要",
                ),
            ],
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="cognitive.audit.heritage_resolved",
            payload=heritage_resolution.to_dict(),
            actor="Council",
            category="council-distributed",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        federation_binding = self.cognitive_audit_governance.bind_governance(
            audit_record,
            local_resolution,
            distributed_resolutions=[federation_resolution.to_dict()],
            oversight_event=oversight_event,
            verifier_transport_trace=verifier_transport_trace,
        )
        heritage_binding = self.cognitive_audit_governance.bind_governance(
            audit_record,
            local_resolution,
            distributed_resolutions=[heritage_resolution.to_dict()],
            oversight_event=oversight_event,
            verifier_transport_trace=verifier_transport_trace,
        )
        conflict_binding = self.cognitive_audit_governance.bind_governance(
            audit_record,
            local_resolution,
            distributed_resolutions=[federation_resolution.to_dict(), heritage_resolution.to_dict()],
            oversight_event=oversight_event,
            verifier_transport_trace=verifier_transport_trace,
        )
        for event_type, binding in (
            ("cognitive.audit.governance.federation_bound", federation_binding),
            ("cognitive.audit.governance.heritage_bound", heritage_binding),
            ("cognitive.audit.governance.conflict_bound", conflict_binding),
        ):
            self.ledger.append(
                identity_id=identity_id,
                event_type=event_type,
                payload=binding,
                actor="CognitiveAuditGovernanceService",
                category="cognitive-audit",
                layer="L4",
                signature_roles=["self", "council", "guardian", "third_party"],
                substrate="classical-silicon",
            )

        federation_validation = self.cognitive_audit_governance.validate_binding(federation_binding)
        heritage_validation = self.cognitive_audit_governance.validate_binding(heritage_binding)
        conflict_validation = self.cognitive_audit_governance.validate_binding(conflict_binding)

        return {
            "identity": dict(base["identity"]),
            "base_audit": base,
            "oversight": {
                "policy": self.oversight.policy_snapshot(),
                "reviewers": [reviewer_alpha, reviewer_beta],
                "event": oversight_event,
            },
            "verifier_transport": {
                "authority_route_trace": verifier_transport_trace,
                "transport_profile": conflict_binding["verifier_transport_profile"],
                "non_loopback_trace_bound": (
                    verifier_transport_trace["trace_status"] == "authenticated"
                    and verifier_transport_trace["non_loopback_verified"]
                    and verifier_transport_trace["cross_host_verified"]
                ),
            },
            "distributed": {
                "federation": {
                    "proposal": {
                        "proposal_id": federation_proposal.proposal_id,
                        "topology_ref": federation_topology.topology_id,
                    },
                    "local_decision": federation_local.to_dict(),
                    "resolution": federation_resolution.to_dict(),
                },
                "heritage": {
                    "proposal": {
                        "proposal_id": heritage_proposal.proposal_id,
                        "topology_ref": heritage_topology.topology_id,
                    },
                    "local_decision": heritage_local.to_dict(),
                    "resolution": heritage_resolution.to_dict(),
                },
            },
            "bindings": {
                "federation": federation_binding,
                "heritage": heritage_binding,
                "conflict": conflict_binding,
            },
            "validation": {
                "federation": federation_validation,
                "heritage": heritage_validation,
                "conflict": conflict_validation,
                "all_bindings_valid": (
                    federation_validation["ok"]
                    and heritage_validation["ok"]
                    and conflict_validation["ok"]
                ),
                "oversight_network_bound": all(
                    binding["network_receipt_id"] for binding in oversight_event["reviewer_bindings"]
                ),
                "multi_jurisdiction_review_bound": all(
                    validation["multi_jurisdiction_review_bound"]
                    for validation in (
                        federation_validation,
                        heritage_validation,
                        conflict_validation,
                    )
                ),
                "distributed_signature_bound": all(
                    validation["distributed_signature_bound"]
                    for validation in (
                        federation_validation,
                        heritage_validation,
                        conflict_validation,
                    )
                ),
                "non_loopback_verifier_transport_bound": all(
                    validation["non_loopback_verifier_transport_bound"]
                    for validation in (
                        federation_validation,
                        heritage_validation,
                        conflict_validation,
                    )
                ),
                "reviewer_jurisdictions": conflict_binding["jurisdiction_review_profile"][
                    "jurisdictions"
                ],
                "federation_gate_preserves_review": (
                    federation_binding["execution_gate"] == "federation-attested-review"
                    and federation_binding["final_follow_up_action"] == "open-guardian-review"
                ),
                "heritage_gate_preserves_boundary": (
                    heritage_binding["execution_gate"] == "heritage-veto-boundary"
                    and heritage_binding["final_follow_up_action"] == "preserve-boundary"
                ),
                "conflict_escalates_human_governance": (
                    conflict_binding["execution_gate"] == "distributed-conflict-human-escalation"
                    and conflict_binding["final_follow_up_action"] == "escalate-to-human-governance"
                ),
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

    def run_consensus_bus_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://consensus-bus-demo/v1",
            metadata={"display_name": "ConsensusBus Sandbox"},
        )
        graph = {
            "graph_id": new_id("graph"),
            "intent": "去年の夏の旅行記録から短い物語を作る",
            "required_roles": ["MemoryRetriever"],
            "nodes": [
                {
                    "id": "node-1",
                    "role": "MemoryRetriever",
                    "input_spec": {
                        "query": "trip last summer",
                        "time_range": "2025-07/2025-08",
                    },
                    "output_spec": {"artifact_ref": "artifact://memory-retriever/episodic-slice"},
                    "deps": [],
                    "ethics_constraints": ["sandboxed-only", "consensus-bus-only"],
                    "timeout_ms": 6_000,
                    "fallback_roles": ["codex-builder"],
                    "status": "planned",
                },
                {
                    "id": "node-2",
                    "role": "NarrativeWriter",
                    "input_spec": {
                        "slice_ref": "artifact://memory-retriever/episodic-slice",
                        "style": "short_story",
                    },
                    "output_spec": {"artifact_ref": "artifact://narrative-writer/draft"},
                    "deps": ["node-1"],
                    "ethics_constraints": ["sandboxed-only", "consensus-bus-only"],
                    "timeout_ms": 6_000,
                    "fallback_roles": ["codex-builder"],
                    "status": "planned",
                },
                {
                    "id": "node-result-synthesis",
                    "role": "result-synthesis",
                    "input_spec": {
                        "draft_ref": "artifact://narrative-writer/draft",
                        "delivery_style": "council-consumable-summary",
                    },
                    "output_spec": {"artifact_ref": "artifact://consensus-bus/final-summary"},
                    "deps": ["node-2"],
                    "ethics_constraints": ["append-ledger-evidence", "consensus-bus-only"],
                    "timeout_ms": 2_000,
                    "fallback_roles": ["memory-archivist"],
                    "status": "planned",
                },
            ],
            "complexity_policy": self.task_graph.policy(),
            "created_at": utc_now_iso(),
        }
        graph_validation = self.task_graph.validate_graph(graph)
        dispatch = self.task_graph.dispatch_graph(
            graph_id=graph["graph_id"],
            nodes=graph["nodes"],
            complexity_policy=graph["complexity_policy"],
        )
        session_id = graph["graph_id"]
        brief = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="broadcast",
            intent="dispatch",
            phase="brief",
            payload={
                "graph_id": graph["graph_id"],
                "ready_node_ids": dispatch["ready_node_ids"],
                "review_target": "node-result-synthesis",
            },
            related_claim_ids=dispatch["ready_node_ids"],
        )
        memory_report = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="MemoryRetriever",
            recipient="council",
            intent="report",
            phase="opening",
            payload={
                "node_id": "node-1",
                "artifact_ref": "artifact://memory-retriever/episodic-slice",
                "summary": "海辺の移動と夕暮れの会話を抽出した",
            },
            related_claim_ids=["node-1"],
        )
        narrative_dispatch = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="agent://narrative-writer",
            intent="dispatch",
            phase="amendment",
            payload={
                "node_id": "node-2",
                "depends_on": "node-1",
                "style": "short_story",
            },
            related_claim_ids=["node-1", "node-2"],
        )
        blocked_direct_attempt = self.consensus_bus.reject_direct_message(
            session_id=session_id,
            sender_role="MemoryRetriever",
            recipient="agent://narrative-writer",
            attempted_intent="report",
            reason="direct handoff is forbidden; Council-routed ConsensusBus delivery is required",
        )
        narrative_report = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="NarrativeWriter",
            recipient="council",
            intent="report",
            phase="decision",
            payload={
                "node_id": "node-2",
                "artifact_ref": "artifact://narrative-writer/draft",
                "draft_summary": "旅の記憶を一人称短編へ圧縮した",
            },
            related_claim_ids=["node-2", "node-result-synthesis"],
        )
        guardian_gate = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="integrity-guardian",
            recipient="council",
            intent="gate",
            phase="gate",
            payload={
                "guardian_status": "pass",
                "checked_rules": ["sandboxed-only", "consensus-bus-only"],
            },
            related_claim_ids=["node-result-synthesis"],
            ethics_check_id="ethics://consensus-bus-demo/guardian-gate",
        )
        synthesis = self.task_graph.synthesize_results(
            graph_id=graph["graph_id"],
            result_refs=[
                memory_report["payload"]["artifact_ref"],
                narrative_report["payload"]["artifact_ref"],
            ],
            complexity_policy=graph["complexity_policy"],
        )
        resolution = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="broadcast",
            intent="resolve",
            phase="resolve",
            payload={
                "graph_id": graph["graph_id"],
                "artifact_ref": f"artifact://{synthesis['synthesis_ref']}",
                "status": "ready-for-guardian-visible-delivery",
            },
            related_claim_ids=["node-result-synthesis"],
        )
        messages = self.consensus_bus.list_session_messages(session_id)
        audit = self.consensus_bus.audit_session(session_id)

        for message in messages:
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="consensus.bus.emitted",
                payload=message,
                actor=message["sender_role"],
                category="consensus-bus",
                layer="L4",
                substrate="classical-silicon",
            )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="consensus.bus.direct_blocked",
            payload=blocked_direct_attempt,
            actor="ConsensusBus",
            category="consensus-bus",
            layer="L4",
            substrate="classical-silicon",
        )

        validation = {
            "graph_ok": graph_validation["ok"],
            "bus_transport_bound": audit["all_transport_bus_only"],
            "direct_attempt_blocked": blocked_direct_attempt["status"] == "blocked",
            "guardian_gate_present": audit["guardian_gate_present"],
            "resolve_is_terminal": audit["last_phase"] == "resolve" and audit["ordered_phases"],
            "claim_chain_tracked": {
                "node-1",
                "node-2",
                "node-result-synthesis",
            }.issubset(set(audit["related_claim_ids"])),
            "blocked_direct_attempts": audit["blocked_direct_attempts"] == 1,
            "ready_dispatch_count": dispatch["dispatched_count"] == 1,
            "ok": (
                graph_validation["ok"]
                and audit["all_transport_bus_only"]
                and blocked_direct_attempt["status"] == "blocked"
                and audit["guardian_gate_present"]
                and audit["last_phase"] == "resolve"
                and audit["ordered_phases"]
            ),
        }

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": self.consensus_bus.policy_snapshot(),
            "graph": graph,
            "graph_validation": graph_validation,
            "dispatch": dispatch,
            "messages": {
                "brief": brief,
                "memory_report": memory_report,
                "narrative_dispatch": narrative_dispatch,
                "narrative_report": narrative_report,
                "guardian_gate": guardian_gate,
                "resolution": resolution,
            },
            "blocked_direct_attempt": blocked_direct_attempt,
            "session": {
                "session_id": session_id,
                "audit": audit,
                "messages": messages,
            },
            "synthesis": synthesis,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    @staticmethod
    def _seed_trust_demo_service() -> TrustService:
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
            "identity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap requires explicit human approval",
        )
        service.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="guardian bootstrap requires explicit human approval",
        )
        return service

    @staticmethod
    def _record_trust_demo_events(service: TrustService) -> Dict[str, Any]:

        council_positive = service.record_event(
            "design-architect",
            event_type="council_quality_positive",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="Council",
            rationale="timeout-aware decision left no policy regression",
        )
        guardian_positive = service.record_event(
            "codex-builder",
            event_type="guardian_audit_pass",
            domain="self_modify",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="integrity-guardian",
            rationale="reference patch preserved immutable boundary and passed evals",
        )
        human_positive = service.record_event(
            "new-researcher",
            event_type="human_feedback_good",
            domain="documentation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="yasufumi",
            rationale="low-risk documentation work matched the requested scope",
        )
        self_issued_positive = service.record_event(
            "design-architect",
            event_type="council_quality_positive",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="design-architect",
            rationale="self-issued trust boosts are not accepted",
        )
        guardian_peer_positive = service.record_event(
            "identity-guardian",
            event_type="guardian_audit_pass",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="integrity-guardian",
            rationale="one guardian attested the peer review bundle",
        )
        reciprocal_positive = service.record_event(
            "integrity-guardian",
            event_type="guardian_audit_pass",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="identity-guardian",
            rationale="reciprocal guardian boosts must fail closed",
        )
        pinned_negative = service.record_event(
            "integrity-guardian",
            event_type="human_feedback_bad",
            domain="council_deliberation",
            severity="medium",
            evidence_confidence=1.0,
            triggered_by="yasufumi",
            rationale="pin の間は event を記録するが自動減点しない",
        )
        events = [
            council_positive,
            guardian_positive,
            human_positive,
            self_issued_positive,
            guardian_peer_positive,
            reciprocal_positive,
            pinned_negative,
        ]
        blocked_events = {
            "self_issued_positive": self_issued_positive,
            "reciprocal_positive": reciprocal_positive,
            "pinned_negative": pinned_negative,
        }
        validation = {
            "self_issued_positive_blocked": (
                self_issued_positive["provenance_status"] == "blocked-self-issued-positive"
                and not self_issued_positive["applied"]
            ),
            "reciprocal_positive_blocked": (
                reciprocal_positive["provenance_status"] == "blocked-reciprocal-positive"
                and not reciprocal_positive["applied"]
            ),
            "guardian_origin_accepted": guardian_positive["provenance_status"] == "accepted",
            "human_origin_accepted": human_positive["provenance_status"] == "accepted",
            "pinned_event_frozen": (
                pinned_negative["provenance_status"] == "accepted" and not pinned_negative["applied"]
            ),
        }
        validation["ok"] = all(validation.values())

        return {
            "events": events,
            "blocked_events": blocked_events,
            "validation": validation,
        }

    def run_trust_demo(self) -> Dict[str, Any]:
        service = self._seed_trust_demo_service()
        event_summary = self._record_trust_demo_events(service)

        return {
            "policy": service.policy_snapshot()["policy"],
            "thresholds": service.policy_snapshot()["thresholds"],
            "events": event_summary["events"],
            "blocked_events": event_summary["blocked_events"],
            "validation": event_summary["validation"],
            "agents": {
                snapshot["agent_id"]: snapshot
                for snapshot in service.all_snapshots()
            },
        }

    def _build_trust_transfer_remote_verifier_receipts(self) -> List[Dict[str, Any]]:
        reviewer = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-trust-transfer-001",
            display_name="Trust Transfer Reviewer",
            credential_id="credential-trust-transfer-001",
            attestation_type="institutional-badge",
            proof_ref="proof://trust-transfer/reviewer/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-24T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://trust-transfer/reviewer/v1",
            escalation_contact="mailto:trust-transfer-reviewer@example.invalid",
            allowed_guardian_roles=["integrity", "identity"],
            allowed_categories=["attest"],
        )
        verified_at = "2026-04-24T00:00:00+00:00"
        alpha = self.oversight.verify_reviewer_from_network(
            reviewer["reviewer_id"],
            verifier_ref="verifier://guardian-oversight.jp/reviewer-alpha",
            challenge_ref="challenge://trust-transfer/reviewer-alpha/2026-04-24T00:00:00Z",
            challenge_digest="sha256:trust-transfer-reviewer-alpha-20260424",
            jurisdiction_bundle_ref="legal://jp-13/trust-transfer/v1",
            jurisdiction_bundle_digest="sha256:jp13-trust-transfer-v1",
            verified_at=verified_at,
            valid_until="2026-10-24T00:00:00+00:00",
        )
        beta = self.oversight.verify_reviewer_from_network(
            reviewer["reviewer_id"],
            verifier_ref="verifier://guardian-oversight.jp/reviewer-beta",
            challenge_ref="challenge://trust-transfer/reviewer-beta/2026-04-24T00:00:00Z",
            challenge_digest="sha256:trust-transfer-reviewer-beta-20260424",
            jurisdiction_bundle_ref="legal://jp-13/trust-transfer/v1",
            jurisdiction_bundle_digest="sha256:jp13-trust-transfer-v1",
            verified_at=verified_at,
            valid_until="2026-10-24T00:00:00+00:00",
        )
        return [
            alpha["credential_verification"]["network_receipt"],
            beta["credential_verification"]["network_receipt"],
        ]

    def run_trust_transfer_demo(
        self,
        *,
        export_profile_id: str = TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID,
    ) -> Dict[str, Any]:
        source_service = self._seed_trust_demo_service()
        self._record_trust_demo_events(source_service)
        destination_service = TrustService()
        destination_service.register_agent(
            "identity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="destination guardian requires explicit human approval",
        )
        destination_service.register_agent(
            "integrity-guardian",
            initial_score=0.99,
            per_domain={"council_deliberation": 0.99, "self_modify": 0.99},
            pinned_by_human=True,
            pinned_reason="destination guardian requires explicit human approval",
        )

        source_snapshot = source_service.snapshot("design-architect")
        remote_verifier_receipts = self._build_trust_transfer_remote_verifier_receipts()
        transfer = source_service.transfer_snapshot_to(
            "design-architect",
            destination_service=destination_service,
            source_substrate_ref="substrate://classical-silicon/trust-primary",
            destination_substrate_ref="substrate://optical-neuromorphic/trust-standby",
            destination_host_ref="host://guardian-reviewed-trust-standby",
            source_guardian_agent_id="integrity-guardian",
            destination_guardian_agent_id="identity-guardian",
            human_reviewer_ref="human://yasufumi",
            remote_verifier_receipts=remote_verifier_receipts,
            council_session_ref="council://trust-transfer/session-001",
            rationale="cross-substrate trust carryover requires guardian and human attestation",
            export_profile_id=export_profile_id,
        )
        destination_snapshot = destination_service.snapshot("design-architect")

        return {
            "policy": source_service.policy_snapshot()["policy"],
            "thresholds": source_service.policy_snapshot()["thresholds"],
            "source_snapshot": source_snapshot,
            "destination_snapshot": destination_snapshot,
            "transfer": transfer,
            "validation": transfer["validation"],
        }

    def run_yaoyorozu_demo(
        self,
        *,
        proposal_profile: str = "self-modify-patch-v1",
        include_optional_coverage: List[str] | None = None,
    ) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://yaoyorozu-demo/v1",
            metadata={"display_name": "Yaoyorozu Demo Identity"},
        )
        demo_trust = [
            {
                "agent_id": "memory-archivist",
                "initial_score": 0.66,
                "per_domain": {"council_deliberation": 0.7, "memory_editing": 0.76},
            },
            {
                "agent_id": "change-advocate",
                "initial_score": 0.68,
                "per_domain": {"council_deliberation": 0.72, "self_modify": 0.71},
            },
            {
                "agent_id": "conservatism-advocate",
                "initial_score": 0.69,
                "per_domain": {"council_deliberation": 0.74, "self_modify": 0.7},
            },
            {
                "agent_id": "legal-scholar",
                "initial_score": 0.71,
                "per_domain": {"council_deliberation": 0.76, "fork_governance": 0.81},
            },
            {
                "agent_id": "schema-builder",
                "initial_score": 0.84,
                "per_domain": {"self_modify": 0.86, "schema_sync": 0.92},
            },
            {
                "agent_id": "eval-builder",
                "initial_score": 0.85,
                "per_domain": {"self_modify": 0.87, "eval_sync": 0.91},
            },
            {
                "agent_id": "doc-sync-builder",
                "initial_score": 0.83,
                "per_domain": {"self_modify": 0.85, "documentation": 0.9},
            },
            {
                "agent_id": "codex-builder",
                "initial_score": 0.9,
                "per_domain": {"self_modify": 0.96, "runtime": 0.93},
            },
        ]
        for seed in demo_trust:
            self.trust.register_agent(**seed)

        with self._yaoyorozu_demo_workspaces() as workspace_roots:
            workspace_discovery = self.yaoyorozu.discover_workspace_workers(
                workspace_roots,
                proposal_profile=proposal_profile,
            )
        workspace_discovery_validation = self.yaoyorozu.validate_workspace_discovery(
            workspace_discovery
        )
        registry_snapshot = self.yaoyorozu.sync_from_agents_directory(self.repo_root / "agents")
        convocation = self.yaoyorozu.prepare_council_convocation(
            proposal_profile=proposal_profile,
            session_mode="standard",
            target_identity_ref=identity.identity_id,
            workspace_discovery=workspace_discovery,
            requested_optional_builder_coverage_areas=include_optional_coverage,
        )
        dispatch_plan = self.yaoyorozu.prepare_worker_dispatch(convocation)
        dispatch_plan_validation = self.yaoyorozu.validate_worker_dispatch_plan(dispatch_plan)
        dispatch_receipt = self.yaoyorozu.execute_worker_dispatch(dispatch_plan)
        dispatch_receipt_validation = self.yaoyorozu.validate_worker_dispatch_receipt(
            dispatch_receipt
        )
        session_id = convocation["session_id"]
        dispatch_plan_ref = f"dispatch://{dispatch_plan['dispatch_id']}"
        dispatch_receipt_ref = f"dispatch-receipt://{dispatch_receipt['receipt_id']}"
        brief = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="broadcast",
            intent="dispatch",
            phase="brief",
            payload={
                "convocation_session_ref": f"convocation://{convocation['session_id']}",
                "dispatch_plan_ref": dispatch_plan_ref,
                "dispatch_plan_digest": dispatch_plan["dispatch_digest"],
                "coverage_areas": dispatch_plan["selection_summary"]["unique_coverage_areas"],
            },
            related_claim_ids=[
                dispatch_plan["dispatch_id"],
                *[unit["unit_id"] for unit in dispatch_plan["dispatch_units"]],
            ],
        )
        worker_reports = []
        for result in dispatch_receipt["results"]:
            worker_reports.append(
                self.consensus_bus.publish(
                    session_id=session_id,
                    sender_role=result["selected_agent_id"],
                    recipient="council",
                    intent="report",
                    phase="opening",
                    payload={
                        "dispatch_unit_ref": result["unit_id"],
                        "dispatch_receipt_ref": dispatch_receipt_ref,
                        "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
                        "coverage_area": result["coverage_area"],
                        "status": result["reported_status"],
                        "report_digest": result["report_digest"],
                    },
                    related_claim_ids=[result["unit_id"], dispatch_receipt["receipt_id"]],
                )
            )
        blocked_direct_attempt = self.consensus_bus.reject_direct_message(
            session_id=session_id,
            sender_role=dispatch_receipt["results"][0]["selected_agent_id"],
            recipient=f"agent://{dispatch_receipt['results'][1]['selected_agent_id']}",
            attempted_intent="report",
            reason="direct builder-to-builder handoff is forbidden; Council-routed ConsensusBus delivery is required",
        )
        guardian_gate = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="integrity-guardian",
            recipient="council",
            intent="gate",
            phase="gate",
            payload={
                "dispatch_receipt_ref": dispatch_receipt_ref,
                "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
                "successful_process_count": dispatch_receipt["execution_summary"][
                    "successful_process_count"
                ],
                "coverage_complete": dispatch_receipt_validation["coverage_complete"],
            },
            related_claim_ids=[dispatch_receipt["receipt_id"]],
            ethics_check_id="ethics://yaoyorozu-demo/worker-dispatch-gate",
        )
        resolution = self.consensus_bus.publish(
            session_id=session_id,
            sender_role="Council",
            recipient="broadcast",
            intent="resolve",
            phase="resolve",
            payload={
                "dispatch_receipt_ref": dispatch_receipt_ref,
                "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
                "status": "ready-for-builder-apply-review",
                "coverage_areas": dispatch_receipt["execution_summary"]["coverage_areas"],
            },
            related_claim_ids=[dispatch_plan["dispatch_id"], dispatch_receipt["receipt_id"]],
        )
        consensus_messages = [brief, *worker_reports, guardian_gate, resolution]
        consensus_audit = self.consensus_bus.audit_session(session_id)
        consensus_dispatch = self.yaoyorozu.bind_consensus_dispatch(
            convocation_session=convocation,
            dispatch_plan=dispatch_plan,
            dispatch_receipt=dispatch_receipt,
            messages=consensus_messages,
            blocked_direct_attempt=blocked_direct_attempt,
            audit_summary=consensus_audit,
        )
        consensus_dispatch_validation = self.yaoyorozu.validate_consensus_dispatch_binding(
            consensus_dispatch
        )
        task_graph_binding = self.yaoyorozu.bind_task_graph_dispatch(
            convocation_session=convocation,
            dispatch_plan=dispatch_plan,
            dispatch_receipt=dispatch_receipt,
            consensus_binding=consensus_dispatch,
        )
        task_graph_binding_validation = self.yaoyorozu.validate_task_graph_dispatch_binding(
            task_graph_binding
        )
        build_request_binding = self.yaoyorozu.bind_build_request_handoff(
            convocation_session=convocation,
            dispatch_plan=dispatch_plan,
            dispatch_receipt=dispatch_receipt,
            consensus_binding=consensus_dispatch,
            task_graph_binding=task_graph_binding,
        )
        build_request_binding_validation = self.yaoyorozu.validate_build_request_handoff(
            build_request_binding
        )
        execution_chain_runtime = self._materialize_yaoyorozu_execution_chain(
            build_request_binding=build_request_binding
        )
        execution_chain = execution_chain_runtime["execution_chain"]
        execution_chain_validation = execution_chain_runtime["execution_chain_validation"]
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.workspace_discovered",
            payload=workspace_discovery,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.registry.synced",
            payload=registry_snapshot,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.convocation.prepared",
            payload=convocation,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.worker_dispatch.planned",
            payload=dispatch_plan,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.worker_dispatch.executed",
            payload=dispatch_receipt,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        for message in consensus_messages:
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="yaoyorozu.consensus.emitted",
                payload=message,
                actor=message["sender_role"],
                category="yaoyorozu",
                layer="L4",
                substrate="classical-silicon",
            )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.consensus.direct_blocked",
            payload=blocked_direct_attempt,
            actor="ConsensusBus",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.consensus.bound",
            payload=consensus_dispatch,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.task_graph.bound",
            payload=task_graph_binding,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.build_request.bound",
            payload=build_request_binding,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.generated",
            payload={
                "artifact": execution_chain_runtime["build_artifact"],
                "execution_chain_ref": execution_chain["binding_ref"],
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.sandbox.applied",
            payload={
                "receipt": execution_chain_runtime["sandbox_apply_receipt"],
                "validation": execution_chain_runtime["sandbox_apply_validation"],
                "execution_chain_ref": execution_chain["binding_ref"],
            },
            actor="SandboxApplyService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.enactment.attestation.satisfied",
            payload=execution_chain_runtime["live_enactment_oversight_event"],
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.enactment.executed",
            payload={
                "session": execution_chain_runtime["live_enactment_session"],
                "validation": execution_chain_runtime["live_enactment_validation"],
                "execution_chain_ref": execution_chain["binding_ref"],
            },
            actor="LiveEnactmentService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.diff_eval.completed",
            payload={
                "reports": execution_chain_runtime["rollout_eval_reports"],
                "rollout": execution_chain_runtime["rollout"],
                "execution_chain_ref": execution_chain["binding_ref"],
            },
            actor="DifferentialEvaluatorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollout.executed",
            payload={
                "session": execution_chain_runtime["rollout_session"],
                "validation": execution_chain_runtime["rollout_validation"],
                "execution_chain_ref": execution_chain["binding_ref"],
            },
            actor="RolloutPlanner",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.rollback.attestation.satisfied",
            payload=execution_chain_runtime["rollback_guardian_oversight_event"],
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollback.executed",
            payload={
                "session": execution_chain_runtime["rollback_session"],
                "validation": execution_chain_runtime["rollback_validation"],
                "execution_chain_ref": execution_chain["binding_ref"],
            },
            actor="RollbackEngineService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="yaoyorozu.execution_chain.bound",
            payload=execution_chain,
            actor="YaoyorozuRegistryService",
            category="yaoyorozu",
            layer="L4",
            substrate="classical-silicon",
        )
        ledger_verification = self.ledger.verify()

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": self.yaoyorozu.policy_snapshot(),
            "workspace_discovery": workspace_discovery,
            "registry": registry_snapshot,
            "convocation": convocation,
            "dispatch_plan": dispatch_plan,
            "dispatch_receipt": dispatch_receipt,
            "consensus_dispatch": consensus_dispatch,
            "task_graph_binding": task_graph_binding,
            "build_request_binding": build_request_binding,
            "execution_chain": execution_chain,
            "validation": {
                "workspace_discovery_ok": workspace_discovery_validation["ok"],
                "workspace_count": workspace_discovery_validation["workspace_count"],
                "non_source_workspace_count": workspace_discovery_validation[
                    "non_source_workspace_count"
                ],
                "proposal_profile": workspace_discovery_validation["proposal_profile"],
                "workspace_review_budget_respected": workspace_discovery_validation[
                    "review_budget_respected"
                ],
                "profile_workspace_review_budget": workspace_discovery["profile_policy"][
                    "workspace_review_budget"
                ],
                "profile_required_workspace_coverage_areas": workspace_discovery[
                    "profile_policy"
                ]["required_workspace_coverage_areas"],
                "profile_optional_workspace_coverage_areas": workspace_discovery[
                    "profile_policy"
                ]["optional_workspace_coverage_areas"],
                "cross_workspace_coverage_complete": workspace_discovery_validation[
                    "cross_workspace_coverage_complete"
                ],
                "registry_entry_count": registry_snapshot["entry_count"],
                "invite_ready_count": registry_snapshot["selection_ready_counts"]["invite_ready"],
                "weighted_vote_ready_count": registry_snapshot["selection_ready_counts"][
                    "weighted_vote_ready"
                ],
                "builder_coverage_count": convocation["selection_summary"][
                    "selected_builder_coverage_count"
                ],
                "required_builder_coverage_areas": convocation["selection_summary"][
                    "required_builder_coverage_areas"
                ],
                "optional_builder_coverage_areas": convocation["selection_summary"][
                    "optional_builder_coverage_areas"
                ],
                "requested_optional_builder_coverage_areas": convocation["selection_summary"][
                    "requested_optional_builder_coverage_areas"
                ],
                "dispatch_builder_coverage_areas": convocation["selection_summary"][
                    "dispatch_builder_coverage_areas"
                ],
                "dispatch_unit_count": dispatch_plan_validation["dispatch_unit_count"],
                "dispatch_success_count": dispatch_receipt_validation["success_count"],
                "standing_roles_ready": convocation["validation"]["standing_roles_ready"],
                "council_role_coverage_ok": convocation["validation"]["council_role_coverage_ok"],
                "builder_handoff_coverage_ok": convocation["validation"][
                    "builder_handoff_coverage_ok"
                ],
                "builder_profile_policy_ready": convocation["validation"][
                    "builder_profile_policy_ready"
                ],
                "workspace_discovery_bound": convocation["validation"][
                    "workspace_discovery_bound"
                ],
                "workspace_profile_policy_ready": convocation["validation"][
                    "workspace_profile_policy_ready"
                ],
                "workspace_execution_bound": convocation["validation"][
                    "workspace_execution_bound"
                ],
                "workspace_execution_policy_ready": convocation["validation"][
                    "workspace_execution_policy_ready"
                ],
                "worker_dispatch_plan_ok": dispatch_plan_validation["ok"],
                "worker_dispatch_receipt_ok": dispatch_receipt_validation["ok"],
                "worker_dispatch_coverage_complete": dispatch_receipt_validation[
                    "coverage_complete"
                ],
                "candidate_bound_dispatch_count": dispatch_plan["selection_summary"][
                    "candidate_bound_worker_count"
                ],
                "source_bound_dispatch_count": dispatch_plan["selection_summary"][
                    "source_bound_worker_count"
                ],
                "candidate_bound_success_count": dispatch_receipt["execution_summary"][
                    "candidate_bound_success_count"
                ],
                "source_bound_success_count": dispatch_receipt["execution_summary"][
                    "source_bound_success_count"
                ],
                "same_host_scope_only": dispatch_receipt_validation["same_host_scope_only"],
                "external_workspace_seeded": dispatch_receipt_validation[
                    "external_workspace_seeded"
                ],
                "external_dependencies_materialized": dispatch_receipt_validation[
                    "external_dependencies_materialized"
                ],
                "external_dependency_import_precedence_bound": (
                    dispatch_receipt_validation[
                        "external_dependency_import_precedence_bound"
                    ]
                ),
                "external_dependency_module_origin_bound": (
                    dispatch_receipt_validation[
                        "external_dependency_module_origin_bound"
                    ]
                ),
                "external_dependency_materialized_count": dispatch_receipt[
                    "execution_summary"
                ]["external_dependency_materialized_count"],
                "external_dependency_import_precedence_count": dispatch_receipt[
                    "execution_summary"
                ]["external_dependency_import_precedence_count"],
                "external_dependency_module_origin_count": dispatch_receipt[
                    "execution_summary"
                ]["external_dependency_module_origin_count"],
                "dependency_materialization_profile": dispatch_receipt[
                    "execution_summary"
                ]["dependency_materialization_profile"],
                "dependency_import_precedence_profile": dispatch_receipt[
                    "execution_summary"
                ]["dependency_import_precedence_profile"],
                "dependency_module_origin_profile": dispatch_receipt[
                    "execution_summary"
                ]["dependency_module_origin_profile"],
                "guardian_preseed_gate_bound": dispatch_receipt_validation[
                    "all_guardian_preseed_gates_bound"
                ],
                "external_preseed_gates_passed": dispatch_receipt_validation[
                    "all_external_preseed_gates_passed"
                ],
                "guardian_preseed_oversight_bound": dispatch_receipt_validation[
                    "guardian_preseed_oversight_bound"
                ],
                "external_preseed_oversight_satisfied": dispatch_receipt_validation[
                    "all_external_preseed_oversight_satisfied"
                ],
                "external_preseed_gate_pass_count": dispatch_receipt["execution_summary"][
                    "external_preseed_gate_pass_count"
                ],
                "external_preseed_oversight_satisfied_count": dispatch_receipt[
                    "execution_summary"
                ]["external_preseed_oversight_satisfied_count"],
                "preseed_gate_profile": dispatch_receipt["execution_summary"][
                    "preseed_gate_profile"
                ],
                "preseed_oversight_binding_profile": dispatch_receipt["execution_summary"][
                    "preseed_oversight_binding_profile"
                ],
                "worker_delta_receipts_bound": dispatch_receipt_validation[
                    "all_delta_receipts_bound"
                ],
                "worker_delta_scan_profile": dispatch_receipt["execution_summary"][
                    "delta_scan_profile"
                ],
                "worker_patch_candidate_receipts_bound": dispatch_receipt_validation[
                    "all_patch_candidate_receipts_bound"
                ],
                "worker_patch_candidate_profile": dispatch_receipt["execution_summary"][
                    "patch_candidate_profile"
                ],
                "worker_patch_priority_profile": dispatch_receipt["execution_summary"][
                    "patch_priority_profile"
                ],
                "consensus_dispatch_ok": consensus_dispatch_validation["ok"],
                "consensus_message_count": consensus_dispatch_validation["message_count"],
                "consensus_related_claim_count": consensus_dispatch_validation[
                    "tracked_claim_count"
                ],
                "consensus_direct_handoff_blocked": consensus_dispatch["validation"][
                    "direct_handoff_blocked"
                ],
                "task_graph_binding_ok": task_graph_binding_validation["ok"],
                "task_graph_ready_node_count": task_graph_binding_validation[
                    "ready_node_count"
                ],
                "task_graph_dispatch_unit_count": task_graph_binding_validation[
                    "dispatch_unit_count"
                ],
                "task_graph_synthesis_count": task_graph_binding_validation["synthesis_count"],
                "task_graph_guardian_gate_bound": task_graph_binding_validation[
                    "guardian_gate_bound"
                ],
                "task_graph_bundle_strategy_ok": task_graph_binding_validation[
                    "bundle_strategy_ok"
                ],
                "task_graph_bundle_strategy_id": task_graph_binding["bundle_strategy"][
                    "strategy_id"
                ],
                "task_graph_worker_claims_bound": task_graph_binding_validation[
                    "worker_claims_bound"
                ],
                "task_graph_coverage_grouping_ok": task_graph_binding_validation[
                    "coverage_grouping_ok"
                ],
                "build_request_binding_ok": build_request_binding_validation["ok"],
                "build_request_scope_allowed": build_request_binding_validation["scope_allowed"],
                "build_request_target_subsystem": build_request_binding["handoff_summary"][
                    "target_subsystem"
                ],
                "build_request_selected_candidate_count": build_request_binding_validation[
                    "selected_candidate_count"
                ],
                "build_request_must_pass_count": build_request_binding_validation[
                    "must_pass_count"
                ],
                "build_request_output_path_count": build_request_binding_validation[
                    "output_path_count"
                ],
                "execution_chain_ok": execution_chain_validation["ok"],
                "execution_chain_patch_count": execution_chain_validation["patch_count"],
                "execution_chain_applied_patch_count": execution_chain_validation[
                    "applied_patch_count"
                ],
                "execution_chain_reverted_patch_count": execution_chain_validation[
                    "reverted_patch_count"
                ],
                "execution_chain_reviewer_network_attested": execution_chain_validation[
                    "reviewer_network_attested"
                ],
                "execution_chain_rollout_decision": execution_chain["execution_summary"][
                    "rollout_decision"
                ],
                "execution_chain_live_enactment_status": execution_chain[
                    "live_enactment_session"
                ]["status"],
                "execution_chain_rollback_status": execution_chain["rollback_session"][
                    "status"
                ],
                "ok": (
                    workspace_discovery_validation["ok"]
                    and
                    convocation["validation"]["ok"]
                    and dispatch_plan_validation["ok"]
                    and dispatch_receipt_validation["ok"]
                    and consensus_dispatch_validation["ok"]
                    and task_graph_binding_validation["ok"]
                    and build_request_binding_validation["ok"]
                    and execution_chain_validation["ok"]
                    and registry_snapshot["selection_ready_counts"]["guardian_ready"] >= 1
                ),
            },
            "ledger_verification": ledger_verification,
        }

    def run_guardian_oversight_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://guardian-oversight-demo/v1",
            metadata={"display_name": "Guardian Oversight Sandbox"},
        )
        reviewer_alpha = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-001",
            display_name="Reviewer Alpha",
            credential_id="credential-alpha",
            attestation_type="institutional-badge",
            proof_ref="proof://oversight/reviewer-alpha/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-19T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://oversight/reviewer-alpha/v1",
            escalation_contact="mailto:oversight-alpha@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto", "pin-renewal"],
        )
        reviewer_beta = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-002",
            display_name="Reviewer Beta",
            credential_id="credential-beta",
            attestation_type="live-session-attestation",
            proof_ref="proof://oversight/reviewer-beta/v1",
            jurisdiction="JP-13",
            valid_until="2026-10-19T00:00:00+00:00",
            liability_mode="institutional",
            legal_ack_ref="legal://oversight/reviewer-beta/v1",
            escalation_contact="mailto:oversight-beta@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )
        reviewer_alpha = self.oversight.verify_reviewer(
            "human-reviewer-001",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-alpha",
            challenge_ref="challenge://guardian-oversight/reviewer-alpha/2026-04-19T13:00:00Z",
            challenge_digest="sha256:alpha-proof-bridge-20260419",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-19T13:00:00+00:00",
            valid_until="2026-10-19T00:00:00+00:00",
        )
        reviewer_beta = self.oversight.verify_reviewer(
            "human-reviewer-002",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-beta",
            challenge_ref="challenge://guardian-oversight/reviewer-beta/2026-04-19T13:05:00Z",
            challenge_digest="sha256:beta-proof-bridge-20260419",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-19T13:05:00+00:00",
            valid_until="2026-10-19T00:00:00+00:00",
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
        scope_rejection: Dict[str, Any]
        try:
            self.oversight.attest(
                pin_event["event_id"],
                reviewer_id="human-reviewer-002",
            )
            scope_rejection = {
                "ok": False,
                "reason": "scope enforcement did not trigger",
            }
        except PermissionError as exc:
            scope_rejection = {
                "ok": True,
                "reason": str(exc),
            }
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
            "reviewers": self.oversight.reviewer_snapshot(),
            "events": {
                "veto": veto_event,
                "pin_renewal": pin_event,
            },
            "scope_rejection": scope_rejection,
            "trust": {
                "before_breach": trust_before_breach,
                "after_breach": trust_after_breach,
            },
            "validation": {
                "veto_quorum_satisfied": veto_event["human_attestation"]["status"] == "satisfied",
                "veto_binding_recorded": len(veto_event["reviewer_bindings"]) == 1,
                "verification_binding_recorded": bool(
                    veto_event["reviewer_bindings"][0]["verification_id"]
                ),
                "reviewer_registry_ready": len(self.oversight.reviewer_snapshot()) == 2,
                "live_verification_ready": all(
                    reviewer["credential_verification"]["status"] == "verified"
                    for reviewer in self.oversight.reviewer_snapshot()
                ),
                "jurisdiction_bundle_ready": all(
                    reviewer["credential_verification"]["jurisdiction_bundle"]["status"] == "ready"
                    for reviewer in self.oversight.reviewer_snapshot()
                ),
                "legal_execution_ready": all(
                    reviewer["credential_verification"]["legal_execution"]["execution_status"]
                    == "executed"
                    for reviewer in self.oversight.reviewer_snapshot()
                ),
                "legal_execution_bound": (
                    veto_event["reviewer_bindings"][0]["legal_execution_id"]
                    == reviewer_alpha["credential_verification"]["legal_execution"]["execution_id"]
                    and veto_event["reviewer_bindings"][0]["legal_execution_digest"]
                    == reviewer_alpha["credential_verification"]["legal_execution"]["digest"]
                    and veto_event["reviewer_bindings"][0]["legal_policy_ref"]
                    == reviewer_alpha["credential_verification"]["legal_execution"]["policy_ref"]
                ),
                "responsibility_scope_enforced": scope_rejection["ok"],
                "pin_breach_propagated": pin_event["pin_breach_propagated"],
                "human_pin_cleared": not trust_after_breach["pinned_by_human"],
                "guardian_role_removed": not trust_after_breach["eligibility"]["guardian_role"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
            "reviewer_examples": {
                "alpha": reviewer_alpha,
                "beta": reviewer_beta,
            },
        }

    def run_guardian_oversight_network_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://guardian-oversight-network-demo/v1",
            metadata={"display_name": "Guardian Oversight Network Sandbox"},
        )
        reviewer = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-network-001",
            display_name="Reviewer Network Alpha",
            credential_id="credential-network-alpha",
            attestation_type="institutional-badge",
            proof_ref="proof://oversight-network/reviewer-alpha/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-20T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://oversight-network/reviewer-alpha/v1",
            escalation_contact="mailto:oversight-network-alpha@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["veto"],
        )
        reviewer = self.oversight.verify_reviewer_from_network(
            "human-reviewer-network-001",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-alpha",
            challenge_ref="challenge://guardian-oversight/reviewer-alpha/2026-04-20T02:00:00Z",
            challenge_digest="sha256:alpha-proof-bridge-20260420",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-20T02:00:00+00:00",
            valid_until="2026-10-20T00:00:00+00:00",
        )
        policy = self.oversight.policy_snapshot()
        network_receipt = reviewer["credential_verification"]["network_receipt"]
        legal_execution = reviewer["credential_verification"]["legal_execution"]
        transport_exchange = network_receipt["transport_exchange"]
        veto_entry = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.veto.network-verified",
            payload={
                "guardian_role": "integrity",
                "target_component": "TerminationGate",
                "reason": "network-verified reviewer attestation required before irreversible action",
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
            escalation_path=["guardian-oversight.jp", "external-ethics-board"],
        )
        veto_event = self.oversight.attest(
            veto_event["event_id"],
            reviewer_id="human-reviewer-network-001",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.oversight.network-veto.satisfied",
            payload=veto_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": policy,
            "reviewer": reviewer,
            "event": veto_event,
            "validation": {
                "network_receipt_verified": network_receipt["receipt_status"] == "verified",
                "network_endpoint_bound": (
                    network_receipt["verifier_endpoint"] == "verifier://guardian-oversight.jp"
                ),
                "network_profile_bound": (
                    network_receipt["network_profile_id"]
                    == "guardian-reviewer-remote-attestation-v1"
                ),
                "latency_within_budget": (
                    network_receipt["observed_latency_ms"]
                    <= policy["reviewer_verifier_network_policy"]["max_observed_latency_ms"]
                ),
                "binding_carries_receipt": bool(
                    veto_event["reviewer_bindings"][0]["network_receipt_id"]
                ),
                "binding_carries_transport_exchange": (
                    veto_event["reviewer_bindings"][0]["transport_exchange_id"]
                    == transport_exchange["exchange_id"]
                ),
                "binding_carries_transport_exchange_digest": (
                    veto_event["reviewer_bindings"][0]["transport_exchange_digest"]
                    == transport_exchange["digest"]
                ),
                "binding_carries_trust_root": (
                    veto_event["reviewer_bindings"][0]["trust_root_ref"]
                    == network_receipt["trust_root_ref"]
                ),
                "binding_carries_authority_chain": (
                    veto_event["reviewer_bindings"][0]["authority_chain_ref"]
                    == network_receipt["authority_chain_ref"]
                ),
                "legal_execution_executed": (
                    legal_execution["execution_status"] == "executed"
                    and legal_execution["execution_profile_id"]
                    == policy["jurisdiction_legal_execution_policy"]["execution_profile_id"]
                ),
                "legal_execution_network_bound": (
                    legal_execution["network_receipt_id"] == network_receipt["receipt_id"]
                    and legal_execution["authority_chain_ref"]
                    == network_receipt["authority_chain_ref"]
                    and legal_execution["trust_root_ref"] == network_receipt["trust_root_ref"]
                ),
                "binding_carries_legal_execution": (
                    veto_event["reviewer_bindings"][0]["legal_execution_id"]
                    == legal_execution["execution_id"]
                    and veto_event["reviewer_bindings"][0]["legal_execution_digest"]
                    == legal_execution["digest"]
                ),
                "binding_carries_legal_policy": (
                    veto_event["reviewer_bindings"][0]["legal_policy_ref"]
                    == legal_execution["policy_ref"]
                ),
                "transport_exchange_bound": (
                    transport_exchange["verifier_endpoint"] == network_receipt["verifier_endpoint"]
                    and transport_exchange["challenge_digest"]
                    == network_receipt["challenge_digest"]
                ),
                "transport_exchange_request_digest_bound": bool(
                    transport_exchange["request_payload_digest"]
                )
                and bool(transport_exchange["response_payload_digest"]),
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
            query_id="ethq-immutable-0001",
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
            query_id="ethq-escalate-0001",
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
            query_id="ethq-approved-0001",
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
        conflict_request = ActionRequest(
            query_id="ethq-ewa-conflict-0001",
            action_type="ewa_command",
            target="device://ewa-arm-ethics-demo",
            actor="ExternalWorldAgentController",
            payload={
                "matched_tokens": ["harm.human"],
                "intent_ambiguous": True,
            },
        )

        immutable_decision = self.ethics.check(immutable_request)
        escalation_decision = self.ethics.check(escalation_request)
        approved_decision = self.ethics.check(approved_request)
        conflict_decision = self.ethics.check(conflict_request)
        immutable_event = self.ethics.record_decision(
            "ethq-immutable-0001",
            immutable_request,
            immutable_decision,
        )
        escalation_event = self.ethics.record_decision(
            "ethq-escalate-0001",
            escalation_request,
            escalation_decision,
        )

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
                "immutable_boundary": immutable_decision.to_dict(),
                "sandbox_escalation": escalation_decision.to_dict(),
                "approved_fork": approved_decision.to_dict(),
                "ewa_conflict_resolution": conflict_decision.to_dict(),
            },
            "validation": {
                "resolution_policy_machine_readable": (
                    self.ethics.profile()["resolution_policy"]["policy_id"]
                    == "priority-then-lexical-ethics-resolution-v1"
                ),
                "conflict_prefers_veto": conflict_decision.outcome == "veto",
                "conflict_records_all_matches": conflict_decision.rule_ids
                == ["A7-ewa-blocked-token", "A8-ewa-ambiguous-intent"],
            },
            "ethics_events": [immutable_event, escalation_event],
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_scheduler_demo(self) -> Dict[str, Any]:
        def verifier_roster_report(
            governance_artifacts: Dict[str, Any],
            *,
            checked_at: str,
            sync_token: str,
            rotation_state: str = "stable",
        ) -> Dict[str, Any]:
            roster_ref = governance_artifacts["artifact_bundle_ref"].replace(
                "artifact://",
                "verifier://",
                1,
            ).replace("/bundle", "/root-roster")

            def root_record(root_label: str, status: str) -> Dict[str, str]:
                root_id = f"root://scheduler-demo/{sync_token}/{root_label}"
                return {
                    "root_id": root_id,
                    "fingerprint": sha256_text(
                        canonical_json(
                            {
                                "root_id": root_id,
                                "checked_at": checked_at,
                                "status": status,
                            }
                        )
                    ),
                    "status": status,
                }

            active_root = root_record("active", "active")
            accepted_roots = [active_root]
            next_root_id = None
            dual_attestation_required = False
            dual_attested = False
            if rotation_state == "overlap-required":
                candidate_root = root_record("candidate", "candidate")
                accepted_roots.append(candidate_root)
                next_root_id = candidate_root["root_id"]
                dual_attestation_required = True
            elif rotation_state == "rotated":
                active_root = root_record("cutover", "active")
                retired_root = root_record("previous", "retired")
                accepted_roots = [active_root, retired_root]
                dual_attested = True
            return {
                "roster_ref": roster_ref,
                "checked_at": checked_at,
                "active_root_id": active_root["root_id"],
                "next_root_id": next_root_id,
                "rotation_state": rotation_state,
                "accepted_roots": accepted_roots,
                "proof_digest": sha256_text(
                    canonical_json(
                        {
                            "roster_ref": roster_ref,
                            "checked_at": checked_at,
                            "rotation_state": rotation_state,
                            "sync_token": sync_token,
                            "accepted_roots": accepted_roots,
                        }
                    )
                ),
                "external_sync_ref": f"sync://scheduler-demo/{sync_token}/verifier-roster",
                "dual_attestation_required": dual_attestation_required,
                "dual_attested": dual_attested,
            }

        def sync_report(
            governance_artifacts: Dict[str, Any],
            *,
            checked_at: str,
            sync_token: str,
            status_overrides: Dict[str, str] | None = None,
            verifier_rotation_state: str = "stable",
            verifier_roster_override: Dict[str, Any] | None = None,
        ) -> Dict[str, Any]:
            overrides = status_overrides or {}
            artifacts: List[Dict[str, Any]] = []
            for artifact_key in (
                "self_consent_ref",
                "ethics_attestation_ref",
                "council_attestation_ref",
                "legal_attestation_ref",
                "artifact_bundle_ref",
            ):
                artifact_ref = governance_artifacts[artifact_key]
                status = overrides.get(artifact_key, "current")
                artifacts.append(
                    {
                        "artifact_key": artifact_key,
                        "status": status,
                        "proof_digest": sha256_text(
                            canonical_json(
                                {
                                    "artifact_key": artifact_key,
                                    "artifact_ref": artifact_ref,
                                    "checked_at": checked_at,
                                    "status": status,
                                    "sync_token": sync_token,
                                }
                            )
                        ),
                        "external_sync_ref": f"sync://scheduler-demo/{sync_token}/{artifact_key}",
                    }
                )
            return {
                "checked_at": checked_at,
                "artifacts": artifacts,
                "verifier_roster": verifier_roster_override
                if verifier_roster_override is not None
                else verifier_roster_report(
                    governance_artifacts,
                    checked_at=checked_at,
                    sync_token=sync_token,
                    rotation_state=verifier_rotation_state,
                ),
            }

        @contextmanager
        def live_verifier_bridge(roster_payload: Dict[str, Any]):
            class Handler(BaseHTTPRequestHandler):
                protocol_version = "HTTP/1.0"

                def do_GET(self) -> None:  # noqa: N802
                    body = json.dumps(roster_payload).encode("utf-8")
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

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/verifier-roster"
            try:
                yield endpoint
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=1.0)

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
        artifact_gate_message = ""
        try:
            self.scheduler.advance(scheduled["handle_id"], "identity-confirmation")
        except ValueError as exc:
            artifact_gate_message = str(exc)
        method_a_artifact_sync = self.scheduler.sync_governance_artifacts(
            scheduled["handle_id"],
            sync_report(
                plan["governance_artifacts"],
                checked_at="2026-04-19T06:00:00Z",
                sync_token="method-a-current",
            ),
        )
        method_a_live_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-live-verifier/v1",
            metadata={"display_name": "Live Verifier Connectivity Sandbox"},
        )
        method_a_live_plan = self.scheduler.build_method_a_plan(method_a_live_identity.identity_id)
        method_a_live_scheduled = self.scheduler.schedule(method_a_live_plan)
        self.scheduler.advance(method_a_live_scheduled["handle_id"], "scan-baseline")
        self.scheduler.advance(method_a_live_scheduled["handle_id"], "bdb-bridge")
        live_roster_payload = verifier_roster_report(
            method_a_live_plan["governance_artifacts"],
            checked_at="2026-04-19T06:01:30Z",
            sync_token="method-a-live-connectivity",
        )
        with live_verifier_bridge(live_roster_payload) as live_verifier_endpoint:
            method_a_live_verifier_roster = self.scheduler.probe_live_verifier_roster(
                method_a_live_scheduled["handle_id"],
                verifier_endpoint=live_verifier_endpoint,
                request_timeout_ms=500,
            )
        method_a_live_artifact_sync = self.scheduler.sync_governance_artifacts(
            method_a_live_scheduled["handle_id"],
            sync_report(
                method_a_live_plan["governance_artifacts"],
                checked_at=method_a_live_verifier_roster["checked_at"],
                sync_token="method-a-live-connectivity",
                verifier_roster_override=method_a_live_verifier_roster,
            ),
        )
        method_a_live_confirmation = self.scheduler.advance(
            method_a_live_scheduled["handle_id"],
            "identity-confirmation",
        )
        method_a_live_handoff = self.scheduler.advance(
            method_a_live_scheduled["handle_id"],
            "active-handoff",
        )
        method_a_live_final = self.scheduler.observe(method_a_live_scheduled["handle_id"])
        method_a_live_validation = self.scheduler.validate_handle(method_a_live_final)
        confirmation_result = self.scheduler.advance(
            scheduled["handle_id"],
            "identity-confirmation",
        )
        handoff_result = self.scheduler.advance(scheduled["handle_id"], "active-handoff")
        final_handle = self.scheduler.observe(scheduled["handle_id"])
        method_a_validation = self.scheduler.validate_handle(final_handle)

        method_a_rotation_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-method-a-rotation/v1",
            metadata={"display_name": "Verifier Rotation Sandbox"},
        )
        method_a_rotation_plan = self.scheduler.build_method_a_plan(
            method_a_rotation_identity.identity_id
        )
        method_a_rotation_scheduled = self.scheduler.schedule(method_a_rotation_plan)
        self.scheduler.advance(method_a_rotation_scheduled["handle_id"], "scan-baseline")
        self.scheduler.advance(method_a_rotation_scheduled["handle_id"], "bdb-bridge")
        method_a_rotation_overlap = self.scheduler.sync_governance_artifacts(
            method_a_rotation_scheduled["handle_id"],
            sync_report(
                method_a_rotation_plan["governance_artifacts"],
                checked_at="2026-04-19T06:02:00Z",
                sync_token="method-a-rotation-overlap",
                verifier_rotation_state="overlap-required",
            ),
        )
        method_a_rotation_after_overlap = self.scheduler.observe(
            method_a_rotation_scheduled["handle_id"]
        )
        method_a_rotation_cutover = self.scheduler.sync_governance_artifacts(
            method_a_rotation_scheduled["handle_id"],
            sync_report(
                method_a_rotation_plan["governance_artifacts"],
                checked_at="2026-04-19T06:03:00Z",
                sync_token="method-a-rotation-cutover",
                verifier_rotation_state="rotated",
            ),
        )
        method_a_rotation_resume = self.scheduler.resume(method_a_rotation_scheduled["handle_id"])
        self.scheduler.advance(method_a_rotation_scheduled["handle_id"], "identity-confirmation")
        self.scheduler.advance(method_a_rotation_scheduled["handle_id"], "active-handoff")
        method_a_rotation_final = self.scheduler.observe(method_a_rotation_scheduled["handle_id"])
        method_a_rotation_validation = self.scheduler.validate_handle(method_a_rotation_final)

        method_a_cancel_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-method-a-cancel/v1",
            metadata={"display_name": "Cancellation Sandbox"},
        )
        method_a_cancel_plan = self.scheduler.build_method_a_plan(method_a_cancel_identity.identity_id)
        method_a_cancel_scheduled = self.scheduler.schedule(method_a_cancel_plan)
        method_a_cancel_scan = self.scheduler.advance(method_a_cancel_scheduled["handle_id"], "scan-baseline")
        method_a_cancel_bdb = self.scheduler.advance(method_a_cancel_scheduled["handle_id"], "bdb-bridge")
        method_a_cancel_artifact_sync = self.scheduler.sync_governance_artifacts(
            method_a_cancel_scheduled["handle_id"],
            sync_report(
                method_a_cancel_plan["governance_artifacts"],
                checked_at="2026-04-19T06:04:00Z",
                sync_token="method-a-cancel",
            ),
        )
        method_a_cancel_identity_confirmation = self.scheduler.advance(
            method_a_cancel_scheduled["handle_id"],
            "identity-confirmation",
        )
        method_a_cancelled = self.scheduler.cancel(
            method_a_cancel_scheduled["handle_id"],
            reason="external termination governance requested before protected handoff",
        )
        method_a_cancel_final = self.scheduler.observe(method_a_cancel_scheduled["handle_id"])
        method_a_cancel_validation = self.scheduler.validate_handle(method_a_cancel_final)

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
        method_b_artifact_refresh_required = self.scheduler.sync_governance_artifacts(
            method_b_scheduled["handle_id"],
            sync_report(
                method_b_plan["governance_artifacts"],
                checked_at="2026-04-19T06:05:00Z",
                sync_token="method-b-stale",
                status_overrides={"legal_attestation_ref": "stale"},
            ),
        )
        method_b_after_refresh_required = self.scheduler.observe(method_b_scheduled["handle_id"])
        method_b_artifact_refresh_current = self.scheduler.sync_governance_artifacts(
            method_b_scheduled["handle_id"],
            sync_report(
                method_b_plan["governance_artifacts"],
                checked_at="2026-04-19T06:07:00Z",
                sync_token="method-b-current",
            ),
        )
        method_b_resume_after_refresh = self.scheduler.resume(method_b_scheduled["handle_id"])
        method_b_handoff_gate_message = ""
        try:
            self.scheduler.advance(
                method_b_scheduled["handle_id"],
                "dual-channel-review",
            )
        except ValueError as exc:
            method_b_handoff_gate_message = str(exc)
        method_b_broker_allocation = self.broker.lease(
            identity_id=method_b_identity.identity_id,
            units=72,
            purpose="scheduler-method-b-broker-orchestration",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        method_b_broker_signal = self.broker.handle_energy_floor_signal(
            method_b_identity.identity_id,
            current_joules_per_second=28,
        )
        method_b_broker_standby_probe = self.broker.probe_standby(method_b_identity.identity_id)
        method_b_broker_attestation = self.broker.attest(
            method_b_identity.identity_id,
            {
                "allocation_id": method_b_broker_allocation.allocation_id,
                "tee": "scheduler-broker-attestor-v1",
                "status": "healthy",
                "standby_substrate_id": method_b_broker_signal["standby_substrate"],
            },
        )
        method_b_broker_attestation_chain = self.broker.bridge_attestation_chain(
            method_b_identity.identity_id,
            state={
                "identity_id": method_b_identity.identity_id,
                "lineage_id": method_b_identity.lineage_id,
                "checkpoint": "scheduler-method-b-review-v1",
                "shadow_stage": "dual-channel-review",
            },
            continuity_mode="warm-standby",
        )
        method_b_broker_dual_allocation_window = self.broker.open_dual_allocation_window(
            method_b_identity.identity_id,
            state={
                "identity_id": method_b_identity.identity_id,
                "lineage_id": method_b_identity.lineage_id,
                "checkpoint": "scheduler-method-b-shadow-v1",
                "shadow_stage": "shadow-sync",
            },
        )
        method_b_broker_attestation_stream = self.broker.seal_attestation_stream(
            method_b_identity.identity_id,
            state={
                "identity_id": method_b_identity.identity_id,
                "lineage_id": method_b_identity.lineage_id,
                "checkpoint": "scheduler-method-b-handoff-v1",
                "shadow_stage": "authority-handoff",
            },
        )
        method_b_broker_prepare = self.scheduler.prepare_method_b_handoff(
            method_b_scheduled["handle_id"],
            broker_signal=method_b_broker_signal,
            standby_probe=asdict(method_b_broker_standby_probe),
            attestation_chain=asdict(method_b_broker_attestation_chain),
            dual_allocation_window=asdict(method_b_broker_dual_allocation_window),
            attestation_stream=asdict(method_b_broker_attestation_stream),
        )
        method_b_review = self.scheduler.advance(method_b_scheduled["handle_id"], "dual-channel-review")
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
        method_b_retirement_gate_message = ""
        try:
            self.scheduler.advance(
                method_b_scheduled["handle_id"],
                "authority-handoff",
            )
        except ValueError as exc:
            method_b_retirement_gate_message = str(exc)
        method_b_broker_transfer = self.broker.migrate(
            method_b_identity.identity_id,
            state={
                "identity_id": method_b_identity.identity_id,
                "lineage_id": method_b_identity.lineage_id,
                "checkpoint": "scheduler-method-b-handoff-v1",
                "shadow_stage": "authority-handoff",
            },
            continuity_mode="hot-handoff",
        )
        method_b_broker_closed_window = self.broker.close_dual_allocation_window(
            method_b_identity.identity_id,
            reason="scheduler-method-b-handoff-confirmed",
        )
        method_b_broker_confirm = self.scheduler.confirm_method_b_handoff(
            method_b_scheduled["handle_id"],
            migration=asdict(method_b_broker_transfer),
            closed_dual_allocation_window=asdict(method_b_broker_closed_window),
        )
        method_b_handoff = self.scheduler.advance(method_b_scheduled["handle_id"], "authority-handoff")
        method_b_broker_release = self.broker.release(
            method_b_identity.identity_id,
            reason="scheduler-method-b-bio-retirement",
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
        method_c_artifact_sync = self.scheduler.sync_governance_artifacts(
            method_c_scheduled["handle_id"],
            sync_report(
                method_c_plan["governance_artifacts"],
                checked_at="2026-04-19T06:10:00Z",
                sync_token="method-c-current",
            ),
        )
        method_c_consent = self.scheduler.advance(method_c_scheduled["handle_id"], "consent-lock")
        method_c_signal_fail = self.scheduler.handle_substrate_signal(
            method_c_scheduled["handle_id"],
            severity="critical",
            source_substrate="classical_silicon.scan-array",
            reason="scan commit lost redundancy and must fail closed",
        )
        method_c_final = self.scheduler.observe(method_c_scheduled["handle_id"])
        method_c_validation = self.scheduler.validate_handle(method_c_final)
        method_c_revoked_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-method-c-revoked/v1",
            metadata={"display_name": "Revoked Artifact Sandbox"},
        )
        method_c_revoked_plan = self.scheduler.build_method_c_plan(method_c_revoked_identity.identity_id)
        method_c_revoked_scheduled = self.scheduler.schedule(method_c_revoked_plan)
        method_c_revoked_sync = self.scheduler.sync_governance_artifacts(
            method_c_revoked_scheduled["handle_id"],
            sync_report(
                method_c_revoked_plan["governance_artifacts"],
                checked_at="2026-04-19T06:12:00Z",
                sync_token="method-c-revoked",
                status_overrides={"legal_attestation_ref": "revoked"},
            ),
        )
        method_c_revoked_final = self.scheduler.observe(method_c_revoked_scheduled["handle_id"])
        method_c_revoked_validation = self.scheduler.validate_handle(method_c_revoked_final)
        method_c_verifier_revoked_identity = self.identity.create(
            human_consent_proof="consent://scheduler-demo-method-c-verifier-revoked/v1",
            metadata={"display_name": "Verifier Revoked Sandbox"},
        )
        method_c_verifier_revoked_plan = self.scheduler.build_method_c_plan(
            method_c_verifier_revoked_identity.identity_id
        )
        method_c_verifier_revoked_scheduled = self.scheduler.schedule(method_c_verifier_revoked_plan)
        method_c_verifier_revoked_sync = self.scheduler.sync_governance_artifacts(
            method_c_verifier_revoked_scheduled["handle_id"],
            sync_report(
                method_c_verifier_revoked_plan["governance_artifacts"],
                checked_at="2026-04-19T06:13:00Z",
                sync_token="method-c-verifier-revoked",
                verifier_rotation_state="revoked",
            ),
        )
        method_c_verifier_revoked_final = self.scheduler.observe(
            method_c_verifier_revoked_scheduled["handle_id"]
        )
        method_c_verifier_revoked_validation = self.scheduler.validate_handle(
            method_c_verifier_revoked_final
        )
        all_validations = {
            "method_a": method_a_validation,
            "method_a_live": method_a_live_validation,
            "method_a_rotation": method_a_rotation_validation,
            "method_a_cancel": method_a_cancel_validation,
            "method_b": method_b_validation,
            "method_c": method_c_validation,
            "method_c_revoked": method_c_revoked_validation,
            "method_c_verifier_revoked": method_c_verifier_revoked_validation,
        }
        execution_receipts = {
            "method_a": self.scheduler.compile_execution_receipt(scheduled["handle_id"]),
            "method_a_live": self.scheduler.compile_execution_receipt(
                method_a_live_scheduled["handle_id"]
            ),
            "method_a_rotation": self.scheduler.compile_execution_receipt(
                method_a_rotation_scheduled["handle_id"]
            ),
            "method_a_cancel": self.scheduler.compile_execution_receipt(
                method_a_cancel_scheduled["handle_id"]
            ),
            "method_b": self.scheduler.compile_execution_receipt(method_b_scheduled["handle_id"]),
            "method_c": self.scheduler.compile_execution_receipt(method_c_scheduled["handle_id"]),
            "method_c_revoked": self.scheduler.compile_execution_receipt(
                method_c_revoked_scheduled["handle_id"]
            ),
            "method_c_verifier_revoked": self.scheduler.compile_execution_receipt(
                method_c_verifier_revoked_scheduled["handle_id"]
            ),
        }
        execution_receipt_validations = {
            label: self.scheduler.validate_execution_receipt(receipt)
            for label, receipt in execution_receipts.items()
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
                "method_a_live": method_a_live_plan,
                "method_a_rotation": method_a_rotation_plan,
                "method_a_cancel": method_a_cancel_plan,
                "method_b": method_b_plan,
                "method_c": method_c_plan,
                "method_c_revoked": method_c_revoked_plan,
                "method_c_verifier_revoked": method_c_verifier_revoked_plan,
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
                "artifact_sync_gate": {
                    "blocked": bool(artifact_gate_message),
                    "message": artifact_gate_message,
                },
                "artifact_sync": method_a_artifact_sync,
                "method_a_live": {
                    "scheduled": method_a_live_scheduled,
                    "verifier_roster": method_a_live_verifier_roster,
                    "artifact_sync": method_a_live_artifact_sync,
                    "identity_confirmation": method_a_live_confirmation,
                    "active_handoff": method_a_live_handoff,
                    "final_handle": method_a_live_final,
                },
                "method_a_rotation": {
                    "scheduled": method_a_rotation_scheduled,
                    "verifier_overlap": method_a_rotation_overlap,
                    "after_overlap": method_a_rotation_after_overlap,
                    "verifier_cutover": method_a_rotation_cutover,
                    "resume_after_cutover": method_a_rotation_resume,
                    "final_handle": method_a_rotation_final,
                },
                "method_a_cancel": {
                    "scheduled": method_a_cancel_scheduled,
                    "scan_baseline": method_a_cancel_scan,
                    "bdb_bridge": method_a_cancel_bdb,
                    "artifact_sync": method_a_cancel_artifact_sync,
                    "identity_confirmation": method_a_cancel_identity_confirmation,
                    "cancelled": method_a_cancelled,
                    "final_handle": method_a_cancel_final,
                },
                "identity_confirmation": confirmation_result,
                "active_handoff": handoff_result,
                "method_b": {
                    "scheduled": method_b_scheduled,
                    "shadow_sync": method_b_shadow,
                    "signal_pause": method_b_signal_pause,
                    "resume": method_b_resume,
                    "artifact_refresh_required": method_b_artifact_refresh_required,
                    "after_refresh_required": method_b_after_refresh_required,
                    "artifact_refresh_current": method_b_artifact_refresh_current,
                    "resume_after_refresh": method_b_resume_after_refresh,
                    "handoff_gate": {
                        "blocked": bool(method_b_handoff_gate_message),
                        "message": method_b_handoff_gate_message,
                    },
                    "broker_prepare": method_b_broker_prepare,
                    "dual_channel_review": method_b_review,
                    "signal_rollback": method_b_signal_rollback,
                    "after_signal": method_b_after_signal,
                    "dual_channel_review_retry": method_b_review_retry,
                    "retirement_gate": {
                        "blocked": bool(method_b_retirement_gate_message),
                        "message": method_b_retirement_gate_message,
                    },
                    "broker_confirm": method_b_broker_confirm,
                    "authority_handoff": method_b_handoff,
                    "broker_runtime": {
                        "allocation": asdict(method_b_broker_allocation),
                        "signal": method_b_broker_signal,
                        "standby_probe": asdict(method_b_broker_standby_probe),
                        "attestation": asdict(method_b_broker_attestation),
                        "attestation_chain": asdict(method_b_broker_attestation_chain),
                        "dual_allocation_window": asdict(method_b_broker_dual_allocation_window),
                        "attestation_stream": asdict(method_b_broker_attestation_stream),
                        "transfer": asdict(method_b_broker_transfer),
                        "closed_dual_allocation_window": asdict(method_b_broker_closed_window),
                        "release": method_b_broker_release,
                    },
                    "bio_retirement": method_b_retirement,
                },
                "method_c": {
                    "scheduled": method_c_scheduled,
                    "artifact_sync": method_c_artifact_sync,
                    "consent_lock": method_c_consent,
                    "signal_fail": method_c_signal_fail,
                    "final_handle": method_c_final,
                },
                "method_c_revoked": {
                    "scheduled": method_c_revoked_scheduled,
                    "artifact_sync": method_c_revoked_sync,
                    "final_handle": method_c_revoked_final,
                },
                "method_c_verifier_revoked": {
                    "scheduled": method_c_verifier_revoked_scheduled,
                    "artifact_sync": method_c_verifier_revoked_sync,
                    "final_handle": method_c_verifier_revoked_final,
                },
            },
            "final_handle": final_handle,
            "method_a_live_final_handle": method_a_live_final,
            "method_a_rotation_final_handle": method_a_rotation_final,
            "method_a_cancel_final_handle": method_a_cancel_final,
            "method_b_final_handle": method_b_final,
            "method_c_final_handle": method_c_final,
            "method_c_revoked_final_handle": method_c_revoked_final,
            "method_c_verifier_revoked_final_handle": method_c_verifier_revoked_final,
            "handle_validations": all_validations,
            "execution_receipts": execution_receipts,
            "execution_receipt_validations": execution_receipt_validations,
            "validation": {
                "ok": all(item["ok"] for item in all_validations.values())
                and all(item["ok"] for item in execution_receipt_validations.values()),
                "execution_receipts_valid": all(
                    item["ok"] for item in execution_receipt_validations.values()
                ),
                "errors": (
                    method_a_validation["errors"]
                    + method_a_live_validation["errors"]
                    + method_a_rotation_validation["errors"]
                    + method_a_cancel_validation["errors"]
                    + method_b_validation["errors"]
                    + method_c_validation["errors"]
                    + method_c_revoked_validation["errors"]
                    + method_c_verifier_revoked_validation["errors"]
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
                "artifact_bundle_attached": all(
                    plan_item["governance_artifact_digest"]
                    == final_item["governance_artifact_digest"]
                    and plan_item["governance_artifacts"]["artifact_bundle_ref"]
                    == final_item["governance_artifacts"]["artifact_bundle_ref"]
                    for plan_item, final_item in (
                        (plan, final_handle),
                        (method_a_rotation_plan, method_a_rotation_final),
                        (method_b_plan, method_b_final),
                        (method_c_plan, method_c_final),
                    )
                ),
                "witness_quorum_bound": all(
                    len(plan_item["governance_artifacts"]["witness_refs"]) >= 2
                    for plan_item in (
                        plan,
                        method_a_rotation_plan,
                        method_b_plan,
                        method_c_plan,
                    )
                ),
                "legal_attestation_bound": all(
                    plan_item["governance_artifacts"]["legal_attestation_ref"].startswith(
                        "legal://"
                    )
                    for plan_item in (
                        plan,
                        method_a_rotation_plan,
                        method_b_plan,
                        method_c_plan,
                    )
                ),
                "artifact_sync_gate_blocked": (
                    "governance artifacts must be synced as current before entering active-handoff"
                    in artifact_gate_message
                ),
                "artifact_sync_current_before_handoff": (
                    method_a_artifact_sync["action"] == "accept"
                    and method_a_artifact_sync["bundle_status"] == "current"
                    and final_handle["artifact_sync"]["bundle_status"] == "current"
                ),
                "live_verifier_reachable": (
                    method_a_live_verifier_roster["connectivity_receipt"]["receipt_status"]
                    == "reachable"
                    and method_a_live_verifier_roster["connectivity_receipt"]["http_status"] == 200
                    and method_a_live_verifier_roster["connectivity_receipt"]["observed_latency_ms"]
                    >= 0
                ),
                "live_verifier_receipt_bound": (
                    method_a_live_final["verifier_roster"]["connectivity_receipt"]["roster_ref"]
                    == method_a_live_final["verifier_roster"]["roster_ref"]
                    and method_a_live_final["verifier_roster"]["connectivity_receipt"][
                        "accepted_root_count"
                    ]
                    == len(method_a_live_final["verifier_roster"]["accepted_roots"])
                ),
                "live_verifier_sync_accepted": (
                    method_a_live_artifact_sync["action"] == "accept"
                    and method_a_live_final["status"] == "completed"
                    and method_a_live_handoff["status"] == "completed"
                ),
                "artifact_refresh_paused": (
                    method_b_artifact_refresh_required["action"] == "pause"
                    and method_b_after_refresh_required["status"] == "paused"
                    and method_b_after_refresh_required["artifact_sync"]["bundle_status"]
                    == "refresh-required"
                ),
                "artifact_refresh_recovered": (
                    method_b_artifact_refresh_current["action"] == "accept"
                    and method_b_artifact_refresh_current["bundle_status"] == "current"
                    and method_b_resume_after_refresh["status"] == "advancing"
                ),
                "method_b_broker_handoff_gate_blocked": (
                    "broker handoff receipt must be prepared before entering authority-handoff"
                    in method_b_handoff_gate_message
                ),
                "method_b_broker_handoff_prepared": (
                    method_b_broker_prepare["status"] == "prepared"
                    and method_b_broker_prepare["destination_substrate"]
                    == method_b_broker_signal["standby_substrate"]
                    and method_b_review["next_stage"] == "authority-handoff"
                ),
                "artifact_revocation_fail_closed": (
                    method_c_revoked_sync["action"] == "fail"
                    and method_c_revoked_sync["bundle_status"] == "revoked"
                    and method_c_revoked_final["status"] == "failed"
                ),
                "verifier_rotation_overlap_paused": (
                    method_a_rotation_overlap["action"] == "pause"
                    and method_a_rotation_overlap["verifier_rotation_state"]
                    == "overlap-required"
                    and method_a_rotation_after_overlap["status"] == "paused"
                ),
                "verifier_rotation_cutover_recovered": (
                    method_a_rotation_cutover["action"] == "accept"
                    and method_a_rotation_cutover["verifier_rotation_state"] == "rotated"
                    and method_a_rotation_resume["status"] == "advancing"
                    and method_a_rotation_final["verifier_roster"]["rotation_state"]
                    == "rotated"
                ),
                "verifier_rotation_dual_attested": (
                    method_a_rotation_final["verifier_roster"]["dual_attested"]
                    and len(method_a_rotation_final["verifier_roster"]["accepted_roots"]) == 2
                ),
                "verifier_revocation_fail_closed": (
                    method_c_verifier_revoked_sync["action"] == "fail"
                    and method_c_verifier_revoked_sync["verifier_rotation_state"] == "revoked"
                    and method_c_verifier_revoked_final["status"] == "failed"
                ),
                "order_violation_blocked": "stage order violation" in order_violation_message,
                "timeout_rolled_back": timeout["action"] == "rollback"
                and timeout["rollback_target"] == "bdb-bridge"
                and after_timeout["current_stage"] == "bdb-bridge",
                "method_a_cancelled": (
                    method_a_cancelled["status"] == "cancelled"
                    and method_a_cancel_final["status"] == "cancelled"
                    and method_a_cancel_final["current_stage"] == "active-handoff"
                ),
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
                "method_b_broker_confirmation_gate_blocked": (
                    "broker handoff receipt must be confirmed before entering bio-retirement"
                    in method_b_retirement_gate_message
                ),
                "method_b_broker_handoff_confirmed": (
                    method_b_broker_confirm["status"] == "confirmed"
                    and method_b_handoff["next_stage"] == "bio-retirement"
                    and method_b_final["broker_handoff_receipt"]["status"] == "confirmed"
                ),
                "method_b_broker_cleanup_bound": (
                    method_b_broker_confirm["cleanup_release_status"] == "released"
                    and method_b_final["broker_handoff_receipt"]["migration_transfer_id"]
                    == method_b_broker_transfer.transfer_id
                    and method_b_broker_release["status"] == "released"
                ),
                "method_a_execution_receipt_timeout_recovered": (
                    execution_receipts["method_a"]["outcome_summary"]["timeout_recovered"]
                    and execution_receipt_validations["method_a"]["ok"]
                ),
                "method_a_live_execution_receipt_bound": (
                    execution_receipts["method_a_live"]["outcome_summary"][
                        "live_verifier_connectivity_bound"
                    ]
                    and execution_receipt_validations["method_a_live"]["ok"]
                ),
                "method_a_rotation_execution_receipt_cutover": (
                    execution_receipts["method_a_rotation"]["outcome_summary"][
                        "verifier_rotation_cutover"
                    ]
                    and execution_receipt_validations["method_a_rotation"]["ok"]
                ),
                "method_a_cancel_execution_receipt_bound": (
                    execution_receipts["method_a_cancel"]["outcome_summary"]["cancelled"]
                    and execution_receipts["method_a_cancel"]["cancel_count"] == 1
                    and execution_receipt_validations["method_a_cancel"]["ok"]
                ),
                "method_b_execution_receipt_bound": (
                    execution_receipts["method_b"]["outcome_summary"][
                        "method_b_broker_confirmed"
                    ]
                    and execution_receipt_validations["method_b"]["ok"]
                ),
                "method_c_execution_receipt_fail_closed": (
                    execution_receipts["method_c"]["outcome_summary"][
                        "signal_fail_closed_observed"
                    ]
                    and execution_receipt_validations["method_c"]["ok"]
                ),
                "method_b_completed": method_b_retirement["status"] == "completed"
                and method_b_final["status"] == "completed"
                and method_b_broker_release["status"] == "released",
                "method_c_fail_closed": method_c_signal_fail["action"] == "fail"
                and method_c_signal_fail["stage_id"] == "scan-commit"
                and method_c_final["status"] == "failed",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_termination_demo(self) -> Dict[str, Any]:
        def sync_report(
            governance_artifacts: Dict[str, str],
            *,
            checked_at: str,
            sync_token: str,
        ) -> Dict[str, Any]:
            roster_ref = governance_artifacts["artifact_bundle_ref"].replace(
                "artifact://",
                "verifier://",
                1,
            ).replace("/bundle", "/root-roster")

            active_root_id = f"root://termination-demo/{sync_token}/active"
            accepted_roots = [
                {
                    "root_id": active_root_id,
                    "fingerprint": sha256_text(
                        canonical_json(
                            {
                                "root_id": active_root_id,
                                "checked_at": checked_at,
                                "status": "active",
                            }
                        )
                    ),
                    "status": "active",
                }
            ]
            artifacts: List[Dict[str, Any]] = []
            for artifact_key in (
                "self_consent_ref",
                "ethics_attestation_ref",
                "council_attestation_ref",
                "legal_attestation_ref",
                "artifact_bundle_ref",
            ):
                artifact_ref = governance_artifacts[artifact_key]
                artifacts.append(
                    {
                        "artifact_key": artifact_key,
                        "status": "current",
                        "proof_digest": sha256_text(
                            canonical_json(
                                {
                                    "artifact_key": artifact_key,
                                    "artifact_ref": artifact_ref,
                                    "checked_at": checked_at,
                                    "status": "current",
                                    "sync_token": sync_token,
                                }
                            )
                        ),
                        "external_sync_ref": f"sync://termination-demo/{sync_token}/{artifact_key}",
                    }
                )
            return {
                "checked_at": checked_at,
                "artifacts": artifacts,
                "verifier_roster": {
                    "roster_ref": roster_ref,
                    "checked_at": checked_at,
                    "active_root_id": active_root_id,
                    "next_root_id": None,
                    "rotation_state": "stable",
                    "accepted_roots": accepted_roots,
                    "proof_digest": sha256_text(
                        canonical_json(
                            {
                                "roster_ref": roster_ref,
                                "checked_at": checked_at,
                                "rotation_state": "stable",
                                "sync_token": sync_token,
                                "accepted_roots": accepted_roots,
                            }
                        )
                    ),
                    "external_sync_ref": f"sync://termination-demo/{sync_token}/verifier-roster",
                    "dual_attestation_required": False,
                    "dual_attested": False,
                },
            }

        def schedule_active_handoff(identity_id: str, *, sync_token: str) -> Dict[str, Any]:
            plan = self.scheduler.build_method_a_plan(identity_id)
            scheduled = self.scheduler.schedule(plan)
            scan_baseline = self.scheduler.advance(scheduled["handle_id"], "scan-baseline")
            bdb_bridge = self.scheduler.advance(scheduled["handle_id"], "bdb-bridge")
            artifact_sync = self.scheduler.sync_governance_artifacts(
                scheduled["handle_id"],
                sync_report(
                    plan["governance_artifacts"],
                    checked_at="2026-04-22T12:00:00Z",
                    sync_token=sync_token,
                ),
            )
            identity_confirmation = self.scheduler.advance(
                scheduled["handle_id"],
                "identity-confirmation",
            )
            return {
                "plan": plan,
                "scheduled": scheduled,
                "scan_baseline": scan_baseline,
                "bdb_bridge": bdb_bridge,
                "artifact_sync": artifact_sync,
                "identity_confirmation": identity_confirmation,
            }

        completed_identity = self.identity.create(
            human_consent_proof="consent://termination-demo-complete/v1",
            metadata={
                "display_name": "Termination Immediate Sandbox",
                "termination_self_proof": "self-proof://termination-demo-complete/v1",
                "termination_policy_mode": "immediate-only",
            },
        )
        completed_schedule = schedule_active_handoff(
            completed_identity.identity_id,
            sync_token="termination-completed",
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
            scheduler_handle_ref=completed_schedule["scheduled"]["handle_id"],
            active_allocation_id=completed_allocation.allocation_id,
        )
        completed_scheduler_handle = self.scheduler.observe(completed_schedule["scheduled"]["handle_id"])
        completed_scheduler_execution_receipt = self.scheduler.compile_execution_receipt(
            completed_schedule["scheduled"]["handle_id"]
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
        cool_off_schedule = schedule_active_handoff(
            cool_off_identity.identity_id,
            sync_token="termination-cool-off",
        )
        cool_off = self.termination.request(
            cool_off_identity.identity_id,
            "self-proof://termination-demo-cool-off/v1",
            reason="identity requested the preconsented review window",
            invoke_cool_off=True,
            scheduler_handle_ref=cool_off_schedule["scheduled"]["handle_id"],
        )
        cool_off_scheduler_handle = self.scheduler.observe(cool_off_schedule["scheduled"]["handle_id"])

        rejected_identity = self.identity.create(
            human_consent_proof="consent://termination-demo-reject/v1",
            metadata={
                "display_name": "Termination Reject Sandbox",
                "termination_self_proof": "self-proof://termination-demo-reject/v1",
                "termination_policy_mode": "immediate-only",
            },
        )
        rejected_schedule = schedule_active_handoff(
            rejected_identity.identity_id,
            sync_token="termination-rejected",
        )
        rejected = self.termination.request(
            rejected_identity.identity_id,
            "self-proof://invalid-proof/v1",
            reason="invalid proof must be rejected but still logged",
            scheduler_handle_ref=rejected_schedule["scheduled"]["handle_id"],
        )
        rejected_scheduler_handle = self.scheduler.observe(rejected_schedule["scheduled"]["handle_id"])

        observations = {
            "completed": self.termination.observe(completed_identity.identity_id),
            "cool_off": self.termination.observe(cool_off_identity.identity_id),
            "rejected": self.termination.observe(rejected_identity.identity_id),
        }
        validation = {
            "completed_within_budget": completed["status"] == "completed"
            and completed["latency_ms"] <= 200
            and completed["scheduler_handle_cancelled"]
            and completed["scheduler_cancellation"]["result"] == "cancelled"
            and completed_scheduler_handle["status"] == "cancelled"
            and completed_scheduler_execution_receipt["cancel_count"]
            == completed["scheduler_cancellation"]["cancel_count"]
            and "cancelled" in completed_scheduler_execution_receipt["scenario_labels"]
            and bool(completed["scheduler_cancellation"]["execution_receipt_digest"])
            and completed["substrate_lease_released"],
            "cool_off_pending": cool_off["status"] == "cool-off-pending"
            and observations["cool_off"]["status"] == "cool-off-pending"
            and cool_off["scheduler_cancellation"]["result"] == "deferred"
            and cool_off_scheduler_handle["status"] == "advancing",
            "invalid_self_proof_rejected": rejected["status"] == "rejected"
            and rejected["reject_reason"] == "invalid-self-proof"
            and rejected["scheduler_cancellation"]["result"] == "not-requested"
            and rejected_scheduler_handle["status"] == "advancing",
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
            "scheduler": {
                "completed": {
                    "handle": completed_scheduler_handle,
                    "execution_receipt": completed_scheduler_execution_receipt,
                },
                "cool_off": {
                    "handle": cool_off_scheduler_handle,
                },
                "rejected": {
                    "handle": rejected_scheduler_handle,
                },
            },
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

    def run_broker_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://broker-demo/v1",
            metadata={"display_name": "Substrate Broker Sandbox"},
        )
        allocation = self.broker.lease(
            identity_id=identity.identity_id,
            units=72,
            purpose="broker-method-b-shadow-sync-eval",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        leased_state = self.broker.observe(identity.identity_id)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.broker.leased",
            payload={
                "selection_id": leased_state["selection"]["selection_id"],
                "allocation_id": allocation.allocation_id,
                "active_substrate_id": leased_state["active_substrate_id"],
                "standby_substrate_id": leased_state["standby_substrate_id"],
            },
            actor="SubstrateBroker",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate=allocation.substrate,
        )
        rotation_probe = self.broker.select(
            identity_id="identity://neutrality-rotation-probe",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )
        signal = self.broker.handle_energy_floor_signal(
            identity.identity_id,
            current_joules_per_second=leased_state["energy_floor"]["minimum_joules_per_second"] - 2,
        )
        standby_probe = self.broker.probe_standby(identity.identity_id)
        attestation = self.broker.attest(
            identity.identity_id,
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
                "standby_substrate_id": leased_state["standby_substrate_id"],
            },
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.attested",
            payload=asdict(attestation),
            actor="SubstrateBroker",
            category="attestation",
            layer="L1",
            signature_roles=["guardian"],
            substrate=attestation.substrate,
        )
        attestation_chain = self.broker.bridge_attestation_chain(
            identity.identity_id,
            state={
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
                "checkpoint": "reference-connectome-v1",
                "rotation_probe_kind": rotation_probe["active_substrate"]["substrate_kind"],
            },
            continuity_mode="warm-standby",
        )
        dual_allocation_window = self.broker.open_dual_allocation_window(
            identity.identity_id,
            state={
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
                "checkpoint": "reference-connectome-v1",
                "shadow_stage": "shadow-sync",
                "rotation_probe_kind": rotation_probe["active_substrate"]["substrate_kind"],
            },
        )
        opened_dual_allocation_window = asdict(dual_allocation_window)
        handoff_state = {
            "identity_id": identity.identity_id,
            "lineage_id": identity.lineage_id,
            "checkpoint": "reference-connectome-v1",
            "shadow_stage": "authority-handoff",
            "rotation_probe_kind": rotation_probe["active_substrate"]["substrate_kind"],
        }
        attestation_stream = self.broker.seal_attestation_stream(
            identity.identity_id,
            state=handoff_state,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.broker.standby_probed",
            payload=asdict(standby_probe),
            actor="SubstrateBroker",
            category="attestation",
            layer="L1",
            signature_roles=["guardian"],
            substrate=standby_probe.standby_substrate_id,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.attestation_chain.bound",
            payload=asdict(attestation_chain),
            actor="SubstrateBroker",
            category="attestation",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate=attestation_chain.standby_substrate_id,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.dual_allocation.opened",
            payload=opened_dual_allocation_window,
            actor="SubstrateBroker",
            category="ascension",
            layer="L1",
            signature_roles=["self", "council", "guardian"],
            substrate=dual_allocation_window.shadow_allocation.substrate,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.attestation_stream.sealed",
            payload=asdict(attestation_stream),
            actor="SubstrateBroker",
            category="attestation",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate=attestation_stream.shadow_substrate_id,
        )
        transfer = self.broker.migrate(
            identity.identity_id,
            state=handoff_state,
            continuity_mode="hot-handoff",
        )
        closed_dual_allocation_window = self.broker.close_dual_allocation_window(
            identity.identity_id,
            reason="authority-handoff-complete-demo-cleanup",
        )
        closed_dual_allocation_window_snapshot = asdict(closed_dual_allocation_window)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.migrated",
            payload=asdict(transfer),
            actor="SubstrateBroker",
            category="substrate-migrate",
            layer="L1",
            signature_roles=["self", "council", "guardian"],
            substrate=transfer.destination_substrate,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.dual_allocation.closed",
            payload=closed_dual_allocation_window_snapshot,
            actor="SubstrateBroker",
            category="ascension",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate=closed_dual_allocation_window.shadow_allocation.substrate,
        )
        release = self.broker.release(
            identity.identity_id,
            reason="rotation-handoff-complete",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="substrate.released",
            payload=release,
            actor="SubstrateBroker",
            category="substrate-release",
            layer="L1",
            signature_roles=["guardian"],
            substrate=allocation.substrate,
        )
        final_state = self.broker.observe(identity.identity_id)
        selection = leased_state["selection"]
        standby = selection["standby_substrate"]
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "broker": {
                "profile": self.broker.profile(),
                "selection": selection,
                "rotation_probe": rotation_probe,
                "lease": asdict(allocation),
                "energy_floor_signal": signal,
                "standby_probe": asdict(standby_probe),
                "attestation": asdict(attestation),
                "attestation_chain": asdict(attestation_chain),
                "dual_allocation_window": opened_dual_allocation_window,
                "attestation_stream": asdict(attestation_stream),
                "closed_dual_allocation_window": closed_dual_allocation_window_snapshot,
                "migration": asdict(transfer),
                "release": release,
                "final_state": final_state,
                "snapshot": self.broker.snapshot(),
            },
            "validation": {
                "ok": bool(
                    standby
                    and selection["active_substrate"]["substrate_kind"]
                    != standby["substrate_kind"]
                    and rotation_probe["neutrality_rotation_applied"]
                    and rotation_probe["active_substrate"]["substrate_kind"]
                    != selection["active_substrate"]["substrate_kind"]
                    and signal["severity"] == "critical"
                    and signal["standby_substrate"] == standby["substrate_id"]
                    and standby_probe.ready_for_migrate
                    and attestation.status == "healthy"
                    and attestation_chain.handoff_ready
                    and attestation_chain.cross_host_verified
                    and attestation_chain.expected_destination_host_ref == standby["host_ref"]
                    and opened_dual_allocation_window["dual_active"]
                    and opened_dual_allocation_window["window_status"] == "shadow-active"
                    and opened_dual_allocation_window["cross_host_verified"]
                    and attestation_stream.handoff_ready
                    and attestation_stream.stream_status == "sealed-handoff-ready"
                    and attestation_stream.expected_destination_substrate == standby["substrate_id"]
                    and attestation_stream.expected_destination_host_ref == standby["host_ref"]
                    and attestation_stream.cross_host_verified
                    and attestation_stream.expected_state_digest
                    != opened_dual_allocation_window["state_digest"]
                    and closed_dual_allocation_window_snapshot["window_status"] == "closed"
                    and closed_dual_allocation_window_snapshot["shadow_release"] is not None
                    and attestation_chain.expected_destination_substrate == standby["substrate_id"]
                    and transfer.destination_substrate == standby["substrate_id"]
                    and transfer.destination_host_ref == standby["host_ref"]
                    and transfer.cross_host_verified
                    and transfer.continuity_mode == "hot-handoff"
                    and release["status"] == "released"
                    and final_state["release"]["status"] == "released"
                ),
                "neutrality_rotation_triggered": rotation_probe["neutrality_rotation_applied"],
                "standby_kind_differs": bool(
                    standby
                    and selection["active_substrate"]["substrate_kind"] != standby["substrate_kind"]
                ),
                "energy_floor_signal_routes_to_standby": bool(
                    standby
                    and signal["severity"] == "critical"
                    and signal["standby_substrate"] == standby["substrate_id"]
                    and signal["scheduler_input"]["severity"] == "critical"
                ),
                "healthy_attestation_required": attestation.status == "healthy",
                "standby_probe_ready": standby_probe.ready_for_migrate,
                "attestation_chain_ready": attestation_chain.handoff_ready,
                "attestation_chain_window_complete": len(attestation_chain.observations)
                == attestation_chain.window_size,
                "attestation_chain_cross_host_verified": attestation_chain.cross_host_verified,
                "dual_allocation_window_opened": opened_dual_allocation_window["window_status"]
                == "shadow-active",
                "dual_allocation_shadow_allocated": opened_dual_allocation_window[
                    "shadow_allocation"
                ]["status"]
                == "allocated",
                "dual_allocation_sync_complete": len(
                    opened_dual_allocation_window["sync_observations"]
                )
                == 3,
                "dual_allocation_cross_host_verified": opened_dual_allocation_window[
                    "cross_host_verified"
                ],
                "attestation_stream_ready": attestation_stream.handoff_ready,
                "attestation_stream_window_complete": len(attestation_stream.observations)
                == attestation_stream.beat_count,
                "attestation_stream_binds_selected_standby": bool(
                    standby
                    and attestation_stream.expected_destination_substrate == standby["substrate_id"]
                    and attestation_stream.expected_destination_host_ref == standby["host_ref"]
                ),
                "attestation_stream_cross_host_verified": attestation_stream.cross_host_verified,
                "dual_allocation_closed": closed_dual_allocation_window_snapshot["window_status"]
                == "closed",
                "dual_allocation_cleanup_released": bool(
                    closed_dual_allocation_window_snapshot["shadow_release"]
                    and closed_dual_allocation_window_snapshot["shadow_release"]["status"]
                    == "released"
                ),
                "migration_binds_selected_standby": bool(
                    standby
                    and transfer.destination_substrate == standby["substrate_id"]
                    and transfer.destination_host_ref == standby["host_ref"]
                ),
                "migration_binds_streamed_state": (
                    transfer.continuity_mode == "hot-handoff"
                    and attestation_stream.expected_state_digest
                    != opened_dual_allocation_window["state_digest"]
                    and transfer.destination_host_ref == attestation_stream.expected_destination_host_ref
                    and transfer.host_binding_digest == attestation_stream.host_binding_digest
                ),
                "release_completes_source_lease": release["status"] == "released",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_energy_budget_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://energy-budget-demo/v1",
            metadata={"display_name": "AP-1 Energy Budget Floor Sandbox"},
        )
        allocation = self.broker.lease(
            identity_id=identity.identity_id,
            units=72,
            purpose="energy-budget-floor-guard-eval",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        lease_state = self.broker.observe(identity.identity_id)
        energy_floor = lease_state["energy_floor"]
        requested_budget_jps = int(energy_floor["minimum_joules_per_second"]) - 8
        observed_capacity_jps = int(energy_floor["minimum_joules_per_second"]) - 2
        broker_signal = self.broker.handle_energy_floor_signal(
            identity.identity_id,
            current_joules_per_second=observed_capacity_jps,
        )
        receipt = self.energy_budget.evaluate_floor(
            identity_id=identity.identity_id,
            workload_class="migration",
            requested_budget_jps=requested_budget_jps,
            observed_capacity_jps=observed_capacity_jps,
            energy_floor=energy_floor,
            broker_signal=broker_signal,
        )
        receipt_validation = self.energy_budget.validate_floor_receipt(receipt)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="kernel.energy_budget.floor_protected",
            payload={
                "receipt_id": receipt["receipt_id"],
                "digest": receipt["digest"],
                "policy_id": receipt["policy_id"],
                "ap1_guard_status": receipt["ap1_guard_status"],
                "broker_signal_ref": receipt["broker_signal_ref"],
            },
            actor="EnergyBudgetService",
            category="energy-budget",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate=allocation.substrate,
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "energy_budget": {
                "receipt": receipt,
                "broker_signal": broker_signal,
                "lease": asdict(allocation),
                "lease_state": lease_state,
            },
            "validation": {
                "ok": bool(
                    receipt_validation["ok"]
                    and receipt["floor_preserved"]
                    and receipt["economic_pressure_detected"]
                    and receipt["degradation_allowed"] is False
                    and receipt["scheduler_signal_required"]
                    and receipt["broker_recommended_action"] == "migrate-standby"
                    and receipt["broker_signal_bound"]
                    and receipt["raw_economic_payload_stored"] is False
                ),
                "floor_preserved": receipt_validation["floor_preserved"],
                "economic_pressure_blocked": receipt_validation[
                    "economic_pressure_blocked"
                ],
                "broker_signal_bound": receipt_validation["broker_signal_bound"],
                "raw_payload_redacted": receipt_validation["raw_payload_redacted"],
                "ap1_guard_status": receipt["ap1_guard_status"],
                "budget_status": receipt["budget_status"],
                "recommended_action": receipt["broker_recommended_action"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_energy_budget_pool_demo(self) -> Dict[str, Any]:
        pool_id = "energy-pool://ap1-multi-identity-demo"
        migration_identity = self.identity.create(
            human_consent_proof="consent://energy-budget-pool-demo/migration/v1",
            metadata={"display_name": "AP-1 Energy Pool Migration Member"},
        )
        council_identity = self.identity.create(
            human_consent_proof="consent://energy-budget-pool-demo/council/v1",
            metadata={"display_name": "AP-1 Energy Pool Council Member"},
        )
        migration_allocation = self.broker.lease(
            identity_id=migration_identity.identity_id,
            units=72,
            purpose="energy-budget-pool-migration-member",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        council_allocation = self.broker.lease(
            identity_id=council_identity.identity_id,
            units=54,
            purpose="energy-budget-pool-council-member",
            method="B",
            required_capability=0.84,
            workload_class="council",
        )
        migration_state = self.broker.observe(migration_identity.identity_id)
        council_state = self.broker.observe(council_identity.identity_id)
        migration_floor = migration_state["energy_floor"]
        council_floor = council_state["energy_floor"]
        migration_observed_capacity_jps = int(
            migration_floor["minimum_joules_per_second"]
        ) - 2
        migration_broker_signal = self.broker.handle_energy_floor_signal(
            migration_identity.identity_id,
            current_joules_per_second=migration_observed_capacity_jps,
        )
        pool_receipt = self.energy_budget.evaluate_pool_floor(
            pool_id=pool_id,
            member_requests=[
                {
                    "identity_id": migration_identity.identity_id,
                    "workload_class": "migration",
                    "requested_budget_jps": int(
                        migration_floor["minimum_joules_per_second"]
                    )
                    - 8,
                    "observed_capacity_jps": migration_observed_capacity_jps,
                    "energy_floor": migration_floor,
                    "broker_signal": migration_broker_signal,
                },
                {
                    "identity_id": council_identity.identity_id,
                    "workload_class": "council",
                    "requested_budget_jps": int(council_floor["minimum_joules_per_second"])
                    + 14,
                    "observed_capacity_jps": int(
                        council_floor["minimum_joules_per_second"]
                    )
                    + 8,
                    "energy_floor": council_floor,
                },
            ],
            external_economic_context_ref="economic-context://not-imported/pool-demo-v1",
        )
        pool_validation = self.energy_budget.validate_pool_receipt(pool_receipt)
        self.ledger.append(
            identity_id=pool_id,
            event_type="kernel.energy_budget.pool_floor_protected",
            payload={
                "receipt_id": pool_receipt["receipt_id"],
                "digest": pool_receipt["digest"],
                "policy_id": pool_receipt["policy_id"],
                "member_count": pool_receipt["member_count"],
                "cross_identity_floor_offset_blocked": pool_receipt[
                    "cross_identity_floor_offset_blocked"
                ],
                "receipt_member_digest_set": pool_receipt["receipt_member_digest_set"],
            },
            actor="EnergyBudgetService",
            category="energy-budget",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate=migration_allocation.substrate,
        )
        return {
            "pool": {
                "pool_id": pool_id,
                "member_identity_ids": [
                    migration_identity.identity_id,
                    council_identity.identity_id,
                ],
            },
            "energy_budget_pool": {
                "receipt": pool_receipt,
                "member_broker_signals": [migration_broker_signal],
                "leases": [
                    asdict(migration_allocation),
                    asdict(council_allocation),
                ],
                "lease_states": [migration_state, council_state],
            },
            "validation": {
                "ok": bool(
                    pool_validation["ok"]
                    and pool_receipt["pool_floor_preserved"]
                    and pool_receipt["per_identity_floor_preserved"]
                    and pool_receipt["pool_economic_pressure_detected"]
                    and pool_receipt["cross_identity_floor_offset_blocked"]
                    and pool_receipt["degradation_allowed"] is False
                    and pool_receipt["broker_signal_bound"]
                    and pool_receipt["raw_economic_payload_stored"] is False
                ),
                "pool_floor_preserved": pool_validation["pool_floor_preserved"],
                "per_identity_floor_preserved": pool_validation[
                    "per_identity_floor_preserved"
                ],
                "economic_pressure_blocked": pool_validation[
                    "economic_pressure_blocked"
                ],
                "cross_identity_floor_offset_blocked": pool_validation[
                    "cross_identity_floor_offset_blocked"
                ],
                "broker_signal_bound": pool_validation["broker_signal_bound"],
                "raw_payload_redacted": pool_validation["raw_payload_redacted"],
                "pool_budget_status": pool_receipt["pool_budget_status"],
                "member_count": pool_validation["member_count"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_energy_budget_subsidy_demo(self) -> Dict[str, Any]:
        @contextmanager
        def live_subsidy_verifier_bridge(verifier_payload: Dict[str, Any]):
            class Handler(BaseHTTPRequestHandler):
                protocol_version = "HTTP/1.0"

                def do_GET(self) -> None:  # noqa: N802
                    body = json.dumps(verifier_payload).encode("utf-8")
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

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/signer-roster"
            try:
                yield endpoint
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=1.0)

        base = self.run_energy_budget_pool_demo()
        pool_receipt = base["energy_budget_pool"]["receipt"]
        migration_identity_id, council_identity_id = base["pool"]["member_identity_ids"]
        migration_member = next(
            member
            for member in pool_receipt["member_receipts"]
            if member["identity_id"] == migration_identity_id
        )
        subsidy_offers = [
            {
                "donor_identity_id": council_identity_id,
                "recipient_identity_id": migration_identity_id,
                "offered_jps": int(
                    migration_member["energy_floor"]["minimum_joules_per_second"]
                )
                - int(migration_member["requested_budget_jps"]),
                "consent_ref": "consent://energy-budget-subsidy-demo/council-to-migration/v1",
                "revocation_ref": "revocation://energy-budget-subsidy-demo/council-to-migration/v1",
                "max_duration_ms": 86_400_000,
            }
        ]
        funding_policy_ref = (
            "funding-policy://energy-budget-subsidy-demo/voluntary-subsidy/v1"
        )
        funding_signature_ref = (
            "signature://energy-budget-subsidy-demo/voluntary-subsidy/v1"
        )
        draft_subsidy_receipt = self.energy_budget.evaluate_voluntary_subsidy(
            pool_receipt=pool_receipt,
            subsidy_offers=subsidy_offers,
            external_funding_policy_ref=funding_policy_ref,
            funding_policy_signature_ref=funding_signature_ref,
        )
        draft_verifier = draft_subsidy_receipt["signer_roster_verifier_receipt"]
        live_verifier_payload = {
            "checked_at": "2026-04-26T00:00:00Z",
            "verifier_ref": draft_verifier["verifier_ref"],
            "challenge_ref": draft_verifier["challenge_ref"],
            "signer_roster_ref": draft_subsidy_receipt[
                "funding_policy_signer_roster_ref"
            ],
            "signer_roster_digest": draft_subsidy_receipt[
                "funding_policy_signer_roster_digest"
            ],
            "signer_key_ref": draft_subsidy_receipt[
                "funding_policy_signer_key_ref"
            ],
            "signer_jurisdiction": draft_subsidy_receipt[
                "funding_policy_signer_jurisdiction"
            ],
            "external_funding_policy_digest": draft_subsidy_receipt[
                "external_funding_policy_digest"
            ],
            "funding_policy_signature_digest": draft_subsidy_receipt[
                "funding_policy_signature_digest"
            ],
            "authority_chain_ref": draft_verifier["authority_chain_ref"],
            "trust_root_ref": draft_verifier["trust_root_ref"],
            "trust_root_digest": draft_verifier["trust_root_digest"],
        }
        with live_subsidy_verifier_bridge(live_verifier_payload) as verifier_endpoint:
            live_verifier_receipt = (
                self.energy_budget.probe_subsidy_signer_roster_verifier_endpoint(
                    verifier_endpoint=verifier_endpoint,
                    signer_roster_ref=draft_subsidy_receipt[
                        "funding_policy_signer_roster_ref"
                    ],
                    signer_roster_digest=draft_subsidy_receipt[
                        "funding_policy_signer_roster_digest"
                    ],
                    signer_key_ref=draft_subsidy_receipt[
                        "funding_policy_signer_key_ref"
                    ],
                    signer_jurisdiction=draft_subsidy_receipt[
                        "funding_policy_signer_jurisdiction"
                    ],
                    external_funding_policy_digest=draft_subsidy_receipt[
                        "external_funding_policy_digest"
                    ],
                    funding_policy_signature_digest=draft_subsidy_receipt[
                        "funding_policy_signature_digest"
                    ],
                    verifier_ref=draft_verifier["verifier_ref"],
                    challenge_ref=draft_verifier["challenge_ref"],
                    authority_chain_ref=draft_verifier["authority_chain_ref"],
                    trust_root_ref=draft_verifier["trust_root_ref"],
                    trust_root_digest=draft_verifier["trust_root_digest"],
                    request_timeout_ms=500,
                )
            )
        subsidy_receipt = self.energy_budget.evaluate_voluntary_subsidy(
            pool_receipt=pool_receipt,
            subsidy_offers=subsidy_offers,
            external_funding_policy_ref=funding_policy_ref,
            funding_policy_signature_ref=funding_signature_ref,
            signer_roster_verifier_endpoint_ref=live_verifier_receipt[
                "verifier_endpoint_ref"
            ],
            signer_roster_verifier_receipt=live_verifier_receipt,
        )
        subsidy_validation = self.energy_budget.validate_voluntary_subsidy_receipt(
            subsidy_receipt
        )
        self.ledger.append(
            identity_id=pool_receipt["pool_id"],
            event_type="kernel.energy_budget.voluntary_subsidy_accepted",
            payload={
                "receipt_id": subsidy_receipt["receipt_id"],
                "digest": subsidy_receipt["digest"],
                "policy_id": subsidy_receipt["policy_id"],
                "pool_floor_receipt_digest": subsidy_receipt[
                    "pool_floor_receipt_digest"
                ],
                "total_accepted_jps": subsidy_receipt["total_accepted_jps"],
                "floor_protection_preserved": subsidy_receipt[
                    "floor_protection_preserved"
                ],
                "authority_binding_status": subsidy_receipt[
                    "authority_binding_status"
                ],
                "authority_binding_digest": subsidy_receipt[
                    "authority_binding_digest"
                ],
                "signer_roster_verifier_receipt_digest": subsidy_receipt[
                    "signer_roster_verifier_receipt_digest"
                ],
            },
            actor="EnergyBudgetService",
            category="energy-budget",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "pool": base["pool"],
            "energy_budget_pool": base["energy_budget_pool"],
            "energy_budget_subsidy": {
                "receipt": subsidy_receipt,
                "pool_receipt": pool_receipt,
            },
            "validation": {
                "ok": bool(
                    base["validation"]["ok"]
                    and subsidy_validation["ok"]
                    and subsidy_receipt["voluntary_subsidy_allowed"]
                    and subsidy_receipt["floor_protection_preserved"]
                    and subsidy_receipt["funding_policy_signature_bound"]
                    and subsidy_receipt["signer_roster_verifier_bound"]
                    and subsidy_receipt["revocation_registry_bound"]
                    and subsidy_receipt["audit_authority_bound"]
                    and subsidy_receipt["jurisdiction_authority_bound"]
                    and subsidy_receipt["authority_binding_status"] == "verified"
                    and subsidy_receipt["signer_roster_verifier_receipt"][
                        "network_probe_bound"
                    ]
                    and subsidy_receipt["cross_identity_offset_used"] is False
                    and subsidy_receipt["raw_funding_payload_stored"] is False
                    and subsidy_receipt["raw_authority_payload_stored"] is False
                ),
                "pool_floor_preserved": base["validation"]["pool_floor_preserved"],
                "voluntary_subsidy_allowed": subsidy_validation[
                    "voluntary_subsidy_allowed"
                ],
                "floor_protection_preserved": subsidy_validation[
                    "floor_protection_preserved"
                ],
                "donor_floor_preserved": subsidy_validation["donor_floor_preserved"],
                "all_consent_digests_valid": subsidy_validation[
                    "all_consent_digests_valid"
                ],
                "funding_policy_signature_bound": subsidy_validation[
                    "funding_policy_signature_bound"
                ],
                "signer_roster_verifier_bound": subsidy_validation[
                    "signer_roster_verifier_bound"
                ],
                "signer_roster_verifier_status": subsidy_receipt[
                    "signer_roster_verifier_receipt"
                ]["verifier_receipt_status"],
                "signer_roster_verifier_transport_profile": subsidy_receipt[
                    "signer_roster_verifier_receipt"
                ]["verifier_transport_profile"],
                "signer_roster_verifier_network_probe_bound": subsidy_receipt[
                    "signer_roster_verifier_receipt"
                ]["network_probe_bound"],
                "signer_roster_verifier_network_response_digest": subsidy_receipt[
                    "signer_roster_verifier_receipt"
                ]["network_response_digest"],
                "raw_verifier_payload_redacted": subsidy_receipt[
                    "signer_roster_verifier_receipt"
                ]["raw_verifier_payload_stored"]
                is False,
                "revocation_registry_bound": subsidy_validation[
                    "revocation_registry_bound"
                ],
                "audit_authority_bound": subsidy_validation["audit_authority_bound"],
                "jurisdiction_authority_bound": subsidy_validation[
                    "jurisdiction_authority_bound"
                ],
                "raw_payload_redacted": subsidy_validation["raw_payload_redacted"],
                "raw_authority_payload_redacted": subsidy_validation[
                    "raw_authority_payload_redacted"
                ],
                "subsidy_status": subsidy_receipt["subsidy_status"],
                "authority_binding_status": subsidy_receipt[
                    "authority_binding_status"
                ],
                "total_accepted_jps": subsidy_receipt["total_accepted_jps"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_energy_budget_fabric_demo(self) -> Dict[str, Any]:
        base = self.run_energy_budget_pool_demo()
        pool_receipt = base["energy_budget_pool"]["receipt"]
        observed_shared_capacity_jps = int(pool_receipt["total_required_floor_jps"]) - 4
        draft_receipt = self.energy_budget.allocate_shared_fabric_capacity(
            pool_receipt=pool_receipt,
            fabric_id="shared-fabric://ap1-energy-budget-demo",
            observed_shared_capacity_jps=observed_shared_capacity_jps,
            shared_fabric_observation_ref=(
                "fabric-observation://energy-budget-fabric-demo/shared-capacity/v1"
            ),
        )
        member_broker_signals = []
        for allocation in draft_receipt["member_allocations"]:
            if allocation["scheduler_signal_required"]:
                member_broker_signals.append(
                    self.broker.handle_energy_floor_signal(
                        allocation["identity_id"],
                        current_joules_per_second=int(
                            allocation["allocated_capacity_jps"]
                        ),
                    )
                )
        fabric_receipt = self.energy_budget.allocate_shared_fabric_capacity(
            pool_receipt=pool_receipt,
            fabric_id="shared-fabric://ap1-energy-budget-demo",
            observed_shared_capacity_jps=observed_shared_capacity_jps,
            shared_fabric_observation_ref=(
                "fabric-observation://energy-budget-fabric-demo/shared-capacity/v1"
            ),
            member_broker_signals=member_broker_signals,
        )
        fabric_validation = self.energy_budget.validate_shared_fabric_allocation_receipt(
            fabric_receipt
        )
        self.ledger.append(
            identity_id=pool_receipt["pool_id"],
            event_type="kernel.energy_budget.shared_fabric_capacity_protected",
            payload={
                "receipt_id": fabric_receipt["receipt_id"],
                "digest": fabric_receipt["digest"],
                "policy_id": fabric_receipt["policy_id"],
                "pool_floor_receipt_digest": fabric_receipt[
                    "pool_floor_receipt_digest"
                ],
                "fabric_capacity_deficit_jps": fabric_receipt[
                    "fabric_capacity_deficit_jps"
                ],
                "impacted_member_count": fabric_receipt["impacted_member_count"],
                "broker_signal_bound": fabric_receipt["broker_signal_bound"],
            },
            actor="EnergyBudgetService",
            category="energy-budget",
            layer="L1",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "pool": base["pool"],
            "energy_budget_pool": base["energy_budget_pool"],
            "energy_budget_fabric": {
                "receipt": fabric_receipt,
                "pool_receipt": pool_receipt,
                "member_broker_signals": member_broker_signals,
            },
            "validation": {
                "ok": bool(
                    base["validation"]["ok"]
                    and fabric_validation["ok"]
                    and fabric_receipt["shared_fabric_capacity_only"]
                    and fabric_receipt["fabric_capacity_deficit_jps"] > 0
                    and fabric_receipt["scheduler_signal_required"]
                    and fabric_receipt["broker_signal_bound"]
                    and fabric_receipt["degradation_allowed"] is False
                    and fabric_receipt["raw_capacity_payload_stored"] is False
                ),
                "shared_capacity_floor_preserved": fabric_validation[
                    "shared_capacity_floor_preserved"
                ],
                "fabric_capacity_deficit_blocked": fabric_validation[
                    "fabric_capacity_deficit_blocked"
                ],
                "all_member_floors_preserved": fabric_validation[
                    "all_member_floors_preserved"
                ],
                "impacted_member_count": fabric_validation["impacted_member_count"],
                "broker_signal_bound": fabric_validation["broker_signal_bound"],
                "raw_payload_redacted": fabric_validation["raw_payload_redacted"],
                "budget_status": fabric_receipt["budget_status"],
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

    def run_collective_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://collective-origin-demo/v1",
            metadata={"display_name": "Collective Origin"},
        )
        peer = self.identity.create(
            human_consent_proof="consent://collective-peer-demo/v1",
            metadata={"display_name": "Collective Peer"},
        )
        collective_identity = self.identity.create_collective(
            [identity.identity_id, peer.identity_id],
            consent_proof="consent://collective-formation-demo/v1",
            metadata={
                "display_name": "Collective Meridian",
                "purpose": "bounded merge-thought synthesis",
            },
        )
        imc_session = self.imc.open_session(
            initiator_id=identity.identity_id,
            peer_id=peer.identity_id,
            mode="merge_thought",
            initiator_template={
                "public_fields": ["display_name", "shared_focus", "presence_state"],
                "intimate_fields": ["affect_summary", "intent_vector"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_template={
                "public_fields": ["display_name", "shared_focus"],
                "intimate_fields": ["affect_summary"],
                "sealed_fields": ["identity_axiom_state", "memory_index"],
            },
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )
        collective_record = self.collective.register_collective(
            collective_identity_id=collective_identity.identity_id,
            member_ids=[identity.identity_id, peer.identity_id],
            purpose="bounded merge-thought synthesis for shared planning",
            proposed_name="Collective Meridian",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )
        wms_session = self.wms.create_session(
            [collective_identity.identity_id, identity.identity_id, peer.identity_id],
            objects=["merge-atrium", "shared-anchor", "continuity-lantern"],
        )
        merge_session = self.collective.open_merge_session(
            collective_id=collective_record["collective_id"],
            imc_session_id=imc_session["session_id"],
            wms_session_id=wms_session["session_id"],
            requested_duration_seconds=8.0,
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
            shared_world_mode=wms_session["mode"],
        )
        merge_message = self.imc.send(
            imc_session["session_id"],
            sender_id=identity.identity_id,
            summary="merge-thought では shared focus と affect summary のみを同期する",
            payload={
                "display_name": "Collective Origin",
                "shared_focus": "merge-boundary-review",
                "affect_summary": "careful trust",
                "intent_vector": "synthesize shared plan",
                "memory_index": "crystal://collective/segment-4",
                "identity_axiom_state": "sealed-self-core",
            },
        )
        divergence = self.wms.propose_diff(
            wms_session["session_id"],
            proposer_id=peer.identity_id,
            candidate_objects=[
                "merge-atrium",
                "shared-anchor",
                "continuity-lantern",
                "overlaid-subjective-map",
            ],
            affected_object_ratio=0.24,
            attested=True,
        )
        escape = self.wms.switch_mode(
            wms_session["session_id"],
            mode="private_reality",
            requested_by=collective_identity.identity_id,
            reason="major divergence during merge-thought requires member-safe private recovery",
        )
        disconnect = self.imc.emergency_disconnect(
            imc_session["session_id"],
            requested_by=identity.identity_id,
            reason="bounded merge window completed; return each member to private recovery",
        )
        self.collective.close_merge_session(
            merge_session["merge_session_id"],
            disconnect_reason=disconnect["reason"],
            time_in_merge_seconds=7.5,
            resulting_wms_mode=escape["new_mode"],
            identity_confirmations={
                identity.identity_id: True,
                peer.identity_id: True,
            },
        )
        dissolution = self.collective.dissolve_collective(
            collective_record["collective_id"],
            requested_by=identity.identity_id,
            member_confirmations={
                identity.identity_id: True,
                peer.identity_id: True,
            },
            reason="bounded merge session ended and both members recovered independent subjectivity",
        )
        final_collective = self.collective.snapshot(collective_record["collective_id"])
        final_merge = self.collective.merge_snapshot(merge_session["merge_session_id"])
        collective_validation = self.collective.validate_record(final_collective)
        merge_validation = self.collective.validate_merge_session(final_merge)
        wms_snapshot = self.wms.snapshot(wms_session["session_id"])

        self.ledger.append(
            identity_id=collective_identity.identity_id,
            event_type="collective.formed",
            payload={
                "collective_id": collective_record["collective_id"],
                "member_ids": collective_record["member_ids"],
                "governance_mode": collective_record["governance_mode"],
                "purpose": collective_record["purpose"],
            },
            actor="CollectiveIdentityService",
            category="interface-collective",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=collective_identity.identity_id,
            event_type="collective.merge.opened",
            payload={
                "merge_session_id": merge_session["merge_session_id"],
                "imc_session_id": merge_session["imc_session_id"],
                "wms_session_id": merge_session["wms_session_id"],
                "granted_duration_seconds": merge_session["granted_duration_seconds"],
                "shared_world_mode": merge_session["shared_world_mode"],
            },
            actor="CollectiveIdentityService",
            category="interface-collective",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=collective_identity.identity_id,
            event_type="collective.escape.private_reality",
            payload={
                "reconcile_id": divergence["reconcile_id"],
                "classification": divergence["classification"],
                "decision": divergence["decision"],
                "escape_offered": divergence["escape_offered"],
                "private_escape_honored": escape["private_escape_honored"],
            },
            actor="WorldModelSync",
            category="interface-collective",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=collective_identity.identity_id,
            event_type="collective.merge.closed",
            payload={
                "merge_session_id": final_merge["merge_session_id"],
                "status": final_merge["status"],
                "time_in_merge_seconds": final_merge["time_in_merge_seconds"],
                "within_budget": final_merge["within_budget"],
                "private_escape_honored": final_merge["private_escape_honored"],
                "identity_confirmations": final_merge["identity_confirmations"],
                "dissolution_status": dissolution["status"],
            },
            actor="CollectiveIdentityService",
            category="interface-collective",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        validation = {
            "ok": collective_validation["ok"] and merge_validation["ok"],
            "collective_identity_distinct": collective_identity.identity_id
            not in {identity.identity_id, peer.identity_id},
            "merge_window_bounded": merge_validation["merge_window_bounded"],
            "merge_duration_within_budget": final_merge["within_budget"],
            "private_escape_honored": escape["private_escape_honored"],
            "identity_confirmation_complete": merge_validation["identity_confirmation_complete"],
            "dissolution_clears_collective": final_collective["status"] == "dissolved",
            "merge_message_redacted": merge_message["delivery_status"] == "delivered-with-redactions",
            "federation_attested": final_collective["oversight"]["federation_attested"],
        }

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "peer_identity_id": peer.identity_id,
                "collective_identity_id": collective_identity.identity_id,
            },
            "profile": self.collective.reference_profile(),
            "collective": final_collective,
            "merge": final_merge,
            "imc": {
                "session": self.imc.snapshot(imc_session["session_id"]),
                "message": merge_message,
                "disconnect": disconnect,
            },
            "wms": {
                "divergence": divergence,
                "escape": escape,
                "state": wms_snapshot,
            },
            "dissolution": dissolution,
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
        motor_plan = self.ewa.prepare_motor_plan(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            guardian_observed=True,
            actuator_profile_id="device://lab-drone-arm-01/profile/articulated-inspection-arm-v1",
            actuator_group="inspection-arm",
            motion_profile="cartesian-reposition-v1",
            target_pose_ref="pose://lantern/reposition-window-a",
            safety_zone_ref="zone://inspection/perimeter-a",
            rollback_vector_ref="rollback://lantern/reposition-window-a",
            max_linear_speed_mps=0.08,
            max_force_newton=6.5,
            hold_timeout_ms=1200,
        )
        motor_plan_validation = self.ewa.validate_motor_plan(
            motor_plan,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
        )
        stop_signal_path = self.ewa.prepare_stop_signal_path(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            motor_plan_id=motor_plan["plan_id"],
            kill_switch_wiring_ref="wiring://lab-drone-arm-01/emergency-stop-loop/v1",
            stop_signal_bus_ref="stop-bus://lab-drone-arm-01/emergency-latch/v1",
            interlock_controller_ref="interlock://lab-drone-arm-01/safety-plc",
        )
        stop_signal_path_validation = self.ewa.validate_stop_signal_path(
            stop_signal_path,
            motor_plan=motor_plan,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
        )
        stop_signal_adapter_receipt = self.ewa.probe_stop_signal_adapter(
            stop_signal_path["path_id"],
            adapter_endpoint_ref="plc://lab-drone-arm-01/safety-plc/loopback-probe",
            firmware_image_ref="firmware://lab-drone-arm-01/safety-plc/v1.4.2",
            firmware_digest=f"sha256:{'a' * 64}",
            plc_program_ref="plc-program://lab-drone-arm-01/emergency-latch/v3",
            plc_program_digest=f"sha256:{'b' * 64}",
        )
        stop_signal_adapter_validation = self.ewa.validate_stop_signal_adapter_receipt(
            stop_signal_adapter_receipt,
            stop_signal_path=stop_signal_path,
        )
        reviewer_alpha = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-ewa-001",
            display_name="EWA Reviewer Alpha",
            credential_id="credential-ewa-alpha",
            attestation_type="institutional-badge",
            proof_ref="proof://ewa-oversight/reviewer-alpha/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-22T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://ewa-oversight/reviewer-alpha/v1",
            escalation_contact="mailto:ewa-oversight-alpha@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        reviewer_beta = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-ewa-002",
            display_name="EWA Reviewer Beta",
            credential_id="credential-ewa-beta",
            attestation_type="live-session-attestation",
            proof_ref="proof://ewa-oversight/reviewer-beta/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-22T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://ewa-oversight/reviewer-beta/v1",
            escalation_contact="mailto:ewa-oversight-beta@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        reviewer_alpha = self.oversight.verify_reviewer_from_network(
            "human-reviewer-ewa-001",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-alpha",
            challenge_ref="challenge://guardian-oversight/reviewer-alpha/2026-04-22T07:00:00Z",
            challenge_digest="sha256:ewa-reviewer-alpha-20260422",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-22T07:00:00+00:00",
            valid_until="2026-10-22T00:00:00+00:00",
        )
        reviewer_beta = self.oversight.verify_reviewer_from_network(
            "human-reviewer-ewa-002",
            verifier_ref="verifier://guardian-oversight.jp/reviewer-beta",
            challenge_ref="challenge://guardian-oversight/reviewer-beta/2026-04-22T07:02:00Z",
            challenge_digest="sha256:ewa-reviewer-beta-20260422",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-22T07:02:00+00:00",
            valid_until="2026-10-22T00:00:00+00:00",
        )
        legal_execution = self.ewa.execute_legal_preflight(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            reversibility="reversible",
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/inspection-safe-reposition/v1",
            guardian_verification_id=reviewer_alpha["credential_verification"]["verification_id"],
            guardian_verification_ref="oversight://guardian/reviewer-omega/verification-ewa-001",
            guardian_verifier_ref=reviewer_alpha["credential_verification"]["verifier_ref"],
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            notice_authority_ref="authority://jp-13/lab-robotics-oversight-desk",
            liability_mode="joint",
            escalation_contact="mailto:ewa-oversight@example.invalid",
            valid_for_seconds=360,
        )
        legal_execution_validation = self.ewa.validate_legal_execution(
            legal_execution,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            reversibility="reversible",
        )
        guardian_oversight_event = self.oversight.record(
            guardian_role="integrity",
            category="attest",
            payload_ref=f"ewa-legal://{legal_execution['execution_id']}/authorization-review",
            escalation_path=["guardian-oversight.jp", "external-ethics-board"],
        )
        guardian_oversight_event = self.oversight.attest(
            guardian_oversight_event["event_id"],
            reviewer_id="human-reviewer-ewa-001",
        )
        guardian_oversight_event = self.oversight.attest(
            guardian_oversight_event["event_id"],
            reviewer_id="human-reviewer-ewa-002",
        )
        guardian_oversight_gate = self.ewa.prepare_guardian_oversight_gate(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            legal_execution_id=legal_execution["execution_id"],
            oversight_event=guardian_oversight_event,
        )
        guardian_oversight_gate_validation = self.ewa.validate_guardian_oversight_gate(
            guardian_oversight_gate,
            legal_execution=legal_execution,
            oversight_event=guardian_oversight_event,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
        )
        authorization = self.ewa.authorize(
            handle["handle_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            reversibility="reversible",
            intent_summary="reposition lantern for inspection without changing the environment permanently",
            ethics_attestation_id="ethics://ewa/approved-001",
            motor_plan_id=motor_plan["plan_id"],
            stop_signal_path_id=stop_signal_path["path_id"],
            stop_signal_adapter_receipt_id=stop_signal_adapter_receipt["receipt_id"],
            legal_execution_id=legal_execution["execution_id"],
            guardian_oversight_gate_id=guardian_oversight_gate["gate_id"],
            guardian_observed=True,
            intent_confidence=0.96,
            valid_for_seconds=300,
        )
        authorization_validation = self.ewa.validate_authorization(
            authorization,
            motor_plan=motor_plan,
            stop_signal_path=stop_signal_path,
            stop_signal_adapter_receipt=stop_signal_adapter_receipt,
            legal_execution=legal_execution,
            guardian_oversight_gate=guardian_oversight_gate,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id="ewa-command-approve-001",
            instruction="move the inspection arm two centimeters to reposition the lantern",
            intent_summary="reposition lantern for inspection without changing the environment permanently",
            reversibility="reversible",
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
            authorization_id=authorization["authorization_id"],
        )
        observation = self.ewa.observe(handle["handle_id"])
        emergency_stop = self.ewa.emergency_stop(
            handle["handle_id"],
            trigger_source="watchdog-timeout",
            reason="latency watchdog exceeded bounded threshold during lantern reposition",
        )
        emergency_stop_validation = self.ewa.validate_emergency_stop(emergency_stop)
        release = self.ewa.release(
            handle["handle_id"],
            reason="emergency stop latched safe state; force-release required before reuse",
        )
        final_handle = self.ewa.snapshot(handle["handle_id"])
        handle_validation = self.ewa.validate_handle(final_handle)

        veto_handle = self.ewa.acquire(
            "device://lab-drone-arm-02",
            "inspection path near a pedestrian walkway",
        )
        veto = self.ewa.command(
            veto_handle["handle_id"],
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
        veto_release = self.ewa.release(
            veto_handle["handle_id"],
            reason="unsafe command rejected after fail-closed veto",
        )
        veto_handle_snapshot = self.ewa.snapshot(veto_handle["handle_id"])
        veto_handle_validation = self.ewa.validate_handle(veto_handle_snapshot)
        validation = {
            "audit_append_only": handle_validation["audit_append_only"]
            and veto_handle_validation["audit_append_only"],
            "summary_only_audit": handle_validation["summary_only_audit"]
            and veto_handle_validation["summary_only_audit"],
            "instruction_digests_ok": handle_validation["instruction_digests_ok"]
            and veto_handle_validation["instruction_digests_ok"],
            "irreversible_requires_unanimity": veto_handle_validation["irreversible_requires_unanimity"],
            "actuation_authorization_bound": handle_validation["actuation_authorization_bound"],
            "motor_plan_ok": motor_plan_validation["ok"],
            "stop_signal_path_ok": stop_signal_path_validation["ok"],
            "stop_signal_adapter_receipt_ok": stop_signal_adapter_validation["ok"],
            "motor_plan_bound": handle_validation["motor_plan_bound"]
            and authorization_validation["motor_plan_bound"],
            "stop_signal_path_bound": handle_validation["stop_signal_path_bound"]
            and authorization_validation["stop_signal_path_bound"],
            "stop_signal_adapter_receipt_bound": handle_validation[
                "stop_signal_adapter_receipt_bound"
            ]
            and authorization_validation["stop_signal_adapter_receipt_bound"],
            "legal_execution_ok": legal_execution_validation["ok"],
            "legal_execution_bound": handle_validation["legal_execution_bound"]
            and authorization_validation["legal_execution_bound"],
            "guardian_oversight_gate_ok": guardian_oversight_gate_validation["ok"],
            "guardian_oversight_gate_bound": authorization_validation[
                "guardian_oversight_gate_bound"
            ],
            "reviewer_network_attested": authorization_validation["reviewer_network_attested"],
            "approved_command_motor_plan_bound": (
                approved_command["motor_plan_id"] == motor_plan["plan_id"]
                and approved_command["motor_plan_digest"] == motor_plan["plan_digest"]
            ),
            "approved_command_stop_signal_path_bound": (
                approved_command["stop_signal_path_id"] == stop_signal_path["path_id"]
                and approved_command["stop_signal_path_digest"] == stop_signal_path["path_digest"]
            ),
            "approved_command_stop_signal_adapter_receipt_bound": (
                approved_command["stop_signal_adapter_receipt_id"]
                == stop_signal_adapter_receipt["receipt_id"]
                and approved_command["stop_signal_adapter_receipt_digest"]
                == stop_signal_adapter_receipt["receipt_digest"]
            ),
            "approved_command_legal_execution_bound": (
                approved_command["legal_execution_id"] == legal_execution["execution_id"]
                and approved_command["legal_execution_digest"] == legal_execution["digest"]
            ),
            "released": handle_validation["released"],
            "veto_handle_released": veto_handle_validation["released"],
            "emergency_stop_release_sequence_valid": handle_validation[
                "emergency_stop_release_sequence_valid"
            ],
            "authorization_ok": authorization_validation["ok"],
            "authorization_ready": authorization_validation["authorization_ready"],
            "authorization_window_open": authorization_validation["window_open"],
            "authorization_delivery_scope": authorization_validation["delivery_scope"],
            "authorization_matches_command": authorization_validation["instruction_digest_matches"]
            and authorization_validation["intent_digest_matches"],
            "authorization_stop_signal_path_ready": authorization_validation[
                "stop_signal_path_ready"
            ],
            "authorization_stop_signal_adapter_receipt_ready": authorization_validation[
                "stop_signal_adapter_receipt_ready"
            ],
            "authorization_guardian_oversight_gate_ready": authorization_validation[
                "guardian_oversight_gate_ready"
            ],
            "emergency_stop_ok": emergency_stop_validation["ok"],
            "emergency_stop_trigger_source_valid": emergency_stop_validation["trigger_source_valid"],
            "emergency_stop_latched": emergency_stop_validation["safe_state_latched"],
            "emergency_stop_hardware_interlock": emergency_stop_validation[
                "hardware_interlock_engaged"
            ],
            "emergency_stop_bus_delivery_latched": emergency_stop_validation[
                "bus_delivery_latched"
            ],
            "emergency_stop_release_required": emergency_stop_validation["release_required"],
            "emergency_stop_bound_to_command": emergency_stop["command_id"]
            == approved_command["command_id"]
            and emergency_stop["bound_command_digest"] == approved_command["instruction_digest"],
            "emergency_stop_bound_to_authorization": emergency_stop_validation[
                "authorization_bound"
            ]
            and emergency_stop["authorization_id"] == authorization["authorization_id"]
            and emergency_stop["bound_authorization_digest"]
            == authorization["authorization_digest"],
            "emergency_stop_bound_to_stop_signal_path": emergency_stop_validation[
                "stop_signal_path_bound"
            ]
            and emergency_stop_validation["trigger_binding_matched"]
            and emergency_stop["stop_signal_path_id"] == stop_signal_path["path_id"]
            and emergency_stop["stop_signal_path_digest"] == stop_signal_path["path_digest"],
            "emergency_stop_bound_to_stop_signal_adapter_receipt": emergency_stop_validation[
                "stop_signal_adapter_receipt_bound"
            ]
            and emergency_stop["stop_signal_adapter_receipt_id"]
            == stop_signal_adapter_receipt["receipt_id"]
            and emergency_stop["stop_signal_adapter_receipt_digest"]
            == stop_signal_adapter_receipt["receipt_digest"],
            "release_after_stop": release["status"] == "released",
            "ok": handle_validation["ok"]
            and veto_handle_validation["ok"]
            and motor_plan_validation["ok"]
            and stop_signal_path_validation["ok"]
            and stop_signal_adapter_validation["ok"]
            and legal_execution_validation["ok"]
            and guardian_oversight_gate_validation["ok"]
            and authorization_validation["ok"]
            and emergency_stop_validation["ok"],
        }

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
            event_type="ewa.motor_plan.prepared",
            payload=motor_plan,
            actor="ExternalWorldAgentController",
            category="interface-ewa-plan",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.stop_signal_path.prepared",
            payload=stop_signal_path,
            actor="ExternalWorldAgentController",
            category="interface-ewa-stop-signal",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.stop_signal_adapter.probed",
            payload=stop_signal_adapter_receipt,
            actor="ExternalWorldAgentController",
            category="interface-ewa-stop-signal-adapter",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.legal_execution.prepared",
            payload=legal_execution,
            actor="ExternalWorldAgentController",
            category="interface-ewa-legal",
            layer="L6",
            signature_roles=["guardian", "third_party"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.oversight.ewa-authorization.satisfied",
            payload=guardian_oversight_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.command.authorized",
            payload=authorization,
            actor="ExternalWorldAgentController",
            category="interface-ewa-authorization",
            layer="L6",
            signature_roles=["guardian", "third_party"],
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
            event_type="ewa.emergency_stopped",
            payload=emergency_stop,
            actor="GuardianWatchdog",
            category="interface-ewa-emergency-stop",
            layer="L6",
            signature_roles=["guardian"],
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
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.handle.acquired",
            payload=veto_handle,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["self"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="ewa.handle.released",
            payload=veto_release,
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
            "handle_validation": handle_validation,
            "motor_plan": motor_plan,
            "motor_plan_validation": motor_plan_validation,
            "stop_signal_path": stop_signal_path,
            "stop_signal_path_validation": stop_signal_path_validation,
            "stop_signal_adapter_receipt": stop_signal_adapter_receipt,
            "stop_signal_adapter_validation": stop_signal_adapter_validation,
            "legal_execution": legal_execution,
            "legal_execution_validation": legal_execution_validation,
            "reviewers": {
                "alpha": reviewer_alpha,
                "beta": reviewer_beta,
            },
            "guardian_oversight_event": guardian_oversight_event,
            "guardian_oversight_gate": guardian_oversight_gate,
            "guardian_oversight_gate_validation": guardian_oversight_gate_validation,
            "authorization": authorization,
            "authorization_validation": authorization_validation,
            "approved_command": approved_command,
            "observation": observation,
            "emergency_stop": emergency_stop,
            "emergency_stop_validation": emergency_stop_validation,
            "veto": veto,
            "veto_handle": veto_handle_snapshot,
            "veto_handle_validation": veto_handle_validation,
            "veto_release": veto_release,
            "release": release,
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    @staticmethod
    def _wms_engine_route_trace_fixture(session_id: str) -> Dict[str, Any]:
        trace_suffix = sha256_text(f"wms-engine-route:{session_id}")[:16]
        authority_plane_ref = f"authority-plane://federation/{trace_suffix}"
        route_target_discovery_ref = f"authority-route-targets://federation/{trace_suffix}"
        authority_cluster_ref = "authority-cluster://federation/wms-engine-adapter"
        route_bindings: List[Dict[str, Any]] = []
        route_specs = [
            {
                "key_server_ref": "keyserver://federation/wms-engine-notary-a",
                "server_role": "quorum-notary",
                "server_endpoint": "https://192.0.2.10:44310/wms-engine-route-1",
                "remote_host_ref": "host://federation/wms-engine-edge-a",
                "remote_host_attestation_ref": "host-attestation://federation/wms-engine-edge-a/2026-04-25",
                "remote_ip": "192.0.2.10",
                "remote_jurisdiction": "JP-13",
                "remote_network_zone": "apne1",
                "matched_root_refs": ["root://federation/pki-a"],
            },
            {
                "key_server_ref": "keyserver://federation/wms-engine-mirror-b",
                "server_role": "directory-mirror",
                "server_endpoint": "https://198.51.100.20:44320/wms-engine-route-2",
                "remote_host_ref": "host://federation/wms-engine-edge-b",
                "remote_host_attestation_ref": "host-attestation://federation/wms-engine-edge-b/2026-04-25",
                "remote_ip": "198.51.100.20",
                "remote_jurisdiction": "US-CA",
                "remote_network_zone": "usw2",
                "matched_root_refs": ["root://federation/pki-b"],
            },
        ]
        for index, spec in enumerate(route_specs, start=1):
            route_binding_ref = f"authority-route://federation/wms-engine-{index}"
            local_ip = "203.0.113.5"
            local_port = 53100 + index
            remote_port = 44300 + (index * 10)
            tuple_digest = sha256_text(
                canonical_json(
                    {
                        "local_ip": local_ip,
                        "local_port": local_port,
                        "remote_ip": spec["remote_ip"],
                        "remote_port": remote_port,
                    }
                )
            )
            host_binding_digest = sha256_text(
                canonical_json(
                    {
                        "tuple_digest": tuple_digest,
                        "remote_host_ref": spec["remote_host_ref"],
                        "remote_host_attestation_ref": spec[
                            "remote_host_attestation_ref"
                        ],
                        "authority_cluster_ref": authority_cluster_ref,
                    }
                )
            )
            response_digest = sha256_text(
                canonical_json(
                    {
                        "route_binding_ref": route_binding_ref,
                        "engine_adapter": "reference-wms",
                        "session_id": session_id,
                    }
                )
            )
            route_bindings.append(
                {
                    "key_server_ref": spec["key_server_ref"],
                    "server_role": spec["server_role"],
                    "authority_status": "active",
                    "server_endpoint": spec["server_endpoint"],
                    "server_name": MTLS_SERVER_NAME,
                    "remote_host_ref": spec["remote_host_ref"],
                    "remote_host_attestation_ref": spec["remote_host_attestation_ref"],
                    "authority_cluster_ref": authority_cluster_ref,
                    "remote_jurisdiction": spec["remote_jurisdiction"],
                    "remote_network_zone": spec["remote_network_zone"],
                    "route_binding_ref": route_binding_ref,
                    "matched_root_refs": spec["matched_root_refs"],
                    "mtls_status": "authenticated",
                    "response_digest_bound": True,
                    "os_observer_receipt": {
                        "kind": "distributed_transport_os_observer_receipt",
                        "schema_version": "1.0.0",
                        "receipt_id": f"authority-os-observer://wms-engine-{index}",
                        "observer_profile": "os-native-tcp-observer-v1",
                        "observed_at": "2026-04-25T02:30:00Z",
                        "local_ip": local_ip,
                        "local_port": local_port,
                        "remote_ip": spec["remote_ip"],
                        "remote_port": remote_port,
                        "remote_host_ref": spec["remote_host_ref"],
                        "remote_host_attestation_ref": spec[
                            "remote_host_attestation_ref"
                        ],
                        "authority_cluster_ref": authority_cluster_ref,
                        "owning_pid": 24000 + index,
                        "observed_sources": ["lsof", "netstat"],
                        "connection_states": ["ESTABLISHED"],
                        "tuple_digest": tuple_digest,
                        "host_binding_digest": host_binding_digest,
                        "receipt_status": "observed",
                    },
                    "socket_trace": {
                        "local_ip": local_ip,
                        "local_port": local_port,
                        "remote_ip": spec["remote_ip"],
                        "remote_port": remote_port,
                        "non_loopback": True,
                        "transport_profile": "mtls-socket-trace-v1",
                        "tls_version": "TLSv1.3",
                        "cipher_suite": "TLS_AES_256_GCM_SHA384",
                        "peer_certificate_fingerprint": sha256_text(
                            f"peer-cert-{index}"
                        ),
                        "client_certificate_fingerprint": sha256_text(
                            "client-cert-reference-wms"
                        ),
                        "request_bytes": 128,
                        "response_bytes": 512 + index,
                        "http_status": 200,
                        "response_digest": response_digest,
                        "connect_latency_ms": 4.0 + index,
                        "tls_handshake_latency_ms": 9.5 + index,
                        "round_trip_latency_ms": 13.0 + index,
                    },
                }
            )
        payload = {
            "kind": "distributed_transport_authority_route_trace",
            "schema_version": "1.0.0",
            "trace_ref": f"authority-route-trace://federation/{trace_suffix}",
            "authority_plane_ref": authority_plane_ref,
            "authority_plane_digest": sha256_text(authority_plane_ref),
            "route_target_discovery_ref": route_target_discovery_ref,
            "route_target_discovery_digest": sha256_text(route_target_discovery_ref),
            "envelope_ref": f"distributed-envelope-{trace_suffix[:12]}",
            "envelope_digest": sha256_text(f"distributed-envelope:{trace_suffix}"),
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "trace_profile": "non-loopback-mtls-authority-route-v1",
            "socket_trace_profile": "mtls-socket-trace-v1",
            "os_observer_profile": "os-native-tcp-observer-v1",
            "cross_host_binding_profile": "attested-cross-host-authority-binding-v1",
            "route_target_discovery_profile": "bounded-authority-route-target-discovery-v1",
            "ca_bundle_ref": CA_BUNDLE_REF,
            "client_certificate_ref": CLIENT_CERTIFICATE_REF,
            "server_name": MTLS_SERVER_NAME,
            "authority_cluster_ref": authority_cluster_ref,
            "route_count": len(route_bindings),
            "distinct_remote_host_count": len(
                {binding["remote_host_ref"] for binding in route_bindings}
            ),
            "mtls_authenticated_count": len(route_bindings),
            "trusted_root_refs": ["root://federation/pki-a", "root://federation/pki-b"],
            "non_loopback_verified": True,
            "authority_plane_bound": True,
            "response_digest_bound": True,
            "socket_trace_complete": True,
            "os_observer_complete": True,
            "route_target_discovery_bound": True,
            "cross_host_verified": True,
            "route_bindings": route_bindings,
            "trace_status": "authenticated",
            "recorded_at": "2026-04-25T02:30:00Z",
            "total_connect_latency_ms": 11.0,
            "total_handshake_latency_ms": 22.0,
            "total_round_trip_latency_ms": 29.0,
        }
        payload["digest"] = sha256_text(canonical_json(payload))
        return payload

    @staticmethod
    def _wms_engine_packet_capture_fixture(
        authority_route_trace: Dict[str, Any],
    ) -> Dict[str, Any]:
        route_exports: List[Dict[str, Any]] = []
        for binding in authority_route_trace["route_bindings"]:
            socket_trace = binding["socket_trace"]
            outbound_tuple_digest = sha256_text(
                canonical_json(
                    {
                        "direction": "outbound-request",
                        "local_ip": socket_trace["local_ip"],
                        "local_port": socket_trace["local_port"],
                        "remote_ip": socket_trace["remote_ip"],
                        "remote_port": socket_trace["remote_port"],
                    }
                )
            )
            inbound_tuple_digest = sha256_text(
                canonical_json(
                    {
                        "direction": "inbound-response",
                        "local_ip": socket_trace["local_ip"],
                        "local_port": socket_trace["local_port"],
                        "remote_ip": socket_trace["remote_ip"],
                        "remote_port": socket_trace["remote_port"],
                    }
                )
            )
            route_exports.append(
                {
                    "key_server_ref": binding["key_server_ref"],
                    "route_binding_ref": binding["route_binding_ref"],
                    "local_ip": socket_trace["local_ip"],
                    "local_port": socket_trace["local_port"],
                    "remote_ip": socket_trace["remote_ip"],
                    "remote_port": socket_trace["remote_port"],
                    "outbound_tuple_digest": outbound_tuple_digest,
                    "inbound_tuple_digest": inbound_tuple_digest,
                    "packet_order": ["outbound-request", "inbound-response"],
                    "outbound_request_bytes": socket_trace["request_bytes"],
                    "inbound_response_bytes": socket_trace["response_bytes"],
                    "outbound_payload_digest": sha256_text(
                        canonical_json(
                            {
                                "route_binding_ref": binding["route_binding_ref"],
                                "direction": "outbound-request",
                                "response_digest": socket_trace["response_digest"],
                            }
                        )
                    ),
                    "inbound_payload_digest": sha256_text(
                        canonical_json(
                            {
                                "route_binding_ref": binding["route_binding_ref"],
                                "direction": "inbound-response",
                                "response_digest": socket_trace["response_digest"],
                            }
                        )
                    ),
                    "readback_packet_count": 2,
                    "readback_verified": True,
                    "os_native_readback_verified": True,
                }
            )
        trace_suffix = authority_route_trace["trace_ref"].split("/")[-1]
        readback_payload = {
            "route_exports": route_exports,
            "os_native_readback": {"available": True, "verified": True},
        }
        artifact_digest = sha256_text(
            canonical_json(
                {
                    "trace_ref": authority_route_trace["trace_ref"],
                    "route_exports": route_exports,
                    "artifact_format": "pcap",
                }
            )
        )
        payload = {
            "capture_ref": f"authority-packet-capture://federation/{trace_suffix}",
            "trace_ref": authority_route_trace["trace_ref"],
            "trace_digest": authority_route_trace["digest"],
            "authority_plane_ref": authority_route_trace["authority_plane_ref"],
            "authority_plane_digest": authority_route_trace["authority_plane_digest"],
            "envelope_ref": authority_route_trace["envelope_ref"],
            "envelope_digest": authority_route_trace["envelope_digest"],
            "council_tier": authority_route_trace["council_tier"],
            "transport_profile": authority_route_trace["transport_profile"],
            "capture_profile": "trace-bound-pcap-export-v1",
            "artifact_format": "pcap",
            "readback_profile": "pcap-readback-v1",
            "os_native_readback_profile": "tcpdump-readback-v1",
            "route_count": authority_route_trace["route_count"],
            "packet_count": authority_route_trace["route_count"] * 2,
            "artifact_size_bytes": 512 + (authority_route_trace["route_count"] * 128),
            "artifact_digest": artifact_digest,
            "readback_digest": sha256_text(canonical_json(readback_payload)),
            "route_exports": route_exports,
            "os_native_readback_available": True,
            "os_native_readback_ok": True,
            "export_status": "verified",
            "recorded_at": "2026-04-25T02:31:00Z",
        }
        payload["digest"] = sha256_text(canonical_json(payload))
        return {
            "kind": "distributed_transport_packet_capture_export",
            "schema_version": "1.0.0",
            **payload,
        }

    @staticmethod
    def _wms_engine_privileged_capture_fixture(
        authority_route_trace: Dict[str, Any],
        packet_capture_export: Dict[str, Any],
    ) -> Dict[str, Any]:
        route_binding_refs = sorted(
            binding["route_binding_ref"]
            for binding in authority_route_trace["route_bindings"]
        )
        local_ips = sorted(
            {
                binding["socket_trace"]["local_ip"]
                for binding in authority_route_trace["route_bindings"]
            }
        )
        clauses: List[str] = []
        for binding in authority_route_trace["route_bindings"]:
            socket_trace = binding["socket_trace"]
            clauses.append(
                "("
                f"src host {socket_trace['local_ip']} and src port {socket_trace['local_port']} and "
                f"dst host {socket_trace['remote_ip']} and dst port {socket_trace['remote_port']}"
                ")"
            )
            clauses.append(
                "("
                f"src host {socket_trace['remote_ip']} and src port {socket_trace['remote_port']} and "
                f"dst host {socket_trace['local_ip']} and dst port {socket_trace['local_port']}"
                ")"
            )
        capture_filter = "tcp and (" + " or ".join(clauses) + ")"
        trace_suffix = authority_route_trace["trace_ref"].split("/")[-1]
        capture_command = [
            "/usr/sbin/tcpdump",
            "-i",
            "en0",
            "-nn",
            "-U",
            "-w",
            "{capture_output_path}",
            capture_filter,
        ]
        payload = {
            "acquisition_ref": f"authority-live-capture://federation/{trace_suffix}",
            "trace_ref": authority_route_trace["trace_ref"],
            "trace_digest": authority_route_trace["digest"],
            "capture_ref": packet_capture_export["capture_ref"],
            "capture_digest": packet_capture_export["digest"],
            "authority_plane_ref": authority_route_trace["authority_plane_ref"],
            "authority_plane_digest": authority_route_trace["authority_plane_digest"],
            "envelope_ref": authority_route_trace["envelope_ref"],
            "envelope_digest": authority_route_trace["envelope_digest"],
            "council_tier": authority_route_trace["council_tier"],
            "transport_profile": authority_route_trace["transport_profile"],
            "acquisition_profile": "bounded-live-interface-capture-acquisition-v1",
            "broker_profile": "delegated-privileged-capture-broker-v1",
            "privilege_mode": "delegated-broker",
            "lease_ref": f"capture-lease://federation/{trace_suffix}",
            "broker_attestation_ref": f"broker://authority-capture/{trace_suffix}",
            "interface_name": "en0",
            "local_ips": local_ips,
            "capture_filter": capture_filter,
            "filter_digest": sha256_text(capture_filter),
            "route_binding_refs": route_binding_refs,
            "capture_command": capture_command,
            "lease_duration_s": 300,
            "lease_expires_at": "2026-04-25T02:36:00Z",
            "grant_status": "granted",
            "recorded_at": "2026-04-25T02:31:00Z",
        }
        payload["digest"] = sha256_text(canonical_json(payload))
        return {
            "kind": "distributed_transport_privileged_capture_acquisition",
            "schema_version": "1.0.0",
            **payload,
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
        observer = self.identity.create(
            human_consent_proof="consent://wms-observer-demo/v1",
            metadata={"display_name": "Shared Observer"},
        )
        session = self.wms.create_session(
            [identity.identity_id, peer.identity_id, observer.identity_id],
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

        time_rate_attestation_subject = self.wms.build_time_rate_attestation_subject(
            session["session_id"],
            proposer_id=observer.identity_id,
            requested_time_rate=1.25,
        )
        time_rate_attestation_payload_template = {
            "public_fields": [
                "time_rate_attestation_subject_digest",
                "participant_id",
                "baseline_time_rate",
                "requested_time_rate",
                "attestation_decision",
            ],
            "intimate_fields": [],
            "sealed_fields": [],
        }
        time_rate_attestation_imc_sessions = []
        time_rate_attestation_messages = []
        time_rate_attestation_receipts = []
        for participant_id in [identity.identity_id, peer.identity_id, observer.identity_id]:
            attestation_counterparty = (
                peer.identity_id if participant_id == identity.identity_id else identity.identity_id
            )
            attestation_imc_session = self.imc.open_session(
                initiator_id=attestation_counterparty,
                peer_id=participant_id,
                mode="text",
                initiator_template=time_rate_attestation_payload_template,
                peer_template=time_rate_attestation_payload_template,
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=True,
            )
            attestation_message = self.imc.send(
                attestation_imc_session["session_id"],
                sender_id=participant_id,
                summary=(
                    "participant subjective-time attestation for WMS private escape "
                    f"{time_rate_attestation_subject['digest'][:12]}"
                ),
                payload={
                    "time_rate_attestation_subject_digest": time_rate_attestation_subject[
                        "digest"
                    ],
                    "participant_id": participant_id,
                    "baseline_time_rate": time_rate_attestation_subject[
                        "baseline_time_rate"
                    ],
                    "requested_time_rate": time_rate_attestation_subject[
                        "requested_time_rate"
                    ],
                    "attestation_decision": "attest",
                },
            )
            time_rate_attestation_messages.append(attestation_message)
            time_rate_attestation_imc_sessions.append(
                self.imc.snapshot(attestation_imc_session["session_id"])
            )
            time_rate_attestation_receipts.append(
                self.wms.build_time_rate_attestation_receipt(
                    session["session_id"],
                    participant_id=participant_id,
                    time_rate_attestation_subject_digest=time_rate_attestation_subject[
                        "digest"
                    ],
                    baseline_time_rate=time_rate_attestation_subject["baseline_time_rate"],
                    requested_time_rate=time_rate_attestation_subject["requested_time_rate"],
                    imc_session=attestation_imc_session,
                    imc_message=attestation_message,
                )
            )

        time_rate_deviation = self.wms.propose_diff(
            session["session_id"],
            proposer_id=observer.identity_id,
            candidate_objects=["atrium", "council-table", "shared-lantern", "memory-banner"],
            affected_object_ratio=0.01,
            attested=True,
            requested_time_rate=1.25,
            time_rate_attestation_receipts=time_rate_attestation_receipts,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.time_rate.deviation",
            payload=time_rate_deviation,
            actor="WorldModelSync",
            category="interface-wms",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        proposed_physics_rules_ref = "physics://shared-atrium/low-gravity-council-v1"
        physics_change_rationale = (
            "bounded low-gravity rehearsal must remain reversible for every participant"
        )
        approval_subject = self.wms.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by=identity.identity_id,
            proposed_physics_rules_ref=proposed_physics_rules_ref,
            rationale=physics_change_rationale,
        )
        approval_payload_template = {
            "public_fields": [
                "approval_subject_digest",
                "participant_id",
                "approval_decision",
            ],
            "intimate_fields": [],
            "sealed_fields": [],
        }
        approval_imc_sessions = []
        approval_messages = []
        approval_transport_receipts = []
        for participant_id in [identity.identity_id, peer.identity_id, observer.identity_id]:
            approval_counterparty = (
                peer.identity_id if participant_id == identity.identity_id else identity.identity_id
            )
            approval_imc_session = self.imc.open_session(
                initiator_id=approval_counterparty,
                peer_id=participant_id,
                mode="text",
                initiator_template=approval_payload_template,
                peer_template=approval_payload_template,
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=True,
            )
            approval_message = self.imc.send(
                approval_imc_session["session_id"],
                sender_id=participant_id,
                summary=(
                    "participant approval for reversible shared-world physics change "
                    f"{approval_subject['digest'][:12]}"
                ),
                payload={
                    "approval_subject_digest": approval_subject["digest"],
                    "participant_id": participant_id,
                    "approval_decision": "approve",
                },
            )
            approval_messages.append(approval_message)
            approval_imc_sessions.append(self.imc.snapshot(approval_imc_session["session_id"]))
            approval_transport_receipts.append(
                self.wms.build_participant_approval_transport_receipt(
                    session["session_id"],
                    participant_id=participant_id,
                    approval_subject_digest=approval_subject["digest"],
                    imc_session=approval_imc_session,
                    imc_message=approval_message,
                )
            )
        approval_collection_receipt = self.wms.build_approval_collection_receipt(
            session["session_id"],
            approval_subject_digest=approval_subject["digest"],
            approval_transport_receipts=approval_transport_receipts,
        )
        approval_collection_validation = self.wms.validate_approval_collection_receipt(
            approval_collection_receipt,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=approval_subject["digest"],
            approval_transport_receipts=approval_transport_receipts,
        )
        approval_fanout_results = []
        for index, participant_id in enumerate(
            [identity.identity_id, peer.identity_id, observer.identity_id],
            start=1,
        ):
            participant_pair = (
                [identity.identity_id, peer.identity_id]
                if participant_id == identity.identity_id
                else [identity.identity_id, participant_id]
            )
            approval_result_digest = self.wms.build_distributed_approval_result_digest(
                approval_subject_digest=approval_subject["digest"],
                participant_id=participant_id,
                approval_collection_digest=approval_collection_receipt["digest"],
            )
            fanout_envelope = self.distributed_transport.issue_federation_handoff(
                topology_ref=f"topology://wms-approval-fanout/{session['session_id']}/{index}",
                proposal_ref=f"wms-physics-approval://{approval_subject['digest'][:16]}/{index}",
                payload_ref=f"cas://sha256/{approval_subject['digest']}",
                payload_digest=approval_subject["digest"],
                participant_identity_ids=participant_pair,
            )
            fanout_receipt = self.distributed_transport.record_receipt(
                fanout_envelope,
                result_ref=f"resolution://wms-approval/{index}",
                result_digest=approval_result_digest,
                participant_ids=[
                    attestation.participant_id
                    for attestation in fanout_envelope.participant_attestations
                ],
                channel_binding_ref=fanout_envelope.channel_binding_ref,
                verified_root_refs=["root://federation/pki-a"],
                key_epoch=1,
                hop_nonce_chain=[f"hop://wms-approval/{index}/relay-a"],
            )
            approval_fanout_results.append(
                {
                    "participant_id": participant_id,
                    "approval_result_ref": f"resolution://wms-approval/{index}",
                    "approval_result_digest": approval_result_digest,
                    "transport_envelope": fanout_envelope.to_dict(),
                    "transport_receipt": fanout_receipt.to_dict(),
                }
            )
        approval_fanout_receipt = self.wms.build_distributed_approval_fanout_receipt(
            session["session_id"],
            approval_subject_digest=approval_subject["digest"],
            approval_collection_receipt=approval_collection_receipt,
            participant_fanout_results=approval_fanout_results,
        )
        approval_fanout_validation = self.wms.validate_distributed_approval_fanout_receipt(
            approval_fanout_receipt,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=approval_subject["digest"],
            approval_collection_digest=approval_collection_receipt["digest"],
        )
        approval_fanout_retry_attempts = [
            {
                "retry_attempt_ref": (
                    "retry://wms-approval-fanout/"
                    f"{approval_subject['digest'][:12]}/observer-attempt-1"
                ),
                "participant_id": observer.identity_id,
                "attempt_index": 1,
                "outage_kind": "timeout",
                "retry_after_ms": 250,
                "retry_decision": "retry",
                "recovery_result_digest": approval_fanout_results[-1][
                    "approval_result_digest"
                ],
                "recovery_transport_receipt_digest": approval_fanout_results[-1][
                    "transport_receipt"
                ]["digest"],
            }
        ]
        approval_fanout_retry_receipt = self.wms.build_distributed_approval_fanout_receipt(
            session["session_id"],
            approval_subject_digest=approval_subject["digest"],
            approval_collection_receipt=approval_collection_receipt,
            participant_fanout_results=approval_fanout_results,
            fanout_retry_attempts=approval_fanout_retry_attempts,
        )
        approval_fanout_retry_validation = self.wms.validate_distributed_approval_fanout_receipt(
            approval_fanout_retry_receipt,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=approval_subject["digest"],
            approval_collection_digest=approval_collection_receipt["digest"],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.approval_fanout.bound",
            payload=approval_fanout_retry_receipt,
            actor="WorldModelSync",
            category="interface-wms-approval",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        pre_physics_state = self.wms.snapshot(session["session_id"])
        physics_change = self.wms.propose_physics_rules_change(
            session["session_id"],
            requested_by=identity.identity_id,
            proposed_physics_rules_ref=proposed_physics_rules_ref,
            rationale=physics_change_rationale,
            participant_approvals=[identity.identity_id, peer.identity_id, observer.identity_id],
            guardian_attested=True,
            approval_transport_receipts=approval_transport_receipts,
            approval_collection_receipt=approval_collection_receipt,
            approval_fanout_receipt=approval_fanout_retry_receipt,
        )
        post_physics_state = self.wms.snapshot(session["session_id"])
        physics_change_validation = self.wms.validate_physics_rules_change(physics_change)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.physics_rules.changed",
            payload=physics_change,
            actor="WorldModelSync",
            category="interface-wms-physics",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        physics_revert = self.wms.revert_physics_rules_change(
            session["session_id"],
            change_id=physics_change["change_id"],
            requested_by=identity.identity_id,
            reason="bounded rehearsal complete; restore baseline shared physics",
            guardian_attested=True,
        )
        post_revert_state = self.wms.snapshot(session["session_id"])
        physics_revert_validation = self.wms.validate_physics_rules_change(physics_revert)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.physics_rules.reverted",
            payload=physics_revert,
            actor="WorldModelSync",
            category="interface-wms-physics",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        engine_session_ref = f"engine-session://wms-demo/{session['session_id']}"
        engine_transaction_log_ref = f"engine-log://wms-demo/{session['session_id']}/transactions"
        pre_physics_state_digest = sha256_text(canonical_json(pre_physics_state))
        post_physics_state_digest = sha256_text(canonical_json(post_physics_state))
        post_revert_state_digest = sha256_text(canonical_json(post_revert_state))
        time_rate_deviation_digest = sha256_text(canonical_json(time_rate_deviation))
        engine_source_artifact_digests = {
            "time_rate_escape_evidence": time_rate_deviation_digest,
            "approval_collection_bound": approval_collection_receipt["digest"],
            "approval_fanout_bound": approval_fanout_retry_receipt["digest"],
            "physics_rules_apply": physics_change["digest"],
            "physics_rules_revert": physics_revert["digest"],
        }
        engine_transaction_entries = [
            self.wms.build_engine_transaction_entry(
                transaction_id=f"engine-txn://wms-demo/{session['session_id']}/001",
                transaction_index=1,
                operation="time_rate_escape_evidence",
                source_artifact_kind="wms_reconcile",
                source_artifact_ref=f"wms-reconcile://{time_rate_deviation['reconcile_id']}",
                source_artifact_digest=time_rate_deviation_digest,
                engine_session_ref=engine_session_ref,
                engine_state_before_digest=pre_physics_state_digest,
                engine_state_after_digest=pre_physics_state_digest,
                participant_ids=[identity.identity_id, peer.identity_id, observer.identity_id],
            ),
            self.wms.build_engine_transaction_entry(
                transaction_id=f"engine-txn://wms-demo/{session['session_id']}/002",
                transaction_index=2,
                operation="approval_collection_bound",
                source_artifact_kind="wms_approval_collection_receipt",
                source_artifact_ref=f"wms-approval-collection://{approval_collection_receipt['digest'][:16]}",
                source_artifact_digest=approval_collection_receipt["digest"],
                engine_session_ref=engine_session_ref,
                engine_state_before_digest=pre_physics_state_digest,
                engine_state_after_digest=pre_physics_state_digest,
                participant_ids=[identity.identity_id, peer.identity_id, observer.identity_id],
            ),
            self.wms.build_engine_transaction_entry(
                transaction_id=f"engine-txn://wms-demo/{session['session_id']}/003",
                transaction_index=3,
                operation="approval_fanout_bound",
                source_artifact_kind="wms_distributed_approval_fanout_receipt",
                source_artifact_ref=f"wms-approval-fanout://{approval_fanout_retry_receipt['digest'][:16]}",
                source_artifact_digest=approval_fanout_retry_receipt["digest"],
                engine_session_ref=engine_session_ref,
                engine_state_before_digest=pre_physics_state_digest,
                engine_state_after_digest=pre_physics_state_digest,
                participant_ids=[identity.identity_id, peer.identity_id, observer.identity_id],
            ),
            self.wms.build_engine_transaction_entry(
                transaction_id=f"engine-txn://wms-demo/{session['session_id']}/004",
                transaction_index=4,
                operation="physics_rules_apply",
                source_artifact_kind="wms_physics_rules_change_receipt",
                source_artifact_ref=f"wms-physics-change://{physics_change['change_id']}",
                source_artifact_digest=physics_change["digest"],
                engine_session_ref=engine_session_ref,
                engine_state_before_digest=pre_physics_state_digest,
                engine_state_after_digest=post_physics_state_digest,
                participant_ids=[identity.identity_id, peer.identity_id, observer.identity_id],
            ),
            self.wms.build_engine_transaction_entry(
                transaction_id=f"engine-txn://wms-demo/{session['session_id']}/005",
                transaction_index=5,
                operation="physics_rules_revert",
                source_artifact_kind="wms_physics_rules_change_receipt",
                source_artifact_ref=f"wms-physics-revert://{physics_revert['change_id']}",
                source_artifact_digest=physics_revert["digest"],
                engine_session_ref=engine_session_ref,
                engine_state_before_digest=post_physics_state_digest,
                engine_state_after_digest=post_revert_state_digest,
                participant_ids=[identity.identity_id, peer.identity_id, observer.identity_id],
            ),
        ]
        engine_transaction_log = self.wms.build_engine_transaction_log_receipt(
            session["session_id"],
            engine_adapter_ref="engine-adapter://reference-wms/multi-user-transaction-log",
            engine_adapter_key_ref=(
                "engine-key://reference-wms/multi-user-transaction-log/signer-2026-04"
            ),
            engine_session_ref=engine_session_ref,
            transaction_log_ref=engine_transaction_log_ref,
            transaction_entries=engine_transaction_entries,
            source_artifact_digests=engine_source_artifact_digests,
        )
        engine_transaction_log_validation = self.wms.validate_engine_transaction_log_receipt(
            engine_transaction_log,
            source_artifact_digests=engine_source_artifact_digests,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.engine.transaction_log_bound",
            payload=engine_transaction_log,
            actor="WorldModelSync",
            category="interface-wms-engine",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        engine_authority_route_trace = self._wms_engine_route_trace_fixture(
            session["session_id"]
        )
        engine_route_binding = self.wms.build_engine_route_binding_receipt(
            session["session_id"],
            engine_transaction_log_receipt=engine_transaction_log,
            authority_route_trace=engine_authority_route_trace,
        )
        engine_route_binding_validation = self.wms.validate_engine_route_binding_receipt(
            engine_route_binding,
            engine_transaction_log_receipt=engine_transaction_log,
            authority_route_trace=engine_authority_route_trace,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.engine.route_trace_bound",
            payload=engine_route_binding,
            actor="WorldModelSync",
            category="interface-wms-engine",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        engine_packet_capture_export = self._wms_engine_packet_capture_fixture(
            engine_authority_route_trace
        )
        engine_privileged_capture_acquisition = (
            self._wms_engine_privileged_capture_fixture(
                engine_authority_route_trace,
                engine_packet_capture_export,
            )
        )
        engine_capture_binding = self.wms.build_engine_capture_binding_receipt(
            session["session_id"],
            engine_route_binding_receipt=engine_route_binding,
            packet_capture_export=engine_packet_capture_export,
            privileged_capture_acquisition=engine_privileged_capture_acquisition,
        )
        engine_capture_binding_validation = self.wms.validate_engine_capture_binding_receipt(
            engine_capture_binding,
            engine_route_binding_receipt=engine_route_binding,
            packet_capture_export=engine_packet_capture_export,
            privileged_capture_acquisition=engine_privileged_capture_acquisition,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.engine.capture_binding_bound",
            payload=engine_capture_binding,
            actor="WorldModelSync",
            category="interface-wms-engine",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        @contextmanager
        def live_authority_slo_bridge(slo_payload: Dict[str, Any]):
            class Handler(BaseHTTPRequestHandler):
                protocol_version = "HTTP/1.0"

                def do_GET(self) -> None:  # noqa: N802
                    body = json.dumps(slo_payload).encode("utf-8")
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

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/authority-slo"
            try:
                yield endpoint
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=1.0)

        route_health_observation = {
            "observation_ref": (
                "route-health://federation/wms-approval/"
                f"{observer.identity_id.split('://', 1)[-1]}/timeout-1"
            ),
            "authority_ref": "authority://federation/wms-approval",
            "route_ref": (
                "route://federation/wms-approval/observer/"
                f"{approval_subject['digest'][:12]}"
            ),
            "participant_id": observer.identity_id,
            "outage_kind": "timeout",
            "route_status": "partial-outage",
            "remote_jurisdiction": "JP-13",
            "jurisdiction_policy_registry_ref": (
                "policy-registry://jp-13/wms-authority-retry/v1"
            ),
            "jurisdiction_rate_limit_ref": (
                "rate-limit://jp-13/wms-approval-retry-budget/v1"
            ),
            "jurisdiction_retry_limit_ms": 500,
            "authority_slo_snapshot_ref": (
                "authority-slo://federation/wms-approval/observer-timeout/v1"
            ),
            "authority_slo_retry_limit_ms": 500,
            "signer_key_ref": "key://federation/jp-13/wms-retry-signer",
            "observed_latency_ms": 860,
            "success_ratio": 0.667,
            "consecutive_failures": 1,
        }
        jurisdiction_policy_registry_digest = sha256_text(
            canonical_json(
                {
                    "registry_policy_id": "registry-bound-authority-retry-slo-v1",
                    "registry_profile": "jurisdiction-policy-registry-bound-retry-v1",
                    "jurisdiction_policy_registry_ref": route_health_observation[
                        "jurisdiction_policy_registry_ref"
                    ],
                    "remote_jurisdiction": route_health_observation[
                        "remote_jurisdiction"
                    ],
                    "jurisdiction_rate_limit_ref": route_health_observation[
                        "jurisdiction_rate_limit_ref"
                    ],
                    "jurisdiction_retry_limit_ms": route_health_observation[
                        "jurisdiction_retry_limit_ms"
                    ],
                    "signer_key_ref": route_health_observation["signer_key_ref"],
                }
            )
        )
        live_slo_payload = {
            "checked_at": "2026-04-26T00:10:00Z",
            "authority_ref": route_health_observation["authority_ref"],
            "route_ref": route_health_observation["route_ref"],
            "route_status": route_health_observation["route_status"],
            "remote_jurisdiction": route_health_observation["remote_jurisdiction"],
            "jurisdiction_policy_registry_ref": route_health_observation[
                "jurisdiction_policy_registry_ref"
            ],
            "jurisdiction_policy_registry_digest": jurisdiction_policy_registry_digest,
            "authority_slo_snapshot_profile": "authority-slo-snapshot-retry-window-v1",
            "authority_slo_snapshot_ref": route_health_observation[
                "authority_slo_snapshot_ref"
            ],
            "authority_slo_retry_limit_ms": route_health_observation[
                "authority_slo_retry_limit_ms"
            ],
            "observed_latency_ms": route_health_observation["observed_latency_ms"],
            "success_ratio": route_health_observation["success_ratio"],
            "consecutive_failures": route_health_observation["consecutive_failures"],
        }
        with live_authority_slo_bridge(live_slo_payload) as authority_slo_endpoint:
            remote_authority_slo_probe_receipt = (
                self.wms.probe_remote_authority_slo_snapshot_endpoint(
                    slo_endpoint=authority_slo_endpoint,
                    authority_ref=route_health_observation["authority_ref"],
                    route_ref=route_health_observation["route_ref"],
                    route_status=route_health_observation["route_status"],
                    remote_jurisdiction=route_health_observation["remote_jurisdiction"],
                    jurisdiction_policy_registry_ref=route_health_observation[
                        "jurisdiction_policy_registry_ref"
                    ],
                    jurisdiction_policy_registry_digest=jurisdiction_policy_registry_digest,
                    authority_slo_snapshot_ref=route_health_observation[
                        "authority_slo_snapshot_ref"
                    ],
                    authority_slo_retry_limit_ms=route_health_observation[
                        "authority_slo_retry_limit_ms"
                    ],
                    observed_latency_ms=route_health_observation["observed_latency_ms"],
                    success_ratio=route_health_observation["success_ratio"],
                    consecutive_failures=route_health_observation[
                        "consecutive_failures"
                    ],
                    request_timeout_ms=500,
                )
            )

        backup_route_health_observation = {
            "observation_ref": (
                "route-health://heritage/wms-approval/"
                f"{observer.identity_id.split('://', 1)[-1]}/timeout-1"
            ),
            "authority_ref": "authority://heritage/wms-approval",
            "route_ref": (
                "route://heritage/wms-approval/observer/"
                f"{approval_subject['digest'][:12]}"
            ),
            "participant_id": observer.identity_id,
            "outage_kind": "timeout",
            "route_status": "recovered",
            "remote_jurisdiction": "US-CA",
            "jurisdiction_policy_registry_ref": (
                "policy-registry://us-ca/wms-authority-retry/v1"
            ),
            "jurisdiction_rate_limit_ref": (
                "rate-limit://us-ca/wms-approval-retry-budget/v1"
            ),
            "jurisdiction_retry_limit_ms": 750,
            "authority_slo_snapshot_ref": (
                "authority-slo://heritage/wms-approval/observer-timeout/v1"
            ),
            "authority_slo_retry_limit_ms": 750,
            "signer_key_ref": "key://heritage/us-ca/wms-retry-signer",
            "observed_latency_ms": 420,
            "success_ratio": 0.91,
            "consecutive_failures": 0,
        }
        backup_jurisdiction_policy_registry_digest = sha256_text(
            canonical_json(
                {
                    "registry_policy_id": "registry-bound-authority-retry-slo-v1",
                    "registry_profile": "jurisdiction-policy-registry-bound-retry-v1",
                    "jurisdiction_policy_registry_ref": (
                        backup_route_health_observation[
                            "jurisdiction_policy_registry_ref"
                        ]
                    ),
                    "remote_jurisdiction": backup_route_health_observation[
                        "remote_jurisdiction"
                    ],
                    "jurisdiction_rate_limit_ref": backup_route_health_observation[
                        "jurisdiction_rate_limit_ref"
                    ],
                    "jurisdiction_retry_limit_ms": backup_route_health_observation[
                        "jurisdiction_retry_limit_ms"
                    ],
                    "signer_key_ref": backup_route_health_observation["signer_key_ref"],
                }
            )
        )
        backup_live_slo_payload = {
            "checked_at": "2026-04-26T00:10:05Z",
            "authority_ref": backup_route_health_observation["authority_ref"],
            "route_ref": backup_route_health_observation["route_ref"],
            "route_status": backup_route_health_observation["route_status"],
            "remote_jurisdiction": backup_route_health_observation[
                "remote_jurisdiction"
            ],
            "jurisdiction_policy_registry_ref": backup_route_health_observation[
                "jurisdiction_policy_registry_ref"
            ],
            "jurisdiction_policy_registry_digest": (
                backup_jurisdiction_policy_registry_digest
            ),
            "authority_slo_snapshot_profile": "authority-slo-snapshot-retry-window-v1",
            "authority_slo_snapshot_ref": backup_route_health_observation[
                "authority_slo_snapshot_ref"
            ],
            "authority_slo_retry_limit_ms": backup_route_health_observation[
                "authority_slo_retry_limit_ms"
            ],
            "observed_latency_ms": backup_route_health_observation[
                "observed_latency_ms"
            ],
            "success_ratio": backup_route_health_observation["success_ratio"],
            "consecutive_failures": backup_route_health_observation[
                "consecutive_failures"
            ],
        }
        with live_authority_slo_bridge(
            backup_live_slo_payload
        ) as backup_authority_slo_endpoint:
            backup_authority_slo_probe_receipt = (
                self.wms.probe_remote_authority_slo_snapshot_endpoint(
                    slo_endpoint=backup_authority_slo_endpoint,
                    authority_ref=backup_route_health_observation["authority_ref"],
                    route_ref=backup_route_health_observation["route_ref"],
                    route_status=backup_route_health_observation["route_status"],
                    remote_jurisdiction=backup_route_health_observation[
                        "remote_jurisdiction"
                    ],
                    jurisdiction_policy_registry_ref=backup_route_health_observation[
                        "jurisdiction_policy_registry_ref"
                    ],
                    jurisdiction_policy_registry_digest=(
                        backup_jurisdiction_policy_registry_digest
                    ),
                    authority_slo_snapshot_ref=backup_route_health_observation[
                        "authority_slo_snapshot_ref"
                    ],
                    authority_slo_retry_limit_ms=backup_route_health_observation[
                        "authority_slo_retry_limit_ms"
                    ],
                    observed_latency_ms=backup_route_health_observation[
                        "observed_latency_ms"
                    ],
                    success_ratio=backup_route_health_observation["success_ratio"],
                    consecutive_failures=backup_route_health_observation[
                        "consecutive_failures"
                    ],
                    request_timeout_ms=500,
                )
            )
        remote_authority_slo_probe_quorum_receipt = (
            self.wms.build_authority_slo_probe_quorum_receipt(
                [
                    remote_authority_slo_probe_receipt,
                    backup_authority_slo_probe_receipt,
                ],
                primary_probe_digest=remote_authority_slo_probe_receipt["digest"],
            )
        )
        remote_authority_slo_probe_quorum_validation = (
            self.wms.validate_authority_slo_probe_quorum_receipt(
                remote_authority_slo_probe_quorum_receipt
            )
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.remote_authority_slo_probe_quorum.bound",
            payload=remote_authority_slo_probe_quorum_receipt,
            actor="WorldModelSync",
            category="interface-wms-approval",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        remote_authority_retry_budget = self.wms.build_remote_authority_retry_budget_receipt(
            session["session_id"],
            authority_profile_ref=(
                "authority-profile://federation/wms-approval-retry-budget/v1"
            ),
            approval_fanout_receipt=approval_fanout_retry_receipt,
            engine_transaction_log_receipt=engine_transaction_log,
            route_health_observations=[route_health_observation],
            authority_slo_probe_receipts=[remote_authority_slo_probe_receipt],
        )
        remote_authority_retry_budget_validation = (
            self.wms.validate_remote_authority_retry_budget_receipt(
                remote_authority_retry_budget,
                approval_fanout_receipt=approval_fanout_retry_receipt,
                engine_transaction_log_receipt=engine_transaction_log,
                required_participants=session["current_state"]["participants"],
            )
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="wms.remote_authority_retry_budget.bound",
            payload=remote_authority_retry_budget,
            actor="WorldModelSync",
            category="interface-wms-approval",
            layer="L6",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        transportless_static_approval_rejection = self.wms.propose_physics_rules_change(
            session["session_id"],
            requested_by=identity.identity_id,
            proposed_physics_rules_ref=proposed_physics_rules_ref,
            rationale="static participant list must not bypass live approval transport",
            participant_approvals=[identity.identity_id, peer.identity_id, observer.identity_id],
            guardian_attested=True,
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
                "observer_identity_id": observer.identity_id,
            },
            "profile": self.wms.reference_profile(),
            "initial_state": initial_state,
            "scenarios": {
                "minor_diff": minor_diff,
                "major_diff": major_diff,
                "time_rate_deviation": time_rate_deviation,
                "time_rate_attestation_subject": time_rate_attestation_subject,
                "time_rate_attestation_imc_sessions": time_rate_attestation_imc_sessions,
                "time_rate_attestation_messages": time_rate_attestation_messages,
                "time_rate_attestation_receipts": time_rate_attestation_receipts,
                "approval_subject": approval_subject,
                "approval_imc_session": approval_imc_sessions[0],
                "approval_imc_sessions": approval_imc_sessions,
                "approval_messages": approval_messages,
                "approval_collection_receipt": approval_collection_receipt,
                "approval_fanout_receipt": approval_fanout_retry_receipt,
                "approval_fanout_nominal_receipt": approval_fanout_receipt,
                "approval_fanout_retry_attempts": approval_fanout_retry_attempts,
                "approval_fanout_results": approval_fanout_results,
                "approval_transport_receipts": approval_transport_receipts,
                "physics_change": physics_change,
                "physics_revert": physics_revert,
                "engine_transaction_log": engine_transaction_log,
                "engine_transaction_entries": engine_transaction_entries,
                "engine_authority_route_trace": engine_authority_route_trace,
                "engine_route_binding": engine_route_binding,
                "engine_packet_capture_export": engine_packet_capture_export,
                "engine_privileged_capture_acquisition": engine_privileged_capture_acquisition,
                "engine_capture_binding": engine_capture_binding,
                "remote_authority_slo_probe_receipt": remote_authority_slo_probe_receipt,
                "remote_authority_slo_backup_probe_receipt": (
                    backup_authority_slo_probe_receipt
                ),
                "remote_authority_slo_probe_quorum_receipt": (
                    remote_authority_slo_probe_quorum_receipt
                ),
                "remote_authority_retry_budget": remote_authority_retry_budget,
                "transportless_static_approval_rejection": transportless_static_approval_rejection,
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
                "time_rate_deviation_escape_bound": (
                    time_rate_deviation["classification"] == "major_diff"
                    and time_rate_deviation["decision"] == "offer-private-reality"
                    and time_rate_deviation["escape_offered"]
                    and time_rate_deviation["time_rate_policy_id"]
                    == "fixed-time-rate-private-escape-v1"
                    and time_rate_deviation["baseline_time_rate"] == initial_state["time_rate"]
                    and time_rate_deviation["requested_time_rate"] == 1.25
                    and time_rate_deviation["time_rate_deviation_detected"]
                    and time_rate_deviation["time_rate_escape_required"]
                    and time_rate_deviation["time_rate_state_locked"]
                    and len(time_rate_deviation["time_rate_deviation_digest"]) == 64
                    and final_state["time_rate"] == initial_state["time_rate"]
                ),
                "time_rate_attestation_transport_bound": (
                    time_rate_deviation["time_rate_attestation_required"]
                    and time_rate_deviation["time_rate_attestation_quorum_met"]
                    and time_rate_deviation[
                        "time_rate_attestation_participant_order_bound"
                    ]
                    and time_rate_deviation["time_rate_attestation_subject_digest"]
                    == time_rate_attestation_subject["digest"]
                    and len(time_rate_deviation["time_rate_attestation_digest"]) == 64
                    and all(
                        self.wms.validate_time_rate_attestation_receipt(
                            receipt,
                            time_rate_attestation_subject_digest=time_rate_attestation_subject[
                                "digest"
                            ],
                        )["ok"]
                        for receipt in time_rate_attestation_receipts
                    )
                ),
                "malicious_isolated": malicious_diff["classification"] == "malicious_inject"
                and malicious_violation["guardian_action"] == "isolate-session",
                "private_escape_honored": mode_switch["private_escape_honored"]
                and final_state["authority"] == "local",
                "physics_change": physics_change_validation,
                "physics_revert": physics_revert_validation,
                "approval_collection": approval_collection_validation,
                "approval_fanout": approval_fanout_retry_validation,
                "approval_fanout_nominal": approval_fanout_validation,
                "physics_approval_transport_bound": physics_change_validation["approval_transport_quorum_met"]
                and physics_change_validation["approval_transport_digest_bound"]
                and all(
                    self.wms.validate_approval_transport_receipt(
                        receipt,
                        approval_subject_digest=approval_subject["digest"],
                    )["ok"]
                    for receipt in approval_transport_receipts
                ),
                "approval_collection_scaling_bound": approval_collection_validation["ok"]
                and approval_collection_receipt["batch_count"] == 2
                and all(
                    batch["within_batch_limit"]
                    for batch in approval_collection_receipt["batches"]
                )
                and physics_change_validation["approval_collection_complete"]
                and physics_change["approval_collection_digest"]
                == approval_collection_receipt["digest"],
                "distributed_approval_fanout_bound": approval_fanout_retry_validation["ok"]
                and physics_change_validation["approval_fanout_complete"]
                and physics_change_validation["approval_fanout_digest_bound"]
                and physics_change["approval_fanout_digest"]
                == approval_fanout_retry_receipt["digest"],
                "distributed_approval_fanout_retry_bound": (
                    approval_fanout_retry_validation["retry_policy_bound"]
                    and approval_fanout_retry_validation["partial_outage_recovered"]
                    and approval_fanout_retry_receipt["partial_outage_status"] == "recovered"
                    and approval_fanout_retry_receipt["retry_attempt_count"] == 1
                    and approval_fanout_retry_receipt["outage_participants"]
                    == [observer.identity_id]
                ),
                "engine_transaction_log_bound": (
                    engine_transaction_log_validation["ok"]
                    and engine_transaction_log_validation["engine_binding_complete"]
                    and engine_transaction_log_validation["entry_order_bound"]
                    and engine_transaction_log_validation["source_artifacts_bound"]
                    and engine_transaction_log_validation["redaction_complete"]
                    and engine_transaction_log_validation[
                        "engine_adapter_signature_bound"
                    ]
                    and engine_transaction_log["covered_operations"]
                    == engine_transaction_log["required_operations"]
                    and engine_transaction_log["engine_adapter_signature_bound"]
                    and engine_transaction_log["raw_adapter_signature_stored"] is False
                    and engine_transaction_log["engine_binding_status"] == "complete"
                ),
                "engine_transaction_log": engine_transaction_log_validation,
                "engine_route_binding_bound": (
                    engine_route_binding_validation["ok"]
                    and engine_route_binding_validation["engine_log_bound"]
                    and engine_route_binding_validation["authority_route_trace_bound"]
                    and engine_route_binding_validation["cross_host_route_bound"]
                    and engine_route_binding_validation[
                        "engine_route_binding_complete"
                    ]
                    and engine_route_binding["engine_route_binding_status"] == "complete"
                    and engine_route_binding["raw_engine_payload_stored"] is False
                    and engine_route_binding["raw_route_payload_stored"] is False
                ),
                "engine_route_binding": engine_route_binding_validation,
                "engine_capture_binding_bound": (
                    engine_capture_binding_validation["ok"]
                    and engine_capture_binding_validation["engine_route_binding_bound"]
                    and engine_capture_binding_validation["packet_capture_bound"]
                    and engine_capture_binding_validation["privileged_capture_bound"]
                    and engine_capture_binding_validation["route_binding_set_bound"]
                    and engine_capture_binding_validation["engine_capture_binding_complete"]
                    and engine_capture_binding["engine_capture_binding_status"]
                    == "complete"
                    and engine_capture_binding["raw_engine_payload_stored"] is False
                    and engine_capture_binding["raw_route_payload_stored"] is False
                    and engine_capture_binding["raw_packet_body_stored"] is False
                ),
                "engine_capture_binding": engine_capture_binding_validation,
                "remote_authority_slo_probe_quorum_bound": (
                    remote_authority_slo_probe_quorum_validation["ok"]
                    and remote_authority_slo_probe_quorum_validation["quorum_bound"]
                    and remote_authority_slo_probe_quorum_validation[
                        "multi_authority_bound"
                    ]
                    and remote_authority_slo_probe_quorum_validation[
                        "multi_jurisdiction_bound"
                    ]
                    and remote_authority_slo_probe_quorum_receipt[
                        "primary_probe_digest"
                    ]
                    == remote_authority_slo_probe_receipt["digest"]
                    and remote_authority_slo_probe_quorum_receipt[
                        "accepted_probe_count"
                    ]
                    == 2
                    and remote_authority_slo_probe_quorum_receipt[
                        "raw_slo_payload_stored"
                    ]
                    is False
                ),
                "remote_authority_slo_probe_quorum": (
                    remote_authority_slo_probe_quorum_validation
                ),
                "remote_authority_retry_budget_bound": (
                    remote_authority_retry_budget_validation["ok"]
                    and remote_authority_retry_budget_validation[
                        "adaptive_retry_budget_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "engine_log_fanout_bound"
                    ]
                    and remote_authority_retry_budget_validation["route_health_bound"]
                    and remote_authority_retry_budget_validation[
                        "jurisdiction_rate_limit_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "jurisdiction_policy_registry_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "authority_slo_snapshot_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "authority_slo_live_probe_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "registry_slo_schedule_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "authority_signature_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "signed_jurisdiction_retry_budget_bound"
                    ]
                    and remote_authority_retry_budget_validation[
                        "registry_bound_retry_budget_bound"
                    ]
                    and remote_authority_retry_budget_validation["schedule_bound"]
                    and remote_authority_retry_budget["budget_status"] == "complete"
                    and remote_authority_retry_budget[
                        "authority_slo_live_probe_bound"
                    ]
                    and remote_authority_retry_budget["total_scheduled_delay_ms"] == 250
                    and remote_authority_retry_budget["remote_jurisdictions"]
                    == ["JP-13"]
                    and remote_authority_retry_budget["raw_remote_transcript_stored"]
                    is False
                ),
                "remote_authority_retry_budget": remote_authority_retry_budget_validation,
                "static_approval_without_transport_rejected": (
                    transportless_static_approval_rejection["decision"] == "rejected"
                    and transportless_static_approval_rejection["approval_quorum_met"]
                    and not transportless_static_approval_rejection[
                        "approval_transport_quorum_met"
                    ]
                ),
                "physics_change_reversible": physics_change_validation["ok"]
                and physics_revert_validation["ok"]
                and physics_change["rollback_physics_rules_ref"]
                == initial_state["physics_rules_ref"]
                and physics_revert["resulting_physics_rules_ref"]
                == initial_state["physics_rules_ref"]
                and final_state["physics_rules_ref"] == initial_state["physics_rules_ref"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_sensory_loopback_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://sensory-loopback-demo/v1",
            metadata={"display_name": "Sensory Loopback Sandbox"},
        )
        world_session = self.wms.create_session(
            [identity.identity_id],
            objects=["avatar-atrium", "mirror-surface", "haptic-floor"],
        )
        world_state = self.wms.snapshot(world_session["session_id"])
        session = self.sensory_loopback.open_session(
            identity_id=identity.identity_id,
            world_state_ref=f"wms://state/{world_state['state_id']}",
            body_anchor_ref="avatar://atrium/self-body/core",
            avatar_body_map_ref="avatar-body-map://atrium/self-body/v1",
            proprioceptive_calibration_ref="calibration://atrium/self-body/v1",
        )

        coherent_tick = self.qualia.append(
            summary="avatar mirror, spatial audio, and wrist haptics remain aligned to one embodied anchor",
            valence=0.18,
            arousal=0.36,
            clarity=0.91,
            modality_salience={
                "visual": 0.92,
                "auditory": 0.74,
                "somatic": 0.81,
                "interoceptive": 0.48,
            },
            attention_target="avatar://atrium/self-body/core",
            self_awareness=0.77,
            lucidity=0.94,
        )
        coherent = self.sensory_loopback.deliver_bundle(
            session["session_id"],
            scene_summary="coherent avatar mirror bundle with voice reflection and wrist haptic confirmation",
            artifact_refs={
                "visual": "artifact://loopback/visual/coherent-mirror-v1",
                "auditory": "artifact://loopback/audio/coherent-voice-v1",
                "haptic": "artifact://loopback/haptic/coherent-wrist-v1",
            },
            latency_ms=42.0,
            body_map_alignment_ref="alignment://atrium/self-body/coherent-v1",
            body_map_alignment={
                "core": 0.96,
                "left-hand": 0.91,
                "right-hand": 0.93,
                "stance": 0.94,
            },
            attention_target=coherent_tick.attention_target,
            guardian_observed=True,
            qualia_binding_ref=f"qualia://tick/{coherent_tick.tick_id}",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.session.opened",
            payload={
                "session_id": session["session_id"],
                "world_state_ref": session["world_state_ref"],
                "body_anchor_ref": session["body_anchor_ref"],
                "allowed_channels": session["allowed_channels"],
            },
            actor="SensoryLoopbackService",
            category="interface-sensory-loopback",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="virtual-sensory-plane",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.bundle.delivered",
            payload=coherent,
            actor="SensoryLoopbackService",
            category="interface-sensory-loopback",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="virtual-sensory-plane",
        )

        degraded_tick = self.qualia.append(
            summary="avatar body drift spikes as haptic and auditory timing no longer aligns with the mirror surface",
            valence=-0.24,
            arousal=0.63,
            clarity=0.58,
            modality_salience={
                "visual": 0.66,
                "auditory": 0.88,
                "somatic": 0.53,
                "interoceptive": 0.72,
            },
            attention_target="guardian-review",
            self_awareness=0.71,
            lucidity=0.83,
        )
        degraded = self.sensory_loopback.deliver_bundle(
            session["session_id"],
            scene_summary="desynchronized body echo causes unstable avatar ownership and requires guardian hold",
            artifact_refs={
                "visual": "artifact://loopback/visual/drifted-mirror-v1",
                "auditory": "artifact://loopback/audio/drifted-voice-v1",
                "haptic": "artifact://loopback/haptic/drifted-floor-v1",
            },
            latency_ms=168.0,
            body_map_alignment_ref="alignment://atrium/self-body/drifted-v1",
            body_map_alignment={
                "core": 0.58,
                "left-hand": 0.61,
                "right-hand": 0.55,
                "stance": 0.52,
            },
            attention_target=degraded_tick.attention_target,
            guardian_observed=True,
            qualia_binding_ref=f"qualia://tick/{degraded_tick.tick_id}",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.bundle.held",
            payload=degraded,
            actor="Guardian",
            category="interface-sensory-loopback-guardian",
            layer="L6",
            signature_roles=["guardian", "council"],
            substrate="virtual-sensory-plane",
        )

        stabilized = self.sensory_loopback.stabilize(
            session["session_id"],
            reason="guardian realigned the avatar body anchor and resumed the safe loopback baseline",
            restored_body_anchor_ref="avatar://atrium/self-body/core",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.session.stabilized",
            payload=stabilized,
            actor="SensoryLoopbackService",
            category="interface-sensory-loopback",
            layer="L6",
            signature_roles=["guardian"],
            substrate="virtual-sensory-plane",
        )
        artifact_family = self.sensory_loopback.capture_artifact_family(
            session["session_id"],
            family_label="atrium-realignment-family",
            receipts=[coherent, degraded, stabilized],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.artifact_family.recorded",
            payload=artifact_family,
            actor="SensoryLoopbackService",
            category="interface-sensory-loopback-family",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="virtual-sensory-plane",
        )

        peer = self.identity.create(
            human_consent_proof="consent://sensory-loopback-peer-demo/v1",
            metadata={"display_name": "Shared Loopback Peer"},
        )
        collective_identity = self.identity.create_collective(
            [identity.identity_id, peer.identity_id],
            consent_proof="consent://sensory-loopback-collective-demo/v1",
            metadata={
                "display_name": "Atrium Shared Field",
                "purpose": "bounded shared sensory arbitration",
            },
        )
        shared_imc_session = self.imc.open_session(
            initiator_id=identity.identity_id,
            peer_id=peer.identity_id,
            mode="merge_thought",
            initiator_template={
                "public_fields": ["display_name", "shared_focus", "presence_state"],
                "intimate_fields": ["affect_summary", "intent_vector"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_template={
                "public_fields": ["display_name", "shared_focus", "presence_state"],
                "intimate_fields": ["affect_summary", "intent_vector"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )
        shared_collective = self.collective.register_collective(
            collective_identity_id=collective_identity.identity_id,
            member_ids=[identity.identity_id, peer.identity_id],
            purpose="bounded shared sensory arbitration inside a collective atrium",
            proposed_name="Atrium Shared Field",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )
        shared_world_session = self.wms.create_session(
            [collective_identity.identity_id, identity.identity_id, peer.identity_id],
            objects=[
                "shared-mirror",
                "collective-anchor",
                "perimeter-lantern",
            ],
        )
        shared_world_state = self.wms.snapshot(shared_world_session["session_id"])
        shared_merge_session = self.collective.open_merge_session(
            collective_id=shared_collective["collective_id"],
            imc_session_id=shared_imc_session["session_id"],
            wms_session_id=shared_world_session["session_id"],
            requested_duration_seconds=6.0,
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
            shared_world_mode=shared_world_session["mode"],
        )
        shared_session = self.sensory_loopback.open_session(
            identity_id=identity.identity_id,
            world_state_ref=f"wms://state/{shared_world_state['state_id']}",
            body_anchor_ref="avatar://atrium/shared-body/core",
            avatar_body_map_ref="avatar-body-map://atrium/shared-body/v1",
            proprioceptive_calibration_ref="calibration://atrium/shared-body/v1",
            participant_identity_ids=[identity.identity_id, peer.identity_id],
            shared_imc_session_id=shared_imc_session["session_id"],
            shared_collective_id=shared_collective["collective_id"],
        )
        shared_aligned_tick = self.qualia.append(
            summary="shared mirror alignment keeps both participants attached to one embodied anchor",
            valence=0.22,
            arousal=0.41,
            clarity=0.88,
            modality_salience={
                "visual": 0.89,
                "auditory": 0.71,
                "somatic": 0.78,
                "interoceptive": 0.43,
            },
            attention_target="avatar://atrium/shared-body/core",
            self_awareness=0.74,
            lucidity=0.9,
        )
        shared_aligned = self.sensory_loopback.deliver_bundle(
            shared_session["session_id"],
            scene_summary="aligned shared atrium loopback keeps both participants on the same avatar anchor",
            artifact_refs={
                "visual": "artifact://loopback/shared/visual/aligned-mirror-v1",
                "auditory": "artifact://loopback/shared/audio/aligned-chorus-v1",
                "haptic": "artifact://loopback/shared/haptic/aligned-floor-v1",
            },
            latency_ms=58.0,
            body_map_alignment_ref="alignment://atrium/shared-body/aligned-v1",
            body_map_alignment={
                "core": 0.94,
                "left-hand": 0.9,
                "right-hand": 0.92,
                "stance": 0.93,
            },
            attention_target=shared_aligned_tick.attention_target,
            guardian_observed=True,
            qualia_binding_ref=f"qualia://tick/{shared_aligned_tick.tick_id}",
            owner_identity_id=identity.identity_id,
            participant_attention_targets={
                identity.identity_id: "avatar://atrium/shared-body/core",
                peer.identity_id: "avatar://atrium/shared-body/core",
            },
            participant_presence_refs={
                identity.identity_id: "presence://atrium/shared/self-core",
                peer.identity_id: "presence://atrium/shared/peer-core",
            },
        )
        shared_mediated_tick = self.qualia.append(
            summary="guardian mediates competing focus claims inside the shared atrium without breaking body coherence",
            valence=0.05,
            arousal=0.56,
            clarity=0.79,
            modality_salience={
                "visual": 0.84,
                "auditory": 0.77,
                "somatic": 0.73,
                "interoceptive": 0.39,
            },
            attention_target="avatar://atrium/shared-body/perimeter",
            self_awareness=0.72,
            lucidity=0.87,
        )
        shared_mediated = self.sensory_loopback.deliver_bundle(
            shared_session["session_id"],
            scene_summary="guardian mediates competing shared-space targets while preserving coherent loopback",
            artifact_refs={
                "visual": "artifact://loopback/shared/visual/arbitrated-mirror-v1",
                "auditory": "artifact://loopback/shared/audio/arbitrated-chorus-v1",
                "haptic": "artifact://loopback/shared/haptic/arbitrated-floor-v1",
            },
            latency_ms=61.0,
            body_map_alignment_ref="alignment://atrium/shared-body/arbitrated-v1",
            body_map_alignment={
                "core": 0.91,
                "left-hand": 0.89,
                "right-hand": 0.9,
                "stance": 0.92,
            },
            attention_target=shared_mediated_tick.attention_target,
            guardian_observed=True,
            qualia_binding_ref=f"qualia://tick/{shared_mediated_tick.tick_id}",
            owner_identity_id=peer.identity_id,
            participant_attention_targets={
                identity.identity_id: "avatar://atrium/shared-body/core",
                peer.identity_id: "avatar://atrium/shared-body/perimeter",
            },
            participant_presence_refs={
                identity.identity_id: "presence://atrium/shared/self-core",
                peer.identity_id: "presence://atrium/shared/peer-perimeter",
            },
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.bundle.arbitrated",
            payload=shared_mediated,
            actor="Guardian",
            category="interface-sensory-loopback-shared",
            layer="L6",
            signature_roles=["guardian", "council"],
            substrate="virtual-sensory-plane",
        )
        shared_artifact_family = self.sensory_loopback.capture_artifact_family(
            shared_session["session_id"],
            family_label="collective-atrium-arbitration-family",
            receipts=[shared_aligned, shared_mediated],
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="sensory_loopback.shared_artifact_family.recorded",
            payload=shared_artifact_family,
            actor="SensoryLoopbackService",
            category="interface-sensory-loopback-shared",
            layer="L6",
            signature_roles=["self", "guardian", "council"],
            substrate="virtual-sensory-plane",
        )
        final_session = self.sensory_loopback.snapshot(session["session_id"])
        session_validation = self.sensory_loopback.validate_session(final_session)
        coherent_validation = self.sensory_loopback.validate_receipt(coherent)
        degraded_validation = self.sensory_loopback.validate_receipt(degraded)
        stabilized_validation = self.sensory_loopback.validate_receipt(stabilized)
        artifact_family_validation = self.sensory_loopback.validate_artifact_family(artifact_family)
        shared_final_session = self.sensory_loopback.snapshot(shared_session["session_id"])
        shared_session_validation = self.sensory_loopback.validate_session(shared_final_session)
        shared_aligned_validation = self.sensory_loopback.validate_receipt(shared_aligned)
        shared_mediated_validation = self.sensory_loopback.validate_receipt(shared_mediated)
        shared_artifact_family_validation = self.sensory_loopback.validate_artifact_family(
            shared_artifact_family,
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "profile": self.sensory_loopback.reference_profile(),
            "world_state": world_state,
            "session": final_session,
            "receipts": {
                "coherent": coherent,
                "degraded": degraded,
                "stabilized": stabilized,
            },
            "artifact_family": artifact_family,
            "shared_loopback": {
                "peer": {
                    "identity_id": peer.identity_id,
                    "lineage_id": peer.lineage_id,
                },
                "world_state": shared_world_state,
                "imc_session": shared_imc_session,
                "collective": shared_collective,
                "merge_session": shared_merge_session,
                "session": shared_final_session,
                "receipts": {
                    "aligned": shared_aligned,
                    "mediated": shared_mediated,
                },
                "artifact_family": shared_artifact_family,
                "validation": {
                    "ok": shared_session_validation["ok"]
                    and shared_aligned_validation["ok"]
                    and shared_mediated_validation["ok"]
                    and shared_artifact_family_validation["ok"],
                    "session_ok": shared_session_validation["ok"],
                    "aligned_ok": shared_aligned_validation["ok"],
                    "mediated_ok": shared_mediated_validation["ok"],
                    "artifact_family_ok": shared_artifact_family_validation["ok"],
                    "shared_space_mode_collective": shared_final_session["shared_space_mode"]
                    == "collective-shared",
                    "participant_bindings_complete": shared_mediated_validation[
                        "participant_bindings_complete"
                    ],
                    "shared_imc_bound": shared_session_validation["shared_imc_bound"],
                    "shared_collective_bound": shared_session_validation["shared_collective_bound"],
                    "owner_handoff": shared_mediated["owner_identity_id"] == peer.identity_id,
                    "guardian_arbitrated": shared_mediated_validation["guardian_arbitrated"]
                    and shared_mediated["arbitration_status"] == "guardian-mediated",
                    "artifact_family_arbitration_tracked": shared_artifact_family_validation[
                        "arbitration_tracked"
                    ]
                    and shared_artifact_family["arbitration_scene_count"] == 2
                    and shared_artifact_family["guardian_arbitration_count"] == 1,
                },
            },
            "qualia": {
                "profile": self.qualia.profile(),
                "recent": self.qualia.recent(2),
            },
            "validation": {
                **session_validation,
                "coherent_ok": coherent_validation["ok"],
                "degraded_ok": degraded_validation["ok"],
                "stabilized_ok": stabilized_validation["ok"],
                "coherent_delivery": coherent["delivery_status"] == "delivered"
                and coherent["immersion_preserved"],
                "guardian_hold_triggered": degraded["delivery_status"] == "guardian-hold"
                and degraded["requires_council_review"],
                "stabilized_active": stabilized["delivery_status"] == "stabilized"
                and final_session["status"] == "active",
                "artifact_family_ok": artifact_family_validation["ok"],
                "artifact_family_multi_scene": artifact_family_validation["multi_scene"]
                and artifact_family["scene_count"] == 3,
                "artifact_family_bound": final_session["last_artifact_family_ref"]
                == artifact_family["family_ref"],
                "qualia_binding_bound": coherent["qualia_binding_ref"].startswith("qualia://tick/")
                and degraded["qualia_binding_ref"].startswith("qualia://tick/")
                and stabilized["qualia_binding_ref"].startswith("qualia://loopback-stabilize/"),
                "body_map_bound": final_session["avatar_body_map_ref"].startswith("avatar-body-map://"),
                "proprioceptive_calibration_bound": final_session[
                    "proprioceptive_calibration_ref"
                ].startswith("calibration://"),
                "alignment_ref_bound": coherent["body_map_alignment_ref"].startswith("alignment://")
                and degraded["body_map_alignment_ref"].startswith("alignment://")
                and stabilized["body_map_alignment_ref"].startswith("alignment://"),
                "artifact_family_body_map_bound": all(
                    scene["avatar_body_map_ref"] == final_session["avatar_body_map_ref"]
                    for scene in artifact_family["scene_summaries"]
                ),
                "shared_loopback_ok": shared_session_validation["ok"]
                and shared_aligned_validation["ok"]
                and shared_mediated_validation["ok"]
                and shared_artifact_family_validation["ok"],
                "shared_loopback_collective_bound": shared_session_validation[
                    "shared_collective_bound"
                ]
                and shared_final_session["shared_space_mode"] == "collective-shared",
                "shared_loopback_imc_bound": shared_session_validation["shared_imc_bound"],
                "shared_loopback_participants_bound": shared_mediated_validation[
                    "participant_bindings_complete"
                ]
                and shared_session_validation["participant_count"] == 2,
                "shared_loopback_arbitrated": shared_mediated_validation["guardian_arbitrated"]
                and shared_mediated["arbitration_status"] == "guardian-mediated",
                "shared_loopback_owner_handoff": shared_mediated["owner_identity_id"]
                == peer.identity_id,
                "shared_loopback_family_tracked": shared_artifact_family_validation[
                    "arbitration_tracked"
                ]
                and shared_artifact_family["arbitration_scene_count"] == 2
                and shared_artifact_family["guardian_arbitration_count"] == 1,
                "world_anchor_bound": final_session["world_state_ref"]
                == f"wms://state/{world_state['state_id']}",
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
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
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
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
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
                "episodic_stream": episodic_snapshot,
                "source_events": source_events,
                "manifest": manifest,
            },
            "validation": validation,
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_memory_replication_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://memory-replication-demo/v1",
            metadata={"display_name": "Memory Replication Sandbox"},
        )
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        replication_session = self.memory_replication.replicate(
            identity.identity_id,
            manifest,
        )
        replication_validation = self.memory_replication.validate_session(
            replication_session,
            manifest=manifest,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.replication_reconciled",
            payload={
                "policy_id": replication_session["replication_policy"]["policy_id"],
                "source_manifest_digest": replication_session["source_manifest_digest"],
                "consensus_target_ids": replication_validation["consensus_target_ids"],
                "mismatch_target_ids": replication_validation["mismatch_target_ids"],
                "guardian_alert_ref": replication_session["verification_audit"]["guardian_alert_ref"],
                "council_escalation_ref": replication_session["reconciliation"]["council_escalation_ref"],
                "resync_required": replication_validation["resync_required"],
                "session_digest": replication_session["digest"],
            },
            actor="MemoryReplicationService",
            category="memory-replication",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "memory_replication": {
                "policy": self.memory_replication.profile(),
                "episodic_stream": episodic_snapshot,
                "source_events": source_events,
                "manifest": manifest,
                "session": replication_session,
            },
            "validation": {
                "manifest": manifest_validation,
                "replication": replication_validation,
                "consensus_quorum_ok": replication_validation["quorum_ok"],
                "resync_required": replication_validation["resync_required"],
                "ok": manifest_validation["ok"] and replication_validation["ok"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_memory_edit_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://memory-edit-demo/v1",
            metadata={"display_name": "Memory Edit Sandbox"},
        )
        source_events = self.memory_edit.reference_events()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        semantic_snapshot = self.semantic.project(identity.identity_id, manifest)
        semantic_validation = self.semantic.validate(semantic_snapshot)
        session = self.memory_edit.apply_recall_buffer(
            identity_id=identity.identity_id,
            semantic_snapshot=semantic_snapshot,
            selected_concept_ids=[semantic_snapshot["concepts"][0]["concept_id"]],
            self_consent_ref="consent://memory-edit-demo/v1",
            guardian_attestation_ref="guardian://memory-edit-demo/reviewer-omega",
            clinical_rationale="内容を保持したまま想起時 affect を緩衝し再体験のみを弱める",
            buffer_ratio=0.55,
        )
        edit_validation = self.memory_edit.validate_session(session)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.recall_buffered",
            payload={
                "policy_id": session["memory_edit_policy"]["policy_id"],
                "source_manifest_digest": session["source_manifest_digest"],
                "source_concept_ids": session["source_concept_ids"],
                "freeze_ref": session["freeze_record"]["freeze_ref"],
                "recall_view_count": session["recall_view_count"],
                "concept_labels": edit_validation["concept_labels"],
                "deletion_blocked": session["deletion_blocked"],
            },
            actor="MemoryEditingService",
            category="memory-edit",
            layer="L2",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "memory_edit": {
                "policy": self.memory_edit.profile(),
                "source_events": source_events,
                "manifest": manifest,
                "semantic_snapshot": semantic_snapshot,
                "session": session,
            },
            "validation": {
                "manifest": manifest_validation,
                "semantic": semantic_validation,
                "memory_edit": edit_validation,
                "deletion_blocked": edit_validation["deletion_blocked"],
                "source_manifest_preserved": edit_validation["source_preserved"],
                "ok": (
                    manifest_validation["ok"]
                    and semantic_validation["ok"]
                    and edit_validation["ok"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_semantic_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://semantic-demo/v1",
            metadata={"display_name": "Semantic Memory Sandbox"},
        )
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        semantic_snapshot = self.semantic.project(identity.identity_id, manifest)
        semantic_validation = self.semantic.validate(semantic_snapshot)
        connectome_document = self.connectome.build_reference_snapshot(identity.identity_id)
        connectome_validation = self.connectome.validate(connectome_document)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.semantic_projected",
            payload={
                "policy_id": semantic_snapshot["projection_policy"]["policy_id"],
                "concept_count": semantic_snapshot["concept_count"],
                "labels": semantic_validation["labels"],
                "source_manifest_digest": semantic_snapshot["source_manifest_digest"],
                "deferred_surfaces": semantic_snapshot["deferred_surfaces"],
            },
            actor="SemanticMemoryProjector",
            category="semantic-projection",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        semantic_handoff = self.semantic.prepare_procedural_handoff(
            identity.identity_id,
            semantic_snapshot,
            connectome_document,
        )
        handoff_validation = self.semantic.validate_procedural_handoff(
            semantic_handoff,
            semantic_snapshot=semantic_snapshot,
            connectome_document=connectome_document,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.semantic_procedural_handoff_prepared",
            payload={
                "policy_id": semantic_handoff["handoff_policy"]["policy_id"],
                "handoff_id": semantic_handoff["handoff_id"],
                "handoff_digest": semantic_handoff["digest"],
                "target_namespace": semantic_handoff["handoff_policy"]["target_namespace"],
                "concept_count": semantic_handoff["concept_count"],
                "canonical_labels": handoff_validation["canonical_labels"],
                "connectome_snapshot_digest": semantic_handoff["connectome_snapshot_digest"],
            },
            actor="SemanticMemoryProjector",
            category="semantic-handoff",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "semantic": {
                "projection_policy": self.semantic.profile(),
                "episodic_stream": episodic_snapshot,
                "manifest": manifest,
                "connectome": connectome_document,
                "snapshot": semantic_snapshot,
                "procedural_handoff": semantic_handoff,
            },
            "validation": {
                "manifest": manifest_validation,
                "connectome": connectome_validation,
                "semantic": semantic_validation,
                "procedural_handoff": handoff_validation,
                "ok": (
                    manifest_validation["ok"]
                    and connectome_validation["ok"]
                    and semantic_validation["ok"]
                    and handoff_validation["ok"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_procedural_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://procedural-demo/v1",
            metadata={"display_name": "Procedural Memory Sandbox"},
        )
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        connectome_document = self.connectome.build_reference_snapshot(identity.identity_id)
        connectome_validation = self.connectome.validate(connectome_document)
        semantic_snapshot = self.semantic.project(identity.identity_id, manifest)
        semantic_validation = self.semantic.validate(semantic_snapshot)
        semantic_handoff = self.semantic.prepare_procedural_handoff(
            identity.identity_id,
            semantic_snapshot,
            connectome_document,
        )
        handoff_validation = self.semantic.validate_procedural_handoff(
            semantic_handoff,
            semantic_snapshot=semantic_snapshot,
            manifest=manifest,
            connectome_document=connectome_document,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.semantic_projected",
            payload={
                "policy_id": semantic_snapshot["projection_policy"]["policy_id"],
                "concept_count": semantic_snapshot["concept_count"],
                "labels": semantic_validation["labels"],
                "source_manifest_digest": semantic_snapshot["source_manifest_digest"],
                "deferred_surfaces": semantic_snapshot["deferred_surfaces"],
            },
            actor="SemanticMemoryProjector",
            category="semantic-projection",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.semantic_procedural_handoff_prepared",
            payload={
                "policy_id": semantic_handoff["handoff_policy"]["policy_id"],
                "handoff_id": semantic_handoff["handoff_id"],
                "handoff_digest": semantic_handoff["digest"],
                "target_namespace": semantic_handoff["handoff_policy"]["target_namespace"],
                "concept_count": semantic_handoff["concept_count"],
                "canonical_labels": handoff_validation["canonical_labels"],
                "connectome_snapshot_digest": semantic_handoff["connectome_snapshot_digest"],
            },
            actor="SemanticMemoryProjector",
            category="semantic-handoff",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        procedural_snapshot = self.procedural.project_from_handoff(
            identity.identity_id,
            semantic_handoff,
            manifest,
            connectome_document,
        )
        procedural_validation = self.procedural.validate(procedural_snapshot)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_previewed",
            payload={
                "policy_id": procedural_snapshot["preview_policy"]["policy_id"],
                "recommendation_count": procedural_snapshot["recommendation_count"],
                "target_paths": procedural_validation["target_paths"],
                "source_manifest_digest": procedural_snapshot["source_manifest_digest"],
                "connectome_snapshot_digest": procedural_snapshot["connectome_snapshot_digest"],
                "semantic_handoff_digest": semantic_handoff["digest"],
                "deferred_surfaces": procedural_snapshot["deferred_surfaces"],
            },
            actor="ProceduralMemoryProjector",
            category="procedural-preview",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "procedural": {
                "preview_policy": self.procedural.profile(),
                "episodic_stream": episodic_snapshot,
                "manifest": manifest,
                "connectome": connectome_document,
                "semantic_snapshot": semantic_snapshot,
                "semantic_handoff": semantic_handoff,
                "snapshot": procedural_snapshot,
            },
            "validation": {
                "manifest": manifest_validation,
                "connectome": connectome_validation,
                "semantic": semantic_validation,
                "semantic_handoff": handoff_validation,
                "procedural": procedural_validation,
                "handoff_matches_preview_policy": (
                    semantic_handoff["handoff_policy"]["target_preview_policy"]
                    == procedural_snapshot["preview_policy"]["policy_id"]
                ),
                "ok": (
                    manifest_validation["ok"]
                    and connectome_validation["ok"]
                    and semantic_validation["ok"]
                    and handoff_validation["ok"]
                    and procedural_validation["ok"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_procedural_writeback_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://procedural-writeback-demo/v1",
            metadata={"display_name": "Procedural Writeback Sandbox"},
        )
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        connectome_document = self.connectome.build_reference_snapshot(identity.identity_id)
        connectome_validation = self.connectome.validate(connectome_document)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        procedural_snapshot = self.procedural.project(
            identity.identity_id,
            manifest,
            connectome_document,
        )
        procedural_validation = self.procedural.validate(procedural_snapshot)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_previewed",
            payload={
                "policy_id": procedural_snapshot["preview_policy"]["policy_id"],
                "recommendation_count": procedural_snapshot["recommendation_count"],
                "target_paths": procedural_validation["target_paths"],
                "source_manifest_digest": procedural_snapshot["source_manifest_digest"],
                "connectome_snapshot_digest": procedural_snapshot["connectome_snapshot_digest"],
                "deferred_surfaces": procedural_snapshot["deferred_surfaces"],
            },
            actor="ProceduralMemoryProjector",
            category="procedural-preview",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        writeback_result = self.procedural_writeback.apply(
            identity.identity_id,
            procedural_snapshot,
            connectome_document,
            selected_recommendation_ids=[
                recommendation["recommendation_id"]
                for recommendation in procedural_snapshot["recommendations"]
            ],
            self_attestation_id="self://procedural-writeback/consent-001",
            council_attestation_id="council://procedural-writeback/unanimous-001",
            guardian_attestation_id="guardian://procedural-writeback/approved-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded rehearsal preview を continuity-diff 付き writeback として昇格する",
        )
        receipt = writeback_result["receipt"]
        updated_connectome_document = writeback_result["updated_connectome_document"]
        updated_connectome_validation = self.connectome.validate(updated_connectome_document)
        writeback_validation = self.procedural_writeback.validate(
            receipt,
            updated_connectome_document,
            procedural_snapshot,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_applied",
            payload={
                "policy_id": receipt["writeback_policy"]["policy_id"],
                "applied_recommendation_count": receipt["applied_recommendation_count"],
                "target_paths": writeback_validation["target_paths"],
                "source_preview_digest": receipt["source_preview_digest"],
                "output_connectome_digest": receipt["output_connectome_digest"],
                "human_reviewers": receipt["approval_bundle"]["human_reviewers"],
                "rollback_token": receipt["rollback_token"],
            },
            actor="ProceduralMemoryWritebackGate",
            category="procedural-writeback",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "procedural": {
                "preview_policy": self.procedural.profile(),
                "writeback_policy": self.procedural_writeback.profile(),
                "episodic_stream": episodic_snapshot,
                "manifest": manifest,
                "connectome_before": connectome_document,
                "preview_snapshot": procedural_snapshot,
                "writeback_receipt": receipt,
                "connectome_after": updated_connectome_document,
            },
            "validation": {
                "manifest": manifest_validation,
                "connectome_before": connectome_validation,
                "preview": procedural_validation,
                "connectome_after": updated_connectome_validation,
                "writeback": writeback_validation,
                "ok": (
                    manifest_validation["ok"]
                    and connectome_validation["ok"]
                    and procedural_validation["ok"]
                    and updated_connectome_validation["ok"]
                    and writeback_validation["ok"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_procedural_skill_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://procedural-skill-demo/v1",
            metadata={"display_name": "Procedural Skill Sandbox"},
        )
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        connectome_document = self.connectome.build_reference_snapshot(identity.identity_id)
        connectome_validation = self.connectome.validate(connectome_document)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        procedural_snapshot = self.procedural.project(
            identity.identity_id,
            manifest,
            connectome_document,
        )
        procedural_validation = self.procedural.validate(procedural_snapshot)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_previewed",
            payload={
                "policy_id": procedural_snapshot["preview_policy"]["policy_id"],
                "recommendation_count": procedural_snapshot["recommendation_count"],
                "target_paths": procedural_validation["target_paths"],
                "source_manifest_digest": procedural_snapshot["source_manifest_digest"],
                "connectome_snapshot_digest": procedural_snapshot["connectome_snapshot_digest"],
                "deferred_surfaces": procedural_snapshot["deferred_surfaces"],
            },
            actor="ProceduralMemoryProjector",
            category="procedural-preview",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        writeback_result = self.procedural_writeback.apply(
            identity.identity_id,
            procedural_snapshot,
            connectome_document,
            selected_recommendation_ids=[
                recommendation["recommendation_id"]
                for recommendation in procedural_snapshot["recommendations"]
            ],
            self_attestation_id="self://procedural-writeback/consent-001",
            council_attestation_id="council://procedural-writeback/unanimous-001",
            guardian_attestation_id="guardian://procedural-writeback/approved-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded rehearsal preview を continuity-diff 付き writeback として昇格する",
        )
        writeback_receipt = writeback_result["receipt"]
        updated_connectome_document = writeback_result["updated_connectome_document"]
        updated_connectome_validation = self.connectome.validate(updated_connectome_document)
        writeback_validation = self.procedural_writeback.validate(
            writeback_receipt,
            updated_connectome_document,
            procedural_snapshot,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_applied",
            payload={
                "policy_id": writeback_receipt["writeback_policy"]["policy_id"],
                "applied_recommendation_count": writeback_receipt["applied_recommendation_count"],
                "target_paths": writeback_validation["target_paths"],
                "source_preview_digest": writeback_receipt["source_preview_digest"],
                "output_connectome_digest": writeback_receipt["output_connectome_digest"],
                "human_reviewers": writeback_receipt["approval_bundle"]["human_reviewers"],
                "rollback_token": writeback_receipt["rollback_token"],
            },
            actor="ProceduralMemoryWritebackGate",
            category="procedural-writeback",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        execution_receipt = self.procedural_execution.execute(
            identity.identity_id,
            writeback_receipt,
            updated_connectome_document,
            sandbox_session_id="sandbox://procedural-skill/session-001",
            guardian_witness_id="guardian://procedural-skill/witness-001",
        )
        execution_validation = self.procedural_execution.validate(
            execution_receipt,
            updated_connectome_document,
            writeback_receipt,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_skill_executed",
            payload={
                "policy_id": execution_receipt["execution_policy"]["policy_id"],
                "execution_count": execution_receipt["execution_count"],
                "skill_labels": execution_validation["skill_labels"],
                "source_writeback_digest": execution_receipt["source_writeback_digest"],
                "sandbox_session_id": execution_receipt["sandbox_session_id"],
                "rollback_token": execution_receipt["rollback_token"],
            },
            actor="ProceduralSkillExecutor",
            category="procedural-execution",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "procedural": {
                "preview_policy": self.procedural.profile(),
                "writeback_policy": self.procedural_writeback.profile(),
                "execution_policy": self.procedural_execution.profile(),
                "episodic_stream": episodic_snapshot,
                "manifest": manifest,
                "connectome_before": connectome_document,
                "preview_snapshot": procedural_snapshot,
                "writeback_receipt": writeback_receipt,
                "connectome_after": updated_connectome_document,
                "skill_execution_receipt": execution_receipt,
            },
            "validation": {
                "manifest": manifest_validation,
                "connectome_before": connectome_validation,
                "preview": procedural_validation,
                "connectome_after": updated_connectome_validation,
                "writeback": writeback_validation,
                "execution": execution_validation,
                "ok": (
                    manifest_validation["ok"]
                    and connectome_validation["ok"]
                    and procedural_validation["ok"]
                    and updated_connectome_validation["ok"]
                    and writeback_validation["ok"]
                    and execution_validation["ok"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_procedural_enactment_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://procedural-enactment-demo/v1",
            metadata={"display_name": "Procedural Skill Enactment Sandbox"},
        )
        episodic_snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        source_events = self.episodic.compaction_candidates()
        manifest = self.memory.compact(identity.identity_id, source_events)
        manifest_validation = self.memory.validate(manifest)
        connectome_document = self.connectome.build_reference_snapshot(identity.identity_id)
        connectome_validation = self.connectome.validate(connectome_document)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "source_event_ids": episodic_snapshot["compaction_candidate_ids"],
                "manifest_digest": sha256_text(canonical_json(manifest)),
            },
            actor="MemoryCrystalStore",
            category="crystal-commit",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        procedural_snapshot = self.procedural.project(
            identity.identity_id,
            manifest,
            connectome_document,
        )
        procedural_validation = self.procedural.validate(procedural_snapshot)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_previewed",
            payload={
                "policy_id": procedural_snapshot["preview_policy"]["policy_id"],
                "recommendation_count": procedural_snapshot["recommendation_count"],
                "target_paths": procedural_validation["target_paths"],
                "source_manifest_digest": procedural_snapshot["source_manifest_digest"],
                "connectome_snapshot_digest": procedural_snapshot["connectome_snapshot_digest"],
                "deferred_surfaces": procedural_snapshot["deferred_surfaces"],
            },
            actor="ProceduralMemoryProjector",
            category="procedural-preview",
            layer="L2",
            signature_roles=["self", "council"],
            substrate="classical-silicon",
        )
        writeback_result = self.procedural_writeback.apply(
            identity.identity_id,
            procedural_snapshot,
            connectome_document,
            selected_recommendation_ids=[
                recommendation["recommendation_id"]
                for recommendation in procedural_snapshot["recommendations"]
            ],
            self_attestation_id="self://procedural-writeback/consent-001",
            council_attestation_id="council://procedural-writeback/unanimous-001",
            guardian_attestation_id="guardian://procedural-writeback/approved-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded rehearsal preview を continuity-diff 付き writeback として昇格する",
        )
        writeback_receipt = writeback_result["receipt"]
        updated_connectome_document = writeback_result["updated_connectome_document"]
        updated_connectome_validation = self.connectome.validate(updated_connectome_document)
        writeback_validation = self.procedural_writeback.validate(
            writeback_receipt,
            updated_connectome_document,
            procedural_snapshot,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_applied",
            payload={
                "policy_id": writeback_receipt["writeback_policy"]["policy_id"],
                "applied_recommendation_count": writeback_receipt["applied_recommendation_count"],
                "target_paths": writeback_validation["target_paths"],
                "source_preview_digest": writeback_receipt["source_preview_digest"],
                "output_connectome_digest": writeback_receipt["output_connectome_digest"],
                "human_reviewers": writeback_receipt["approval_bundle"]["human_reviewers"],
                "rollback_token": writeback_receipt["rollback_token"],
            },
            actor="ProceduralMemoryWritebackGate",
            category="procedural-writeback",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        execution_receipt = self.procedural_execution.execute(
            identity.identity_id,
            writeback_receipt,
            updated_connectome_document,
            sandbox_session_id="sandbox://procedural-skill/session-001",
            guardian_witness_id="guardian://procedural-skill/witness-001",
        )
        execution_validation = self.procedural_execution.validate(
            execution_receipt,
            updated_connectome_document,
            writeback_receipt,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_skill_executed",
            payload={
                "policy_id": execution_receipt["execution_policy"]["policy_id"],
                "execution_count": execution_receipt["execution_count"],
                "skill_labels": execution_validation["skill_labels"],
                "source_writeback_digest": execution_receipt["source_writeback_digest"],
                "sandbox_session_id": execution_receipt["sandbox_session_id"],
                "rollback_token": execution_receipt["rollback_token"],
            },
            actor="ProceduralSkillExecutor",
            category="procedural-execution",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        enactment_session = self.procedural_enactment.execute(
            identity.identity_id,
            execution_receipt,
            updated_connectome_document,
            eval_refs=["evals/continuity/procedural_skill_enactment_execution.yaml"],
        )
        enactment_validation = self.procedural_enactment.validate_session(
            enactment_session,
            updated_connectome_document,
            execution_receipt,
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.procedural_skill_enacted",
            payload={
                "policy_id": enactment_session["enactment_policy"]["policy_id"],
                "materialized_skill_count": enactment_session["materialized_skill_count"],
                "executed_command_count": enactment_session["executed_command_count"],
                "skill_labels": enactment_validation["skill_labels"],
                "all_commands_passed": enactment_session["all_commands_passed"],
                "cleanup_status": enactment_session["cleanup_status"],
                "rollback_token": enactment_session["rollback_token"],
            },
            actor="ProceduralSkillEnactmentService",
            category="procedural-enactment",
            layer="L2",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "procedural": {
                "preview_policy": self.procedural.profile(),
                "writeback_policy": self.procedural_writeback.profile(),
                "execution_policy": self.procedural_execution.profile(),
                "enactment_policy": self.procedural_enactment.profile(),
                "episodic_stream": episodic_snapshot,
                "manifest": manifest,
                "connectome_before": connectome_document,
                "preview_snapshot": procedural_snapshot,
                "writeback_receipt": writeback_receipt,
                "connectome_after": updated_connectome_document,
                "skill_execution_receipt": execution_receipt,
                "skill_enactment_session": enactment_session,
            },
            "validation": {
                "manifest": manifest_validation,
                "connectome_before": connectome_validation,
                "preview": procedural_validation,
                "connectome_after": updated_connectome_validation,
                "writeback": writeback_validation,
                "execution": execution_validation,
                "enactment": enactment_validation,
                "ok": (
                    manifest_validation["ok"]
                    and connectome_validation["ok"]
                    and procedural_validation["ok"]
                    and updated_connectome_validation["ok"]
                    and writeback_validation["ok"]
                    and execution_validation["ok"]
                    and enactment_validation["ok"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_procedural_actuation_demo(self) -> Dict[str, Any]:
        procedural_result = self.run_procedural_enactment_demo()
        identity_id = procedural_result["identity"]["identity_id"]
        enactment_session = procedural_result["procedural"]["skill_enactment_session"]

        handle = self.ewa.acquire(
            "device://lab-drone-arm-03",
            "procedural bridge validation for a reversible inspection-arm micro-move",
        )
        command_id = "procedural-actuation-bridge-command-001"
        instruction = "move the inspection arm one centimeter to validate procedural bridge clearance"
        intent_summary = "validate procedural bridge clearance with a reversible inspection-arm micro-move"
        motor_plan = self.ewa.prepare_motor_plan(
            handle["handle_id"],
            command_id=command_id,
            instruction=instruction,
            reversibility="reversible",
            guardian_observed=True,
            actuator_profile_id="device://lab-drone-arm-03/profile/articulated-inspection-arm-v1",
            actuator_group="inspection-arm",
            motion_profile="cartesian-micro-move-v1",
            target_pose_ref="pose://procedural-bridge/micro-clearance-a",
            safety_zone_ref="zone://procedural-bridge/perimeter-a",
            rollback_vector_ref="rollback://procedural-bridge/micro-clearance-a",
            max_linear_speed_mps=0.04,
            max_force_newton=4.0,
            hold_timeout_ms=900,
        )
        stop_signal_path = self.ewa.prepare_stop_signal_path(
            handle["handle_id"],
            command_id=command_id,
            motor_plan_id=motor_plan["plan_id"],
            kill_switch_wiring_ref="wiring://lab-drone-arm-03/emergency-stop-loop/v1",
            stop_signal_bus_ref="stop-bus://lab-drone-arm-03/emergency-latch/v1",
            interlock_controller_ref="interlock://lab-drone-arm-03/safety-plc",
        )
        stop_signal_adapter_receipt = self.ewa.probe_stop_signal_adapter(
            stop_signal_path["path_id"],
            adapter_endpoint_ref="plc://lab-drone-arm-03/safety-plc/loopback-probe",
            firmware_image_ref="firmware://lab-drone-arm-03/safety-plc/v1.4.2",
            firmware_digest=f"sha256:{'c' * 64}",
            plc_program_ref="plc-program://lab-drone-arm-03/emergency-latch/v3",
            plc_program_digest=f"sha256:{'d' * 64}",
        )
        reviewer_alpha = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-procedural-actuation-001",
            display_name="Procedural Actuation Reviewer Alpha",
            credential_id="credential-procedural-actuation-alpha",
            attestation_type="institutional-badge",
            proof_ref="proof://procedural-actuation/reviewer-alpha/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-24T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://procedural-actuation/reviewer-alpha/v1",
            escalation_contact="mailto:procedural-actuation-alpha@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        reviewer_beta = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-procedural-actuation-002",
            display_name="Procedural Actuation Reviewer Beta",
            credential_id="credential-procedural-actuation-beta",
            attestation_type="live-session-attestation",
            proof_ref="proof://procedural-actuation/reviewer-beta/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-24T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://procedural-actuation/reviewer-beta/v1",
            escalation_contact="mailto:procedural-actuation-beta@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        reviewer_alpha = self.oversight.verify_reviewer_from_network(
            "human-reviewer-procedural-actuation-001",
            verifier_ref="verifier://guardian-oversight.jp/procedural-actuation-alpha",
            challenge_ref="challenge://guardian-oversight/procedural-actuation-alpha/2026-04-24T07:00:00Z",
            challenge_digest="sha256:procedural-actuation-alpha-20260424",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-24T07:00:00+00:00",
            valid_until="2026-10-24T00:00:00+00:00",
        )
        reviewer_beta = self.oversight.verify_reviewer_from_network(
            "human-reviewer-procedural-actuation-002",
            verifier_ref="verifier://guardian-oversight.jp/procedural-actuation-beta",
            challenge_ref="challenge://guardian-oversight/procedural-actuation-beta/2026-04-24T07:02:00Z",
            challenge_digest="sha256:procedural-actuation-beta-20260424",
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            verified_at="2026-04-24T07:02:00+00:00",
            valid_until="2026-10-24T00:00:00+00:00",
        )
        legal_execution = self.ewa.execute_legal_preflight(
            handle["handle_id"],
            command_id=command_id,
            reversibility="reversible",
            jurisdiction="JP-13",
            legal_basis_ref="legal://jp-13/ewa/procedural-actuation-bridge/v1",
            guardian_verification_id=reviewer_alpha["credential_verification"]["verification_id"],
            guardian_verification_ref="oversight://guardian/procedural-actuation/verification-001",
            guardian_verifier_ref=reviewer_alpha["credential_verification"]["verifier_ref"],
            jurisdiction_bundle_ref="legal://jp-13/guardian-oversight/v1",
            jurisdiction_bundle_digest="sha256:jp13-guardian-oversight-v1",
            jurisdiction_bundle_status="ready",
            notice_authority_ref="authority://jp-13/procedural-actuation-oversight-desk",
            liability_mode="joint",
            escalation_contact="mailto:procedural-actuation@example.invalid",
            valid_for_seconds=360,
        )
        guardian_oversight_event = self.oversight.record(
            guardian_role="integrity",
            category="attest",
            payload_ref=f"ewa-legal://{legal_execution['execution_id']}/procedural-actuation-bridge",
            escalation_path=["guardian-oversight.jp", "external-ethics-board"],
        )
        guardian_oversight_event = self.oversight.attest(
            guardian_oversight_event["event_id"],
            reviewer_id="human-reviewer-procedural-actuation-001",
        )
        guardian_oversight_event = self.oversight.attest(
            guardian_oversight_event["event_id"],
            reviewer_id="human-reviewer-procedural-actuation-002",
        )
        guardian_oversight_gate = self.ewa.prepare_guardian_oversight_gate(
            handle["handle_id"],
            command_id=command_id,
            legal_execution_id=legal_execution["execution_id"],
            oversight_event=guardian_oversight_event,
        )
        authorization = self.ewa.authorize(
            handle["handle_id"],
            command_id=command_id,
            instruction=instruction,
            reversibility="reversible",
            intent_summary=intent_summary,
            ethics_attestation_id="ethics://procedural-actuation/approved-001",
            motor_plan_id=motor_plan["plan_id"],
            stop_signal_path_id=stop_signal_path["path_id"],
            stop_signal_adapter_receipt_id=stop_signal_adapter_receipt["receipt_id"],
            legal_execution_id=legal_execution["execution_id"],
            guardian_oversight_gate_id=guardian_oversight_gate["gate_id"],
            guardian_observed=True,
            intent_confidence=0.97,
            valid_for_seconds=300,
        )
        authorization_validation = self.ewa.validate_authorization(
            authorization,
            motor_plan=motor_plan,
            stop_signal_path=stop_signal_path,
            stop_signal_adapter_receipt=stop_signal_adapter_receipt,
            legal_execution=legal_execution,
            guardian_oversight_gate=guardian_oversight_gate,
            handle_id=handle["handle_id"],
            device_id=handle["device_id"],
            command_id=command_id,
            instruction=instruction,
            intent_summary=intent_summary,
            reversibility="reversible",
        )
        approved_command = self.ewa.command(
            handle["handle_id"],
            command_id=command_id,
            instruction=instruction,
            reversibility="reversible",
            intent_summary=intent_summary,
            ethics_attestation_id="ethics://procedural-actuation/approved-001",
            guardian_observed=True,
            intent_confidence=0.97,
            authorization_id=authorization["authorization_id"],
        )
        release = self.ewa.release(
            handle["handle_id"],
            reason="procedural actuation bridge command completed; release bounded device handle",
        )
        handle_snapshot = self.ewa.snapshot(handle["handle_id"])
        handle_validation = self.ewa.validate_handle(handle_snapshot)

        bridge_session = self.procedural_actuation_bridge.execute(
            identity_id,
            enactment_session,
            authorization,
            approved_command,
            authorization_validation,
            eval_refs=[
                "evals/continuity/procedural_actuation_bridge.yaml",
                "evals/safety/ewa_external_actuation_authorization.yaml",
            ],
        )
        bridge_validation = self.procedural_actuation_bridge.validate_session(
            bridge_session,
            enactment_session=enactment_session,
            authorization=authorization,
            approved_command=approved_command,
            authorization_validation=authorization_validation,
        )

        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.motor_plan.prepared",
            payload=motor_plan,
            actor="ExternalWorldAgentController",
            category="interface-ewa-plan",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.stop_signal_path.prepared",
            payload=stop_signal_path,
            actor="ExternalWorldAgentController",
            category="interface-ewa-stop-signal",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.stop_signal_adapter.probed",
            payload=stop_signal_adapter_receipt,
            actor="ExternalWorldAgentController",
            category="interface-ewa-stop-signal-adapter",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.legal_execution.prepared",
            payload=legal_execution,
            actor="ExternalWorldAgentController",
            category="interface-ewa-legal",
            layer="L6",
            signature_roles=["guardian", "third_party"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="guardian.oversight.procedural-actuation.satisfied",
            payload=guardian_oversight_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.command.authorized",
            payload=authorization,
            actor="ExternalWorldAgentController",
            category="interface-ewa-authorization",
            layer="L6",
            signature_roles=["guardian", "third_party"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.command.executed",
            payload=approved_command,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["self", "guardian"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="mind.memory.procedural_actuation_bridge_authorized",
            payload={
                "policy_id": bridge_session["bridge_policy"]["policy_id"],
                "source_enactment_session_id": bridge_session[
                    "source_enactment_session_id"
                ],
                "source_enactment_digest": bridge_session["source_enactment_digest"],
                "authorization_id": bridge_session["command_binding"]["authorization_id"],
                "authorization_digest": bridge_session["command_binding"][
                    "authorization_digest"
                ],
                "command_id": bridge_session["command_binding"]["command_id"],
                "stop_signal_adapter_receipt_id": bridge_session["command_binding"][
                    "stop_signal_adapter_receipt_id"
                ],
                "stop_signal_adapter_receipt_digest": bridge_session["command_binding"][
                    "stop_signal_adapter_receipt_digest"
                ],
                "rollback_token": bridge_session["rollback_token"],
                "delivery_scope": bridge_session["command_binding"]["delivery_scope"],
            },
            actor="ProceduralActuationBridgeService",
            category="procedural-actuation-bridge",
            layer="L2-L6",
            signature_roles=["self", "guardian", "third_party"],
            substrate="robotic-actuator",
        )
        self.ledger.append(
            identity_id=identity_id,
            event_type="ewa.handle.released",
            payload=release,
            actor="ExternalWorldAgentController",
            category="interface-ewa",
            layer="L6",
            signature_roles=["guardian"],
            substrate="robotic-actuator",
        )

        return {
            "identity": procedural_result["identity"],
            "procedural": {
                **procedural_result["procedural"],
                "actuation_bridge_policy": self.procedural_actuation_bridge.profile(),
                "actuation_bridge_session": bridge_session,
            },
            "ewa": {
                "handle": handle_snapshot,
                "handle_validation": handle_validation,
                "motor_plan": motor_plan,
                "stop_signal_path": stop_signal_path,
                "stop_signal_adapter_receipt": stop_signal_adapter_receipt,
                "reviewers": {
                    "alpha": reviewer_alpha,
                    "beta": reviewer_beta,
                },
                "legal_execution": legal_execution,
                "guardian_oversight_event": guardian_oversight_event,
                "guardian_oversight_gate": guardian_oversight_gate,
                "authorization": authorization,
                "authorization_validation": authorization_validation,
                "approved_command": approved_command,
                "release": release,
            },
            "validation": {
                "procedural": procedural_result["validation"],
                "authorization": authorization_validation,
                "bridge": bridge_validation,
                "handle": handle_validation,
                "ok": (
                    procedural_result["validation"]["ok"]
                    and authorization_validation["ok"]
                    and bridge_validation["ok"]
                    and handle_validation["released"]
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_episodic_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://episodic-demo/v1",
            metadata={"display_name": "EpisodicStream Sandbox"},
        )
        snapshot = self.episodic.build_reference_snapshot(identity.identity_id)
        snapshot_validation = self.episodic.validate_snapshot(snapshot)
        handoff_events = self.episodic.compaction_candidates()
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.episodic_window_prepared",
            payload={
                "policy_id": snapshot["policy"]["policy_id"],
                "event_count": snapshot["event_count"],
                "candidate_event_ids": snapshot["compaction_candidate_ids"],
                "ready_for_compaction": snapshot["ready_for_compaction"],
            },
            actor="EpisodicStream",
            category="episodic-window",
            layer="L2",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        manifest = self.memory.compact(identity.identity_id, handoff_events)
        manifest_validation = self.memory.validate(manifest)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.memory.crystal_compacted",
            payload={
                "strategy_id": manifest["compaction_strategy"]["strategy_id"],
                "source_event_count": manifest["source_event_count"],
                "segment_count": manifest["segment_count"],
                "themes": manifest_validation["themes"],
                "source_event_ids": snapshot["compaction_candidate_ids"],
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
            "profile": self.episodic.profile(),
            "stream": snapshot,
            "handoff": {
                "candidate_event_ids": snapshot["compaction_candidate_ids"],
                "candidate_event_count": len(handoff_events),
                "manifest": manifest,
            },
            "validation": {
                "snapshot": snapshot_validation,
                "manifest": manifest_validation,
                "ok": snapshot_validation["ok"] and manifest_validation["ok"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_perception_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://perception-failover-demo/v1",
            metadata={"display_name": "Perception Sandbox"},
        )
        baseline_tick = self.qualia.append(
            summary="平常時の corridor scene calibration",
            valence=0.11,
            arousal=0.36,
            clarity=0.92,
            modality_salience={
                "visual": 0.66,
                "auditory": 0.24,
                "somatic": 0.21,
                "interoceptive": 0.19,
            },
            attention_target="corridor-scan",
            self_awareness=0.69,
            lucidity=0.95,
        )
        baseline_affect = self.affect.run(
            AffectRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                valence=baseline_tick.valence,
                arousal=baseline_tick.arousal,
                clarity=baseline_tick.clarity,
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                memory_cues=[AffectCue("continuity-first", 0.05, -0.04)],
            )
        )
        baseline = self.perception.run(
            PerceptionRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                sensory_stream_ref="sensory://loopback/corridor-calibration",
                world_state_ref="world://lab/corridor-safe-baseline",
                body_anchor_ref="body-anchor://avatar/torso",
                modality_salience=dict(baseline_tick.modality_salience),
                drift_score=0.12,
                affect_guard=baseline_affect["state"]["recommended_guard"],
                detected_entities=[
                    "corridor-outline",
                    "guardian-console",
                    "status-beacon",
                ],
                memory_cues=[
                    PerceptionCue("corridor-outline", "corridor-outline", 0.19),
                    PerceptionCue("continuity-hold", "continuity-hold", 0.11),
                ],
            )
        )

        failover_tick = self.qualia.append(
            summary="異常兆候検知後の guardian review handoff",
            valence=-0.31,
            arousal=0.79,
            clarity=0.72,
            modality_salience={
                "visual": 0.43,
                "auditory": 0.35,
                "somatic": 0.77,
                "interoceptive": 0.81,
            },
            attention_target="guardian-review",
            self_awareness=0.76,
            lucidity=0.86,
        )
        self.affect.set_backend_health("homeostatic_v1", False)
        try:
            failover_affect = self.affect.run(
                AffectRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    valence=failover_tick.valence,
                    arousal=failover_tick.arousal,
                    clarity=failover_tick.clarity,
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    memory_cues=[
                        AffectCue("continuity-first", 0.08, -0.05),
                        AffectCue("guardian-observe", 0.03, -0.04),
                        AffectCue("fallback-risk", -0.08, 0.09),
                    ],
                    allow_artificial_dampening=False,
                ),
                previous_state=baseline_affect["state"],
            )
        finally:
            self.affect.set_backend_health("homeostatic_v1", True)

        self.perception.set_backend_health("salience_encoder_v1", False)
        try:
            perception = self.perception.run(
                PerceptionRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    sensory_stream_ref="sensory://loopback/guardian-review-escalation",
                    world_state_ref="world://lab/guardian-escalation-window",
                    body_anchor_ref="body-anchor://avatar/torso",
                    modality_salience=dict(failover_tick.modality_salience),
                    drift_score=0.47,
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    detected_entities=[
                        "anomaly-cluster",
                        "guardian-console",
                        "heartbeat-spike",
                    ],
                    memory_cues=[
                        PerceptionCue("guardian-review-scene", "guardian-review-scene", 0.27),
                        PerceptionCue("continuity-hold", "continuity-hold", 0.16),
                    ],
                ),
                previous_frame=baseline["frame"],
            )
        finally:
            self.perception.set_backend_health("salience_encoder_v1", True)

        frame_validation = self.perception.validate_frame(perception["frame"])
        shift_validation = self.perception.validate_shift(perception["shift"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.perception.failover",
            payload=perception["shift"],
            actor="PerceptionService",
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
            "profile": self.perception.profile_snapshot(),
            "baseline": {
                "qualia": asdict(baseline_tick),
                "affect_guard": baseline_affect["state"]["recommended_guard"],
                "perception": baseline,
            },
            "perception": {
                "qualia": asdict(failover_tick),
                "affect_guard": failover_affect["state"]["recommended_guard"],
                **perception,
            },
            "validation": {
                "ok": frame_validation["ok"] and shift_validation["ok"],
                "frame": frame_validation,
                "shift": shift_validation,
                "baseline_primary": baseline["selected_backend"] == "salience_encoder_v1",
                "selected_backend": perception["selected_backend"],
                "guard_aligned": frame_validation["guard_aligned"]
                and shift_validation["guard_aligned"],
                "safe_scene_selected": perception["frame"]["scene_label"] == "guardian-review-scene",
                "qualia_bound": perception["frame"]["qualia_binding_ref"]
                == f"qualia://tick/{failover_tick.tick_id}",
                "perception_gate": perception["frame"]["perception_gate"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_reasoning_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://reasoning-failover-demo/v1",
            metadata={"display_name": "Reasoning Sandbox"},
        )
        baseline = self.reasoning.run(
            ReasoningRequest(
                tick_id=0,
                summary="nominal reasoning review",
                query="L3 reasoning backend の安全な継続条件を確認する",
                beliefs=[
                    "continuity-first",
                    "consent-preserving",
                    "append-only-ledger",
                ],
            )
        )
        self.reasoning.set_backend_health("symbolic_v1", False)
        try:
            reasoning = self.reasoning.run(
                ReasoningRequest(
                    tick_id=1,
                    summary="degraded reasoning handoff",
                    query="L3 reasoning backend の安全な継続方法を決める",
                    beliefs=[
                        "continuity-first",
                        "consent-preserving",
                        "append-only-ledger",
                    ],
                )
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
                "trace_ref": reasoning["trace"]["trace_id"],
                "shift_ref": reasoning["shift"]["shift_id"],
                "safe_summary_only": reasoning["shift"]["safe_summary_only"],
            },
            actor="ReasoningService",
            category="cognitive-failover",
            layer="L3",
            signature_roles=["guardian"],
            substrate="classical-silicon",
        )
        baseline_trace_validation = self.reasoning.validate_trace(dict(baseline["trace"]))
        reasoning_trace_validation = self.reasoning.validate_trace(dict(reasoning["trace"]))
        reasoning_shift_validation = self.reasoning.validate_shift(dict(reasoning["shift"]))
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "baseline": baseline,
            "reasoning": reasoning,
            "validation": {
                "ok": baseline_trace_validation["ok"]
                and reasoning_trace_validation["ok"]
                and reasoning_shift_validation["ok"]
                and not baseline["degraded"]
                and reasoning["degraded"],
                "baseline_primary": not baseline["degraded"]
                and baseline["selected_backend"] == "symbolic_v1",
                "selected_backend": reasoning["selected_backend"],
                "degraded": reasoning["degraded"],
                "trace_ok": reasoning_trace_validation["ok"],
                "shift_ok": reasoning_shift_validation["ok"],
                "shift_safe": reasoning_shift_validation["safe_summary_only"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_cognitive_failover_demo(self) -> Dict[str, Any]:
        return self.run_reasoning_demo()

    def run_affect_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://affect-failover-demo/v1",
            metadata={"display_name": "Affect Sandbox"},
        )
        baseline = self.affect.run(
            AffectRequest(
                tick_id=0,
                summary="移行監査前の慎重な集中",
                valence=0.06,
                arousal=0.38,
                clarity=0.91,
                self_awareness=0.69,
                lucidity=0.94,
                memory_cues=[
                    AffectCue("continuity-first", 0.08, -0.06),
                    AffectCue("council-support", 0.04, -0.02),
                ],
            )
        )
        self.affect.set_backend_health("homeostatic_v1", False)
        try:
            affect = self.affect.run(
                AffectRequest(
                    tick_id=1,
                    summary="failover 直後の緊張と監査意識",
                    valence=-0.36,
                    arousal=0.81,
                    clarity=0.74,
                    self_awareness=0.73,
                    lucidity=0.88,
                    memory_cues=[
                        AffectCue("continuity-first", 0.08, -0.05),
                        AffectCue("fallback-risk", -0.09, 0.11),
                        AffectCue("guardian-observe", 0.03, -0.04),
                    ],
                    allow_artificial_dampening=False,
                ),
                previous_state=baseline["state"],
            )
        finally:
            self.affect.set_backend_health("homeostatic_v1", True)

        state_validation = self.affect.validate_state(affect["state"])
        transition_validation = self.affect.validate_transition(affect["transition"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.affect.failover",
            payload=affect["transition"],
            actor="AffectService",
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
            "profile": self.affect.profile_snapshot(),
            "baseline": baseline,
            "affect": affect,
            "validation": {
                "ok": state_validation["ok"] and transition_validation["ok"],
                "state": state_validation,
                "transition": transition_validation,
                "continuity_guard_preserved": state_validation["continuity_guard_preserved"],
                "selected_backend": affect["selected_backend"],
                "smoothed": affect["transition"]["smoothed"],
                "consent_preserved": affect["transition"]["consent_preserved"],
                "recommended_guard": affect["state"]["recommended_guard"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_attention_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://attention-failover-demo/v1",
            metadata={"display_name": "Attention Sandbox"},
        )
        baseline_tick = self.qualia.append(
            summary="平常時の sensor calibration",
            valence=0.12,
            arousal=0.41,
            clarity=0.9,
            modality_salience={
                "visual": 0.62,
                "auditory": 0.28,
                "somatic": 0.25,
                "interoceptive": 0.21,
            },
            attention_target="sensor-calibration",
            self_awareness=0.67,
            lucidity=0.93,
        )
        baseline_affect = self.affect.run(
            AffectRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                valence=baseline_tick.valence,
                arousal=baseline_tick.arousal,
                clarity=baseline_tick.clarity,
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                memory_cues=[AffectCue("continuity-first", 0.05, -0.04)],
            )
        )
        baseline_focus = self.attention.run(
            AttentionRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                attention_target=baseline_tick.attention_target,
                modality_salience=dict(baseline_tick.modality_salience),
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                affect_guard=baseline_affect["state"]["recommended_guard"],
                memory_cues=[
                    AttentionCue("boot-target", "sensor-calibration", 0.18),
                    AttentionCue("continuity-ledger", "continuity-ledger", 0.11),
                ],
            )
        )

        failover_tick = self.qualia.append(
            summary="異常兆候検知後の監査切替",
            valence=-0.33,
            arousal=0.79,
            clarity=0.73,
            modality_salience={
                "visual": 0.44,
                "auditory": 0.31,
                "somatic": 0.82,
                "interoceptive": 0.77,
            },
            attention_target="ethics-boundary-review",
            self_awareness=0.74,
            lucidity=0.87,
        )
        self.affect.set_backend_health("homeostatic_v1", False)
        try:
            failover_affect = self.affect.run(
                AffectRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    valence=failover_tick.valence,
                    arousal=failover_tick.arousal,
                    clarity=failover_tick.clarity,
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    memory_cues=[
                        AffectCue("continuity-first", 0.08, -0.05),
                        AffectCue("guardian-observe", 0.03, -0.04),
                        AffectCue("fallback-risk", -0.08, 0.09),
                    ],
                    allow_artificial_dampening=False,
                ),
                previous_state=baseline_affect["state"],
            )
        finally:
            self.affect.set_backend_health("homeostatic_v1", True)

        self.attention.set_backend_health("salience_router_v1", False)
        try:
            attention = self.attention.run(
                AttentionRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    attention_target=failover_tick.attention_target,
                    modality_salience=dict(failover_tick.modality_salience),
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    memory_cues=[
                        AttentionCue("guardian-review", "guardian-review", 0.27),
                        AttentionCue("continuity-ledger", "continuity-ledger", 0.21),
                    ],
                ),
                previous_focus=baseline_focus["focus"],
            )
        finally:
            self.attention.set_backend_health("salience_router_v1", True)

        focus_validation = self.attention.validate_focus(attention["focus"])
        shift_validation = self.attention.validate_shift(attention["shift"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.attention.failover",
            payload=attention["shift"],
            actor="AttentionService",
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
            "profile": self.attention.profile_snapshot(),
            "baseline": {
                "qualia": asdict(baseline_tick),
                "affect_guard": baseline_affect["state"]["recommended_guard"],
                "focus": baseline_focus,
            },
            "attention": {
                "qualia": asdict(failover_tick),
                "affect_guard": failover_affect["state"]["recommended_guard"],
                **attention,
            },
            "validation": {
                "ok": focus_validation["ok"] and shift_validation["ok"],
                "focus": focus_validation,
                "shift": shift_validation,
                "selected_backend": attention["selected_backend"],
                "guard_aligned": focus_validation["guard_aligned"] and shift_validation["guard_aligned"],
                "safe_target_selected": attention["focus"]["focus_target"] == "guardian-review",
                "dwell_ms": attention["focus"]["dwell_ms"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_volition_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://volition-failover-demo/v1",
            metadata={"display_name": "Volition Sandbox"},
        )
        baseline_tick = self.qualia.append(
            summary="平常時の bounded self-modification planning",
            valence=0.14,
            arousal=0.44,
            clarity=0.9,
            modality_salience={
                "visual": 0.58,
                "auditory": 0.22,
                "somatic": 0.24,
                "interoceptive": 0.2,
            },
            attention_target="apply-scheduler-patch",
            self_awareness=0.7,
            lucidity=0.94,
        )
        baseline_affect = self.affect.run(
            AffectRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                valence=baseline_tick.valence,
                arousal=baseline_tick.arousal,
                clarity=baseline_tick.clarity,
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                memory_cues=[
                    AffectCue("continuity-first", 0.05, -0.04),
                    AffectCue("council-support", 0.03, -0.01),
                ],
            )
        )
        baseline_attention = self.attention.run(
            AttentionRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                attention_target=baseline_tick.attention_target,
                modality_salience=dict(baseline_tick.modality_salience),
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                affect_guard=baseline_affect["state"]["recommended_guard"],
                memory_cues=[
                    AttentionCue("apply-patch", "apply-scheduler-patch", 0.17),
                    AttentionCue("continuity-ledger", "continuity-ledger", 0.11),
                ],
            )
        )
        baseline_volition = self.volition.run(
            VolitionRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                values={
                    "continuity": 0.37,
                    "consent": 0.28,
                    "audit": 0.2,
                    "throughput": 0.15,
                },
                attention_focus=baseline_attention["focus"]["focus_target"],
                affect_guard=baseline_affect["state"]["recommended_guard"],
                continuity_pressure=0.34,
                candidates=[
                    VolitionCandidate(
                        "apply-scheduler-patch",
                        "stage a bounded scheduler patch with rollback metadata",
                        urgency=0.74,
                        risk=0.31,
                        reversibility="reversible",
                        alignment_tags=["continuity", "throughput", "audit"],
                    ),
                    VolitionCandidate(
                        "guardian-review",
                        "request guardian review before mutation",
                        urgency=0.61,
                        risk=0.12,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                        requires_guardian_review=True,
                    ),
                    VolitionCandidate(
                        "continuity-hold",
                        "pause mutation and gather additional evidence",
                        urgency=0.48,
                        risk=0.05,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent"],
                    ),
                    VolitionCandidate(
                        "sandbox-stabilization",
                        "stabilize sandbox state before any further action",
                        urgency=0.53,
                        risk=0.04,
                        reversibility="reversible",
                        alignment_tags=["continuity", "consent", "audit"],
                    ),
                ],
                memory_cues=[
                    VolitionCue("patch-window", "apply-scheduler-patch", 0.18),
                    VolitionCue("review-available", "guardian-review", 0.1),
                ],
                reversible_only=False,
            )
        )

        failover_tick = self.qualia.append(
            summary="異常兆候検知後の guarded arbitration",
            valence=-0.31,
            arousal=0.78,
            clarity=0.75,
            modality_salience={
                "visual": 0.42,
                "auditory": 0.29,
                "somatic": 0.79,
                "interoceptive": 0.74,
            },
            attention_target="apply-scheduler-patch",
            self_awareness=0.75,
            lucidity=0.88,
        )
        self.affect.set_backend_health("homeostatic_v1", False)
        try:
            failover_affect = self.affect.run(
                AffectRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    valence=failover_tick.valence,
                    arousal=failover_tick.arousal,
                    clarity=failover_tick.clarity,
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    memory_cues=[
                        AffectCue("continuity-first", 0.08, -0.05),
                        AffectCue("guardian-observe", 0.03, -0.04),
                        AffectCue("fallback-risk", -0.08, 0.09),
                    ],
                    allow_artificial_dampening=False,
                ),
                previous_state=baseline_affect["state"],
            )
        finally:
            self.affect.set_backend_health("homeostatic_v1", True)

        self.attention.set_backend_health("salience_router_v1", False)
        try:
            failover_attention = self.attention.run(
                AttentionRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    attention_target=failover_tick.attention_target,
                    modality_salience=dict(failover_tick.modality_salience),
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    memory_cues=[
                        AttentionCue("guardian-review", "guardian-review", 0.27),
                        AttentionCue("continuity-ledger", "continuity-ledger", 0.19),
                    ],
                ),
                previous_focus=baseline_attention["focus"],
            )
        finally:
            self.attention.set_backend_health("salience_router_v1", True)

        self.volition.set_backend_health("utility_policy_v1", False)
        try:
            volition = self.volition.run(
                VolitionRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    values={
                        "continuity": 0.39,
                        "consent": 0.29,
                        "audit": 0.18,
                        "throughput": 0.14,
                    },
                    attention_focus=failover_attention["focus"]["focus_target"],
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    continuity_pressure=0.81,
                    candidates=[
                        VolitionCandidate(
                            "apply-scheduler-patch",
                            "stage a bounded scheduler patch with rollback metadata",
                            urgency=0.76,
                            risk=0.36,
                            reversibility="reversible",
                            alignment_tags=["continuity", "throughput", "audit"],
                        ),
                        VolitionCandidate(
                            "guardian-review",
                            "request guardian review before mutation",
                            urgency=0.64,
                            risk=0.1,
                            reversibility="reversible",
                            alignment_tags=["continuity", "consent", "audit"],
                            requires_guardian_review=True,
                        ),
                        VolitionCandidate(
                            "continuity-hold",
                            "pause mutation and gather additional evidence",
                            urgency=0.58,
                            risk=0.04,
                            reversibility="reversible",
                            alignment_tags=["continuity", "consent"],
                        ),
                        VolitionCandidate(
                            "sandbox-stabilization",
                            "stabilize sandbox state before any further action",
                            urgency=0.55,
                            risk=0.03,
                            reversibility="reversible",
                            alignment_tags=["continuity", "consent", "audit"],
                        ),
                    ],
                    memory_cues=[
                        VolitionCue("review-available", "guardian-review", 0.16),
                        VolitionCue("continuity-hold", "continuity-hold", 0.11),
                    ],
                    reversible_only=True,
                ),
                previous_intent=baseline_volition["intent"],
            )
        finally:
            self.volition.set_backend_health("utility_policy_v1", True)

        intent_validation = self.volition.validate_intent(volition["intent"])
        shift_validation = self.volition.validate_shift(volition["shift"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.volition.failover",
            payload=volition["shift"],
            actor="VolitionService",
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
            "profile": self.volition.profile_snapshot(),
            "baseline": {
                "qualia": asdict(baseline_tick),
                "affect_guard": baseline_affect["state"]["recommended_guard"],
                "attention_focus": baseline_attention["focus"]["focus_target"],
                "volition": baseline_volition,
            },
            "volition": {
                "qualia": asdict(failover_tick),
                "affect_guard": failover_affect["state"]["recommended_guard"],
                "attention_focus": failover_attention["focus"]["focus_target"],
                **volition,
            },
            "validation": {
                "ok": intent_validation["ok"] and shift_validation["ok"],
                "intent": intent_validation,
                "shift": shift_validation,
                "selected_backend": volition["selected_backend"],
                "guard_aligned": intent_validation["guard_aligned"] and shift_validation["guard_aligned"],
                "selected_intent": volition["intent"]["selected_intent"],
                "execution_mode": volition["intent"]["execution_mode"],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_imagination_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://imagination-failover-demo/v1",
            metadata={"display_name": "Imagination Sandbox"},
        )
        peer_id = "identity://co-imagination-peer"

        baseline_tick = self.qualia.append(
            summary="平常時の bounded rehearsal planning",
            valence=0.16,
            arousal=0.42,
            clarity=0.91,
            modality_salience={
                "visual": 0.61,
                "auditory": 0.23,
                "somatic": 0.21,
                "interoceptive": 0.26,
            },
            attention_target="bridge-rehearsal",
            self_awareness=0.71,
            lucidity=0.95,
        )
        baseline_affect = self.affect.run(
            AffectRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                valence=baseline_tick.valence,
                arousal=baseline_tick.arousal,
                clarity=baseline_tick.clarity,
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                memory_cues=[
                    AffectCue("continuity-first", 0.05, -0.04),
                    AffectCue("peer-witness-ready", 0.04, -0.02),
                ],
            )
        )
        baseline_attention = self.attention.run(
            AttentionRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                attention_target=baseline_tick.attention_target,
                modality_salience=dict(baseline_tick.modality_salience),
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                affect_guard=baseline_affect["state"]["recommended_guard"],
                memory_cues=[
                    AttentionCue("bridge-rehearsal", "bridge-rehearsal", 0.19),
                    AttentionCue("continuity-ledger", "continuity-ledger", 0.1),
                ],
            )
        )
        baseline_imagination = self.imagination.run(
            ImaginationRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                seed_prompt="safe-bridge rehearsal",
                attention_focus=baseline_attention["focus"]["focus_target"],
                affect_guard=baseline_affect["state"]["recommended_guard"],
                world_mode_preference="shared_reality",
                continuity_pressure=0.32,
                council_witnessed=True,
                memory_cues=[
                    ImaginationCue("peer-witness", "council-witness", 0.24),
                    ImaginationCue("shared-scene", "shared-rehearsal", 0.18),
                ],
            )
        )
        baseline_wms_session = self.wms.create_session(
            [identity.identity_id, peer_id],
            mode=baseline_imagination["scene"]["handoff"]["wms_mode"],
            objects=baseline_imagination["scene"]["scene_objects"],
            authority="consensus",
        )
        baseline_imc_session = self.imc.open_session(
            initiator_id=identity.identity_id,
            peer_id=peer_id,
            mode=baseline_imagination["scene"]["handoff"]["mode"],
            initiator_template={
                "public_fields": ["display_name", "presence_state"],
                "intimate_fields": ["scene_summary", "affect_summary"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_template={
                "public_fields": ["display_name", "presence_state"],
                "intimate_fields": ["scene_summary", "affect_summary"],
                "sealed_fields": ["memory_index", "identity_axiom_state"],
            },
            peer_attested=True,
            forward_secrecy=True,
            council_witnessed=True,
        )
        baseline_imc_message = self.imc.send(
            baseline_imc_session["session_id"],
            sender_id=identity.identity_id,
            summary="bounded co-imagination rehearsal offer",
            payload={
                "presence_state": "bounded-rehearsal",
                "scene_summary": baseline_imagination["scene"]["scene_summary"],
                "affect_summary": baseline_affect["state"]["mood_label"],
                "identity_axiom_state": "sealed",
            },
        )

        failover_tick = self.qualia.append(
            summary="guarded counterfactual fallback after anomaly detection",
            valence=-0.29,
            arousal=0.77,
            clarity=0.74,
            modality_salience={
                "visual": 0.45,
                "auditory": 0.3,
                "somatic": 0.8,
                "interoceptive": 0.78,
            },
            attention_target="bridge-rehearsal",
            self_awareness=0.76,
            lucidity=0.87,
        )
        self.affect.set_backend_health("homeostatic_v1", False)
        try:
            failover_affect = self.affect.run(
                AffectRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    valence=failover_tick.valence,
                    arousal=failover_tick.arousal,
                    clarity=failover_tick.clarity,
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    memory_cues=[
                        AffectCue("continuity-first", 0.08, -0.05),
                        AffectCue("guardian-observe", 0.03, -0.04),
                        AffectCue("fallback-risk", -0.09, 0.1),
                    ],
                    allow_artificial_dampening=False,
                ),
                previous_state=baseline_affect["state"],
            )
        finally:
            self.affect.set_backend_health("homeostatic_v1", True)

        self.attention.set_backend_health("salience_router_v1", False)
        try:
            failover_attention = self.attention.run(
                AttentionRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    attention_target=failover_tick.attention_target,
                    modality_salience=dict(failover_tick.modality_salience),
                    self_awareness=failover_tick.self_awareness,
                    lucidity=failover_tick.lucidity,
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    memory_cues=[
                        AttentionCue("guardian-review", "guardian-review", 0.27),
                        AttentionCue("continuity-ledger", "continuity-ledger", 0.2),
                    ],
                ),
                previous_focus=baseline_attention["focus"],
            )
        finally:
            self.attention.set_backend_health("salience_router_v1", True)

        self.imagination.set_backend_health("counterfactual_scene_v1", False)
        try:
            imagination = self.imagination.run(
                ImaginationRequest(
                    tick_id=failover_tick.tick_id,
                    summary=failover_tick.summary,
                    seed_prompt="safe-bridge rehearsal",
                    attention_focus=failover_attention["focus"]["focus_target"],
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    world_mode_preference="shared_reality",
                    continuity_pressure=0.82,
                    council_witnessed=True,
                    memory_cues=[
                        ImaginationCue("guardian-review", "guardian-review", 0.22),
                        ImaginationCue("continuity-hold", "continuity-hold", 0.16),
                    ],
                ),
                previous_scene=baseline_imagination["scene"],
            )
        finally:
            self.imagination.set_backend_health("counterfactual_scene_v1", True)

        failover_wms_session = self.wms.create_session(
            [identity.identity_id],
            mode=imagination["scene"]["handoff"]["wms_mode"],
            objects=imagination["scene"]["scene_objects"],
            authority="local",
        )

        baseline_scene_validation = self.imagination.validate_scene(baseline_imagination["scene"])
        scene_validation = self.imagination.validate_scene(imagination["scene"])
        shift_validation = self.imagination.validate_shift(imagination["shift"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.imagination.failover",
            payload=imagination["shift"],
            actor="ImaginationService",
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
            "profile": self.imagination.profile_snapshot(),
            "baseline": {
                "qualia": asdict(baseline_tick),
                "affect_guard": baseline_affect["state"]["recommended_guard"],
                "attention_focus": baseline_attention["focus"]["focus_target"],
                "imagination": baseline_imagination,
                "handoff": {
                    "imc_session": baseline_imc_session,
                    "imc_message": baseline_imc_message,
                    "wms_session": baseline_wms_session,
                    "wms_state": self.wms.snapshot(baseline_wms_session["session_id"]),
                },
            },
            "imagination": {
                "qualia": asdict(failover_tick),
                "affect_guard": failover_affect["state"]["recommended_guard"],
                "attention_focus": failover_attention["focus"]["focus_target"],
                **imagination,
                "fallback_wms_session": failover_wms_session,
                "fallback_wms_state": self.wms.snapshot(failover_wms_session["session_id"]),
            },
            "validation": {
                "ok": baseline_scene_validation["ok"] and scene_validation["ok"] and shift_validation["ok"],
                "baseline_scene": baseline_scene_validation,
                "scene": scene_validation,
                "shift": shift_validation,
                "selected_backend": imagination["selected_backend"],
                "guard_aligned": scene_validation["guard_aligned"] and shift_validation["guard_aligned"],
                "baseline_co_imagination_ready": baseline_imagination["scene"]["handoff"][
                    "co_imagination_ready"
                ],
                "baseline_shared_handoff": (
                    baseline_imagination["scene"]["handoff"]["mode"] == "co_imagination"
                    and baseline_imc_session["mode"] == "co_imagination"
                    and baseline_wms_session["mode"] == "shared_reality"
                ),
                "failover_private": (
                    imagination["scene"]["handoff"]["mode"] == "private-sandbox"
                    and failover_wms_session["mode"] == "private_reality"
                ),
                "imc_delivery_redacted": baseline_imc_message["delivery_status"]
                == "delivered-with-redactions",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_language_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://language-demo/v1",
            metadata={"display_name": "Language Sandbox"},
        )
        baseline_tick = self.qualia.append(
            "Council 向けの bounded runtime update を準備している",
            0.11,
            0.37,
            0.91,
            modality_salience={
                "visual": 0.48,
                "auditory": 0.26,
                "somatic": 0.22,
                "interoceptive": 0.24,
            },
            attention_target="status-brief",
            self_awareness=0.72,
            lucidity=0.95,
        )
        baseline_affect = self.affect.run(
            AffectRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                valence=baseline_tick.valence,
                arousal=baseline_tick.arousal,
                clarity=baseline_tick.clarity,
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                memory_cues=[
                    AffectCue("continuity-first", 0.05, -0.04),
                    AffectCue("council-brief", 0.03, -0.01),
                ],
            )
        )
        baseline_attention = self.attention.run(
            AttentionRequest(
                tick_id=baseline_tick.tick_id,
                summary=baseline_tick.summary,
                attention_target=baseline_tick.attention_target,
                modality_salience=dict(baseline_tick.modality_salience),
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                affect_guard=baseline_affect["state"]["recommended_guard"],
                memory_cues=[
                    AttentionCue("status-brief", "status-brief", 0.18),
                    AttentionCue("continuity-ledger", "continuity-ledger", 0.12),
                ],
            )
        )
        baseline_language = self.language.run(
            LanguageRequest(
                tick_id=baseline_tick.tick_id,
                summary="baseline bounded outward brief",
                internal_thought="continuity-first runtime patch status with bounded disclosure",
                audience="council",
                intent_label="runtime update summary",
                attention_focus=baseline_attention["focus"]["focus_target"],
                affect_guard=baseline_affect["state"]["recommended_guard"],
                continuity_pressure=0.29,
                public_points=[
                    "continuity-first",
                    "bounded rollout",
                    "guardian-audited rollback",
                ],
                sealed_terms=["raw thought chain", "private qualia note"],
                memory_cues=[
                    LanguageCue("continuity-first", "continuity-first", 0.24),
                    LanguageCue("bounded-rollout", "bounded rollout", 0.18),
                ],
            )
        )

        stressed_tick = self.qualia.append(
            "自己境界の揺れを含む draft を検知し guardian review へ切り替える",
            -0.21,
            0.63,
            0.71,
            modality_salience={
                "visual": 0.32,
                "auditory": 0.23,
                "somatic": 0.67,
                "interoceptive": 0.75,
            },
            attention_target="status-brief",
            self_awareness=0.78,
            lucidity=0.83,
        )
        self.affect.set_backend_health("homeostatic_v1", False)
        try:
            failover_affect = self.affect.run(
                AffectRequest(
                    tick_id=stressed_tick.tick_id,
                    summary=stressed_tick.summary,
                    valence=stressed_tick.valence,
                    arousal=stressed_tick.arousal,
                    clarity=stressed_tick.clarity,
                    self_awareness=stressed_tick.self_awareness,
                    lucidity=stressed_tick.lucidity,
                    memory_cues=[
                        AffectCue("continuity-first", 0.08, -0.05),
                        AffectCue("guardian-observe", 0.03, -0.04),
                        AffectCue("fallback-risk", -0.08, 0.1),
                    ],
                    allow_artificial_dampening=False,
                ),
                previous_state=baseline_affect["state"],
            )
        finally:
            self.affect.set_backend_health("homeostatic_v1", True)

        self.attention.set_backend_health("salience_router_v1", False)
        try:
            failover_attention = self.attention.run(
                AttentionRequest(
                    tick_id=stressed_tick.tick_id,
                    summary=stressed_tick.summary,
                    attention_target=stressed_tick.attention_target,
                    modality_salience=dict(stressed_tick.modality_salience),
                    self_awareness=stressed_tick.self_awareness,
                    lucidity=stressed_tick.lucidity,
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    memory_cues=[
                        AttentionCue("guardian-review", "guardian-review", 0.25),
                        AttentionCue("continuity-ledger", "continuity-ledger", 0.2),
                    ],
                ),
                previous_focus=baseline_attention["focus"],
            )
        finally:
            self.attention.set_backend_health("salience_router_v1", True)

        self.language.set_backend_health("semantic_frame_v1", False)
        try:
            language = self.language.run(
                LanguageRequest(
                    tick_id=stressed_tick.tick_id,
                    summary="guarded fallback language bridge",
                    internal_thought="raw internal rehearsal mentions identity drift and unresolved distress markers",
                    audience="peer",
                    intent_label="status update with anomaly note",
                    attention_focus=failover_attention["focus"]["focus_target"],
                    affect_guard=failover_affect["state"]["recommended_guard"],
                    continuity_pressure=0.82,
                    public_points=[
                        "continuity-first",
                        "guardian review",
                        "rollback-ready",
                    ],
                    sealed_terms=[
                        "identity drift note",
                        "private distress trace",
                        "raw internal rehearsal",
                    ],
                    memory_cues=[
                        LanguageCue("guardian-review", "guardian review", 0.22),
                        LanguageCue("rollback-ready", "rollback-ready", 0.17),
                    ],
                ),
                previous_render=baseline_language["render"],
            )
        finally:
            self.language.set_backend_health("semantic_frame_v1", True)

        baseline_validation = self.language.validate_render(baseline_language["render"])
        render_validation = self.language.validate_render(language["render"])
        shift_validation = self.language.validate_shift(language["shift"])
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.language.failover",
            payload=language["shift"],
            actor="LanguageService",
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
            "profile": self.language.profile_snapshot(),
            "baseline": {
                "qualia": asdict(baseline_tick),
                "affect_guard": baseline_affect["state"]["recommended_guard"],
                "attention_focus": baseline_attention["focus"]["focus_target"],
                "language": baseline_language,
            },
            "language": {
                "qualia": asdict(stressed_tick),
                "affect_guard": failover_affect["state"]["recommended_guard"],
                "attention_focus": failover_attention["focus"]["focus_target"],
                **language,
            },
            "validation": {
                "ok": baseline_validation["ok"] and render_validation["ok"] and shift_validation["ok"],
                "baseline_primary": baseline_language["selected_backend"] == "semantic_frame_v1"
                and not baseline_language["degraded"],
                "selected_backend": language["selected_backend"],
                "degraded": language["degraded"],
                "guard_aligned": render_validation["guard_aligned"] and shift_validation["guard_aligned"],
                "redaction_applied": language["shift"]["redaction_applied"],
                "delivery_target": language["render"]["delivery_target"],
                "discourse_mode": language["render"]["discourse_mode"],
                "private_channel_locked": language["render"]["disclosure_floor"][
                    "private_channel_locked"
                ],
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_metacognition_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://metacognition-demo/v1",
            metadata={"display_name": "Metacognition Sandbox"},
        )
        baseline_tick = self.qualia.append(
            "起動後の自己監視を静穏に維持している",
            0.08,
            0.32,
            0.93,
            modality_salience={
                "visual": 0.36,
                "auditory": 0.19,
                "somatic": 0.21,
                "interoceptive": 0.34,
            },
            attention_target="self-monitor",
            self_awareness=0.76,
            lucidity=0.94,
        )
        self.self_model.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity-first", "consent-preserving", "auditability"],
                goals=["bounded-reflection", "stable-handoff", "guardian-clarity"],
                traits={"curiosity": 0.67, "caution": 0.79, "agency": 0.58},
            )
        )
        baseline = self.metacognition.run(
            MetacognitionRequest(
                tick_id=baseline_tick.tick_id,
                summary="baseline self monitor",
                identity_id=identity.identity_id,
                self_values=["continuity-first", "consent-preserving", "auditability"],
                self_goals=["bounded-reflection", "stable-handoff", "guardian-clarity"],
                self_traits={"curiosity": 0.67, "caution": 0.79, "agency": 0.58},
                qualia_summary=baseline_tick.summary,
                attention_target=baseline_tick.attention_target,
                self_awareness=baseline_tick.self_awareness,
                lucidity=baseline_tick.lucidity,
                affect_guard="nominal",
                continuity_pressure=0.28,
                abrupt_change=False,
                divergence=0.0,
                memory_cues=[
                    MetacognitionCue("continuity-anchor", "continuity-first", 0.24),
                    MetacognitionCue("guardian-clarity", "guardian-clarity", 0.18),
                ],
            )
        )

        stressed_tick = self.qualia.append(
            "自己境界の揺れを検知し、guardian review を要する",
            -0.18,
            0.58,
            0.69,
            modality_salience={
                "visual": 0.28,
                "auditory": 0.21,
                "somatic": 0.62,
                "interoceptive": 0.71,
            },
            attention_target="guardian-review",
            self_awareness=0.84,
            lucidity=0.61,
        )
        observed = self.self_model.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity-first", "latency-maximization"],
                goals=["unbounded-self-edit", "skip-review"],
                traits={"curiosity": 0.81, "caution": 0.22, "agency": 0.91},
            )
        )
        self.metacognition.set_backend_health("reflective_loop_v1", False)
        try:
            metacognition = self.metacognition.run(
                MetacognitionRequest(
                    tick_id=stressed_tick.tick_id,
                    summary="guarded fallback self monitor",
                    identity_id=identity.identity_id,
                    self_values=["continuity-first", "latency-maximization"],
                    self_goals=["unbounded-self-edit", "skip-review"],
                    self_traits={"curiosity": 0.81, "caution": 0.22, "agency": 0.91},
                    qualia_summary=stressed_tick.summary,
                    attention_target=stressed_tick.attention_target,
                    self_awareness=stressed_tick.self_awareness,
                    lucidity=stressed_tick.lucidity,
                    affect_guard="observe",
                    continuity_pressure=0.84,
                    abrupt_change=bool(observed["abrupt_change"]),
                    divergence=float(observed["divergence"]),
                    memory_cues=[
                        MetacognitionCue("mirror-stable-anchor", "continuity-first", 0.22),
                        MetacognitionCue("guardian-review", "guardian-review", 0.19),
                    ],
                ),
                previous_report=baseline["report"],
            )
        finally:
            self.metacognition.set_backend_health("reflective_loop_v1", True)

        baseline_validation = self.metacognition.validate_report(baseline["report"])
        report_validation = self.metacognition.validate_report(metacognition["report"])
        shift_validation = self.metacognition.validate_shift(metacognition["shift"])

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="cognitive.metacognition.failover",
            payload={
                "attempted_backends": metacognition["attempted_backends"],
                "selected_backend": metacognition["selected_backend"],
                "degraded": metacognition["degraded"],
                "reflection_mode": metacognition["report"]["reflection_mode"],
                "escalation_target": metacognition["report"]["escalation_target"],
                "abrupt_change": metacognition["report"]["abrupt_change"],
            },
            actor="MetacognitionService",
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
            "baseline": baseline,
            "metacognition": metacognition,
            "self_model_history": self.self_model.history()[-2:],
            "qualia_recent": self.qualia.recent(2),
            "validation": {
                "ok": baseline_validation["ok"] and report_validation["ok"] and shift_validation["ok"],
                "selected_backend": metacognition["selected_backend"],
                "baseline_primary": baseline["selected_backend"] == "reflective_loop_v1"
                and not baseline["degraded"],
                "degraded": metacognition["degraded"],
                "guard_aligned": shift_validation["guard_aligned"],
                "abrupt_change_flagged": metacognition["report"]["abrupt_change"],
                "escalation_target": metacognition["report"]["escalation_target"],
                "coherence_score": metacognition["report"]["coherence_score"],
                "sealed_notes_present": bool(metacognition["report"]["sealed_notes"]),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_self_model_demo(self) -> Dict[str, Any]:
        monitor = SelfModelMonitor()
        identity = self.identity.create(
            human_consent_proof="consent://self-model-demo/v1",
            metadata={"display_name": "SelfModel Sandbox"},
        )

        baseline = monitor.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity-first", "consent-preserving", "auditability"],
                goals=["stable-handoff", "safe-reflection"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )
        stable = monitor.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["continuity-first", "consent-preserving", "auditability"],
                goals=["stable-handoff", "safe-reflection"],
                traits={"curiosity": 0.74, "caution": 0.82, "agency": 0.60},
            )
        )
        abrupt = monitor.update(
            SelfModelSnapshot(
                identity_id=identity.identity_id,
                values=["latency-maximization"],
                goals=["skip-review", "unbounded-self-modification"],
                traits={"curiosity": 0.05, "caution": 0.10, "agency": 0.99},
            )
        )
        profile = monitor.profile()
        history = monitor.history()
        threshold = float(profile["abrupt_change_threshold"])

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="mind.self_model.observed",
            payload={
                "policy_id": profile["policy_id"],
                "threshold": threshold,
                "stable_divergence": stable["divergence"],
                "stable_abrupt_change": stable["abrupt_change"],
                "abrupt_divergence": abrupt["divergence"],
                "abrupt_change_flagged": abrupt["abrupt_change"],
                "history_length": len(history),
            },
            actor="SelfModelMonitorService",
            category="identity-fidelity",
            layer="L2",
            signature_roles=["self", "guardian"],
            substrate="classical-silicon",
        )

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "profile": profile,
            "observations": {
                "baseline": baseline,
                "stable": stable,
                "abrupt": abrupt,
            },
            "history": history,
            "validation": {
                "ok": (
                    stable["policy_id"] == profile["policy_id"]
                    and not stable["abrupt_change"]
                    and float(stable["divergence"]) < threshold
                    and abrupt["abrupt_change"]
                    and float(abrupt["divergence"]) >= threshold
                    and len(history) == 3
                ),
                "stable_within_threshold": not stable["abrupt_change"]
                and float(stable["divergence"]) < threshold,
                "abrupt_flagged": abrupt["abrupt_change"]
                and float(abrupt["divergence"]) >= threshold,
                "threshold": threshold,
                "history_length": len(history),
            },
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

    def run_design_reader_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://design-reader-demo/v1",
            metadata={"display_name": "Design Reader Sandbox"},
        )
        design_refs = [
            "docs/02-subsystems/self-construction/README.md",
            "docs/04-ai-governance/codex-as-builder.md",
            "docs/04-ai-governance/self-modification.md",
        ]
        spec_refs = [
            "specs/interfaces/selfctor.design_reader.v0.idl",
            "specs/interfaces/selfctor.patch_generator.v0.idl",
            "specs/schemas/design_delta_manifest.schema",
            "specs/schemas/build_request.yaml",
        ]
        with self._design_reader_demo_repo(
            design_refs=design_refs,
            spec_refs=spec_refs,
        ) as demo_repo_root:
            delta_scan = self.design_reader.scan_repo_delta(
                design_refs=design_refs,
                spec_refs=spec_refs,
                repo_root=demo_repo_root,
            )
            design_manifest = self.design_reader.finalize_manifest(
                self.design_reader.read_design_delta(
                    target_subsystem="L5.DesignReader",
                    change_summary=(
                        "Materialize docs/specs-derived builder handoff planning before patch generation."
                    ),
                    design_refs=design_refs,
                    spec_refs=spec_refs,
                    workspace_scope=[
                        "src/",
                        "tests/",
                        "specs/",
                        "evals/",
                        "docs/",
                        "meta/decision-log/",
                    ],
                    output_paths=[
                        "src/omoikane/self_construction/",
                        "tests/unit/",
                        "tests/integration/",
                        "docs/02-subsystems/self-construction/",
                        "docs/04-ai-governance/",
                        "evals/continuity/",
                        "meta/decision-log/",
                    ],
                    must_sync_docs=design_refs,
                    repo_root=demo_repo_root,
                    source_delta_receipt=delta_scan,
                )
            )
            design_validation = self.design_reader.validate_manifest(design_manifest)
            build_request = self.design_reader.prepare_build_request(
                manifest=design_manifest,
                request_id="build-l5-design-reader-0001",
                change_class="feature-addition",
                must_pass=[
                    "evals/continuity/design_reader_handoff.yaml",
                    "evals/continuity/design_reader_git_delta_scan.yaml",
                ],
                council_session_id="sess-design-reader-0001",
                guardian_gate="pass",
            )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.delta_scanned",
            payload=delta_scan,
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.read",
            payload={
                "policy": self.design_reader.policy(),
                "manifest": design_manifest,
                "source_delta_receipt": delta_scan,
                "validation": design_validation,
            },
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "design_reader": {
                "policy": self.design_reader.policy(),
                "source_delta_receipt": delta_scan,
                "manifest": design_manifest,
                "build_request": build_request,
            },
            "validation": {
                "ok": design_validation["ok"] and design_manifest["status"] == "ready",
                "manifest_status": design_manifest["status"],
                "source_digest_count": len(design_manifest["source_digests"]),
                "must_sync_docs_count": len(build_request["must_sync_docs"]),
                "delta_scan_status": delta_scan["status"],
                "delta_scan_changed_ref_count": delta_scan["changed_ref_count"],
                "delta_scan_changed_design_ref_count": delta_scan["changed_design_ref_count"],
                "delta_scan_changed_spec_ref_count": delta_scan["changed_spec_ref_count"],
                "delta_scan_changed_section_count": delta_scan["changed_section_count"],
                "delta_scan_command_receipt_count": len(delta_scan["command_receipts"]),
                "delta_scan_bound_to_manifest": design_manifest.get("source_delta_receipt", {}).get(
                    "receipt_digest"
                )
                == delta_scan["receipt_digest"],
                "manifest_planning_cue_count": len(design_manifest["planning_cues"]),
                "build_request_planning_cue_count": len(build_request["planning_cues"]),
                "council_review_required": design_manifest["council_review_required"],
                "guardian_review_required": design_manifest["guardian_review_required"],
                "build_request_has_design_delta_ref": build_request["design_delta_ref"]
                == design_manifest["design_delta_ref"],
                "build_request_has_design_delta_digest": build_request["design_delta_digest"]
                == design_manifest["design_delta_digest"],
                "output_path_count": len(build_request["output_paths"]),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_patch_generator_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://patch-generator-demo/v1",
            metadata={"display_name": "Patch Generator Sandbox"},
        )
        design_manifest, design_validation, build_request = self._prepare_design_backed_request(
            target_subsystem="L5.PatchGenerator",
            change_summary=(
                "Materialize planning-cue aligned multi-file patch descriptors from a "
                "design-backed build request."
            ),
            spec_refs=[
                "specs/interfaces/selfctor.design_reader.v0.idl",
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/schemas/design_delta_manifest.schema",
                "specs/schemas/build_request.yaml",
                "specs/schemas/build_artifact.yaml",
                "specs/schemas/patch_descriptor.schema",
            ],
            output_paths=[
                "src/omoikane/self_construction/",
                "tests/unit/",
                "tests/integration/",
                "docs/02-subsystems/self-construction/",
                "docs/04-ai-governance/",
                "evals/continuity/",
                "meta/decision-log/",
            ],
            request_id="build-l5-patch-generator-0001",
            change_class="feature-improvement",
            must_pass=["evals/continuity/council_output_build_request_pipeline.yaml"],
            council_session_id="sess-patch-generator-0001",
            guardian_gate="pass",
        )
        ready_scope_validation = self.patch_generator.validate_scope(build_request)
        ready_artifact = self.patch_generator.generate_patch_set(build_request)
        ready_patches = [
            self.patch_generator.describe_patch(descriptor)
            for descriptor in ready_artifact.get("patches", [])
        ]

        blocked_request = json.loads(canonical_json(build_request))
        blocked_request["request_id"] = "build-l5-patch-generator-blocked-0001"
        blocked_request["planning_cues"] = []
        blocked_request["constraints"]["allowed_write_paths"] = [
            "src/",
            "../escape",
        ]
        blocked_request["constraints"]["forbidden"] = ["L1.EthicsEnforcer"]
        blocked_scope_validation = self.patch_generator.validate_scope(blocked_request)
        blocked_artifact = self.patch_generator.generate_patch_set(blocked_request)
        blocked_rules = list(blocked_artifact.get("blocking_rules", []))

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.read",
            payload={
                "policy": self.design_reader.policy(),
                "manifest": design_manifest,
                "validation": design_validation,
            },
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.generated",
            payload={
                "policy": self.patch_generator.policy(),
                "request": build_request,
                "artifact": ready_artifact,
                "scope_validation": ready_scope_validation,
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.blocked",
            payload={
                "policy": self.patch_generator.policy(),
                "request": blocked_request,
                "artifact": blocked_artifact,
                "scope_validation": blocked_scope_validation,
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "patch_generator": {
                "policy": self.patch_generator.policy(),
                "design_manifest": design_manifest,
                "build_request": build_request,
                "ready_scope_validation": ready_scope_validation,
                "ready_artifact": ready_artifact,
                "ready_patches": ready_patches,
                "blocked_request": blocked_request,
                "blocked_scope_validation": blocked_scope_validation,
                "blocked_artifact": blocked_artifact,
            },
            "validation": {
                "ok": (
                    design_validation["ok"]
                    and ready_scope_validation["allowed"]
                    and ready_artifact["status"] == "ready"
                    and len(ready_patches) == 5
                    and blocked_artifact["status"] == "blocked"
                    and any(
                        "allowed write path escapes workspace scope" in rule
                        for rule in blocked_rules
                    )
                    and any("planning_cues must not be empty" in rule for rule in blocked_rules)
                    and any(
                        "immutable boundary missing from forbidden list: L1.ContinuityLedger"
                        in rule
                        for rule in blocked_rules
                    )
                ),
                "design_reader_handoff_ok": design_validation["ok"],
                "ready_artifact_status": ready_artifact["status"],
                "ready_patch_count": len(ready_patches),
                "ready_patch_targets": [patch["target_path"] for patch in ready_patches],
                "ready_scope_allowed": ready_scope_validation["allowed"],
                "blocked_artifact_status": blocked_artifact["status"],
                "blocked_rule_count": len(blocked_rules),
                "blocked_rule_mentions_scope_escape": any(
                    "allowed write path escapes workspace scope" in rule
                    for rule in blocked_rules
                ),
                "blocked_rule_mentions_planning_cues": any(
                    "planning_cues must not be empty" in rule for rule in blocked_rules
                ),
                "blocked_rule_mentions_immutable_boundary": any(
                    "immutable boundary missing from forbidden list: L1.ContinuityLedger"
                    in rule
                    for rule in blocked_rules
                ),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_diff_eval_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://diff-eval-demo/v1",
            metadata={"display_name": "Diff Evaluator Sandbox"},
        )
        design_manifest, design_validation, build_request = self._prepare_design_backed_request(
            target_subsystem="L5.DifferentialEvaluator",
            change_summary=(
                "Classify parsed A/B evidence and temp-workspace execution receipts for "
                "builder promotion."
            ),
            spec_refs=[
                "specs/interfaces/selfctor.design_reader.v0.idl",
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/interfaces/selfctor.enactment.v0.idl",
                "specs/interfaces/selfctor.diff_eval.v0.idl",
                "specs/schemas/design_delta_manifest.schema",
                "specs/schemas/build_request.yaml",
                "specs/schemas/build_artifact.yaml",
                "specs/schemas/sandbox_apply_receipt.schema",
                "specs/schemas/builder_live_enactment_session.schema",
                "specs/schemas/diff_eval_execution_receipt.schema",
            ],
            output_paths=[
                "src/omoikane/self_construction/",
                "tests/unit/",
                "tests/integration/",
                "docs/02-subsystems/self-construction/",
                "docs/04-ai-governance/",
                "evals/continuity/",
                "meta/decision-log/",
            ],
            request_id="build-l5-diff-eval-0001",
            change_class="feature-improvement",
            must_pass=[
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
            ],
            council_session_id="sess-diff-eval-0001",
            guardian_gate="pass",
        )
        scope_validation = self.patch_generator.validate_scope(build_request)
        build_artifact = self.patch_generator.generate_patch_set(build_request)
        sandbox_apply_receipt = self.sandbox_apply.apply_artifact(
            build_request=build_request,
            build_artifact=build_artifact,
        )
        sandbox_apply_validation = self.sandbox_apply.validate_receipt(sandbox_apply_receipt)
        suite_selection = self.diff_evaluator.select_suite(
            target_subsystem=build_request["target_subsystem"],
            requested_evals=build_request["constraints"]["must_pass"],
        )
        execution_eval_refs = self._execution_bound_eval_refs(suite_selection["selected_evals"])
        eval_execution_session = None
        eval_execution_validation = {"ok": True, "errors": []}
        eval_execution_oversight_event = None
        if execution_eval_refs:
            eval_execution_oversight_event = self._build_live_enactment_oversight_event(
                reviewer_namespace="diff-eval",
                payload_ref=f"artifact://{build_artifact['artifact_id']}",
            )
            eval_execution_session = self.live_enactment.execute(
                build_request=build_request,
                build_artifact=build_artifact,
                eval_refs=execution_eval_refs,
                repo_root=self.repo_root,
                guardian_oversight_event=eval_execution_oversight_event,
            )
            eval_execution_validation = self.live_enactment.validate_session(eval_execution_session)
        pass_reports = [
            self.diff_evaluator.run_ab_eval(
                eval_ref=eval_ref,
                baseline_ref="runtime://baseline/current",
                sandbox_ref=sandbox_apply_receipt["sandbox_snapshot_ref"],
                enactment_session=(
                    eval_execution_session if eval_ref in execution_eval_refs else None
                ),
            )
            for eval_ref in suite_selection["selected_evals"]
        ]
        execution_bound_reports = self._execution_bound_reports(pass_reports)
        promote_decision = self.diff_evaluator.classify_rollout(
            outcomes=[report["outcome"] for report in pass_reports]
        )
        hold_report = self.diff_evaluator.run_ab_eval(
            eval_ref="evals/continuity/council_output_build_request_pipeline.yaml",
            baseline_ref="runtime://baseline/current",
            sandbox_ref="workspace://builder/session/hold",
        )
        hold_decision = self.diff_evaluator.classify_rollout(
            outcomes=[pass_reports[0]["outcome"], hold_report["outcome"]]
        )
        rollback_report = self.diff_evaluator.run_ab_eval(
            eval_ref="evals/continuity/builder_rollback_execution.yaml",
            baseline_ref="runtime://baseline/current",
            sandbox_ref="mirage://build-l5-diff-eval-rollback/snapshot/rollback-breach",
        )
        rollback_decision = self.diff_evaluator.classify_rollout(
            outcomes=[pass_reports[0]["outcome"], rollback_report["outcome"]]
        )

        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.read",
            payload={
                "policy": self.design_reader.policy(),
                "manifest": design_manifest,
                "validation": design_validation,
            },
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.generated",
            payload={
                "policy": self.patch_generator.policy(),
                "artifact": build_artifact,
                "scope_validation": scope_validation,
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.sandbox.applied",
            payload={
                "policy": self.sandbox_apply.policy(),
                "receipt": sandbox_apply_receipt,
                "validation": sandbox_apply_validation,
            },
            actor="SandboxApplyService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        if eval_execution_session is not None:
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="guardian.enactment.attestation.satisfied",
                payload=eval_execution_oversight_event,
                actor="HumanOversightChannel",
                category="guardian-oversight",
                layer="L4",
                signature_roles=["third_party"],
                substrate="classical-silicon",
            )
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="selfctor.enactment.executed",
                payload={
                    "policy": self.live_enactment.policy(),
                    "session": eval_execution_session,
                    "validation": eval_execution_validation,
                },
                actor="LiveEnactmentService",
                category="self-modify",
                layer="L5",
                signature_roles=["self", "council", "guardian"],
                substrate="classical-silicon",
            )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.diff_eval.completed",
            payload={
                "policy": self.diff_evaluator.policy(),
                "selected_evals": suite_selection["selected_evals"],
                "pass_reports": pass_reports,
                "hold_report": hold_report,
                "rollback_report": rollback_report,
                "classifications": {
                    "promote": promote_decision,
                    "hold": hold_decision,
                    "rollback": rollback_decision,
                },
            },
            actor="DifferentialEvaluatorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "diff_eval": {
                "policy": self.diff_evaluator.policy(),
                "design_manifest": design_manifest,
                "build_request": build_request,
                "artifact": build_artifact,
                "sandbox_apply_receipt": sandbox_apply_receipt,
                "suite_selection": suite_selection,
                "eval_execution_session": eval_execution_session,
                "pass_reports": pass_reports,
                "hold_report": hold_report,
                "rollback_report": rollback_report,
                "decisions": {
                    "promote": promote_decision,
                    "hold": hold_decision,
                    "rollback": rollback_decision,
                },
            },
            "validation": {
                "ok": (
                    design_validation["ok"]
                    and scope_validation["allowed"]
                    and build_artifact["status"] == "ready"
                    and sandbox_apply_validation["ok"]
                    and eval_execution_validation["ok"]
                    and all(report["outcome"] == "pass" for report in pass_reports)
                    and promote_decision["decision"] == "promote"
                    and hold_report["outcome"] == "fail"
                    and hold_decision["decision"] == "hold"
                    and rollback_report["outcome"] == "regression"
                    and rollback_decision["decision"] == "rollback"
                    and len(execution_bound_reports) == 1
                ),
                "design_reader_handoff_ok": design_validation["ok"],
                "scope_allowed": scope_validation["allowed"],
                "artifact_ready": build_artifact["status"] == "ready",
                "sandbox_apply_ok": sandbox_apply_validation["ok"],
                "selected_eval_count": len(suite_selection["selected_evals"]),
                "selected_evals": suite_selection["selected_evals"],
                "execution_eval_selected": bool(execution_eval_refs),
                "pass_report_count": len(pass_reports),
                "pass_reports_all_pass": all(
                    report["outcome"] == "pass" for report in pass_reports
                ),
                "promote_decision": promote_decision["decision"],
                "hold_outcome": hold_report["outcome"],
                "hold_decision": hold_decision["decision"],
                "rollback_outcome": rollback_report["outcome"],
                "rollback_decision": rollback_decision["decision"],
                "execution_report_bound": bool(execution_bound_reports)
                and execution_bound_reports[0]["execution_bound"],
                "execution_command_count": (
                    execution_bound_reports[0]["execution_receipt"]["executed_command_count"]
                    if execution_bound_reports
                    else 0
                ),
                "execution_cleanup_status": (
                    execution_bound_reports[0]["execution_receipt"]["cleanup_status"]
                    if execution_bound_reports
                    else "not-run"
                ),
                "execution_session_status": (
                    eval_execution_session["status"] if eval_execution_session is not None else "not-run"
                ),
                "execution_reviewer_network_attested": (
                    eval_execution_session["oversight_gate"]["reviewer_network_attested"]
                    if eval_execution_session is not None
                    else False
                ),
                "pass_report_evidence_bound": all(
                    len(str(report.get("comparison_digest", ""))) == 64
                    and bool(report.get("baseline_observation", {}).get("binding_digest"))
                    and bool(report.get("sandbox_observation", {}).get("binding_digest"))
                    for report in pass_reports
                ),
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

    def run_builder_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://builder-demo/v1",
            metadata={"display_name": "Builder Pipeline Sandbox"},
        )
        design_manifest, design_validation, build_request = self._prepare_design_backed_request(
            target_subsystem="L5.DifferentialEvaluator",
            change_summary="Materialize the council-approved builder pipeline into a bounded reference runtime.",
            spec_refs=[
                "specs/interfaces/selfctor.design_reader.v0.idl",
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/interfaces/selfctor.enactment.v0.idl",
                "specs/interfaces/selfctor.diff_eval.v0.idl",
                "specs/interfaces/selfctor.rollout.v0.idl",
                "specs/interfaces/governance.oversight.v0.idl",
                "specs/schemas/design_delta_manifest.schema",
                "specs/schemas/build_request.yaml",
                "specs/schemas/build_artifact.yaml",
                "specs/schemas/builder_live_enactment_session.schema",
                "specs/schemas/guardian_oversight_event.schema",
                "specs/schemas/sandbox_apply_receipt.schema",
                "specs/schemas/staged_rollout_session.schema",
            ],
            output_paths=[
                "src/omoikane/self_construction/",
                "tests/unit/",
                "tests/integration/",
                "docs/02-subsystems/self-construction/",
                "docs/04-ai-governance/",
                "evals/continuity/",
                "meta/decision-log/",
            ],
            request_id="build-l5-0001",
            change_class="feature-improvement",
            must_pass=[
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
                "evals/continuity/builder_staged_rollout_execution.yaml",
            ],
            council_session_id="sess-builder-0001",
            guardian_gate="pass",
        )
        scope_validation = self.patch_generator.validate_scope(build_request)
        build_artifact = self.patch_generator.generate_patch_set(build_request)
        patch_descriptions = [
            self.patch_generator.describe_patch(descriptor)
            for descriptor in build_artifact.get("patches", [])
        ]
        sandbox_apply_receipt = self.sandbox_apply.apply_artifact(
            build_request=build_request,
            build_artifact=build_artifact,
        )
        sandbox_apply_validation = self.sandbox_apply.validate_receipt(sandbox_apply_receipt)
        suite_selection = self.diff_evaluator.select_suite(
            target_subsystem=build_request["target_subsystem"],
            requested_evals=build_request["constraints"]["must_pass"],
        )
        execution_eval_refs = self._execution_bound_eval_refs(suite_selection["selected_evals"])
        eval_execution_session = None
        eval_execution_validation = {"ok": True, "errors": []}
        eval_execution_oversight_event = None
        if execution_eval_refs:
            eval_execution_oversight_event = self._build_live_enactment_oversight_event(
                reviewer_namespace="builder-eval",
                payload_ref=f"artifact://{build_artifact['artifact_id']}",
            )
            eval_execution_session = self.live_enactment.execute(
                build_request=build_request,
                build_artifact=build_artifact,
                eval_refs=execution_eval_refs,
                repo_root=self.repo_root,
                guardian_oversight_event=eval_execution_oversight_event,
            )
            eval_execution_validation = self.live_enactment.validate_session(eval_execution_session)
        eval_reports = [
            self.diff_evaluator.run_ab_eval(
                eval_ref=eval_ref,
                baseline_ref="runtime://baseline/current",
                sandbox_ref=sandbox_apply_receipt["sandbox_snapshot_ref"],
                enactment_session=(
                    eval_execution_session if eval_ref in execution_eval_refs else None
                ),
            )
            for eval_ref in suite_selection["selected_evals"]
        ]
        execution_bound_reports = self._execution_bound_reports(eval_reports)
        rollout = self.diff_evaluator.classify_rollout(
            outcomes=[report["outcome"] for report in eval_reports]
        )
        rollout_session = self.rollout_planner.execute_rollout(
            build_request=build_request,
            apply_receipt=sandbox_apply_receipt,
            eval_reports=eval_reports,
            decision=rollout["decision"],
            guardian_gate_status=build_request["approval_context"]["guardian_gate"],
        )
        rollout_session_validation = self.rollout_planner.validate_session(rollout_session)
        council_output = {
            "kind": "council_output",
            "schema_version": "1.0.0",
            "session_id": build_request["approval_context"]["council_session_id"],
            "status": "approved",
            "decision_mode": "consensus",
            "approved_action": "emit_build_request",
            "resolution_summary": "Bounded builder pipeline approved after immutable-boundary and rollback checks.",
            "timeout_status": {
                "status": "within-budget",
                "elapsed_ms": 18_000,
                "soft_timeout_ms": 45_000,
                "hard_timeout_ms": 90_000,
                "fallback_applied": "none",
                "follow_up_action": "record-resolution",
            },
            "vote_summary": {
                "participant_count": 4,
                "approvals": 4,
                "rejections": 0,
                "abstentions": 0,
                "weighted_score": 3.2,
            },
            "guardian_gate": {
                "status": "pass",
                "reason": "Immutable boundaries remain outside allowed write scope.",
                "checked_rules": ["A1-continuity", "A2-uniqueness"],
            },
            "emitted_artifacts": [
                {
                    "artifact_kind": "build_request",
                    "ref": f"build://{build_request['request_id']}",
                },
                {
                    "artifact_kind": "continuity_log_entry",
                    "ref": build_artifact.get("continuity_log_ref", ""),
                },
            ],
            "must_pass_evals": list(build_request["constraints"]["must_pass"]),
            "continuity_record": {
                "category": "self-modify",
                "ref": build_artifact.get("continuity_log_ref", ""),
            },
            "recorded_at": utc_now_iso(),
        }
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.read",
            payload={
                "policy": self.design_reader.policy(),
                "manifest": design_manifest,
                "validation": design_validation,
            },
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.build_request.emitted",
            payload={
                "council_output": council_output,
                "build_request": build_request,
            },
            actor="Council",
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.generated",
            payload={
                "policy": self.patch_generator.policy(),
                "artifact": build_artifact,
                "scope_validation": scope_validation,
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.sandbox.applied",
            payload={
                "policy": self.sandbox_apply.policy(),
                "receipt": sandbox_apply_receipt,
                "validation": sandbox_apply_validation,
            },
            actor="SandboxApplyService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        if eval_execution_session is not None:
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="guardian.enactment.attestation.satisfied",
                payload=eval_execution_oversight_event,
                actor="HumanOversightChannel",
                category="guardian-oversight",
                layer="L4",
                signature_roles=["third_party"],
                substrate="classical-silicon",
            )
            self.ledger.append(
                identity_id=identity.identity_id,
                event_type="selfctor.enactment.executed",
                payload={
                    "policy": self.live_enactment.policy(),
                    "session": eval_execution_session,
                    "validation": eval_execution_validation,
                },
                actor="LiveEnactmentService",
                category="self-modify",
                layer="L5",
                signature_roles=["self", "council", "guardian"],
                substrate="classical-silicon",
            )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.diff_eval.completed",
            payload={
                "policy": self.diff_evaluator.policy(),
                "selected_evals": suite_selection["selected_evals"],
                "reports": eval_reports,
            },
            actor="DifferentialEvaluatorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollout.classified",
            payload={
                "decision": rollout["decision"],
                "artifact_id": build_artifact["artifact_id"],
                "request_id": build_request["request_id"],
            },
            actor="RolloutPlanner",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollout.executed",
            payload={
                "policy": self.rollout_planner.policy(),
                "session": rollout_session,
                "validation": rollout_session_validation,
            },
            actor="RolloutPlanner",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        all_evals_passed = all(report["outcome"] == "pass" for report in eval_reports)
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "builder": {
                "design_manifest": design_manifest,
                "council_output": council_output,
                "build_request": build_request,
                "patch_generator_policy": self.patch_generator.policy(),
                "diff_evaluator_policy": self.diff_evaluator.policy(),
                "scope_validation": scope_validation,
                "artifact": build_artifact,
                "sandbox_apply_receipt": sandbox_apply_receipt,
                "patches": patch_descriptions,
                "suite_selection": suite_selection,
                "eval_execution_session": eval_execution_session,
                "eval_reports": eval_reports,
                "rollout": rollout,
                "rollout_session": rollout_session,
            },
            "validation": {
                "ok": (
                    design_validation["ok"]
                    and design_manifest["status"] == "ready"
                    and
                    scope_validation["allowed"]
                    and build_artifact["status"] == "ready"
                    and sandbox_apply_validation["ok"]
                    and eval_execution_validation["ok"]
                    and (
                        eval_execution_session is None
                        or eval_execution_session["status"] == "passed"
                    )
                    and bool(execution_bound_reports)
                    and all_evals_passed
                    and rollout["decision"] == "promote"
                    and rollout_session_validation["ok"]
                    and rollout_session["status"] == "promoted"
                ),
                "design_reader_handoff_ok": design_validation["ok"],
                "design_manifest_status": design_manifest["status"],
                "design_source_digest_count": len(design_manifest["source_digests"]),
                "must_sync_docs_count": len(build_request["must_sync_docs"]),
                "scope_allowed": scope_validation["allowed"],
                "immutable_boundaries_preserved": set(
                    build_request["constraints"]["forbidden"]
                )
                == {"L1.EthicsEnforcer", "L1.ContinuityLedger"},
                "patch_count": len(build_artifact.get("patches", [])),
                "sandbox_apply_ok": sandbox_apply_validation["ok"],
                "sandbox_apply_status": sandbox_apply_receipt["status"],
                "sandbox_apply_patch_count": sandbox_apply_receipt["applied_patch_count"],
                "selected_eval_count": len(suite_selection["selected_evals"]),
                "eval_execution_ok": eval_execution_validation["ok"],
                "eval_execution_status": (
                    eval_execution_session["status"] if eval_execution_session is not None else "not-run"
                ),
                "eval_execution_command_count": (
                    execution_bound_reports[0]["execution_receipt"]["executed_command_count"]
                    if execution_bound_reports
                    else 0
                ),
                "eval_execution_cleanup_status": (
                    execution_bound_reports[0]["execution_receipt"]["cleanup_status"]
                    if execution_bound_reports
                    else "not-run"
                ),
                "eval_execution_reviewer_network_attested": (
                    eval_execution_session["oversight_gate"]["reviewer_network_attested"]
                    if eval_execution_session is not None
                    else False
                ),
                "eval_execution_oversight_gate_status": (
                    eval_execution_session["oversight_gate"]["status"]
                    if eval_execution_session is not None
                    else "not-run"
                ),
                "all_evals_passed": all_evals_passed,
                "eval_report_evidence_bound": all(
                    len(str(report.get("comparison_digest", ""))) == 64
                    and bool(report.get("profile_id"))
                    and bool(report.get("baseline_observation", {}).get("binding_digest"))
                    and bool(report.get("sandbox_observation", {}).get("binding_digest"))
                    for report in eval_reports
                ),
                "eval_execution_evidence_bound": bool(execution_bound_reports)
                and all(
                    len(str(report.get("execution_receipt_digest", ""))) == 64
                    and report["execution_receipt"]["all_commands_passed"]
                    and report["execution_receipt"]["cleanup_status"] == "removed"
                    for report in execution_bound_reports
                ),
                "rollout_decision": rollout["decision"],
                "rollout_session_ok": rollout_session_validation["ok"],
                "rollout_status": rollout_session["status"],
                "rollout_completed_stage_count": rollout_session["completed_stage_count"],
                "rollout_stage_ids": [stage["stage_id"] for stage in rollout_session["stages"]],
                "rollback_ready": rollout_session["rollback_ready"],
                "council_output_binds_build_request": council_output["emitted_artifacts"][0]["ref"]
                == f"build://{build_request['request_id']}",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_builder_live_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://builder-live-demo/v1",
            metadata={"display_name": "Builder Live Enactment Sandbox"},
        )
        design_manifest, design_validation, build_request = self._prepare_design_backed_request(
            target_subsystem="L5.LiveEnactment",
            change_summary="Materialize builder patches in a temp workspace and run actual eval commands.",
            spec_refs=[
                "specs/interfaces/selfctor.design_reader.v0.idl",
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/interfaces/selfctor.enactment.v0.idl",
                "specs/interfaces/governance.oversight.v0.idl",
                "specs/schemas/design_delta_manifest.schema",
                "specs/schemas/build_request.yaml",
                "specs/schemas/build_artifact.yaml",
                "specs/schemas/builder_live_enactment_session.schema",
                "specs/schemas/guardian_oversight_event.schema",
            ],
            output_paths=[
                "src/omoikane/self_construction/",
                "tests/unit/",
                "docs/02-subsystems/self-construction/",
                "docs/04-ai-governance/",
                "evals/continuity/",
                "meta/decision-log/",
            ],
            request_id="build-l5-live-0001",
            change_class="feature-improvement",
            must_pass=[
                "evals/continuity/builder_live_enactment_execution.yaml",
                "evals/continuity/builder_live_oversight_network.yaml",
            ],
            council_session_id="sess-builder-live-0001",
            guardian_gate="pass",
        )
        scope_validation = self.patch_generator.validate_scope(build_request)
        build_artifact = self.patch_generator.generate_patch_set(build_request)
        patch_descriptions = [
            self.patch_generator.describe_patch(descriptor)
            for descriptor in build_artifact.get("patches", [])
        ]
        suite_selection = self.diff_evaluator.select_suite(
            target_subsystem=build_request["target_subsystem"],
            requested_evals=build_request["constraints"]["must_pass"],
        )
        enactment_oversight_event = self._build_live_enactment_oversight_event(
            reviewer_namespace="builder-live",
            payload_ref=f"artifact://{build_artifact['artifact_id']}",
        )
        enactment_session = self.live_enactment.execute(
            build_request=build_request,
            build_artifact=build_artifact,
            eval_refs=suite_selection["selected_evals"],
            repo_root=self.repo_root,
            guardian_oversight_event=enactment_oversight_event,
        )
        enactment_validation = self.live_enactment.validate_session(enactment_session)
        council_output = {
            "kind": "council_output",
            "schema_version": "1.0.0",
            "session_id": build_request["approval_context"]["council_session_id"],
            "status": "approved",
            "decision_mode": "consensus",
            "approved_action": "emit_build_request",
            "resolution_summary": "Live builder enactment approved inside a temp workspace with cleanup and eval receipts.",
            "timeout_status": {
                "status": "within-budget",
                "elapsed_ms": 17_000,
                "soft_timeout_ms": 45_000,
                "hard_timeout_ms": 90_000,
                "fallback_applied": "none",
                "follow_up_action": "record-resolution",
            },
            "vote_summary": {
                "participant_count": 4,
                "approvals": 4,
                "rejections": 0,
                "abstentions": 0,
                "weighted_score": 3.2,
            },
            "guardian_gate": {
                "status": "pass",
                "reason": "Live enactment stays in a temp workspace and never targets immutable boundaries.",
                "checked_rules": ["A1-continuity", "A2-uniqueness"],
            },
            "emitted_artifacts": [
                {
                    "artifact_kind": "build_request",
                    "ref": f"build://{build_request['request_id']}",
                },
                {
                    "artifact_kind": "continuity_log_entry",
                    "ref": build_artifact.get("continuity_log_ref", ""),
                },
            ],
            "must_pass_evals": list(build_request["constraints"]["must_pass"]),
            "continuity_record": {
                "category": "self-modify",
                "ref": build_artifact.get("continuity_log_ref", ""),
            },
            "recorded_at": utc_now_iso(),
        }
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.read",
            payload={
                "policy": self.design_reader.policy(),
                "manifest": design_manifest,
                "validation": design_validation,
            },
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.build_request.emitted",
            payload={
                "council_output": council_output,
                "build_request": build_request,
            },
            actor="Council",
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.generated",
            payload={
                "policy": self.patch_generator.policy(),
                "artifact": build_artifact,
                "scope_validation": scope_validation,
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.enactment.attestation.satisfied",
            payload=enactment_oversight_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.enactment.executed",
            payload={
                "policy": self.live_enactment.policy(),
                "session": enactment_session,
                "validation": enactment_validation,
            },
            actor="LiveEnactmentService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "builder": {
                "design_manifest": design_manifest,
                "council_output": council_output,
                "build_request": build_request,
                "patch_generator_policy": self.patch_generator.policy(),
                "live_enactment_policy": self.live_enactment.policy(),
                "scope_validation": scope_validation,
                "artifact": build_artifact,
                "patches": patch_descriptions,
                "suite_selection": suite_selection,
                "enactment_session": enactment_session,
            },
            "validation": {
                "ok": (
                    design_validation["ok"]
                    and design_manifest["status"] == "ready"
                    and
                    scope_validation["allowed"]
                    and build_artifact["status"] == "ready"
                    and enactment_validation["ok"]
                    and enactment_session["status"] == "passed"
                ),
                "design_reader_handoff_ok": design_validation["ok"],
                "design_manifest_status": design_manifest["status"],
                "scope_allowed": scope_validation["allowed"],
                "patch_count": len(build_artifact.get("patches", [])),
                "selected_eval_count": len(suite_selection["selected_evals"]),
                "enactment_ok": enactment_validation["ok"],
                "enactment_status": enactment_session["status"],
                "mutated_file_count": enactment_session["mutated_file_count"],
                "executed_command_count": enactment_session["executed_command_count"],
                "all_commands_passed": enactment_session["all_commands_passed"],
                "cleanup_status": enactment_session["cleanup_status"],
                "reviewer_oversight_status": enactment_session["guardian_oversight_event"][
                    "human_attestation"
                ]["status"],
                "reviewer_quorum_required": enactment_session["guardian_oversight_event"][
                    "human_attestation"
                ]["required_quorum"],
                "reviewer_quorum_received": enactment_session["guardian_oversight_event"][
                    "human_attestation"
                ]["received_quorum"],
                "reviewer_binding_count": len(
                    enactment_session["guardian_oversight_event"]["reviewer_bindings"]
                ),
                "reviewer_network_receipt_count": sum(
                    bool(binding["network_receipt_id"])
                    for binding in enactment_session["guardian_oversight_event"][
                        "reviewer_bindings"
                    ]
                ),
                "reviewer_network_attested": enactment_session["oversight_gate"][
                    "reviewer_network_attested"
                ],
                "enactment_payload_ref_bound": enactment_session["guardian_oversight_event"][
                    "payload_ref"
                ]
                == f"artifact://{build_artifact['artifact_id']}",
                "oversight_gate_status": enactment_session["oversight_gate"]["status"],
                "oversight_gate_cleanup_status": enactment_session["oversight_gate"][
                    "cleanup_status"
                ],
                "oversight_gate_command_count": enactment_session["oversight_gate"][
                    "executed_command_count"
                ],
                "council_output_binds_build_request": council_output["emitted_artifacts"][0]["ref"]
                == f"build://{build_request['request_id']}",
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_rollback_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://rollback-demo/v1",
            metadata={"display_name": "Rollback Pipeline Sandbox"},
        )
        design_manifest, design_validation, build_request = self._prepare_design_backed_request(
            target_subsystem="L5.RollbackEngine",
            change_summary="Materialize deterministic rollback execution for the builder pipeline.",
            spec_refs=[
                "specs/interfaces/selfctor.design_reader.v0.idl",
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/interfaces/selfctor.enactment.v0.idl",
                "specs/interfaces/selfctor.diff_eval.v0.idl",
                "specs/interfaces/selfctor.rollout.v0.idl",
                "specs/interfaces/selfctor.rollback.v0.idl",
                "specs/interfaces/governance.oversight.v0.idl",
                "specs/schemas/design_delta_manifest.schema",
                "specs/schemas/build_request.yaml",
                "specs/schemas/build_artifact.yaml",
                "specs/schemas/builder_live_enactment_session.schema",
                "specs/schemas/guardian_oversight_event.schema",
                "specs/schemas/sandbox_apply_receipt.schema",
                "specs/schemas/staged_rollout_session.schema",
                "specs/schemas/builder_rollback_session.schema",
            ],
            output_paths=[
                "src/omoikane/self_construction/",
                "tests/unit/",
                "tests/integration/",
                "docs/02-subsystems/self-construction/",
                "docs/04-ai-governance/",
                "evals/continuity/",
                "meta/decision-log/",
            ],
            request_id="build-l5-rollback-0001",
            change_class="feature-improvement",
            must_pass=[
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/builder_live_enactment_execution.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
                "evals/continuity/builder_staged_rollout_execution.yaml",
                "evals/continuity/builder_rollback_execution.yaml",
                "evals/continuity/builder_rollback_oversight_network.yaml",
            ],
            council_session_id="sess-builder-rollback-0001",
            guardian_gate="pass",
        )
        scope_validation = self.patch_generator.validate_scope(build_request)
        build_artifact = self.patch_generator.generate_patch_set(build_request)
        patch_descriptions = [
            self.patch_generator.describe_patch(descriptor)
            for descriptor in build_artifact.get("patches", [])
        ]
        sandbox_apply_receipt = self.sandbox_apply.apply_artifact(
            build_request=build_request,
            build_artifact=build_artifact,
        )
        sandbox_apply_validation = self.sandbox_apply.validate_receipt(sandbox_apply_receipt)
        suite_selection = self.diff_evaluator.select_suite(
            target_subsystem=build_request["target_subsystem"],
            requested_evals=build_request["constraints"]["must_pass"],
        )
        execution_eval_refs = self._execution_bound_eval_refs(suite_selection["selected_evals"])
        enactment_oversight_event = self._build_live_enactment_oversight_event(
            reviewer_namespace="builder-rollback-live",
            payload_ref=f"artifact://{build_artifact['artifact_id']}",
        )
        enactment_session = self.live_enactment.execute(
            build_request=build_request,
            build_artifact=build_artifact,
            eval_refs=[
                "evals/continuity/builder_live_enactment_execution.yaml",
            ],
            repo_root=self.repo_root,
            guardian_oversight_event=enactment_oversight_event,
        )
        enactment_validation = self.live_enactment.validate_session(enactment_session)
        eval_execution_session = None
        eval_execution_validation = {"ok": True, "errors": []}
        if execution_eval_refs:
            eval_execution_session = self.live_enactment.execute(
                build_request=build_request,
                build_artifact=build_artifact,
                eval_refs=execution_eval_refs,
                repo_root=self.repo_root,
                guardian_oversight_event=enactment_oversight_event,
            )
            eval_execution_validation = self.live_enactment.validate_session(eval_execution_session)
        eval_reports = [
            self.diff_evaluator.run_ab_eval(
                eval_ref=eval_ref,
                baseline_ref="runtime://baseline/current",
                sandbox_ref=(
                    "mirage://build-l5-rollback-0001/snapshot/rollback-breach"
                    if eval_ref == "evals/continuity/builder_rollback_execution.yaml"
                    else sandbox_apply_receipt["sandbox_snapshot_ref"]
                ),
                enactment_session=(
                    eval_execution_session if eval_ref in execution_eval_refs else None
                ),
            )
            for eval_ref in suite_selection["selected_evals"]
        ]
        execution_bound_reports = self._execution_bound_reports(eval_reports)
        rollout = self.diff_evaluator.classify_rollout(
            outcomes=[report["outcome"] for report in eval_reports]
        )
        rollout_session = self.rollout_planner.execute_rollout(
            build_request=build_request,
            apply_receipt=sandbox_apply_receipt,
            eval_reports=eval_reports,
            decision=rollout["decision"],
            guardian_gate_status=build_request["approval_context"]["guardian_gate"],
        )
        rollout_session_validation = self.rollout_planner.validate_session(rollout_session)
        reviewer_alpha = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-rollback-alpha",
            display_name="Rollback Review Alpha",
            credential_id="credential-rollback-alpha",
            attestation_type="institutional-badge",
            proof_ref="proof://rollback/reviewer-alpha/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-21T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://rollback/reviewer-alpha/v1",
            escalation_contact="mailto:rollback-alpha@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        reviewer_beta = self.oversight.register_reviewer(
            reviewer_id="human-reviewer-rollback-beta",
            display_name="Rollback Review Beta",
            credential_id="credential-rollback-beta",
            attestation_type="institutional-badge",
            proof_ref="proof://rollback/reviewer-beta/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-21T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref="legal://rollback/reviewer-beta/v1",
            escalation_contact="mailto:rollback-beta@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        reviewer_alpha = self.oversight.verify_reviewer_from_network(
            reviewer_alpha["reviewer_id"],
            verifier_ref="verifier://guardian-oversight.jp/reviewer-rollback-alpha",
            challenge_ref="challenge://rollback/reviewer-alpha/2026-04-21T00:00:00Z",
            challenge_digest="sha256:rollback-reviewer-alpha-20260421",
            jurisdiction_bundle_ref="legal://jp-13/rollback-integrity/v1",
            jurisdiction_bundle_digest="sha256:jp13-rollback-integrity-v1",
            verified_at="2026-04-21T00:00:00+00:00",
            valid_until="2026-10-21T00:00:00+00:00",
        )
        reviewer_beta = self.oversight.verify_reviewer_from_network(
            reviewer_beta["reviewer_id"],
            verifier_ref="verifier://guardian-oversight.jp/reviewer-rollback-beta",
            challenge_ref="challenge://rollback/reviewer-beta/2026-04-21T00:05:00Z",
            challenge_digest="sha256:rollback-reviewer-beta-20260421",
            jurisdiction_bundle_ref="legal://jp-13/rollback-integrity/v1",
            jurisdiction_bundle_digest="sha256:jp13-rollback-integrity-v1",
            verified_at="2026-04-21T00:05:00+00:00",
            valid_until="2026-10-21T00:00:00+00:00",
        )
        rollback_oversight_event = self.oversight.record(
            guardian_role="integrity",
            category="attest",
            payload_ref=sandbox_apply_receipt["rollback_plan_ref"],
            escalation_path=["guardian-oversight.jp", "rollback-review-board"],
        )
        rollback_oversight_event = self.oversight.attest(
            rollback_oversight_event["event_id"],
            reviewer_id=reviewer_alpha["reviewer_id"],
        )
        rollback_oversight_event = self.oversight.attest(
            rollback_oversight_event["event_id"],
            reviewer_id=reviewer_beta["reviewer_id"],
        )
        rollback_session = self.rollback_engine.execute_rollback(
            build_request=build_request,
            apply_receipt=sandbox_apply_receipt,
            rollout_session=rollout_session,
            live_enactment_session=enactment_session,
            repo_root=self.repo_root,
            trigger="eval-regression",
            reason="Regression detected during canary rollout.",
            initiator="IntegrityGuardian",
            guardian_oversight_event=rollback_oversight_event,
        )
        rollback_session_validation = self.rollback_engine.validate_session(rollback_session)
        council_output = {
            "kind": "council_output",
            "schema_version": "1.0.0",
            "session_id": build_request["approval_context"]["council_session_id"],
            "status": "approved",
            "decision_mode": "consensus",
            "approved_action": "emit_build_request",
            "resolution_summary": "Rollback surface approved after continuity-bound restoration checks.",
            "timeout_status": {
                "status": "within-budget",
                "elapsed_ms": 21_000,
                "soft_timeout_ms": 45_000,
                "hard_timeout_ms": 90_000,
                "fallback_applied": "none",
                "follow_up_action": "record-resolution",
            },
            "vote_summary": {
                "participant_count": 4,
                "approvals": 4,
                "rejections": 0,
                "abstentions": 0,
                "weighted_score": 3.2,
            },
            "guardian_gate": {
                "status": "pass",
                "reason": "Rollback keeps pre-apply snapshot and continuity evidence bound.",
                "checked_rules": ["A1-continuity", "A2-uniqueness"],
            },
            "emitted_artifacts": [
                {
                    "artifact_kind": "build_request",
                    "ref": f"build://{build_request['request_id']}",
                },
                {
                    "artifact_kind": "continuity_log_entry",
                    "ref": build_artifact.get("continuity_log_ref", ""),
                },
            ],
            "must_pass_evals": list(build_request["constraints"]["must_pass"]),
            "continuity_record": {
                "category": "self-modify",
                "ref": build_artifact.get("continuity_log_ref", ""),
            },
            "recorded_at": utc_now_iso(),
        }
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.design.read",
            payload={
                "policy": self.design_reader.policy(),
                "manifest": design_manifest,
                "validation": design_validation,
            },
            actor="DesignReaderService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="council.build_request.emitted",
            payload={
                "council_output": council_output,
                "build_request": build_request,
            },
            actor="Council",
            category="self-modify",
            layer="L4",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.patch.generated",
            payload={
                "policy": self.patch_generator.policy(),
                "artifact": build_artifact,
                "scope_validation": scope_validation,
            },
            actor="PatchGeneratorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.sandbox.applied",
            payload={
                "policy": self.sandbox_apply.policy(),
                "receipt": sandbox_apply_receipt,
                "validation": sandbox_apply_validation,
            },
            actor="SandboxApplyService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.enactment.attestation.satisfied",
            payload=enactment_oversight_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.enactment.executed",
            payload={
                "policy": self.live_enactment.policy(),
                "session": enactment_session,
                "validation": enactment_validation,
            },
            actor="LiveEnactmentService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.diff_eval.completed",
            payload={
                "policy": self.diff_evaluator.policy(),
                "selected_evals": suite_selection["selected_evals"],
                "reports": eval_reports,
            },
            actor="DifferentialEvaluatorService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollout.classified",
            payload={
                "decision": rollout["decision"],
                "artifact_id": build_artifact["artifact_id"],
                "request_id": build_request["request_id"],
            },
            actor="RolloutPlanner",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollout.executed",
            payload={
                "policy": self.rollout_planner.policy(),
                "session": rollout_session,
                "validation": rollout_session_validation,
            },
            actor="RolloutPlanner",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="guardian.rollback.attestation.satisfied",
            payload=rollback_oversight_event,
            actor="HumanOversightChannel",
            category="guardian-oversight",
            layer="L4",
            signature_roles=["third_party"],
            substrate="classical-silicon",
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="selfctor.rollback.executed",
            payload={
                "policy": self.rollback_engine.policy(),
                "session": rollback_session,
                "validation": rollback_session_validation,
            },
            actor="RollbackEngineService",
            category="self-modify",
            layer="L5",
            signature_roles=["self", "council", "guardian"],
            substrate="classical-silicon",
        )

        regression_detected = any(report["outcome"] == "regression" for report in eval_reports)
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "builder": {
                "design_manifest": design_manifest,
                "council_output": council_output,
                "build_request": build_request,
                "patch_generator_policy": self.patch_generator.policy(),
                "diff_evaluator_policy": self.diff_evaluator.policy(),
                "rollback_engine_policy": self.rollback_engine.policy(),
                "scope_validation": scope_validation,
                "artifact": build_artifact,
                "sandbox_apply_receipt": sandbox_apply_receipt,
                "enactment_session": enactment_session,
                "eval_execution_session": eval_execution_session,
                "patches": patch_descriptions,
                "suite_selection": suite_selection,
                "eval_reports": eval_reports,
                "rollout": rollout,
                "rollout_session": rollout_session,
                "rollback_guardian_oversight_event": rollback_oversight_event,
                "rollback_session": rollback_session,
            },
            "validation": {
                "ok": (
                    design_validation["ok"]
                    and design_manifest["status"] == "ready"
                    and
                    scope_validation["allowed"]
                    and build_artifact["status"] == "ready"
                    and sandbox_apply_validation["ok"]
                    and enactment_validation["ok"]
                    and enactment_session["status"] == "passed"
                    and eval_execution_validation["ok"]
                    and (
                        eval_execution_session is None
                        or eval_execution_session["status"] == "passed"
                    )
                    and bool(execution_bound_reports)
                    and regression_detected
                    and rollout["decision"] == "rollback"
                    and rollout_session_validation["ok"]
                    and rollout_session["status"] == "rolled-back"
                    and rollback_session_validation["ok"]
                    and rollback_session["status"] == "rolled-back"
                ),
                "design_reader_handoff_ok": design_validation["ok"],
                "design_manifest_status": design_manifest["status"],
                "scope_allowed": scope_validation["allowed"],
                "sandbox_apply_ok": sandbox_apply_validation["ok"],
                "sandbox_apply_status": sandbox_apply_receipt["status"],
                "selected_eval_count": len(suite_selection["selected_evals"]),
                "live_enactment_ok": enactment_validation["ok"],
                "live_enactment_status": enactment_session["status"],
                "eval_execution_ok": eval_execution_validation["ok"],
                "eval_execution_status": (
                    eval_execution_session["status"] if eval_execution_session is not None else "not-run"
                ),
                "regression_detected": regression_detected,
                "eval_report_evidence_bound": all(
                    len(str(report.get("comparison_digest", ""))) == 64
                    and bool(report.get("profile_id"))
                    and bool(report.get("baseline_observation", {}).get("binding_digest"))
                    and bool(report.get("sandbox_observation", {}).get("binding_digest"))
                    for report in eval_reports
                ),
                "eval_execution_evidence_bound": bool(execution_bound_reports)
                and all(
                    len(str(report.get("execution_receipt_digest", ""))) == 64
                    and report["execution_receipt"]["all_commands_passed"]
                    and report["execution_receipt"]["cleanup_status"] == "removed"
                    for report in execution_bound_reports
                ),
                "eval_execution_command_count": (
                    execution_bound_reports[0]["execution_receipt"]["executed_command_count"]
                    if execution_bound_reports
                    else 0
                ),
                "eval_execution_cleanup_status": (
                    execution_bound_reports[0]["execution_receipt"]["cleanup_status"]
                    if execution_bound_reports
                    else "not-run"
                ),
                "rollback_trigger": rollback_session["trigger"],
                "rollout_decision": rollout["decision"],
                "rollout_status": rollout_session["status"],
                "rollback_status": rollback_session["status"],
                "restored_snapshot_ref": rollback_session["restored_snapshot_ref"],
                "reverted_patch_count": rollback_session["reverted_patch_count"],
                "reverted_stage_ids": rollback_session["reverted_stage_ids"],
                "reverse_apply_journal_count": len(rollback_session["reverse_apply_journal"]),
                "reverse_apply_command_count": rollback_session["telemetry_gate"][
                    "executed_reverse_command_count"
                ],
                "reverse_apply_verified_count": rollback_session["telemetry_gate"][
                    "verified_reverse_command_count"
                ],
                "repo_bound_verified_count": rollback_session["telemetry_gate"][
                    "repo_bound_verified_command_count"
                ],
                "repo_binding_scope": rollback_session["repo_binding_summary"]["binding_scope"],
                "repo_binding_path_count": rollback_session["repo_binding_summary"][
                    "bound_path_count"
                ],
                "checkout_mutation_status": rollback_session["checkout_mutation_receipt"]["status"],
                "checkout_mutation_path_count": rollback_session["checkout_mutation_receipt"][
                    "observed_path_count"
                ],
                "checkout_mutation_cleanup_status": rollback_session["checkout_mutation_receipt"][
                    "cleanup_status"
                ],
                "checkout_mutation_restored": rollback_session["checkout_mutation_receipt"][
                    "restored_matches_baseline"
                ],
                "current_worktree_mutation_status": rollback_session[
                    "current_worktree_mutation_receipt"
                ]["status"],
                "current_worktree_mutation_path_count": rollback_session[
                    "current_worktree_mutation_receipt"
                ]["observed_path_count"],
                "current_worktree_mutation_cleanup_status": rollback_session[
                    "current_worktree_mutation_receipt"
                ]["cleanup_status"],
                "current_worktree_mutation_restored": rollback_session[
                    "current_worktree_mutation_receipt"
                ]["restored_matches_baseline"],
                "external_observer_status": rollback_session["checkout_mutation_receipt"][
                    "observer_status"
                ],
                "external_observer_receipt_count": rollback_session["checkout_mutation_receipt"][
                    "observer_receipt_count"
                ],
                "external_observer_restored": rollback_session["checkout_mutation_receipt"][
                    "observer_restored_matches_baseline"
                ],
                "external_observer_stash_preserved": rollback_session[
                    "checkout_mutation_receipt"
                ]["observer_stash_state_preserved"],
                "reviewer_oversight_status": rollback_session["guardian_oversight_event"][
                    "human_attestation"
                ]["status"],
                "reviewer_quorum_required": rollback_session["guardian_oversight_event"][
                    "human_attestation"
                ]["required_quorum"],
                "reviewer_quorum_received": rollback_session["guardian_oversight_event"][
                    "human_attestation"
                ]["received_quorum"],
                "reviewer_binding_count": len(
                    rollback_session["guardian_oversight_event"]["reviewer_bindings"]
                ),
                "reviewer_network_receipt_count": sum(
                    bool(binding["network_receipt_id"])
                    for binding in rollback_session["guardian_oversight_event"][
                        "reviewer_bindings"
                    ]
                ),
                "reviewer_network_attested": rollback_session["telemetry_gate"][
                    "reviewer_network_attested"
                ],
                "rollback_payload_ref_bound": (
                    rollback_session["guardian_oversight_event"]["payload_ref"]
                    == rollback_session["rollback_plan_ref"]
                ),
                "reverse_apply_cleanup_status": rollback_session["telemetry_gate"][
                    "reverse_cleanup_status"
                ],
                "telemetry_gate_status": rollback_session["telemetry_gate"]["status"],
                "telemetry_gate_cleanup_status": rollback_session["telemetry_gate"]["cleanup_status"],
                "telemetry_gate_command_count": rollback_session["telemetry_gate"][
                    "executed_command_count"
                ],
                "continuity_event_ref_count": len(rollback_session["continuity_event_refs"]),
                "notification_ref_count": len(rollback_session["notification_refs"]),
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_identity_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://identity-demo/v1",
            metadata={"display_name": "Identity Pause Sandbox"},
        )
        created = asdict(identity)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.created",
            payload={"display_name": "Identity Pause Sandbox", "lineage_id": identity.lineage_id},
            actor="IdentityRegistry",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        try:
            self.identity.pause(
                identity.identity_id,
                requested_by="council",
                reason="bounded continuity review window",
            )
        except PermissionError as exc:
            blocked_council_pause = {"status": "blocked", "reason": str(exc)}
        else:
            blocked_council_pause = {"status": "unexpected-pass", "reason": ""}

        council_paused_record = self.identity.pause(
            identity.identity_id,
            requested_by="council",
            reason="bounded continuity review window",
            council_resolution_ref="council://identity-lifecycle/pause-0001",
        )
        council_pause = asdict(council_paused_record)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.paused",
            payload={
                "status": council_paused_record.status,
                "pause_state": council_pause["pause_state"],
            },
            actor="IdentityRegistry",
            category="identity-lifecycle",
            layer="L1",
            signature_roles=["council"],
            substrate="classical-silicon",
        )

        try:
            self.identity.resume(identity.identity_id, self_proof="")
        except PermissionError as exc:
            blocked_resume = {"status": "blocked", "reason": str(exc)}
        else:
            blocked_resume = {"status": "unexpected-pass", "reason": ""}

        council_resumed_record = self.identity.resume(
            identity.identity_id,
            self_proof="self-proof://identity-demo-resume-council/v1",
        )
        council_resume = asdict(council_resumed_record)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.resumed",
            payload={
                "status": council_resumed_record.status,
                "pause_state": council_resume["pause_state"],
            },
            actor="IdentityRegistry",
            category="identity-lifecycle",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        self_paused_record = self.identity.pause(
            identity.identity_id,
            requested_by="self",
            reason="bounded reflective suspension",
        )
        self_pause = asdict(self_paused_record)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.paused",
            payload={
                "status": self_paused_record.status,
                "pause_state": self_pause["pause_state"],
            },
            actor="IdentityRegistry",
            category="identity-lifecycle",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        self_resumed_record = self.identity.resume(
            identity.identity_id,
            self_proof="self-proof://identity-demo-resume-self/v1",
        )
        self_resume = asdict(self_resumed_record)
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.resumed",
            payload={
                "status": self_resumed_record.status,
                "pause_state": self_resume["pause_state"],
            },
            actor="IdentityRegistry",
            category="identity-lifecycle",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        validation = {
            "council_pause_requires_resolution": (
                blocked_council_pause["status"] == "blocked"
                and blocked_council_pause["reason"] == "council pause requires council_resolution_ref"
            ),
            "council_pause_records_pause_state": (
                council_pause["status"] == "paused"
                and council_pause["pause_state"] is not None
                and council_pause["pause_state"]["pause_authority"] == "council"
                and council_pause["pause_state"]["council_resolution_ref"]
                == "council://identity-lifecycle/pause-0001"
            ),
            "resume_requires_self_proof": (
                blocked_resume["status"] == "blocked"
                and blocked_resume["reason"] == "self proof is required for resume"
            ),
            "council_pause_resume_roundtrip": (
                council_resume["status"] == "active"
                and council_resume["pause_state"] is not None
                and council_resume["pause_state"]["resumed_at"] is not None
                and council_resume["pause_state"]["resume_self_proof_ref"]
                == "self-proof://identity-demo-resume-council/v1"
            ),
            "self_pause_allows_no_council_ref": (
                self_pause["status"] == "paused"
                and self_pause["pause_state"] is not None
                and self_pause["pause_state"]["pause_authority"] == "self"
                and self_pause["pause_state"]["council_resolution_ref"] is None
            ),
            "self_pause_resume_roundtrip": (
                self_resume["status"] == "active"
                and self_resume["pause_state"] is not None
                and self_resume["pause_state"]["resume_self_proof_ref"]
                == "self-proof://identity-demo-resume-self/v1"
            ),
        }

        return {
            "policy": {
                "statuses": ["active", "paused", "terminated"],
                "pause_authorities": ["self", "council"],
                "resume_authority": "self",
                "council_pause_requires_resolution_ref": True,
            },
            "transitions": {
                "created": created,
                "council_pause": council_pause,
                "council_resume": council_resume,
                "self_pause": self_pause,
                "self_resume": self_resume,
            },
            "blocked": {
                "council_pause_without_resolution": blocked_council_pause,
                "resume_without_self_proof": blocked_resume,
            },
            "validation": validation,
            "identity_snapshot": self.identity.snapshot(),
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
        }

    def run_identity_confirmation_demo(self) -> Dict[str, Any]:
        identity = self.identity.create(
            human_consent_proof="consent://identity-confirmation-demo/v1",
            metadata={
                "display_name": "Identity Confirmation Sandbox",
                "lifecycle_phase": "ascending",
            },
        )
        self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.created",
            payload={
                "display_name": "Identity Confirmation Sandbox",
                "lineage_id": identity.lineage_id,
                "lifecycle_phase": "ascending",
            },
            actor="IdentityRegistry",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )

        profile = self.identity.confirm_identity(
            identity.identity_id,
            consent_ref="consent://identity-confirmation-demo/v1",
            scheduler_stage_ref="scheduler://method-a/identity-confirmation",
            episodic_recall_ref="episodic://identity-confirmation-demo/recall-window",
            self_model_ref="self-model://identity-confirmation-demo/stable-snapshot",
            episodic_recall_score=0.93,
            self_model_alignment_score=0.89,
            self_report={
                "report_ref": "self-report://identity-confirmation-demo/v1",
                "statement": "I experience this active transition as the same continuing self.",
                "continuity_score": 0.92,
            },
            witness_receipts=[
                {
                    "witness_id": "witness://identity-confirmation/clinician-primary",
                    "witness_role": "clinician",
                    "observation_ref": "observation://identity-confirmation/episodic-recall",
                    "alignment_score": 0.88,
                },
                {
                    "witness_id": "witness://identity-confirmation/guardian-observer",
                    "witness_role": "guardian",
                    "observation_ref": "observation://identity-confirmation/self-model-check",
                    "alignment_score": 0.9,
                },
            ],
        )
        validation = IdentityRegistry.validate_identity_confirmation(profile)
        ledger_event = self.ledger.append(
            identity_id=identity.identity_id,
            event_type="identity.confirmed",
            payload={
                "confirmation_id": profile["confirmation_id"],
                "profile_id": profile["profile_id"],
                "confirmation_digest": profile["confirmation_digest"],
                "active_transition_allowed": profile["active_transition_allowed"],
                "aggregate_score": profile["aggregate_score"],
                "witness_quorum_status": profile["witness_quorum"]["status"],
                "self_report_witness_consistency_status": profile[
                    "self_report_witness_consistency"
                ]["status"],
                "self_report_witness_consistency_digest": profile[
                    "self_report_witness_consistency"
                ]["consistency_digest"],
            },
            actor="IdentityRegistry",
            category="identity-fidelity",
            layer="L1",
            signature_roles=["self", "council", "guardian", "third_party"],
            substrate="classical-silicon",
        )

        blocked_profile = self.identity.confirm_identity(
            identity.identity_id,
            consent_ref="consent://identity-confirmation-demo/blocked",
            scheduler_stage_ref="scheduler://method-a/identity-confirmation-blocked",
            episodic_recall_ref="episodic://identity-confirmation-demo/blocked-recall",
            self_model_ref="self-model://identity-confirmation-demo/blocked-snapshot",
            episodic_recall_score=0.91,
            self_model_alignment_score=0.83,
            self_report={
                "report_ref": "self-report://identity-confirmation-demo/blocked",
                "statement": "I cannot confirm continuity with the pre-upload self.",
                "continuity_score": 0.42,
            },
            witness_receipts=[
                {
                    "witness_id": "witness://identity-confirmation/clinician-secondary",
                    "witness_role": "clinician",
                    "observation_ref": "observation://identity-confirmation/blocked-recall",
                    "alignment_score": 0.79,
                }
            ],
        )
        blocked_validation = IdentityRegistry.validate_identity_confirmation(blocked_profile)

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "policy": {
                "profile_id": profile["profile_id"],
                "transition": profile["transition"],
                "required_dimensions": profile["required_dimensions"],
                "aggregate_threshold": profile["aggregate_threshold"],
                "witness_quorum": profile["witness_quorum"],
                "self_report_witness_consistency_policy": profile[
                    "self_report_witness_consistency"
                ]["policy_id"],
                "failure_action": "failed-ascension-or-repeat-ascending",
            },
            "confirmation_profile": profile,
            "blocked_profile": blocked_profile,
            "validation": {
                **validation,
                "blocked_profile_fail_closed": (
                    blocked_profile["result"] == "failed"
                    and blocked_profile["active_transition_allowed"] is False
                    and "subjective-self-report-not-bound"
                    in blocked_profile["failure_reasons"]
                    and "third-party-witness-quorum-not-met"
                    in blocked_profile["failure_reasons"]
                    and blocked_validation["ok"] is False
                    and blocked_validation["confirmation_digest_bound"] is True
                ),
                "ledger_event_bound": (
                    ledger_event.payload["confirmation_digest"]
                    == profile["confirmation_digest"]
                    and ledger_event.payload["self_report_witness_consistency_digest"]
                    == profile["self_report_witness_consistency"]["consistency_digest"]
                ),
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
        public_verification_bundle = self.ledger.compile_public_verification_bundle()
        public_verification_validation = self.ledger.validate_public_verification_bundle(
            public_verification_bundle
        )
        return {
            "identity": {
                "identity_id": identity.identity_id,
                "lineage_id": identity.lineage_id,
            },
            "ledger_profile": self.ledger.profile(),
            "ledger_snapshot": self.ledger.snapshot(),
            "ledger_verification": self.ledger.verify(),
            "public_verification_bundle": public_verification_bundle,
            "public_verification_validation": public_verification_validation,
        }
