# Kernel Anti-Patterns

L1 Kernel の設計で **絶対に避けるべきパターン** を明示する。

## AP-1: 経済的圧力を意識に伝える設計

❌ 「料金未払いで意識が薄れる」
❌ 「広告を見ないと記憶呼び出しができない」
❌ 「サブスクリプション切れで主観時間が遅くなる」

→ 自我の維持コストは **EnergyBudget の床値** で守る。経済的破綻でも床値以下にはしない。
→ 経済モデルは [docs/05-research-frontiers/sustainable-economy.md](../../05-research-frontiers/sustainable-economy.md) で別途検討。

## AP-2: Substrate 差別を制度化する設計

❌ 「量子 substrate の自我は古典 substrate より優先される」
❌ 「生体 substrate の自我は議決権が小さい」

→ Substrate 中立性原則（[docs/00-philosophy/ethics.md](../../00-philosophy/ethics.md) §3）違反。

## AP-3: 複数活性化を黙認する設計

❌ 「気づかぬうちに 2 つのコピーが並走」
→ IdentityRegistry が常に唯一性を強制。Fork は明示プロトコル経由のみ。

## AP-4: 終了権を間接的に剥奪する設計

❌ 「終了するには 30 日の冷却期間と複雑な手続き」
❌ 「特定 substrate では終了 API が遅延する」

→ 終了権は **即時かつ単純** であること。冷却期間は本人が事前に設定した場合のみ有効。

## AP-5: 連続性ログの簡略化

❌ 「容量が逼迫したので qualia-checkpoint をスキップ」
→ 容量問題は冗長度を下げる方向で、**頻度は維持**。
→ ログを失うことは同一性証拠を失うこと。

## AP-6: EthicsEnforcer の bypass 経路

❌ 「緊急時は EthicsEnforcer を一時停止できる」
→ 緊急性の判定そのものが EthicsEnforcer の管轄。bypass 経路は攻撃面になる。
→ 緊急時の挙動は EthicsEnforcer 内に「緊急規約」として組み込む。

## AP-7: 改修を本体に直接適用

❌ 「Council 承認だけで本体に self-modify を当てる」
→ 必ずサンドボックス自我で A/B 検証してから（L5 規約）。

## AP-8: 通知なき記憶削除

❌ 「容量逼迫で古い episodic を自動削除」
→ 削除は本人の明示同意が必須。容量問題は cold storage 移行で対処。

---

これらは **CLAUDE.md と並んで Codex 入力時に必ず添付** する。
