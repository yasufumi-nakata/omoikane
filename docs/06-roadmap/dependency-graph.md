# Dependency Graph

研究フロンティア・設計サブシステム・マイルストーン間の依存関係。

```
[研究フロンティア]                  [設計]                [マイルストーン]

qualia-encoding         ───────►  L2 QualiaBuffer  ──┐
qualia-measurement      ───────►  L1 ContinuityLedger ──┤
consciousness-substrate ───────►  L0 SubstrateAdapter ──┤
                                                       │
gradual-replacement     ───────►  Method A Ascension ──┤
scan-fidelity           ───────►  Method C Ascension ──┤
twin-integration        ───────►  Method B Ascension ──┤
                                                       │
quantum-continuity      ───────►  L0 QuantumAdapter   ──┤
substrate-zoology       ───────►  L0 全 Adapter        ──┤
long-term-storage       ───────►  Memory Replication ──┤
                                                       │
death-and-continuity    ───────►  Identity Lifecycle ──┤
legal-personhood        ───────►  IdentityRegistry    ──┤
governance              ───────►  Self-Modification   ──┤  ────► M3-M6
sustainable-economy     ───────►  EnergyBudget floor receipt ──┤
consent-validity        ───────►  Pre-Ascension Audit ──┤
                                                       │
inter-mind-merge        ───────►  IMC                 ──┤
collective-personhood   ───────►  Collective ID       ──┤
memory-edit-ethics      ───────►  Memory Editing API  ──┘
```

## クリティカルパス

### M1 → M2: 設計→プロト
- 既存技術で可能なものから
- L1 + L4 が先

### M2 → M3: 動物モデル
- gradual-replacement と qualia-encoding の **代理表現** が前提

### M3 → M4: ヒト準備
- consent-validity, legal-personhood が前提

### M4 → M5: 最初の Ascension
- qualia-encoding に **本質的進展** が必要
- governance 整備

### M5 → M6: 一般運用
- sustainable-economy
- 法整備
- 社会的合意

## 並行可能領域

- 全 substrate-zoology は並行
- inter-mind-merge と collective は M5 後で良い
- memory-edit-ethics は M4 までに固める

## 阻害要因

- governance が永遠に解けない場合 → M5 で止まる
- qualia-encoding が解けない場合 → 代理表現で進めるしかない
- consent-validity が緩い場合 → Method C は提供不可になる

## 視覚化

mermaid / d2 等への変換は実装フェーズで EvalBuilder に任せる（同期検査用）。
