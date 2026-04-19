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
- `cognitive.reasoning.v0.idl`
- `agentic.consensus_bus.v0.idl`
- `agentic.council.v0.idl`
- `agentic.distributed_transport.v0.idl`
- `agentic.cognitive_audit.v0.idl`
- `agentic.task_graph.v0.idl`
- `agentic.trust.v0.idl`
- `cognitive.affect.v0.idl`
- `cognitive.attention.v0.idl`
- `cognitive.volition.v0.idl`
- `cognitive.imagination.v0.idl`
- `cognitive.language.v0.idl`
- `cognitive.metacognition.v0.idl`
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

L2 procedural skill execution enactment、
L6 sensory loopback、
live PKI federation / transport key rotation / multi-hop anti-replay を伴う
richer distributed surfaces は docs 側で設計を深めてから昇格させる。

## 形式

各 IDL は `idl_version`, `namespace`, `imports`, `operations`, `events`
を持つ機械可読フォーマットで記述する。
