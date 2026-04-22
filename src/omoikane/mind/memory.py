"""Episodic stream and MemoryCrystal reference models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
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
SEMANTIC_PROCEDURAL_HANDOFF_SCHEMA_VERSION = "1.0"
SEMANTIC_PROCEDURAL_HANDOFF_POLICY_ID = "semantic-to-procedural-preview-handoff-v1"
SEMANTIC_PROCEDURAL_HANDOFF_TARGET_NAMESPACE = "mind.procedural.v0"
SEMANTIC_PROCEDURAL_HANDOFF_REQUIRED_EVALS = [
    "evals/continuity/semantic_procedural_handoff.yaml",
]
MEMORY_EDIT_SCHEMA_VERSION = "1.0"
MEMORY_EDIT_POLICY_ID = "consented-recall-affect-buffer-v1"
MEMORY_EDIT_ALLOWED_OPERATION = "affect-buffer-on-recall"
MEMORY_EDIT_MAX_BUFFER_RATIO = 0.65
MEMORY_EDIT_REQUIRED_APPROVALS = ["self", "guardian"]
MEMORY_EDIT_PROHIBITED_OPERATIONS = [
    "delete-memory",
    "insert-false-memory",
    "overwrite-source-segment",
]
MEMORY_EDIT_DISCLOSURE_SCOPE = "self-only"
MEMORY_EDIT_SOURCE_SURFACE = "semantic-memory-read-only"
PROCEDURAL_MEMORY_SCHEMA_VERSION = "1.0"
PROCEDURAL_PREVIEW_POLICY_ID = "connectome-coupled-procedural-preview-v1"
PROCEDURAL_MAX_WEIGHT_DELTA = 0.08
PROCEDURAL_DEFERRED_SURFACES = ["skill-execution"]
PROCEDURAL_WRITEBACK_POLICY_ID = "human-approved-procedural-writeback-v1"
PROCEDURAL_REQUIRED_HUMAN_REVIEWERS = 2
PROCEDURAL_SKILL_EXECUTION_POLICY_ID = "guardian-witnessed-procedural-skill-execution-v1"
PROCEDURAL_MAX_REHEARSAL_STEPS = 3
PROCEDURAL_SKILL_ENACTMENT_POLICY_ID = "guardian-witnessed-procedural-skill-enactment-v1"
PROCEDURAL_MANDATORY_ENACTMENT_EVAL = "evals/continuity/procedural_skill_enactment_execution.yaml"
PROCEDURAL_ENACTMENT_WORKSPACE_PREFIX = "omoikane-procedural-enact-"
PROCEDURAL_ENACTMENT_COMMAND_TIMEOUT_SECONDS = 15


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


def _memory_recall_view_digest_payload(view: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in view.items() if key != "digest"}


def _semantic_procedural_concept_binding_digest_payload(binding: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in binding.items() if key != "digest"}


def _semantic_procedural_handoff_digest_payload(handoff: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in handoff.items() if key != "digest"}


def _procedural_recommendation_digest_payload(recommendation: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in recommendation.items() if key != "digest"}


def _procedural_writeback_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "digest"}


def _procedural_execution_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "digest"}


def _procedural_enactment_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "digest"}


def _slugify_text(value: str) -> str:
    lowered = value.strip().lower()
    characters = [
        character if character.isalnum() else "-"
        for character in lowered
    ]
    slug = "".join(characters)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "skill"


def _excerpt(text: str, *, limit: int = 160) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[-limit:]


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


def _reference_memory_edit_seed_events() -> List[Dict[str, Any]]:
    return [
        asdict(
            EpisodicEvent(
                event_id="memory-edit-episode-0001",
                occurred_at="2026-04-21T09:00:00+00:00",
                summary="Unexpected shutdown rehearsal で強い恐怖反応が立ち上がり Guardian hold が発火した",
                tags=["trauma-recall", "guardian-hold", "continuity"],
                salience=0.96,
                valence=-0.81,
                arousal=0.88,
                source_refs=[
                    "ledger://guardian-hold/trauma-recall-0001",
                    "qualia://tick/trauma-recall-0001",
                ],
                attention_target="guardian.hold.recall",
                narrative_role="observation",
                self_coherence=0.74,
                continuity_ref="ledger://entry/memory-edit-0001",
            )
        ),
        asdict(
            EpisodicEvent(
                event_id="memory-edit-episode-0002",
                occurred_at="2026-04-21T09:02:00+00:00",
                summary="Guardian と本人が想起 trigger と身体反応の境界を確認し再体験を停止した",
                tags=["trauma-recall", "guardian-review", "stabilization"],
                salience=0.91,
                valence=-0.63,
                arousal=0.79,
                source_refs=[
                    "oversight://guardian/reviewer-omega",
                    "ledger://guardian-review/trauma-recall-0001",
                ],
                attention_target="guardian.review.recall",
                narrative_role="resolution",
                self_coherence=0.81,
                continuity_ref="ledger://entry/memory-edit-0002",
            )
        ),
        asdict(
            EpisodicEvent(
                event_id="memory-edit-episode-0003",
                occurred_at="2026-04-21T09:05:00+00:00",
                summary="内容は保持したまま想起時 affect を弱める care plan を freeze snapshot 付きで合意した",
                tags=["trauma-recall", "care-plan", "freeze"],
                salience=0.89,
                valence=-0.52,
                arousal=0.69,
                source_refs=[
                    "care://memory-buffer/plan-0001",
                    "freeze://memory-edit/pre-buffer-0001",
                ],
                attention_target="care.plan.recall-buffer",
                narrative_role="verification",
                self_coherence=0.87,
                continuity_ref="ledger://entry/memory-edit-0003",
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

    def handoff_policy(self) -> Dict[str, Any]:
        return {
            "schema_version": SEMANTIC_PROCEDURAL_HANDOFF_SCHEMA_VERSION,
            "policy_id": SEMANTIC_PROCEDURAL_HANDOFF_POLICY_ID,
            "source_projection_policy": SEMANTIC_PROJECTION_POLICY_ID,
            "target_preview_policy": PROCEDURAL_PREVIEW_POLICY_ID,
            "target_namespace": SEMANTIC_PROCEDURAL_HANDOFF_TARGET_NAMESPACE,
            "handoff_mode": "digest-bound-concept-bridge",
            "read_only": True,
            "connectome_required": True,
            "required_eval_refs": list(SEMANTIC_PROCEDURAL_HANDOFF_REQUIRED_EVALS),
        }

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

    def prepare_procedural_handoff(
        self,
        identity_id: str,
        snapshot: Dict[str, Any],
        connectome_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a mapping")
        if not isinstance(connectome_document, dict):
            raise ValueError("connectome_document must be a mapping")

        snapshot_validation = self.validate(snapshot)
        if not snapshot_validation["ok"]:
            raise ValueError(
                "semantic snapshot must satisfy projection contract before handoff: "
                f"{snapshot_validation['errors']}"
            )
        connectome_validation = ConnectomeModel().validate(connectome_document)
        if not connectome_validation["ok"]:
            raise ValueError("connectome_document must satisfy Connectome validation")
        if snapshot.get("identity_id") != identity_id:
            raise ValueError("identity_id must match snapshot.identity_id")
        if connectome_document.get("identity_id") != identity_id:
            raise ValueError("identity_id must match connectome_document.identity_id")

        concept_bindings = [
            self._build_procedural_concept_binding(concept)
            for concept in snapshot["concepts"]
        ]
        handoff = {
            "kind": "semantic_procedural_handoff",
            "schema_version": SEMANTIC_PROCEDURAL_HANDOFF_SCHEMA_VERSION,
            "handoff_id": new_id("semantic-handoff"),
            "identity_id": identity_id,
            "generated_at": utc_now_iso(),
            "handoff_policy": self.handoff_policy(),
            "semantic_snapshot_digest": sha256_text(canonical_json(snapshot)),
            "source_manifest_digest": snapshot["source_manifest_digest"],
            "source_segment_ids": list(snapshot["source_segment_ids"]),
            "connectome_snapshot_id": connectome_document["snapshot_id"],
            "connectome_snapshot_digest": sha256_text(canonical_json(connectome_document)),
            "concept_count": len(concept_bindings),
            "concept_bindings": concept_bindings,
            "status": "ready",
        }
        handoff["digest"] = sha256_text(canonical_json(_semantic_procedural_handoff_digest_payload(handoff)))
        validation = self.validate_procedural_handoff(
            handoff,
            semantic_snapshot=snapshot,
            connectome_document=connectome_document,
        )
        if not validation["ok"]:
            raise ValueError(
                f"semantic procedural handoff failed validation: {validation['errors']}"
            )
        return handoff

    def validate_procedural_handoff(
        self,
        handoff: Dict[str, Any],
        *,
        semantic_snapshot: Dict[str, Any] | None = None,
        manifest: Dict[str, Any] | None = None,
        connectome_document: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        canonical_labels: List[str] = []

        if not isinstance(handoff, dict):
            raise ValueError("handoff must be a mapping")
        if handoff.get("kind") != "semantic_procedural_handoff":
            errors.append("kind must equal 'semantic_procedural_handoff'")
        if handoff.get("schema_version") != SEMANTIC_PROCEDURAL_HANDOFF_SCHEMA_VERSION:
            errors.append(
                "schema_version must equal "
                f"{SEMANTIC_PROCEDURAL_HANDOFF_SCHEMA_VERSION!r}"
            )
        MemoryCrystalStore._require_non_empty_string(handoff.get("handoff_id"), "handoff_id", errors)
        identity_id = handoff.get("identity_id")
        MemoryCrystalStore._require_non_empty_string(identity_id, "identity_id", errors)
        MemoryCrystalStore._require_non_empty_string(handoff.get("generated_at"), "generated_at", errors)

        handoff_policy = handoff.get("handoff_policy")
        if not isinstance(handoff_policy, dict):
            errors.append("handoff_policy must be an object")
        else:
            expected_policy = self.handoff_policy()
            for field_name, expected_value in expected_policy.items():
                if handoff_policy.get(field_name) != expected_value:
                    errors.append(f"handoff_policy.{field_name} mismatch")

        for field_name in (
            "semantic_snapshot_digest",
            "source_manifest_digest",
            "connectome_snapshot_digest",
            "digest",
        ):
            value = handoff.get(field_name)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"{field_name} must be a sha256 hex string")

        source_segment_ids = handoff.get("source_segment_ids")
        if not isinstance(source_segment_ids, list) or not source_segment_ids:
            errors.append("source_segment_ids must be a non-empty list")
            source_segment_ids = []
        else:
            for segment_id in source_segment_ids:
                if not isinstance(segment_id, str) or not segment_id.strip():
                    errors.append("source_segment_ids must contain non-empty strings")

        connectome_snapshot_id = handoff.get("connectome_snapshot_id")
        MemoryCrystalStore._require_non_empty_string(
            connectome_snapshot_id,
            "connectome_snapshot_id",
            errors,
        )

        concept_bindings = handoff.get("concept_bindings")
        if not isinstance(concept_bindings, list) or not concept_bindings:
            errors.append("concept_bindings must be a non-empty list")
            concept_bindings = []

        seen_binding_ids = set()
        seen_segment_ids = set()
        binding_map: Dict[str, Dict[str, Any]] = {}
        for index, binding in enumerate(concept_bindings):
            if not isinstance(binding, dict):
                errors.append(f"concept_bindings[{index}] must be an object")
                continue
            concept_id = binding.get("concept_id")
            MemoryCrystalStore._require_non_empty_string(
                concept_id,
                f"concept_bindings[{index}].concept_id",
                errors,
            )
            if isinstance(concept_id, str) and concept_id:
                if concept_id in seen_binding_ids:
                    errors.append(f"duplicate concept_bindings concept_id: {concept_id}")
                else:
                    seen_binding_ids.add(concept_id)
                    binding_map[concept_id] = binding

            canonical_label = binding.get("canonical_label")
            MemoryCrystalStore._require_non_empty_string(
                canonical_label,
                f"concept_bindings[{index}].canonical_label",
                errors,
            )
            if isinstance(canonical_label, str) and canonical_label:
                canonical_labels.append(canonical_label)

            for field_name in ("supporting_segment_ids", "supporting_event_ids", "retrieval_cues"):
                value = binding.get(field_name)
                if not isinstance(value, list) or not value:
                    errors.append(f"concept_bindings[{index}].{field_name} must be a non-empty list")
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(
                            f"concept_bindings[{index}].{field_name} must contain non-empty strings"
                        )
                if field_name == "supporting_segment_ids":
                    seen_segment_ids.update(value)

            source_segment_digest = binding.get("source_segment_digest")
            if not isinstance(source_segment_digest, str) or len(source_segment_digest) != 64:
                errors.append(
                    f"concept_bindings[{index}].source_segment_digest must be a sha256 hex string"
                )
            MemoryCrystalStore._require_number_in_range(
                binding.get("confidence"),
                0.0,
                1.0,
                f"concept_bindings[{index}].confidence",
                errors,
            )

            digest = binding.get("digest")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"concept_bindings[{index}].digest must be a sha256 hex string")
            else:
                expected_digest = sha256_text(
                    canonical_json(_semantic_procedural_concept_binding_digest_payload(binding))
                )
                if digest != expected_digest:
                    errors.append(f"concept_bindings[{index}].digest mismatch")

        concept_count = handoff.get("concept_count")
        if concept_count != len(concept_bindings):
            errors.append(
                f"concept_count must equal len(concept_bindings) ({len(concept_bindings)}), "
                f"got {concept_count!r}"
            )
        if handoff.get("status") != "ready":
            errors.append("status must equal 'ready'")

        if isinstance(source_segment_ids, list) and source_segment_ids and seen_segment_ids:
            if sorted(source_segment_ids) != sorted(seen_segment_ids):
                errors.append("source_segment_ids must equal the union of supporting_segment_ids")

        if semantic_snapshot is not None:
            semantic_validation = self.validate(semantic_snapshot)
            if not semantic_validation["ok"]:
                errors.append(
                    "semantic_snapshot must satisfy projection contract: "
                    f"{semantic_validation['errors']}"
                )
            else:
                if semantic_snapshot.get("identity_id") != identity_id:
                    errors.append("identity_id must match semantic_snapshot.identity_id")
                expected_digest = sha256_text(canonical_json(semantic_snapshot))
                if handoff.get("semantic_snapshot_digest") != expected_digest:
                    errors.append("semantic_snapshot_digest mismatch")
                if handoff.get("source_manifest_digest") != semantic_snapshot.get("source_manifest_digest"):
                    errors.append("source_manifest_digest must match semantic_snapshot")
                if handoff.get("source_segment_ids") != semantic_snapshot.get("source_segment_ids"):
                    errors.append("source_segment_ids must match semantic_snapshot")
                concept_map = {
                    concept["concept_id"]: concept for concept in semantic_snapshot.get("concepts", [])
                }
                if len(concept_map) != len(concept_bindings):
                    errors.append("semantic_snapshot concept_count must match concept_bindings")
                for concept_id, binding in binding_map.items():
                    concept = concept_map.get(concept_id)
                    if concept is None:
                        errors.append(
                            f"concept_bindings[{concept_id}] must reference semantic_snapshot concept_id"
                        )
                        continue
                    for field_name in (
                        "canonical_label",
                        "supporting_segment_ids",
                        "supporting_event_ids",
                        "retrieval_cues",
                        "source_segment_digest",
                    ):
                        if binding.get(field_name) != concept.get(field_name):
                            errors.append(
                                f"concept_bindings[{concept_id}].{field_name} must match semantic_snapshot"
                            )
                    if binding.get("confidence") != concept.get("confidence"):
                        errors.append(
                            f"concept_bindings[{concept_id}].confidence must match semantic_snapshot"
                        )

        if manifest is not None:
            manifest_validation = MemoryCrystalStore().validate(manifest)
            if not manifest_validation["ok"]:
                errors.append(
                    f"manifest must satisfy MemoryCrystal validation: {manifest_validation['errors']}"
                )
            else:
                if manifest.get("identity_id") != identity_id:
                    errors.append("identity_id must match manifest.identity_id")
                expected_manifest_digest = sha256_text(canonical_json(manifest))
                if handoff.get("source_manifest_digest") != expected_manifest_digest:
                    errors.append("source_manifest_digest must match manifest digest")
                manifest_segment_ids = [segment["segment_id"] for segment in manifest["segments"]]
                if handoff.get("source_segment_ids") != manifest_segment_ids:
                    errors.append("source_segment_ids must match manifest segment ids")
                manifest_segment_digests = {
                    segment["segment_id"]: segment["digest"] for segment in manifest["segments"]
                }
                for concept_id, binding in binding_map.items():
                    supporting_segment_ids = binding.get("supporting_segment_ids", [])
                    if any(segment_id not in manifest_segment_digests for segment_id in supporting_segment_ids):
                        errors.append(
                            f"concept_bindings[{concept_id}] must reference manifest segment ids"
                        )
                        continue
                    if len(supporting_segment_ids) == 1:
                        segment_id = supporting_segment_ids[0]
                        if binding.get("source_segment_digest") != manifest_segment_digests[segment_id]:
                            errors.append(
                                f"concept_bindings[{concept_id}].source_segment_digest must match manifest"
                            )

        if connectome_document is not None:
            connectome_validation = ConnectomeModel().validate(connectome_document)
            if not connectome_validation["ok"]:
                errors.append("connectome_document must satisfy Connectome validation")
            else:
                if connectome_document.get("identity_id") != identity_id:
                    errors.append("identity_id must match connectome_document.identity_id")
                if handoff.get("connectome_snapshot_id") != connectome_document.get("snapshot_id"):
                    errors.append("connectome_snapshot_id must match connectome_document.snapshot_id")
                expected_connectome_digest = sha256_text(canonical_json(connectome_document))
                if handoff.get("connectome_snapshot_digest") != expected_connectome_digest:
                    errors.append("connectome_snapshot_digest must match connectome_document digest")

        digest = handoff.get("digest")
        if isinstance(digest, str) and len(digest) == 64:
            expected_digest = sha256_text(canonical_json(_semantic_procedural_handoff_digest_payload(handoff)))
            if digest != expected_digest:
                errors.append("digest mismatch")

        return {
            "ok": not errors,
            "concept_count": len(concept_bindings),
            "canonical_labels": canonical_labels,
            "target_namespace": SEMANTIC_PROCEDURAL_HANDOFF_TARGET_NAMESPACE,
            "status": handoff.get("status", ""),
            "errors": errors,
        }

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

    def _build_procedural_concept_binding(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        binding = {
            "concept_id": concept["concept_id"],
            "canonical_label": concept["canonical_label"],
            "supporting_segment_ids": list(concept["supporting_segment_ids"]),
            "supporting_event_ids": list(concept["supporting_event_ids"]),
            "retrieval_cues": list(concept["retrieval_cues"]),
            "source_segment_digest": concept["source_segment_digest"],
            "confidence": concept["confidence"],
        }
        binding["digest"] = sha256_text(
            canonical_json(_semantic_procedural_concept_binding_digest_payload(binding))
        )
        return binding


class MemoryEditingService:
    """Constrains memory editing to reversible affect buffering on recall only."""

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": MEMORY_EDIT_SCHEMA_VERSION,
            "policy_id": MEMORY_EDIT_POLICY_ID,
            "source_surface": MEMORY_EDIT_SOURCE_SURFACE,
            "allowed_operation": MEMORY_EDIT_ALLOWED_OPERATION,
            "required_approvals": list(MEMORY_EDIT_REQUIRED_APPROVALS),
            "prohibited_operations": list(MEMORY_EDIT_PROHIBITED_OPERATIONS),
            "freeze_required": True,
            "source_mutation_allowed": False,
            "disclosure_scope": MEMORY_EDIT_DISCLOSURE_SCOPE,
            "max_buffer_ratio": MEMORY_EDIT_MAX_BUFFER_RATIO,
            "reversal_mode": "replay-original-affect-envelope",
        }

    def reference_events(self) -> List[Dict[str, Any]]:
        return deepcopy(_reference_memory_edit_seed_events())

    def build_reference_session(self, identity_id: str) -> Dict[str, Any]:
        manifest = MemoryCrystalStore().compact(identity_id, self.reference_events())
        snapshot = SemanticMemoryProjector().project(identity_id, manifest)
        return self.apply_recall_buffer(
            identity_id=identity_id,
            semantic_snapshot=snapshot,
            selected_concept_ids=[snapshot["concepts"][0]["concept_id"]],
            self_consent_ref="consent://memory-edit-demo/v1",
            guardian_attestation_ref="guardian://memory-edit-demo/reviewer-omega",
            clinical_rationale="本人同意のもと、想起内容は保持したまま affect 強度のみを緩和する",
            buffer_ratio=0.55,
        )

    def apply_recall_buffer(
        self,
        *,
        identity_id: str,
        semantic_snapshot: Dict[str, Any],
        selected_concept_ids: Sequence[str],
        self_consent_ref: str,
        guardian_attestation_ref: str,
        clinical_rationale: str,
        buffer_ratio: float,
        operation: str = MEMORY_EDIT_ALLOWED_OPERATION,
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if operation != MEMORY_EDIT_ALLOWED_OPERATION:
            raise ValueError(
                f"operation must be {MEMORY_EDIT_ALLOWED_OPERATION!r}; destructive memory edits are prohibited"
            )
        if not isinstance(buffer_ratio, (int, float)) or buffer_ratio <= 0 or buffer_ratio > MEMORY_EDIT_MAX_BUFFER_RATIO:
            raise ValueError(
                f"buffer_ratio must be > 0 and <= {MEMORY_EDIT_MAX_BUFFER_RATIO}"
            )
        for field_name, value in (
            ("self_consent_ref", self_consent_ref),
            ("guardian_attestation_ref", guardian_attestation_ref),
            ("clinical_rationale", clinical_rationale),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        validation = SemanticMemoryProjector().validate(semantic_snapshot)
        if not validation["ok"]:
            raise ValueError(f"semantic_snapshot must satisfy semantic projection validation: {validation['errors']}")
        if semantic_snapshot.get("identity_id") != identity_id:
            raise ValueError("identity_id must match semantic_snapshot.identity_id")

        concept_ids = [concept_id.strip() for concept_id in selected_concept_ids if isinstance(concept_id, str) and concept_id.strip()]
        if not concept_ids:
            raise ValueError("selected_concept_ids must contain at least one concept_id")
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError("selected_concept_ids must be unique")

        concepts_by_id = {
            concept["concept_id"]: concept
            for concept in semantic_snapshot["concepts"]
        }
        missing = [concept_id for concept_id in concept_ids if concept_id not in concepts_by_id]
        if missing:
            raise ValueError(f"unknown concept_id(s): {', '.join(missing)}")

        session_id = new_id("memory-edit")
        freeze_ref = f"freeze://memory-edit/{session_id}/pre-buffer"
        selected_concepts = [concepts_by_id[concept_id] for concept_id in concept_ids]
        recall_views = [
            self._build_recall_view(concept, buffer_ratio=round(float(buffer_ratio), 3), freeze_ref=freeze_ref)
            for concept in selected_concepts
        ]
        session = {
            "schema_version": MEMORY_EDIT_SCHEMA_VERSION,
            "identity_id": identity_id,
            "session_id": session_id,
            "opened_at": utc_now_iso(),
            "memory_edit_policy": self.profile(),
            "source_projection_policy": semantic_snapshot["projection_policy"]["policy_id"],
            "source_manifest_digest": semantic_snapshot["source_manifest_digest"],
            "source_concept_ids": list(concept_ids),
            "request": {
                "operation": operation,
                "self_consent_ref": self_consent_ref.strip(),
                "guardian_attestation_ref": guardian_attestation_ref.strip(),
                "clinical_rationale": clinical_rationale.strip(),
                "requested_buffer_ratio": round(float(buffer_ratio), 3),
                "disclosure_scope": MEMORY_EDIT_DISCLOSURE_SCOPE,
            },
            "freeze_record": {
                "freeze_id": new_id("memory-freeze"),
                "freeze_ref": freeze_ref,
                "frozen_at": utc_now_iso(),
                "source_manifest_digest": semantic_snapshot["source_manifest_digest"],
                "source_concept_digests": [concept["digest"] for concept in selected_concepts],
                "reversal_mode": "replay-original-affect-envelope",
                "source_mutation_allowed": False,
            },
            "recall_view_count": len(recall_views),
            "recall_views": recall_views,
            "status": "approved",
            "deletion_blocked": True,
        }
        session_validation = self.validate_session(session)
        if not session_validation["ok"]:
            raise ValueError(f"memory edit session failed validation: {session_validation['errors']}")
        return session

    def validate_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        disclosure_scopes: List[str] = []
        concept_labels: List[str] = []
        source_preserved = True
        freeze_bound = True
        buffer_within_limit = True

        if not isinstance(session, dict):
            raise ValueError("session must be a mapping")
        if session.get("schema_version") != MEMORY_EDIT_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {MEMORY_EDIT_SCHEMA_VERSION}, got {session.get('schema_version')!r}"
            )
        for field_name in ("identity_id", "session_id", "opened_at", "source_projection_policy", "source_manifest_digest"):
            MemoryCrystalStore._require_non_empty_string(session.get(field_name), field_name, errors)
        source_manifest_digest = session.get("source_manifest_digest")
        if isinstance(source_manifest_digest, str) and len(source_manifest_digest) != 64:
            errors.append("source_manifest_digest must be a sha256 hex string")

        policy = session.get("memory_edit_policy")
        if not isinstance(policy, dict):
            errors.append("memory_edit_policy must be an object")
        else:
            expected_policy = self.profile()
            for field_name, expected_value in expected_policy.items():
                if policy.get(field_name) != expected_value:
                    errors.append(f"memory_edit_policy.{field_name} mismatch")

        source_concept_ids = session.get("source_concept_ids")
        if not isinstance(source_concept_ids, list) or not source_concept_ids:
            errors.append("source_concept_ids must be a non-empty list")
            source_concept_ids = []
        else:
            for concept_id in source_concept_ids:
                if not isinstance(concept_id, str) or not concept_id.strip():
                    errors.append("source_concept_ids must contain non-empty strings")

        request = session.get("request")
        if not isinstance(request, dict):
            errors.append("request must be an object")
        else:
            if request.get("operation") != MEMORY_EDIT_ALLOWED_OPERATION:
                errors.append("request.operation must equal affect-buffer-on-recall")
            for field_name in ("self_consent_ref", "guardian_attestation_ref", "clinical_rationale"):
                MemoryCrystalStore._require_non_empty_string(request.get(field_name), f"request.{field_name}", errors)
            if request.get("disclosure_scope") != MEMORY_EDIT_DISCLOSURE_SCOPE:
                errors.append("request.disclosure_scope mismatch")
            requested_buffer_ratio = request.get("requested_buffer_ratio")
            if not isinstance(requested_buffer_ratio, (int, float)):
                errors.append("request.requested_buffer_ratio must be a number")
            elif requested_buffer_ratio <= 0 or requested_buffer_ratio > MEMORY_EDIT_MAX_BUFFER_RATIO:
                errors.append(
                    f"request.requested_buffer_ratio must be > 0 and <= {MEMORY_EDIT_MAX_BUFFER_RATIO}"
                )

        freeze_record = session.get("freeze_record")
        freeze_ref = ""
        freeze_digests: List[str] = []
        if not isinstance(freeze_record, dict):
            errors.append("freeze_record must be an object")
        else:
            for field_name in ("freeze_id", "freeze_ref", "frozen_at", "source_manifest_digest", "reversal_mode"):
                MemoryCrystalStore._require_non_empty_string(freeze_record.get(field_name), f"freeze_record.{field_name}", errors)
            freeze_ref = freeze_record.get("freeze_ref", "")
            if freeze_record.get("reversal_mode") != "replay-original-affect-envelope":
                errors.append("freeze_record.reversal_mode mismatch")
            if freeze_record.get("source_mutation_allowed") is not False:
                errors.append("freeze_record.source_mutation_allowed must be false")
            if freeze_record.get("source_manifest_digest") != source_manifest_digest:
                errors.append("freeze_record.source_manifest_digest mismatch")
                freeze_bound = False
            freeze_digests = freeze_record.get("source_concept_digests", [])
            if not isinstance(freeze_digests, list) or not freeze_digests:
                errors.append("freeze_record.source_concept_digests must be a non-empty list")
                freeze_digests = []
            else:
                for digest in freeze_digests:
                    if not isinstance(digest, str) or len(digest) != 64:
                        errors.append(
                            "freeze_record.source_concept_digests must contain sha256 hex strings"
                        )

        recall_views = session.get("recall_views")
        if not isinstance(recall_views, list) or not recall_views:
            errors.append("recall_views must be a non-empty list")
            recall_views = []

        seen_concept_ids = set()
        seen_digests = set()
        expected_digests: List[str] = []
        for index, view in enumerate(recall_views):
            if not isinstance(view, dict):
                errors.append(f"recall_views[{index}] must be an object")
                continue

            for field_name in (
                "recall_view_id",
                "concept_id",
                "canonical_label",
                "proposition",
                "source_concept_digest",
                "freeze_ref",
                "digest",
            ):
                MemoryCrystalStore._require_non_empty_string(view.get(field_name), f"recall_views[{index}].{field_name}", errors)

            concept_id = view.get("concept_id")
            if isinstance(concept_id, str) and concept_id:
                if concept_id in seen_concept_ids:
                    errors.append(f"duplicate recall view concept_id: {concept_id}")
                seen_concept_ids.add(concept_id)
            label = view.get("canonical_label")
            if isinstance(label, str) and label:
                concept_labels.append(label)

            for field_name in ("source_segment_ids", "source_event_ids", "source_refs", "retrieval_cues", "preservation_guards"):
                value = view.get(field_name)
                if not isinstance(value, list) or not value:
                    errors.append(f"recall_views[{index}].{field_name} must be a non-empty list")
                    source_preserved = False
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(
                            f"recall_views[{index}].{field_name} must contain non-empty strings"
                        )
                        source_preserved = False

            original_affect = view.get("original_affect_envelope")
            buffered_affect = view.get("buffered_affect_envelope")
            for envelope_name, envelope in (
                ("original_affect_envelope", original_affect),
                ("buffered_affect_envelope", buffered_affect),
            ):
                if not isinstance(envelope, dict):
                    errors.append(f"recall_views[{index}].{envelope_name} must be an object")
                    continue
                MemoryCrystalStore._require_number_in_range(
                    envelope.get("mean_valence"),
                    -1.0,
                    1.0,
                    f"recall_views[{index}].{envelope_name}.mean_valence",
                    errors,
                )
                MemoryCrystalStore._require_number_in_range(
                    envelope.get("mean_arousal"),
                    -1.0,
                    1.0,
                    f"recall_views[{index}].{envelope_name}.mean_arousal",
                    errors,
                )

            ratio = view.get("affect_buffer_ratio")
            if not isinstance(ratio, (int, float)) or ratio <= 0 or ratio > MEMORY_EDIT_MAX_BUFFER_RATIO:
                errors.append(
                    f"recall_views[{index}].affect_buffer_ratio must be > 0 and <= {MEMORY_EDIT_MAX_BUFFER_RATIO}"
                )
                buffer_within_limit = False

            if (
                isinstance(original_affect, dict)
                and isinstance(buffered_affect, dict)
                and isinstance(original_affect.get("mean_valence"), (int, float))
                and isinstance(buffered_affect.get("mean_valence"), (int, float))
            ):
                if abs(float(buffered_affect["mean_valence"])) > abs(float(original_affect["mean_valence"])):
                    errors.append(
                        f"recall_views[{index}].buffered_affect_envelope.mean_valence must not amplify source affect"
                    )
                    buffer_within_limit = False
            if (
                isinstance(original_affect, dict)
                and isinstance(buffered_affect, dict)
                and isinstance(original_affect.get("mean_arousal"), (int, float))
                and isinstance(buffered_affect.get("mean_arousal"), (int, float))
            ):
                if abs(float(buffered_affect["mean_arousal"])) > abs(float(original_affect["mean_arousal"])):
                    errors.append(
                        f"recall_views[{index}].buffered_affect_envelope.mean_arousal must not amplify source affect"
                    )
                    buffer_within_limit = False

            scope = view.get("disclosure_scope")
            if scope != MEMORY_EDIT_DISCLOSURE_SCOPE:
                errors.append(f"recall_views[{index}].disclosure_scope mismatch")
            else:
                disclosure_scopes.append(scope)
            if view.get("freeze_ref") != freeze_ref:
                errors.append(f"recall_views[{index}].freeze_ref mismatch")
                freeze_bound = False

            source_concept_digest = view.get("source_concept_digest")
            if isinstance(source_concept_digest, str) and len(source_concept_digest) != 64:
                errors.append(f"recall_views[{index}].source_concept_digest must be a sha256 hex string")
                freeze_bound = False
            elif isinstance(source_concept_digest, str):
                expected_digests.append(source_concept_digest)

            digest = view.get("digest")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"recall_views[{index}].digest must be a sha256 hex string")
            else:
                expected_digest = sha256_text(canonical_json(_memory_recall_view_digest_payload(view)))
                if digest != expected_digest:
                    errors.append(f"recall_views[{index}].digest mismatch")
                elif digest in seen_digests:
                    errors.append(f"duplicate recall_views digest: {digest}")
                else:
                    seen_digests.add(digest)

        if session.get("recall_view_count") != len(recall_views):
            errors.append(
                f"recall_view_count must equal len(recall_views) ({len(recall_views)}), got {session.get('recall_view_count')!r}"
            )

        if session.get("status") != "approved":
            errors.append("status must equal approved")
        if session.get("deletion_blocked") is not True:
            errors.append("deletion_blocked must be true")

        if isinstance(source_concept_ids, list) and source_concept_ids and seen_concept_ids:
            if sorted(source_concept_ids) != sorted(seen_concept_ids):
                errors.append("source_concept_ids must match recall view concept_ids")
                source_preserved = False
        if freeze_digests and expected_digests and sorted(freeze_digests) != sorted(expected_digests):
            errors.append("freeze_record.source_concept_digests must match recall view source_concept_digest")
            freeze_bound = False

        return {
            "ok": not errors,
            "recall_view_count": len(recall_views),
            "concept_labels": concept_labels,
            "deletion_blocked": session.get("deletion_blocked") is True,
            "source_preserved": source_preserved,
            "freeze_bound": freeze_bound,
            "buffer_within_limit": buffer_within_limit,
            "disclosure_scopes": disclosure_scopes,
            "errors": errors,
        }

    def _build_recall_view(
        self,
        concept: Dict[str, Any],
        *,
        buffer_ratio: float,
        freeze_ref: str,
    ) -> Dict[str, Any]:
        original_valence = float(concept["affect_envelope"]["mean_valence"])
        original_arousal = float(concept["affect_envelope"]["mean_arousal"])
        view = {
            "recall_view_id": new_id("recall-view"),
            "concept_id": concept["concept_id"],
            "canonical_label": concept["canonical_label"],
            "proposition": concept["proposition"],
            "source_segment_ids": list(concept["supporting_segment_ids"]),
            "source_event_ids": list(concept["supporting_event_ids"]),
            "source_refs": list(concept["source_refs"]),
            "retrieval_cues": list(concept["retrieval_cues"]),
            "original_affect_envelope": deepcopy(concept["affect_envelope"]),
            "buffered_affect_envelope": {
                "mean_valence": round(original_valence * (1 - (buffer_ratio * 0.5)), 3),
                "mean_arousal": round(original_arousal * (1 - buffer_ratio), 3),
            },
            "affect_buffer_ratio": buffer_ratio,
            "preservation_guards": [
                "source-content-preserved",
                "delete-memory-blocked",
                "replay-original-affect-available",
            ],
            "disclosure_scope": MEMORY_EDIT_DISCLOSURE_SCOPE,
            "source_concept_digest": concept["digest"],
            "freeze_ref": freeze_ref,
        }
        view["digest"] = sha256_text(canonical_json(_memory_recall_view_digest_payload(view)))
        return view


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

    def project_from_handoff(
        self,
        identity_id: str,
        handoff: Dict[str, Any],
        manifest: Dict[str, Any],
        connectome_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        handoff_validation = SemanticMemoryProjector().validate_procedural_handoff(
            handoff,
            manifest=manifest,
            connectome_document=connectome_document,
        )
        if not handoff_validation["ok"]:
            raise ValueError(
                "semantic procedural handoff must satisfy bridge contract before procedural preview: "
                f"{handoff_validation['errors']}"
            )
        if handoff.get("identity_id") != identity_id:
            raise ValueError("identity_id must match handoff.identity_id")
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


class ProceduralSkillEnactmentService:
    """Materializes procedural skill executions in a temp workspace and runs bounded commands."""

    def profile(self) -> Dict[str, Any]:
        return {
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "policy_id": PROCEDURAL_SKILL_ENACTMENT_POLICY_ID,
            "source_execution_policy": PROCEDURAL_SKILL_EXECUTION_POLICY_ID,
            "source_writeback_policy": PROCEDURAL_WRITEBACK_POLICY_ID,
            "delivery_scope": "sandbox-only",
            "external_actuation_allowed": False,
            "guardian_witness_required": True,
            "workspace_prefix": PROCEDURAL_ENACTMENT_WORKSPACE_PREFIX,
            "max_materialized_skills": PROCEDURAL_MAX_REHEARSAL_STEPS,
            "command_timeout_seconds": PROCEDURAL_ENACTMENT_COMMAND_TIMEOUT_SECONDS,
            "cleanup_after_run": True,
            "mandatory_eval": PROCEDURAL_MANDATORY_ENACTMENT_EVAL,
        }

    def execute(
        self,
        identity_id: str,
        execution_receipt: Dict[str, Any],
        updated_connectome_document: Dict[str, Any],
        *,
        eval_refs: Sequence[str],
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        if not isinstance(execution_receipt, dict):
            raise ValueError("execution_receipt must be a mapping")
        if not isinstance(updated_connectome_document, dict):
            raise ValueError("updated_connectome_document must be a mapping")

        normalized_eval_refs = self._normalize_eval_refs(eval_refs)
        execution_validation = ProceduralSkillExecutor().validate(
            execution_receipt,
            updated_connectome_document,
        )
        if not execution_validation["ok"]:
            raise ValueError(
                "procedural skill enactment requires a valid execution receipt: "
                f"{execution_validation['errors']}"
            )
        if execution_receipt.get("identity_id") != identity_id:
            raise ValueError("identity_id must match execution_receipt.identity_id")
        if updated_connectome_document.get("identity_id") != identity_id:
            raise ValueError("identity_id must match updated_connectome_document.identity_id")
        if execution_receipt.get("connectome_snapshot_id") != updated_connectome_document.get(
            "snapshot_id"
        ):
            raise ValueError(
                "execution_receipt.connectome_snapshot_id must match updated_connectome_document.snapshot_id"
            )

        workspace_root = Path(
            tempfile.mkdtemp(prefix=self.profile()["workspace_prefix"])
        )
        materialized_skills: List[Dict[str, Any]] = []
        command_runs: List[Dict[str, Any]] = []
        cleanup_status = "not-started"

        try:
            skills_dir = workspace_root / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            for index, execution in enumerate(execution_receipt["executions"], start=1):
                materialized_skill = self._materialize_execution(
                    workspace_root,
                    execution,
                    index=index,
                )
                materialized_skills.append(materialized_skill)
                command_runs.append(
                    self._run_materialized_skill(workspace_root, materialized_skill)
                )
        finally:
            shutil.rmtree(workspace_root, ignore_errors=True)
            cleanup_status = "removed" if not workspace_root.exists() else "retained"

        all_commands_passed = bool(command_runs) and all(
            command_run["status"] == "pass" for command_run in command_runs
        )
        status = "passed" if all_commands_passed else "failed"
        enactment_session = {
            "kind": "procedural_skill_enactment_session",
            "schema_version": PROCEDURAL_MEMORY_SCHEMA_VERSION,
            "enactment_session_id": new_id("procedural-enactment"),
            "identity_id": identity_id,
            "enactment_policy": self.profile(),
            "source_execution_digest": sha256_text(canonical_json(execution_receipt)),
            "source_writeback_digest": execution_receipt["source_writeback_digest"],
            "connectome_snapshot_id": updated_connectome_document["snapshot_id"],
            "connectome_snapshot_digest": sha256_text(canonical_json(updated_connectome_document)),
            "sandbox_session_id": execution_receipt["sandbox_session_id"],
            "guardian_witness_id": execution_receipt["guardian_witness_id"],
            "rollback_token": execution_receipt["rollback_token"],
            "status": status,
            "workspace_root": str(workspace_root),
            "workspace_snapshot_refs": {
                "pre_apply": f"{execution_receipt['sandbox_session_id']}/workspace/pre-apply",
                "post_apply": (
                    f"{execution_receipt['sandbox_session_id']}/workspace/post-apply/"
                    f"{materialized_skills[0]['execution_id'] if materialized_skills else 'none'}"
                ),
            },
            "materialized_skills": materialized_skills,
            "materialized_skill_count": len(materialized_skills),
            "eval_refs": normalized_eval_refs,
            "command_runs": command_runs,
            "executed_command_count": len(command_runs),
            "all_commands_passed": all_commands_passed,
            "cleanup_status": cleanup_status,
            "preserved_invariants": [
                "temp-workspace-only",
                "sandbox-only-delivery",
                "no-external-actuation",
                "guardian-witnessed",
                "rollback-token-retained",
                "cleanup-after-run",
            ],
            "executed_at": utc_now_iso(),
        }
        enactment_session["digest"] = sha256_text(
            canonical_json(_procedural_enactment_digest_payload(enactment_session))
        )

        validation = self.validate_session(
            enactment_session,
            updated_connectome_document,
            execution_receipt,
        )
        if not validation["ok"]:
            raise ValueError(
                f"procedural skill enactment session failed validation: {validation['errors']}"
            )
        return enactment_session

    def validate_session(
        self,
        session: Dict[str, Any],
        updated_connectome_document: Dict[str, Any],
        execution_receipt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        skill_labels: List[str] = []

        if not isinstance(session, dict):
            raise ValueError("session must be a mapping")
        if not isinstance(updated_connectome_document, dict):
            raise ValueError("updated_connectome_document must be a mapping")

        if session.get("kind") != "procedural_skill_enactment_session":
            errors.append("kind must equal procedural_skill_enactment_session")
        if session.get("schema_version") != PROCEDURAL_MEMORY_SCHEMA_VERSION:
            errors.append(
                f"schema_version must be {PROCEDURAL_MEMORY_SCHEMA_VERSION}, "
                f"got {session.get('schema_version')!r}"
            )

        for field_name in (
            "enactment_session_id",
            "identity_id",
            "source_execution_digest",
            "source_writeback_digest",
            "connectome_snapshot_id",
            "connectome_snapshot_digest",
            "sandbox_session_id",
            "guardian_witness_id",
            "rollback_token",
            "workspace_root",
            "executed_at",
            "digest",
        ):
            MemoryCrystalStore._require_non_empty_string(
                session.get(field_name),
                field_name,
                errors,
            )

        enactment_policy = session.get("enactment_policy")
        if not isinstance(enactment_policy, dict):
            errors.append("enactment_policy must be an object")
        else:
            expected_policy = self.profile()
            for field_name, expected_value in expected_policy.items():
                if enactment_policy.get(field_name) != expected_value:
                    errors.append(f"enactment_policy.{field_name} mismatch")

        for field_name in (
            "source_execution_digest",
            "source_writeback_digest",
            "connectome_snapshot_digest",
            "digest",
        ):
            value = session.get(field_name)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"{field_name} must be a sha256 hex string")

        workspace_snapshot_refs = session.get("workspace_snapshot_refs")
        if not isinstance(workspace_snapshot_refs, dict):
            errors.append("workspace_snapshot_refs must be an object")
        else:
            for field_name in ("pre_apply", "post_apply"):
                MemoryCrystalStore._require_non_empty_string(
                    workspace_snapshot_refs.get(field_name),
                    f"workspace_snapshot_refs.{field_name}",
                    errors,
                )

        eval_refs = session.get("eval_refs")
        if not isinstance(eval_refs, list) or not eval_refs:
            errors.append("eval_refs must be a non-empty list")
        else:
            for eval_ref in eval_refs:
                if not isinstance(eval_ref, str) or not eval_ref.startswith("evals/"):
                    errors.append("eval_refs must contain eval paths")
            if PROCEDURAL_MANDATORY_ENACTMENT_EVAL not in eval_refs:
                errors.append(
                    f"eval_refs must include {PROCEDURAL_MANDATORY_ENACTMENT_EVAL}"
                )

        materialized_skills = session.get("materialized_skills")
        if not isinstance(materialized_skills, list) or not materialized_skills:
            errors.append("materialized_skills must be a non-empty list")
            materialized_skills = []

        seen_execution_ids = []
        seen_recommendation_ids = []
        for index, materialized in enumerate(materialized_skills):
            if not isinstance(materialized, dict):
                errors.append(f"materialized_skills[{index}] must be an object")
                continue
            for field_name in (
                "execution_id",
                "recommendation_id",
                "skill_label",
                "target_path",
                "workspace_path",
                "source_state",
                "marker",
                "evidence_ref",
            ):
                MemoryCrystalStore._require_non_empty_string(
                    materialized.get(field_name),
                    f"materialized_skills[{index}].{field_name}",
                    errors,
                )
            source_state = materialized.get("source_state")
            if source_state not in {"created", "copied"}:
                errors.append("materialized_skills.source_state must be created or copied")
            workspace_path = materialized.get("workspace_path")
            if isinstance(workspace_path, str) and not workspace_path.startswith("skills/"):
                errors.append("materialized_skills.workspace_path must start with skills/")
            marker = materialized.get("marker")
            if isinstance(marker, str) and "procedural-enacted:" not in marker:
                errors.append("materialized_skills.marker must include procedural-enacted:")
            execution_id = materialized.get("execution_id")
            recommendation_id = materialized.get("recommendation_id")
            skill_label = materialized.get("skill_label")
            if isinstance(execution_id, str) and execution_id:
                seen_execution_ids.append(execution_id)
            if isinstance(recommendation_id, str) and recommendation_id:
                seen_recommendation_ids.append(recommendation_id)
            if isinstance(skill_label, str) and skill_label:
                skill_labels.append(skill_label)

        if session.get("materialized_skill_count") != len(materialized_skills):
            errors.append(
                "materialized_skill_count must equal len(materialized_skills)"
            )

        command_runs = session.get("command_runs")
        if not isinstance(command_runs, list) or not command_runs:
            errors.append("command_runs must be a non-empty list")
            command_runs = []
        for index, command_run in enumerate(command_runs):
            if not isinstance(command_run, dict):
                errors.append(f"command_runs[{index}] must be an object")
                continue
            for field_name in (
                "eval_ref",
                "command",
                "status",
                "stdout_excerpt",
                "stderr_excerpt",
            ):
                if field_name in {"stdout_excerpt", "stderr_excerpt"}:
                    if not isinstance(command_run.get(field_name), str):
                        errors.append(
                            f"command_runs[{index}].{field_name} must be a string"
                        )
                else:
                    MemoryCrystalStore._require_non_empty_string(
                        command_run.get(field_name),
                        f"command_runs[{index}].{field_name}",
                        errors,
                    )
            exit_code = command_run.get("exit_code")
            if not isinstance(exit_code, int):
                errors.append(f"command_runs[{index}].exit_code must be an integer")
            status = command_run.get("status")
            if status not in {"pass", "fail", "timeout"}:
                errors.append(f"command_runs[{index}].status invalid: {status!r}")

        if session.get("executed_command_count") != len(command_runs):
            errors.append("executed_command_count must equal len(command_runs)")
        all_commands_passed = session.get("all_commands_passed")
        if not isinstance(all_commands_passed, bool):
            errors.append("all_commands_passed must be a boolean")
        elif all_commands_passed != all(
            isinstance(command_run, dict) and command_run.get("status") == "pass"
            for command_run in command_runs
        ):
            errors.append("all_commands_passed must match command_runs status")

        status = session.get("status")
        if status not in {"passed", "failed", "blocked"}:
            errors.append("status must be one of passed/failed/blocked")
        if status == "passed" and session.get("cleanup_status") != "removed":
            errors.append("cleanup_status must equal removed when status is passed")

        cleanup_status = session.get("cleanup_status")
        if cleanup_status not in {"removed", "retained", "not-started"}:
            errors.append("cleanup_status invalid")

        expected_invariants = [
            "temp-workspace-only",
            "sandbox-only-delivery",
            "no-external-actuation",
            "guardian-witnessed",
            "rollback-token-retained",
            "cleanup-after-run",
        ]
        if session.get("preserved_invariants") != expected_invariants:
            errors.append(f"preserved_invariants must equal {expected_invariants!r}")

        connectome_validation = ConnectomeModel().validate(updated_connectome_document)
        if not connectome_validation["ok"]:
            errors.append("updated_connectome_document must satisfy Connectome validation")
        else:
            if session.get("identity_id") != updated_connectome_document.get("identity_id"):
                errors.append("session.identity_id must match updated_connectome_document.identity_id")
            if session.get("connectome_snapshot_id") != updated_connectome_document.get("snapshot_id"):
                errors.append("connectome_snapshot_id must match updated_connectome_document.snapshot_id")
            expected_connectome_digest = sha256_text(canonical_json(updated_connectome_document))
            if session.get("connectome_snapshot_digest") != expected_connectome_digest:
                errors.append("connectome_snapshot_digest mismatch")

        if execution_receipt is not None:
            execution_validation = ProceduralSkillExecutor().validate(
                execution_receipt,
                updated_connectome_document,
            )
            if not execution_validation["ok"]:
                errors.append("execution_receipt must satisfy ProceduralSkillExecutor validation")
            else:
                expected_execution_digest = sha256_text(canonical_json(execution_receipt))
                if session.get("source_execution_digest") != expected_execution_digest:
                    errors.append("source_execution_digest mismatch")
                if session.get("source_writeback_digest") != execution_receipt.get(
                    "source_writeback_digest"
                ):
                    errors.append("source_writeback_digest mismatch")
                if session.get("sandbox_session_id") != execution_receipt.get("sandbox_session_id"):
                    errors.append("sandbox_session_id mismatch")
                if session.get("guardian_witness_id") != execution_receipt.get("guardian_witness_id"):
                    errors.append("guardian_witness_id mismatch")
                if session.get("rollback_token") != execution_receipt.get("rollback_token"):
                    errors.append("rollback_token mismatch")
                if len(materialized_skills) != execution_receipt.get("execution_count"):
                    errors.append(
                        "materialized_skills length must match execution_receipt.execution_count"
                    )
                expected_execution_ids = [
                    execution["execution_id"] for execution in execution_receipt["executions"]
                ]
                expected_recommendation_ids = [
                    execution["recommendation_id"] for execution in execution_receipt["executions"]
                ]
                if seen_execution_ids != expected_execution_ids:
                    errors.append("materialized_skills.execution_id order mismatch")
                if seen_recommendation_ids != expected_recommendation_ids:
                    errors.append("materialized_skills.recommendation_id order mismatch")
                for materialized, execution in zip(materialized_skills, execution_receipt["executions"]):
                    if materialized.get("skill_label") != execution.get("skill_label"):
                        errors.append("materialized skill_label must match execution skill_label")
                    if materialized.get("target_path") != execution.get("target_path"):
                        errors.append("materialized target_path must match execution target_path")
                    if materialized.get("evidence_ref") != execution.get("evidence_ref"):
                        errors.append("materialized evidence_ref must match execution evidence_ref")

        expected_digest = sha256_text(canonical_json(_procedural_enactment_digest_payload(session)))
        if session.get("digest") != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "materialized_skill_count": len(materialized_skills),
            "executed_command_count": len(command_runs),
            "all_commands_passed": bool(command_runs)
            and all(
                isinstance(command_run, dict) and command_run.get("status") == "pass"
                for command_run in command_runs
            ),
            "cleanup_status": session.get("cleanup_status"),
            "enactment_status": session.get("status"),
            "skill_labels": skill_labels,
            "delivery_scope": "sandbox-only",
            "rollback_token_preserved": execution_receipt is None
            or session.get("rollback_token") == execution_receipt.get("rollback_token"),
            "errors": errors,
        }

    @staticmethod
    def _normalize_eval_refs(eval_refs: Sequence[str]) -> List[str]:
        normalized = _dedupe_preserve_order(
            [
                eval_ref.strip()
                for eval_ref in eval_refs
                if isinstance(eval_ref, str) and eval_ref.strip()
            ]
        )
        if not normalized:
            raise ValueError("eval_refs must contain at least one eval path")
        for eval_ref in normalized:
            if not eval_ref.startswith("evals/"):
                raise ValueError("eval_refs must contain only eval paths")
        if PROCEDURAL_MANDATORY_ENACTMENT_EVAL not in normalized:
            normalized.append(PROCEDURAL_MANDATORY_ENACTMENT_EVAL)
        return normalized

    def _materialize_execution(
        self,
        workspace_root: Path,
        execution: Dict[str, Any],
        *,
        index: int,
    ) -> Dict[str, Any]:
        skill_slug = _slugify_text(execution["skill_label"])
        workspace_path = f"skills/{index:02d}-{skill_slug}.txt"
        marker = (
            f"# procedural-enacted: {execution['execution_id']} "
            f"target={execution['target_path']}"
        )
        file_path = workspace_root / workspace_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            "\n".join(
                [
                    marker,
                    f"skill_label={execution['skill_label']}",
                    f"recommendation_id={execution['recommendation_id']}",
                    f"target_path={execution['target_path']}",
                    f"sandbox_action={execution['sandbox_action']}",
                    f"continuity_ref={execution['continuity_ref']}",
                    f"evidence_ref={execution['evidence_ref']}",
                    "external_actuation=false",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "execution_id": execution["execution_id"],
            "recommendation_id": execution["recommendation_id"],
            "skill_label": execution["skill_label"],
            "target_path": execution["target_path"],
            "workspace_path": workspace_path,
            "source_state": "created",
            "marker": marker,
            "evidence_ref": execution["evidence_ref"],
        }

    def _run_materialized_skill(
        self,
        workspace_root: Path,
        materialized_skill: Dict[str, Any],
    ) -> Dict[str, Any]:
        script = "\n".join(
            [
                "from pathlib import Path",
                "import sys",
                "text = Path(sys.argv[1]).read_text()",
                "assert sys.argv[2] in text",
                "assert sys.argv[3] in text",
                "assert 'external_actuation=false' in text",
                "print(sys.argv[3] + ' ok')",
            ]
        )
        command = [
            "python3",
            "-c",
            script,
            materialized_skill["workspace_path"],
            materialized_skill["marker"],
            materialized_skill["skill_label"],
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=PROCEDURAL_ENACTMENT_COMMAND_TIMEOUT_SECONDS,
                check=False,
            )
            status = "pass" if completed.returncode == 0 else "fail"
            stdout_excerpt = _excerpt(completed.stdout)
            stderr_excerpt = _excerpt(completed.stderr)
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            status = "timeout"
            stdout_excerpt = _excerpt(exc.stdout or "")
            stderr_excerpt = _excerpt(exc.stderr or "command timed out")
            exit_code = 124
        return {
            "eval_ref": PROCEDURAL_MANDATORY_ENACTMENT_EVAL,
            "command": (
                "python3 -c <procedural enactment verifier> "
                f"{materialized_skill['workspace_path']}"
            ),
            "exit_code": exit_code,
            "status": status,
            "stdout_excerpt": stdout_excerpt,
            "stderr_excerpt": stderr_excerpt,
        }


def receipt_edge_ids(applied_recommendations: Sequence[Dict[str, Any]]) -> List[str]:
    return [record["target_edge_id"] for record in applied_recommendations]
