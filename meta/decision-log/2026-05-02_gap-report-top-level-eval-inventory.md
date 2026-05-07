---
date: 2026-05-02
status: decided
closes_next_gaps:
  - gap-report-top-level-eval-inventory
deciders: [yasufumi, codex-builder]
related_docs:
  - evals/*/README.md
  - evals/README.md
  - evals/**/*.yaml
---

# Decision: gap-report は top-level eval inventory drift も監査する

## Context

`gap-report` は `evals/*/README.md` と各 surface の YAML を照合していたが、
`evals/README.md` 自体は scan surface と inventory drift 判定から外れていた。
そのため top-level eval index が古くても all-zero gate は通過できた。

## Decision

`evals/README.md` を scan receipt の digest-bound surface に追加し、
`evals/**/*.yaml` / `*.yml` の repo-local eval path が top-level inventory に無い場合は
`inventory_drift_hits` として報告する。
surface 別 README は従来どおり basename だけを照合し、
top-level README だけ path を含む inventory entry を許可する。

## Consequences

- top-level eval index の欠落は high-priority inventory drift として all-zero gate を止める
- clean repo では `evals/README.md` の surface digest が scan receipt に含まれる
- surface 別 README の cross-surface mention 無視ルールは維持される

## Revisit triggers

- eval inventory を README ではなく generated manifest に移す時
- eval file metadata を subsystem / level / ethics_check ごとに構造化して照合する時
