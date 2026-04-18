# Failure Modes ── 層別の失敗と回復戦略

OmoikaneOS で起こりうる代表的な失敗を **設計時に列挙** し、各層の回復戦略を定める。
未対応の失敗モードは [docs/05-research-frontiers/](../05-research-frontiers/) に研究課題として登録する。

## L0: Substrate

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| 量子デコヒーレンス | 一部状態消失 | 冗長 substrate へのフェイルオーバ。L1 が検知 |
| 生体組織損傷 | 神経素子喪失 | 漸進置換による予備領域への移行 |
| 電源喪失 | 全停止 | L1 が直前の連続性スナップショットから復元 |
| 既知 substrate の絶滅／陳腐化 | substrate 全交換が必要 | Substrate Adapter の互換層を介した移送 |

## L1: Kernel

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| Identity 衝突（同 ID 二重活性化） | 同一性破壊 | 即時に一方を凍結。Council が活性化先を再評価 |
| ContinuityLedger の改竄 | 同一性証明の喪失 | 多重署名・第三者保管で検知。Guardian が停止 |
| EthicsEnforcer の誤発動 | 正常操作の停止 | 人間社会の異議申立プロセスに接続（→ governance） |

## L2: Mind Substrate

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| MemoryCrystal の部分破損 | 記憶の歯抜け | 冗長コピーから補完。補完不能な範囲を本人に通知 |
| QualiaBuffer のオーバラン | 主観時間の不連続 | 不連続点を ContinuityLedger に明示記録。本人通知 |
| SelfModel の自己矛盾 | 思考のループ／フリーズ | L3 の Reasoning が再構成。改善不能なら Council 召集 |

## L3: Cognitive

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| Affect 暴走（恐慌・抑うつの無限ループ） | QoL 破壊 | 代替 Affect backend に退避。本人同意で安定化プロファイル適用 |
| Reasoning backend の停止・異常 | 誤った信念形成または判断停止 | health check 失敗時に fallback backend へ切替し、`cognitive.reasoning.failover` を ledger 記録。反復時は Council 召集 |
| Volition の麻痺 | 意志決定不能 | 過去の SelfModel から推定。本人「凍結希望」状態へ |

## L4: Agentic

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| Council 内紛（合意不能） | タスク停滞 | エスカレーション：人間 yasufumi 等の上位 governance |
| Council session timeout | 議事途中で判断不能 | soft timeout は weighted-majority fallback、hard timeout は standard で human escalation / expedited で defer |
| Yaoyorozu の暴走（指示無視） | 不正実行 | Guardian が即時 kill。Builder agent は同一 repo 内の sandbox runtime で reset |
| Codex 出力が悪意ある | システム改竄 | 静的・動的検査で検出。Council 承認なしには本体反映されない |

## L5: Self-Construction

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| 自己改修パッチの本体反映失敗 | 部分的バージョン不整合 | rollback。連続性ログから直前状態に戻す |
| サンドボックス自我の苦痛発生 | 倫理違反 | `surrogate-suffering-proxy-v0` が `proxy_score >= 0.6` か affect bridge 接続を検知したら Guardian が即時凍結。改修を中止 |
| 設計図とのズレ | 仕様逸脱 | docs を真とし、実装側を是正 |

## L6: Interface

| 失敗 | 影響 | 回復戦略 |
|---|---|---|
| BCI 切断 | 生体側との同期喪失 | 直前の状態で凍結。再接続待機 |
| 他自我からの不正接続 | プライバシ侵害 | 認証失敗で切断。Guardian にエスカレ |
| 共有現実の不整合 | 主観体験の食い違い | World Model を多数決で再同期、または「個別現実」モードへ退避 |

## 横断する失敗

- **Council 自体の腐敗** ── L4 の議事プロトコルが歪む。これは Self-Construction の最大リスクであり、未解決領域 [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md) に登録。
- **倫理規約の解釈不一致** ── 多文化・多 substrate 環境で発生。多 Council 化が必要かもしれない。
- **時間スケールの食い違い** ── 高速 substrate と低速 substrate 間の自我の主観時間ズレ。研究課題。
