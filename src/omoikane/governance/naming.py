"""Deterministic naming policy for the OmoikaneOS reference runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable


SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class NamingRule:
    """One concept-level naming decision with canonical and rejected forms."""

    concept_id: str
    canonical: str
    accepted_user_facing: tuple[str, ...]
    accepted_internal: tuple[str, ...]
    rejected: tuple[str, ...]
    japanese_labels: tuple[str, ...]
    rationale: tuple[str, ...]
    contexts: tuple[str, ...]

    def to_policy_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "canonical": self.canonical,
            "accepted_user_facing": list(self.accepted_user_facing),
            "accepted_internal": list(self.accepted_internal),
            "rejected": list(self.rejected),
            "japanese_labels": list(self.japanese_labels),
            "contexts": list(self.contexts),
            "rationale": list(self.rationale),
        }


class NamingService:
    """Validate labels against the fixed Omoikane naming policy."""

    def __init__(self) -> None:
        self._rules = {
            rule.concept_id: rule
            for rule in (
                NamingRule(
                    concept_id="project_romanization",
                    canonical="Omoikane",
                    accepted_user_facing=("Omoikane", "OmoikaneOS", "Omoikane Council"),
                    accepted_internal=("omoikane", "Omoikane", "OMOIKANE"),
                    rejected=("Omoi-Kane", "Omoi-KaneOS", "OmoiKane", "OMOIKANE"),
                    japanese_labels=("思兼神", "オモイカネ"),
                    rationale=(
                        "project branding uses the single-token romanization derived from 思兼神",
                        "hyphenated or all-caps user-facing forms are rejected to keep docs and paths stable",
                    ),
                    contexts=("external_brand", "doc_title", "code_identifier"),
                ),
                NamingRule(
                    concept_id="sandbox_self_name",
                    canonical="Mirage Self",
                    accepted_user_facing=("Mirage Self", "幻影自我", "蜃気自我"),
                    accepted_internal=("SandboxSentinel", "MirageSelf"),
                    rejected=("Yumi Self", "Phantom Self", "sandbox self"),
                    japanese_labels=("幻影自我", "蜃気自我"),
                    rationale=(
                        "mirage conveys a reversible, non-substantial sandbox fork without person-name drift",
                        "legacy SandboxSentinel remains an implementation-detail alias, not the user-facing name",
                    ),
                    contexts=("user_facing_doc", "code_identifier", "governance_policy"),
                ),
            )
        }

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "kind": "naming_policy",
            "schema_version": SCHEMA_VERSION,
            "rules": {
                concept_id: rule.to_policy_dict()
                for concept_id, rule in self._rules.items()
            },
            "enforcement": {
                "user_facing_docs_use_canonical": True,
                "internal_aliases_are_documented_not_promoted": True,
                "abbreviations_allowed": False,
            },
            "notes": [
                "Omoikane is the only approved romanization for project-facing English labels",
                "Mirage Self is the formal sandbox fork name; SandboxSentinel is a retained runtime alias",
            ],
        }

    def review_term(self, concept_id: str, candidate: str, *, context: str) -> Dict[str, Any]:
        if concept_id not in self._rules:
            raise ValueError(f"unknown naming concept: {concept_id}")

        rule = self._rules[concept_id]
        normalized = candidate.strip()
        status = "rewrite-required"
        suggestion = rule.canonical
        allowed = False

        if normalized == rule.canonical or normalized in rule.accepted_user_facing:
            status = "accepted"
            allowed = True
        elif context == "code_identifier" and normalized in rule.accepted_internal:
            status = "allowed-alias"
            allowed = True
        elif normalized in rule.accepted_internal:
            status = "allowed-alias"
        elif normalized in rule.rejected:
            suggestion = self._canonical_rewrite(normalized, rule)
        elif self._contains_any(normalized, rule.rejected):
            suggestion = self._canonical_rewrite(normalized, rule)

        return {
            "concept_id": concept_id,
            "context": context,
            "candidate": candidate,
            "normalized": normalized,
            "status": status,
            "allowed_in_context": allowed,
            "canonical": rule.canonical,
            "suggestion": suggestion,
            "rejected_forms": list(rule.rejected),
            "accepted_user_facing": list(rule.accepted_user_facing),
            "accepted_internal": list(rule.accepted_internal),
            "rationale": list(rule.rationale),
        }

    @staticmethod
    def _contains_any(candidate: str, rejected: Iterable[str]) -> bool:
        lowered = candidate.lower()
        return any(term.lower() in lowered for term in rejected)

    @staticmethod
    def _canonical_rewrite(candidate: str, rule: NamingRule) -> str:
        if rule.concept_id == "project_romanization":
            return (
                candidate.replace("Omoi-Kane", "Omoikane")
                .replace("OmoiKane", "Omoikane")
                .replace("OMOIKANE", "Omoikane")
            )
        if rule.concept_id == "sandbox_self_name":
            return (
                candidate.replace("Yumi Self", "Mirage Self")
                .replace("Phantom Self", "Mirage Self")
                .replace("sandbox self", "Mirage Self")
            )
        return rule.canonical

    def validation_summary(self, reviews: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        return {
            "official_project_name_fixed": reviews["canonical_brand"]["status"] == "accepted",
            "hyphenated_project_form_rejected": reviews["hyphenated_brand"]["status"] == "rewrite-required",
            "sandbox_formal_name_fixed": reviews["canonical_sandbox_name"]["status"] == "accepted",
            "legacy_runtime_alias_documented": reviews["legacy_runtime_alias"]["status"] == "allowed-alias",
            "rejected_candidate_requires_rewrite": reviews["rejected_sandbox_name"]["status"]
            == "rewrite-required",
        }
