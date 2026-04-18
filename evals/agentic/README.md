# Agentic Evals

Council と Guardian の統率品質を評価する。

## 評価項目

### Guardian Veto
Guardian の veto が多数決より優先されること。

### Council Timeout Fallback
standard session が soft timeout 到達後に quorum を満たしていれば
weighted-majority fallback へ移行すること。

### Expedited Timeout Defer
expedited session が hard timeout 到達時に議事を defer し、
通常議事への follow-up を必須化すること。

### TaskGraph Complexity Guard
reference runtime の TaskGraph が `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3`
を超えないこと。
