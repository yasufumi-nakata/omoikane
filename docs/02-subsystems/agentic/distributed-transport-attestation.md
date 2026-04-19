# Distributed Transport Attestation ── Federation / Heritage remote handoff の真正性

`distributed-council-resolution.md` が returned result の binding 規則を固定するのに対し、
ここでは Federation / Heritage へ投げる前段の **remote handoff bundle** を
どう attestation し、どう replay を防ぐかを reference runtime で固定する。

## 目的

- Federation / Heritage review を participant-attested な transport envelope に束縛する
- remote receipt が channel binding と quorum roles を満たしたときだけ `authenticated` にする
- 同一 `route_nonce` の再利用を `replay-blocked` で止める
- key epoch overlap と federated trust-root quorum を bounded contract として固定する
- multi-hop relay をまたぐ `hop_nonce_chain` の再利用を `replay-blocked` で止める

## Federation handoff

`cross-self` proposal は `federation-mtls-quorum-v1` で handoff する。

| 項目 | 固定値 |
|---|---|
| transport_profile | `federation-mtls-quorum-v1` |
| recipient_endpoint | `federation://shared-reality-review` |
| required_roles | `self-liaison x2 + guardian x1` |
| quorum | `3` |
| freshness_window_s | `900` |

- `participant_attestations` は各 `self-liaison` と neutral `guardian` の
  `credential_ref / proof_ref / transport_key_ref` を immutable に保持する
- rotated envelope は `accepted_key_epochs=[1, 2]` の overlap を持ち、
  Federation root `pki-a / pki-b` の quorum を両方確認した receipt だけを `authenticated` にする
- `channel_binding_ref` は `topology_ref + payload_digest + route_nonce` から導出し、
  envelope ごとに一意でなければならない

## Heritage handoff

`interpretive` proposal は `heritage-attested-review-v1` で handoff する。

| 項目 | 固定値 |
|---|---|
| transport_profile | `heritage-attested-review-v1` |
| recipient_endpoint | `heritage://interpretive-review` |
| required_roles | `cultural-representative x2 + legal-advisor + ethics-committee` |
| quorum | `4` |
| freshness_window_s | `1800` |

- clause-bound review のため `referenced_clauses` が空なら envelope を発行しない
- Heritage 側は固定 reviewer role をすべて attest しない限り receipt を受理しない
- `hop_nonce_chain` は relay ごとの nonce 列として保持し、
  別 envelope で再利用された場合も `multi_hop_replay_status=blocked` になる

## Receipt verification

remote endpoint から返る receipt は次を同時に満たしたときだけ `authenticated` になる。

1. `channel_binding_ref` が envelope と一致する
2. `participant_bindings` が required roles を満たす
3. attested participant 数が quorum 以上である
4. `route_nonce` が未使用である
5. `verified_root_refs` が `trust_root_quorum` を満たす
6. `key_epoch` が `accepted_key_epochs` に含まれる
7. `hop_nonce_chain` が未使用で、かつ `max_hops` 以内である

同一 `route_nonce` を再利用した receipt は、他が正しくても `replay-blocked` になる。
同一 `hop_nonce_chain` を別 envelope で再利用した receipt も `replay-blocked` になる。

reference runtime では `distributed-transport-demo` が
Federation handoff / rotated federation handoff / Heritage handoff /
route nonce replay block / multi-hop replay block を出力する。

## 参照物

- schema: `specs/schemas/distributed_participant_attestation.schema`
- schema: `specs/schemas/distributed_transport_envelope.schema`
- schema: `specs/schemas/distributed_transport_receipt.schema`
- IDL: `specs/interfaces/agentic.distributed_transport.v0.idl`
- eval: `evals/agentic/distributed_transport_authenticity.yaml`
- eval: `evals/agentic/distributed_transport_rotation.yaml`
- decision log: `meta/decision-log/2026-04-19_distributed-transport-attestation.md`
- decision log: `meta/decision-log/2026-04-19_distributed-transport-key-rotation.md`
