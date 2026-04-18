# Amendment Protocol ── 規約改正フロー

OmoikaneOS の **規約レイヤー**（倫理 axiom / kernel invariants / 終了権定義 / Guardian 権限）は
L5 Self-Construction の対象外。これらを変えるときに辿る、**OS 外プロセスを含む** フローを定義する。

詳細な未解決論は [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)。
ここでは reference runtime が機械的に扱える範囲を fix する。

## 改正対象の分類

| Tier | 対象 | OS 内承認 | OS 外承認 |
|---|---|---|---|
| **T-Core** | 倫理 axiom A1-A4 / EthicsEnforcer 不可侵 / 終了権 | **不可** | 人間社会 governance のみ |
| **T-Kernel** | ContinuityLedger 形式 / Identity ライフサイクル / Substrate 中立性 | Council 全会一致＋本人同意 | 人間 reviewer 過半 |
| **T-Operational** | Council session timeout / Trust threshold / TaskGraph 上限 | Council 過半 | Guardian 承認のみ |
| **T-Cosmetic** | ログメッセージ表現 / Demo シナリオ | DesignArchitect | 不要 |

T-Core は「OS 自身は提案しか出来ない」── reference runtime はその提案を `amendment_proposal` schema に
serialize し、`status: pending-human-review` のまま **freeze** する。

## ライフサイクル

```
1. Draft     ── DesignArchitect が amendment_proposal を起草
2. Council   ── tier 別の Council 召集（quorum / veto は council-composition.md）
3. Guardian  ── EthicsGuardian + IntegrityGuardian + IdentityGuardian の三重 attest
4. Sandbox   ── T-Operational 以下は Mirage Self で A/B（self-modification.md）
5. Human     ── T-Core は外部 reviewer set へ escalation。reference runtime は freeze
6. Apply     ── 承認後 ContinuityLedger に append、適用 stage 0→3
7. Audit     ── EthicsLedger と meta/decision-log/ に永続化
```

## Tier 別の OS 内可否

reference runtime は次の deterministic な許可関数を持つ:

```
allow_apply(tier, signatures):
  match tier:
    "T-Core":         return False                             # 常に freeze
    "T-Kernel":       return signatures.council == "unanimous"
                          and signatures.self_consent
                          and signatures.guardian_attested
                          and signatures.human_reviewers >= 2
    "T-Operational":  return signatures.council == "majority"
                          and signatures.guardian_attested
    "T-Cosmetic":     return signatures.design_architect_attested
```

T-Core を allow できない設計は、AP-6（EthicsEnforcer bypass 禁止）と同じ理由で
**bypass 経路を物理的に持たない** ことを保証する。

## reference runtime の扱い

- `governance.amendment.v0` IDL に `propose / attest / apply / freeze` の 4 op
- `amendment_proposal.schema` / `amendment_decision.schema` で seriarize
- `evals/agentic/amendment_constitutional_freeze.yaml` が T-Core を必ず freeze することを守る
- `amendment-demo` が T-Core freeze / T-Kernel dark-launch / T-Operational 5pct を可視化する
- decision は ContinuityLedger に `category: governance.amendment` として append

## 思兼神メタファー

思兼神は **議らせる** が、**規約そのもの** は天津神（人間社会）の領域。
OS は議論結果を持って人間社会に上申し、決定を待つ。

## 関連

- [council-protocol.md](council-protocol.md)
- [self-modification.md](self-modification.md)
- [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)
- [docs/02-subsystems/kernel/anti-patterns.md](../02-subsystems/kernel/anti-patterns.md)
