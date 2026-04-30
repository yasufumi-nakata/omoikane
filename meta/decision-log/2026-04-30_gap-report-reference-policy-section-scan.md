---
date: 2026-04-30
deciders: [yasufumi, codex]
related_docs:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/gaps.py
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - evals/continuity/gap_scanner_required_reference_files.yaml
status: decided
closes_next_gaps:
  - 2026-04-30_parallel-codex-orchestration-reference.md#gap-3
---

# Decision: gap-report で reference policy section を検証する

## Context

`references/*.md` は hourly builder の pull-first / worker ownership / verification
境界を repo-local に固定する safety contract です。前段では required file の存在を
`missing_required_reference_files` として検出するところまで進めましたが、runbook が
空洞化した場合は all-zero gate を通過できる余地が残っていました。

## Options considered

- A: reference file の存在確認だけを維持する
- B: 各 required reference file の必須 section heading を gap-report で検査する
- C: 全 section 本文を exact digest allowlist として固定する

## Decision

B を採用しました。exact digest allowlist は通常の runbook 更新を過度に固くするため避け、
`Preflight`、`Gate Order`、`Worker Boundaries`、`Verification`、`Handoff` などの
section-level policy が消えた時だけ high-priority task として surfacing します。

## Consequences

- `gap-report` は present repo-local reference runbook の section 欠落を
  `missing_required_reference_policy_sections` として返します。
- scan receipt の counts と public schema は、この section 欠落数を all-zero 判定へ含めます。
- IntegrityGuardian は runbook の存在だけでなく policy section の維持も監査対象にします。
