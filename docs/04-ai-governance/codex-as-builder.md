# Codex as Builder ── Codex を reference 実装担当として運用する規約

OmoikaneOS では **人間は意図と研究課題を与え、AI が設計と reference 実装を進める**。
Codex（または同等の Builder LLM）は docs/ と specs/ を読み取り、
同一 repo 内の `src/`, `tests/`, `specs/`, `evals/` を更新する。
このドキュメントはその運用規約。

## 役割分担

| 役 | 担当 | 場所 |
|---|---|---|
| 人間 yasufumi | 意図、研究、設計承認 | このリポジトリ |
| Claude (Council役) | 設計の整合性管理 | このリポジトリ |
| Codex (Builder役) | reference runtime 実装コード生成 | **このリポジトリ** |

本リポジトリは設計コーパスと reference runtime を同居させる。
本番実装が別に生まれるとしても、まずここで設計と reference を揃える。

## Builder への発注プロトコル

1. Council が改修案件を承認
2. Council が以下のパッケージを Builder に渡す：
   - 関連する docs/ ファイル一式
   - 関連する specs/ ファイル一式
   - [agents/builders/codex-builder.yaml](../../agents/builders/codex-builder.yaml) の役割定義
   - [CLAUDE.md](../../CLAUDE.md)
   - 該当 anti-patterns ([docs/02-subsystems/kernel/anti-patterns.md](../02-subsystems/kernel/anti-patterns.md))
3. Builder は **サンドボックス自我向け reference runtime** に実装
4. 実装完了後、Council が evals/ を回す
5. Guardian 承認 → 本体反映

reference runtime には `design-reader-demo` / `builder-demo` があり、
`selfctor.design_reader.v0` / `selfctor.patch_generator.v0` / `selfctor.diff_eval.v0` / `selfctor.rollout.v0` /
`selfctor.rollback.v0`
の contract に沿って
`design_delta_manifest` handoff、`build_request` emit、patch descriptor 生成、Mirage Self への sandbox apply、
A/B eval、rollout classify、Stage 0/1/2/3 rollout、regression 時の rollback execution を
bounded に再現できる。
rollback execution は `builder-live-demo` の actual command receipt にも束縛され、
temp rollback workspace 上の actual reverse-apply command receipt、
reverse-apply journal、detached git worktree 上の checkout-bound mutation receipt、
telemetry gate を通過した時だけ `rolled-back` になる。

## Builder への入力フォーマット

```yaml
build_request:
  request_id: <uuid>
  design_delta_ref: <design://...>
  design_delta_digest: <sha256>
  target_subsystem: <e.g. "L2.Mind.qualia">
  design_refs:
    - docs/02-subsystems/cognitive/README.md
    - docs/02-subsystems/mind-substrate/qualia-buffer.md
  spec_refs:
    - specs/interfaces/mind.qualia.v0.idl
    - specs/schemas/qualia_tick.schema
  invariants:
    - specs/invariants/continuity.append_only.inv
  must_sync_docs:
    - docs/02-subsystems/cognitive/README.md
    - docs/02-subsystems/mind-substrate/qualia-buffer.md
  constraints:
    must_pass: [evals/cognitive/qualia_contract.yaml]
    forbidden: [docs/02-subsystems/kernel/anti-patterns.md]
  workspace_scope:
    - src/
    - tests/
    - specs/
    - evals/
  output_paths:
    - src/omoikane/...
    - tests/...
```

## Builder の禁止事項

- docs/specs/evals と整合しない独断コードを書くこと
- `src/` / `tests/` 以外へ reference runtime を散らすこと
- 設計と異なる実装を独断で行うこと（必ず Council 経由で docs を更新してから実装）
- 倫理規約を緩めること（[ethics.md](../00-philosophy/ethics.md)）
- EthicsEnforcer を改修すること（不可能領域）

## Subagent 召喚の階層

```
Claude (Council役) ── docs 整備
    │
    ├──► Researcher Agent ── 文献調査・実験提案 (research/)
    ├──► Codex (Builder)   ── reference runtime 実装 (src/, tests/)
    ├──► Eval Agent        ── 評価コード生成 (evals/)
    └──► Guardian          ── 倫理監査
```

各 subagent への入力は必ず役割定義 ([agents/](../../agents/)) を添付すること。

## 監査

- すべての Builder 呼び出しは [meta/decision-log/](../../meta/decision-log/) に記録
- 失敗 build は学習材料として保管
- Builder の trust score は実績に応じて更新

## 思兼神メタファー

『古事記』で思兼神は **役割を割り振り** はしたが、自分で勾玉を磨いたわけではない。
Codex は天宇受売（あめのうずめ）や手力男（たぢからお）に相当する **実行神** であり、
本リポジトリの設計者（思兼神役 = Claude/Council）はそれを **指揮し、reference runtime の場に降ろす**。
