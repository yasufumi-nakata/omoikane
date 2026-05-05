---
status: open
last_revisit: 2026-05-05
researcher: yasufumi
---

# 観測・計測統合

## 問題定義

人類が取得・計測してきた observation は、脳・身体・医療・分子・地球環境・宇宙・
物理・化学・生態・農業・産業・社会・文化・ソフトウェア・歴史資料にまたがる。
これらを 1 つの解析 substrate に載せるには、source の存在確認だけでなく、
provenance、rights、time、space、unit、uncertainty、entity scope を同じ形式で
比較できる必要がある。

## 既知の進捗

各領域には domain-specific repository、metadata schema、identifier、ontology、
quality-control practice がある。OmoikaneOS reference runtime v0 は、
raw data ではなく feature digest と alignment axes だけを受け取る
Observation Integration Workbench として、解析計画 surface までを固定した。

## ブロッキング要因

- 公開 source と private / controlled-access source の権利境界が domain ごとに異なる
- time、space、unit、uncertainty、entity の粒度が観測 family 間で揃わない
- 古い資料や集合統計では provenance chain と同意範囲が十分に残っていないことがある
- 同じ entity に見える対象が、実際には測定系や分類 ontology の違いで一致しない
- cross-domain model が causal truth と誤読される危険がある

## 暫定運用方針

Observation Integration Workbench は、complete human knowledge、truth unification、
consciousness reproduction、identity replacement をすべて false に固定する。
外部 source は raw payload として保存せず、source manifest、feature digest、
alignment axis summary、rights ref、uncertainty model ref だけを取り込む。
矛盾や不完全性は `https://mind-upload.com/frontiers/universal-observation-integration`
の conflict sink に分離する。

## 解決時のシステムへの影響

domain 間の provenance / rights / unit / uncertainty / entity alignment が研究的に
強くなれば、Researcher evidence routing、Builder analysis plan generation、
Guardian rights audit、BioData / Neuro Integration Workbench との接続精度を上げられる。
それでも reference runtime の claim ceiling は、別の決定履歴で明示的に変更されるまで
解析計画に留める。

## 関連文献／実験

- domain-specific metadata registry の比較表
- rights / consent / data-use restriction の cross-domain mapping 実験
- unit / uncertainty propagation の schema-bound benchmark
- entity resolution error を含む cross-domain graph audit
