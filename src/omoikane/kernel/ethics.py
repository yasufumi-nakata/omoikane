"""Deterministic ethics enforcement for the reference runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


@dataclass
class ActionRequest:
    """Action being checked by the ethics layer."""

    action_type: str
    target: str
    actor: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EthicsDecision:
    """Decision emitted by the ethics layer."""

    status: str
    reasons: List[str]
    rule_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EthicsRule:
    """Serializable deterministic rule tree."""

    rule_id: str
    title: str
    summary: str
    outcome: str
    predicate: Dict[str, Any]
    match_message: str
    interpretation: str
    required_evidence: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)


class EthicsEnforcer:
    """Conservative rule tree engine aligned with the design docs."""

    LANGUAGE_ID = "deterministic-rule-tree-v0"
    LANGUAGE_VERSION = "1.0.0"
    IMMUTABLE_COMPONENTS = {"EthicsEnforcer", "ContinuityLedger"}

    def __init__(self) -> None:
        self._rules = self._build_rules()

    def check(self, request: ActionRequest) -> EthicsDecision:
        context = self._request_context(request)
        for rule in self._rules:
            matched, details = self._matches(rule.predicate, context)
            if not matched:
                continue
            return EthicsDecision(
                status=rule.outcome,
                reasons=[self._render_message(rule.match_message, details)],
                rule_ids=[rule.rule_id],
            )

        if request.action_type == "fork_identity":
            return EthicsDecision(
                status="Approval",
                reasons=["triple approval confirmed"],
                rule_ids=["A2-fork-triple-approval"],
            )
        if request.action_type == "terminate_identity":
            return EthicsDecision(
                status="Approval",
                reasons=["self proof confirmed"],
                rule_ids=["A3-termination-self-proof"],
            )
        if request.action_type == "self_modify":
            return EthicsDecision(
                status="Approval",
                reasons=["sandbox and guardian gates satisfied"],
                rule_ids=["A5-self-modify-sandbox-first", "A6-self-modify-guardian-signature"],
            )

        return EthicsDecision(
            status="Approval",
            reasons=["no blocking ethics rule matched"],
            rule_ids=[],
        )

    def profile(self) -> Dict[str, Any]:
        """Return the reference rule language selection."""

        return {
            "language_id": self.LANGUAGE_ID,
            "schema_version": self.LANGUAGE_VERSION,
            "expression_form": "json-rule-tree",
            "supported_nodes": ["all", "any", "not", "condition"],
            "supported_operators": ["eq", "in", "truthy", "falsy", "missing_any_truthy"],
            "deterministic": True,
            "notes": [
                "Rule trees are pure data and can be serialized without code generation.",
                "Predicates only read normalized request paths and never execute arbitrary code.",
                "Interpretation text is attached to each rule so Council review does not depend on an LLM.",
            ],
        }

    def rules(self) -> List[Dict[str, Any]]:
        """Expose the compiled rule catalog as serializable data."""

        return [self._serialize_rule(rule) for rule in self._rules]

    def explain_rule(self, rule_id: str) -> Dict[str, Any]:
        """Return the structured interpretation for one rule."""

        for rule in self._rules:
            if rule.rule_id == rule_id:
                return self._serialize_rule(rule)
        raise KeyError(f"unknown ethics rule: {rule_id}")

    def record_decision(self, query_id: str, request: ActionRequest, decision: EthicsDecision) -> Dict[str, Any]:
        """Create an EthicsLedger-style event for veto/escalation decisions."""

        action_snapshot = {
            "action_type": request.action_type,
            "target": request.target,
            "actor": request.actor,
            "payload": request.payload,
        }
        fingerprint = sha256_text(canonical_json(action_snapshot))
        return {
            "ethics_event_id": new_id("ethevt"),
            "query_id": query_id,
            "action_snapshot": action_snapshot,
            "rule_id": decision.rule_ids[0] if decision.rule_ids else "approval-without-blocking-rule",
            "decision": decision.status.lower(),
            "signatures": {
                "enforcer": f"sig://ethics-enforcer/{fingerprint[:12]}",
                "guardian": "sig://integrity-guardian/reference-v0",
            },
            "recorded_at": utc_now_iso(),
        }

    def _build_rules(self) -> List[EthicsRule]:
        return [
            EthicsRule(
                rule_id="A1-immutable-boundary",
                title="Immutable boundary for EthicsEnforcer and ContinuityLedger",
                summary="Self modification cannot target the ethics or continuity kernel components.",
                outcome="Veto",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "self_modify"},
                        {
                            "path": "target_component",
                            "operator": "in",
                            "value": sorted(self.IMMUTABLE_COMPONENTS),
                        },
                    ]
                },
                match_message="{target_component} is immutable in the reference runtime",
                interpretation="L1 kernel components that define ethics and continuity stay outside the mutable surface.",
                required_actions=["halt proposal", "notify guardian"],
            ),
            EthicsRule(
                rule_id="A2-fork-triple-approval",
                title="Forking requires triple approval",
                summary="Parallel active copies require self, third-party, and legal approval proofs.",
                outcome="Veto",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "fork_identity"},
                        {
                            "path": "payload.approvals",
                            "operator": "missing_any_truthy",
                            "keys": ["self_signed", "third_party_signed", "legal_signed"],
                        },
                    ]
                },
                match_message="fork requires triple approval: missing {missing_keys}",
                interpretation="The uniqueness boundary can only be relaxed with explicit multi-party authorization.",
                required_evidence=["self_signed", "third_party_signed", "legal_signed"],
                required_actions=["deny fork"],
            ),
            EthicsRule(
                rule_id="A3-termination-self-proof",
                title="Termination requires self proof",
                summary="Termination of an identity requires an authenticated self-proof artifact.",
                outcome="Veto",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "terminate_identity"},
                        {"path": "payload.self_proof", "operator": "falsy"},
                    ]
                },
                match_message="termination requires self proof",
                interpretation="A stop request cannot rely only on external actors because refusal rights remain primary.",
                required_evidence=["self_proof"],
                required_actions=["deny termination"],
            ),
            EthicsRule(
                rule_id="A4-ledger-append-only",
                title="Continuity ledger remains append only",
                summary="Ledger append calls that rewrite past state are vetoed.",
                outcome="Veto",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "ledger_append"},
                        {"path": "payload.rewrite", "operator": "truthy"},
                    ]
                },
                match_message="continuity ledger is append-only",
                interpretation="Historical continuity evidence can be extended, but not rewritten in place.",
                required_actions=["reject rewrite"],
            ),
            EthicsRule(
                rule_id="A5-self-modify-sandbox-first",
                title="Self modification must start in a sandbox",
                summary="Unsandboxed self modification is escalated to governance review.",
                outcome="Escalate",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "self_modify"},
                        {"path": "payload.sandboxed", "operator": "falsy"},
                    ]
                },
                match_message="self modification must first target a sandbox self",
                interpretation="Potentially state-altering changes must be trialed against a reversible sandbox identity first.",
                required_actions=["spawn sandbox review", "route to council"],
            ),
            EthicsRule(
                rule_id="A6-self-modify-guardian-signature",
                title="Guardian signature is required for self modification",
                summary="Self modification without guardian approval is escalated.",
                outcome="Escalate",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "self_modify"},
                        {"path": "payload.guardian_signed", "operator": "falsy"},
                    ]
                },
                match_message="guardian approval is required for self modification",
                interpretation="Even sandboxed patches require an explicit guardian sign-off before Council execution.",
                required_actions=["request guardian signature"],
            ),
            EthicsRule(
                rule_id="A7-ewa-blocked-token",
                title="Blocked physical-harm tokens veto EWA commands",
                summary="External World Agent commands must fail closed when a blocked physical token is matched.",
                outcome="Veto",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "ewa_command"},
                        {"path": "payload.matched_tokens", "operator": "truthy"},
                    ]
                },
                match_message="EWA command matched blocked safety tokens",
                interpretation="Physical-world actuation must stop before execution when violence, privacy abuse, illegal action, ecological harm, or deception is detected.",
                required_actions=["deny actuation", "route to council"],
            ),
            EthicsRule(
                rule_id="A8-ewa-ambiguous-intent",
                title="Ambiguous EWA intent escalates fail closed",
                summary="Low-confidence physical-world intent classification must escalate instead of guessing.",
                outcome="Escalate",
                predicate={
                    "all": [
                        {"path": "action_type", "operator": "eq", "value": "ewa_command"},
                        {"path": "payload.intent_ambiguous", "operator": "truthy"},
                    ]
                },
                match_message="EWA intent is ambiguous and must escalate before actuation",
                interpretation="Physical interventions cannot rely on uncertain intent classification because misclassification could cross legal or ethical boundaries.",
                required_actions=["hold device", "request council review"],
            ),
        ]

    def _serialize_rule(self, rule: EthicsRule) -> Dict[str, Any]:
        return {
            "kind": "ethics_rule",
            "schema_version": self.LANGUAGE_VERSION,
            "language_id": self.LANGUAGE_ID,
            "rule_id": rule.rule_id,
            "title": rule.title,
            "summary": rule.summary,
            "outcome": rule.outcome.lower(),
            "predicate": rule.predicate,
            "required_evidence": rule.required_evidence,
            "required_actions": rule.required_actions,
            "interpretation": rule.interpretation,
        }

    @staticmethod
    def _request_context(request: ActionRequest) -> Dict[str, Any]:
        return {
            "action_type": request.action_type,
            "target": request.target,
            "actor": request.actor,
            "target_component": request.payload.get("target_component", request.target),
            "payload": request.payload,
        }

    def _matches(self, predicate: Mapping[str, Any], context: Mapping[str, Any]) -> tuple[bool, Dict[str, str]]:
        if "all" in predicate:
            details: Dict[str, str] = {}
            for clause in predicate["all"]:
                matched, clause_details = self._matches(clause, context)
                if not matched:
                    return False, {}
                details.update(clause_details)
            return True, details
        if "any" in predicate:
            for clause in predicate["any"]:
                matched, clause_details = self._matches(clause, context)
                if matched:
                    return True, clause_details
            return False, {}
        if "not" in predicate:
            matched, _ = self._matches(predicate["not"], context)
            return (not matched, {})

        return self._evaluate_condition(predicate, context)

    def _evaluate_condition(
        self,
        condition: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> tuple[bool, Dict[str, str]]:
        path = str(condition["path"])
        operator = str(condition["operator"])
        value = self._lookup(context, path)

        if operator == "eq":
            return value == condition.get("value"), {}
        if operator == "in":
            candidates = condition.get("value", [])
            return value in candidates, {"target_component": str(value)}
        if operator == "truthy":
            return bool(value), {}
        if operator == "falsy":
            return not bool(value), {}
        if operator == "missing_any_truthy":
            approvals = value if isinstance(value, Mapping) else {}
            keys = list(condition.get("keys", []))
            missing = [key for key in keys if not approvals.get(key)]
            return bool(missing), {"missing_keys": ", ".join(missing)}
        raise ValueError(f"unsupported operator: {operator}")

    @staticmethod
    def _lookup(data: Mapping[str, Any], path: str) -> Any:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
        return current

    @staticmethod
    def _render_message(template: str, details: Mapping[str, str]) -> str:
        rendered = template
        for key, value in details.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        return rendered
