"""CLI for the OmoikaneOS reference runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .agentic.trust import TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES
from .agentic.yaoyorozu import YAOYOROZU_PROPOSAL_PROFILES
from .reference_os import OmoikaneReferenceOS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OmoikaneOS reference runtime CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="Run a safe reference scenario")
    demo_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    amendment_parser = subparsers.add_parser(
        "amendment-demo",
        help="Run the governance amendment policy and constitutional freeze scenario",
    )
    amendment_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    version_parser = subparsers.add_parser(
        "version-demo",
        help="Emit the hybrid semver/calver release manifest for the reference runtime",
    )
    version_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    naming_parser = subparsers.add_parser(
        "naming-demo",
        help="Emit the fixed naming policy for project romanization and sandbox self labels",
    )
    naming_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    connectome_parser = subparsers.add_parser(
        "connectome-demo",
        help="Emit a reference L2 connectome snapshot and validation summary",
    )
    connectome_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    bdb_parser = subparsers.add_parser(
        "bdb-demo",
        help="Run the L6 Biological-Digital Bridge viability scenario",
    )
    bdb_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    imc_parser = subparsers.add_parser(
        "imc-demo",
        help="Run the L6 Inter-Mind Channel handshake, disclosure, and disconnect scenario",
    )
    imc_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    collective_parser = subparsers.add_parser(
        "collective-demo",
        help="Run the bounded L6 collective identity, merge-thought, and recovery scenario",
    )
    collective_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    ewa_parser = subparsers.add_parser(
        "ewa-demo",
        help="Run the L6 External World Agent authorization, safety, and veto scenario",
    )
    ewa_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    wms_parser = subparsers.add_parser(
        "wms-demo",
        help="Run the L6 World Model Sync reconciliation and private-escape scenario",
    )
    wms_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    sensory_loopback_parser = subparsers.add_parser(
        "sensory-loopback-demo",
        help="Run the L6 sensory loopback coherence, guardian hold, and stabilization scenario",
    )
    sensory_loopback_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    memory_parser = subparsers.add_parser(
        "memory-demo",
        help="Emit a reference MemoryCrystal compaction manifest and validation summary",
    )
    memory_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    memory_replication_parser = subparsers.add_parser(
        "memory-replication-demo",
        help="Run the L2 MemoryCrystal replication quorum, audit, and reconciliation scenario",
    )
    memory_replication_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    memory_edit_parser = subparsers.add_parser(
        "memory-edit-demo",
        help="Run the reversible recall-affect buffer scenario without mutating source memory",
    )
    memory_edit_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    semantic_parser = subparsers.add_parser(
        "semantic-demo",
        help="Emit a deterministic semantic memory projection derived from MemoryCrystal",
    )
    semantic_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    procedural_parser = subparsers.add_parser(
        "procedural-demo",
        help="Emit a connectome-coupled procedural memory preview derived from MemoryCrystal",
    )
    procedural_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    procedural_writeback_parser = subparsers.add_parser(
        "procedural-writeback-demo",
        help="Apply a human-approved bounded procedural writeback to a copied Connectome snapshot",
    )
    procedural_writeback_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    procedural_skill_parser = subparsers.add_parser(
        "procedural-skill-demo",
        help="Run guardian-witnessed sandbox skill execution from a validated procedural writeback",
    )
    procedural_skill_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    procedural_enactment_parser = subparsers.add_parser(
        "procedural-enactment-demo",
        help="Run temp-workspace procedural skill enactment from a validated sandbox execution receipt",
    )
    procedural_enactment_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    procedural_actuation_parser = subparsers.add_parser(
        "procedural-actuation-demo",
        help="Bridge a passed procedural enactment to an EWA external actuation authorization artifact",
    )
    procedural_actuation_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    episodic_parser = subparsers.add_parser(
        "episodic-demo",
        help="Run the L2 episodic stream canonical shape and MemoryCrystal handoff scenario",
    )
    episodic_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    perception_parser = subparsers.add_parser(
        "perception-demo",
        help="Run the L3 perception backend failover and qualia-bound scene encoding scenario",
    )
    perception_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    reasoning_parser = subparsers.add_parser(
        "reasoning-demo",
        help="Run the L3 reasoning backend failover and ledger-safe trace scenario",
    )
    reasoning_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    cognitive_parser = subparsers.add_parser(
        "cognitive-demo",
        help="Legacy alias for reasoning-demo",
    )
    cognitive_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    affect_parser = subparsers.add_parser(
        "affect-demo",
        help="Run the L3 affect backend failover and continuity smoothing scenario",
    )
    affect_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    attention_parser = subparsers.add_parser(
        "attention-demo",
        help="Run the L3 attention backend failover and affect-aware focus routing scenario",
    )
    attention_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    volition_parser = subparsers.add_parser(
        "volition-demo",
        help="Run the L3 volition backend failover and guard-aware intent arbitration scenario",
    )
    volition_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    imagination_parser = subparsers.add_parser(
        "imagination-demo",
        help="Run the L3 imagination backend failover and bounded IMC/WMS handoff scenario",
    )
    imagination_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    language_parser = subparsers.add_parser(
        "language-demo",
        help="Run the L3 language bridge failover and disclosure-floor redaction scenario",
    )
    language_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    metacognition_parser = subparsers.add_parser(
        "metacognition-demo",
        help="Run the L3 metacognition backend failover and bounded self-monitor scenario",
    )
    metacognition_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    qualia_parser = subparsers.add_parser(
        "qualia-demo",
        help="Run the L2 qualia surrogate profile and checkpoint scenario",
    )
    qualia_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    self_model_parser = subparsers.add_parser(
        "self-model-demo",
        help="Run the L2 self-model stability and abrupt-change monitoring scenario",
    )
    self_model_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    design_reader_parser = subparsers.add_parser(
        "design-reader-demo",
        help="Run the L5 docs/specs design-delta handoff planning scenario",
    )
    design_reader_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    patch_generator_parser = subparsers.add_parser(
        "patch-generator-demo",
        help="Run the L5 planning-cue aligned patch descriptor generation and fail-closed scope blocking scenario",
    )
    patch_generator_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    diff_eval_parser = subparsers.add_parser(
        "diff-eval-demo",
        help="Run the L5 parsed A/B evidence, execution receipt binding, and promote/hold/rollback classification scenario",
    )
    diff_eval_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    sandbox_parser = subparsers.add_parser(
        "sandbox-demo",
        help="Run the L5 sandbox suffering proxy and freeze scenario",
    )
    sandbox_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    builder_parser = subparsers.add_parser(
        "builder-demo",
        help="Run the L5 build-request, sandbox apply, differential eval, and staged rollout scenario",
    )
    builder_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    builder_live_parser = subparsers.add_parser(
        "builder-live-demo",
        help="Run the L5 temp workspace mutation and actual eval command enactment scenario",
    )
    builder_live_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    rollback_parser = subparsers.add_parser(
        "rollback-demo",
        help="Run the L5 regression-triggered rollback, direct current-checkout restoration, and pre-apply snapshot recovery scenario",
    )
    rollback_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    substrate_parser = subparsers.add_parser(
        "substrate-demo",
        help="Run the L0 substrate allocation/attestation/migration scenario",
    )
    substrate_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    broker_parser = subparsers.add_parser(
        "broker-demo",
        help="Run the L1 substrate broker selection, shadow-sync dual allocation, and migration scenario",
    )
    broker_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    energy_budget_parser = subparsers.add_parser(
        "energy-budget-demo",
        help="Run the L1 AP-1 energy budget floor protection and standby signal scenario",
    )
    energy_budget_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    energy_budget_pool_parser = subparsers.add_parser(
        "energy-budget-pool-demo",
        help="Run the L1 multi-identity AP-1 energy budget pool floor protection scenario",
    )
    energy_budget_pool_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    energy_budget_subsidy_parser = subparsers.add_parser(
        "energy-budget-subsidy-demo",
        help="Run the L1 consent-bound voluntary energy budget subsidy scenario",
    )
    energy_budget_subsidy_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON only",
    )

    continuity_parser = subparsers.add_parser(
        "continuity-demo",
        help="Run the L1 continuity ledger profile and signature policy scenario",
    )
    continuity_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    identity_parser = subparsers.add_parser(
        "identity-demo",
        help="Run the L1 identity pause/resume lifecycle scenario with machine-readable pause_state output",
    )
    identity_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    identity_confirmation_parser = subparsers.add_parser(
        "identity-confirmation-demo",
        help="Run the L1 identity confirmation profile scenario",
    )
    identity_confirmation_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON only",
    )

    scheduler_parser = subparsers.add_parser(
        "scheduler-demo",
        help="Run the L1 ascension scheduler Method A/B/C, artifact sync, and verifier rotation scenario",
    )
    scheduler_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    council_parser = subparsers.add_parser(
        "council-demo",
        help="Run the L4 Council session budget and timeout strategy scenario",
    )
    council_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    multi_council_parser = subparsers.add_parser(
        "multi-council-demo",
        help="Run the L4 multi-council trigger and external routing scenario",
    )
    multi_council_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    distributed_council_parser = subparsers.add_parser(
        "distributed-council-demo",
        help="Run the L4 distributed Federation/Heritage review and conflict escalation scenario",
    )
    distributed_council_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    distributed_transport_parser = subparsers.add_parser(
        "distributed-transport-demo",
        help="Run the L4 distributed participant attestation, authority route target discovery, cross-host authority routing, privileged capture acquisition, and replay-guard scenario",
    )
    distributed_transport_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    cognitive_audit_parser = subparsers.add_parser(
        "cognitive-audit-demo",
        help="Run the L2/L3/L4 cross-layer cognitive audit and bounded Council review scenario",
    )
    cognitive_audit_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    cognitive_audit_governance_parser = subparsers.add_parser(
        "cognitive-audit-governance-demo",
        help="Run the L2/L3/L4 cognitive audit governance binding across oversight, Federation, and Heritage review",
    )
    cognitive_audit_governance_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON only",
    )

    task_graph_parser = subparsers.add_parser(
        "task-graph-demo",
        help="Run the L4 TaskGraph complexity policy and dispatch scenario",
    )
    task_graph_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    consensus_bus_parser = subparsers.add_parser(
        "consensus-bus-demo",
        help="Run the L4 ConsensusBus audited delivery and direct-handoff blocking scenario",
    )
    consensus_bus_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    trust_parser = subparsers.add_parser(
        "trust-demo",
        help="Run the L4 trust update policy and human pin scenario",
    )
    trust_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    trust_transfer_parser = subparsers.add_parser(
        "trust-transfer-demo",
        help="Run the L4 cross-substrate trust export/import receipt scenario",
    )
    trust_transfer_parser.add_argument(
        "--export-profile",
        choices=TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES,
        default=TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES[0],
        help="Select the trust transfer export profile to materialize",
    )
    trust_transfer_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    yaoyorozu_parser = subparsers.add_parser(
        "yaoyorozu-demo",
        help="Run the repo-local Yaoyorozu registry sync, council convocation, and build-request handoff scenario",
    )
    yaoyorozu_parser.add_argument(
        "--proposal-profile",
        default="self-modify-patch-v1",
        choices=YAOYOROZU_PROPOSAL_PROFILES,
        help="Select the bounded Yaoyorozu proposal profile to materialize",
    )
    yaoyorozu_parser.add_argument(
        "--include-optional-coverage",
        action="append",
        choices=["runtime", "schema", "eval", "docs"],
        help="Opt into proposal-profile optional worker coverage for this demo run",
    )
    yaoyorozu_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    oversight_parser = subparsers.add_parser(
        "oversight-demo",
        help="Run the Guardian human oversight quorum and pin breach scenario",
    )
    oversight_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    oversight_network_parser = subparsers.add_parser(
        "oversight-network-demo",
        help="Run the Guardian reviewer verifier-network attestation scenario",
    )
    oversight_network_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    ethics_parser = subparsers.add_parser(
        "ethics-demo",
        help="Run the L1 ethics rule language and decision recording scenario",
    )
    ethics_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    termination_parser = subparsers.add_parser(
        "termination-demo",
        help="Run the L1 termination gate immediate, cool-off, and reject scenarios",
    )
    termination_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    gap_parser = subparsers.add_parser("gap-report", help="Scan design gaps in this repo")
    gap_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect",
    )
    gap_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    return parser


def _print_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    runtime = OmoikaneReferenceOS()

    if args.command == "demo":
        _print_result(runtime.run_reference_scenario(), args.json)
        return

    if args.command == "amendment-demo":
        _print_result(runtime.run_amendment_demo(), args.json)
        return

    if args.command == "version-demo":
        _print_result(runtime.run_version_demo(), args.json)
        return

    if args.command == "naming-demo":
        _print_result(runtime.run_naming_demo(), args.json)
        return

    if args.command == "connectome-demo":
        _print_result(runtime.run_connectome_demo(), args.json)
        return

    if args.command == "bdb-demo":
        _print_result(runtime.run_bdb_demo(), args.json)
        return

    if args.command == "imc-demo":
        _print_result(runtime.run_imc_demo(), args.json)
        return

    if args.command == "collective-demo":
        _print_result(runtime.run_collective_demo(), args.json)
        return

    if args.command == "ewa-demo":
        _print_result(runtime.run_ewa_demo(), args.json)
        return

    if args.command == "wms-demo":
        _print_result(runtime.run_wms_demo(), args.json)
        return

    if args.command == "sensory-loopback-demo":
        _print_result(runtime.run_sensory_loopback_demo(), args.json)
        return

    if args.command == "memory-demo":
        _print_result(runtime.run_memory_demo(), args.json)
        return

    if args.command == "memory-replication-demo":
        _print_result(runtime.run_memory_replication_demo(), args.json)
        return

    if args.command == "memory-edit-demo":
        _print_result(runtime.run_memory_edit_demo(), args.json)
        return

    if args.command == "semantic-demo":
        _print_result(runtime.run_semantic_demo(), args.json)
        return

    if args.command == "procedural-demo":
        _print_result(runtime.run_procedural_demo(), args.json)
        return

    if args.command == "procedural-writeback-demo":
        _print_result(runtime.run_procedural_writeback_demo(), args.json)
        return

    if args.command == "procedural-skill-demo":
        _print_result(runtime.run_procedural_skill_demo(), args.json)
        return

    if args.command == "procedural-enactment-demo":
        _print_result(runtime.run_procedural_enactment_demo(), args.json)
        return

    if args.command == "procedural-actuation-demo":
        _print_result(runtime.run_procedural_actuation_demo(), args.json)
        return

    if args.command == "episodic-demo":
        _print_result(runtime.run_episodic_demo(), args.json)
        return

    if args.command == "perception-demo":
        _print_result(runtime.run_perception_demo(), args.json)
        return

    if args.command == "reasoning-demo":
        _print_result(runtime.run_reasoning_demo(), args.json)
        return

    if args.command == "cognitive-demo":
        _print_result(runtime.run_reasoning_demo(), args.json)
        return

    if args.command == "affect-demo":
        _print_result(runtime.run_affect_demo(), args.json)
        return

    if args.command == "attention-demo":
        _print_result(runtime.run_attention_demo(), args.json)
        return

    if args.command == "volition-demo":
        _print_result(runtime.run_volition_demo(), args.json)
        return

    if args.command == "imagination-demo":
        _print_result(runtime.run_imagination_demo(), args.json)
        return

    if args.command == "language-demo":
        _print_result(runtime.run_language_demo(), args.json)
        return

    if args.command == "metacognition-demo":
        _print_result(runtime.run_metacognition_demo(), args.json)
        return

    if args.command == "qualia-demo":
        _print_result(runtime.run_qualia_demo(), args.json)
        return

    if args.command == "self-model-demo":
        _print_result(runtime.run_self_model_demo(), args.json)
        return

    if args.command == "design-reader-demo":
        _print_result(runtime.run_design_reader_demo(), args.json)
        return

    if args.command == "patch-generator-demo":
        _print_result(runtime.run_patch_generator_demo(), args.json)
        return

    if args.command == "diff-eval-demo":
        _print_result(runtime.run_diff_eval_demo(), args.json)
        return

    if args.command == "sandbox-demo":
        _print_result(runtime.run_sandbox_demo(), args.json)
        return

    if args.command == "builder-demo":
        _print_result(runtime.run_builder_demo(), args.json)
        return

    if args.command == "builder-live-demo":
        _print_result(runtime.run_builder_live_demo(), args.json)
        return

    if args.command == "rollback-demo":
        _print_result(runtime.run_rollback_demo(), args.json)
        return

    if args.command == "substrate-demo":
        _print_result(runtime.run_substrate_demo(), args.json)
        return

    if args.command == "broker-demo":
        _print_result(runtime.run_broker_demo(), args.json)
        return

    if args.command == "energy-budget-demo":
        _print_result(runtime.run_energy_budget_demo(), args.json)
        return

    if args.command == "energy-budget-pool-demo":
        _print_result(runtime.run_energy_budget_pool_demo(), args.json)
        return

    if args.command == "energy-budget-subsidy-demo":
        _print_result(runtime.run_energy_budget_subsidy_demo(), args.json)
        return

    if args.command == "continuity-demo":
        _print_result(runtime.run_continuity_demo(), args.json)
        return

    if args.command == "identity-demo":
        _print_result(runtime.run_identity_demo(), args.json)
        return

    if args.command == "identity-confirmation-demo":
        _print_result(runtime.run_identity_confirmation_demo(), args.json)
        return

    if args.command == "scheduler-demo":
        _print_result(runtime.run_scheduler_demo(), args.json)
        return

    if args.command == "council-demo":
        _print_result(runtime.run_council_demo(), args.json)
        return

    if args.command == "multi-council-demo":
        _print_result(runtime.run_multi_council_demo(), args.json)
        return

    if args.command == "distributed-council-demo":
        _print_result(runtime.run_distributed_council_demo(), args.json)
        return

    if args.command == "distributed-transport-demo":
        _print_result(runtime.run_distributed_transport_demo(), args.json)
        return

    if args.command == "cognitive-audit-demo":
        _print_result(runtime.run_cognitive_audit_demo(), args.json)
        return

    if args.command == "cognitive-audit-governance-demo":
        _print_result(runtime.run_cognitive_audit_governance_demo(), args.json)
        return

    if args.command == "task-graph-demo":
        _print_result(runtime.run_task_graph_demo(), args.json)
        return

    if args.command == "consensus-bus-demo":
        _print_result(runtime.run_consensus_bus_demo(), args.json)
        return

    if args.command == "trust-demo":
        _print_result(runtime.run_trust_demo(), args.json)
        return

    if args.command == "trust-transfer-demo":
        _print_result(
            runtime.run_trust_transfer_demo(export_profile_id=args.export_profile),
            args.json,
        )
        return

    if args.command == "yaoyorozu-demo":
        _print_result(
            runtime.run_yaoyorozu_demo(
                proposal_profile=args.proposal_profile,
                include_optional_coverage=args.include_optional_coverage,
            ),
            args.json,
        )
        return

    if args.command == "oversight-demo":
        _print_result(runtime.run_guardian_oversight_demo(), args.json)
        return

    if args.command == "oversight-network-demo":
        _print_result(runtime.run_guardian_oversight_network_demo(), args.json)
        return

    if args.command == "ethics-demo":
        _print_result(runtime.run_ethics_demo(), args.json)
        return

    if args.command == "termination-demo":
        _print_result(runtime.run_termination_demo(), args.json)
        return

    if args.command == "gap-report":
        repo_root = Path(args.repo_root).resolve()
        _print_result(runtime.generate_gap_report(repo_root), args.json)
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
