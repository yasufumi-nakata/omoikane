# Schemas ── reference runtime が参照する実体 schema

## 実装済み

- `continuity_log_entry.schema`
- `ethics_event.schema`
- `ethics_rule.schema`
- `identity_record.schema`
- `qualia_tick.schema`
- `self_model.schema`
- `connectome_document.schema`
- `memory_crystal_manifest.schema`
- `substrate_allocation.schema`
- `substrate_attestation.schema`
- `substrate_transfer.schema`
- `substrate_release.schema`
- `energy_floor.schema`
- `council_input.yaml`
- `council_session_policy.schema`
- `council_output.yaml`
- `council_argument.yaml`
- `ethics_query.yaml`
- `ethics_decision.yaml`
- `task_node.schema`
- `task_graph_policy.schema`
- `consensus_message.schema`
- `trust_event.schema`
- `trust_snapshot.schema`
- `build_request.yaml`
- `build_artifact.yaml`
- `patch_descriptor.schema`

## 次段階

episodic event / interface handshake は reference runtime の対象が
広がる段階で追加する。

## 形式

JSON Schema 2020-12 または同等の YAML 形式を採用する。

優先順位の根拠は [../catalog.yaml](../catalog.yaml) を参照。
