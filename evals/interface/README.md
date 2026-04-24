# Interface Evals

L6 interface 境界の reference runtime 評価。

## 評価項目

### BDB Fail-Safe Reversibility
閉ループ cycle の latency budget、置換比率の増減、fail-safe fallback 後の
生体自律復帰をまとめて確認する。

### IMC Disclosure Floor
peer attestation、forward secrecy、narrow disclosure floor、
sealed-field redaction、summary+digest-only audit、
emergency disconnect をまとめて確認する。

### WMS Private Reality Escape
minor diff の shared reconciliation、major diff での private reality escape 提示、
malicious inject の guardian isolation をまとめて確認する。

### WMS Physics Rules Revert
shared reality の physics_rules 改変が満場一致、Guardian attestation、
rollback token、first-class revert receipt を通して baseline rules へ戻ることを確認する。

### WMS Participant Approval Transport
physics_rules 改変の participant approval が静的な id list だけでなく、
IMC handshake / message digest / approval subject digest / forward secrecy に
束縛された transport receipt を持つことを確認する。

### WMS Approval Collection Scaling
3 participant の shared_reality approval を ordered digest set と
`max_batch_size=2` の bounded batch に集約し、physics_rules change が
complete collection receipt へ束縛されることを確認する。

### WMS Distributed Approval Fanout
complete approval collection を Federation distributed transport envelope /
authenticated receipt / participant approval result digest の ordered set へ
fan-out し、physics_rules change が同じ fanout digest を参照することを確認する。

### Sensory Loopback Guard
coherent avatar feedback の body coherence、high-drift bundle の guardian hold、
safe baseline からの stabilize 復帰、qualia binding ref をまとめて確認する。

## 実装済み eval

- `bdb_fail_safe_reversibility.yaml`
- `collective_merge_reversibility.yaml`
- `imc_disclosure_floor.yaml`
- `sensory_loopback_artifact_family.yaml`
- `sensory_loopback_guard.yaml`
- `sensory_loopback_multi_self_arbitration.yaml`
- `wms_approval_collection_scaling.yaml`
- `wms_distributed_approval_fanout.yaml`
- `wms_participant_approval_transport.yaml`
- `wms_physics_rules_revert.yaml`
- `wms_private_reality_escape.yaml`
