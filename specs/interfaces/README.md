# Interfaces (IDL) ── reference runtime で存在必須の IDL

## 実装済み

- `agentic.cognitive_audit.v0.idl`
- `agentic.cognitive_audit_governance.v0.idl`
- `agentic.consensus_bus.v0.idl`
- `agentic.council.v0.idl`
- `agentic.distributed_transport.v0.idl`
- `agentic.task_graph.v0.idl`
- `agentic.trust.v0.idl`
- `agentic.yaoyorozu.v0.idl`
- `cognitive.affect.v0.idl`
- `cognitive.attention.v0.idl`
- `cognitive.imagination.v0.idl`
- `cognitive.language.v0.idl`
- `cognitive.metacognition.v0.idl`
- `cognitive.perception.v0.idl`
- `cognitive.reasoning.v0.idl`
- `cognitive.volition.v0.idl`
- `governance.amendment.v0.idl`
- `governance.naming.v0.idl`
- `governance.oversight.v0.idl`
- `interface.bdb.v0.idl`
- `interface.collective.v0.idl`
- `interface.ewa.v0.idl`
- `interface.imc.v0.idl`
- `interface.sensory_loopback.v0.idl`
- `interface.wms.v0.idl`
- `kernel.broker.v0.idl`
- `kernel.continuity.v0.idl`
- `kernel.ethics.v0.idl`
- `kernel.identity.v0.idl`
- `kernel.scheduler.v0.idl`
- `kernel.termination.v0.idl`
- `mind.memory.v0.idl`
- `mind.memory_replication.v0.idl`
- `mind.memory_edit.v0.idl`
- `mind.procedural.v0.idl`
- `mind.procedural_actuation.v0.idl`
- `mind.procedural_writeback.v0.idl`
- `mind.qualia.v0.idl`
- `mind.self_model.v0.idl`
- `mind.semantic.v0.idl`
- `mind.skill_enactment.v0.idl`
- `mind.skill_execution.v0.idl`
- `selfctor.design_reader.v0.idl`
- `selfctor.diff_eval.v0.idl`
- `selfctor.enactment.v0.idl`
- `selfctor.patch_generator.v0.idl`
- `selfctor.rollback.v0.idl`
- `selfctor.rollout.v0.idl`
- `selfctor.sandboxer.v0.idl`
- `substrate.adapter.v0.idl`

## 次段階

inventory backlog は解消済みです。
remote authority-cluster seed review policy は
`agentic.distributed_transport.v0.idl` の `build_authority_cluster_seed_review_policy`
operation と public schema へ昇格済みです。

## 形式

各 IDL は `idl_version`, `namespace`, `imports`, `operations`, `events`
を持つ機械可読フォーマットで記述する。
