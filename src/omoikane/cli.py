"""CLI for the OmoikaneOS reference runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

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

    memory_parser = subparsers.add_parser(
        "memory-demo",
        help="Emit a reference MemoryCrystal compaction manifest and validation summary",
    )
    memory_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    cognitive_parser = subparsers.add_parser(
        "cognitive-demo",
        help="Run the L3 reasoning backend failover scenario",
    )
    cognitive_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    qualia_parser = subparsers.add_parser(
        "qualia-demo",
        help="Run the L2 qualia surrogate profile and checkpoint scenario",
    )
    qualia_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    sandbox_parser = subparsers.add_parser(
        "sandbox-demo",
        help="Run the L5 sandbox suffering proxy and freeze scenario",
    )
    sandbox_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    substrate_parser = subparsers.add_parser(
        "substrate-demo",
        help="Run the L0 substrate allocation/attestation/migration scenario",
    )
    substrate_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    continuity_parser = subparsers.add_parser(
        "continuity-demo",
        help="Run the L1 continuity ledger profile and signature policy scenario",
    )
    continuity_parser.add_argument("--json", action="store_true", help="Emit JSON only")

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

    task_graph_parser = subparsers.add_parser(
        "task-graph-demo",
        help="Run the L4 TaskGraph complexity policy and dispatch scenario",
    )
    task_graph_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    trust_parser = subparsers.add_parser(
        "trust-demo",
        help="Run the L4 trust update policy and human pin scenario",
    )
    trust_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    oversight_parser = subparsers.add_parser(
        "oversight-demo",
        help="Run the Guardian human oversight quorum and pin breach scenario",
    )
    oversight_parser.add_argument("--json", action="store_true", help="Emit JSON only")

    ethics_parser = subparsers.add_parser(
        "ethics-demo",
        help="Run the L1 ethics rule language and decision recording scenario",
    )
    ethics_parser.add_argument("--json", action="store_true", help="Emit JSON only")

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

    if args.command == "connectome-demo":
        _print_result(runtime.run_connectome_demo(), args.json)
        return

    if args.command == "bdb-demo":
        _print_result(runtime.run_bdb_demo(), args.json)
        return

    if args.command == "memory-demo":
        _print_result(runtime.run_memory_demo(), args.json)
        return

    if args.command == "cognitive-demo":
        _print_result(runtime.run_cognitive_failover_demo(), args.json)
        return

    if args.command == "qualia-demo":
        _print_result(runtime.run_qualia_demo(), args.json)
        return

    if args.command == "sandbox-demo":
        _print_result(runtime.run_sandbox_demo(), args.json)
        return

    if args.command == "substrate-demo":
        _print_result(runtime.run_substrate_demo(), args.json)
        return

    if args.command == "continuity-demo":
        _print_result(runtime.run_continuity_demo(), args.json)
        return

    if args.command == "council-demo":
        _print_result(runtime.run_council_demo(), args.json)
        return

    if args.command == "multi-council-demo":
        _print_result(runtime.run_multi_council_demo(), args.json)
        return

    if args.command == "task-graph-demo":
        _print_result(runtime.run_task_graph_demo(), args.json)
        return

    if args.command == "trust-demo":
        _print_result(runtime.run_trust_demo(), args.json)
        return

    if args.command == "oversight-demo":
        _print_result(runtime.run_guardian_oversight_demo(), args.json)
        return

    if args.command == "ethics-demo":
        _print_result(runtime.run_ethics_demo(), args.json)
        return

    if args.command == "gap-report":
        repo_root = Path(args.repo_root).resolve()
        _print_result(runtime.generate_gap_report(repo_root), args.json)
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
