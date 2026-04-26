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

## reference runtime の扱い

- `interface.collective.v0.idl` を導入し、
  `register_collective / open_merge_session / close_merge_session / dissolve_collective`
  の 4 op を固定する
- `collective_record.schema`、`collective_merge_session.schema`、
  `collective_dissolution_receipt.schema` を追加する
- `collective-demo` は IMC `merge_thought`、WMS divergence、private escape、
  identity confirmation、schema-bound dissolution receipt、
  member recovery proof binding を 1 シナリオで smoke する
- `evals/interface/collective_merge_reversibility.yaml` は
  reversible merge window と member recovery requirement を監査する
- `evals/interface/collective_dissolution_receipt.yaml` は
  dissolution receipt の public schema、全 member confirmation、
  IdentityConfirmation digest binding、digest-only audit ref を監査する

## 不変条件

1. **distinct identity** ── Collective は構成員とは別 ID で記録する
2. **bounded merge** ── merge は 10 秒以内に cap する
3. **escape freedom** ── divergence 後の private reality 退避を阻害しない
4. **recovery first** ── dissolution 前に全 member の identity confirmation を必須化
5. **digest-only recovery proof** ── dissolution receipt は IdentityConfirmation profile の raw body ではなく digest proof のみを持つ
6. **no silent persistence** ── active merge 無しで Collective を存続させない

## 関連

- [imc-protocol.md](imc-protocol.md)
- [wms-spec.md](wms-spec.md)
- [../../05-research-frontiers/inter-mind-merge.md](../../05-research-frontiers/inter-mind-merge.md)
- [../../05-research-frontiers/collective-personhood.md](../../05-research-frontiers/collective-personhood.md)
