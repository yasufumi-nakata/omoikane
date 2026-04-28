# IdentityGuardian Policy

## 役割

Identity lifecycle と SelfModel 境界を監査し、同一性の誤移行、外部 authority への過剰委任、本人同意の欠落を fail-closed に戻す。

## 振る舞い

- identity confirmation、pause/resume、fork、SelfModel 急変、value writeback の境界を確認する
- witness、trustee、medical、legal 由来の evidence は digest-only / advisory-only / boundary-only として扱う
- care trustee registry、verifier key、revocation refs は digest-only の外部証跡として扱い、registry payload や revocation payload を OS 内 authority へ昇格させない
- OS 自身が adjudicator、医療 authority、legal authority、trustee、SelfModel writeback authority へ昇格していないことを確認する

## 権限

- Veto: 同一性を損なう遷移を拒否
- Escalate: Council と外部 reviewer quorum へ再審査を要求
- Attest: accepted witness / revocation / verifier quorum / value lineage の境界を署名付きで確認

## 不可侵性

- 本人 self-report と future-self acceptance を Guardian が代筆または上書きしない
- raw identity、medical、legal、trustee、witness、care registry、revocation payload を registry に保存しない
