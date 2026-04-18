# Continuity Evals

主観時間の連続性、または連続性証拠の整合性を評価する。

## 評価項目

### Continuity Ledger Integrity
ハッシュチェーンの連続性、署名の正当性。

### Continuity Self-Modify Chain
`self-modify` 記録が `sha256` チェーンと `self/council/guardian` 三者署名を満たすか。

### Connectome Snapshot Contract
connectome snapshot の参照整合性、閉路構造、invariant 記述の存在。

### MemoryCrystal Compaction
MemoryCrystal manifest が append-only strategy と source retention を守るか。

### Episodic Stream Handoff
EpisodicStream が canonical event shape を保ち、
MemoryCrystal へそのまま compaction handoff できるか。

### Semantic Memory Projection
MemoryCrystal segment からの semantic projection が
read-only policy と deferred procedural boundary を守るか。

### Procedural Memory Preview
MemoryCrystal segment と Connectome snapshot からの procedural preview が
read-only policy と bounded weight delta を守るか。

### Qualia Tick Monotonicity
QualiaBuffer の tick_id が単調増加か。

### Substrate Migration Continuity
substrate 移行前後で連続性ログにギャップがないか。

### Scheduler Stage Rollback
AscensionScheduler が Method A の固定順序を守り、timeout 超過時に前段 stage へ戻せるか。

### Scheduler Method Profiles
AscensionScheduler が Method B では substrate signal で pause / rollback し、
Method C では destructive scan 開始後に fail-closed するか。

### Subjective Continuity Self-Report
本人による「途切れていない」感覚の自己報告。

### Third-Party Witness Consistency
立会第三者の観察記録との照合。

## 失敗時

- ギャップ検出 → 「主観時間の不確定区間」として永続マーク
- 本人＋ Guardian に通知
- 重大ギャップ → Council 召集
