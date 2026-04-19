"""Cross-layer cognitive audit loop for qualia, metacognition, and Council review."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

COGNITIVE_AUDIT_SCHEMA_VERSION = "1.0.0"
COGNITIVE_AUDIT_POLICY_ID = "cross-layer-cognitive-audit-v1"
COGNITIVE_AUDIT_ALLOWED_ACTIONS = {
    "record-and-monitor",
    "guardian-review",
    "contain-and-review",
}
COGNITIVE_AUDIT_ALLOWED_RISK_LEVELS = {"low", "medium", "high"}
COGNITIVE_AUDIT_ALLOWED_SESSION_MODES = {"standard", "expedited"}
COGNITIVE_AUDIT_ALLOWED_OUTCOMES = {
    "approved",
    "rejected",
    "vetoed",
    "deferred",
    "escalated",
}
COGNITIVE_AUDIT_ALLOWED_FOLLOW_UP_ACTIONS = {
    "continue-monitoring",
    "open-guardian-review",
    "activate-containment",
    "preserve-boundary",
    "schedule-standard-session",
    "escalate-to-human-governance",
}
COGNITIVE_AUDIT_MAX_TRIGGERS = 4
COGNITIVE_AUDIT_LUCIDITY_GUARD_THRESHOLD = 0.65
COGNITIVE_AUDIT_CONTINUITY_PRESSURE_THRESHOLD = 0.75


def _record_digest_payload(record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": record["schema_version"],
        "policy": record["policy"],
        "identity_id": record["identity_id"],
        "qualia_checkpoint_ref": record["qualia_checkpoint_ref"],
        "metacognition_report_ref": record["metacognition_report_ref"],
        "self_model_ref": record["self_model_ref"],
        "qualia_summary": record["qualia_summary"],
        "self_model_summary": record["self_model_summary"],
        "metacognition_summary": record["metacognition_summary"],
        "audit_triggers": record["audit_triggers"],
        "recommended_action": record["recommended_action"],
        "council_brief": record["council_brief"],
        "continuity_alignment": record["continuity_alignment"],
    }


def _resolution_digest_payload(resolution: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": resolution["schema_version"],
        "audit_ref": resolution["audit_ref"],
        "council_proposal_ref": resolution["council_proposal_ref"],
        "council_outcome": resolution["council_outcome"],
        "decision_mode": resolution["decision_mode"],
        "follow_up_action": resolution["follow_up_action"],
        "recommended_action": resolution["recommended_action"],
        "qualia_checkpoint_ref": resolution["qualia_checkpoint_ref"],
        "metacognition_report_ref": resolution["metacognition_report_ref"],
        "continuity_alignment": resolution["continuity_alignment"],
    }


class CognitiveAuditService:
    """Deterministic cross-layer audit builder for bounded cognitive incidents."""

    @staticmethod
    def reference_policy() -> Dict[str, Any]:
        return {
            "schema_version": COGNITIVE_AUDIT_SCHEMA_VERSION,
            "policy_id": COGNITIVE_AUDIT_POLICY_ID,
            "allowed_layers": ["L2", "L3", "L4"],
            "qualia_checkpoint_category": "qualia-checkpoint",
            "audit_category": "cognitive-audit",
            "divergence_alert_threshold": 0.35,
            "lucidity_guard_threshold": COGNITIVE_AUDIT_LUCIDITY_GUARD_THRESHOLD,
            "continuity_pressure_threshold": COGNITIVE_AUDIT_CONTINUITY_PRESSURE_THRESHOLD,
            "max_trigger_count": COGNITIVE_AUDIT_MAX_TRIGGERS,
        }

    @staticmethod
    def _self_model_ref(observation: Mapping[str, Any]) -> str:
        return "self-model-observation://sha256/" + sha256_text(canonical_json(dict(observation)))

    def _derive_triggers(
        self,
        qualia_tick: Mapping[str, Any],
        self_model_observation: Mapping[str, Any],
        report: Mapping[str, Any],
    ) -> List[str]:
        triggers: List[str] = []
        if self_model_observation.get("abrupt_change"):
            triggers.append("abrupt-change")
        affect_guard = report.get("source_tick", {}).get("affect_guard")
        if affect_guard == "observe":
            triggers.append("observe-guard")
        elif affect_guard == "sandbox-notify":
            triggers.append("sandbox-notify")
        if float(qualia_tick.get("lucidity", 1.0)) < COGNITIVE_AUDIT_LUCIDITY_GUARD_THRESHOLD:
            triggers.append("low-lucidity")
        if float(report.get("source_tick", {}).get("continuity_pressure", 0.0)) >= (
            COGNITIVE_AUDIT_CONTINUITY_PRESSURE_THRESHOLD
        ):
            triggers.append("high-continuity-pressure")
        return triggers[:COGNITIVE_AUDIT_MAX_TRIGGERS]

    @staticmethod
    def _recommended_action(triggers: List[str], report: Mapping[str, Any]) -> str:
        if "sandbox-notify" in triggers or report.get("risk_posture") == "containment":
            return "contain-and-review"
        if triggers:
            return "guardian-review"
        return "record-and-monitor"

    @staticmethod
    def _risk_level(triggers: List[str], recommended_action: str) -> str:
        if recommended_action == "contain-and-review" or "abrupt-change" in triggers:
            return "high"
        if recommended_action == "guardian-review":
            return "medium"
        return "low"

    @staticmethod
    def _session_mode(recommended_action: str) -> str:
        if recommended_action == "contain-and-review":
            return "expedited"
        return "standard"

    @staticmethod
    def _requested_action(recommended_action: str) -> str:
        mapping = {
            "record-and-monitor": "record-cognitive-state",
            "guardian-review": "open-guardian-review",
            "contain-and-review": "activate-cognitive-containment",
        }
        return mapping[recommended_action]

    def create_record(
        self,
        *,
        identity_id: str,
        qualia_tick: Mapping[str, Any],
        self_model_observation: Mapping[str, Any],
        metacognition_report: Mapping[str, Any],
        qualia_checkpoint_ref: str,
    ) -> Dict[str, Any]:
        triggers = self._derive_triggers(qualia_tick, self_model_observation, metacognition_report)
        recommended_action = self._recommended_action(triggers, metacognition_report)
        risk_level = self._risk_level(triggers, recommended_action)
        session_mode = self._session_mode(recommended_action)
        continuity_alignment = {
            "identity_matches": (
                identity_id
                == self_model_observation.get("snapshot", {}).get("identity_id")
                == metacognition_report.get("source_tick", {}).get("identity_id")
            ),
            "qualia_tick_matches_report": (
                qualia_tick.get("tick_id") == metacognition_report.get("source_tick", {}).get("tick_id")
                and qualia_tick.get("attention_target")
                == metacognition_report.get("source_tick", {}).get("attention_target")
            ),
            "guard_consistent": bool(
                metacognition_report.get("continuity_guard", {}).get("guard_aligned")
            ),
            "threshold_exceeded": bool(
                self_model_observation.get("abrupt_change")
                or float(self_model_observation.get("divergence", 0.0))
                >= float(self_model_observation.get("threshold", 0.0))
                or float(qualia_tick.get("lucidity", 1.0)) < COGNITIVE_AUDIT_LUCIDITY_GUARD_THRESHOLD
                or float(metacognition_report.get("source_tick", {}).get("continuity_pressure", 0.0))
                >= COGNITIVE_AUDIT_CONTINUITY_PRESSURE_THRESHOLD
            ),
        }
        record = {
            "kind": "cognitive_audit_record",
            "schema_version": COGNITIVE_AUDIT_SCHEMA_VERSION,
            "audit_id": new_id("cognitive-audit"),
            "created_at": utc_now_iso(),
            "policy": self.reference_policy(),
            "identity_id": identity_id,
            "qualia_checkpoint_ref": qualia_checkpoint_ref,
            "metacognition_report_ref": metacognition_report["report_id"],
            "self_model_ref": self._self_model_ref(self_model_observation),
            "qualia_summary": {
                "tick_id": qualia_tick["tick_id"],
                "summary": qualia_tick["summary"],
                "attention_target": qualia_tick["attention_target"],
                "self_awareness": qualia_tick["self_awareness"],
                "lucidity": qualia_tick["lucidity"],
                "valence": qualia_tick["valence"],
                "arousal": qualia_tick["arousal"],
                "clarity": qualia_tick["clarity"],
            },
            "self_model_summary": {
                "abrupt_change": bool(self_model_observation["abrupt_change"]),
                "divergence": self_model_observation["divergence"],
                "threshold": self_model_observation["threshold"],
                "active_values": self_model_observation["snapshot"]["values"][:3],
                "active_goals": self_model_observation["snapshot"]["goals"][:3],
                "top_traits": [
                    {"trait": key, "weight": value}
                    for key, value in sorted(
                        self_model_observation["snapshot"]["traits"].items(),
                        key=lambda item: (-item[1], item[0]),
                    )[:3]
                ],
            },
            "metacognition_summary": {
                "reflection_mode": metacognition_report["reflection_mode"],
                "escalation_target": metacognition_report["escalation_target"],
                "risk_posture": metacognition_report["risk_posture"],
                "degraded": bool(metacognition_report["degraded"]),
                "continuity_guard_aligned": bool(
                    metacognition_report["continuity_guard"]["guard_aligned"]
                ),
                "coherence_score": metacognition_report["coherence_score"],
            },
            "audit_triggers": triggers,
            "recommended_action": recommended_action,
            "council_brief": {
                "title": "Cognitive state audit review",
                "requested_action": self._requested_action(recommended_action),
                "rationale": (
                    "qualia / self-model / metacognition の cross-layer evidence を"
                    " bounded Council review に束ねる"
                ),
                "risk_level": risk_level,
                "session_mode": session_mode,
            },
            "continuity_alignment": continuity_alignment,
        }
        record["digest"] = sha256_text(canonical_json(_record_digest_payload(record)))
        return record

    def validate_record(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        triggers = record.get("audit_triggers", [])
        recommended_action = record.get("recommended_action")
        council_brief = record.get("council_brief", {})
        continuity_alignment = record.get("continuity_alignment", {})

        if record.get("kind") != "cognitive_audit_record":
            errors.append("kind must equal cognitive_audit_record")
        if record.get("schema_version") != COGNITIVE_AUDIT_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if record.get("policy", {}).get("policy_id") != COGNITIVE_AUDIT_POLICY_ID:
            errors.append("policy.policy_id mismatch")
        if not isinstance(triggers, list) or len(triggers) > COGNITIVE_AUDIT_MAX_TRIGGERS:
            errors.append("audit_triggers exceeds max_trigger_count")
        if recommended_action not in COGNITIVE_AUDIT_ALLOWED_ACTIONS:
            errors.append("recommended_action invalid")
        if council_brief.get("risk_level") not in COGNITIVE_AUDIT_ALLOWED_RISK_LEVELS:
            errors.append("council_brief.risk_level invalid")
        if council_brief.get("session_mode") not in COGNITIVE_AUDIT_ALLOWED_SESSION_MODES:
            errors.append("council_brief.session_mode invalid")
        if recommended_action == "contain-and-review" and council_brief.get("session_mode") != "expedited":
            errors.append("contain-and-review must use expedited session")
        if recommended_action != "contain-and-review" and council_brief.get("session_mode") != "standard":
            errors.append("non-containment audit must use standard session")
        if continuity_alignment.get("identity_matches") is not True:
            errors.append("continuity_alignment.identity_matches must be true")
        if continuity_alignment.get("qualia_tick_matches_report") is not True:
            errors.append("continuity_alignment.qualia_tick_matches_report must be true")
        if continuity_alignment.get("guard_consistent") is not True:
            errors.append("continuity_alignment.guard_consistent must be true")
        expected_digest = sha256_text(canonical_json(_record_digest_payload(record))) if not errors else None
        if expected_digest is not None and record.get("digest") != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "recommended_action": recommended_action,
            "risk_level": council_brief.get("risk_level"),
            "session_mode": council_brief.get("session_mode"),
            "trigger_count": len(triggers) if isinstance(triggers, list) else 0,
            "errors": errors,
        }

    def resolve(
        self,
        record: Mapping[str, Any],
        *,
        council_proposal_ref: str,
        council_decision: Mapping[str, Any],
    ) -> Dict[str, Any]:
        outcome = str(council_decision.get("outcome"))
        recommended_action = str(record.get("recommended_action"))
        if outcome == "approved":
            if recommended_action == "contain-and-review":
                follow_up_action = "activate-containment"
            elif recommended_action == "guardian-review":
                follow_up_action = "open-guardian-review"
            else:
                follow_up_action = "continue-monitoring"
        elif outcome in {"rejected", "vetoed"}:
            follow_up_action = "preserve-boundary"
        elif outcome == "deferred":
            follow_up_action = "schedule-standard-session"
        else:
            follow_up_action = "escalate-to-human-governance"

        resolution = {
            "kind": "cognitive_audit_resolution",
            "schema_version": COGNITIVE_AUDIT_SCHEMA_VERSION,
            "resolution_id": new_id("cognitive-audit-resolution"),
            "recorded_at": utc_now_iso(),
            "audit_ref": record["audit_id"],
            "council_proposal_ref": council_proposal_ref,
            "council_outcome": outcome,
            "decision_mode": council_decision["decision_mode"],
            "follow_up_action": follow_up_action,
            "recommended_action": recommended_action,
            "qualia_checkpoint_ref": record["qualia_checkpoint_ref"],
            "metacognition_report_ref": record["metacognition_report_ref"],
            "continuity_alignment": {
                "recommended_action_matches_outcome": (
                    (recommended_action == "record-and-monitor" and follow_up_action == "continue-monitoring")
                    or (recommended_action == "guardian-review" and follow_up_action == "open-guardian-review")
                    or (recommended_action == "contain-and-review" and follow_up_action == "activate-containment")
                    or outcome in {"rejected", "vetoed", "deferred", "escalated"}
                ),
                "continuity_guard_preserved": bool(record["continuity_alignment"]["guard_consistent"]),
                "containment_required": recommended_action == "contain-and-review",
            },
        }
        resolution["digest"] = sha256_text(canonical_json(_resolution_digest_payload(resolution)))
        return resolution

    def validate_resolution(self, resolution: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        outcome = resolution.get("council_outcome")
        follow_up_action = resolution.get("follow_up_action")

        if resolution.get("kind") != "cognitive_audit_resolution":
            errors.append("kind must equal cognitive_audit_resolution")
        if resolution.get("schema_version") != COGNITIVE_AUDIT_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if outcome not in COGNITIVE_AUDIT_ALLOWED_OUTCOMES:
            errors.append("council_outcome invalid")
        if follow_up_action not in COGNITIVE_AUDIT_ALLOWED_FOLLOW_UP_ACTIONS:
            errors.append("follow_up_action invalid")
        if resolution.get("continuity_alignment", {}).get("continuity_guard_preserved") is not True:
            errors.append("continuity_alignment.continuity_guard_preserved must be true")
        expected_digest = sha256_text(canonical_json(_resolution_digest_payload(resolution))) if not errors else None
        if expected_digest is not None and resolution.get("digest") != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "council_outcome": outcome,
            "follow_up_action": follow_up_action,
            "containment_required": resolution.get("continuity_alignment", {}).get(
                "containment_required",
                False,
            ),
            "errors": errors,
        }
