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
bounded authority-plane fleet probe / authority-plane churn reconciliation /
bounded authority route target discovery /
non-loopback mTLS authority route trace を出力する。

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
- authority plane は `overlap-safe-authority-handoff-v1` を固定 churn profile とし、
  `authority_status=draining` の server が残る間も各 `trusted_root_ref` に
  少なくとも 1 つの `authority_status=active` server を要求する
- `root_coverage` は root ごとに `active_server_refs / draining_server_refs /
  coverage_status` (`stable` or `handoff-ready`) を保持し、
  draining overlap が replacement server で吸収できていることを machine-checkable にする
- rotated receipt verification は root-directory 直結ではなく、
  authority plane が返した `trusted_root_refs` を使って authenticate する

authority membership が実際に変わる時は `reconcile_authority_churn` により、
overlap snapshot と post-churn snapshot を
`distributed_transport_authority_churn_window` に束縛する。

- `retained_server_refs` は churn 中も残った key server を示し、
  membership change が起きた場合は少なくとも 1 server の overlap を要求する
- `removed_server_refs` は previous snapshot で `draining` だった server だけを許容し、
  fail-closed で abrupt removal を防ぐ
- `continuity_guard` は overlap count / draining removal / quorum maintained を固定し、
  `status=quorum-maintained` だけを rotated receipt 前段の valid churn outcome とする

## Authority route target discovery

stable な authority plane に対しては
`discover_authority_route_targets` により、
reviewed `route_catalog` を active authority-plane member へ束縛し、
trace 前段の discovery receipt を固定する。

| 項目 | 固定値 |
|---|---|
| discovery profile | `bounded-authority-route-target-discovery-v1` |
| target scope | `active-only` |
| authority cluster scope | single `authority_cluster_ref` |
| source of truth | stable authority plane + reviewed route catalog |

- discovery は `authority_plane` の active member 全件を `key_server_ref` 単位で覆わなければ fail-closed
- 各 discovered target は `server_endpoint / server_name / remote_host_ref /
  remote_host_attestation_ref / authority_cluster_ref / remote_jurisdiction /
  remote_network_zone` を持ち、さらに authority plane 由来の
  `server_role / authority_status / matched_root_refs` を retain する
- `authority_cluster_ref` は discovery receipt 全体で 1 種類に固定し、
  `distinct_remote_host_count` は cross-host binding の前提観測として保持する
- route trace は raw `route_targets` ではなく
  `route_target_discovery_ref / route_target_discovery_digest` に束縛され、
  discovery receipt が `all_active_members_targeted=true` の時だけ進める

## Non-loopback mTLS authority route trace

stable な authority plane に対しては
`trace_non_loopback_authority_routes` により、
actual non-loopback mTLS route と socket-level trace を
current authority snapshot へ束縛する。

| 項目 | 固定値 |
|---|---|
| trace profile | `non-loopback-mtls-authority-route-v1` |
| socket trace profile | `mtls-socket-trace-v1` |
| cross-host binding profile | `attested-cross-host-authority-binding-v1` |
| tls server name | `authority.local` |
| route coverage | stable authority plane の全 reachable member |

- 各 route target は `remote_host_ref / remote_host_attestation_ref /
  authority_cluster_ref / remote_jurisdiction / remote_network_zone` を必須にし、
  各 route binding へ同じ binding を焼き付ける
- 各 route binding は `key_server_ref / server_endpoint / server_name /
  remote_host_ref / remote_host_attestation_ref / authority_cluster_ref /
  route_binding_ref / matched_root_refs / mtls_status` を保持する
- `socket_trace` は `local_ip / local_port / remote_ip / remote_port /
  non_loopback / tls_version / cipher_suite / peer_certificate_fingerprint /
  client_certificate_fingerprint / request_bytes / response_bytes /
  http_status / response_digest / connect_latency_ms /
  tls_handshake_latency_ms / round_trip_latency_ms` を保持する
- `os_observer_receipt` は `netstat` / `lsof` が live TCP tuple を観測した証跡として
  `observed_sources / connection_states / owning_pid / tuple_digest /
  remote_host_ref / remote_host_attestation_ref / authority_cluster_ref /
  host_binding_digest` を保持し、
  少なくとも 1 source で tuple が観測された時だけ route trace を `authenticated` に進める
- trace receipt 自体は `route_target_discovery_ref / route_target_discovery_digest /
  route_target_discovery_profile=bounded-authority-route-target-discovery-v1` を保持し、
  discovery receipt と authority plane の provenance を同時に固定する
- `cross_host_verified` は traced authority-plane member ごとに distinct な
  `remote_host_ref` が同一 `authority_cluster_ref` の下で束縛された時だけ true になる
- `response_digest` は authority-plane snapshot の per-server digest と一致しなければ fail-closed
- remote endpoint が loopback だった場合や mTLS が成立しない場合、
  trace 全体は `authenticated` にならない
- reference runtime は local machine 上の non-loopback address に bind した
  mTLS server を使い、actual route trace 自体は same host 上で再現しつつ、
  route target の host/cluster binding を通じて bounded な cross-host authority routing まで
  machine-checkable にする

## Packet capture export

authenticated な route trace に対しては
`export_authority_route_packet_capture` により、
trace-bound な PCAP artifact を export し、
route tuple と payload length を packet-capture surface へ束縛する。

| 項目 | 固定値 |
|---|---|
| capture profile | `trace-bound-pcap-export-v1` |
| artifact format | `pcap` |
| readback profile | `pcap-readback-v1` |
| OS-native readback | `tcpdump-readback-v1` |

- export は各 traced route ごとに `outbound-request` と `inbound-response` の
  2 packet を持ち、`local_ip / local_port / remote_ip / remote_port` と
  request/response byte count を保持する
- in-process readback は PCAP から tuple と payload length を再構成し、
  route trace の socket evidence と一致した時だけ `readback_verified=true` になる
- `tcpdump` が利用可能な環境では readback を追加で走らせ、
  tuple ごとの line match が揃った時だけ `os_native_readback_ok=true` にする
- export は live privileged sniffing ではなく、
  authenticated route trace を packet-capture artifact へ落とし直す bounded contract である

## Privileged capture acquisition

verified な packet export に対しては
`acquire_privileged_interface_capture` により、
delegated broker が発行した live capture lease と command preview を
route trace / packet export / resolved interface へ束縛する。

| 項目 | 固定値 |
|---|---|
| acquisition profile | `bounded-live-interface-capture-acquisition-v1` |
| privilege mode | `delegated-broker` |
| capture tool preview | `tcpdump` |

- acquisition は traced route の `local_ip` 群を 1 つの host interface へ解決し、
  その interface 名を receipt に固定する
- capture filter は traced route の双方向 tuple を全て束縛し、
  `filter_digest` と `route_binding_refs` が broker lease に immutable binding される
- delegated broker は `approved_interface` / `approved_filter_digest` /
  `route_binding_refs` を echo しつつ `lease_ref` と `broker_attestation_ref` を返す
- `capture_command` は `tcpdump` / resolved interface / exact filter を含む preview として固定し、
  actual live capture 自体は repo 外の broker 実行面へ委譲する
- residual future work は broad な cross-host authority routing 不在ではなく、
  bounded reviewed route catalog の外側にある unbounded remote authority-cluster discovery へ絞られる

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
- schema: `specs/schemas/distributed_transport_authority_route_target_discovery.schema`
- schema: `specs/schemas/distributed_transport_authority_churn_window.schema`
- schema: `specs/schemas/distributed_transport_os_observer_receipt.schema`
- schema: `specs/schemas/distributed_transport_authority_route_trace.schema`
- schema: `specs/schemas/distributed_transport_packet_capture_export.schema`
- schema: `specs/schemas/distributed_transport_privileged_capture_acquisition.schema`
- IDL: `specs/interfaces/agentic.distributed_transport.v0.idl`
- eval: `evals/agentic/distributed_transport_authenticity.yaml`
- eval: `evals/agentic/distributed_transport_rotation.yaml`
- eval: `evals/agentic/distributed_transport_relay_telemetry.yaml`
- eval: `evals/agentic/distributed_transport_live_root_directory.yaml`
- eval: `evals/agentic/distributed_transport_authority_plane.yaml`
- eval: `evals/agentic/distributed_transport_authority_route_target_discovery.yaml`
- eval: `evals/agentic/distributed_transport_authority_churn.yaml`
- eval: `evals/agentic/distributed_transport_authority_route_trace.yaml`
- eval: `evals/agentic/distributed_transport_packet_capture_export.yaml`
- eval: `evals/agentic/distributed_transport_privileged_capture_acquisition.yaml`
- decision log: `meta/decision-log/2026-04-19_distributed-transport-attestation.md`
- decision log: `meta/decision-log/2026-04-19_distributed-transport-key-rotation.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-relay-telemetry.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-live-root-directory.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-authority-plane.md`
- decision log: `meta/decision-log/2026-04-20_distributed-transport-authority-churn.md`
- decision log: `meta/decision-log/2026-04-22_distributed-transport-route-target-discovery.md`
- decision log: `meta/decision-log/2026-04-21_distributed-transport-non-loopback-route-trace.md`
- decision log: `meta/decision-log/2026-04-21_distributed-transport-os-observer-receipt.md`
- decision log: `meta/decision-log/2026-04-21_distributed-transport-pcap-export.md`
- decision log: `meta/decision-log/2026-04-21_distributed-transport-privileged-capture-acquisition.md`
