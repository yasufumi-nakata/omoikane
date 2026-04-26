# Collective Identity

L6 Interface の実験的サブシステム。`merge_thought` を mode 名だけで終わらせず、
**短時間・可逆・post-disconnect recovery 必須** の bounded contract として固定する。

## 問題設定

- 複数自我が高密度通信した時、セッション単位で Collective をどう扱うか
- merge 中の shared reality divergence が起きた時、どう安全側へ退避するか
- 切断後に各構成員が独立した subjectivity を回復したことをどう確認するか

reference runtime v0 は哲学的な人格成立を主張しない。
代わりに、

1. IdentityRegistry 上の **distinct collective ID**
2. `merge_thought` に限った **10 秒以内の bounded merge**
3. WMS の **private_reality escape**
4. 切断後の **all-members identity confirmation**
5. その後の **collective dissolution**

だけを machine-readable に固定する。

## bounded policy

```yaml
collective_profile:
  formation_mode: bounded-collective-merge-v0
  member_count_bounds:
    min: 2
    max: 4
  governance_mode: meta-council
  merge_policy:
    merge_mode: merge_thought
    max_duration_seconds: 10.0
    council_witness_required: true
    federation_attestation_required: true
    guardian_observation_required: true
    post_disconnect_identity_confirmation: all-members
    escape_route: private_reality
```

## contract

### register_collective

- 構成員 2-4 名のみ
- member ID と distinct な collective ID を IdentityRegistry に登録
- Council witness / Federation attestation / Guardian observe を必須化
- governance mode は `meta-council` に固定

### open_merge_session

- backing transport は IMC `merge_thought`
- shared world handle は WMS session を必須化
- merge は 1 collective あたり 1 session のみ
- requested duration は受理するが、granted duration は最大 10 秒へ cap

### close_merge_session

- major divergence 後でも `private_reality` 退避を阻害しない
- `time_in_merge_seconds > granted_duration_seconds` は `recovery-required`
- 構成員の identity confirmation が 1 人でも落ちたら `recovery-required`

### dissolve_collective

- active merge session が残っている間は不可
- 構成員全員の confirmation が揃って初めて `dissolved`
- collective 側の目的は終了し、各構成員は独立 subjectivity へ戻る
- `collective_dissolution_receipt.schema` に合う
  first-class receipt を返し、`schema_version`、全 member confirmation、
  `member_recovery_required=true`、digest-only `audit_event_ref` を束縛する
- `collective-dissolution-identity-confirmation-binding-v1` により、
  各 member の `multidimensional-identity-confirmation-v1` profile から
  confirmation digest、witness quorum status、
  self-report/witness consistency digest だけを receipt へ縮約する
- raw identity confirmation profile は dissolution receipt に保存しない
- `collective-dissolution-recovery-verifier-transport-v1` により、
  dissolution receipt digest と各 member recovery proof を remote reviewer verifier
  transport receipt に束縛する
- raw verifier request / response payload は保存せず、challenge digest、
  request / response digest、transport exchange digest だけを保持する
- `collective-recovery-non-loopback-route-trace-binding-v1` により、
  recovery verifier transport receipt set を authenticated non-loopback
  distributed authority-route trace、cross-host route binding、OS observer digest に束縛する
- raw route payload は保存せず、route binding ref、socket response digest、
  remote host attestation ref、member route binding digest だけを保持する
- `collective-recovery-route-trace-capture-export-v1` により、
  recovery route trace binding を verified pcap export と delegated-broker
  privileged capture acquisition に束縛する
- raw packet body は保存せず、packet capture artifact digest、readback digest、
  capture filter digest、member capture binding digest だけを保持する
- `collective-dissolution-external-registry-sync-v1` により、
  recovery capture export binding を external legal registry と governance registry の
  digest-only entry / submission / acknowledgement receipt へ同期する
- `collective-external-registry-ack-quorum-v1` により、legal / governance の
  2 registry acknowledgement を 2 jurisdiction quorum として digest-only に束縛する
- `collective-external-registry-ack-route-trace-v1` により、その acknowledgement quorum を
  authenticated non-loopback authority-route trace と OS observer evidence に束縛する
- `collective-external-registry-ack-route-capture-export-v1` により、その ack route trace を
  verified pcap export と delegated-broker privileged capture acquisition に束縛する
- `collective-external-registry-ack-live-endpoint-probe-v1` により、legal / governance
  registry acknowledgement を live HTTP JSON endpoint response digest、HTTP status、
  probe latency、endpoint ref、signed response envelope digest に束縛する
- `collective-external-registry-ack-mtls-client-certificate-proof-v1` により、
  live acknowledgement endpoint probe を mTLS client certificate ref、certificate
  fingerprint、certificate chain digest、client CA ref、response digest に束縛する
- `collective-external-registry-ack-client-certificate-freshness-revocation-v1`
  により、同じ probe を client certificate revocation registry ref、
  OCSP-style response digest、not-revoked status、24h freshness window に束縛する
- `collective-external-registry-ack-client-certificate-lifecycle-v1` により、
  同じ probe を previous certificate ref、retirement digest、renewal event digest、
  `renewed` status に束縛し、stale / revoked lifecycle は fail-closed にする
- `collective-external-registry-ack-client-certificate-rollover-chain-v1` により、
  ancestor -> previous -> current の 3 generation chain を固定し、
  `collective-external-registry-ack-client-certificate-ct-log-readback-v1` で
  CT-style log ref、leaf digest、inclusion proof digest を同じ probe に束縛する
- raw dissolution payload、raw registry payload、raw ack payload、raw ack-route payload、raw endpoint payload、raw response signature payload、raw client certificate payload、raw client certificate freshness payload、raw client certificate lifecycle payload、raw client certificate lifecycle chain payload、raw CT log payload、raw packet body は保存しない

## reference runtime の扱い

- `interface.collective.v0.idl` を導入し、
  `register_collective / open_merge_session / close_merge_session / dissolve_collective /
  bind_recovery_verifier_transport / bind_recovery_verifier_route_trace /
  bind_recovery_route_trace_capture_export / sync_dissolution_external_registry /
  bind_external_registry_ack_endpoint_probes`
  の 9 op を固定する
- `collective_record.schema`、`collective_merge_session.schema`、
  `collective_dissolution_receipt.schema`、
  `collective_recovery_verifier_transport_binding.schema`、
  `collective_recovery_route_trace_binding.schema`、
  `collective_recovery_capture_export_binding.schema`、
  `collective_external_registry_sync.schema` を追加する
- `collective-demo` は IMC `merge_thought`、WMS divergence、private escape、
  identity confirmation、schema-bound dissolution receipt、
  member recovery proof binding、remote verifier transport binding、
  non-loopback authority-route trace binding、packet capture export binding、
  external legal/governance registry sync、ack route capture export binding、
  live registry acknowledgement endpoint probe binding、mTLS client certificate
  proof binding、client certificate freshness/revocation proof binding、
  client certificate lifecycle renewal proof binding、
  3 generation client certificate rollover chain proof binding、
  CT-style certificate log readback proof binding を
  1 シナリオで smoke する
- `evals/interface/collective_merge_reversibility.yaml` は
  reversible merge window と member recovery requirement を監査する
- `evals/interface/collective_dissolution_receipt.yaml` は
  dissolution receipt の public schema、全 member confirmation、
  IdentityConfirmation digest binding、digest-only audit ref を監査する
- `evals/interface/collective_recovery_verifier_transport.yaml` は
  dissolution receipt digest、member recovery binding digest、
  per-member verified transport receipt、raw verifier payload redaction を監査する
- `evals/interface/collective_recovery_route_trace_binding.yaml` は
  recovery verifier transport receipt set と authenticated non-loopback route trace の
  digest-only binding、cross-host route coverage、raw route payload redaction を監査する
- `evals/interface/collective_recovery_capture_export_binding.yaml` は
  route trace binding と verified pcap export / delegated privileged capture acquisition の
  route-ref alignment、member capture digest、raw packet body redaction を監査する
- `evals/interface/collective_external_registry_sync.yaml` は
  capture export binding と external legal / governance registry digest、
  registry entry、submission、acknowledgement receipt、2 jurisdiction ack quorum の
  束縛、ack route trace binding、ack route capture export binding、
  live acknowledgement endpoint probe binding、mTLS client certificate proof binding、
  client certificate freshness/revocation proof binding、
  client certificate lifecycle renewal proof binding、
  client certificate rollover chain proof binding、
  client certificate CT-style readback proof binding、
  raw registry / ack / ack-route / endpoint / client certificate / freshness / lifecycle / lifecycle chain / CT log payload redaction を監査する

## 不変条件

1. **distinct identity** ── Collective は構成員とは別 ID で記録する
2. **bounded merge** ── merge は 10 秒以内に cap する
3. **escape freedom** ── divergence 後の private reality 退避を阻害しない
4. **recovery first** ── dissolution 前に全 member の identity confirmation を必須化
5. **digest-only recovery proof** ── dissolution receipt は IdentityConfirmation profile の raw body ではなく digest proof のみを持つ
6. **packet-body redaction** ── recovery capture binding は raw packet body を保存せず digest/readback/route ref だけを持つ
7. **remote verifier transport binding** ── recovery proof は reviewer verifier transport digest set に束縛する
8. **external registry redaction** ── registry sync は legal/governance registry digest、acknowledgement quorum digest、ack route trace digest、ack endpoint response digest、mTLS client certificate proof digest、client certificate freshness proof digest、client certificate lifecycle proof digest、certificate lifecycle chain proof digest、CT-style readback digest だけを保持し、raw registry / ack / ack-route / endpoint / client certificate / freshness / lifecycle / lifecycle chain / CT log payload を保存しない
9. **no silent persistence** ── active merge 無しで Collective を存続させない

## 関連

- [imc-protocol.md](imc-protocol.md)
- [wms-spec.md](wms-spec.md)
- [../../05-research-frontiers/inter-mind-merge.md](../../05-research-frontiers/inter-mind-merge.md)
- [../../05-research-frontiers/collective-personhood.md](../../05-research-frontiers/collective-personhood.md)
