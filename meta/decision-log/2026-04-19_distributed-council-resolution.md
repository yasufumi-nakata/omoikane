# 2026-04-19 Distributed Council Resolution

## Context

`multi-council-demo` までは Federation / Heritage への request 発火だけが reference runtime にあり、
returned result が返ってきた後に Local advisory / blocked state をどう binding 化するかは
README future-work に残っていた。
このままでは `cross-self` と `interpretive` の distributed surface が docs-only のままで、
external pending の先でどの tier が最終優先権を持つかを machine-readable に検証できなかった。

## Decision

reference runtime は `distributed_council_resolution` contract を導入し、次を固定する。

1. `cross-self` proposal は `federation-shared-reality-v1` で解決する
2. Federation quorum は `participant_count + 1`、veto policy は `self-liaison-unanimous-reject`
3. `interpretive` proposal は `heritage-interpretive-review-v1` で解決する
4. Heritage quorum は `4`、`ethics-committee` の `veto` は単独で binding reject を成立させる
5. Federation と Heritage の returned result が衝突したときは local bind を再開せず
   `escalate-human-governance` を返す

## Consequences

- `agentic.council.v0.idl` は request-only ではなく returned result / reconciliation まで含む
- `distributed-council-demo` で Federation binding / Heritage veto / cross-tier conflict escalation
  を JSON で確認できる
- `specs/schemas/distributed_council_resolution.schema` と
  `evals/agentic/distributed_council_resolution.yaml` が distributed council surface の
  truth source になる
- 残課題は participant attestation、transport authenticity、実在 remote transport 上の
  replay resistance であり、repo 内 reference runtime は resolution policy までを責務とする
