---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/interfaces/governance.oversight.v0.idl
  - specs/interfaces/interface.ewa.v0.idl
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/interfaces/agentic.distributed_transport.v0.idl
status: decided
---

# Decision: gap-report は current truth-source の residual future work も列挙する

## Context

2026-04-22 時点の `gap-report --json` は
open question / missing file / empty eval / placeholder を検出できましたが、
IDL や reference README に残る current truth-source の `future work` を
拾えませんでした。

そのため repo には未充足 gap が残っていても
automation 上は all-zero に見え、
次に閉じるべき contract を自動で選びにくい状態でした。

## Options considered

- A: 現行 scanner を維持し、future-work 探索は毎回人手で README / IDL を読む
- B: `gap-report` が curated truth-source の `future work` を抽出し、prioritized task として返す
- C: decision-log 全件を scan して future-work を拾う

## Decision

Option B を採択します。

- `gap-report` は `README.md`、`docs/07-reference-implementation/README.md`、
  `specs/interfaces/**/*.idl`、`specs/schemas/README.md`
  を truth source として scan します
- `future work` を含む line は `future_work_hits` として report に残し、
  `prioritized_tasks` へ high priority で載せます
- `deferred surface` のような明示的 boundary は false positive を避けるため除外します
- historical `meta/decision-log/` は truth source に使いません

## Consequences

- hourly builder は `gap-report` だけでも
  current tree に残る residual future work を見失いにくくなります
- all-zero report は「本当に current truth-source 上の immediate gap が薄い」状態に近づきます
- false positive は `deferred surface` 除外と
  truth-source file の限定で抑制します

## Revisit triggers

- truth source を docs/02-subsystems や docs/04-ai-governance まで広げたくなった時
- `future work` 以外の語彙でも stable に gap 抽出したくなった時
- prioritized task を line 単位ではなく
  structured surface ID に昇格したくなった時
