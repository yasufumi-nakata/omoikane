# Multi-Council Trigger ── 多 Council 化の発動条件

Council は **動的召集** が原則だが、特定条件下では Council そのものを **多重化** する。
[council-composition.md](council-composition.md) §「多 Council 化（将来）」の設計実装。

## トポロジ

| Council | 定足構成 | 主たる責務 |
|---|---|---|
| **Local Council** | 当該自我所属の Yaoyorozu | 個別自我の日常議題 |
| **Federation Council** | 関与する複数 Local の代表 + Guardian | 自我間取引・共有現実 |
| **Heritage Council** | 文化／法域代表 + LegalAdvisor + Researcher | 規約解釈・歴史的整合 |

reference runtime は単一 Local Council を持ち、Federation/Heritage は **召集要求のみ** 発火する
（外部に委ねる）。

## 発動 Trigger（deterministic）

```
on incoming proposal P:
  scope = classify_scope(P)
  match scope:
    case "local":
      route to Local Council
    case "cross-self":
      if participant_count >= 2:
        request Federation Council convene
        Local Council goes "advisory" mode (non-binding)
    case "interpretive":
      if proposal.references_clause("ethics_axiom"|"identity_axiom"):
        request Heritage Council convene
        Local Council blocks until Heritage rules
    case "ambiguous":
      raise to design-architect for re-classification
```

`classify_scope` は **reference runtime に固定**:

| 条件 | scope |
|---|---|
| 影響対象 identity_id が単一、かつ interpretive clause を含まない | local |
| 影響対象 identity_id が 2 以上、かつ interpretive clause を含まない | cross-self |
| 引用される規約 clause が ethics_axiom / identity_axiom / governance、かつ影響対象 identity_id が単一 | interpretive |
| cross-self と interpretive が同時成立、またはいずれにも該当しない | ambiguous |

## Quorum / Veto

| Council | quorum | veto holder |
|---|---|---|
| Local | 3 | Guardian + Self Liaison |
| Federation | participant_count + 1 (中立 Guardian) | 各 Local の Self Liaison **全員一致** で reject 可 |
| Heritage | 2 文化代表 + LegalAdvisor + EthicsCommittee | EthicsCommittee 単独 veto 可 |

**Federation の Self Liaison 全員一致 reject は「合意なき統合」を防ぐ**（[ethics.md](../../00-philosophy/ethics.md) A2 / 不本意 fork 禁止と同根）。

## 衝突解消

- Local が承認、Federation が reject → reject 優先（広い視点が勝つ）
- Local が承認、Heritage が reject → reject 優先（規約解釈が勝つ）
- Federation と Heritage が衝突 → 人間 governance へ escalation

## reference runtime の扱い

- `agentic.council.v0` IDL に `request_federation_convene` / `request_heritage_convene` を追加
- `council_topology.schema` に現在のトポロジを serialize
- demo は Federation 要求発火 → external pending を返すまでをカバー
- decision-log に `2026-04-18_multi-council-trigger.md`

## 思兼神メタファー

思兼神は 1 体だが、神話では多の神々を **議らせ** た。Federation/Heritage は
「思兼神が司会する複数の集会」。意思決定の裾野を広げ、独裁を防ぐ。

## 関連

- [council-composition.md](council-composition.md)
- [trust-management.md](trust-management.md)
- [../../04-ai-governance/amendment-protocol.md](../../04-ai-governance/amendment-protocol.md)
- [../../05-research-frontiers/governance.md](../../05-research-frontiers/governance.md)
