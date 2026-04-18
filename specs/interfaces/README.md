# Interfaces (IDL) ── reference runtime で存在必須の IDL

## 実装済み

- `substrate.adapter.v0.idl`
- `kernel.identity.v0.idl`
- `kernel.continuity.v0.idl`
- `kernel.ethics.v0.idl`
- `mind.qualia.v0.idl`
- `mind.self_model.v0.idl`
- `agentic.council.v0.idl`
- `agentic.task_graph.v0.idl`
- `agentic.trust.v0.idl`
- `selfctor.patch_generator.v0.idl`
- `selfctor.diff_eval.v0.idl`

## 次段階

L1 scheduler/broker/termination、L2 connectome/memory、L3 cognitive、L6 interface は
docs 側で設計を深めてから昇格させる。
reference runtime にある reasoning failover も、現時点では内部実装に留め、
IDL 化は service 境界が安定してから行う。

## 形式

各 IDL は `idl_version`, `namespace`, `imports`, `operations`, `events`
を持つ機械可読フォーマットで記述する。
