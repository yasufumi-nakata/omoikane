---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - evals/agentic/README.md
  - evals/cognitive/README.md
  - evals/continuity/README.md
  - evals/interface/README.md
  - evals/performance/README.md
  - evals/safety/README.md
  - src/omoikane/self_construction/gaps.py
status: decided
---

# Decision: gap-report は eval README inventory drift も fail-closed で拾う

## Context

2026-04-23 時点の `gap-report --json` は all-zero でしたが、
`evals/*/README.md` には現行 tree の YAML surface が多数記載されておらず、
automation が README inventory を見ても current eval coverage を正しく把握できない状態でした。

spec inventory drift は既に scanner が拾えますが、
eval inventory drift は blind spot のままで、
「実装済み eval が truth-source から落ちている」ことを
hourly builder が自力で検知できませんでした。

## Options considered

- A: eval README の棚卸しは手動 review に残し、scanner は specs だけを見る
- B: `gap-report` が `evals/*/README.md` と実在 YAML を突き合わせ、inventory drift を high-priority task として返す
- C: eval README inventory を廃止し、ファイル一覧だけを別 generated artifact に切り出す

## Decision

Option B を採択します。

- `GapScanner` は `evals/*/README.md` を truth-source inventory として扱い、
  README に無い実在 YAML/YML を `inventory_drift_hits` として返します
- cross-surface reference のような `../agentic/...` 参照は inventory 対象から外し、
  local eval surface の棚卸しだけを fail-closed に監視します
- あわせて `evals/agentic` / `continuity` / `interface` / `performance` / `safety`
  の README inventory を current tree に同期し、
  `evals/cognitive/README.md` の cross-surface mention を
  local inventory と分離します

## Consequences

- `gap-report --json` の all-zero を、
  eval README inventory まで current であることを含めて解釈できます
- hourly builder は spec だけでなく eval coverage inventory の drift も
  prioritized task で拾えるようになります
- eval README が再び repo-local truth-source として機能し、
  next gap selection の入口が安定します

## Revisit triggers

- eval inventory を hand-maintained README ではなく generated manifest に置き換えたくなった時
- nested eval directories や sidecar artifact まで同じ scanner で棚卸ししたくなった時
- drift hit を file 名だけでなく eval group / subsystem ごとに構造化したくなった時
