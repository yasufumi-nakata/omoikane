"""Repo-local worker stub used by the Yaoyorozu dispatch demo."""

from __future__ import annotations

import argparse
import json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit one bounded Yaoyorozu worker report.")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--role-id", required=True)
    parser.add_argument("--coverage-area", required=True)
    parser.add_argument("--dispatch-profile", required=True)
    parser.add_argument("--workspace-scope", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--target-path", action="append", dest="target_paths", default=[])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = {
        "kind": "yaoyorozu_local_worker_report",
        "agent_id": args.agent_id,
        "role_id": args.role_id,
        "coverage_area": args.coverage_area,
        "dispatch_profile": args.dispatch_profile,
        "workspace_scope": args.workspace_scope,
        "source_ref": args.source_ref,
        "target_paths": list(args.target_paths),
        "status": "ready",
    }
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
