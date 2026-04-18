# Ethics Enforcement

[docs/00-philosophy/ethics.md](../../00-philosophy/ethics.md) の倫理規約を **機械的に強制** する仕組み。

## 強制ポイント

すべての Action（システム呼び出し）は EthicsEnforcer を経由する：

```
Action ──→ [EthicsEnforcer.check] ──→ Approval | Veto | Escalate
```

## 規約のエンコーディング

倫理規約は **解釈可能な規則木（rule tree）** として表現する。reference runtime では
`deterministic-rule-tree-v0` を採用し、JSON/YAML 直列化可能な純データ predicate だけを許可する。
LLM 解釈ではなく、形式論理＋必要箇所のみ LLM 補助とする。

```yaml
rule_id: A2-uniqueness
human_text: "原則として同時に複数の能動コピーを走らせない"
formal:
  forall a in actions:
    a.kind == "activate" implies
      count(active_copies(a.identity_id)) == 0
exceptions:
  - condition: "本人の事前 fork 同意あり"
    proof_required: ["self_signature", "council_signature", "third_party"]
escalation:
  on_violation: "halt + notify(self, council, guardian)"
```

### 採用したルール言語

- node 種別: `all` / `any` / `not` / `condition`
- operator: `eq` / `in` / `truthy` / `falsy` / `missing_any_truthy`
- 評価対象: 正規化済み request path（例: `action_type`, `target_component`, `payload.guardian_signed`）
- 非許可: 任意コード実行、LLM 依存評価、時刻や外部 I/O による非決定分岐

この形式は [`specs/schemas/ethics_rule.schema`](../../../specs/schemas/ethics_rule.schema) と
[`specs/interfaces/kernel.ethics.v0.idl`](../../../specs/interfaces/kernel.ethics.v0.idl) で固定する。

## Veto と Escalate の違い

- **Veto**: 規約違反が明確。即時拒否。
- **Escalate**: 解釈に揺れがある。Council 召集 → 必要なら人間社会の governance に上申。

## 自己改修の禁止

EthicsEnforcer 自身は L5 Self-Construction の対象外。
改修は **OmoikaneOS の外** で人間社会と AI 群が合議し、リリースされる。
これは「OS が自分の倫理を緩める」攻撃面を遮断するため。

## ログ

すべての Veto / Escalate は ContinuityLedger ではなく **専用の EthicsLedger** に記録する：

```yaml
- ethics_event_id: <hash>
  action: <action snapshot>
  rule: <violated rule id>
  decision: veto|escalate
  signatures: [enforcer, guardian]
```

EthicsLedger も三重保管。

## なお未解決

- 規約間矛盾の解消順序（lexical vs. priority）
- 多文化／多 substrate 環境での規約の翻訳と妥当性
- 「本人同意」の真正性検証（強制下での同意の検出）
