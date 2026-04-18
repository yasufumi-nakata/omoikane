"""MemoryCrystal compaction reference model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

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
        return [
            asdict(
                EpisodicEvent(
                    event_id="episode-0001",
                    occurred_at="2026-04-18T00:00:00+00:00",
                    summary="Council review で traceability 強化案を採択した",
                    tags=["council-review", "traceability", "safety"],
                    salience=0.91,
                    valence=0.24,
                    arousal=0.43,
                    source_refs=[
                        "ledger://proposal/traceability-0001",
                        "qualia://slice/council-focus-0001",
                    ],
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
                )
            ),
            asdict(
                EpisodicEvent(
                    event_id="episode-0005",
                    occurred_at="2026-04-18T00:11:00+00:00",
                    summary="Mirror 側の hash 照合が primary と一致することを確認した",
                    tags=["migration-check", "replication", "continuity"],
                    salience=0.76,
                    valence=0.05,
                    arousal=0.29,
                    source_refs=[
                        "mirror://hash/primary-0001",
                        "mirror://hash/mirror-0001",
                    ],
                )
            ),
        ]

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
