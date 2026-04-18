# 2026-04-18 Multi-Council Trigger

## Context

`Council` は単一セッションの weighted-majority / guardian veto までは reference runtime に存在したが、
複数 identity をまたぐ議題や規約解釈議題をどの時点で外部 Council へ送るかが未固定だった。
`meta/open-questions.md` でも「多 Council 化のトリガ条件」が未解決として残っていた。

## Decision

reference runtime は次の deterministic trigger を採用する。

1. `target_identity_ids` が単一で、`ethics_axiom` / `identity_axiom` / `governance` clause を参照しない提案は `local`
2. `target_identity_ids` が 2 件以上で、上記 interpretive clause を含まない提案は `cross-self`
3. interpretive clause を参照し、`target_identity_ids` が単一の提案は `interpretive`
4. 上記が複数同時成立、またはどれにも該当しない提案は `ambiguous`

`cross-self` は Federation Council 要求、`interpretive` は Heritage Council 要求へ外部化し、
`ambiguous` は local binding decision を停止して再分類待ちにする。

## Consequences

- `agentic.council.v0.idl` に Federation / Heritage convene contract を追加した
- `council_topology.schema` で routing snapshot を serialize できるようにした
- `multi-council-demo` と `evals/agentic/multi_council_externalization.yaml` で cross-self /
  interpretive / ambiguous の 3 経路を smoke できるようにした
- Local Council 自体は引き続き in-repo 実装だが、外部 Council は `external-pending` で止め、
  distributed 実装は将来課題として分離した
