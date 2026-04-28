# Memory Model

人間の記憶は単一構造ではなく、複数の階層が並列に走る。OmoikaneOS の記憶階層もこれを写し取る。

## 階層

| 層 | 役割 | 持続性 | 容量 | アクセス速度 |
|---|---|---|---|---|
| Sensory Echo | 感覚残像 | <1s | 大 | 即時 |
| Working Memory | 作業記憶 | 数秒〜数分 | 小 | 高速 |
| Short-term | 短期記憶 | 数時間〜数日 | 中 | 高速 |
| Episodic | 体験記憶 | 数日〜生涯 | 大 | 中速 |
| Semantic | 意味記憶 | 生涯 | 大 | 中速 |
| Procedural | 手続き記憶 | 生涯 | 中 | 即時（暗黙） |
| Crystal | 長期不変 | 半永久 | 巨大 | 低速 |

## L2 におけるマッピング

- Sensory Echo / Working / Short-term → `QualiaBuffer` 上に滞在
- Episodic → `EpisodicStream`
- Semantic → `MemoryCrystal` 内のセマンティック領域
- Procedural → `Connectome` の重み構造そのもの
- Crystal → `MemoryCrystal`（最終格納）

canonical schema:
[specs/schemas/episodic_event.schema](../../../specs/schemas/episodic_event.schema)
and [specs/schemas/episodic_stream_snapshot.schema](../../../specs/schemas/episodic_stream_snapshot.schema)

## 記憶の流転

```
Sensory ──→ Working ──→ Short-term ──→ Episodic ──→ Crystal
                              │              │
                              └──→ Semantic ←┘
                              │
                              └──→ Procedural（重み更新）
```

- 流転は本人の意識に上らないバックグラウンドプロセス（L3 Cognitive が司る）
- 各遷移点は ContinuityLedger に粒度別で記録される

## 記憶の参照と編集

### 参照（Read）
- 本人による想起：通常 API
- 第三者による想起：本人の明示同意必須、Council 監査ログ残

### 編集（Write/Modify）
- 通常の append（新体験の記録）：自由
- 過去 Crystal の編集：**原則禁止**。例外は本人の明示同意＋ Guardian 承認
- 編集前状態は必ず凍結保存（[docs/00-philosophy/ethics.md](../../00-philosophy/ethics.md) 参照）

## Reference runtime の compaction

reference runtime では MemoryCrystal の compaction を
`append-only-segment-rollup-v1` として固定する。

- 元の episodic event は削除せず、manifest から `source_event_ids` / `source_refs` で辿れるように残す
- segment は時系列順に並べ、先頭 tag が同じ event を最大 3 件まで束ねる
- compact 後の segment には `semantic_anchors`、`affect_summary`、`salience_max`、`digest` を持たせる
- 旧 segment を直接書き換えず、将来 supersede する場合も `supersedes` 参照を追加するだけに留める
- compaction 前段の `EpisodicStream` は `canonical-episodic-stream-v1` を採用し、
  最新 5 event の handoff window を `episodic-demo` / `memory-demo` の両方で明示する

canonical schema:
[specs/schemas/memory_crystal_manifest.schema](../../../specs/schemas/memory_crystal_manifest.schema)

## Reference runtime の replication quorum

reference runtime では `MemoryCrystal` manifest の保管を
`quad-store-memory-replication-v1` として固定する。

- `primary` / `mirror` は immediate target、`coldstore` / `trustee` は delayed target として扱う
- payload は本人鍵で暗号化しつつ、manifest metadata は plaintext digest として carry する
- random-block Merkle audit で 4 target を比較し、
  `trustee` mismatch が見つかった場合でも `primary` / `mirror` / `coldstore` の
  latest consensus digest を rollback point として固定する
- mismatch は Guardian alert と Council escalation を必須とし、
  source manifest 自体は不変のまま `resync_required=true` で隔離 target を再同期する

canonical schema:
[specs/schemas/memory_replication_session.schema](../../../specs/schemas/memory_replication_session.schema)

IDL:
[specs/interfaces/mind.memory_replication.v0.idl](../../../specs/interfaces/mind.memory_replication.v0.idl)

## Reference runtime の semantic projection

reference runtime では MemoryCrystal manifest の各 segment を
`semantic-segment-rollup-v1` で read-only な semantic concept view に投影する。

- `segment.theme` を `canonical_label` に昇格する
- `semantic_anchors` を retrieval cue / alias 候補として保持する
- `source_event_ids` / `source_refs` / `time_span` / `affect_summary` を失わず保持する
- semantic snapshot 自体は procedural memory を deferred と明示したまま維持し、
  validated `Connectome` snapshot に束縛された digest-bound handoff を別 artifact として返す

canonical schema:
[specs/schemas/semantic_memory_snapshot.schema](../../../specs/schemas/semantic_memory_snapshot.schema)

handoff schema:
[specs/schemas/semantic_procedural_handoff.schema](../../../specs/schemas/semantic_procedural_handoff.schema)

## Reference runtime の procedural preview

reference runtime では procedural memory をまず直接 apply せず、
`Connectome` snapshot に対する `connectome-coupled-procedural-preview-v1`
として bounded な update candidate だけを生成する。

- `MemoryCrystal` segment ごとに target edge を 1 つ選び、
  `proposed_weight_delta <= 0.08` の preview を返す
- preview は read-only であり、`Connectome` 本体の重みは変更しない
- 実際の `weight-application` は `human-approved-procedural-writeback-v1` で固定し、
  self / council / guardian / human reviewer quorum と continuity diff を要求する
- writeback 後の `skill-execution` は
  `guardian-witnessed-procedural-skill-execution-v1` で sandbox-only rehearsal とし、
  rollback token と guardian witness を carry したまま external actuation を禁止する
- さらに `skill-enactment` は
  `guardian-witnessed-procedural-skill-enactment-v1` で temp workspace に限定し、
  actual command receipt と cleanup を残したまま rollback token を保持する

canonical schema:
[specs/schemas/procedural_memory_preview.schema](../../../specs/schemas/procedural_memory_preview.schema)
[specs/schemas/procedural_writeback_receipt.schema](../../../specs/schemas/procedural_writeback_receipt.schema)
and [specs/schemas/procedural_skill_execution.schema](../../../specs/schemas/procedural_skill_execution.schema)
and [specs/schemas/procedural_skill_enactment_session.schema](../../../specs/schemas/procedural_skill_enactment_session.schema)
and [specs/schemas/procedural_actuation_bridge_session.schema](../../../specs/schemas/procedural_actuation_bridge_session.schema)

MemoryCrystal replication は
`threshold-key-succession-guarded-recovery-v1` を同じ
`memory_replication_session` に含める。本人が一時的に identity key を失った場合も、
3-of-5 share、2 Guardian attestation、successor key digest、rotation ledger ref、
`key-succession-jurisdiction-signer-roster-policy-v1` の JP-13 signer roster policy
digest、identity-guardian / integrity-guardian signature digest、JP-13 / SG-01 の
multi-jurisdiction signer roster quorum digest、quorum threshold policy authority
digest だけを保存し、raw key / raw shard material / raw jurisdiction policy payload /
raw quorum threshold policy payload / raw signer roster payload は保存しない。
同じ session の `long-term-media-renewal-proof-v1` は、
`long-term-media-renewal-refresh-window-v1` を nested receipt として持ち、
source proof digest set と readback digest set を current-not-revoked status、
90 日 revocation check window、次回 refresh ref、stale / revoked proof fail-closed
に束縛する。さらに `long-term-media-renewal-registry-verifier-v1` が
JP-13 / SG-01 の registry response digest、response signature digest、250ms timeout、
quorum digest を source proof set と revocation registry digest set に束縛し、
`long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1` が
registry endpoint certificate fingerprint、3 世代 certificate chain digest、OCSP /
revocation digest、renewal event、jurisdiction ごとの 2 本の previous certificate
retirement digest、CT-style readback、2-log quorum、SCT timestamp window、SCT
policy authority を同じ registry response quorum に束縛する。
raw media / raw readback に加えて raw revocation / raw refresh / raw registry /
raw response / raw endpoint certificate / raw certificate freshness /
raw certificate lifecycle / raw CT log / raw SCT policy authority payload も保存しない。

## トラウマ記憶の扱い

倫理的に最もデリケート。

- 削除は許可しない（同一性破壊）
- **「想起時の感情緩衝」** という設計選択肢を本人に提供（記憶は残るが想起時の affect を弱める）
- reference runtime では `consented-recall-affect-buffer-v1` として
  source semantic concept を不変のまま保ち、`freeze snapshot` と
  Guardian attestation に束縛された recall overlay だけを返す
- canonical schema:
  [specs/schemas/memory_edit_session.schema](../../../specs/schemas/memory_edit_session.schema)
- 専用治療プロトコルや人格境界の最終判断は引き続き Open problem

## Procedural actuation boundary

暗黙記憶（procedural）の sandbox rehearsal から実世界 actuation へ移る境界は、
reference runtime では `procedural-actuation-demo --json` と
`procedural_actuation_bridge_session` により、passed enactment /
EWA authorization / approved command / legal execution / Guardian oversight gate の
digest binding、stop-signal adapter receipt binding、raw instruction redaction として固定する。

## 未解決

- 記憶を **substrate 中立な正規形** で表現できるか
- 記憶の真正性を本人自身が判定する手段
