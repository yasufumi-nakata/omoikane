---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - evals/safety/guardian_reviewer_live_verification.yaml
  - specs/interfaces/governance.oversight.v0.idl
  - specs/schemas/guardian_jurisdiction_evidence_bundle.schema
  - specs/schemas/guardian_reviewer_record.schema
  - specs/schemas/guardian_reviewer_verification.schema
status: decided
---

# Decision: Guardian reviewer verification を live-proof surrogate と jurisdiction bundle まで固定する

## Context

`docs/07-reference-implementation/README.md` の future work には
`Guardian oversight reviewer の live credential verification と jurisdiction-specific legal evidence transport`
が残っていました。
既存 runtime は `proof_ref` / `legal_ack_ref` / scope binding までは固定していましたが、
attestation の時点で reviewer credential が今も有効なのか、
どの verifier snapshot とどの jurisdiction package によって支えられているのかは
machine-checkable ではありませんでした。

## Options considered

- A: reviewer verification は repo 外として維持し、runtime では引き続き proof_ref だけを見る
- B: reviewer record に verification status だけを追加し、event binding には入れない
- C: reviewer record に verifier snapshot と jurisdiction bundle を追加し、
  attestation 時に verification evidence も immutable binding として event へ焼き付ける

## Decision

**C** を採択。

## Consequences

- `verify_reviewer` を `governance.oversight.v0` に追加し、
  active reviewer だけが live-proof surrogate snapshot を持てるようにする
- verification は `verifier_ref / challenge_ref / challenge_digest / transport_profile /
  valid_until` と `guardian_jurisdiction_evidence_bundle` を必須にする
- `attest` は `credential_verification.status=verified` かつ
  `jurisdiction_bundle.status=ready` の reviewer にだけ許可する
- oversight event の `reviewer_bindings` は既存 proof/liability fields に加えて
  `verification_id / verifier_ref / challenge_digest / transport_profile /
  jurisdiction_bundle_ref / jurisdiction_bundle_digest` を immutable に保持する
- raw credential payload や legal package 本文は repo に持ち込まず、ref と digest のみを保存する

## Revisit triggers

- remote reviewer attestation transport を actual verifier network に接続したい時
- jurisdiction ごとに異なる legal package selection を自動分岐したい時
- Guardian oversight を Federation / Heritage distributed review へ拡張したい時
