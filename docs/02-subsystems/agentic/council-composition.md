# Council Composition

Council（評議体）は **固定の閣僚** ではなく、案件ごとに **動的に召集** される。

## 常設役割

- **Speaker**: 議事進行
- **Recorder**: EthicsLedger への記録
- **Guardian Liaison**: Guardian エージェントとの連絡
- **Self Liaison**: 本人（自我）との連絡

## 案件ごとに召集される役割

| 案件種別 | 召集される Agent タイプ |
|---|---|
| Substrate Migration | SubstrateExpert, SafetyOfficer, ContinuityAuditor |
| Memory Edit Request | MemoryEthicist, NeuropsychAnalogue, PrivacyOfficer |
| Self-Modify Patch | DesignAuditor, RegressionTester, ConservatismAdvocate |
| Inter-Mind Negotiation | DiplomatAgent, IdentityProtector |
| Fork Request | FamilyAdvocate, LegalAdvisor, EthicsCommittee |
| Daily Routine | （召集なし、SOP のみ） |

## 召集アルゴリズム

```
on incoming proposal P:
  required_roles = lookup(case_type(P))
  candidates = YaoyorozuRegistry.filter(role in required_roles)
  for r in required_roles:
    select top-K by trust_score(r)
    invite to Council session
  Speaker opens session
```

session_mode ごとの budget は固定する:

- standard: soft timeout 45s / hard timeout 90s / quorum 3 / max 4 rounds
- expedited: soft timeout 250ms / hard timeout 1s / quorum 2 / max 1 round

## 議決方式

- **合意（consensus）** が原則
- 不一致時は **加重多数決**（trust_score を重みに）
- **veto 権** は Guardian と本人 (Self Liaison) のみ持つ
- veto 行使時は EthicsLedger に理由を記載
- soft timeout では quorum が揃った時だけ weighted-majority に落とし、
  それでも決まらない案件は defer または human escalation に送る

## トラスト管理

各 Agent には trust score が付与される（→ [trust-management.md](trust-management.md)）。
- 過去の判断品質
- Guardian の評価
- 本人のフィードバック

trust score が閾値以下の Agent は召集されない。

## 多 Council 化（将来）

substrate や文化圏により規約解釈が異なる場合、Council を **多重化** する。
- Local Council: 当該自我の専属
- Federation Council: 自我間取引・共有現実の調整
- Heritage Council: 文化・歴史的規約の維持

これは未解決領域 → [docs/05-research-frontiers/governance.md](../../05-research-frontiers/governance.md)

## 思兼神メタファーとの整合

『古事記』の天の石屋戸の場面では、思兼神が **「八百万神を集めて議らせ」** た。本仕様の動的召集は神話と一致する。
