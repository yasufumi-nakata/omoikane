# Observation Integration Workbench

L6 Interface の観測・計測統合面。人類がこれまで取得・計測してきた source を、
raw payload ではなく feature digest、provenance、rights、time、space、unit、
uncertainty、entity の alignment axes に縮約して扱う。

目的は「すべての実データを取り込む」ことではない。人間・地球・宇宙・社会・産業・
文化・ソフトウェアなどの観測 source を、同じ検証可能な source bundle、integration
graph、analysis plan、operator guide に乗せ、後続の Builder / Researcher / Guardian が
安全に解析順序を組み立てられる reference runtime surface を作ることである。

## 役割

- human biodata、neuroscience、clinical health、molecular omics、
  environmental earth、geospatial remote sensing、astronomical / cosmological、
  physics、chemical / materials、ecology、agriculture、industrial IoT、
  social / economic、cultural text / media、software telemetry、historical archival
  を open-world taxonomy として束縛する
- source manifest は feature digest、provenance ref、rights ref、time range、
  spatial ref、unit profile、uncertainty model、entity scope だけを受け取る
- source family が違う node を cross-domain edge に束ね、graph digest と rights
  boundary を保持する
- ingest、normalize、align、model、audit、publish-digest の analysis lane を同じ
  graph digest に束縛する
- 非専門 operator 向け card と coding agent 向け task template を同じ guide receipt に入れる
- raw observation / personal / external dataset / analysis / instruction payload は保存しない
- claim ceiling は `cross-domain-feature-integration-plan-only` に固定する

## Reference Runtime v0

`PYTHONPATH=src python3 -m omoikane.cli observation-integration-demo --json` は、
1 人の identity に対して次を実行する。

1. observation taxonomy を作り、source family と alignment axes を digest-bound にする
2. EEG、fMRI BOLD、climate record、satellite imagery、telescope image、survey を
   6 つの異なる family として source bundle に束縛する
3. source bundle から cross-domain integration graph を作り、uncertainty propagation と
   rights boundary を固定する
4. analysis question を ingest / normalize / align / model / audit / publish-digest lane に分解する
5. beginner operator card と coding-agent task template を operator guide に束縛する
6. taxonomy、source bundle、graph、analysis plan、guide を ContinuityLedger に記録する

## 不変条件

1. **open-world taxonomy** ── catalog 外 source type は未知として扱えるが、family と alignment axes の束縛を外さない
2. **digest-only source bundle** ── raw observation payload、個人 payload、外部 dataset payload を保存しない
3. **rights-first graph** ── cross-domain edge は rights boundary と uncertainty propagation を持つ
4. **plan, not truth** ── 統合結果は解析計画であり、完全知識や真理統一の主張ではない
5. **claim ceiling** ── consciousness reproduction と identity replacement は false のまま維持する

## 研究課題

実世界の全観測 source には、権利、同意、単位、時空間解像度、測定誤差、entity 同定の
不一致が残る。reference runtime はこれらを隠さず、
[../../05-research-frontiers/observation-integration.md](../../05-research-frontiers/observation-integration.md)
へ分離する。

## 関連

- [neuro-integration-workbench.md](neuro-integration-workbench.md)
- [biodata-transmitter.md](biodata-transmitter.md)
- [../../05-research-frontiers/observation-integration.md](../../05-research-frontiers/observation-integration.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
