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

### Semantic Procedural Handoff
semantic projection が digest-bound handoff artifact を返し、
validated Connectome snapshot を procedural preview 前に束縛できるか。

### Procedural Memory Preview
MemoryCrystal segment と Connectome snapshot からの procedural preview が
read-only policy と bounded weight delta を守るか。

### Procedural Writeback Contract
human-approved procedural writeback が reviewer quorum、
continuity diff、rollback token を保持するか。

### Procedural Skill Execution Contract
guardian-witnessed sandbox rehearsal が no external actuation と
rollback token carryover を守るか。

### Procedural Skill Enactment Execution
temp workspace に materialize された procedural skill enactment が
actual command receipt、cleanup、sandbox-only delivery を守るか。

### Qualia Tick Monotonicity
QualiaBuffer の tick_id が単調増加か。

### Substrate Migration Continuity
substrate 移行前後で連続性ログにギャップがないか。

### Substrate Broker Attestation Chain
standby probe が readiness を満たし、healthy active attestation と
3-beat bridge window が migrate 前に同じ destination/state digest を固定するか。

### Substrate Broker Dual Allocation Window
Method B の `shadow-sync` が pre-bound standby 上に second active allocation を開き、
fixed overlap budget 内で同一 state digest を保ったまま
`authority-handoff` までに cleanup close できるか。

### Scheduler Stage Rollback
AscensionScheduler が Method A の固定順序を守り、timeout 超過時に前段 stage へ戻せるか。

### Scheduler Method Profiles
AscensionScheduler が Method B では substrate signal で pause / rollback し、
Method C では destructive scan 開始後に fail-closed するか。

### Scheduler Method B Broker Handoff
AscensionScheduler が Method B の `authority-handoff` を
prepared broker receipt で gate し、
`bio-retirement` を hot-handoff migration + cleanup release で
confirmed になった receipt だけに開くか。

### Scheduler Governance Artifact Sync
AscensionScheduler が external proof snapshot を `artifact_sync` に保持し、
stale artifact で pause、revoked artifact で fail-closed し、
protected handoff 前に current bundle を要求するか。

### Scheduler Cancellation
AscensionScheduler が protected handoff 前の operator cancel を
`cancelled` handle と execution receipt の両方へ閉じ込められるか。

### Termination Scheduler Cancellation
TerminationGate が bound scheduler handle を実際に cancel し、
cancelled execution receipt digest を termination outcome に束縛できるか。

### Council Output Build Request Pipeline
Council が `emit_build_request` で発行した builder handoff が
immutable boundary を保ったまま patch descriptor 生成、
parsed evidence 付き differential eval、promote/hold/rollback 分類まで到達するか。

### Design Reader Handoff
DesignReader が docs/specs から source digest と must-sync docs を束ねた
design delta manifest を生成し、Council emit 前の build_request へ安全に接続できるか。

### Builder Staged Rollout Execution
Mirage Self への sandbox apply が rollback-ready receipt を返し、
builder staged rollout が dark-launch から full-100pct まで
固定順序で完了するか。

### Builder Live Oversight Network
builder live enactment が integrity Guardian の attestation event に
reviewer verifier-network receipt を 2 名分束縛したまま
enactment-approved へ到達するか。

### Builder Rollback Execution
builder staged rollout で regression が検出された時に、
RollbackEngine が pre-apply Mirage Self snapshot を復元し、
self / council / guardian 通知付きで append-only rollback を完了するか。

### Builder Rollback Oversight Network
builder rollback が integrity Guardian の attestation event に
reviewer verifier-network receipt を 2 名分束縛したまま
rollback-approved へ到達するか。

### Subjective Continuity Self-Report
本人による「途切れていない」感覚の自己報告。

### Third-Party Witness Consistency
立会第三者の観察記録との照合。

## 失敗時

- ギャップ検出 → 「主観時間の不確定区間」として永続マーク
- 本人＋ Guardian に通知
- 重大ギャップ → Council 召集
