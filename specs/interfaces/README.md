# Interfaces (IDL) ── reference runtime で存在必須の IDL

## 実装済み

- `substrate.adapter.v0.idl`
- `kernel.identity.v0.idl`
- `kernel.scheduler.v0.idl`
- `kernel.termination.v0.idl`
- `kernel.continuity.v0.idl`
- `kernel.ethics.v0.idl`
- `mind.memory.v0.idl`
- `mind.semantic.v0.idl`
- `mind.procedural.v0.idl`
- `mind.procedural_writeback.v0.idl`
- `mind.qualia.v0.idl`
- `mind.self_model.v0.idl`
- `agentic.council.v0.idl`
- `agentic.task_graph.v0.idl`
- `agentic.trust.v0.idl`
- `cognitive.affect.v0.idl`
- `cognitive.attention.v0.idl`
- `governance.amendment.v0.idl`
- `governance.oversight.v0.idl`
- `governance.naming.v0.idl`
- `interface.bdb.v0.idl`
- `interface.ewa.v0.idl`
- `interface.wms.v0.idl`
- `selfctor.patch_generator.v0.idl`
- `selfctor.diff_eval.v0.idl`
- `selfctor.sandboxer.v0.idl`

## 次段階

L2 procedural skill execution enactment、L3 volition / imagination、
L6 sensory loopback や richer distributed surfaces は
docs 側で設計を深めてから昇格させる。
reference runtime にある reasoning failover も、現時点では内部実装に留め、
IDL 化は service 境界が安定してから行う。

## 形式

各 IDL は `idl_version`, `namespace`, `imports`, `operations`, `events`
を持つ機械可読フォーマットで記述する。
