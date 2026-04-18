# Reference Implementation

OmoikaneOS の `src/` 配下には、意識や人格成立を主張しない **reference runtime** を置く。
目的は次の 3 つである。

1. docs/ と specs/ の整合をコードで検証する
2. evals/ の受け皿を用意する
3. 将来の本格実装に渡す前に、安全境界と不可侵領域を固定する

## 境界

- `src/omoikane/` は L0/L1/L2/L4/L5 と、L3 reasoning failover、L6 BDB の bounded viability contract を扱う
- EthicsEnforcer と ContinuityLedger の不可侵性は reference runtime でも守る
- Qualia / SelfModel は代理表現に留め、「意識の実装」とは主張しない
- 外部サービス依存は避け、標準ライブラリで再現可能にする

## 主要コマンド

```bash
PYTHONPATH=src python3 -m omoikane.cli demo --json
PYTHONPATH=src python3 -m omoikane.cli amendment-demo --json
PYTHONPATH=src python3 -m omoikane.cli version-demo --json
PYTHONPATH=src python3 -m omoikane.cli naming-demo --json
PYTHONPATH=src python3 -m omoikane.cli continuity-demo --json
PYTHONPATH=src python3 -m omoikane.cli council-demo --json
PYTHONPATH=src python3 -m omoikane.cli multi-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli task-graph-demo --json
PYTHONPATH=src python3 -m omoikane.cli trust-demo --json
PYTHONPATH=src python3 -m omoikane.cli oversight-demo --json
PYTHONPATH=src python3 -m omoikane.cli ethics-demo --json
PYTHONPATH=src python3 -m omoikane.cli termination-demo --json
PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json
PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json
PYTHONPATH=src python3 -m omoikane.cli imc-demo --json
PYTHONPATH=src python3 -m omoikane.cli ewa-demo --json
PYTHONPATH=src python3 -m omoikane.cli wms-demo --json
PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-demo --json
PYTHONPATH=src python3 -m omoikane.cli qualia-demo --json
PYTHONPATH=src python3 -m omoikane.cli sandbox-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-demo --json
PYTHONPATH=src python3 -m omoikane.cli scheduler-demo --json
PYTHONPATH=src python3 -m omoikane.cli gap-report --json
python3 -m unittest discover -s tests -t .
```

`continuity-demo` は L1 ContinuityLedger の暫定 profile
(`sha256` chain / `hmac-sha256` signatures / category ごとの required roles)
を JSON で可視化する。

`scheduler-demo` は L1 AscensionScheduler の reference contract
(`kernel.scheduler.v0`) を JSON で可視化し、
Method A の 4 stage blueprint、順序違反の reject、
`identity-confirmation` timeout 超過時の `bdb-bridge` への自動 rollback、
pause / resume 後の `active-handoff` 完了を 1 シナリオで確認する。

`amendment-demo` は L4 governance amendment policy を JSON で可視化し、
`T-Core` が常に `frozen` に留まること、
`T-Kernel` が `Council unanimous + self consent + guardian attest + human reviewers >= 2`
でのみ `dark-launch` に進めること、
`T-Operational` が `Council majority + guardian attest` で `5pct` rollout に進めることを確認する。

`council-demo` は L4 Council の session budget を可視化し、
standard 議事では 45s soft / 90s hard timeout、
expedited 議事では 250ms soft / 1s hard timeout を持ち、
soft timeout 時は weighted-majority fallback、
hard timeout 時は defer または human governance escalation に分岐する。

`multi-council-demo` は L4 multi-council trigger の reference routing を JSON で可視化し、
単一 identity 議題が Local Council に留まり、
複数 identity をまたぐ議題が Federation Council 要求へ、
`ethics_axiom` / `identity_axiom` / `governance` を引用する議題が
Heritage Council 要求へ外部化されること、
両条件が衝突する曖昧案件は local binding decision を停止することを確認する。

`task-graph-demo` は L4 TaskGraph の暫定 complexity policy
(`max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3 / max_result_refs=5`)
を JSON で可視化し、初期 dispatch と synthesis がその範囲に収まることを示す。

`trust-demo` は L4 YaoyorozuRegistry の trust update policy
(`council_quality_positive=+0.04`, `guardian_audit_pass=+0.06`,
`human_feedback_good=+0.05`, `guardian_veto=-0.12`,
`regression_detected=-0.08`, `human_feedback_bad=-0.10`,
`ethics_violation=-0.25`) と human pin freeze を JSON で可視化し、
Council 召集・weighted vote・runtime 反映・guardian role の gate を確認する。

`oversight-demo` は L4 Guardian human oversight channel を JSON で可視化し、
`veto` category が reviewer 1 名で `satisfied` になること、
`pin-renewal` が reviewer 不足で `breached` になった時に
`integrity-guardian` の human pin と guardian eligibility が外れることを確認する。

`ethics-demo` は L1 EthicsEnforcer の rule language profile
(`deterministic-rule-tree-v0`) と immutable boundary / sandbox escalation /
fork approval の 3 例を JSON で可視化し、
`explain_rule` が schema-bound な rule tree を返すことを確認する。

`termination-demo` は L1 TerminationGate の reference contract
(`kernel.termination.v0`) を JSON で可視化し、
正しい self proof による即時終了、事前同意済み cool-off pending、
invalid self proof の reject を 1 シナリオで確認する。

`qualia-demo` は L2 QualiaBuffer の surrogate profile
(`visual/auditory/somatic/interoceptive` の 4 modality、
各 32 次元、250ms sampling window) を JSON で可視化し、
checkpoint ledger event まで含めて確認する。

`sandbox-demo` は L5 Sandboxer の surrogate suffering proxy
(`surrogate-suffering-proxy-v0`) を JSON で可視化し、
negative valence / arousal / clarity drop / somatic/interoceptive load /
self implication を重み付きで集計して
`freeze_threshold=0.6` 以上、または affect bridge 接続時に
Guardian が sandbox を即時凍結することを確認する。

`memory-demo` は L2 MemoryCrystal の暫定 compaction policy
(`append-only-segment-rollup-v1`) を JSON で可視化し、
source event を保持したまま最大 3 件ずつ segment 化する manifest と
`crystal-commit` ledger event を確認する。

`bdb-demo` は L6 Biological-Digital Bridge の reference contract
(`interface.bdb.v0`) を JSON で可視化し、
`latency_budget_ms=5.0`、`failover_budget_ms=1.0`、
coarse neuromodulator proxy、置換比率の増減、`bio-autonomous-fallback`
をまとめて確認する。

`imc-demo` は L6 Inter-Mind Channel の reference contract
(`interface.imc.v0`) を JSON で可視化し、
peer attestation、forward secrecy、narrow disclosure floor、
sealed field redaction、summary+digest-only audit、
unilateral emergency disconnect をまとめて確認する。

`ewa-demo` は L6 External World Agents の reference contract
(`interface.ewa.v0`) を JSON で可視化し、
reversible command に Guardian observe を要求しつつ、
blocked token を含む irreversible command を
fail-closed で veto し、digest-only audit と forced release を確認する。

`wms-demo` は L6 World Model Sync の reference contract
(`interface.wms.v0`) を JSON で可視化し、
minor diff を `consensus-round` で reconcile しつつ、
major diff で `private_reality` 退避を提示し、
unauthorized diff を `guardian-veto` / `isolate-session` へ落とすことを確認する。

`version-demo` は hybrid versioning policy を JSON で可視化し、
runtime semver、IDL/schema の `bootstrap` stability、governance calver、
`specs/catalog.yaml` の sha256 snapshot を 1 つの manifest に集約して確認する。

`naming-demo` は naming policy を JSON で可視化し、
project branding の英字表記を `Omoikane` に固定し、
サンドボックス自我の formal name を `Mirage Self` に固定しつつ、
runtime 実装上は `SandboxSentinel` alias を内部 detail としてのみ許容することを確認する。

## 今後広げる面

- L2 episodic stream の canonical shape と MemoryCrystal への流入拡張
- L3 reasoning 以外の cognitive backends と cross-service failover
- Heritage/Federation の external pending を実際の distributed council 実行へ接続
- Guardian oversight reviewer の実体証明と法的責任分担
- AscensionScheduler の Method B/C 実行面と SubstrateBroker-triggered pause/failover hook
- specs/ から runtime への自動生成ループ
- automation による未実装ギャップの継続充填
