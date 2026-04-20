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
- multi-hop relay telemetry を hop 順序・latency・jurisdiction・root visibility ごとに固定する

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
route nonce replay block / multi-hop replay block / live root directory probe /
bounded authority-plane fleet probe を出力する。

## Live Root Directory Federation

rotated handoff では `probe_live_root_directory` により、
live HTTP JSON endpoint から root-directory snapshot を取得し、
その場で trusted root quorum を envelope に束縛する。

| 項目 | 固定値 |
|---|---|
| connectivity transport | `live-http-json-rootdir-v1` |
| payload shape | `distributed_transport_root_directory` |
| quorum source | envelope `trust_root_quorum` と一致 |
| trusted roots | envelope `trust_root_refs` との交差集合 |

- `connectivity_receipt` は `directory_endpoint / response_digest /
  observed_latency_ms / matched_root_count / quorum_satisfied` を必ず保持する
- `key_epoch` は rotated envelope の `accepted_key_epochs` に含まれなければ fail-closed
- `trusted_root_refs` が quorum を満たした時だけ rotated receipt verification に使う
- reference runtime は loopback endpoint でこの handoff を再現し、
  actual remote key server を持ち込まなくても machine-checkable にする

## Authority Plane Fleet

live root directory の次段では `probe_authority_plane` により、
bounded external key-server fleet を probe し、
`root-directory -> authority-plane -> rotated receipt` の束縛を固定する。

| 項目 | 固定値 |
|---|---|
| authority profile | `bounded-key-server-fleet-v1` |
| server transport | `live-http-json-keyserver-v1` |
| server roles | `quorum-notary`, `directory-mirror` |
| quorum source | envelope `trust_root_quorum` と一致 |

- 各 `key_servers` entry は `key_server_ref / server_role / server_endpoint /
  observed_latency_ms / response_digest / matched_root_refs / proof_digest`
  を保持し、authority plane digest に含める
- 各 server の `served_transport_profile` と `key_epoch` は
  envelope / root-directory と一致しなければ fail-closed
- `trusted_root_refs` は reachable server 群が広告した root のうち
  root-directory `trusted_root_refs` と交差するものだけを採用する
- rotated receipt verification は root-directory 直結ではなく、
  authority plane が返した `trusted_root_refs` を使って authenticate する

## Relay telemetry

reference runtime は `capture_relay_telemetry` により、
receipt に束縛された bounded relay observability surface も返す。

| 項目 | 固定値 |
|---|---|
| path_profile | `bounded-relay-observability-v1` |
| hop transport layer | Federation=`mtls`, Heritage=`attested-bridge` |
| hop count source | `receipt.hop_nonce_chain` と同順 |
| end-to-end status | receipt `receipt_status` を mirror |

- `relay_hops` は `relay_id / relay_endpoint / jurisdiction / network_zone /
  hop_nonce / observed_latency_ms / root_refs_seen / route_binding_ref` を保持する
- 最終 hop の `delivery_status` は receipt `receipt_status` と一致し、
  intermediate hop は `forwarded` として残す
- `anti_replay_status` と `replay_guard_status` は receipt authenticity check を mirror し、
  replay-blocked path でも telemetry 自体は残す
- `total_latency_ms` は hop latency 合計で、`max_hops` を超える経路は fail-closed で拒否する

## 参照物

- schema: `specs/schemas/distributed_participant_attestation.schema`
- schema: `specs/schemas/distributed_transport_envelope.schema`
- schema: `specs/schemas/distributed_transport_receipt.schema`
- schema: `specs/schemas/distributed_transport_relay_telemetry.schema`
- schema: `specs/schemas/distributed_transport_root_connectivity_receipt.schema`
- schema: `specs/schemas/distributed_transport_root_directory.schema`
- schema: `specs/schemas/distributed_transport_authority_plane.schema`
- IDL: `specs/interfaces/agentic.distributed_transport.v0.idl`
- eval: `evals/agentic/distributed_transport_authenticity.yaml`
- eval: `evals/agentic/distributed_transport_rotation.yaml`
- eval: `evals/agentic/distributed_transport_relay_telemetry.yaml`
- eval: `evals/agentic/distributed_transport_live_root_directory.yaml`
- eval: `evals/agentic/distributed_transport_authority_plane.yaml`
- decision log: `meta/decision-log/2026-04-19_distributed-transport-attestation.md`
- decision log: `meta/decision-log/2026-04-19_distributed-transport-key-rotation.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-relay-telemetry.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-live-root-directory.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-authority-plane.md`
