---
decision_id: parallel-codex-yaoyorozu-dispatch-validation-2026-05-02
status: accepted
date: 2026-05-02
closes_next_gaps:
  - parallel-codex-yaoyorozu-upstream-dispatch-validation
---

# Parallel Codex Yaoyorozu Dispatch Validation

Parallel Codex の Yaoyorozu bridge は、dispatch receipt を単なる patch candidate
digest list として受け取らず、upstream dispatch 自体の構造と coverage を
`yaoyorozu-worker-dispatch-schema-coverage-validation-v1` として検証する。

検証 digest は `parallel_codex_worker_result_receipt` の
`upstream_dispatch_validation_digest` に保存し、さらに `upstream_binding_digest` の
入力にも含める。3 件未満または 4 件超の worker result、result ごとの
patch candidate receipt 欠落、target path 不一致、candidate digest 欠落は
schema-bound のまま `integration_decision=blocked` とする。

raw Yaoyorozu dispatch payload は Parallel Codex receipt に保存しない。bridge 後に
残るのは validation profile、result count、patch candidate receipt count、短い
validation error list、digest、既存の upstream refs/digests のみである。
