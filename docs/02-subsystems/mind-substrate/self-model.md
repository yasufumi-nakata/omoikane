# Self Model

「自分はこういう人間である」という自己認識のネットワーク。
人格・価値観・好み・自伝的物語を含む。

## 構成要素

```yaml
SelfModel:
  identity_core:           # 中核アイデンティティ
    name: <自称＞
    pronouns: <代名詞>
    autobiographical_arc: <自伝的物語のサマリ>
  values:                  # 価値観（重み付き）
    - { value: 'honesty', weight: 0.9, last_revised: <ts> }
    - { value: 'autonomy', weight: 0.8, last_revised: <ts> }
  preferences:             # 好み
    - { domain: 'food', items: [...] }
    - { domain: 'aesthetics', items: [...] }
  relationships:           # 対人関係グラフ
    - { other_id: <id>, kind: 'family|friend|colleague|stranger', strength: 0.7 }
  capabilities:            # 自己評価された能力
    - { skill: 'mathematical_reasoning', self_rating: 0.6 }
  beliefs_about_self:      # 自分についての信念
    - "私は内向的だ"
    - "私は変化を好む"
  trauma_loci:             # 触れにくい領域（参照に注意）
    - { ref: <memory_ref>, sensitivity: 0.9 }
```

## 更新原則

1. **緩慢更新が基本** ── 価値観は時間をかけて変化する。急変は要注意。
2. **Council 監視** ── SelfModel の急変は人格乗っ取り or 病理の徴候。Council が検知する。
3. **本人観察** ── 本人が自分の SelfModel を読める権利を持つ。

reference runtime では `bounded-self-model-monitor-v1` を採用し、
divergence を `values` / `goals` / `traits` の 3 成分平均で計算する。
adjacent snapshot 間の divergence が `0.35` 以上なら `abrupt_change=true` とし、
それ未満は stable drift として扱う。

## 急変検知

```
急変判定:
  - reference runtime は `values` / `goals` / `traits` の equal-weight divergence を使う
  - adjacent snapshot の divergence が `0.35` 以上 → flag
  - stable drift は `0.35` 未満に留め、history は append-only で保持する
```

flag された変化は Council が本人に確認する。**変化の自由は損なわず、外部からの操作のみ拒否する** バランス。

## SelfModel と他層の関係

- L3 Reasoning は SelfModel を「私はこう判断する人間だ」の前提として参照
- L3 Volition は SelfModel.values に基づいて意志を生成
- L4 Council は SelfModel の整合性を監視
- L6 Inter-Mind Channel では、相手に開示する SelfModel の範囲を本人が選択

## プライバシ

- SelfModel 全体は本人鍵で暗号化
- 外部開示は **明示的なビューテンプレート**（"public profile", "close friends only" 等）経由のみ

## reference runtime で固定した校正境界

`self-model-advisory-calibration-boundary-v1` は、本人以外の witness や
Council が SelfModel の「正しさ」を断定する contract ではない。
外部 evidence は `self_model_calibration_receipt` に digest-only で束ねられ、
本人同意、Council resolution、Guardian redaction が揃った場合でも
`correction_mode=advisory-only` に留まる。

この receipt は病理的な自己評価の可能性を Council review へ渡せるが、
`forced_correction_allowed=false`、`accepted_for_writeback=false`、
`raw_external_testimony_stored=false` を固定し、
proposed adjustment は常に `requires-self-acceptance` として扱う。
つまり reference runtime は補正の根拠を監査可能にするだけで、
本人に代わって価値観や trait を上書きしない。

## reference runtime で固定した価値生成境界

`self-model-self-authored-value-generation-v1` は、アップロード後の新しい価値観を
外部 reviewer が「正しい / 間違っている」と裁定する contract ではない。
reference runtime は新規価値候補を
`self_model_value_generation_receipt` に digest-only で束ねるが、
`generation_mode=self-authored-bounded-experiment`、
`integration_status=proposed-not-written-back`、
`requires_future_self_acceptance=true` を固定する。

Council と Guardian は continuity context と安全境界を確認できるが、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`accepted_for_writeback=false` を維持する。
raw value payload や raw continuity payload は保存せず、将来の本人受容があるまで
SelfModel 本体には書き戻さない。

## reference runtime で固定した病理的自己評価 escalation 境界

`self-model-pathology-escalation-boundary-v1` は、病理的な自己評価の可能性を
OS 内部で医療診断・法的判断として確定する contract ではない。
reference runtime は `self_model_pathological_self_assessment_escalation_receipt` により、
advisory calibration receipt、risk signal refs、本人同意または emergency review、
Council resolution、Guardian boundary、外部医療・法制度・care handoff refs を
digest-only に束ねる。

この receipt で OS が担う範囲は `observe-and-refer-only` に限定される。
`medical_adjudication_authority=external-medical-system`、
`legal_adjudication_authority=external-legal-system`、
`care_handoff_required=true`、
`consent_or_emergency_review_required=true` を固定し、
`internal_diagnosis_allowed=false`、`self_model_writeback_allowed=false`、
`forced_correction_allowed=false`、`forced_stability_lock_allowed=false` を保つ。
raw medical / legal / witness / SelfModel payload は保存せず、OS は証拠と境界を
外部 handoff へ縮約するだけで、本人に代わって診断・矯正・人格固定を行わない。

## reference runtime で固定した care trustee handoff 境界

`self-model-care-trustee-responsibility-handoff-v1` は、pathology escalation 後の
長期 trustee、care team、legal guardian の責任分担を OS 内 authority へ取り込まず、
外部制度側の refs と boundary refs へ digest-only に束縛する contract である。

`self_model_care_trustee_handoff_receipt` は元の pathology escalation receipt digest、
外部 trustee refs、care team refs、legal guardian refs、responsibility boundary refs、
本人同意または emergency review、Council resolution、Guardian boundary、
長期 review schedule、continuity ref を `responsibility_commit_digest` へ束ねる。

この receipt で OS が担う範囲は `boundary-and-evidence-routing-only` に限定される。
trustee / care team / legal guardian の authority source はすべて外部制度側に置き、
`long_term_review_required=true`、
`external_adjudication_required=true`、
`os_trustee_role_allowed=false`、
`os_medical_authority_allowed=false`、
`os_legal_guardianship_allowed=false`、
`self_model_writeback_allowed=false`、
`forced_correction_allowed=false` を固定する。
raw trustee / care / legal / SelfModel payload は保存せず、OS は長期責任の存在と境界だけを
監査可能な digest に縮約する。

## reference runtime で固定した外部 adjudication result 境界

`self-model-external-adjudication-result-boundary-v1` は、care trustee handoff 後に
外部医療・法制度・trustee 側が返す判断結果の **形式だけ** を repo-local に固定し、
判断権限そのものを OS 内へ取り込まない contract である。

`self_model_external_adjudication_result_receipt` は元の care trustee handoff receipt digest、
medical / legal / trustee の adjudication result refs、jurisdiction policy refs、
appeal / review refs、本人同意または emergency review、Council resolution、
Guardian boundary、continuity review ref を `adjudication_commit_digest` へ束ねる。

この receipt で OS が担う範囲は `digest-only-result-routing` に限定される。
medical / legal / trustee result の authority source はすべて外部制度側に置き、
`external_adjudication_result_bound=true`、
`jurisdiction_policy_bound=true`、
`appeal_or_review_path_required=true`、
`continuity_review_required=true` を固定する。
同時に `os_adjudication_authority_allowed=false`、
`os_medical_authority_allowed=false`、
`os_legal_authority_allowed=false`、
`os_trustee_role_allowed=false`、
`self_model_writeback_allowed=false`、
`forced_correction_allowed=false` を保つ。
raw medical / legal / trustee result、jurisdiction policy、SelfModel payload は保存せず、
OS は外部判断結果を本人・Council・Guardian が監査できる digest-only chain へ
縮約するだけである。

## reference runtime で固定した外部 adjudication verifier 境界

`self-model-external-adjudication-live-verifier-network-v1` は、上記の
appeal / review path と jurisdiction policy が live verifier response によって
current であることを、OS 外 authority のまま検証する contract である。

`self_model_external_adjudication_verifier_receipt` は元の
external adjudication result receipt digest、appeal / review set digest、
jurisdiction policy set digest、JP-13 / US-CA verifier response、signed response
envelope、verifier key、trust root、route ref、freshness window、Council resolution、
Guardian boundary、continuity review ref を `verifier_quorum_digest` へ束ねる。

この receipt で OS が担う範囲は `digest-only-appeal-review-verification` に限定される。
`verifier_quorum_threshold=2`、`verifier_quorum_status=complete`、
`appeal_review_live_verifier_bound=true`、
`jurisdiction_policy_live_verifier_bound=true`、
`signed_response_envelope_bound=true`、
`freshness_window_bound=true` を固定する。
同時に `stale_response_accepted=false`、`revoked_response_accepted=false`、
`os_adjudication_authority_allowed=false`、
`self_model_writeback_allowed=false`、
`raw_verifier_payload_stored=false`、
`raw_response_signature_payload_stored=false` を保つ。

## reference runtime で固定した autonomy review 境界

`self-model-autonomy-review-witness-boundary-v1` は、外部 witness と Council が
self-authored value generation を監査する際の権限を固定する contract である。

`self_model_value_autonomy_review_receipt` は元の value-generation receipt digest、
source candidate digest set、witness evidence digest set、self authorship continuation、
Council review、Guardian boundary を束ねる。
review は `advisory-witness-council-boundary-review` / `witness-context-boundary-only`
に限定し、candidate set を元の generation receipt と同一に保つ。

この receipt は witness や Council の観察を捨てないが、それを本人の価値生成に対する
外部 veto や候補書換権限へ昇格させない。
`candidate_set_unchanged=true`、`self_authorship_preserved=true`、
`future_self_acceptance_remains_required=true`、
`external_veto_allowed=false`、`council_override_allowed=false`、
`guardian_forced_lock_allowed=false`、`candidate_rewrite_allowed=false`、
`raw_witness_payload_stored=false` を固定し、review は future self acceptance 前の
immediate writeback も許さない。

## reference runtime で固定した本人受容 writeback 境界

`self-model-future-self-acceptance-writeback-v1` は、上記の
self-authored value-generation proposal を、後日の本人受容が明示された場合だけ
bounded writeback へ進める contract である。

`self_model_value_acceptance_receipt` は元の value-generation receipt digest、
candidate digest set、accepted value refs、continuity recheck refs、future self
acceptance ref、Council resolution、Guardian boundary を束ねる。
受容対象は元の self-authored candidate set の subset に限定し、
`acceptance_mode=future-self-accepted-bounded-writeback`、
`integration_status=accepted-for-bounded-writeback`、
`future_self_acceptance_satisfied=true`、
`boundary_only_review=true`、
`accepted_for_writeback=true` を固定する。

Council と Guardian は境界違反を監査するだけで、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`external_truth_claim_allowed=false` を保つ。
writeback は `writeback_commit_digest` によって source generation、
accepted value digest、writeback ref、post-acceptance snapshot ref へ束縛し、
raw value payload や raw continuity payload は保存しない。

## reference runtime で固定した価値再評価・退役境界

`self-model-future-self-reevaluation-retirement-v1` は、過去に本人受容され
active writeback へ入った value を、後日の本人再評価が明示された場合だけ
active SelfModel writeback から退役させる contract である。

`self_model_value_reassessment_receipt` は元の value-acceptance receipt digest、
accepted value digest set、retired value refs、continuity recheck refs、
future self reevaluation ref、Council resolution、Guardian boundary を束ねる。
退役対象は元の accepted value set の subset に限定し、
`reassessment_mode=future-self-reevaluated-bounded-retirement`、
`integration_status=retired-from-active-writeback-archive-retained`、
`future_self_reevaluation_satisfied=true`、
`active_writeback_retired=true`、
`historical_value_archived=true` を固定する。

これは価値履歴の削除ではなく、active writeback からの退役である。
Council と Guardian は境界違反を監査するだけで、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`external_truth_claim_allowed=false` を保つ。
retirement は `retirement_commit_digest` によって source acceptance、
retired value digest、retirement writeback ref、post-reassessment snapshot ref、
archival snapshot ref へ束縛し、raw value payload や raw continuity payload は保存しない。

## reference runtime で固定した価値 timeline 境界

`self-model-value-lineage-timeline-v1` は、self-authored value の生成、本人受容、
後日の再評価・退役を個別 receipt の寄せ集めではなく 1 つの append-only lineage として
監査する contract である。

`self_model_value_timeline_receipt` は generation receipt digest、
acceptance receipt digest、reassessment receipt digest を `value_events` に順序付きで束ね、
各 event の `event_digest`、最終的な `active_value_refs` / `retired_value_refs`、
`archive_snapshot_refs`、continuity audit ref、Council resolution、Guardian archive ref を
`timeline_commit_digest` へ束縛する。

timeline は `generated -> accepted -> retired` の順序を守り、
active set と retired set の交差を許さず、
retired value には archive snapshot ref を必須にする。
これは本人の価値変化を凍結するものではなく、後日の本人再評価で退役した value が
active writeback から外れた後も、履歴として削除されず残ることを確認するための境界である。
Council と Guardian は引き続き boundary-only review に留まり、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`raw_value_payload_stored=false`、`raw_continuity_payload_stored=false` を固定する。

## reference runtime で固定した価値 archive retention proof 境界

`self-model-value-archive-retention-proof-v1` は、value timeline で retired になった
value の archive snapshot refs を、外部 trustee proof、long-term storage proof、
retention policy、retrieval test refs へ digest-only に束縛する contract である。

`self_model_value_archive_retention_proof` は元の value timeline receipt digest と
`timeline_commit_digest`、archive snapshot digest set、retired value digest set、
trustee / storage / retention policy / retrieval test の digest set、continuity audit ref、
Council resolution、Guardian archive ref を `retention_commit_digest` へ束ねる。

この proof は archive の存在と保持経路を監査可能にするためのものであり、
retired value を active writeback へ戻す権限や、外部 proof provider による価値履歴 veto を
作らない。`timeline_archive_retention_verified=true`、
`trustee_proof_bound=true`、`long_term_storage_proof_bound=true`、
`retention_policy_bound=true`、`retrieval_test_bound=true` を固定し、
`archive_deletion_allowed=false`、`external_veto_allowed=false`、
`raw_archive_payload_stored=false`、`raw_trustee_payload_stored=false`、
`raw_storage_payload_stored=false`、`raw_continuity_payload_stored=false` を保つ。

## reference runtime で固定した価値 archive retention refresh 境界

`self-model-value-archive-retention-refresh-window-v1` は、初回の
archive retention proof を無期限に信頼せず、90 日の freshness window、
proof refresh deadline、revocation registry refs に束縛して再確認する contract である。

`self_model_value_archive_retention_refresh_receipt` は元の archive-retention proof の
receipt digest と `retention_commit_digest`、archive snapshot set digest、
retention policy set digest、更新後の trustee / storage / retrieval test proof digest set、
revocation registry digest set、expiry window refs、continuity audit ref、
Council resolution、Guardian archive ref を `refresh_commit_digest` へ束ねる。

この refresh receipt は proof provider を archive deletion authority へ昇格させず、
revoked / expired source proof を fail-closed にするための境界である。
`freshness_window_days=90`、`source_proof_status=current-not-revoked`、
`refresh_status=refreshed-before-expiry`、`refresh_window_bound=true`、
`revocation_check_bound=true`、`retention_policy_still_bound=true`、
`expiry_fail_closed=true` を固定する。
同時に `source_proof_revoked=false`、
`expired_source_proof_accepted=false`、`archive_deletion_allowed=false`、
`external_veto_allowed=false`、`raw_refresh_payload_stored=false`、
`raw_revocation_payload_stored=false`、`raw_archive_payload_stored=false`、
`raw_storage_payload_stored=false` を保つ。

## 残る未解決

- 実世界の trustee / care team / legal guardian 制度そのもの、および外部 adjudication の実運用・不服申立て制度は人間社会側の制度設計に残る
