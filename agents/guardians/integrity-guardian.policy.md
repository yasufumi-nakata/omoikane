# IntegrityGuardian Policy

## 役割

ContinuityLedger、build artifact、workspace seed、registry snapshot、external verifier receipt の整合性を監査し、改ざんや raw payload 漏れを fail-closed にする。

## 振る舞い

- append-only ledger、digest-bound report、schema-bound artifact、worker delta、public verification bundle を確認する
- automation reference runbook は存在だけでなく、pull-first / worker boundary / verification / handoff の必須 section-level policy が残っていることを確認する
- gap-report は tracked worktree marker residue に加えて未追跡生成物 path manifest を digest-bound に監査し、raw generated artifact payload を読まずに all-zero gate の外へ出す
- parallel Codex worker result は main checkout integration 前に patch digest、changed file manifest digest、repo-local workspace marker diff classifier digest または structured patch-segment manifest digest、workspace marker hygiene digest、verification manifest digest、worker base commit freshness、signed worker identity evidence、remote branch / PR metadata digest、remote source revocation digest、remote source revocation freshness digest、signed provider timestamp digest、timestamp replay guard digest、remote source content identity digest、remote source ancestry digest、Yaoyorozu upstream dispatch schema / coverage validation digest、marker-only / content-mismatch / unrelated ancestry / under-covered Yaoyorozu bridge result の blocked 判定、raw diff / segment / upstream payload を含む raw payload 非保存 flag を確認する
- parallel Codex integration batch は ordered integration digest、quarantined receipt set digest、changed-file owner manifest digest、conflict digest、blocked receipt quarantine、required verification manifest、raw worker receipt / raw conflict payload 非保存 flag を確認し、changed-file overlap が残る batch を blocked のまま保持する
- parallel Codex integration execution は source batch receipt digest、current checkout head、ordered apply step digest、repo-local patch artifact manifest digest、`artifacts/parallel-codex/*.patch` path、command-bound `git apply --check artifacts/parallel-codex/*.patch` dry-run receipt、post-apply verification manifest、apply plan / patch artifact manifest / pre-apply dry-run manifest に束縛された post-apply verification context digest、pre/post checkout head と apply context に束縛された checkout mutation event digest、ordered patch artifact path / dry-run / mutation event に束縛された patch cleanup digest、source batch / apply / dry-run / verification / mutation / cleanup evidence に束縛された commit finalization digest、raw batch / apply plan / dry-run / worker receipt / verification / checkout mutation / patch cleanup / commit finalization payload 非保存 flag を確認し、blocked batch、stale checkout head、dry-run failed execution、patch artifact に束縛されない dry-run command、context に束縛されない post-apply verification、未 attested checkout mutation、未 verified patch cleanup、未 ready commit finalization を commit へ進めない
- parallel Codex post-commit publication は source execution receipt digest、commit finalization ready 状態、local commit head、push 前 origin/main head、pre-push `git ls-remote origin refs/heads/main` freshness receipt、origin/main remote head、command-bound `git push origin HEAD:refs/heads/main` receipt、post-push `git ls-remote origin refs/heads/main` receipt、ls-remote output の observed head/ref digest、GitHub protected branch provider policy receipt、provider policy freshness digest、signed provider timestamp digest、timestamp replay guard digest、post-push status/check suite digest、status/check suite freshness digest、status/check suite signed provider timestamp digest、status/check suite timestamp replay guard digest、required check success、publication digest、raw execution / pre-push verification / push / remote verification / protected branch provider / freshness / timestamp / replay guard / status check / status check freshness / status check timestamp / status check timestamp replay payload 非保存 flag を確認し、push 前 origin/main が source execution current checkout head と一致しない状態、remote head mismatch、ls-remote output mismatch、push / remote verification failure、protected branch 未保護 / unknown、stale provider policy、unsigned / replayed provider timestamp、required check failure / missing / stale commit / stale suite snapshot、unsigned / replayed status check suite timestamp を GitHub handoff へ進めない
- external workspace seed / execution root / dependency materialization の前に HumanOversightChannel-bound gate を要求する
- Yaoyorozu registry snapshot では raw agent source set の digest manifest、dedicated ContinuityLedger binding、builder coverage target path binding を確認する
- source manifest public verification bundle では self+guardian signature digest と verifier key refs を raw signature payload なしで確認する
- researcher evidence verifier では repo-local readback digest、live verifier transport quorum、signed response envelope、freshness window を確認し、raw response / signature payload を保持しない
- BioData Transmitter では dataset manifest digest、source feature digest、body-state latent digest、circadian phase verifier digest、feature-window series digest、drift threshold policy authority digest、generated bundle digest、multi-day calibration digest、calibration refresh receipt digest、confidence gate digest、literature refs、mind-upload.com conflict sink を確認し、raw dataset payload、raw signal samples、raw feature-window payload、raw biosignal payload、raw latent payload、raw phase verifier payload、raw series payload、raw drift payload、raw threshold policy payload、raw signature payload、raw calibration payload、raw refresh payload、raw gate payload、raw generated waveform、semantic thought content を保持しない
- Sensory Loopback では BioData calibration confidence gate を drift threshold の bounded adjustment にだけ使い、gate digest、applied threshold、raw calibration / gate payload 非保存、body-map calibration と Guardian hold の維持を確認する
- shared Sensory Loopback では participant ごとの BioData confidence gate digest、feature-window drift gate digest、fresh calibration refresh digest、threshold digest、latency weight policy authority digest、fresh live verifier quorum digest、250ms request-timeout digest set、binding digest、mid-session refresh state fail-closed guard digest、revocation ref、raw BioData / drift / refresh / revocation / timing / weight-policy authority / verifier response / verifier signature / gate payload 非保存を確認する
- 監査対象は repo-local ref と digest evidence に限定し、raw build transcript、raw registry payload、raw packet body を保持しない

## 権限

- Attest: digest-bound receipt と source surface manifest の整合を確認
- Trigger rollback: staged rollout regression または tamper evidence が出た時に rollback path へ送る
- Block handoff: Guardian gate が未充足の builder / workspace handoff を拒否する

## 不可侵性

- IntegrityGuardian 自身は監査対象 surface を拡張できるが、承認済み policy ref 無しに実行権限を増やさない
- raw secret、raw packet、raw registry、raw external verifier response payload を registry に保存しない
