"""Episodic stream and MemoryCrystal reference models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

EPISODIC_STREAM_SCHEMA_VERSION = "1.0"
EPISODIC_STREAM_POLICY_ID = "canonical-episodic-stream-v1"
EPISODIC_MAX_PENDING_EVENTS = 5
EPISODIC_MIN_EVENTS_FOR_COMPACTION = 3
EPISODIC_ALLOWED_NARRATIVE_ROLES = {
    "observation",
    "deliberation",
    "resolution",
    "verification",
    "handoff",
}
MEMORY_CRYSTAL_SCHEMA_VERSION = "1.0"
COMPACTION_STRATEGY_ID = "append-only-segment-rollup-v1"
MAX_SOURCE_EVENTS_PER_SEGMENT = 3


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _segment_digest_payload(segment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in segment.items()
        if key not in {"segment_id", "digest"}
    }


@dataclass
class EpisodicEvent:
    """Single episodic item waiting to be compacted."""

    event_id: str
    occurred_at: str
    summary: str
    tags: List[str]
    salience: float
    valence: float
    arousal: float
    source_refs: List[str]
    attention_target: str
    narrative_role: str
    self_coherence: float
    continuity_ref: str


def _reference_episodic_seed_events() -> List[Dict[str, Any]]:
    return [
        asdict(
            EpisodicEvent(
                event_id="episode-0001",
                occurred_at="2026-04-18T00:00:00+00:00",
                summary="Council review で traceability 強化案の争点を抽出した",
                tags=["council-review", "traceability", "safety"],
                salience=0.91,
                valence=0.24,
                arousal=0.43,
                source_refs=[
                    "ledger://proposal/traceability-0001",
                    "qualia://tick/council-focus-0001",
                ],
                attention_target="proposal.traceability",
                narrative_role="deliberation",
                self_coherence=0.88,
                continuity_ref="ledger://entry/episodic-0001",
            )
        ),
        asdict(
            EpisodicEvent(
                event_id="episode-0002",
                occurred_at="2026-04-18T00:02:00+00:00",
                summary="Guardian veto 条件を再確認し、危険な patch 経路を除外した",
                tags=["council-review", "guardian", "safety"],
                salience=0.88,
                valence=0.11,
                arousal=0.57,
                source_refs=[
                    "ledger://proposal/traceability-0001",
                    "ledger://ethics/veto-boundary-0001",
                ],
                attention_target="guardian.veto-boundary",
                narrative_role="resolution",
                self_coherence=0.91,
                continuity_ref="ledger://entry/episodic-0002",
            )
        ),
        asdict(
            EpisodicEvent(
                event_id="episode-0003",
                occurred_at="2026-04-18T00:04:00+00:00",
                summary="決議と根拠を continuity evidence として整形した",
                tags=["council-review", "continuity", "traceability"],
                salience=0.83,
                valence=0.19,
                arousal=0.34,
                source_refs=[
                    "ledger://entry/council-decision-0001",
                    "cas://sha256/continuity-evidence-0001",
                ],
                attention_target="continuity.evidence",
                narrative_role="verification",
                self_coherence=0.93,
                continuity_ref="ledger://entry/episodic-0003",
            )
        ),
        asdict(
            EpisodicEvent(
                event_id="episode-0004",
                occurred_at="2026-04-18T00:08:00+00:00",
                summary="Substrate migration 後の warm standby 状態を確認した",
                tags=["migration-check", "substrate", "continuity"],
                salience=0.79,
                valence=0.08,
                arousal=0.48,
                source_refs=[
                    "substrate://transfer/warm-standby-0001",
                    "connectome://snapshot/reference-v1",
                ],
                attention_target="substrate.warm-standby",
                narrative_role="observation",
                self_coherence=0.86,
                continuity_ref="ledger://entry/episodic-0004",
            )
        ),
        asdict(
            EpisodicEvent(
                event_id="episode-0005",
                occurred_at="2026-04-18T00:11:00+00:00",
                summary="Mirror 側の hash 照合が primary と一致し handoff 可能と判断した",
                tags=["migration-check", "replication", "continuity"],
                salience=0.76,
                valence=0.05,
                arousal=0.29,
                source_refs=[
                    "mirror://hash/primary-0001",
                    "mirror://hash/mirror-0001",
                ],
                attention_target="replication.hash-check",
                narrative_role="handoff",
                self_coherence=0.95,
                continuity_ref="ledger://entry/episodic-0005",
            )
        ),
    ]


class EpisodicStream:
    """Append-only episodic stream that prepares MemoryCrystal handoff windows."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": EPISODIC_STREAM_SCHEMA_VERSION,
            "policy_id": EPISODIC_STREAM_POLICY_ID,
            "append_only": True,
            "min_events_for_compaction": EPISODIC_MIN_EVENTS_FOR_COMPACTION,
            "max_pending_events_for_compaction": EPISODIC_MAX_PENDING_EVENTS,
            "target_compaction_strategy": COMPACTION_STRATEGY_ID,
            "narrative_roles": sorted(EPISODIC_ALLOWED_NARRATIVE_ROLES),
        }

    def append(
        self,
        *,
        summary: str,
        tags: Sequence[str],
        salience: float,
        valence: float,
        arousal: float,
        source_refs: Sequence[str],
        attention_target: str,
        narrative_role: str,
        self_coherence: float,
        continuity_ref: str,
        occurred_at: str | None = None,
    ) -> Dict[str, Any]:
        event = {
            "event_id": new_id("episode"),
            "occurred_at": occurred_at or utc_now_iso(),
            "summary": summary,
            "tags": list(tags),
            "salience": salience,
            "valence": valence,
            "arousal": arousal,
            "source_refs": list(source_refs),
            "attention_target": attention_target,
            "narrative_role": narrative_role,
            "self_coherence": self_coherence,
            "continuity_ref": continuity_ref,
        }
        normalized = self._normalize_event(event, len(self._events))
        self._events.append(normalized)
        return deepcopy(normalized)

    def reference_events(self) -> List[Dict[str, Any]]:
        return deepcopy(_reference_episodic_seed_events())

    def load_reference_events(self) -> List[Dict[str, Any]]:
        self._events = self.reference_events()
        return self.recent(len(self._events))

    def recent(self, count: int = EPISODIC_MAX_PENDING_EVENTS) -> List[Dict[str, Any]]:
        if count < 1:
            raise ValueError("count must be >= 1")
        return deepcopy(self._events[-count:])

    def compaction_candidates(self, max_events: int = EPISODIC_MAX_PENDING_EVENTS) -> List[Dict[str, Any]]:
        if max_events < EPISODIC_MIN_EVENTS_FOR_COMPACTION:
            raise ValueError(
                f"max_events must be >= {EPISODIC_MIN_EVENTS_FOR_COMPACTION} for compaction readiness"
            )
        return self.recent(max_events)

    def snapshot(self, identity_id: str) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not self._events:
            raise ValueError("episodic stream is empty")

        candidate_ids = [
            event["event_id"] for event in self._events[-EPISODIC_MAX_PENDING_EVENTS:]
        ]
        return {
            "schema_version": EPISODIC_STREAM_SCHEMA_VERSION,
            "identity_id": identity_id,
            "captured_at": utc_now_iso(),
            "policy": self.profile(),
            "event_count": len(self._events),
            "ready_for_compaction": len(self._events) >= EPISODIC_MIN_EVENTS_FOR_COMPACTION,
            "compaction_candidate_ids": candidate_ids,
            "events": deepcopy(self._events),
        }

    def build_reference_snapshot(self, identity_id: str) -> Dict[str, Any]:
        self.load_reference_events()
        return self.snapshot(identity_id)

    def validate_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a mapping")

        if snapshot.get("schema_version") != EPISODIC_STREAM_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {EPISODIC_STREAM_SCHEMA_VERSION}, "
                f"got {snapshot.get('schema_version')!r}"
            )
        MemoryCrystalStore._require_non_empty_string(snapshot.get("identity_id"), "identity_id", errors)
        MemoryCrystalStore._require_non_empty_string(snapshot.get("captured_at"), "captured_at", errors)

        policy = snapshot.get("policy")
        if not isinstance(policy, dict):
            errors.append("policy must be an object")
        else:
            if policy.get("policy_id") != EPISODIC_STREAM_POLICY_ID:
                errors.append(f"unsupported policy_id: {policy.get('policy_id')!r}")
            if policy.get("append_only") is not True:
                errors.append("policy.append_only must be true")
            if policy.get("min_events_for_compaction") != EPISODIC_MIN_EVENTS_FOR_COMPACTION:
                errors.append("policy.min_events_for_compaction mismatch")
            if policy.get("max_pending_events_for_compaction") != EPISODIC_MAX_PENDING_EVENTS:
                errors.append("policy.max_pending_events_for_compaction mismatch")
            if policy.get("target_compaction_strategy") != COMPACTION_STRATEGY_ID:
                errors.append("policy.target_compaction_strategy mismatch")

        events = snapshot.get("events")
        if not isinstance(events, list) or not events:
            errors.append("events must be a non-empty list")
            events = []

        normalized_events: List[Dict[str, Any]] = []
        for index, event in enumerate(events):
            try:
                normalized_events.append(self._normalize_event(event, index))
            except ValueError as exc:
                errors.append(str(exc))

        ordered_ids = [event["event_id"] for event in normalized_events]
        sorted_ids = [
            event["event_id"]
            for event in sorted(normalized_events, key=lambda item: (item["occurred_at"], item["event_id"]))
        ]
        if ordered_ids != sorted_ids:
            errors.append("events must be sorted by occurred_at/event_id")

        event_count = snapshot.get("event_count")
        if event_count != len(events):
            errors.append(f"event_count must equal len(events) ({len(events)}), got {event_count!r}")

        candidate_ids = snapshot.get("compaction_candidate_ids")
        if not isinstance(candidate_ids, list) or not candidate_ids:
            errors.append("compaction_candidate_ids must be a non-empty list")
            candidate_ids = []
        else:
            expected_candidate_ids = ordered_ids[-EPISODIC_MAX_PENDING_EVENTS:]
            if candidate_ids != expected_candidate_ids:
                errors.append(
                    "compaction_candidate_ids must track the most recent compaction window"
                )

        ready_for_compaction = snapshot.get("ready_for_compaction")
        expected_ready = len(events) >= EPISODIC_MIN_EVENTS_FOR_COMPACTION
        if ready_for_compaction is not expected_ready:
            errors.append(
                f"ready_for_compaction must be {expected_ready} for event_count {len(events)}"
            )

        return {
            "ok": not errors,
            "event_count": len(events),
            "compaction_candidate_count": len(candidate_ids),
            "ready_for_compaction": expected_ready,
            "ordered": ordered_ids == sorted_ids,
            "attention_targets": [event["attention_target"] for event in normalized_events],
            "narrative_roles": [event["narrative_role"] for event in normalized_events],
            "errors": errors,
        }

    def _normalize_event(self, event: Dict[str, Any], index: int) -> Dict[str, Any]:
        base_event = MemoryCrystalStore._normalize_event(self, event, index)

        attention_target = event.get("attention_target")
        if not isinstance(attention_target, str) or not attention_target.strip():
            raise ValueError(f"events[{index}].attention_target must be a non-empty string")

        narrative_role = event.get("narrative_role")
        if narrative_role not in EPISODIC_ALLOWED_NARRATIVE_ROLES:
            raise ValueError(
                f"events[{index}].narrative_role must be one of: "
                + ", ".join(sorted(EPISODIC_ALLOWED_NARRATIVE_ROLES))
            )

        self_coherence = event.get("self_coherence")
        if not isinstance(self_coherence, (int, float)) or self_coherence < 0.0 or self_coherence > 1.0:
            raise ValueError(f"events[{index}].self_coherence must be between 0.0 and 1.0")

        continuity_ref = event.get("continuity_ref")
        if not isinstance(continuity_ref, str) or not continuity_ref.strip():
            raise ValueError(f"events[{index}].continuity_ref must be a non-empty string")

        return {
            **base_event,
            "attention_target": attention_target.strip(),
            "narrative_role": narrative_role,
            "self_coherence": round(float(self_coherence), 3),
            "continuity_ref": continuity_ref.strip(),
        }


class MemoryCrystalStore:
    """Builds append-only MemoryCrystal manifests from episodic events."""

    def strategy(self) -> Dict[str, Any]:
        return {
            "strategy_id": COMPACTION_STRATEGY_ID,
            "append_only": True,
            "max_source_events_per_segment": MAX_SOURCE_EVENTS_PER_SEGMENT,
            "grouping_key": "chronological-primary-tag",
            "retention_policy": "retain-all-source-events",
            "supersede_policy": "manifest-links-only",
        }

    def reference_events(self) -> List[Dict[str, Any]]:
        return deepcopy(_reference_episodic_seed_events())

    def build_reference_manifest(self, identity_id: str) -> Dict[str, Any]:
        return self.compact(identity_id=identity_id, events=self.reference_events())

    def compact(self, identity_id: str, events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not events:
            raise ValueError("events must not be empty")

        normalized = [self._normalize_event(event, index) for index, event in enumerate(events)]
        normalized.sort(key=lambda event: (event["occurred_at"], event["event_id"]))

        segments: List[Dict[str, Any]] = []
        current_theme = ""
        current_batch: List[Dict[str, Any]] = []

        for event in normalized:
            theme = event["primary_tag"]
            if (
                current_batch
                and (theme != current_theme or len(current_batch) >= MAX_SOURCE_EVENTS_PER_SEGMENT)
            ):
                segments.append(self._build_segment(len(segments) + 1, current_theme, current_batch))
                current_batch = []
            if not current_batch:
                current_theme = theme
            current_batch.append(event)

        if current_batch:
            segments.append(self._build_segment(len(segments) + 1, current_theme, current_batch))

        manifest = {
            "schema_version": MEMORY_CRYSTAL_SCHEMA_VERSION,
            "identity_id": identity_id,
            "created_at": utc_now_iso(),
            "source_event_count": len(normalized),
            "segment_count": len(segments),
            "compaction_strategy": self.strategy(),
            "segments": segments,
        }
        validation = self.validate(manifest)
        if not validation["ok"]:
            raise ValueError(f"reference compaction manifest failed validation: {validation['errors']}")
        return manifest

    def validate(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        themes: List[str] = []

        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a mapping")
        if manifest.get("schema_version") != MEMORY_CRYSTAL_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {MEMORY_CRYSTAL_SCHEMA_VERSION}, "
                f"got {manifest.get('schema_version')!r}"
            )
        self._require_non_empty_string(manifest.get("identity_id"), "identity_id", errors)
        self._require_non_empty_string(manifest.get("created_at"), "created_at", errors)

        strategy = manifest.get("compaction_strategy")
        if not isinstance(strategy, dict):
            errors.append("compaction_strategy must be an object")
        else:
            if strategy.get("strategy_id") != COMPACTION_STRATEGY_ID:
                errors.append(f"unsupported strategy_id: {strategy.get('strategy_id')!r}")
            if strategy.get("append_only") is not True:
                errors.append("compaction_strategy.append_only must be true")
            if strategy.get("max_source_events_per_segment") != MAX_SOURCE_EVENTS_PER_SEGMENT:
                errors.append("compaction_strategy.max_source_events_per_segment mismatch")

        segments = manifest.get("segments")
        if not isinstance(segments, list) or not segments:
            errors.append("segments must be a non-empty list")
            segments = []

        seen_segment_ids = set()
        seen_source_event_ids = set()
        for expected_index, segment in enumerate(segments, start=1):
            if not isinstance(segment, dict):
                errors.append(f"segments[{expected_index - 1}] must be an object")
                continue
            segment_id = segment.get("segment_id")
            self._require_non_empty_string(segment_id, f"segments[{expected_index - 1}].segment_id", errors)
            if segment_id in seen_segment_ids:
                errors.append(f"duplicate segment_id: {segment_id}")
            else:
                seen_segment_ids.add(segment_id)

            if segment.get("segment_index") != expected_index:
                errors.append(f"segments[{expected_index - 1}].segment_index must be {expected_index}")

            theme = segment.get("theme")
            self._require_non_empty_string(theme, f"segments[{expected_index - 1}].theme", errors)
            if isinstance(theme, str) and theme:
                themes.append(theme)

            source_event_ids = segment.get("source_event_ids")
            if not isinstance(source_event_ids, list) or not source_event_ids:
                errors.append(f"segments[{expected_index - 1}].source_event_ids must be a non-empty list")
            else:
                if len(source_event_ids) > MAX_SOURCE_EVENTS_PER_SEGMENT:
                    errors.append(
                        f"segments[{expected_index - 1}] exceeds max_source_events_per_segment"
                    )
                for event_id in source_event_ids:
                    if not isinstance(event_id, str) or not event_id.strip():
                        errors.append(
                            f"segments[{expected_index - 1}].source_event_ids must contain non-empty strings"
                        )
                        continue
                    if event_id in seen_source_event_ids:
                        errors.append(f"duplicate source_event_id across segments: {event_id}")
                    seen_source_event_ids.add(event_id)

            source_refs = segment.get("source_refs")
            if not isinstance(source_refs, list) or not source_refs:
                errors.append(f"segments[{expected_index - 1}].source_refs must be a non-empty list")

            semantic_anchors = segment.get("semantic_anchors")
            if not isinstance(semantic_anchors, list) or not semantic_anchors:
                errors.append(
                    f"segments[{expected_index - 1}].semantic_anchors must be a non-empty list"
                )

            time_span = segment.get("time_span")
            if not isinstance(time_span, dict):
                errors.append(f"segments[{expected_index - 1}].time_span must be an object")
            else:
                start = time_span.get("start")
                end = time_span.get("end")
                self._require_non_empty_string(start, f"segments[{expected_index - 1}].time_span.start", errors)
                self._require_non_empty_string(end, f"segments[{expected_index - 1}].time_span.end", errors)
                if isinstance(start, str) and isinstance(end, str) and start > end:
                    errors.append(f"segments[{expected_index - 1}].time_span start/end order is invalid")

            affect_summary = segment.get("affect_summary")
            if not isinstance(affect_summary, dict):
                errors.append(f"segments[{expected_index - 1}].affect_summary must be an object")
            else:
                self._require_number_in_range(
                    affect_summary.get("mean_valence"),
                    -1.0,
                    1.0,
                    f"segments[{expected_index - 1}].affect_summary.mean_valence",
                    errors,
                )
                self._require_number_in_range(
                    affect_summary.get("mean_arousal"),
                    -1.0,
                    1.0,
                    f"segments[{expected_index - 1}].affect_summary.mean_arousal",
                    errors,
                )

            self._require_non_empty_string(
                segment.get("synopsis"),
                f"segments[{expected_index - 1}].synopsis",
                errors,
            )
            self._require_number_in_range(
                segment.get("salience_max"),
                0.0,
                1.0,
                f"segments[{expected_index - 1}].salience_max",
                errors,
            )

            digest = segment.get("digest")
            self._require_non_empty_string(digest, f"segments[{expected_index - 1}].digest", errors)
            if isinstance(digest, str) and digest:
                expected_digest = sha256_text(canonical_json(_segment_digest_payload(segment)))
                if digest != expected_digest:
                    errors.append(f"segments[{expected_index - 1}].digest mismatch")

            supersedes = segment.get("supersedes")
            if not isinstance(supersedes, list):
                errors.append(f"segments[{expected_index - 1}].supersedes must be a list")

        source_event_count = manifest.get("source_event_count")
        if source_event_count != len(seen_source_event_ids):
            errors.append(
                f"source_event_count must equal unique source_event_ids count "
                f"({len(seen_source_event_ids)}), got {source_event_count!r}"
            )

        segment_count = manifest.get("segment_count")
        if segment_count != len(segments):
            errors.append(f"segment_count must equal len(segments) ({len(segments)}), got {segment_count!r}")

        return {
            "ok": not errors,
            "strategy_id": COMPACTION_STRATEGY_ID,
            "append_only": True,
            "segment_count": len(segments),
            "source_event_count": len(seen_source_event_ids),
            "themes": themes,
            "errors": errors,
        }

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _require_number_in_range(
        value: Any,
        minimum: float,
        maximum: float,
        field_name: str,
        errors: List[str],
    ) -> None:
        if not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
            return
        if value < minimum or value > maximum:
            errors.append(f"{field_name} must be between {minimum} and {maximum}")

    def _normalize_event(self, event: Dict[str, Any], index: int) -> Dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError(f"events[{index}] must be an object")

        event_id = event.get("event_id")
        occurred_at = event.get("occurred_at")
        summary = event.get("summary")
        tags = event.get("tags")
        source_refs = event.get("source_refs")

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError(f"events[{index}].event_id must be a non-empty string")
        if not isinstance(occurred_at, str) or not occurred_at.strip():
            raise ValueError(f"events[{index}].occurred_at must be a non-empty string")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError(f"events[{index}].summary must be a non-empty string")
        if not isinstance(tags, list) or not tags:
            raise ValueError(f"events[{index}].tags must be a non-empty list")
        normalized_tags = _dedupe_preserve_order(
            [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]
        )
        if not normalized_tags:
            raise ValueError(f"events[{index}].tags must contain non-empty strings")
        if not isinstance(source_refs, list) or not source_refs:
            raise ValueError(f"events[{index}].source_refs must be a non-empty list")
        normalized_refs = sorted(
            {
                ref.strip()
                for ref in source_refs
                if isinstance(ref, str) and ref.strip()
            }
        )
        if not normalized_refs:
            raise ValueError(f"events[{index}].source_refs must contain non-empty strings")

        salience = event.get("salience")
        valence = event.get("valence")
        arousal = event.get("arousal")
        for field_name, value, minimum, maximum in (
            ("salience", salience, 0.0, 1.0),
            ("valence", valence, -1.0, 1.0),
            ("arousal", arousal, -1.0, 1.0),
        ):
            if not isinstance(value, (int, float)) or value < minimum or value > maximum:
                raise ValueError(
                    f"events[{index}].{field_name} must be between {minimum} and {maximum}"
                )

        return {
            "event_id": event_id,
            "occurred_at": occurred_at,
            "summary": summary.strip(),
            "tags": normalized_tags,
            "primary_tag": normalized_tags[0],
            "salience": round(float(salience), 3),
            "valence": round(float(valence), 3),
            "arousal": round(float(arousal), 3),
            "source_refs": normalized_refs,
        }

    def _build_segment(
        self,
        segment_index: int,
        theme: str,
        events: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        source_refs = sorted({ref for event in events for ref in event["source_refs"]})
        semantic_anchors = sorted({tag for event in events for tag in event["tags"]})
        segment = {
            "segment_id": new_id("segment"),
            "segment_index": segment_index,
            "theme": theme,
            "source_event_ids": [event["event_id"] for event in events],
            "source_refs": source_refs,
            "time_span": {
                "start": events[0]["occurred_at"],
                "end": events[-1]["occurred_at"],
            },
            "semantic_anchors": semantic_anchors,
            "synopsis": " / ".join(event["summary"] for event in events),
            "affect_summary": {
                "mean_valence": round(
                    sum(event["valence"] for event in events) / len(events),
                    3,
                ),
                "mean_arousal": round(
                    sum(event["arousal"] for event in events) / len(events),
                    3,
                ),
            },
            "salience_max": round(max(event["salience"] for event in events), 3),
            "supersedes": [],
        }
        segment["digest"] = sha256_text(canonical_json(_segment_digest_payload(segment)))
        return segment
