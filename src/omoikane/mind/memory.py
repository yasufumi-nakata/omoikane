"""Episodic stream and MemoryCrystal reference models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence
from uuid import uuid4

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .connectome import CONNECTOME_SCHEMA_VERSION, ConnectomeModel

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
SEMANTIC_MEMORY_SCHEMA_VERSION = "1.0"
SEMANTIC_PROJECTION_POLICY_ID = "semantic-segment-rollup-v1"
PROCEDURAL_MEMORY_SCHEMA_VERSION = "1.0"
PROCEDURAL_PREVIEW_POLICY_ID = "connectome-coupled-procedural-preview-v1"
PROCEDURAL_MAX_WEIGHT_DELTA = 0.08
PROCEDURAL_DEFERRED_SURFACES = ["skill-execution"]
PROCEDURAL_WRITEBACK_POLICY_ID = "human-approved-procedural-writeback-v1"
PROCEDURAL_REQUIRED_HUMAN_REVIEWERS = 2
PROCEDURAL_SKILL_EXECUTION_POLICY_ID = "guardian-witnessed-procedural-skill-execution-v1"
PROCEDURAL_MAX_REHEARSAL_STEPS = 3


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


def _semantic_concept_digest_payload(concept: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in concept.items() if key != "digest"}


def _procedural_recommendation_digest_payload(recommendation: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in recommendation.items() if key != "digest"}


def _procedural_writeback_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "digest"}


def _procedural_execution_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "digest"}


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


class SemanticMemoryProjector:
    """Projects MemoryCrystal segments into a deterministic semantic view."""

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": SEMANTIC_MEMORY_SCHEMA_VERSION,
            "policy_id": SEMANTIC_PROJECTION_POLICY_ID,
            "read_only_view": True,
            "source_compaction_strategy": COMPACTION_STRATEGY_ID,
            "grouping_key": "memory-crystal-segment-theme",
            "projection_mode": "derived-semantic-view",
            "confidence_floor": 0.55,
            "deferred_surfaces": ["procedural-memory"],
        }

    def build_reference_snapshot(self, identity_id: str) -> Dict[str, Any]:
        manifest = MemoryCrystalStore().build_reference_manifest(identity_id)
        return self.project(identity_id, manifest)

    def project(self, identity_id: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a mapping")

        manifest_validation = MemoryCrystalStore().validate(manifest)
        if not manifest_validation["ok"]:
            raise ValueError(
                f"semantic projection requires a valid MemoryCrystal manifest: {manifest_validation['errors']}"
            )
        if manifest.get("identity_id") != identity_id:
            raise ValueError("identity_id must match manifest.identity_id")

        concepts = [
            self._build_concept(segment)
            for segment in manifest["segments"]
        ]
        snapshot = {
            "schema_version": SEMANTIC_MEMORY_SCHEMA_VERSION,
            "identity_id": identity_id,
            "projected_at": utc_now_iso(),
            "projection_policy": self.profile(),
            "source_manifest_digest": sha256_text(canonical_json(manifest)),
            "source_segment_ids": [segment["segment_id"] for segment in manifest["segments"]],
            "concept_count": len(concepts),
            "concepts": concepts,
            "deferred_surfaces": ["procedural-memory"],
        }
        validation = self.validate(snapshot)
        if not validation["ok"]:
            raise ValueError(f"semantic snapshot failed validation: {validation['errors']}")
        return snapshot

    def validate(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        labels: List[str] = []

        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a mapping")
        if snapshot.get("schema_version") != SEMANTIC_MEMORY_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {SEMANTIC_MEMORY_SCHEMA_VERSION}, "
                f"got {snapshot.get('schema_version')!r}"
            )
        MemoryCrystalStore._require_non_empty_string(snapshot.get("identity_id"), "identity_id", errors)
        MemoryCrystalStore._require_non_empty_string(snapshot.get("projected_at"), "projected_at", errors)

        projection_policy = snapshot.get("projection_policy")
        if not isinstance(projection_policy, dict):
            errors.append("projection_policy must be an object")
        else:
            expected_policy = self.profile()
            for field_name, expected_value in expected_policy.items():
                if projection_policy.get(field_name) != expected_value:
                    errors.append(f"projection_policy.{field_name} mismatch")

        source_manifest_digest = snapshot.get("source_manifest_digest")
        if not isinstance(source_manifest_digest, str) or len(source_manifest_digest) != 64:
            errors.append("source_manifest_digest must be a sha256 hex string")

        source_segment_ids = snapshot.get("source_segment_ids")
        if not isinstance(source_segment_ids, list) or not source_segment_ids:
            errors.append("source_segment_ids must be a non-empty list")
            source_segment_ids = []
        else:
            for segment_id in source_segment_ids:
                if not isinstance(segment_id, str) or not segment_id.strip():
                    errors.append("source_segment_ids must contain non-empty strings")

        concepts = snapshot.get("concepts")
        if not isinstance(concepts, list) or not concepts:
            errors.append("concepts must be a non-empty list")
            concepts = []

        seen_concept_ids = set()
        seen_segment_ids = set()
        for index, concept in enumerate(concepts):
            if not isinstance(concept, dict):
                errors.append(f"concepts[{index}] must be an object")
                continue

            concept_id = concept.get("concept_id")
            MemoryCrystalStore._require_non_empty_string(concept_id, f"concepts[{index}].concept_id", errors)
            if isinstance(concept_id, str) and concept_id:
                if concept_id in seen_concept_ids:
                    errors.append(f"duplicate concept_id: {concept_id}")
                else:
                    seen_concept_ids.add(concept_id)

            canonical_label = concept.get("canonical_label")
            MemoryCrystalStore._require_non_empty_string(
                canonical_label,
                f"concepts[{index}].canonical_label",
                errors,
            )
            if isinstance(canonical_label, str) and canonical_label:
                labels.append(canonical_label)

            for field_name in ("aliases", "supporting_segment_ids", "supporting_event_ids", "source_refs", "retrieval_cues"):
                value = concept.get(field_name)
                if not isinstance(value, list) or not value:
                    errors.append(f"concepts[{index}].{field_name} must be a non-empty list")
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(f"concepts[{index}].{field_name} must contain non-empty strings")
                if field_name == "supporting_segment_ids":
                    seen_segment_ids.update(value)

            MemoryCrystalStore._require_non_empty_string(
                concept.get("proposition"),
                f"concepts[{index}].proposition",
                errors,
            )
            reinforcement_count = concept.get("reinforcement_count")
            if not isinstance(reinforcement_count, int) or reinforcement_count < 1:
                errors.append(f"concepts[{index}].reinforcement_count must be >= 1")

            MemoryCrystalStore._require_number_in_range(
                concept.get("confidence"),
                0.0,
                1.0,
                f"concepts[{index}].confidence",
                errors,
            )
            MemoryCrystalStore._require_number_in_range(
                concept.get("salience_max"),
                0.0,
                1.0,
                f"concepts[{index}].salience_max",
                errors,
            )

            affect_envelope = concept.get("affect_envelope")
            if not isinstance(affect_envelope, dict):
                errors.append(f"concepts[{index}].affect_envelope must be an object")
            else:
                MemoryCrystalStore._require_number_in_range(
                    affect_envelope.get("mean_valence"),
                    -1.0,
                    1.0,
                    f"concepts[{index}].affect_envelope.mean_valence",
                    errors,
                )
                MemoryCrystalStore._require_number_in_range(
                    affect_envelope.get("mean_arousal"),
                    -1.0,
                    1.0,
                    f"concepts[{index}].affect_envelope.mean_arousal",
                    errors,
                )

            time_span = concept.get("time_span")
            if not isinstance(time_span, dict):
                errors.append(f"concepts[{index}].time_span must be an object")
            else:
                start = time_span.get("start")
                end = time_span.get("end")
                MemoryCrystalStore._require_non_empty_string(
                    start,
                    f"concepts[{index}].time_span.start",
                    errors,
                )
                MemoryCrystalStore._require_non_empty_string(
                    end,
                    f"concepts[{index}].time_span.end",
                    errors,
                )
                if isinstance(start, str) and isinstance(end, str) and start > end:
                    errors.append(f"concepts[{index}].time_span start/end order is invalid")

            for field_name in ("source_segment_digest", "digest"):
                value = concept.get(field_name)
                if not isinstance(value, str) or len(value) != 64:
                    errors.append(f"concepts[{index}].{field_name} must be a sha256 hex string")

            digest = concept.get("digest")
            if isinstance(digest, str) and len(digest) == 64:
                expected_digest = sha256_text(canonical_json(_semantic_concept_digest_payload(concept)))
                if digest != expected_digest:
                    errors.append(f"concepts[{index}].digest mismatch")

        concept_count = snapshot.get("concept_count")
        if concept_count != len(concepts):
            errors.append(f"concept_count must equal len(concepts) ({len(concepts)}), got {concept_count!r}")

        if isinstance(source_segment_ids, list) and source_segment_ids and seen_segment_ids:
            if sorted(source_segment_ids) != sorted(seen_segment_ids):
                errors.append("source_segment_ids must equal the union of supporting_segment_ids")

        deferred_surfaces = snapshot.get("deferred_surfaces")
        if deferred_surfaces != ["procedural-memory"]:
            errors.append("deferred_surfaces must equal ['procedural-memory']")

        return {
            "ok": not errors,
            "concept_count": len(concepts),
            "labels": labels,
            "deferred_surfaces": ["procedural-memory"],
            "errors": errors,
        }

    def _build_concept(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        aliases = [anchor for anchor in segment["semantic_anchors"] if anchor != segment["theme"]]
        confidence = 0.55 + (segment["salience_max"] * 0.30) + (
            0.03 * (len(segment["source_event_ids"]) - 1)
        )
        concept = {
            "concept_id": f"concept-{segment['segment_id']}",
            "canonical_label": segment["theme"],
            "aliases": aliases or [segment["theme"]],
            "proposition": segment["synopsis"],
            "supporting_segment_ids": [segment["segment_id"]],
            "supporting_event_ids": list(segment["source_event_ids"]),
            "source_refs": list(segment["source_refs"]),
            "retrieval_cues": list(segment["semantic_anchors"]),
            "reinforcement_count": len(segment["source_event_ids"]),
            "confidence": round(min(0.98, confidence), 3),
            "salience_max": segment["salience_max"],
            "affect_envelope": deepcopy(segment["affect_summary"]),
            "time_span": deepcopy(segment["time_span"]),
            "source_segment_digest": segment["digest"],
        }
        concept["digest"] = sha256_text(canonical_json(_semantic_concept_digest_payload(concept)))
        return concept


class ProceduralMemoryProjector:
    """Projects MemoryCrystal segments into read-only connectome update previews."""

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "policy_id": PROCEDURAL_PREVIEW_POLICY_ID,
            "read_only_preview": True,
            "source_compaction_strategy": COMPACTION_STRATEGY_ID,
            "target_connectome_schema": CONNECTOME_SCHEMA_VERSION,
            "update_mode": "weight-delta-preview",
            "max_weight_delta": PROCEDURAL_MAX_WEIGHT_DELTA,
            "approval_required": ["self", "council", "guardian"],
            "deferred_surfaces": list(PROCEDURAL_DEFERRED_SURFACES),
        }

    def build_reference_snapshot(self, identity_id: str) -> Dict[str, Any]:
        manifest = MemoryCrystalStore().build_reference_manifest(identity_id)
        connectome_document = ConnectomeModel().build_reference_snapshot(identity_id)
        return self.project(identity_id, manifest, connectome_document)

    def project(
        self,
        identity_id: str,
        manifest: Dict[str, Any],
        connectome_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a mapping")
        if not isinstance(connectome_document, dict):
            raise ValueError("connectome_document must be a mapping")

        manifest_validation = MemoryCrystalStore().validate(manifest)
        if not manifest_validation["ok"]:
            raise ValueError(
                "procedural projection requires a valid MemoryCrystal manifest: "
                f"{manifest_validation['errors']}"
            )
        connectome_validation = ConnectomeModel().validate(connectome_document)
        if not connectome_validation["ok"]:
            raise ValueError("connectome_document must satisfy Connectome validation")
        if manifest.get("identity_id") != identity_id:
            raise ValueError("identity_id must match manifest.identity_id")
        if connectome_document.get("identity_id") != identity_id:
            raise ValueError("identity_id must match connectome_document.identity_id")

        edge_contexts = self._edge_contexts(connectome_document)
        recommendations = [
            self._build_recommendation(segment, self._select_edge(segment, edge_contexts))
            for segment in manifest["segments"]
        ]
        snapshot = {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "identity_id": identity_id,
            "projected_at": utc_now_iso(),
            "preview_policy": self.profile(),
            "source_manifest_digest": sha256_text(canonical_json(manifest)),
            "source_segment_ids": [segment["segment_id"] for segment in manifest["segments"]],
            "connectome_snapshot_id": connectome_document["snapshot_id"],
            "connectome_snapshot_digest": sha256_text(canonical_json(connectome_document)),
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "preview_only": True,
            "deferred_surfaces": list(PROCEDURAL_DEFERRED_SURFACES),
        }
        validation = self.validate(snapshot)
        if not validation["ok"]:
            raise ValueError(f"procedural preview failed validation: {validation['errors']}")
        return snapshot

    def validate(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        target_paths: List[str] = []

        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a mapping")
        if snapshot.get("schema_version") != PROCEDURAL_MEMORY_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {PROCEDURAL_MEMORY_SCHEMA_VERSION}, "
                f"got {snapshot.get('schema_version')!r}"
            )
        MemoryCrystalStore._require_non_empty_string(snapshot.get("identity_id"), "identity_id", errors)
        MemoryCrystalStore._require_non_empty_string(snapshot.get("projected_at"), "projected_at", errors)
        MemoryCrystalStore._require_non_empty_string(
            snapshot.get("connectome_snapshot_id"),
            "connectome_snapshot_id",
            errors,
        )

        preview_policy = snapshot.get("preview_policy")
        if not isinstance(preview_policy, dict):
            errors.append("preview_policy must be an object")
        else:
            expected_policy = self.profile()
            for field_name, expected_value in expected_policy.items():
                if preview_policy.get(field_name) != expected_value:
                    errors.append(f"preview_policy.{field_name} mismatch")

        for field_name in ("source_manifest_digest", "connectome_snapshot_digest"):
            value = snapshot.get(field_name)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"{field_name} must be a sha256 hex string")

        source_segment_ids = snapshot.get("source_segment_ids")
        if not isinstance(source_segment_ids, list) or not source_segment_ids:
            errors.append("source_segment_ids must be a non-empty list")
            source_segment_ids = []
        else:
            for segment_id in source_segment_ids:
                if not isinstance(segment_id, str) or not segment_id.strip():
                    errors.append("source_segment_ids must contain non-empty strings")

        recommendations = snapshot.get("recommendations")
        if not isinstance(recommendations, list) or not recommendations:
            errors.append("recommendations must be a non-empty list")
            recommendations = []

        seen_recommendation_ids = set()
        seen_segment_ids = set()
        for index, recommendation in enumerate(recommendations):
            if not isinstance(recommendation, dict):
                errors.append(f"recommendations[{index}] must be an object")
                continue

            recommendation_id = recommendation.get("recommendation_id")
            MemoryCrystalStore._require_non_empty_string(
                recommendation_id,
                f"recommendations[{index}].recommendation_id",
                errors,
            )
            if isinstance(recommendation_id, str) and recommendation_id:
                if recommendation_id in seen_recommendation_ids:
                    errors.append(f"duplicate recommendation_id: {recommendation_id}")
                else:
                    seen_recommendation_ids.add(recommendation_id)

            for field_name in ("source_segment_ids", "source_event_ids", "source_refs", "guardrails"):
                value = recommendation.get(field_name)
                if not isinstance(value, list) or not value:
                    errors.append(f"recommendations[{index}].{field_name} must be a non-empty list")
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(
                            f"recommendations[{index}].{field_name} must contain non-empty strings"
                        )
                if field_name == "source_segment_ids":
                    seen_segment_ids.update(value)

            for field_name in ("target_edge_id", "target_path", "plasticity_rule", "justification"):
                MemoryCrystalStore._require_non_empty_string(
                    recommendation.get(field_name),
                    f"recommendations[{index}].{field_name}",
                    errors,
                )

            target_path = recommendation.get("target_path")
            if isinstance(target_path, str) and target_path:
                target_paths.append(target_path)

            MemoryCrystalStore._require_number_in_range(
                recommendation.get("proposed_weight_delta"),
                0.0,
                PROCEDURAL_MAX_WEIGHT_DELTA,
                f"recommendations[{index}].proposed_weight_delta",
                errors,
            )
            MemoryCrystalStore._require_number_in_range(
                recommendation.get("target_weight_after_preview"),
                0.0,
                1.0,
                f"recommendations[{index}].target_weight_after_preview",
                errors,
            )
            MemoryCrystalStore._require_number_in_range(
                recommendation.get("confidence"),
                0.0,
                1.0,
                f"recommendations[{index}].confidence",
                errors,
            )
            MemoryCrystalStore._require_number_in_range(
                recommendation.get("rehearsal_priority"),
                0.0,
                1.0,
                f"recommendations[{index}].rehearsal_priority",
                errors,
            )

            source_segment_digest = recommendation.get("source_segment_digest")
            if not isinstance(source_segment_digest, str) or len(source_segment_digest) != 64:
                errors.append(
                    f"recommendations[{index}].source_segment_digest must be a sha256 hex string"
                )
            digest = recommendation.get("digest")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"recommendations[{index}].digest must be a sha256 hex string")
            else:
                expected_digest = sha256_text(
                    canonical_json(_procedural_recommendation_digest_payload(recommendation))
                )
                if digest != expected_digest:
                    errors.append(f"recommendations[{index}].digest mismatch")

        recommendation_count = snapshot.get("recommendation_count")
        if recommendation_count != len(recommendations):
            errors.append(
                "recommendation_count must equal len(recommendations) "
                f"({len(recommendations)}), got {recommendation_count!r}"
            )

        if snapshot.get("preview_only") is not True:
            errors.append("preview_only must equal true")

        deferred_surfaces = snapshot.get("deferred_surfaces")
        if deferred_surfaces != PROCEDURAL_DEFERRED_SURFACES:
            errors.append(f"deferred_surfaces must equal {PROCEDURAL_DEFERRED_SURFACES!r}")

        if isinstance(source_segment_ids, list) and source_segment_ids and seen_segment_ids:
            if sorted(source_segment_ids) != sorted(seen_segment_ids):
                errors.append("source_segment_ids must equal the union of recommendation source_segment_ids")

        return {
            "ok": not errors,
            "recommendation_count": len(recommendations),
            "target_paths": target_paths,
            "deferred_surfaces": list(PROCEDURAL_DEFERRED_SURFACES),
            "errors": errors,
        }

    @staticmethod
    def _edge_contexts(connectome_document: Dict[str, Any]) -> List[Dict[str, Any]]:
        node_labels = {
            node["id"]: node.get("properties", {}).get("label", node["id"])
            for node in connectome_document["nodes"]
        }
        return [
            {
                "edge_id": edge["id"],
                "source_label": node_labels[edge["source"]],
                "target_label": node_labels[edge["target"]],
                "plasticity_rule": edge["plasticity"]["rule"],
                "current_weight": edge["weight"],
            }
            for edge in connectome_document["edges"]
        ]

    def _select_edge(
        self,
        segment: Dict[str, Any],
        edge_contexts: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        anchors = set(segment["semantic_anchors"])
        theme = segment["theme"]
        best_edge = edge_contexts[0]
        best_score = -1

        for edge_context in edge_contexts:
            score = 0
            source_label = edge_context["source_label"]
            target_label = edge_context["target_label"]
            plasticity_rule = edge_context["plasticity_rule"]

            if theme == "council-review" or anchors & {"guardian", "safety", "traceability"}:
                if target_label == "ethics_gate":
                    score += 3
                if plasticity_rule == "homeostatic-clamp":
                    score += 2
            if theme == "migration-check" or anchors & {"migration-check", "replication", "substrate"}:
                if source_label == "sensory_ingress":
                    score += 3
                if plasticity_rule == "hebbian-windowed":
                    score += 2
            if "continuity" in anchors and (
                source_label == "continuity_integrator" or target_label == "continuity_integrator"
            ):
                score += 1

            if score > best_score:
                best_edge = edge_context
                best_score = score

        return best_edge

    def _build_recommendation(
        self,
        segment: Dict[str, Any],
        edge_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        reinforcement_count = len(segment["source_event_ids"])
        salience = segment["salience_max"]
        arousal = abs(segment["affect_summary"]["mean_arousal"])
        delta = 0.015 + (salience * 0.04) + ((reinforcement_count - 1) * 0.005)
        if edge_context["target_label"] == "ethics_gate":
            delta += 0.005
        proposed_weight_delta = round(min(PROCEDURAL_MAX_WEIGHT_DELTA, delta), 3)
        target_weight_after_preview = round(
            min(1.0, edge_context["current_weight"] + proposed_weight_delta),
            3,
        )
        confidence = round(min(0.97, 0.56 + (salience * 0.25) + (reinforcement_count * 0.04)), 3)
        rehearsal_priority = round(min(0.98, 0.45 + (salience * 0.30) + (arousal * 0.15)), 3)

        recommendation = {
            "recommendation_id": f"procedural-{segment['segment_id']}",
            "source_segment_ids": [segment["segment_id"]],
            "source_event_ids": list(segment["source_event_ids"]),
            "target_edge_id": edge_context["edge_id"],
            "target_path": f"{edge_context['source_label']}->{edge_context['target_label']}",
            "plasticity_rule": edge_context["plasticity_rule"],
            "proposed_weight_delta": proposed_weight_delta,
            "target_weight_after_preview": target_weight_after_preview,
            "confidence": confidence,
            "rehearsal_priority": rehearsal_priority,
            "justification": (
                f"{segment['theme']} segment を {edge_context['source_label']} -> "
                f"{edge_context['target_label']} の結合へ rehearsal preview として反映する"
            ),
            "source_refs": list(segment["source_refs"]),
            "guardrails": [
                "preview-only",
                "apply requires self/council/guardian approval",
                "connectome mutation must emit continuity diff",
            ],
            "source_segment_digest": segment["digest"],
        }
        recommendation["digest"] = sha256_text(
            canonical_json(_procedural_recommendation_digest_payload(recommendation))
        )
        return recommendation


class ProceduralMemoryWritebackGate:
    """Applies approved procedural previews to a copied Connectome snapshot."""

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "policy_id": PROCEDURAL_WRITEBACK_POLICY_ID,
            "source_preview_policy": PROCEDURAL_PREVIEW_POLICY_ID,
            "target_connectome_schema": CONNECTOME_SCHEMA_VERSION,
            "update_mode": "bounded-weight-application",
            "max_weight_delta": PROCEDURAL_MAX_WEIGHT_DELTA,
            "approval_required": ["self", "council", "guardian", "human"],
            "required_human_reviewers": PROCEDURAL_REQUIRED_HUMAN_REVIEWERS,
            "continuity_diff_required": True,
            "rollback_ready": True,
        }

    def apply(
        self,
        identity_id: str,
        preview_snapshot: Dict[str, Any],
        connectome_document: Dict[str, Any],
        *,
        selected_recommendation_ids: Sequence[str] | None = None,
        self_attestation_id: str,
        council_attestation_id: str,
        guardian_attestation_id: str,
        human_reviewers: Sequence[str],
        approval_reason: str,
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not isinstance(preview_snapshot, dict):
            raise ValueError("preview_snapshot must be a mapping")
        if not isinstance(connectome_document, dict):
            raise ValueError("connectome_document must be a mapping")

        preview_validation = ProceduralMemoryProjector().validate(preview_snapshot)
        if not preview_validation["ok"]:
            raise ValueError(
                f"procedural writeback requires a valid preview snapshot: {preview_validation['errors']}"
            )
        connectome_validation = ConnectomeModel().validate(connectome_document)
        if not connectome_validation["ok"]:
            raise ValueError("connectome_document must satisfy Connectome validation")
        if preview_snapshot.get("identity_id") != identity_id:
            raise ValueError("identity_id must match preview_snapshot.identity_id")
        if connectome_document.get("identity_id") != identity_id:
            raise ValueError("identity_id must match connectome_document.identity_id")
        if preview_snapshot.get("connectome_snapshot_id") != connectome_document.get("snapshot_id"):
            raise ValueError("preview_snapshot must reference connectome_document.snapshot_id")

        normalized_reviewers = _dedupe_preserve_order(list(human_reviewers))
        if len(normalized_reviewers) < PROCEDURAL_REQUIRED_HUMAN_REVIEWERS:
            raise PermissionError(
                f"procedural writeback requires at least {PROCEDURAL_REQUIRED_HUMAN_REVIEWERS} human reviewers"
            )
        for field_name, value in (
            ("self_attestation_id", self_attestation_id),
            ("council_attestation_id", council_attestation_id),
            ("guardian_attestation_id", guardian_attestation_id),
            ("approval_reason", approval_reason),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        selected_ids = self._normalize_selected_recommendation_ids(
            preview_snapshot["recommendations"],
            selected_recommendation_ids,
        )
        selected_recommendations = [
            recommendation
            for recommendation in preview_snapshot["recommendations"]
            if recommendation["recommendation_id"] in selected_ids
        ]
        updated_connectome = deepcopy(connectome_document)
        edge_map = {edge["id"]: edge for edge in updated_connectome["edges"]}

        applied_recommendations: List[Dict[str, Any]] = []
        target_paths: List[str] = []
        for recommendation in selected_recommendations:
            edge = edge_map.get(recommendation["target_edge_id"])
            if edge is None:
                raise ValueError(
                    f"preview recommendation references unknown edge: {recommendation['target_edge_id']}"
                )
            previous_weight = round(float(edge["weight"]), 3)
            applied_weight_delta = round(float(recommendation["proposed_weight_delta"]), 3)
            resulting_weight = round(min(1.0, previous_weight + applied_weight_delta), 3)
            edge["weight"] = resulting_weight
            target_paths.append(recommendation["target_path"])

            applied_record = {
                "recommendation_id": recommendation["recommendation_id"],
                "target_edge_id": recommendation["target_edge_id"],
                "target_path": recommendation["target_path"],
                "source_segment_ids": list(recommendation["source_segment_ids"]),
                "source_event_ids": list(recommendation["source_event_ids"]),
                "source_recommendation_digest": recommendation["digest"],
                "previous_weight": previous_weight,
                "applied_weight_delta": applied_weight_delta,
                "resulting_weight": resulting_weight,
                "continuity_diff_ref": f"ledger://entry/{new_id('procedural-writeback')}",
            }
            applied_record["digest"] = sha256_text(
                canonical_json(_procedural_writeback_digest_payload(applied_record))
            )
            applied_recommendations.append(applied_record)

        updated_connectome["snapshot_id"] = str(uuid4())
        updated_connectome["snapshot_time"] = utc_now_iso()
        updated_connectome_validation = ConnectomeModel().validate(updated_connectome)
        if not updated_connectome_validation["ok"]:
            raise ValueError("updated_connectome must satisfy Connectome validation")

        source_preview_digest = sha256_text(canonical_json(preview_snapshot))
        input_connectome_digest = sha256_text(canonical_json(connectome_document))
        output_connectome_digest = sha256_text(canonical_json(updated_connectome))
        rollback_token = new_id("rollback")

        receipt = {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "identity_id": identity_id,
            "applied_at": utc_now_iso(),
            "writeback_policy": self.profile(),
            "source_preview_digest": source_preview_digest,
            "source_preview_recommendation_ids": list(selected_ids),
            "input_connectome_snapshot_id": connectome_document["snapshot_id"],
            "input_connectome_digest": input_connectome_digest,
            "output_connectome_snapshot_id": updated_connectome["snapshot_id"],
            "output_connectome_digest": output_connectome_digest,
            "applied_recommendation_count": len(applied_recommendations),
            "applied_recommendations": applied_recommendations,
            "approval_bundle": {
                "self_attestation_id": self_attestation_id.strip(),
                "council_attestation_id": council_attestation_id.strip(),
                "guardian_attestation_id": guardian_attestation_id.strip(),
                "human_reviewers": normalized_reviewers,
                "approval_reason": approval_reason.strip(),
            },
            "continuity_diff": {
                "diff_id": new_id("connectome-diff"),
                "event_type": "mind.memory.procedural_applied",
                "mutated_edge_ids": [record["target_edge_id"] for record in applied_recommendations],
                "recorded_by": "ProceduralMemoryWritebackGate",
                "target_paths": target_paths,
            },
            "status": "approved",
            "rollback_token": rollback_token,
            "unchanged_edge_ids": [
                edge["id"]
                for edge in updated_connectome["edges"]
                if edge["id"] not in receipt_edge_ids(applied_recommendations)
            ],
        }

        validation = self.validate(receipt, updated_connectome, preview_snapshot)
        if not validation["ok"]:
            raise ValueError(f"procedural writeback receipt failed validation: {validation['errors']}")

        return {
            "receipt": receipt,
            "updated_connectome_document": updated_connectome,
        }

    def validate(
        self,
        receipt: Dict[str, Any],
        updated_connectome_document: Dict[str, Any],
        preview_snapshot: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        target_paths: List[str] = []

        if not isinstance(receipt, dict):
            raise ValueError("receipt must be a mapping")
        if not isinstance(updated_connectome_document, dict):
            raise ValueError("updated_connectome_document must be a mapping")
        if receipt.get("schema_version") != PROCEDURAL_MEMORY_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {PROCEDURAL_MEMORY_SCHEMA_VERSION}, "
                f"got {receipt.get('schema_version')!r}"
            )

        for field_name in (
            "identity_id",
            "applied_at",
            "input_connectome_snapshot_id",
            "output_connectome_snapshot_id",
            "rollback_token",
        ):
            MemoryCrystalStore._require_non_empty_string(receipt.get(field_name), field_name, errors)

        writeback_policy = receipt.get("writeback_policy")
        if not isinstance(writeback_policy, dict):
            errors.append("writeback_policy must be an object")
        else:
            expected_policy = self.profile()
            for field_name, expected_value in expected_policy.items():
                if writeback_policy.get(field_name) != expected_value:
                    errors.append(f"writeback_policy.{field_name} mismatch")

        for field_name in (
            "source_preview_digest",
            "input_connectome_digest",
            "output_connectome_digest",
        ):
            value = receipt.get(field_name)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"{field_name} must be a sha256 hex string")

        selected_ids = receipt.get("source_preview_recommendation_ids")
        if not isinstance(selected_ids, list) or not selected_ids:
            errors.append("source_preview_recommendation_ids must be a non-empty list")
            selected_ids = []
        else:
            for recommendation_id in selected_ids:
                if not isinstance(recommendation_id, str) or not recommendation_id.strip():
                    errors.append(
                        "source_preview_recommendation_ids must contain non-empty strings"
                    )

        applied_recommendations = receipt.get("applied_recommendations")
        if not isinstance(applied_recommendations, list) or not applied_recommendations:
            errors.append("applied_recommendations must be a non-empty list")
            applied_recommendations = []

        seen_recommendation_ids = set()
        mutated_edge_ids: List[str] = []
        human_reviewers: List[str] = []
        for index, record in enumerate(applied_recommendations):
            if not isinstance(record, dict):
                errors.append(f"applied_recommendations[{index}] must be an object")
                continue

            for field_name in (
                "recommendation_id",
                "target_edge_id",
                "target_path",
                "source_recommendation_digest",
                "continuity_diff_ref",
            ):
                MemoryCrystalStore._require_non_empty_string(
                    record.get(field_name),
                    f"applied_recommendations[{index}].{field_name}",
                    errors,
                )

            recommendation_id = record.get("recommendation_id")
            if isinstance(recommendation_id, str) and recommendation_id:
                if recommendation_id in seen_recommendation_ids:
                    errors.append(f"duplicate applied recommendation_id: {recommendation_id}")
                else:
                    seen_recommendation_ids.add(recommendation_id)

            target_path = record.get("target_path")
            if isinstance(target_path, str) and target_path:
                target_paths.append(target_path)
            target_edge_id = record.get("target_edge_id")
            if isinstance(target_edge_id, str) and target_edge_id:
                mutated_edge_ids.append(target_edge_id)

            for field_name in ("source_segment_ids", "source_event_ids"):
                value = record.get(field_name)
                if not isinstance(value, list) or not value:
                    errors.append(
                        f"applied_recommendations[{index}].{field_name} must be a non-empty list"
                    )
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(
                            f"applied_recommendations[{index}].{field_name} must contain non-empty strings"
                        )

            for field_name, minimum, maximum in (
                ("previous_weight", 0.0, 1.0),
                ("applied_weight_delta", 0.0, PROCEDURAL_MAX_WEIGHT_DELTA),
                ("resulting_weight", 0.0, 1.0),
            ):
                MemoryCrystalStore._require_number_in_range(
                    record.get(field_name),
                    minimum,
                    maximum,
                    f"applied_recommendations[{index}].{field_name}",
                    errors,
                )

            digest = record.get("digest")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"applied_recommendations[{index}].digest must be a sha256 hex string")
            else:
                expected_digest = sha256_text(canonical_json(_procedural_writeback_digest_payload(record)))
                if digest != expected_digest:
                    errors.append(f"applied_recommendations[{index}].digest mismatch")

        applied_recommendation_count = receipt.get("applied_recommendation_count")
        if applied_recommendation_count != len(applied_recommendations):
            errors.append(
                "applied_recommendation_count must equal len(applied_recommendations) "
                f"({len(applied_recommendations)}), got {applied_recommendation_count!r}"
            )

        approval_bundle = receipt.get("approval_bundle")
        if not isinstance(approval_bundle, dict):
            errors.append("approval_bundle must be an object")
        else:
            for field_name in (
                "self_attestation_id",
                "council_attestation_id",
                "guardian_attestation_id",
                "approval_reason",
            ):
                MemoryCrystalStore._require_non_empty_string(
                    approval_bundle.get(field_name),
                    f"approval_bundle.{field_name}",
                    errors,
                )
            human_reviewers = approval_bundle.get("human_reviewers", [])
            if not isinstance(human_reviewers, list):
                errors.append("approval_bundle.human_reviewers must be a list")
                human_reviewers = []
            else:
                for reviewer in human_reviewers:
                    if not isinstance(reviewer, str) or not reviewer.strip():
                        errors.append("approval_bundle.human_reviewers must contain non-empty strings")
                if human_reviewers != _dedupe_preserve_order(human_reviewers):
                    errors.append("approval_bundle.human_reviewers must be deduplicated")
                if len(human_reviewers) < PROCEDURAL_REQUIRED_HUMAN_REVIEWERS:
                    errors.append(
                        f"approval_bundle.human_reviewers must contain at least {PROCEDURAL_REQUIRED_HUMAN_REVIEWERS} reviewers"
                    )

        continuity_diff = receipt.get("continuity_diff")
        if not isinstance(continuity_diff, dict):
            errors.append("continuity_diff must be an object")
        else:
            for field_name in ("diff_id", "recorded_by", "event_type"):
                MemoryCrystalStore._require_non_empty_string(
                    continuity_diff.get(field_name),
                    f"continuity_diff.{field_name}",
                    errors,
                )
            if continuity_diff.get("event_type") != "mind.memory.procedural_applied":
                errors.append("continuity_diff.event_type mismatch")
            mutated = continuity_diff.get("mutated_edge_ids")
            if not isinstance(mutated, list) or not mutated:
                errors.append("continuity_diff.mutated_edge_ids must be a non-empty list")
            elif mutated != mutated_edge_ids:
                errors.append("continuity_diff.mutated_edge_ids must match applied target_edge_ids")
            target_paths_value = continuity_diff.get("target_paths")
            if not isinstance(target_paths_value, list) or not target_paths_value:
                errors.append("continuity_diff.target_paths must be a non-empty list")
            elif target_paths_value != target_paths:
                errors.append("continuity_diff.target_paths must match applied target_paths")

        if receipt.get("status") != "approved":
            errors.append("status must equal 'approved'")

        unchanged_edge_ids = receipt.get("unchanged_edge_ids")
        if not isinstance(unchanged_edge_ids, list):
            errors.append("unchanged_edge_ids must be a list")

        connectome_validation = ConnectomeModel().validate(updated_connectome_document)
        if not connectome_validation["ok"]:
            errors.append("updated_connectome_document must satisfy Connectome validation")
        else:
            if receipt.get("identity_id") != updated_connectome_document.get("identity_id"):
                errors.append("receipt.identity_id must match updated_connectome_document.identity_id")
            if receipt.get("output_connectome_snapshot_id") != updated_connectome_document.get("snapshot_id"):
                errors.append(
                    "output_connectome_snapshot_id must match updated_connectome_document.snapshot_id"
                )
            expected_output_digest = sha256_text(canonical_json(updated_connectome_document))
            if receipt.get("output_connectome_digest") != expected_output_digest:
                errors.append("output_connectome_digest mismatch")
            if isinstance(unchanged_edge_ids, list):
                all_edge_ids = [edge["id"] for edge in updated_connectome_document["edges"]]
                expected_unchanged = [edge_id for edge_id in all_edge_ids if edge_id not in mutated_edge_ids]
                if unchanged_edge_ids != expected_unchanged:
                    errors.append("unchanged_edge_ids mismatch")

        if preview_snapshot is not None:
            preview_validation = ProceduralMemoryProjector().validate(preview_snapshot)
            if not preview_validation["ok"]:
                errors.append("preview_snapshot must satisfy ProceduralMemoryProjector validation")
            else:
                expected_preview_digest = sha256_text(canonical_json(preview_snapshot))
                if receipt.get("source_preview_digest") != expected_preview_digest:
                    errors.append("source_preview_digest mismatch")
                expected_ids = [record["recommendation_id"] for record in applied_recommendations]
                if selected_ids != expected_ids:
                    errors.append(
                        "source_preview_recommendation_ids must match applied recommendation_ids"
                    )

        return {
            "ok": not errors,
            "applied_recommendation_count": len(applied_recommendations),
            "target_paths": target_paths,
            "human_reviewers": human_reviewers,
            "errors": errors,
        }

    @staticmethod
    def _normalize_selected_recommendation_ids(
        recommendations: Sequence[Dict[str, Any]],
        selected_recommendation_ids: Sequence[str] | None,
    ) -> List[str]:
        available_ids = [recommendation["recommendation_id"] for recommendation in recommendations]
        if selected_recommendation_ids is None:
            return list(available_ids)
        normalized = _dedupe_preserve_order(
            [
                recommendation_id.strip()
                for recommendation_id in selected_recommendation_ids
                if isinstance(recommendation_id, str) and recommendation_id.strip()
            ]
        )
        if not normalized:
            raise ValueError("selected_recommendation_ids must contain at least one recommendation id")
        missing = [recommendation_id for recommendation_id in normalized if recommendation_id not in available_ids]
        if missing:
            raise ValueError(f"selected_recommendation_ids contain unknown ids: {missing}")
        return normalized


class ProceduralSkillExecutor:
    """Executes sandboxed procedural rehearsals after validated writeback."""

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "policy_id": PROCEDURAL_SKILL_EXECUTION_POLICY_ID,
            "source_writeback_policy": PROCEDURAL_WRITEBACK_POLICY_ID,
            "target_connectome_schema": CONNECTOME_SCHEMA_VERSION,
            "delivery_scope": "sandbox-only",
            "external_actuation_allowed": False,
            "guardian_witness_required": True,
            "required_human_reviewers": PROCEDURAL_REQUIRED_HUMAN_REVIEWERS,
            "rollback_token_required": True,
            "max_rehearsal_steps": PROCEDURAL_MAX_REHEARSAL_STEPS,
        }

    def execute(
        self,
        identity_id: str,
        writeback_receipt: Dict[str, Any],
        updated_connectome_document: Dict[str, Any],
        *,
        sandbox_session_id: str,
        guardian_witness_id: str,
        selected_recommendation_ids: Sequence[str] | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not isinstance(writeback_receipt, dict):
            raise ValueError("writeback_receipt must be a mapping")
        if not isinstance(updated_connectome_document, dict):
            raise ValueError("updated_connectome_document must be a mapping")
        for field_name, value in (
            ("sandbox_session_id", sandbox_session_id),
            ("guardian_witness_id", guardian_witness_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        writeback_validation = ProceduralMemoryWritebackGate().validate(
            writeback_receipt,
            updated_connectome_document,
        )
        if not writeback_validation["ok"]:
            raise ValueError(
                "procedural skill execution requires a valid writeback receipt: "
                f"{writeback_validation['errors']}"
            )
        if writeback_receipt.get("identity_id") != identity_id:
            raise ValueError("identity_id must match writeback_receipt.identity_id")
        if updated_connectome_document.get("identity_id") != identity_id:
            raise ValueError("identity_id must match updated_connectome_document.identity_id")
        if writeback_receipt.get("output_connectome_snapshot_id") != updated_connectome_document.get(
            "snapshot_id"
        ):
            raise ValueError(
                "writeback_receipt.output_connectome_snapshot_id must match updated_connectome_document.snapshot_id"
            )

        selected_ids = self._normalize_selected_recommendation_ids(
            writeback_receipt["applied_recommendations"],
            selected_recommendation_ids,
        )
        selected_recommendations = [
            recommendation
            for recommendation in writeback_receipt["applied_recommendations"]
            if recommendation["recommendation_id"] in selected_ids
        ]
        if len(selected_recommendations) > PROCEDURAL_MAX_REHEARSAL_STEPS:
            raise ValueError(
                f"selected_recommendation_ids must contain at most {PROCEDURAL_MAX_REHEARSAL_STEPS} items"
            )

        executions = [
            self._build_execution_record(
                recommendation,
                sandbox_session_id=sandbox_session_id.strip(),
            )
            for recommendation in selected_recommendations
        ]
        receipt = {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "identity_id": identity_id,
            "executed_at": utc_now_iso(),
            "execution_policy": self.profile(),
            "source_writeback_digest": sha256_text(canonical_json(writeback_receipt)),
            "source_preview_digest": writeback_receipt["source_preview_digest"],
            "connectome_snapshot_id": updated_connectome_document["snapshot_id"],
            "connectome_snapshot_digest": sha256_text(canonical_json(updated_connectome_document)),
            "sandbox_session_id": sandbox_session_id.strip(),
            "guardian_witness_id": guardian_witness_id.strip(),
            "executed_recommendation_ids": list(selected_ids),
            "execution_count": len(executions),
            "executions": executions,
            "status": "sandbox-complete",
            "rollback_token": writeback_receipt["rollback_token"],
            "external_effects": [],
            "preserved_invariants": [
                "no-external-actuation",
                "guardian-witnessed",
                "rollback-token-retained",
            ],
        }

        validation = self.validate(receipt, updated_connectome_document, writeback_receipt)
        if not validation["ok"]:
            raise ValueError(
                f"procedural skill execution receipt failed validation: {validation['errors']}"
            )
        return receipt

    def validate(
        self,
        receipt: Dict[str, Any],
        updated_connectome_document: Dict[str, Any],
        writeback_receipt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        skill_labels: List[str] = []

        if not isinstance(receipt, dict):
            raise ValueError("receipt must be a mapping")
        if not isinstance(updated_connectome_document, dict):
            raise ValueError("updated_connectome_document must be a mapping")
        if receipt.get("schema_version") != PROCEDURAL_MEMORY_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {PROCEDURAL_MEMORY_SCHEMA_VERSION}, "
                f"got {receipt.get('schema_version')!r}"
            )

        for field_name in (
            "identity_id",
            "executed_at",
            "connectome_snapshot_id",
            "sandbox_session_id",
            "guardian_witness_id",
            "rollback_token",
        ):
            MemoryCrystalStore._require_non_empty_string(receipt.get(field_name), field_name, errors)

        execution_policy = receipt.get("execution_policy")
        if not isinstance(execution_policy, dict):
            errors.append("execution_policy must be an object")
        else:
            expected_policy = self.profile()
            for field_name, expected_value in expected_policy.items():
                if execution_policy.get(field_name) != expected_value:
                    errors.append(f"execution_policy.{field_name} mismatch")

        for field_name in (
            "source_writeback_digest",
            "source_preview_digest",
            "connectome_snapshot_digest",
        ):
            value = receipt.get(field_name)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"{field_name} must be a sha256 hex string")

        executed_recommendation_ids = receipt.get("executed_recommendation_ids")
        if not isinstance(executed_recommendation_ids, list) or not executed_recommendation_ids:
            errors.append("executed_recommendation_ids must be a non-empty list")
            executed_recommendation_ids = []
        else:
            for recommendation_id in executed_recommendation_ids:
                if not isinstance(recommendation_id, str) or not recommendation_id.strip():
                    errors.append("executed_recommendation_ids must contain non-empty strings")
            if executed_recommendation_ids != _dedupe_preserve_order(executed_recommendation_ids):
                errors.append("executed_recommendation_ids must be deduplicated")
            if len(executed_recommendation_ids) > PROCEDURAL_MAX_REHEARSAL_STEPS:
                errors.append(
                    f"executed_recommendation_ids must contain at most {PROCEDURAL_MAX_REHEARSAL_STEPS} items"
                )

        executions = receipt.get("executions")
        if not isinstance(executions, list) or not executions:
            errors.append("executions must be a non-empty list")
            executions = []

        seen_execution_ids = set()
        seen_recommendation_ids = []
        continuity_refs: List[str] = []
        for index, execution in enumerate(executions):
            if not isinstance(execution, dict):
                errors.append(f"executions[{index}] must be an object")
                continue

            for field_name in (
                "execution_id",
                "recommendation_id",
                "target_edge_id",
                "target_path",
                "skill_label",
                "rehearsal_prompt",
                "sandbox_action",
                "source_recommendation_digest",
                "continuity_ref",
                "result_summary",
                "evidence_ref",
            ):
                MemoryCrystalStore._require_non_empty_string(
                    execution.get(field_name),
                    f"executions[{index}].{field_name}",
                    errors,
                )

            execution_id = execution.get("execution_id")
            if isinstance(execution_id, str) and execution_id:
                if execution_id in seen_execution_ids:
                    errors.append(f"duplicate execution_id: {execution_id}")
                else:
                    seen_execution_ids.add(execution_id)

            recommendation_id = execution.get("recommendation_id")
            if isinstance(recommendation_id, str) and recommendation_id:
                seen_recommendation_ids.append(recommendation_id)

            skill_label = execution.get("skill_label")
            if isinstance(skill_label, str) and skill_label:
                skill_labels.append(skill_label)

            continuity_ref = execution.get("continuity_ref")
            if isinstance(continuity_ref, str) and continuity_ref:
                continuity_refs.append(continuity_ref)

            for field_name in ("source_segment_ids", "source_event_ids", "guardrails"):
                value = execution.get(field_name)
                if not isinstance(value, list) or not value:
                    errors.append(f"executions[{index}].{field_name} must be a non-empty list")
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(
                            f"executions[{index}].{field_name} must contain non-empty strings"
                        )

            MemoryCrystalStore._require_number_in_range(
                execution.get("rehearsal_window_ms"),
                1,
                1000,
                f"executions[{index}].rehearsal_window_ms",
                errors,
            )
            MemoryCrystalStore._require_number_in_range(
                execution.get("expected_confidence_gain"),
                0.0,
                1.0,
                f"executions[{index}].expected_confidence_gain",
                errors,
            )
            if execution.get("outcome") != "rehearsed":
                errors.append(f"executions[{index}].outcome must equal 'rehearsed'")

            digest = execution.get("digest")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"executions[{index}].digest must be a sha256 hex string")
            else:
                expected_digest = sha256_text(
                    canonical_json(_procedural_execution_digest_payload(execution))
                )
                if digest != expected_digest:
                    errors.append(f"executions[{index}].digest mismatch")

        execution_count = receipt.get("execution_count")
        if execution_count != len(executions):
            errors.append(
                f"execution_count must equal len(executions) ({len(executions)}), got {execution_count!r}"
            )

        if executed_recommendation_ids != seen_recommendation_ids:
            errors.append("executed_recommendation_ids must match executions.recommendation_id order")

        if receipt.get("status") != "sandbox-complete":
            errors.append("status must equal 'sandbox-complete'")

        external_effects = receipt.get("external_effects")
        if external_effects != []:
            errors.append("external_effects must equal []")

        preserved_invariants = receipt.get("preserved_invariants")
        expected_invariants = [
            "no-external-actuation",
            "guardian-witnessed",
            "rollback-token-retained",
        ]
        if preserved_invariants != expected_invariants:
            errors.append(f"preserved_invariants must equal {expected_invariants!r}")

        connectome_validation = ConnectomeModel().validate(updated_connectome_document)
        if not connectome_validation["ok"]:
            errors.append("updated_connectome_document must satisfy Connectome validation")
        else:
            if receipt.get("identity_id") != updated_connectome_document.get("identity_id"):
                errors.append("receipt.identity_id must match updated_connectome_document.identity_id")
            if receipt.get("connectome_snapshot_id") != updated_connectome_document.get("snapshot_id"):
                errors.append(
                    "connectome_snapshot_id must match updated_connectome_document.snapshot_id"
                )
            expected_connectome_digest = sha256_text(canonical_json(updated_connectome_document))
            if receipt.get("connectome_snapshot_digest") != expected_connectome_digest:
                errors.append("connectome_snapshot_digest mismatch")

        if writeback_receipt is not None:
            writeback_validation = ProceduralMemoryWritebackGate().validate(
                writeback_receipt,
                updated_connectome_document,
            )
            if not writeback_validation["ok"]:
                errors.append(
                    "writeback_receipt must satisfy ProceduralMemoryWritebackGate validation"
                )
            else:
                expected_writeback_digest = sha256_text(canonical_json(writeback_receipt))
                if receipt.get("source_writeback_digest") != expected_writeback_digest:
                    errors.append("source_writeback_digest mismatch")
                if receipt.get("source_preview_digest") != writeback_receipt.get("source_preview_digest"):
                    errors.append("source_preview_digest mismatch")
                if receipt.get("rollback_token") != writeback_receipt.get("rollback_token"):
                    errors.append("rollback_token mismatch")
                if executed_recommendation_ids:
                    available_ids = [
                        record["recommendation_id"]
                        for record in writeback_receipt["applied_recommendations"]
                    ]
                    missing_ids = [
                        recommendation_id
                        for recommendation_id in executed_recommendation_ids
                        if recommendation_id not in available_ids
                    ]
                    if missing_ids:
                        errors.append(
                            f"executed_recommendation_ids contain unknown writeback ids: {missing_ids}"
                        )
                expected_refs = [
                    record["continuity_diff_ref"]
                    for record in writeback_receipt["applied_recommendations"]
                    if record["recommendation_id"] in executed_recommendation_ids
                ]
                if continuity_refs != expected_refs:
                    errors.append("executions.continuity_ref must match selected writeback continuity refs")

        return {
            "ok": not errors,
            "execution_count": len(executions),
            "skill_labels": skill_labels,
            "delivery_scope": "sandbox-only",
            "rollback_token_preserved": not errors or (
                writeback_receipt is not None
                and receipt.get("rollback_token") == writeback_receipt.get("rollback_token")
            ),
            "errors": errors,
        }

    @staticmethod
    def _normalize_selected_recommendation_ids(
        applied_recommendations: Sequence[Dict[str, Any]],
        selected_recommendation_ids: Sequence[str] | None,
    ) -> List[str]:
        available_ids = [
            recommendation["recommendation_id"] for recommendation in applied_recommendations
        ]
        if selected_recommendation_ids is None:
            return list(available_ids)
        normalized = _dedupe_preserve_order(
            [
                recommendation_id.strip()
                for recommendation_id in selected_recommendation_ids
                if isinstance(recommendation_id, str) and recommendation_id.strip()
            ]
        )
        if not normalized:
            raise ValueError("selected_recommendation_ids must contain at least one recommendation id")
        missing = [
            recommendation_id for recommendation_id in normalized if recommendation_id not in available_ids
        ]
        if missing:
            raise ValueError(f"selected_recommendation_ids contain unknown ids: {missing}")
        return normalized

    def _build_execution_record(
        self,
        recommendation: Dict[str, Any],
        *,
        sandbox_session_id: str,
    ) -> Dict[str, Any]:
        target_path = recommendation["target_path"]
        if target_path == "continuity_integrator->ethics_gate":
            skill_label = "guardian-review-rehearsal"
            sandbox_action = "replay-guardian-checklist"
            rehearsal_prompt = (
                "Continuity evidence を guardian checklist と照合し、"
                "ethics gate 手前で停止条件を rehearsal する"
            )
        else:
            skill_label = "migration-handoff-rehearsal"
            sandbox_action = "rehearse-handoff-checklist"
            rehearsal_prompt = (
                "Migration handoff の hash 照合と warm-standby continuity 確認を "
                "sandbox 内で反復する"
            )

        execution = {
            "execution_id": new_id("procedural-execution"),
            "recommendation_id": recommendation["recommendation_id"],
            "target_edge_id": recommendation["target_edge_id"],
            "target_path": target_path,
            "skill_label": skill_label,
            "rehearsal_prompt": rehearsal_prompt,
            "sandbox_action": sandbox_action,
            "rehearsal_window_ms": 750,
            "expected_confidence_gain": round(
                min(0.99, 0.25 + float(recommendation["applied_weight_delta"]) * 3.5),
                3,
            ),
            "source_segment_ids": list(recommendation["source_segment_ids"]),
            "source_event_ids": list(recommendation["source_event_ids"]),
            "source_recommendation_digest": recommendation["source_recommendation_digest"],
            "continuity_ref": recommendation["continuity_diff_ref"],
            "guardrails": [
                "sandbox-only",
                "no external actuation",
                "guardian witness required",
                f"session-bound:{sandbox_session_id}",
            ],
            "outcome": "rehearsed",
            "result_summary": (
                f"{skill_label} を {target_path} に対して sandbox 内で rehearsal し、"
                "rollback-ready 境界を維持した"
            ),
            "evidence_ref": f"{sandbox_session_id}/{recommendation['recommendation_id']}",
        }
        execution["digest"] = sha256_text(
            canonical_json(_procedural_execution_digest_payload(execution))
        )
        return execution


def receipt_edge_ids(applied_recommendations: Sequence[Dict[str, Any]]) -> List[str]:
    return [record["target_edge_id"] for record in applied_recommendations]
