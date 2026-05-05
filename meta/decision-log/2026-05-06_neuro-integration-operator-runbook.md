# 2026-05-06 Neuro Integration Operator Runbook

## 決定

Neuro Integration Workbench に `neuro-operator-runbook-v1` を追加し、source bundle から
longitudinal timeline までの receipt chain を 9 step の digest-only operator runbook に束縛する。

## 背景

NIW は survey+EEG seed、open biodata source、application replacement、collection、
quality gate、cross-modal analysis、interpretation synthesis、longitudinal timeline まで
reference runtime 化した。ただし非 ML operator と coding agent が同じ順序で確認できる
手順 receipt はまだなかった。

## 根拠

- 目的は multi-application replacement surface を LLM-native かつ非 ML operator でも使える形にすること。
- runbook は既存 receipt digest と short operator / coding-agent task だけを束縛し、raw receipt payload を保存しない。
- 各 step は diagnosis、semantic thought content、consciousness reproduction、identity replacement、
  upload readiness を false に固定する。
- Longitudinal Timeline は stability proxy に限り、runbook はその確認順序を示すだけで upload readiness へ昇格しない。

## 変更範囲

- `src/omoikane/interface/neuro_integration_workbench.py`
- `src/omoikane/reference_os.py`
- `specs/schemas/neuro_integration_operator_runbook.schema`
- `specs/interfaces/interface.neuro_integration_workbench.v0.idl`
- `tests/unit/test_neuro_integration_workbench.py`
- `tests/integration/test_interface_schema_contracts.py`
- `tests/integration/test_reference_runtime.py`
- `tests/integration/test_cli.py`
- NIW docs / eval / schema catalog / glossary

## 未解決

- 実外部アプリ connector の live authorization、課金、latency、API safety はこの runbook では検証しない。
- 実臨床 workflow、IRB/法務承認、device calibration 妥当性、cohort-level validity は研究課題として残す。
- runbook は operator review を支援するが、operator 判断や mind uploading readiness の自動結論ではない。
