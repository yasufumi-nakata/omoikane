---
status: decided
related:
  - 2026-04-18_versioning-policy.md
  - 2026-04-27_catalog-coverage-gap-report.md
---

# Decision: catalog hash を generated inventory receipt に昇格する

## Context

`gap-report --json` は catalog coverage gap を all-zero として返せますが、
`version-demo` の release manifest は `specs/catalog.yaml` の sha256 のみを
保持していました。この状態では、catalog entries の実体数、priority/kind 分布、
実装済み schema/IDL contract の登録 coverage、欠落・重複ゼロの確認が
reviewer-facing artifact として直接検証できません。

## Decision

`VersioningService` は `specs-catalog-generated-inventory-v1` の
`catalog_inventory_receipt` を生成し、release manifest に埋め込む。
receipt は `specs/catalog.yaml` の source digest、entry digest 群、
priority/kind counts、declared file coverage、implemented schema/IDL coverage、
missing / duplicate / catalog coverage gap counts を持ち、同じ payload から
`inventory_digest` を計算する。

## Consequences

- `version-demo --json` は catalog hash だけでなく structured inventory receipt を返す。
- `release_manifest.schema` と `catalog_inventory_receipt.schema` が同じ artifact family を検証する。
- `evals/continuity/catalog_inventory_receipt.yaml` と schema contract tests が、欠落・重複・未登録 contract file を release manifest 側で検出できることを固定する。
- IntegrityGuardian は release manifest の catalog inventory attestation を監査対象に含める。
