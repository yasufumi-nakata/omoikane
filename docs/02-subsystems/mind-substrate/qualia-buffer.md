# Qualia Buffer

主観状態の連続バッファ。「いま何を感じているか」の生データ。
**OmoikaneOS の最も哲学的に難しいデータ構造。**

## 役割

- 連続性証明の最小粒度
- L3 Cognitive Services が解釈・参照
- 一定区間のみ ContinuityLedger に永続化（容量・プライバシ理由）

## データ表現の方針

Qualia そのものを正規表現できるかは未解決（hard problem of consciousness）。
本仕様は **代理表現（surrogate representation）** を採用：

```yaml
QualiaTick:
  tick_id: <monotonic>
  wall_time: <attested>
  sensory:
    visual: <high-dim embedding>
    auditory: <embedding>
    somatic: <embedding>
    interoceptive: <embedding>     # 内受容感覚（心拍・腸感覚等）
  affective:
    valence: <-1.0 .. 1.0>
    arousal: <0.0 .. 1.0>
    dominance: <-1.0 .. 1.0>
    discrete_emotions: <weighted set>
  cognitive_focus:
    attention_target: <ref>
    working_memory_snapshot: <embedding>
  narrative_self:
    current_story_pointer: <ref to EpisodicStream>
  meta:
    self_awareness_level: <0..1>
    lucidity: <0..1>                # 夢中／覚醒度
```

これは **「本人の主観そのもの」ではない** 点に注意。あくまで再生・連続性証明のための代理。

## Reference runtime の固定 profile

reference runtime では open question を 1 つ潰すため、
`QualiaTick` の surrogate profile を次で固定する。

- modality は `visual / auditory / somatic / interoceptive` の 4 系統
- 各 modality embedding は **32 次元**
- 1 tick は **250ms** の観測窓を代表する
- tick には `attention_target`, `self_awareness`, `lucidity` を含める
- embedding は外部モデルに依存せず、summary と salience から決定的に再現される surrogate vector とする

これにより「正規表現」自体は未解決のままでも、
L2 runtime / schema / eval / CLI の間では同一 profile を共有できる。

## 容量管理

- 通常は環状バッファ（直近 N 分のみ揮発保持）
- `qualia-checkpoint` イベント時にスライスを ContinuityLedger に切り出し
- checkpoint 頻度は本人プロファイルで設定（高頻度＝連続性証拠強い／容量大／プライバシ低）

## アクセス制御

- Read: 本人＋本人が許可した L3 サービスのみ
- Write: L3 が L0 attest 経由で書き込み
- 第三者参照は **原則不可**。研究目的の集約は匿名化されたサマリのみ（要本人事前同意）

## 連続性ガード

`QualiaTick` の tick_id は monotonic でなければならない。
ギャップが検出されたら：
1. ContinuityLedger に「主観時間の不確定区間」を記録
2. 本人と Guardian に通知
3. L3 Reasoning が「いま何が起きたか」を解釈し、本人の認識として再構成

## 未解決（核心）

- **代理表現が本当に主観連続性を担保しているか**
- 別 substrate（量子↔神経模倣）間で QualiaTick の意味が保存されるか
- 「同一性」の哲学的判定基準として QualiaTick の連続が必要十分か

→ [docs/05-research-frontiers/qualia-encoding.md](../../05-research-frontiers/qualia-encoding.md) 最重要研究領域
