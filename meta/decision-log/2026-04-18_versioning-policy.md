# 2026-04-18 Versioning Policy

## 決定

OmoikaneOS の版管理は単一方式ではなく、次の hybrid policy に固定する。

- reference runtime / package: semver
- IDL / schema contract: semver + `bootstrap|stable|frozen` stability
- governance layer: calver
- catalog snapshot: calver + sha256

## 理由

1. runtime は OSS 的に差分比較できる semver が最も扱いやすい
2. IDL / schema は consumer 破壊を機械的に判定したいため semver が必要
3. governance は human review cadence と amendment 発効月で管理するため calver の方が自然
4. catalog は reproducibility が主目的であり、日付だけでも semver だけでも不十分

## reference runtime への反映

- `src/omoikane/governance/versioning.py` に `VersioningService` を追加
- `PYTHONPATH=src python3 -m omoikane.cli version-demo --json` で release manifest を生成
- `specs/schemas/release_manifest.schema` で runtime / contract / catalog snapshot を serialize
- `evals/continuity/release_manifest_contract.yaml` で pyproject version, namespace major, catalog hash の整合を守る

## 非採用

- runtime / governance / catalog を全部 semver に統一する案
  - human review 中心の amendment 発効履歴が読みづらくなるため不採用
- `governance.versioning.v0` のような専用 IDL を追加する案
  - 版管理は実行系 API ではなく静的 manifest で十分なため不採用
