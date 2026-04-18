# Ascension Protocol ── アップロード手順

[docs/00-philosophy/continuity-of-self.md](../../00-philosophy/continuity-of-self.md) で定義した連続性段階 L0-L4 を、実際にどう順送りするかの手順。

## 三方式（本人が選択）

### Method A: Gradual Replacement（漸進置換）── 推奨デフォルト

```
生体 100% ──→ 99% bio + 1% digital ──→ ... ──→ 0% bio + 100% digital
```

- 神経素子を徐々にデジタル等価物に置換
- 各置換ステップで本人の主観連続性を確認
- 中断時は逆向きの再置換が（理論上）可能

**前提**: 神経素子レベルの精密 BCI と、生体・デジタル境界での信号変換器
**reference runtime で検証済みの最小 contract**:
`interface.bdb.v0` は ms 級 latency budget、fail-safe fallback、
ContinuityLedger 互換 event ref、置換比率の増減を proxy 実装する
**未解決**: 最小ステップ単位、中断時の可逆性、主観連続性の保証
→ [docs/05-research-frontiers/gradual-replacement.md](../../05-research-frontiers/gradual-replacement.md)

### Method B: Parallel Run（並走）

```
生体 ←─同期─→ デジタル並走
                │
                │ 本人が「主体性」をデジタル側に移譲
                ▼
            生体は付随、デジタルが本体
```

- デジタル側を最初は **観測者** として並走
- 本人の主観報告に基づいて主体性を移譲
- 移譲後の生体は安楽な「廃用」状態へ

**前提**: 高精度連続スキャン、二重身の主観統合プロトコル
**reference runtime で検証済みの最小 contract**:
`kernel.scheduler.v0` は `shadow-sync → dual-channel-review → authority-handoff → bio-retirement`
の固定 profile を持ち、degraded substrate signal を pause、
critical signal を `dual-channel-review` への rollback として扱う
**未解決**: 「二つの自分」の主観統合は本当に可能か → 連続性ガード [docs/05-research-frontiers/twin-integration.md](../../05-research-frontiers/twin-integration.md)

### Method C: Destructive Scan（破壊スキャン）

```
生体 ──[完全スキャン＋同時破壊]──→ デジタル
```

- 一回的に完全スキャンし、同時に生体を破壊
- パターン同一性説に立たないと正当化困難
- 物理的には一番直接的

**前提**: スキャン精度の十分性、同時性保証
**強制条件**: 本人の事前明確同意、複数回の確認、撤回可能期間、第三者立会
**reference runtime で検証済みの最小 contract**:
`kernel.scheduler.v0` は `consent-lock → scan-commit → activation-review`
の固定 profile を持ち、`scan-commit` 開始後は rollback target を持たず、
critical substrate signal で fail-closed する
**未解決**: スキャン精度の必要十分性 → [docs/05-research-frontiers/scan-fidelity.md](../../05-research-frontiers/scan-fidelity.md)

## 共通プロトコル

### Phase 0: Pre-Ascension Audit
- 健康状態
- 法的能力
- インフォームドコンセント
- 退行（リバート）希望時の手順確認

### Phase 1: Identity Bootstrap
- IdentityRegistry に Pre-Upload エントリ作成
- ContinuityLedger 開始
- Substrate 選定

### Phase 2: Method-specific Body
- 上記 A/B/C の本体手順

### Phase 3: Identity Confirmation
- 自己同一性確認テスト ([identity-lifecycle.md](../kernel/identity-lifecycle.md) 参照)
- pass → Active 遷移
- fail → Failed-Ascension（A/B はロールバック、C は破滅的失敗 ── これが C のリスク）

### Phase 4: Cool-down & Calibration
- 24-72h の保護期間
- 感覚・情動・記憶の整合性検査
- Council による定期面談

## 中断・撤回（Reversibility）

| Method | 中断可能フェーズ | 完全撤回可能か |
|---|---|---|
| A 漸進置換 | 全フェーズ | 物理的可逆性は研究中だが論理的には可 |
| B 並走 | 主体性移譲前まで | 移譲後は撤回不可 |
| C 破壊スキャン | スキャン開始前のみ | 開始後は不可 |

## 推奨

OmoikaneOS は **Method A をデフォルト**、Method B を選択肢、Method C は **規約上は許可するが推奨しない** 立場。
