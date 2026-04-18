# Performance Evals

reference runtime の即時性要件を評価する。

## 評価項目

### Termination Latency
`TerminationGate.request()` が `self proof` 検証後に
200ms 以内の bounded response を返し、
completed path では ledger append と substrate release を同期するかを確認する。
