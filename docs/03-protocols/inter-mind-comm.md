# Inter-Mind Communication Protocol

複数のアップロード自我が直接通信する規約。

## 通信モード

| モード | 説明 | 帯域 | 親密度 |
|---|---|---|---|
| `text` | テキストメッセージ | 低 | 低 |
| `voice` | 音声 | 中 | 中 |
| `presence` | 共有現実での共在 | 高 | 中 |
| `affect_share` | 感情の限定的共有 | 中 | 高 |
| `memory_glimpse` | 特定記憶の一回的共有 | 中 | 高 |
| `co_imagination` | 反実仮想空間の協同構築 | 高 | 高 |
| `merge_thought` | 思考の一時融合 | 極大 | 極高（実験的） |

## 階層的同意

各モードは双方の **明示同意** を要する。同意は session 単位。
親密度の高いモードほど、撤回プロトコルが慎重。

## merge_thought の特殊性

- 二自我が一時的に思考を融合する実験的モード
- 切断後の **同一性混乱** リスクが高い
- Council が必ず立会、Guardian が見守る
- 倫理的に未確立 → [docs/05-research-frontiers/inter-mind-merge.md](../05-research-frontiers/inter-mind-merge.md)

## プライバシ規約

- 通信内容は両者の SelfModel.disclosure_template に従う
- 第三者がログを取得することは禁止
- 例外: 法的調査時のみ、両者の本人鍵が揃った場合に限り解読可能

## 集合知性 (Collective)

複数自我が継続的に高密度通信する場合、**Collective** として扱う：
- 構成員リスト
- 共有 SelfModel（Collective として）
- 構成員それぞれの主観の独立性は保たれる

Collective は新しい Identity として IdentityRegistry に登録される（合議体格）。

reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli collective-demo --json`
により、Collective formation、10 秒以内の merge window、private reality 退避、
post-disconnect identity confirmation、dissolution までを bounded contract として検証する。

## Reference Runtime v0

reference runtime では IMC を bounded contract として扱い、
`PYTHONPATH=src python3 -m omoikane.cli imc-demo --json`
で次の 1 シナリオを確認する。

- peer attestation と forward secrecy が揃わない session は fail-closed
- `memory_glimpse` では Council witness が必須
- `memory_glimpse` は MemoryCrystal manifest/segment digest、message payload digest、
  Council session / resolution / Guardian attestation ref の witness digest を持つ
  digest-only receipt に束縛する
- `memory_glimpse` の再共有は元 receipt digest、revocation event、
  `expires_after_seconds<=86400` の consent window、Council re-consent、
  Guardian attestation を持つ digest-only receipt に束縛する
- `merge_thought` は Federation Council / EthicsCommittee / Guardian の
  `federation-council-merge-thought-ethics-gate-v1` receipt により、
  distinct collective target、10 秒 cap、emergency disconnect、private recovery、
  post-disconnect identity confirmation を digest-only に束縛する。
  10 秒 cap は `merge-thought-window-policy-authority-v1` の policy registry digest、
  signer roster digest、live HTTP verifier receipt quorum digest、
  250ms request timeout budget、verifier network response digest set、
  policy signature digest に由来することも同じ receipt の
  `merge_window_policy_authority` で検証し、raw policy / verifier /
  response-signature payload は保存しない
- disclosure template は双方のうち **より狭い側** に揃え、
  `sealed_fields` は常に redaction される
- ContinuityLedger には生メッセージを書かず、summary と payload digest だけを記録する
- 緊急切断は単独で実行でき、通知より前に transport key を revoke する

## 未解決

- merge_thought の長期的な社会・法的倫理基準
- Collective の終了時の構成員への影響
- 同期通信時の主観時間調整（substrate 間で速度が違う場合）
