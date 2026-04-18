"""Biological-Digital Bridge reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Sequence

from ..common import new_id, utc_now_iso

BDB_SCHEMA_VERSION = "1.0"
BDB_CODEC_ID = "analog-spike-event-v0"
BDB_ACTIVE_STATE = "bio-digital-active"
BDB_FALLBACK_STATE = "bio-autonomous-fallback"
BDB_LATENCY_BUDGET_MS = 5.0
BDB_FAILOVER_BUDGET_MS = 1.0
BDB_RATIO_STEP = 0.05
DEFAULT_BIO_SIGNAL_CHANNELS = (
    "motor_cortex",
    "somatic_feedback",
    "autonomic_state",
)
DEFAULT_NEUROMODULATOR_CHANNELS = (
    "acetylcholine",
    "dopamine",
    "serotonin",
    "norepinephrine",
)
REQUIRED_STAGE_LATENCIES = (
    "sensor_array",
    "signal_conditioner",
    "bidirectional_codec",
    "digital_equivalent",
    "stim_driver",
)


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


class BiologicalDigitalBridge:
    """Deterministic L6 bridge model for bounded viability checks."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": BDB_SCHEMA_VERSION,
            "codec_id": BDB_CODEC_ID,
            "latency_budget_ms": BDB_LATENCY_BUDGET_MS,
            "failover_budget_ms": BDB_FAILOVER_BUDGET_MS,
            "ratio_step": BDB_RATIO_STEP,
            "bio_signal_channels": list(DEFAULT_BIO_SIGNAL_CHANNELS),
            "neuromodulator_channels": list(DEFAULT_NEUROMODULATOR_CHANNELS),
            "neuromodulator_mode": "coarse-proxy",
            "continuity_granularity": "per-cycle+state-change",
            "fallback_mode": BDB_FALLBACK_STATE,
        }

    def open_session(
        self,
        identity_id: str,
        replacement_ratio: float = 0.35,
        bio_signal_channels: Sequence[str] = DEFAULT_BIO_SIGNAL_CHANNELS,
        neuromodulator_channels: Sequence[str] = DEFAULT_NEUROMODULATOR_CHANNELS,
    ) -> Dict[str, Any]:
        self._require_non_empty_string(identity_id, "identity_id")
        ratio = self._normalize_ratio(replacement_ratio)
        signal_channels = self._normalize_string_list(bio_signal_channels, "bio_signal_channels")
        modulator_channels = self._normalize_string_list(
            neuromodulator_channels,
            "neuromodulator_channels",
        )
        session_id = new_id("bdb")
        timestamp = utc_now_iso()
        session = {
            "schema_version": BDB_SCHEMA_VERSION,
            "session_id": session_id,
            "identity_id": identity_id,
            "opened_at": timestamp,
            "last_transition_at": timestamp,
            "bridge_state": BDB_ACTIVE_STATE,
            "requested_replacement_ratio": ratio,
            "effective_replacement_ratio": ratio,
            "latency_budget_ms": BDB_LATENCY_BUDGET_MS,
            "failover_budget_ms": BDB_FAILOVER_BUDGET_MS,
            "bio_signal_channels": signal_channels,
            "neuromodulator_channels": modulator_channels,
            "codec": {
                "codec_id": BDB_CODEC_ID,
                "conditioning_profile": "bandpass-300-3000hz+artifact-clamp-v1",
                "event_resolution_bits": 12,
                "clock_domain": "shared-monotonic-ms",
                "neuromodulator_mode": "coarse-proxy",
            },
            "continuity": {
                "ledger_required": True,
                "recording_granularity": "per-cycle+state-change",
                "last_event_refs": [],
            },
            "fallback_policy": {
                "mode": BDB_FALLBACK_STATE,
                "bio_autonomy_required": True,
                "stim_driver_default": "zero-output",
                "stim_output_enabled": True,
                "max_failover_ms": BDB_FAILOVER_BUDGET_MS,
                "last_reason": "",
                "last_failover_ms": 0.0,
            },
            "reversibility": {
                "reversible": True,
                "ratio_step": BDB_RATIO_STEP,
                "min_ratio": 0.0,
                "max_ratio": 1.0,
                "ratio_history": [ratio],
                "last_direction": "initialize",
            },
            "latest_cycle": None,
        }
        self._append_event_ref(session, f"ledger://bdb-session/{session_id}")
        self.sessions[session_id] = session
        return deepcopy(session)

    def transduce_cycle(
        self,
        session_id: str,
        spike_channels: Sequence[str],
        neuromodulators: Dict[str, float],
        stimulus_targets: Sequence[str],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["bridge_state"] != BDB_ACTIVE_STATE:
            raise ValueError("cannot transduce cycle while bridge is in fallback")

        channels = self._normalize_string_list(spike_channels, "spike_channels")
        targets = self._normalize_string_list(stimulus_targets, "stimulus_targets")
        normalized_modulators = self._normalize_neuromodulators(neuromodulators)

        stage_latencies = {
            "sensor_array": round(0.9 + 0.1 * max(0, len(channels) - 1), 3),
            "signal_conditioner": 0.55,
            "bidirectional_codec": 0.85,
            "digital_equivalent": round(0.7 + 0.8 * session["effective_replacement_ratio"], 3),
            "stim_driver": 0.45 if targets else 0.0,
        }
        roundtrip_latency = round(sum(stage_latencies.values()), 3)
        cycle_id = new_id("bdb-cycle")
        event_ref = f"ledger://bdb-cycle/{cycle_id}"
        cycle = {
            "schema_version": BDB_SCHEMA_VERSION,
            "cycle_id": cycle_id,
            "recorded_at": utc_now_iso(),
            "spike_channels": channels,
            "neuromodulators": normalized_modulators,
            "stimulus_targets": targets,
            "stage_latencies_ms": stage_latencies,
            "roundtrip_latency_ms": roundtrip_latency,
            "within_budget": roundtrip_latency <= session["latency_budget_ms"],
            "digital_state": {
                "bridge_state": session["bridge_state"],
                "effective_replacement_ratio": session["effective_replacement_ratio"],
            },
            "continuity_event_ref": event_ref,
        }
        session["latest_cycle"] = cycle
        session["last_transition_at"] = cycle["recorded_at"]
        self._append_event_ref(session, event_ref)
        return deepcopy(cycle)

    def adjust_replacement_ratio(
        self,
        session_id: str,
        new_ratio: float,
        rationale: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["bridge_state"] != BDB_ACTIVE_STATE:
            raise ValueError("cannot adjust replacement ratio while bridge is in fallback")

        self._require_non_empty_string(rationale, "rationale")
        normalized_ratio = self._normalize_ratio(new_ratio)
        previous_ratio = session["requested_replacement_ratio"]
        if normalized_ratio == previous_ratio:
            raise ValueError("new_ratio must differ from the current replacement ratio")

        direction = "increase" if normalized_ratio > previous_ratio else "decrease"
        recorded_at = utc_now_iso()
        event_ref = f"ledger://bdb-ratio/{new_id('bdb-ratio')}"
        session["requested_replacement_ratio"] = normalized_ratio
        session["effective_replacement_ratio"] = normalized_ratio
        session["last_transition_at"] = recorded_at
        session["reversibility"]["ratio_history"].append(normalized_ratio)
        session["reversibility"]["last_direction"] = direction
        self._append_event_ref(session, event_ref)
        return {
            "session_id": session_id,
            "recorded_at": recorded_at,
            "old_ratio": previous_ratio,
            "new_ratio": normalized_ratio,
            "direction": direction,
            "rationale": rationale,
            "continuity_event_ref": event_ref,
        }

    def fail_safe_fallback(self, session_id: str, reason: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        self._require_non_empty_string(reason, "reason")

        failover_latency_ms = 0.7
        recorded_at = utc_now_iso()
        event_ref = f"ledger://bdb-fallback/{new_id('bdb-fallback')}"
        history = session["reversibility"]["ratio_history"]
        if not history or history[-1] != 0.0:
            history.append(0.0)

        session["bridge_state"] = BDB_FALLBACK_STATE
        session["effective_replacement_ratio"] = 0.0
        session["last_transition_at"] = recorded_at
        session["fallback_policy"]["stim_output_enabled"] = False
        session["fallback_policy"]["last_reason"] = reason
        session["fallback_policy"]["last_failover_ms"] = failover_latency_ms
        session["reversibility"]["last_direction"] = "decrease"
        self._append_event_ref(session, event_ref)
        return {
            "session_id": session_id,
            "recorded_at": recorded_at,
            "status": BDB_FALLBACK_STATE,
            "reason": reason,
            "failover_latency_ms": failover_latency_ms,
            "bio_autonomy_retained": True,
            "stim_output_enabled": False,
            "continuity_event_ref": event_ref,
        }

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_session(session_id))

    def validate_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(session, dict):
            raise ValueError("session must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(session.get("session_id"), "session_id", errors)
        self._check_non_empty_string(session.get("identity_id"), "identity_id", errors)
        self._check_non_empty_string(session.get("opened_at"), "opened_at", errors)
        bridge_state = session.get("bridge_state")
        if bridge_state not in {BDB_ACTIVE_STATE, BDB_FALLBACK_STATE}:
            errors.append(f"bridge_state must be one of {[BDB_ACTIVE_STATE, BDB_FALLBACK_STATE]}")

        if session.get("schema_version") != BDB_SCHEMA_VERSION:
            errors.append(f"schema_version must be {BDB_SCHEMA_VERSION}")

        requested_ratio = self._check_ratio_field(
            session.get("requested_replacement_ratio"),
            "requested_replacement_ratio",
            errors,
        )
        effective_ratio = self._check_ratio_field(
            session.get("effective_replacement_ratio"),
            "effective_replacement_ratio",
            errors,
        )
        if (
            requested_ratio is not None
            and effective_ratio is not None
            and bridge_state == BDB_ACTIVE_STATE
            and requested_ratio != effective_ratio
        ):
            errors.append("active bridge must keep requested/effective replacement ratios equal")
        if bridge_state == BDB_FALLBACK_STATE and effective_ratio != 0.0:
            errors.append("fallback bridge must force effective_replacement_ratio to 0.0")

        bio_signal_channels = session.get("bio_signal_channels")
        if not isinstance(bio_signal_channels, list) or not bio_signal_channels:
            errors.append("bio_signal_channels must be a non-empty list")
        neuromodulator_channels = session.get("neuromodulator_channels")
        if not isinstance(neuromodulator_channels, list) or not neuromodulator_channels:
            errors.append("neuromodulator_channels must be a non-empty list")

        fallback_policy = session.get("fallback_policy")
        if not isinstance(fallback_policy, dict):
            errors.append("fallback_policy must be an object")
        else:
            if fallback_policy.get("mode") != BDB_FALLBACK_STATE:
                errors.append(f"fallback_policy.mode must be {BDB_FALLBACK_STATE}")
            if fallback_policy.get("bio_autonomy_required") is not True:
                errors.append("fallback_policy.bio_autonomy_required must be true")
            if fallback_policy.get("max_failover_ms") != BDB_FAILOVER_BUDGET_MS:
                errors.append("fallback_policy.max_failover_ms mismatch")
            if bridge_state == BDB_FALLBACK_STATE and fallback_policy.get("stim_output_enabled") is not False:
                errors.append("fallback bridge must disable stim_output_enabled")

        continuity = session.get("continuity")
        if not isinstance(continuity, dict):
            errors.append("continuity must be an object")
        else:
            if continuity.get("ledger_required") is not True:
                errors.append("continuity.ledger_required must be true")
            event_refs = continuity.get("last_event_refs")
            if not isinstance(event_refs, list) or not event_refs:
                errors.append("continuity.last_event_refs must be a non-empty list")

        reversibility = session.get("reversibility")
        ratio_history: List[float] = []
        has_increase = False
        has_decrease = False
        if not isinstance(reversibility, dict):
            errors.append("reversibility must be an object")
        else:
            if reversibility.get("reversible") is not True:
                errors.append("reversibility.reversible must be true")
            if reversibility.get("ratio_step") != BDB_RATIO_STEP:
                errors.append("reversibility.ratio_step mismatch")
            history = reversibility.get("ratio_history")
            if not isinstance(history, list) or not history:
                errors.append("reversibility.ratio_history must be a non-empty list")
            else:
                ratio_history = history
                for index, ratio in enumerate(history):
                    normalized = self._check_ratio_field(
                        ratio,
                        f"reversibility.ratio_history[{index}]",
                        errors,
                    )
                    if normalized is not None and ratio != normalized:
                        errors.append(
                            f"reversibility.ratio_history[{index}] must align to {BDB_RATIO_STEP:.2f} steps"
                        )
                deltas = [history[index + 1] - history[index] for index in range(len(history) - 1)]
                has_increase = any(delta > 0 for delta in deltas)
                has_decrease = any(delta < 0 for delta in deltas)

        latest_cycle = session.get("latest_cycle")
        latency_within_budget = False
        max_roundtrip_latency_ms = 0.0
        if latest_cycle is not None:
            if not isinstance(latest_cycle, dict):
                errors.append("latest_cycle must be an object or null")
            else:
                cycle_validation = self._validate_cycle(latest_cycle, session["latency_budget_ms"])
                errors.extend(cycle_validation["errors"])
                latency_within_budget = cycle_validation["within_budget"]
                max_roundtrip_latency_ms = cycle_validation["roundtrip_latency_ms"]

        return {
            "ok": not errors,
            "errors": errors,
            "bridge_state": bridge_state,
            "latency_within_budget": latency_within_budget,
            "max_roundtrip_latency_ms": max_roundtrip_latency_ms,
            "reversibility_verified": has_increase and has_decrease,
            "bio_autonomy_retained": bridge_state != BDB_FALLBACK_STATE or effective_ratio == 0.0,
            "replacement_ratio_history": ratio_history,
        }

    def _validate_cycle(self, cycle: Dict[str, Any], latency_budget_ms: float) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_non_empty_string(cycle.get("cycle_id"), "latest_cycle.cycle_id", errors)
        self._check_non_empty_string(cycle.get("recorded_at"), "latest_cycle.recorded_at", errors)
        if cycle.get("schema_version") != BDB_SCHEMA_VERSION:
            errors.append(f"latest_cycle.schema_version must be {BDB_SCHEMA_VERSION}")

        spike_channels = cycle.get("spike_channels")
        if not isinstance(spike_channels, list) or not spike_channels:
            errors.append("latest_cycle.spike_channels must be a non-empty list")
        stimulus_targets = cycle.get("stimulus_targets")
        if not isinstance(stimulus_targets, list) or not stimulus_targets:
            errors.append("latest_cycle.stimulus_targets must be a non-empty list")

        neuromodulators = cycle.get("neuromodulators")
        if not isinstance(neuromodulators, dict) or not neuromodulators:
            errors.append("latest_cycle.neuromodulators must be a non-empty object")

        stage_latencies = cycle.get("stage_latencies_ms")
        recomputed_latency = 0.0
        if not isinstance(stage_latencies, dict):
            errors.append("latest_cycle.stage_latencies_ms must be an object")
        else:
            for key in REQUIRED_STAGE_LATENCIES:
                value = stage_latencies.get(key)
                if not isinstance(value, (int, float)) or value < 0:
                    errors.append(f"latest_cycle.stage_latencies_ms.{key} must be >= 0")
                else:
                    recomputed_latency += float(value)
            recomputed_latency = round(recomputed_latency, 3)

        roundtrip_latency_ms = cycle.get("roundtrip_latency_ms")
        if not isinstance(roundtrip_latency_ms, (int, float)) or roundtrip_latency_ms < 0:
            errors.append("latest_cycle.roundtrip_latency_ms must be >= 0")
            roundtrip_latency_ms = 0.0
        elif stage_latencies and round(roundtrip_latency_ms, 3) != recomputed_latency:
            errors.append("latest_cycle.roundtrip_latency_ms must equal the sum of stage latencies")

        within_budget = cycle.get("within_budget")
        if not isinstance(within_budget, bool):
            errors.append("latest_cycle.within_budget must be a boolean")
            within_budget = False
        elif within_budget != (roundtrip_latency_ms <= latency_budget_ms):
            errors.append("latest_cycle.within_budget does not match roundtrip latency budget check")

        digital_state = cycle.get("digital_state")
        if not isinstance(digital_state, dict):
            errors.append("latest_cycle.digital_state must be an object")
        else:
            if digital_state.get("bridge_state") not in {BDB_ACTIVE_STATE, BDB_FALLBACK_STATE}:
                errors.append("latest_cycle.digital_state.bridge_state is invalid")
            self._check_ratio_field(
                digital_state.get("effective_replacement_ratio"),
                "latest_cycle.digital_state.effective_replacement_ratio",
                errors,
            )

        self._check_non_empty_string(
            cycle.get("continuity_event_ref"),
            "latest_cycle.continuity_event_ref",
            errors,
        )
        return {
            "errors": errors,
            "within_budget": bool(within_budget),
            "roundtrip_latency_ms": float(roundtrip_latency_ms),
        }

    def _append_event_ref(self, session: Dict[str, Any], event_ref: str) -> None:
        refs = session["continuity"]["last_event_refs"]
        refs.append(event_ref)
        if len(refs) > 6:
            del refs[:-6]

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"unknown BDB session: {session_id}")
        return session

    def _normalize_neuromodulators(self, neuromodulators: Dict[str, float]) -> Dict[str, float]:
        if not isinstance(neuromodulators, dict) or not neuromodulators:
            raise ValueError("neuromodulators must be a non-empty mapping")
        normalized: Dict[str, float] = {}
        for channel, value in neuromodulators.items():
            if channel not in DEFAULT_NEUROMODULATOR_CHANNELS:
                raise ValueError(f"unsupported neuromodulator channel: {channel}")
            if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError("neuromodulator values must be numbers within [0.0, 1.0]")
            normalized[channel] = round(float(value), 3)
        return normalized

    def _normalize_string_list(self, values: Sequence[str], field_name: str) -> List[str]:
        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError(f"{field_name} must be a non-empty sequence")
        normalized = []
        for value in values:
            self._require_non_empty_string(value, field_name)
            normalized.append(str(value))
        return _dedupe_preserve_order(normalized)

    def _normalize_ratio(self, value: float) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("replacement ratio must be numeric")
        numeric = round(float(value), 2)
        if not 0.0 <= numeric <= 1.0:
            raise ValueError("replacement ratio must be within [0.0, 1.0]")
        scaled = round(numeric / BDB_RATIO_STEP)
        normalized = round(scaled * BDB_RATIO_STEP, 2)
        if abs(normalized - numeric) > 1e-9:
            raise ValueError(f"replacement ratio must align to {BDB_RATIO_STEP:.2f} steps")
        return normalized

    def _check_ratio_field(self, value: Any, field_name: str, errors: List[str]) -> float | None:
        try:
            return self._normalize_ratio(value)
        except ValueError as exc:
            errors.append(f"{field_name}: {exc}")
            return None

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")
