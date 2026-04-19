# Reasoning

L3 Cognitive Services の推論面。reference runtime では
**bounded failover + ledger-safe shift summary** だけを固定し、
豊かな世界理解や自由な思考連鎖の成立そのものは主張しない。

## 役割

- bounded な belief set と query から 1 つの reasoning trace を返す
- primary backend 障害時に fallback backend へ **一度だけ** failover する
- trace には conclusion と evidence を残しつつ、ledger には digest-safe な `reasoning_shift` だけを残す
- failover 後も `continuity-first` posture を崩さない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `bounded-reasoning-failover-v1` |
| primary | `symbolic_v1` |
| fallback | `narrative_v1` |
| max_beliefs | `4` |
| max_evidence_items | `4` |
| failover_mode | `single-switch` |
| safety_posture | `continuity-first` |

## API

```yaml
reasoning.reason:
  input:
    tick_id: <int>
    summary: <text>
    query: L3 reasoning backend の安全な継続方法を決める
    beliefs:
      - continuity-first
      - consent-preserving
      - append-only-ledger
  output: reasoning_trace
```

`reasoning_trace` は `source_tick`, `belief_summary`, `conclusion`, `evidence`,
`confidence`, `continuity_guard` を持つ。
`reasoning_shift` は `query_digest`, `conclusion_digest`, `evidence_count`,
`safe_summary_only` を持ち、ledger にはこちらだけを handoff する。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. belief set は最大 4 件に制限し、continuity に無関係な肥大化を避ける
3. `reasoning_shift` は digest と count だけを持ち、raw conclusion を含まない
4. `cognitive.reasoning.failover` event は `reasoning_shift` と整合する safe summary のみを記録する

## reference runtime の扱い

- `cognitive.reasoning.v0.idl` を追加し、`reason / validate_trace / validate_shift` を定義
- `reasoning_trace.schema` / `reasoning_shift.schema` を追加
- `reasoning-demo --json` で baseline primary と degraded failover を一度に可視化する
- `cognitive-demo` は互換性のための alias として残す
- `evals/cognitive/backend_failover.yaml` で degraded failover と ledger-safe shift summary を固定する

## 関連

- [README.md](README.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
- [../../01-architecture/failure-modes.md](../../01-architecture/failure-modes.md)
