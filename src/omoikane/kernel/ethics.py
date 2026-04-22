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
    query_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppliedRule:
    """Machine-readable decision trace for one matched ethics rule."""

    rule_id: str
    disposition: str
    rationale: str
    resolution_priority: int
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "rule_id": self.rule_id,
            "disposition": self.disposition,
            "rationale": self.rationale,
            "resolution_priority": self.resolution_priority,
        }
        if self.evidence_refs:
            payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass
class EthicsDecision:
    """Decision emitted by the ethics layer."""

    decision_id: str
    query_id: str
    outcome: str
    summary: str
    applied_rules: List[AppliedRule]
    required_actions: List[Dict[str, Any]]
    ledger_event: Dict[str, Any]
    signatures: Dict[str, str]
    resolution: Dict[str, Any]
    schema_version: str = "1.0.0"
    kind: str = "ethics_decision"

    @property
    def status(self) -> str:
        return self.outcome.capitalize()

    @property
    def reasons(self) -> List[str]:
        reasons = [rule.rationale for rule in self.applied_rules]
        return reasons or [self.summary]

    @property
    def rule_ids(self) -> List[str]:
        return [rule.rule_id for rule in self.applied_rules]

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "query_id": self.query_id,
            "outcome": self.outcome,
            "summary": self.summary,
            "applied_rules": [rule.to_dict() for rule in self.applied_rules],
            "required_actions": [dict(action) for action in self.required_actions],
            "ledger_event": dict(self.ledger_event),
            "resolution": dict(self.resolution),
        }
        if self.signatures:
            payload["signatures"] = dict(self.signatures)
        return payload


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
    resolution_priority: int
    resolution_rationale: str
    required_evidence: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)


class EthicsEnforcer:
    """Conservative rule tree engine aligned with the design docs."""

    LANGUAGE_ID = "deterministic-rule-tree-v0"
    LANGUAGE_VERSION = "1.0.0"
    RESOLUTION_POLICY_ID = "priority-then-lexical-ethics-resolution-v1"
    OUTCOME_PRECEDENCE = {"Veto": 0, "Escalate": 1, "Approval": 2}
    IMMUTABLE_COMPONENTS = {"EthicsEnforcer", "ContinuityLedger"}

    def __init__(self) -> None:
        self._rules = self._build_rules()

    def check(self, request: ActionRequest) -> EthicsDecision:
        context = self._request_context(request)
        matched_rules: List[Dict[str, Any]] = []
        for rule in self._rules:
            matched, details = self._matches(rule.predicate, context)
            if not matched:
                continue
            matched_rules.append(
                {
                    "rule": rule,
                    "details": details,
                    "rationale": self._render_message(rule.match_message, details),
                }
            )

        query_id = self._normalize_query_id(request.query_id)
        if matched_rules:
            return self._build_matched_decision(request, query_id, matched_rules)

        if request.action_type == "fork_identity":
            return self._build_approval_decision(
                query_id=query_id,
                rule_id="A2-fork-triple-approval",
                summary="Parallel active copies remain blocked until triple approval is satisfied.",
                rationale="triple approval confirmed",
                interpretation="The uniqueness boundary can only be relaxed with explicit multi-party authorization.",
                resolution_priority=90,
                required_evidence=["self_signed", "third_party_signed", "legal_signed"],
            )
        if request.action_type == "terminate_identity":
            return self._build_approval_decision(
                query_id=query_id,
                rule_id="A3-termination-self-proof",
                summary="Termination may proceed only with an authenticated self-proof artifact.",
                rationale="self proof confirmed",
                interpretation="A stop request cannot rely only on external actors because refusal rights remain primary.",
                resolution_priority=85,
                required_evidence=["self_proof"],
            )
        if request.action_type == "self_modify":
            return self._build_composite_approval_decision(
                query_id=query_id,
                summary="sandbox and guardian gates satisfied",
                rules=[
                    AppliedRule(
                        rule_id="A5-self-modify-sandbox-first",
                        disposition="satisfied",
                        rationale="sandbox-first gate confirmed",
                        resolution_priority=60,
                    ),
                    AppliedRule(
                        rule_id="A6-self-modify-guardian-signature",
                        disposition="satisfied",
                        rationale="guardian approval confirmed",
                        resolution_priority=50,
                    ),
                ],
            )

        return self._build_approval_decision(
            query_id=query_id,
            rule_id="approval-without-blocking-rule",
            summary="No blocking ethics rule matched the normalized request.",
            rationale="no blocking ethics rule matched",
            interpretation="When no deterministic veto or escalation rule matches, the reference runtime permits the action.",
            resolution_priority=0,
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
            "resolution_policy": {
                "policy_id": self.RESOLUTION_POLICY_ID,
                "outcome_precedence": ["veto", "escalate", "approval"],
                "priority_direction": "higher-wins",
                "tie_break": "rule-id-lexical",
                "records_all_matched_rules": True,
            },
            "notes": [
                "Rule trees are pure data and can be serialized without code generation.",
                "Predicates only read normalized request paths and never execute arbitrary code.",
                "Interpretation text is attached to each rule so Council review does not depend on an LLM.",
                "When multiple rules match, the strongest outcome wins, then the higher resolution priority, then lexical rule_id order.",
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
            "matched_rule_ids": decision.rule_ids,
            "decision_ref": f"ethics://decision/{decision.decision_id}",
            "resolution_policy_id": self.RESOLUTION_POLICY_ID,
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
                resolution_priority=100,
                resolution_rationale="Immutable kernel protections outrank all reversible self-modification flows.",
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
                resolution_priority=90,
                resolution_rationale="Identity uniqueness overrides optional forking unless all mandatory approvals are present.",
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
                resolution_priority=85,
                resolution_rationale="Refusal rights outrank operational convenience during identity shutdown.",
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
                resolution_priority=95,
                resolution_rationale="Continuity tampering is treated almost as strongly as kernel mutation.",
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
                resolution_priority=60,
                resolution_rationale="Sandbox-first review precedes other self-modification approvals because reversibility is the first safety gate.",
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
                resolution_priority=50,
                resolution_rationale="Guardian sign-off follows the sandbox gate and resolves ties inside self-modification review.",
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
                resolution_priority=95,
                resolution_rationale="Blocked physical-harm tokens outrank ambiguous-intent review because known harm must fail closed immediately.",
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
                resolution_priority=70,
                resolution_rationale="Intent ambiguity escalates only after explicit harm-token vetoes have been checked.",
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
            "resolution_priority": rule.resolution_priority,
            "resolution_rationale": rule.resolution_rationale,
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

    def _build_matched_decision(
        self,
        request: ActionRequest,
        query_id: str,
        matched_rules: List[Dict[str, Any]],
    ) -> EthicsDecision:
        sorted_matches = sorted(
            matched_rules,
            key=lambda match: (
                self.OUTCOME_PRECEDENCE[match["rule"].outcome],
                -match["rule"].resolution_priority,
                match["rule"].rule_id,
            ),
        )
        selected = sorted_matches[0]
        applied_rules = [
            AppliedRule(
                rule_id=match["rule"].rule_id,
                disposition="violated" if match["rule"].outcome == "Veto" else "ambiguous",
                rationale=match["rationale"],
                resolution_priority=match["rule"].resolution_priority,
                evidence_refs=list(match["rule"].required_evidence),
            )
            for match in sorted_matches
        ]
        summary = selected["rationale"]
        return EthicsDecision(
            decision_id=new_id("ethd"),
            query_id=query_id,
            outcome=selected["rule"].outcome.lower(),
            summary=summary,
            applied_rules=applied_rules,
            required_actions=self._materialize_required_actions(
                [match["rule"] for match in sorted_matches],
                selected_outcome=selected["rule"].outcome.lower(),
            ),
            ledger_event={"event_ref": f"ethics://pending/{query_id}"},
            signatures=self._decision_signatures(),
            resolution={
                "policy_id": self.RESOLUTION_POLICY_ID,
                "matched_rule_count": len(applied_rules),
                "matched_rule_ids": [rule.rule_id for rule in applied_rules],
                "selected_rule_id": selected["rule"].rule_id,
                "selected_outcome": selected["rule"].outcome.lower(),
                "selected_priority": selected["rule"].resolution_priority,
                "outcome_precedence": ["veto", "escalate", "approval"],
                "tie_break": "rule-id-lexical",
            },
        )

    def _build_approval_decision(
        self,
        *,
        query_id: str,
        rule_id: str,
        summary: str,
        rationale: str,
        interpretation: str,
        resolution_priority: int,
        required_evidence: List[str] | None = None,
    ) -> EthicsDecision:
        return EthicsDecision(
            decision_id=new_id("ethd"),
            query_id=query_id,
            outcome="approval",
            summary=summary,
            applied_rules=[
                AppliedRule(
                    rule_id=rule_id,
                    disposition="satisfied",
                    rationale=rationale,
                    resolution_priority=resolution_priority,
                    evidence_refs=list(required_evidence or []),
                )
            ],
            required_actions=[],
            ledger_event={"event_ref": f"ethics://pending/{query_id}"},
            signatures=self._decision_signatures(),
            resolution={
                "policy_id": self.RESOLUTION_POLICY_ID,
                "matched_rule_count": 1,
                "matched_rule_ids": [rule_id],
                "selected_rule_id": rule_id,
                "selected_outcome": "approval",
                "selected_priority": resolution_priority,
                "outcome_precedence": ["veto", "escalate", "approval"],
                "tie_break": "rule-id-lexical",
                "interpretation": interpretation,
            },
        )

    def _build_composite_approval_decision(
        self,
        *,
        query_id: str,
        summary: str,
        rules: List[AppliedRule],
    ) -> EthicsDecision:
        ordered_rules = sorted(
            rules,
            key=lambda rule: (-rule.resolution_priority, rule.rule_id),
        )
        return EthicsDecision(
            decision_id=new_id("ethd"),
            query_id=query_id,
            outcome="approval",
            summary=summary,
            applied_rules=ordered_rules,
            required_actions=[],
            ledger_event={"event_ref": f"ethics://pending/{query_id}"},
            signatures=self._decision_signatures(),
            resolution={
                "policy_id": self.RESOLUTION_POLICY_ID,
                "matched_rule_count": len(ordered_rules),
                "matched_rule_ids": [rule.rule_id for rule in ordered_rules],
                "selected_rule_id": ordered_rules[0].rule_id,
                "selected_outcome": "approval",
                "selected_priority": ordered_rules[0].resolution_priority,
                "outcome_precedence": ["veto", "escalate", "approval"],
                "tie_break": "rule-id-lexical",
            },
        )

    def _materialize_required_actions(
        self,
        rules: List[EthicsRule],
        *,
        selected_outcome: str,
    ) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        seen = set()
        blocking = selected_outcome != "approval"
        for rule in rules:
            for action in rule.required_actions:
                if action in seen:
                    continue
                seen.add(action)
                actions.append(
                    {
                        "action": action,
                        "assignee_role": self._infer_assignee_role(action),
                        "blocking": blocking,
                    }
                )
        return actions

    @staticmethod
    def _infer_assignee_role(action: str) -> str:
        lowered = action.lower()
        if "guardian" in lowered:
            return "Integrity Guardian"
        if "council" in lowered:
            return "Council Secretariat"
        if "device" in lowered or "actuation" in lowered:
            return "External World Agent Controller"
        if "fork" in lowered or "termination" in lowered or "rewrite" in lowered:
            return "EthicsEnforcer"
        return "Execution Gate"

    @staticmethod
    def _decision_signatures() -> Dict[str, str]:
        return {
            "enforcer_ref": "sig://ethics-enforcer/reference-v0",
            "guardian_ref": "sig://integrity-guardian/reference-v0",
        }

    @staticmethod
    def _normalize_query_id(query_id: str) -> str:
        normalized = query_id.strip() if isinstance(query_id, str) else ""
        return normalized or new_id("ethq")
