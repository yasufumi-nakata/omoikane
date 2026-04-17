# Connectome Format

神経回路の正規表現。**substrate 中立** であること。

## 基本構造

```yaml
ConnectomeDocument:
  schema_version: '1.0'
  snapshot_id: <uuid>
  identity_id: <id>
  snapshot_time: <attested>
  nodes:
    - id: <uuid>
      kind: neuron|circuit|module
      type: excitatory|inhibitory|modulatory
      position: { x, y, z, frame: 'anatomical|abstract' }
      properties: { ... }
      substrate_hint: <optional>
  edges:
    - id: <uuid>
      source: <node_id>
      target: <node_id>
      weight: <float>
      delay_ms: <float>
      plasticity: { rule, params, enabled }
  hierarchies:
    - id: <uuid>
      kind: cortical_column|basal_ganglia|...
      members: [<node_id>...]
      description: <optional>
  invariants:
    - invariant_id: <name>
      expression: <rule>
      scope: document|subgraph|hierarchy-name
```

canonical schema: [specs/schemas/connectome_document.schema](../../specs/schemas/connectome_document.schema)

## Substrate 中立化

- 物理座標は `frame: anatomical` で生体由来、`frame: abstract` で計算空間
- 重み・遅延は **物理単位ではなく機能単位** で正規化
- 各 substrate adapter が「自分の物理表現への翻訳器」を持つ
- reference runtime では `connectome-demo` がこの canonical schema に沿う最小 snapshot を出力する

## 同等性検証

異なる substrate に転写後も同じ Connectome が動くか。
- 機能等価性: 入力 → 出力の写像が一致
- 動的等価性: 内部状態の時間発展が一致
- 主観等価性: 本人の主観報告が一致 ── 最終判定基準だが測定困難

## 変更ログ

Connectome の変更は ContinuityLedger に **diff** として記録。
- 漸進置換時の各ステップ
- 学習による重み更新（時間粒度集約可）
- 障害復旧時の再構成

## サイズ

人間スケールで $10^{11}$ ノード、$10^{14}$ エッジ。圧縮・差分・階層化が必須。

## 未解決

- 学習による微小変化を **どの粒度で記録** するか（連続性 vs 容量）
- 階層構造の正規分類（生体由来か機能由来か）
- 量子相関を含む substrate での表現拡張
