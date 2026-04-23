---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-cross-substrate-transfer-receipt.md#agentic.trust.remote-attestation-federation
next_gap_ids:
  - agentic.trust.destination-revocation-renewal-history
---

# Decision: Trust transfer receipt に live verifier federation と re-attestation cadence を内包する

## Context

2026-04-24 時点で `trust-transfer-demo` は
`source-guardian` / `destination-guardian` / `human-reviewer` の
fixed 3 者 quorum と snapshot preserve までは public contract 化されていましたが、
human reviewer attestation を live remote verifier network に束縛する artifact と、
その attestation をいつ更新し直すかの cadence が未定でした。

このままでは cross-substrate trust transfer が
「一度 imported された後に verifier freshness が切れても検知できない receipt」
に留まり、bounded remote verifier federation を repo 内 runtime で
machine-checkable に閉じられません。

## Options considered

- A: verifier federation と cadence を docs 上の future work に残し、receipt には入れない
- B: trust transfer と別 artifact として `re-attestation-demo` を増やす
- C: 既存 `trust_transfer_receipt` の `federation_attestation` 配下に
  `remote_verifier_federation` と `re_attestation_cadence` を追加する

## Decision

**C** を採択。

## Consequences

- `trust-transfer-demo` は fixed guardian/human quorum に加えて、
  `guardian-reviewer-remote-attestation-v1` の 2 verifier receipt を
  human reviewer attestation へ束縛した `remote_verifier_federation` を返す
- `re_attestation_cadence` は `attested_at` / `renew_after=10m` /
  `grace_window=240s` / `valid_until=min(verifier freshness)` を固定し、
  `renew_after + grace_window <= valid_until` の時だけ current と見なす
- `TrustService.validate_transfer_receipt()` は
  `live_remote_verifier_attested` /
  `remote_verifier_receipts_bound` /
  `re_attestation_cadence_bound` /
  `re_attestation_current`
  を public validation surface として返す
- schema / IDL / eval / CLI / integration test / unit test は
  verifier federation と cadence binding を継続検証する

## Revisit triggers

- trust transfer に destination-side revocation や renewal history ledger を追加したくなった時
- verifier federation を single jurisdiction から multi-root / cross-jurisdiction へ広げたくなった時
- live verifier receipt を redacted export profile へ分岐したくなった時
