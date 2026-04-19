# Distributed Council Resolution ── Federation / Heritage の returned result

`multi-council-trigger.md` が **request 発火** を固定する文書なのに対し、
ここでは external pending の先で返ってくる **returned result** を
reference runtime でどう扱うかを固定する。

## 目的

- `cross-self` 議題の advisory Local decision を Federation returned result で binding 化する
- `interpretive` 議題の blocked Local decision を Heritage returned result で確定する
- Federation と Heritage が衝突したときは local bind を再開せず human governance へ送る

## Federation review

`cross-self` proposal は Federation Council returned result を待つ。

| 項目 | 固定値 |
|---|---|
| policy_id | `federation-shared-reality-v1` |
| quorum | `participant_count + 1` |
| 必須役割 | 各 identity の `self-liaison` + 中立 `guardian` |
| veto policy | `self-liaison-unanimous-reject` |
| local binding status | `advisory` |

- 全 `self-liaison` が `reject` / `veto` した場合は `binding-rejected`
- それ以外は weighted-majority で `binding-approved` / `binding-rejected`
- Local が `approved` でも Federation が reject したら `federation-overrides-local`

## Heritage review

`interpretive` proposal は Heritage Council returned result を待つ。

| 項目 | 固定値 |
|---|---|
| policy_id | `heritage-interpretive-review-v1` |
| quorum | `4` |
| 必須役割 | `culture-a`, `culture-b`, `legal-advisor`, `ethics-committee` |
| veto policy | `ethics-committee-single-veto` |
| local binding status | `blocked` |

- `ethics-committee` の `veto` は単独で `binding-rejected`
- veto が無い場合は weighted-majority で `binding-approved` / `binding-rejected`
- Local が `approved` でも Heritage が reject したら `heritage-overrides-local`

## Cross-tier conflict

Federation と Heritage の returned result が同一 change-set 上で衝突した場合:

- Local binding を再開しない
- `conflict-escalation` を記録する
- final outcome は `escalate-human-governance`
- `external_resolution_refs` に衝突した external result の ref を残す

reference runtime では `distributed-council-demo` が
Federation binding / Heritage veto / cross-tier conflict escalation を 1 回ずつ出力する。

## 参照物

- schema: `specs/schemas/distributed_council_resolution.schema`
- IDL: `specs/interfaces/agentic.council.v0.idl`
- eval: `evals/agentic/distributed_council_resolution.yaml`
- decision log: `meta/decision-log/2026-04-19_distributed-council-resolution.md`
