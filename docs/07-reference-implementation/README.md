# Reference Implementation

OmoikaneOS の `src/` 配下には、意識や人格成立を主張しない **reference runtime** を置く。
目的は次の 3 つである。

1. docs/ と specs/ の整合をコードで検証する
2. evals/ の受け皿を用意する
3. 将来の本格実装に渡す前に、安全境界と不可侵領域を固定する

## 境界

- `src/omoikane/` は L0/L1/L2/L4/L5 と、L3 reasoning failover の最小骨格のみを扱う
- EthicsEnforcer と ContinuityLedger の不可侵性は reference runtime でも守る
- Qualia / SelfModel は代理表現に留め、「意識の実装」とは主張しない
- 外部サービス依存は避け、標準ライブラリで再現可能にする

## 主要コマンド

```bash
PYTHONPATH=src python3 -m omoikane.cli demo --json
PYTHONPATH=src python3 -m omoikane.cli continuity-demo --json
PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json
PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-demo --json
PYTHONPATH=src python3 -m omoikane.cli gap-report --json
python3 -m unittest discover -s tests -t .
```

`continuity-demo` は L1 ContinuityLedger の暫定 profile
(`sha256` chain / `hmac-sha256` signatures / category ごとの required roles)
を JSON で可視化する。

## 今後広げる面

- L2 connectome から memory crystal / episodic stream への展開
- L3 reasoning 以外の cognitive backends と cross-service failover
- L6 interface protocol の adapter
- specs/ から runtime への自動生成ループ
- automation による未実装ギャップの継続充填
