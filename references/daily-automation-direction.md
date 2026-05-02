# Daily Automation Direction

Omoikane automation が毎時または毎日走る時の方向性です。
このファイルは「何を進めるか」と同じくらい、「進んでいない時に何を更新しないか」を固定します。

## Purpose

- OmoikaneOS を、マインドアップロードに向けた design corpus と safe reference runtime として保つ
- 現時点で実装できる範囲を BioData Transmitter / Biological-Digital Bridge / Council / ledger / builder runtime の検証可能な contract に限定する
- 意識、主観同一性、thought content、完全な人格再現は research frontier として扱い、reference runtime の達成済み claim にしない

## Daily Triage

1. `git status --short --branch` と `git pull --ff-only` を先に通す
2. Spark Desktop の件名だけで Codex 宛の追加指示を確認する
3. `README.md`、`meta/open-questions.md`、`docs/05-research-frontiers/README.md`、`docs/07-reference-implementation/README.md`、`specs/catalog.yaml`、`references/operating-playbook.md`、`PYTHONPATH=src python3 -m omoikane.cli gap-report --json` を読む
4. repo 内で deterministic に閉じられる gap があれば、runtime / schema / eval / CLI / tests / docs / decision log を揃えて更新する
5. 研究 frontier 側に新しい一次根拠や人間 yasufumi の明示指示がある場合だけ、frontier note と claim ceiling を更新する
6. repo 内 gap も新しい研究根拠も無い場合は no-op として完了し、変更・commit・push を作らない

## Update Classes

- `runtime-gap`: reference runtime、schema、IDL、eval、CLI、tests で検証可能な未充足項目を閉じる
- `research-frontier-sync`: 文献、実験、人間の判断などの外部根拠を frontier note に反映し、runtime claim を上げずに境界を更新する
- `automation-hygiene`: pull-first、required reference、gap-report、verification、decision log index など automation 自体の継続性を保つ
- `no-op-watch`: 新しい gap や根拠が無く、既存 claim を維持するだけの日。これは正常完了であり、無理に差分を作らない

## Claim Ceiling

- BioData Transmitter は `body-state-surrogate-input-only` を上限にする
- 生体データ変換は、宣言済み biosignal から体内状態 latent を経由して別 biosignal proxy を生成する reference contract であり、意識再現の達成ではない
- BDB は bounded viability、latency budget、fail-safe fallback、可逆な置換比率の検証に留める
- 主観同一性、意識基板、qualia encoding、scan fidelity、death and continuity が research frontier の open status である限り、マインドアップロード成立済みとは書かない

## No-Progress Policy

人類側の研究、実験、制度、または yasufumi の判断が進んでいない日は、更新が無いことを正しい状態として扱います。
次の行為は禁止します。

- 進展を装う placeholder file や空の decision log を増やす
- 外部根拠なしに frontier status を `partial-solution` や `solved` へ上げる
- prose だけで claim ceiling を上げる
- tests や gap-report を通していない runtime claim を README に反映する

no-op の最終報告には、少なくとも確認した gate、見た truth source、no-op とした理由を日本語で短く残します。

## Evidence Intake

研究 frontier を更新できる根拠は、次のいずれかに限ります。

- yasufumi が明示した研究結果または設計判断
- 査読論文、preprint、公式 dataset、公式 protocol、実験ログなど追跡可能な一次根拠
- repo 内 runtime / eval / test が新しく示した machine-checkable evidence

外部根拠を入れる場合は、frontier note に未解決点と blocking factor を残し、decision log には採用理由と残る claim ceiling を記録します。

## Reporting

automation の最終報告は日本語で、次の形に揃えます。

- 更新区分: `runtime-gap` / `research-frontier-sync` / `automation-hygiene` / `no-op-watch` / `blocked-preflight`
- 変更ファイル、または no-op の場合は変更なし
- 検証コマンドと結果
- 残る大きな open question
