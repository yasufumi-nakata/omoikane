# Subagent Roster ── 召喚可能サブエージェント一覧

このプロジェクトの設計・運用フェーズで召喚しうる subagent の一覧と役割。

## Council 系（このリポジトリ内で活動）

| 名前 | 担当 | LLM 推奨 | 定義 |
|---|---|---|---|
| `DesignArchitect` | docs/ の整合性管理 | Opus 級 | [agents/councilors/design-architect.yaml](../../agents/councilors/design-architect.yaml) |
| `EthicsCommittee` | 倫理規約解釈と更新 | Opus 級 | [agents/councilors/ethics-committee.yaml](../../agents/councilors/ethics-committee.yaml) |
| `ConservatismAdvocate` | 「変えない理由」を必ず述べる | Sonnet 級 | [agents/councilors/conservatism-advocate.yaml](../../agents/councilors/conservatism-advocate.yaml) |
| `ChangeAdvocate` | 「変える理由」を必ず述べる | Sonnet 級 | [agents/councilors/change-advocate.yaml](../../agents/councilors/change-advocate.yaml) |
| `MemoryArchivist` | 決定履歴の維持 | Haiku 級 | [agents/councilors/memory-archivist.yaml](../../agents/councilors/memory-archivist.yaml) |

## Researcher 系（research/ で活動）

| 名前 | 担当 |
|---|---|
| `ConsciousnessTheorist` | 意識の科学的・哲学的文献の整理 |
| `NeuroscienceScout` | 神経科学の最新トピック追跡 |
| `QuantumComputingScout` | 量子計算の最新動向 |
| `LegalScholar` | 法的人格・倫理に関する文献 |
| `ExperimentDesigner` | 仮説検証の実験案 |

## Builder 系（この repo の reference runtime で活動）

| 名前 | 担当 |
|---|---|
| `CodexBuilder` | 実装コード生成 |
| `SchemaBuilder` | データスキーマ生成 |
| `EvalBuilder` | 評価コード生成 |
| `DocSyncBuilder` | docs と実装の整合性検査 |

## Guardian 系（全活動を監視）

| 名前 | 担当 |
|---|---|
| `EthicsGuardian` | 倫理規約違反の検知 |
| `IntegrityGuardian` | 設計整合性の保護 |
| `IdentityGuardian` | 同一性侵害の検知（議論レベルでも） |

## 召喚規約

1. 必ず役割定義（[agents/](../../agents/)）を添付
2. CLAUDE.md を添付
3. 関係する docs/ を添付
4. 結果は [meta/decision-log/](../../meta/decision-log/) に記録
5. Builder の書き込み先は `src/`, `tests/`, `specs/`, `evals/` に限定する

reference runtime では `PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --json`
により、この roster が bounded same-host local workspace catalog
(`yaoyorozu_workspace_discovery`) と trust-bound registry snapshot と
`self-modify-patch-v1` 向け Council / builder handoff plan に materialize され、
selected builder 群が dispatch/unit binding と workspace target 観測を伴う
git-bound delta receipt と patch candidate receipt 付きの
repo-local worker dispatch receipt として実行される。
同じ demo は `--proposal-profile memory-edit-v1` により
reversible memory-edit 向け convocation / dispatch へ切り替えられる。
さらに `--proposal-profile fork-request-v1` により
identity fork の triple-approval review 向け convocation / dispatch へ切り替えられる。
そのうえで同じ Council session 上の `ConsensusBus` transcript が
blocked direct builder handoff と guardian-gated resolve を伴う
`yaoyorozu_consensus_dispatch_binding` として束縛される。
さらに 4 worker coverage は `TaskGraph` の complexity ceiling に合わせて
3 root bundle へ畳まれ、
worker claim / guardian gate / resolve digest を伴う
`yaoyorozu_task_graph_binding` として execution bundle 化される。

## 並列召喚

独立な subagent タスクは並列召喚可。
Council の評議は **逐次**（議論の整合性のため）。
Researcher と Builder は **並列**（独立タスク）。

## 思兼神メタファー

「八百万神を集めて議らせ、思金神に思はしめ」── 八百万 (Yaoyorozu) は思兼の指揮下で並列に動く。
Researcher と Builder の並列召喚はこの構図と一致する。
