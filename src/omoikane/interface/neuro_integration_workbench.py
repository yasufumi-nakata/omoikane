"""Neuroscience data integration workbench reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

NIW_SCHEMA_VERSION = "1.0"
NIW_APP_REGISTRY_PROFILE_ID = "neuro-biodata-multi-application-registry-v1"
NIW_SOURCE_BUNDLE_PROFILE_ID = "neuro-cross-modal-source-bundle-v1"
NIW_WORKSPACE_PROFILE_ID = "llm-native-neuroscience-workspace-v1"
NIW_ANALYSIS_PROFILE_ID = "survey-eeg-neurodata-fusion-analysis-v1"
NIW_OPERATOR_GUIDE_PROFILE_ID = "llm-native-non-ml-operator-guide-v1"
NIW_REPLACEMENT_PLAN_PROFILE_ID = "neuro-application-replacement-plan-v1"
NIW_CONNECTOR_PROFILE_ID = "neuro-application-connector-v1"
NIW_CONNECTOR_BUNDLE_PROFILE_ID = "neuro-application-connector-bundle-v1"
NIW_BIODATA_SURVEY_EEG_FUSION_PROFILE_ID = "biodata-survey-eeg-window-fusion-v1"
NIW_BIODATA_SURVEY_EEG_FUSION_CLAIM_CEILING = "survey-eeg-correlation-input-only"
NIW_BIODATA_FUSION_BINDING_ROLE = "biodata-survey-eeg-fusion"
NIW_CLAIM_CEILING = "feature-alignment-and-analysis-plan-only"
NIW_CONFLICT_SINK_URL = "https://mind-upload.com/frontiers/neurodata-integration"
NIW_SOURCE_STORAGE_POLICY = "feature-digest+analysis-axis-summary-only"
NIW_WORKSPACE_STORAGE_POLICY = "app-receipt-digest+source-bundle-digest-only"
NIW_GUIDE_POLICY = "plain-language-cards+agent-task-templates-v1"
NIW_REPLACEMENT_PLAN_POLICY = "app-digest+source-family-lane-coverage-only"
NIW_CONNECTOR_BUNDLE_POLICY = "connector-ref+credential-ref+contract-digest-only"
NIW_SEED_SOURCE_TYPES = ("questionnaire", "eeg")
NIW_EXPANSION_SOURCE_TYPES = ("fmri_bold", "brain_organoid")
NIW_REQUIRED_REPLACEMENT_LANES = (
    "measurement",
    "analysis",
    "data-curation",
    "operator-copilot",
    "agent-automation",
)
NIW_OPERATOR_SKILL_FLOORS = (
    "non_ml_operator",
    "coding_agent",
    "analyst",
    "researcher",
)
NIW_APP_KINDS = (
    "measurement",
    "analysis",
    "data-curation",
    "visualization",
    "operator-copilot",
    "agent-automation",
)
NIW_CONNECTOR_KINDS = (
    "measurement-ingest",
    "analysis-runner",
    "curation-ledger",
    "operator-console",
    "agent-runner",
    "visualization-viewer",
)
NIW_CONNECTOR_PROTOCOLS = (
    "local-file",
    "https-api",
    "database-view",
    "notebook-runner",
    "llm-tool",
    "message-queue",
)
NIW_SOURCE_TYPE_ALIASES = {
    "survey": "questionnaire",
    "self-report": "questionnaire",
    "self_report": "questionnaire",
    "electroencephalogram": "eeg",
    "fmri": "fmri_bold",
    "fmri-bold": "fmri_bold",
    "bold": "fmri_bold",
    "organoid": "brain_organoid",
    "brain-organoid": "brain_organoid",
    "neural_organoid": "brain_organoid",
    "wearable": "biosensor",
    "wearables": "biosensor",
    "behavior": "behavioral_task",
}
NIW_SOURCE_FAMILIES = {
    "questionnaire": "self_report_survey",
    "eeg": "neural_electrical",
    "fmri_bold": "neurovascular_imaging",
    "brain_organoid": "in_vitro_neural_tissue",
    "biosensor": "human_biosignal",
    "behavioral_task": "behavioral_assay",
    "omics": "molecular_omics",
    "clinical_metadata": "clinical_context",
    "environment": "environmental_context",
}
NIW_REPLACEMENT_LANE_BY_APP_KIND = {
    "measurement": "measurement",
    "analysis": "analysis",
    "data-curation": "data-curation",
    "visualization": "analysis",
    "operator-copilot": "operator-copilot",
    "agent-automation": "agent-automation",
}
NIW_CONFLICT_REFS = (
    {
        "topic": "survey-eeg-mind-equivalence",
        "status": "unresolved",
        "mind_upload_ref": f"{NIW_CONFLICT_SINK_URL}#survey-eeg-equivalence",
        "reason": "survey and EEG feature alignment does not prove subjective sameness",
    },
    {
        "topic": "multi-modal-neuroscience-to-upload-readiness",
        "status": "insufficient-evidence",
        "mind_upload_ref": f"{NIW_CONFLICT_SINK_URL}#upload-readiness",
        "reason": "multi-modal integration is an analysis substrate, not a mind-upload completion proof",
    },
)


class NeuroIntegrationWorkbench:
    """Digest-only workbench for multi-application neuroscience data integration."""

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": NIW_SCHEMA_VERSION,
            "app_registry_profile_id": NIW_APP_REGISTRY_PROFILE_ID,
            "source_bundle_profile_id": NIW_SOURCE_BUNDLE_PROFILE_ID,
            "workspace_profile_id": NIW_WORKSPACE_PROFILE_ID,
            "analysis_profile_id": NIW_ANALYSIS_PROFILE_ID,
            "operator_guide_profile_id": NIW_OPERATOR_GUIDE_PROFILE_ID,
            "replacement_plan_profile_id": NIW_REPLACEMENT_PLAN_PROFILE_ID,
            "connector_profile_id": NIW_CONNECTOR_PROFILE_ID,
            "connector_bundle_profile_id": NIW_CONNECTOR_BUNDLE_PROFILE_ID,
            "biodata_survey_eeg_fusion_profile_id": (
                NIW_BIODATA_SURVEY_EEG_FUSION_PROFILE_ID
            ),
            "seed_source_types": list(NIW_SEED_SOURCE_TYPES),
            "expansion_source_types": list(NIW_EXPANSION_SOURCE_TYPES),
            "source_families": dict(NIW_SOURCE_FAMILIES),
            "required_replacement_lanes": list(NIW_REQUIRED_REPLACEMENT_LANES),
            "operator_skill_floors": list(NIW_OPERATOR_SKILL_FLOORS),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "source_storage_policy": NIW_SOURCE_STORAGE_POLICY,
            "workspace_storage_policy": NIW_WORKSPACE_STORAGE_POLICY,
            "operator_guide_policy": NIW_GUIDE_POLICY,
            "replacement_plan_policy": NIW_REPLACEMENT_PLAN_POLICY,
            "connector_bundle_policy": NIW_CONNECTOR_BUNDLE_POLICY,
            "conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_questionnaire_payload_stored": False,
            "raw_eeg_payload_stored": False,
            "raw_neuroimaging_payload_stored": False,
            "raw_organoid_payload_stored": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }

    def register_application(
        self,
        app_name: str,
        app_kind: str,
        supported_source_types: Sequence[str],
        workflow_roles: Sequence[str],
        operator_skill_floor: str = "non_ml_operator",
        llm_native: bool = True,
    ) -> Dict[str, Any]:
        self._require_non_empty_string(app_name, "app_name")
        normalized_kind = self._normalize_app_kind(app_kind)
        source_types = self._normalize_source_types(
            supported_source_types,
            "supported_source_types",
        )
        roles = self._normalize_workflow_roles(workflow_roles)
        if operator_skill_floor not in NIW_OPERATOR_SKILL_FLOORS:
            raise ValueError("operator_skill_floor is not supported")

        modality_families = {
            source_type: self._source_family(source_type) for source_type in source_types
        }
        replacement_lanes = sorted(
            {
                NIW_REPLACEMENT_LANE_BY_APP_KIND[normalized_kind],
                *(role for role in roles if role in NIW_REQUIRED_REPLACEMENT_LANES),
            }
        )
        receipt = {
            "schema_version": NIW_SCHEMA_VERSION,
            "app_ref": f"app://neuro-integration/{new_id('niw-app')}",
            "registered_at": utc_now_iso(),
            "profile_id": NIW_APP_REGISTRY_PROFILE_ID,
            "app_name": app_name,
            "app_kind": normalized_kind,
            "supported_source_types": source_types,
            "supported_source_families": modality_families,
            "workflow_roles": roles,
            "replacement_lanes": replacement_lanes,
            "operator_skill_floor": operator_skill_floor,
            "llm_native": bool(llm_native),
            "beginner_safe_mode": operator_skill_floor == "non_ml_operator",
            "raw_app_payload_stored": False,
            "raw_credential_payload_stored": False,
        }
        receipt["app_digest"] = sha256_text(
            canonical_json(self._app_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def bind_source_bundle(
        self,
        identity_id: str,
        source_manifests: Sequence[Dict[str, Any]],
        upstream_receipts: Sequence[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        self._require_non_empty_string(identity_id, "identity_id")
        if len(source_manifests) < 2:
            raise ValueError("source_manifests must include at least questionnaire and eeg")

        sources = [
            self._normalize_source_manifest(source_manifest)
            for source_manifest in source_manifests
        ]
        source_types = [source["source_type"] for source in sources]
        if not all(source_type in source_types for source_type in NIW_SEED_SOURCE_TYPES):
            raise ValueError("source_manifests must include questionnaire and eeg")
        upstream_receipt_bindings = [
            self._normalize_upstream_receipt(receipt, identity_id)
            for receipt in (upstream_receipts or [])
        ]
        survey_eeg_fusion_receipt_bound = any(
            binding["receipt_role"] == NIW_BIODATA_FUSION_BINDING_ROLE
            for binding in upstream_receipt_bindings
        )
        upstream_receipt_digest_set = self._upstream_receipt_digest_set(
            upstream_receipt_bindings
        )
        source_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_SOURCE_BUNDLE_PROFILE_ID,
                    "source_digests": [source["feature_digest"] for source in sources],
                    "source_types": source_types,
                }
            )
        )
        expansion_source_types_present = [
            source_type for source_type in NIW_EXPANSION_SOURCE_TYPES if source_type in source_types
        ]
        bundle = {
            "schema_version": NIW_SCHEMA_VERSION,
            "source_bundle_ref": f"source-bundle://neuro-integration/{new_id('niw-source-bundle')}",
            "created_at": utc_now_iso(),
            "profile_id": NIW_SOURCE_BUNDLE_PROFILE_ID,
            "identity_id": identity_id,
            "source_count": len(sources),
            "source_types": source_types,
            "source_families": {
                source_type: self._source_family(source_type) for source_type in source_types
            },
            "sources": sources,
            "source_digest_set": source_digest_set,
            "seed_sources_required": list(NIW_SEED_SOURCE_TYPES),
            "seed_survey_eeg_bound": True,
            "upstream_receipt_count": len(upstream_receipt_bindings),
            "upstream_receipt_digest_set": upstream_receipt_digest_set,
            "upstream_receipt_bindings": upstream_receipt_bindings,
            "survey_eeg_fusion_receipt_bound": survey_eeg_fusion_receipt_bound,
            "expansion_source_types_present": expansion_source_types_present,
            "expansion_modalities_bound": bool(expansion_source_types_present),
            "storage_policy": NIW_SOURCE_STORAGE_POLICY,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_questionnaire_payload_stored": False,
            "raw_eeg_payload_stored": False,
            "raw_neuroimaging_payload_stored": False,
            "raw_organoid_payload_stored": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        bundle["source_bundle_digest"] = sha256_text(
            canonical_json(self._source_bundle_digest_payload(bundle))
        )
        return deepcopy(bundle)

    def open_workspace(
        self,
        identity_id: str,
        app_receipts: Sequence[Dict[str, Any]],
        source_bundle: Dict[str, Any],
        analysis_goal: str,
        operator_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._require_non_empty_string(identity_id, "identity_id")
        self._require_non_empty_string(analysis_goal, "analysis_goal")
        self._check_source_bundle(source_bundle)
        if source_bundle.get("identity_id") != identity_id:
            raise ValueError("source_bundle.identity_id must match identity_id")
        apps = [self._check_app_receipt(app_receipt) for app_receipt in app_receipts]
        if not apps:
            raise ValueError("app_receipts must not be empty")
        operator = self._normalize_operator_profile(operator_profile)

        app_digests = [app["app_digest"] for app in apps]
        replacement_lanes = sorted(
            {lane for app in apps for lane in app["replacement_lanes"]}
        )
        source_types = list(source_bundle["source_types"])
        llm_native_workflow_bound = any(app["llm_native"] for app in apps) and operator[
            "llm_assistive_mode"
        ]
        beginner_operator_supported = (
            operator["skill_level"] == "non_ml_operator"
            or any(app["beginner_safe_mode"] for app in apps)
        )
        workspace = {
            "schema_version": NIW_SCHEMA_VERSION,
            "workspace_ref": f"workspace://neuro-integration/{new_id('niw-workspace')}",
            "created_at": utc_now_iso(),
            "profile_id": NIW_WORKSPACE_PROFILE_ID,
            "identity_id": identity_id,
            "analysis_goal": analysis_goal,
            "operator_profile": operator,
            "app_refs": [app["app_ref"] for app in apps],
            "app_digests": app_digests,
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "source_types": source_types,
            "replacement_lanes": replacement_lanes,
            "required_replacement_lanes": list(NIW_REQUIRED_REPLACEMENT_LANES),
            "replacement_lanes_bound": all(
                lane in replacement_lanes for lane in NIW_REQUIRED_REPLACEMENT_LANES
            ),
            "llm_native_workflow_bound": llm_native_workflow_bound,
            "beginner_operator_supported": beginner_operator_supported,
            "coding_agent_ready": "agent-automation" in replacement_lanes,
            "storage_policy": NIW_WORKSPACE_STORAGE_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_app_payload_stored": False,
            "raw_source_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        workspace["workspace_digest"] = sha256_text(
            canonical_json(self._workspace_digest_payload(workspace))
        )
        return deepcopy(workspace)

    def build_survey_eeg_fusion(
        self,
        workspace: Dict[str, Any],
        source_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_workspace(workspace)
        self._check_source_bundle(source_bundle)
        if workspace["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("workspace.source_bundle_digest must match source bundle")
        sources_by_type = {source["source_type"]: source for source in source_bundle["sources"]}
        if not all(source_type in sources_by_type for source_type in NIW_SEED_SOURCE_TYPES):
            raise ValueError("source bundle must include questionnaire and eeg")

        survey = sources_by_type["questionnaire"]
        eeg = sources_by_type["eeg"]
        survey_axes = survey["analysis_axes"]
        eeg_axes = eeg["analysis_axes"]
        distress = float(survey_axes.get("distress_proxy", 0.0))
        attention = float(survey_axes.get("attention_difficulty_proxy", 0.0))
        cortical_load = float(eeg_axes.get("cortical_load_proxy", 0.0))
        alpha_suppression = float(eeg_axes.get("alpha_suppression_proxy", 0.0))
        theta_beta_ratio = float(eeg_axes.get("theta_beta_ratio", 0.0))
        distress_alignment = self._round_score(1.0 - abs(distress - cortical_load))
        attention_alignment = self._round_score(1.0 - abs(attention - alpha_suppression))
        joint_readiness = self._round_score(
            (distress_alignment + attention_alignment + min(1.0, theta_beta_ratio / 3.0)) / 3.0
        )
        expansion_lanes = self._build_expansion_lanes(source_bundle)
        upstream_fusion_binding = self._build_upstream_fusion_binding(source_bundle)
        analysis = {
            "schema_version": NIW_SCHEMA_VERSION,
            "analysis_ref": f"analysis://neuro-integration/{new_id('niw-analysis')}",
            "created_at": utc_now_iso(),
            "profile_id": NIW_ANALYSIS_PROFILE_ID,
            "workspace_ref": workspace["workspace_ref"],
            "workspace_digest": workspace["workspace_digest"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "identity_id": workspace["identity_id"],
            "seed_pair": {
                "questionnaire_source_ref": survey["source_ref"],
                "eeg_source_ref": eeg["source_ref"],
                "questionnaire_feature_digest": survey["feature_digest"],
                "eeg_feature_digest": eeg["feature_digest"],
            },
            "upstream_fusion_binding": upstream_fusion_binding,
            "derived_axes": {
                "self_report_distress_proxy": distress,
                "self_report_attention_difficulty_proxy": attention,
                "eeg_cortical_load_proxy": cortical_load,
                "eeg_alpha_suppression_proxy": alpha_suppression,
                "survey_eeg_distress_alignment": distress_alignment,
                "survey_eeg_attention_alignment": attention_alignment,
                "joint_analysis_readiness": joint_readiness,
            },
            "planned_analyses": [
                {
                    "analysis_id": "quality-control",
                    "plain_language_goal": "Check whether each source can be trusted before modeling.",
                    "agent_action": "summarize missingness, artifact burden, and digest coverage",
                    "requires_ml_expertise": False,
                },
                {
                    "analysis_id": "biodata-fusion-receipt-reconciliation",
                    "plain_language_goal": "Check that the BioData survey plus EEG fusion receipt is bound before using the workbench analysis.",
                    "agent_action": "compare upstream fusion receipt digest, fused window digest, and source-bundle digest",
                    "requires_ml_expertise": False,
                },
                {
                    "analysis_id": "survey-eeg-feature-alignment",
                    "plain_language_goal": "Compare self-report distress and attention scores with EEG load proxies.",
                    "agent_action": "compute bounded correlations or grouped contrasts from approved feature summaries",
                    "requires_ml_expertise": False,
                },
                {
                    "analysis_id": "multi-modal-expansion",
                    "plain_language_goal": "Attach fMRI and organoid summaries as additional context without changing the claim ceiling.",
                    "agent_action": "add modality-specific feature digests and rerun the source-bundle validation",
                    "requires_ml_expertise": False,
                },
            ],
            "expansion_lanes": expansion_lanes,
            "seed_survey_eeg_bound": True,
            "expansion_modalities_bound": any(lane["bound"] for lane in expansion_lanes),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "storage_policy": "cross-modal-feature-digest+axis-summary-only",
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_questionnaire_payload_stored": False,
            "raw_eeg_payload_stored": False,
            "raw_neuroimaging_payload_stored": False,
            "raw_organoid_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        analysis["seed_pair_digest"] = sha256_text(
            canonical_json(analysis["seed_pair"])
        )
        analysis["analysis_digest"] = sha256_text(
            canonical_json(self._analysis_digest_payload(analysis))
        )
        return deepcopy(analysis)

    def build_operator_guide(
        self,
        workspace: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_workspace(workspace)
        self._check_analysis(analysis)
        if workspace["workspace_digest"] != analysis["workspace_digest"]:
            raise ValueError("analysis.workspace_digest must match workspace")
        cards = [
            {
                "card_id": "import-sources",
                "title": "Import approved summaries",
                "plain_language_prompt": "Use questionnaire and EEG summaries plus the BioData fusion receipt first, then add fMRI or organoid summaries when available.",
                "agent_action": "bind_source_bundle",
                "safety_gate": "do-not-store-raw-payloads",
            },
            {
                "card_id": "check-quality",
                "title": "Check quality",
                "plain_language_prompt": "Flag missing answers, EEG artifacts, and unbound consent before analysis.",
                "agent_action": "validate_source_bundle",
                "safety_gate": "consent-and-digest-required",
            },
            {
                "card_id": "run-fusion",
                "title": "Run survey plus EEG fusion",
                "plain_language_prompt": "Compare self-report distress and attention with EEG load proxies.",
                "agent_action": "build_survey_eeg_fusion",
                "safety_gate": "feature-alignment-claim-ceiling",
            },
            {
                "card_id": "extend-modalities",
                "title": "Extend modalities",
                "plain_language_prompt": "Attach fMRI, organoid, biosensor, behavioral, omics, and future modality summaries through the same source-bundle contract.",
                "agent_action": "register_or_replace_application",
                "safety_gate": "no-consciousness-or-identity-claim",
            },
        ]
        guide = {
            "schema_version": NIW_SCHEMA_VERSION,
            "guide_ref": f"operator-guide://neuro-integration/{new_id('niw-guide')}",
            "created_at": utc_now_iso(),
            "profile_id": NIW_OPERATOR_GUIDE_PROFILE_ID,
            "workspace_ref": workspace["workspace_ref"],
            "workspace_digest": workspace["workspace_digest"],
            "analysis_ref": analysis["analysis_ref"],
            "analysis_digest": analysis["analysis_digest"],
            "guide_policy": NIW_GUIDE_POLICY,
            "operator_skill_floor": workspace["operator_profile"]["skill_level"],
            "cards": cards,
            "agent_task_templates": [
                {
                    "template_id": "coding-agent-analysis-plan",
                    "target_actor": "coding-agent",
                    "prompt_contract": "read schemas, load only approved feature summaries, emit validation and analysis receipts",
                    "output_ref": "analysis://neuro-integration/result-receipt",
                },
                {
                    "template_id": "non-ml-operator-review",
                    "target_actor": "non-ml-operator",
                    "prompt_contract": "show source status, quality flags, and next safe action in plain language",
                    "output_ref": "operator-guide://neuro-integration/plain-status",
                },
            ],
            "llm_native_workflow_bound": workspace["llm_native_workflow_bound"],
            "beginner_operator_supported": workspace["beginner_operator_supported"],
            "coding_agent_ready": workspace["coding_agent_ready"],
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_instruction_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        guide["guide_digest"] = sha256_text(
            canonical_json(self._guide_digest_payload(guide))
        )
        return deepcopy(guide)

    def build_application_replacement_plan(
        self,
        app_receipts: Sequence[Dict[str, Any]],
        source_bundle: Dict[str, Any],
        workspace: Dict[str, Any],
        operator_guide: Dict[str, Any],
    ) -> Dict[str, Any]:
        apps = [self._check_app_receipt(app_receipt) for app_receipt in app_receipts]
        if not apps:
            raise ValueError("app_receipts must not be empty")
        self._check_source_bundle(source_bundle)
        self._check_workspace(workspace)
        self._check_operator_guide(operator_guide)
        if workspace["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("workspace.source_bundle_digest must match source bundle")
        if operator_guide["workspace_digest"] != workspace["workspace_digest"]:
            raise ValueError("operator_guide.workspace_digest must match workspace")

        source_types = list(source_bundle["source_types"])
        source_families = dict(source_bundle["source_families"])
        app_digests = [app["app_digest"] for app in apps]
        app_refs = [app["app_ref"] for app in apps]
        lane_coverage = self._build_lane_coverage(apps, source_types)
        source_type_coverage = self._build_source_type_coverage(apps, source_types)
        all_required_lanes_bound = all(item["bound"] for item in lane_coverage)
        source_type_lane_coverage_bound = all(
            item["covered"] for item in source_type_coverage
        )
        plan = {
            "schema_version": NIW_SCHEMA_VERSION,
            "replacement_plan_ref": (
                f"replacement-plan://neuro-integration/{new_id('niw-replacement-plan')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_REPLACEMENT_PLAN_PROFILE_ID,
            "workspace_ref": workspace["workspace_ref"],
            "workspace_digest": workspace["workspace_digest"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "operator_guide_ref": operator_guide["guide_ref"],
            "operator_guide_digest": operator_guide["guide_digest"],
            "app_refs": app_refs,
            "app_digests": app_digests,
            "source_types": source_types,
            "source_families": source_families,
            "required_replacement_lanes": list(NIW_REQUIRED_REPLACEMENT_LANES),
            "lane_coverage": lane_coverage,
            "source_type_coverage": source_type_coverage,
            "coverage_summary": {
                "app_count": len(apps),
                "source_type_count": len(source_types),
                "source_family_count": len(set(source_families.values())),
                "required_replacement_lane_count": len(NIW_REQUIRED_REPLACEMENT_LANES),
                "covered_replacement_lane_count": sum(
                    1 for item in lane_coverage if item["bound"]
                ),
                "covered_source_type_count": sum(
                    1 for item in source_type_coverage if item["covered"]
                ),
            },
            "all_required_lanes_bound": all_required_lanes_bound,
            "source_type_lane_coverage_bound": source_type_lane_coverage_bound,
            "replacement_plan_bound": (
                all_required_lanes_bound
                and source_type_lane_coverage_bound
                and workspace["replacement_lanes_bound"]
            ),
            "llm_native_workflow_bound": workspace["llm_native_workflow_bound"],
            "beginner_operator_supported": workspace["beginner_operator_supported"],
            "coding_agent_ready": workspace["coding_agent_ready"],
            "operator_handoffs": [
                {
                    "target_actor": "non-ml-operator",
                    "guide_ref": operator_guide["guide_ref"],
                    "guide_digest": operator_guide["guide_digest"],
                    "handoff_policy": "plain-language-card-review",
                    "requires_ml_expertise": False,
                },
                {
                    "target_actor": "coding-agent",
                    "guide_ref": operator_guide["guide_ref"],
                    "guide_digest": operator_guide["guide_digest"],
                    "handoff_policy": "schema-bound-task-template",
                    "requires_ml_expertise": False,
                },
            ],
            "storage_policy": NIW_REPLACEMENT_PLAN_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_app_payload_stored": False,
            "raw_source_payload_stored": False,
            "raw_operator_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        plan["replacement_plan_digest"] = sha256_text(
            canonical_json(self._replacement_plan_digest_payload(plan))
        )
        return deepcopy(plan)

    def bind_application_connector_bundle(
        self,
        app_receipts: Sequence[Dict[str, Any]],
        replacement_plan: Dict[str, Any],
        connector_manifests: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        apps = [self._check_app_receipt(app_receipt) for app_receipt in app_receipts]
        if not apps:
            raise ValueError("app_receipts must not be empty")
        self._check_replacement_plan(replacement_plan)
        if not connector_manifests:
            raise ValueError("connector_manifests must not be empty")

        app_digests = [app["app_digest"] for app in apps]
        if replacement_plan.get("app_digests") != app_digests:
            raise ValueError("replacement_plan.app_digests must match app_receipts")
        app_by_ref = {app["app_ref"]: app for app in apps}
        connectors = [
            self._normalize_connector_manifest(connector_manifest, app_by_ref)
            for connector_manifest in connector_manifests
        ]
        connector_app_refs = {connector["app_ref"] for connector in connectors}
        all_apps_connected = all(
            app_ref in connector_app_refs for app_ref in replacement_plan["app_refs"]
        )
        source_types = list(replacement_plan["source_types"])
        lane_coverage = self._build_connector_lane_coverage(
            connectors,
            source_types,
        )
        source_type_coverage = self._build_connector_source_type_coverage(
            connectors,
            source_types,
        )
        required_lanes_connected = all(item["bound"] for item in lane_coverage)
        source_types_connector_bound = all(item["covered"] for item in source_type_coverage)
        llm_tooling_bound = all(connector["llm_tool_bound"] for connector in connectors)
        operator_safe_mode_bound = all(
            connector["operator_safe_mode"] for connector in connectors
        )
        connector_digests = [connector["connector_digest"] for connector in connectors]
        connector_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_CONNECTOR_BUNDLE_PROFILE_ID,
                    "connector_digests": connector_digests,
                    "replacement_plan_digest": replacement_plan[
                        "replacement_plan_digest"
                    ],
                }
            )
        )
        bundle = {
            "schema_version": NIW_SCHEMA_VERSION,
            "connector_bundle_ref": (
                f"connector-bundle://neuro-integration/{new_id('niw-connector-bundle')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_CONNECTOR_BUNDLE_PROFILE_ID,
            "replacement_plan_ref": replacement_plan["replacement_plan_ref"],
            "replacement_plan_digest": replacement_plan["replacement_plan_digest"],
            "workspace_digest": replacement_plan["workspace_digest"],
            "source_bundle_digest": replacement_plan["source_bundle_digest"],
            "operator_guide_digest": replacement_plan["operator_guide_digest"],
            "app_refs": list(replacement_plan["app_refs"]),
            "app_digests": app_digests,
            "source_types": source_types,
            "required_replacement_lanes": list(NIW_REQUIRED_REPLACEMENT_LANES),
            "connector_count": len(connectors),
            "connectors": connectors,
            "connector_digests": connector_digests,
            "connector_digest_set": connector_digest_set,
            "lane_connector_coverage": lane_coverage,
            "source_type_connector_coverage": source_type_coverage,
            "all_apps_connected": all_apps_connected,
            "required_lanes_connected": required_lanes_connected,
            "source_types_connector_bound": source_types_connector_bound,
            "llm_tooling_bound": llm_tooling_bound,
            "operator_safe_mode_bound": operator_safe_mode_bound,
            "connector_bundle_bound": (
                all_apps_connected
                and required_lanes_connected
                and source_types_connector_bound
                and llm_tooling_bound
                and operator_safe_mode_bound
                and replacement_plan["replacement_plan_bound"]
            ),
            "storage_policy": NIW_CONNECTOR_BUNDLE_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_connector_payload_stored": False,
            "raw_credential_payload_stored": False,
            "raw_endpoint_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        bundle["connector_bundle_digest"] = sha256_text(
            canonical_json(self._connector_bundle_digest_payload(bundle))
        )
        return deepcopy(bundle)

    def validate_integration_bundle(
        self,
        app_receipts: Sequence[Dict[str, Any]],
        source_bundle: Dict[str, Any],
        workspace: Dict[str, Any],
        analysis: Dict[str, Any],
        operator_guide: Dict[str, Any],
        replacement_plan: Dict[str, Any] | None = None,
        connector_bundle: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        normalized_apps: List[Dict[str, Any]] = []
        for app_receipt in app_receipts:
            try:
                normalized_apps.append(self._check_app_receipt(app_receipt))
            except ValueError as exc:
                errors.append(str(exc))
        try:
            self._check_source_bundle(source_bundle)
        except ValueError as exc:
            errors.append(str(exc))
        try:
            self._check_workspace(workspace)
        except ValueError as exc:
            errors.append(str(exc))
        try:
            self._check_analysis(analysis)
        except ValueError as exc:
            errors.append(str(exc))
        try:
            self._check_operator_guide(operator_guide)
        except ValueError as exc:
            errors.append(str(exc))
        if replacement_plan is not None:
            try:
                self._check_replacement_plan(replacement_plan)
            except ValueError as exc:
                errors.append(str(exc))
        if connector_bundle is not None:
            try:
                self._check_connector_bundle(connector_bundle)
            except ValueError as exc:
                errors.append(str(exc))
            if replacement_plan is None:
                errors.append("connector_bundle requires replacement_plan")

        app_registry_digest_bound = all(
            app.get("app_digest") == sha256_text(canonical_json(self._app_digest_payload(app)))
            for app in normalized_apps
        )
        source_bundle_digest_bound = source_bundle.get("source_bundle_digest") == sha256_text(
            canonical_json(self._source_bundle_digest_payload(source_bundle))
        )
        workspace_digest_bound = workspace.get("workspace_digest") == sha256_text(
            canonical_json(self._workspace_digest_payload(workspace))
        )
        analysis_digest_bound = analysis.get("analysis_digest") == sha256_text(
            canonical_json(self._analysis_digest_payload(analysis))
        )
        guide_digest_bound = operator_guide.get("guide_digest") == sha256_text(
            canonical_json(self._guide_digest_payload(operator_guide))
        )
        seed_survey_eeg_bound = (
            source_bundle.get("seed_survey_eeg_bound") is True
            and analysis.get("seed_survey_eeg_bound") is True
        )
        expansion_modalities_bound = (
            source_bundle.get("expansion_modalities_bound") is True
            and analysis.get("expansion_modalities_bound") is True
        )
        replacement_lanes_bound = workspace.get("replacement_lanes_bound") is True
        llm_native_workflow_bound = (
            workspace.get("llm_native_workflow_bound") is True
            and operator_guide.get("llm_native_workflow_bound") is True
        )
        beginner_operator_supported = (
            workspace.get("beginner_operator_supported") is True
            and operator_guide.get("beginner_operator_supported") is True
        )
        coding_agent_ready = (
            workspace.get("coding_agent_ready") is True
            and operator_guide.get("coding_agent_ready") is True
        )
        claim_ceiling_bound = all(
            artifact.get("claim_ceiling") == NIW_CLAIM_CEILING
            for artifact in (workspace, analysis, operator_guide)
        )
        upstream_receipt_bindings = source_bundle.get("upstream_receipt_bindings", [])
        upstream_receipt_digests = {
            binding.get("fusion_receipt_digest")
            for binding in upstream_receipt_bindings
            if isinstance(binding, dict)
        }
        upstream_fusion_binding = analysis.get("upstream_fusion_binding", {})
        survey_eeg_fusion_receipt_bound = (
            source_bundle.get("survey_eeg_fusion_receipt_bound") is True
            and isinstance(upstream_fusion_binding, dict)
            and upstream_fusion_binding.get("bound") is True
            and upstream_fusion_binding.get("fusion_receipt_digest")
            in upstream_receipt_digests
        )
        upstream_receipt_payload_redacted = all(
            isinstance(binding, dict) and binding.get("raw_payload_stored") is False
            for binding in upstream_receipt_bindings
        )
        raw_payload_redacted = all(
            artifact.get(field_name) is False
            for artifact in (source_bundle, workspace, analysis, operator_guide)
            for field_name in artifact
            if field_name.startswith("raw_")
        )
        no_diagnosis_or_identity_claim = all(
            artifact.get("clinical_diagnosis_claimed", False) is False
            and artifact.get("consciousness_reproduction_claimed") is False
            and artifact.get("identity_replacement_claimed") is False
            for artifact in (source_bundle, workspace, analysis, operator_guide)
        )
        replacement_plan_checks: Dict[str, bool] = {}
        if replacement_plan is not None:
            replacement_plan_digest_bound = (
                replacement_plan.get("replacement_plan_digest")
                == sha256_text(
                    canonical_json(
                        self._replacement_plan_digest_payload(replacement_plan)
                    )
                )
            )
            app_digest_set = [app["app_digest"] for app in normalized_apps]
            replacement_plan_checks = {
                "replacement_plan_digest_bound": replacement_plan_digest_bound,
                "application_replacement_plan_bound": (
                    replacement_plan.get("replacement_plan_bound") is True
                    and replacement_plan.get("workspace_digest")
                    == workspace.get("workspace_digest")
                    and replacement_plan.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and replacement_plan.get("operator_guide_digest")
                    == operator_guide.get("guide_digest")
                    and replacement_plan.get("app_digests") == app_digest_set
                ),
                "source_type_lane_coverage_bound": (
                    replacement_plan.get("source_type_lane_coverage_bound") is True
                ),
                "replacement_plan_payload_redacted": all(
                    replacement_plan.get(field_name) is False
                    for field_name in replacement_plan
                    if field_name.startswith("raw_")
                ),
            }
        connector_bundle_checks: Dict[str, bool] = {}
        if connector_bundle is not None:
            connector_bundle_digest_bound = (
                connector_bundle.get("connector_bundle_digest")
                == sha256_text(
                    canonical_json(
                        self._connector_bundle_digest_payload(connector_bundle)
                    )
                )
            )
            expected_replacement_digest = (
                replacement_plan.get("replacement_plan_digest")
                if replacement_plan is not None
                else ""
            )
            connector_bundle_checks = {
                "connector_bundle_digest_bound": connector_bundle_digest_bound,
                "application_connector_bundle_bound": (
                    connector_bundle.get("connector_bundle_bound") is True
                    and connector_bundle.get("replacement_plan_digest")
                    == expected_replacement_digest
                    and connector_bundle.get("app_digests")
                    == [app["app_digest"] for app in normalized_apps]
                ),
                "connector_source_type_coverage_bound": (
                    connector_bundle.get("source_types_connector_bound") is True
                ),
                "connector_payload_redacted": self._connector_payload_redacted(
                    connector_bundle
                ),
            }

        checks = {
            "app_registry_digest_bound": app_registry_digest_bound,
            "source_bundle_digest_bound": source_bundle_digest_bound,
            "workspace_digest_bound": workspace_digest_bound,
            "analysis_digest_bound": analysis_digest_bound,
            "operator_guide_digest_bound": guide_digest_bound,
            "seed_survey_eeg_bound": seed_survey_eeg_bound,
            "expansion_modalities_bound": expansion_modalities_bound,
            "replacement_lanes_bound": replacement_lanes_bound,
            "llm_native_workflow_bound": llm_native_workflow_bound,
            "beginner_operator_supported": beginner_operator_supported,
            "coding_agent_ready": coding_agent_ready,
            "survey_eeg_fusion_receipt_bound": survey_eeg_fusion_receipt_bound,
            "upstream_receipt_payload_redacted": upstream_receipt_payload_redacted,
            "claim_ceiling_bound": claim_ceiling_bound,
            "raw_payload_redacted": raw_payload_redacted,
            "no_diagnosis_or_identity_claim": no_diagnosis_or_identity_claim,
            **replacement_plan_checks,
            **connector_bundle_checks,
        }
        for name, ok in checks.items():
            if not ok:
                errors.append(f"{name} failed")

        return {
            "ok": not errors,
            "errors": errors,
            **checks,
            "source_count": source_bundle.get("source_count", 0),
            "upstream_receipt_count": source_bundle.get("upstream_receipt_count", 0),
            "app_count": len(app_receipts),
            "replacement_lane_count": len(workspace.get("replacement_lanes", [])),
            "covered_source_type_count": (
                replacement_plan.get("coverage_summary", {}).get(
                    "covered_source_type_count",
                    0,
                )
                if replacement_plan is not None
                else 0
            ),
            "connector_count": (
                connector_bundle.get("connector_count", 0)
                if connector_bundle is not None
                else 0
            ),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_questionnaire_payload_stored": False,
            "raw_eeg_payload_stored": False,
            "raw_neuroimaging_payload_stored": False,
            "raw_organoid_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }

    def _normalize_upstream_receipt(
        self,
        receipt: Dict[str, Any],
        identity_id: str,
    ) -> Dict[str, Any]:
        if not isinstance(receipt, dict):
            raise ValueError("upstream_receipt must be a mapping")
        if receipt.get("profile_id") != NIW_BIODATA_SURVEY_EEG_FUSION_PROFILE_ID:
            raise ValueError("upstream_receipt.profile_id is not supported")
        if receipt.get("identity_id") != identity_id:
            raise ValueError("upstream_receipt.identity_id must match identity_id")
        if receipt.get("fusion_status") != "bound":
            raise ValueError("upstream_receipt.fusion_status must be bound")
        if receipt.get("claim_ceiling") != NIW_BIODATA_SURVEY_EEG_FUSION_CLAIM_CEILING:
            raise ValueError("upstream_receipt.claim_ceiling mismatch")
        if receipt.get("operator_accessibility_bound") is not True:
            raise ValueError("upstream_receipt.operator_accessibility_bound must be true")
        for field_name in (
            "raw_survey_response_payload_stored",
            "raw_eeg_samples_stored",
            "raw_dataset_payload_stored",
            "raw_latent_payload_stored",
            "raw_fusion_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
            "diagnosis_claimed",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if receipt.get(field_name) is not False:
                raise ValueError(f"upstream_receipt.{field_name} must be false")
        self._require_non_empty_string(receipt.get("fusion_ref"), "upstream_receipt.fusion_ref")
        axis_summary = receipt.get("fusion_axis_summary")
        if not isinstance(axis_summary, dict) or not axis_summary:
            raise ValueError("upstream_receipt.fusion_axis_summary must be non-empty")
        fusion_confidence = axis_summary.get("fusion_confidence")
        if not isinstance(fusion_confidence, (int, float)):
            raise ValueError("upstream_receipt.fusion_axis_summary.fusion_confidence must be numeric")
        binding = {
            "receipt_role": NIW_BIODATA_FUSION_BINDING_ROLE,
            "profile_id": NIW_BIODATA_SURVEY_EEG_FUSION_PROFILE_ID,
            "fusion_ref": str(receipt["fusion_ref"]),
            "fusion_receipt_digest": self._require_sha256_digest(
                receipt.get("fusion_receipt_digest"),
                "upstream_receipt.fusion_receipt_digest",
            ),
            "fused_window_digest": self._require_sha256_digest(
                receipt.get("fused_window_digest"),
                "upstream_receipt.fused_window_digest",
            ),
            "dataset_adapter_receipt_digest": self._require_sha256_digest(
                receipt.get("dataset_adapter_receipt_digest"),
                "upstream_receipt.dataset_adapter_receipt_digest",
            ),
            "latent_digest": self._require_sha256_digest(
                receipt.get("latent_digest"),
                "upstream_receipt.latent_digest",
            ),
            "source_feature_digest": self._require_sha256_digest(
                receipt.get("source_feature_digest"),
                "upstream_receipt.source_feature_digest",
            ),
            "eeg_feature_digest": self._require_sha256_digest(
                receipt.get("eeg_feature_digest"),
                "upstream_receipt.eeg_feature_digest",
            ),
            "survey_score_digest": self._require_sha256_digest(
                receipt.get("survey_score_digest"),
                "upstream_receipt.survey_score_digest",
            ),
            "fusion_axis_summary_digest": sha256_text(canonical_json(axis_summary)),
            "fusion_confidence": self._round_score(float(fusion_confidence)),
            "bound_source_types": list(NIW_SEED_SOURCE_TYPES),
            "fusion_status": "bound",
            "operator_accessibility_bound": True,
            "claim_ceiling": NIW_BIODATA_SURVEY_EEG_FUSION_CLAIM_CEILING,
            "raw_payload_stored": False,
        }
        return binding

    def _build_lane_coverage(
        self,
        apps: Sequence[Dict[str, Any]],
        source_types: Sequence[str],
    ) -> List[Dict[str, Any]]:
        lane_coverage: List[Dict[str, Any]] = []
        for lane in NIW_REQUIRED_REPLACEMENT_LANES:
            lane_apps = [app for app in apps if lane in app["replacement_lanes"]]
            supported_source_types = sorted(
                {
                    source_type
                    for app in lane_apps
                    for source_type in app["supported_source_types"]
                    if source_type in source_types
                }
            )
            missing_source_types = [
                source_type
                for source_type in source_types
                if source_type not in supported_source_types
            ]
            lane_coverage.append(
                {
                    "replacement_lane": lane,
                    "app_refs": [app["app_ref"] for app in lane_apps],
                    "app_digests": [app["app_digest"] for app in lane_apps],
                    "source_types_covered": supported_source_types,
                    "source_families_covered": sorted(
                        {self._source_family(source_type) for source_type in supported_source_types}
                    ),
                    "missing_source_types": missing_source_types,
                    "operator_skill_floors": sorted(
                        {app["operator_skill_floor"] for app in lane_apps}
                    ),
                    "llm_native_app_count": sum(1 for app in lane_apps if app["llm_native"]),
                    "beginner_safe_app_count": sum(
                        1 for app in lane_apps if app["beginner_safe_mode"]
                    ),
                    "bound": bool(lane_apps) and not missing_source_types,
                }
            )
        return lane_coverage

    def _build_source_type_coverage(
        self,
        apps: Sequence[Dict[str, Any]],
        source_types: Sequence[str],
    ) -> List[Dict[str, Any]]:
        coverage: List[Dict[str, Any]] = []
        for source_type in source_types:
            lane_refs: Dict[str, List[str]] = {}
            lane_digests: Dict[str, List[str]] = {}
            missing_lanes: List[str] = []
            for lane in NIW_REQUIRED_REPLACEMENT_LANES:
                lane_apps = [
                    app
                    for app in apps
                    if lane in app["replacement_lanes"]
                    and source_type in app["supported_source_types"]
                ]
                lane_refs[lane] = [app["app_ref"] for app in lane_apps]
                lane_digests[lane] = [app["app_digest"] for app in lane_apps]
                if not lane_apps:
                    missing_lanes.append(lane)
            coverage.append(
                {
                    "source_type": source_type,
                    "source_family": self._source_family(source_type),
                    "lane_app_refs": lane_refs,
                    "lane_app_digests": lane_digests,
                    "missing_lanes": missing_lanes,
                    "covered": not missing_lanes,
                }
            )
        return coverage

    def _normalize_connector_manifest(
        self,
        connector_manifest: Dict[str, Any],
        app_by_ref: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(connector_manifest, dict):
            raise ValueError("connector_manifest must be a mapping")
        app_ref = str(connector_manifest.get("app_ref", "")).strip()
        if app_ref not in app_by_ref:
            raise ValueError("connector_manifest.app_ref must reference an app receipt")
        app = app_by_ref[app_ref]
        connector_kind = self._normalize_connector_kind(
            connector_manifest.get("connector_kind")
        )
        protocol = self._normalize_connector_protocol(
            connector_manifest.get("protocol")
        )
        supported_source_types = self._normalize_source_types(
            connector_manifest.get("supported_source_types", []),
            "connector_manifest.supported_source_types",
        )
        unsupported = [
            source_type
            for source_type in supported_source_types
            if source_type not in app["supported_source_types"]
        ]
        if unsupported:
            raise ValueError(
                "connector_manifest.supported_source_types must be supported by app: "
                f"{unsupported}"
            )
        for field_name in (
            "endpoint_ref",
            "credential_ref",
            "permission_ref",
            "data_contract_ref",
            "llm_tool_ref",
            "operator_label",
        ):
            self._require_non_empty_string(
                connector_manifest.get(field_name),
                f"connector_manifest.{field_name}",
            )
        dry_run_supported = bool(connector_manifest.get("dry_run_supported", True))
        credential_scope_digest = sha256_text(
            canonical_json(
                {
                    "credential_ref": connector_manifest["credential_ref"],
                    "permission_ref": connector_manifest["permission_ref"],
                    "data_contract_ref": connector_manifest["data_contract_ref"],
                }
            )
        )
        connector = {
            "schema_version": NIW_SCHEMA_VERSION,
            "connector_ref": (
                f"connector://neuro-integration/{new_id('niw-connector')}"
            ),
            "connector_profile_id": NIW_CONNECTOR_PROFILE_ID,
            "app_ref": app["app_ref"],
            "app_digest": app["app_digest"],
            "app_kind": app["app_kind"],
            "replacement_lanes": list(app["replacement_lanes"]),
            "connector_kind": connector_kind,
            "protocol": protocol,
            "endpoint_ref": str(connector_manifest["endpoint_ref"]),
            "credential_ref": str(connector_manifest["credential_ref"]),
            "permission_ref": str(connector_manifest["permission_ref"]),
            "data_contract_ref": str(connector_manifest["data_contract_ref"]),
            "llm_tool_ref": str(connector_manifest["llm_tool_ref"]),
            "operator_label": str(connector_manifest["operator_label"]),
            "supported_source_types": supported_source_types,
            "supported_source_families": {
                source_type: self._source_family(source_type)
                for source_type in supported_source_types
            },
            "credential_scope_digest": credential_scope_digest,
            "dry_run_supported": dry_run_supported,
            "llm_tool_bound": True,
            "operator_safe_mode": app["beginner_safe_mode"] or app["llm_native"],
            "raw_connector_payload_stored": False,
            "raw_credential_payload_stored": False,
            "raw_endpoint_payload_stored": False,
        }
        connector["connector_digest"] = sha256_text(
            canonical_json(self._connector_digest_payload(connector))
        )
        return connector

    def _build_connector_lane_coverage(
        self,
        connectors: Sequence[Dict[str, Any]],
        source_types: Sequence[str],
    ) -> List[Dict[str, Any]]:
        coverage: List[Dict[str, Any]] = []
        for lane in NIW_REQUIRED_REPLACEMENT_LANES:
            lane_connectors = [
                connector
                for connector in connectors
                if lane in connector["replacement_lanes"]
            ]
            supported_source_types = sorted(
                {
                    source_type
                    for connector in lane_connectors
                    for source_type in connector["supported_source_types"]
                    if source_type in source_types
                }
            )
            missing_source_types = [
                source_type
                for source_type in source_types
                if source_type not in supported_source_types
            ]
            coverage.append(
                {
                    "replacement_lane": lane,
                    "connector_refs": [
                        connector["connector_ref"] for connector in lane_connectors
                    ],
                    "connector_digests": [
                        connector["connector_digest"] for connector in lane_connectors
                    ],
                    "source_types_covered": supported_source_types,
                    "missing_source_types": missing_source_types,
                    "bound": bool(lane_connectors) and not missing_source_types,
                }
            )
        return coverage

    def _build_connector_source_type_coverage(
        self,
        connectors: Sequence[Dict[str, Any]],
        source_types: Sequence[str],
    ) -> List[Dict[str, Any]]:
        coverage: List[Dict[str, Any]] = []
        for source_type in source_types:
            lane_connector_refs: Dict[str, List[str]] = {}
            lane_connector_digests: Dict[str, List[str]] = {}
            missing_lanes: List[str] = []
            for lane in NIW_REQUIRED_REPLACEMENT_LANES:
                lane_connectors = [
                    connector
                    for connector in connectors
                    if lane in connector["replacement_lanes"]
                    and source_type in connector["supported_source_types"]
                ]
                lane_connector_refs[lane] = [
                    connector["connector_ref"] for connector in lane_connectors
                ]
                lane_connector_digests[lane] = [
                    connector["connector_digest"] for connector in lane_connectors
                ]
                if not lane_connectors:
                    missing_lanes.append(lane)
            coverage.append(
                {
                    "source_type": source_type,
                    "source_family": self._source_family(source_type),
                    "lane_connector_refs": lane_connector_refs,
                    "lane_connector_digests": lane_connector_digests,
                    "missing_lanes": missing_lanes,
                    "covered": not missing_lanes,
                }
            )
        return coverage

    def _normalize_source_manifest(self, source_manifest: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(source_manifest, dict):
            raise ValueError("source_manifest must be a mapping")
        source_type = self._normalize_source_type(
            source_manifest.get("source_type"),
            "source_type",
        )
        for field_name in (
            "source_ref",
            "app_ref",
            "participant_ref",
            "consent_ref",
            "license_ref",
            "feature_summary_ref",
        ):
            self._require_non_empty_string(source_manifest.get(field_name), field_name)
        feature_summary = source_manifest.get("feature_summary")
        if not isinstance(feature_summary, dict) or not feature_summary:
            raise ValueError("feature_summary must be a non-empty mapping")
        feature_digest = sha256_text(canonical_json(feature_summary))
        axes = self._derive_analysis_axes(source_type, feature_summary)
        return {
            "source_type": source_type,
            "source_family": self._source_family(source_type),
            "source_ref": str(source_manifest["source_ref"]),
            "app_ref": str(source_manifest["app_ref"]),
            "participant_ref": str(source_manifest["participant_ref"]),
            "consent_ref": str(source_manifest["consent_ref"]),
            "license_ref": str(source_manifest["license_ref"]),
            "feature_summary_ref": str(source_manifest["feature_summary_ref"]),
            "feature_digest": feature_digest,
            "feature_name_digest": sha256_text(
                canonical_json({"feature_names": sorted(feature_summary)})
            ),
            "numeric_feature_count": sum(
                1 for value in feature_summary.values() if isinstance(value, (int, float))
            ),
            "string_feature_count": sum(
                1 for value in feature_summary.values() if isinstance(value, str)
            ),
            "analysis_axes": axes,
            "construct_coverage": sorted(axes),
            "storage_policy": NIW_SOURCE_STORAGE_POLICY,
            "raw_payload_stored": False,
        }

    def _derive_analysis_axes(
        self,
        source_type: str,
        feature_summary: Dict[str, Any],
    ) -> Dict[str, float]:
        if source_type == "questionnaire":
            stress = self._bounded_feature(feature_summary, "stress_score", 0.5)
            anxiety = self._bounded_feature(feature_summary, "anxiety_score", 0.5)
            fatigue = self._bounded_feature(feature_summary, "fatigue_score", 0.5)
            attention = self._bounded_feature(
                feature_summary,
                "attention_difficulty_score",
                0.5,
            )
            sleep_quality = self._bounded_feature(feature_summary, "sleep_quality_score", 0.5)
            mood_valence = self._bounded_feature(feature_summary, "mood_valence_score", 0.5)
            return {
                "distress_proxy": self._round_score((stress + anxiety + fatigue) / 3.0),
                "attention_difficulty_proxy": self._round_score(attention),
                "sleep_pressure_proxy": self._round_score(1.0 - sleep_quality),
                "valence_proxy": self._round_score(mood_valence),
            }
        if source_type == "eeg":
            alpha = self._bounded_feature(feature_summary, "alpha_power", 0.4)
            theta = self._bounded_feature(feature_summary, "theta_power", 0.3)
            beta = self._bounded_feature(feature_summary, "beta_power", 0.3)
            artifact = self._bounded_feature(feature_summary, "artifact_rate", 0.1)
            theta_beta_ratio = round(theta / max(beta, 0.001), 3)
            cortical_load = self._round_score((theta_beta_ratio / 3.0 + beta + artifact) / 3.0)
            return {
                "alpha_suppression_proxy": self._round_score(1.0 - alpha),
                "theta_beta_ratio": theta_beta_ratio,
                "cortical_load_proxy": cortical_load,
                "artifact_burden_proxy": self._round_score(artifact),
            }
        if source_type == "fmri_bold":
            bold_change = self._bounded_feature(feature_summary, "bold_percent_change", 0.2)
            network_coupling = self._bounded_feature(feature_summary, "network_coupling", 0.5)
            return {
                "neurovascular_activation_proxy": self._round_score(bold_change),
                "network_context_proxy": self._round_score(network_coupling),
            }
        if source_type == "brain_organoid":
            burst_rate = self._bounded_feature(feature_summary, "network_burst_rate", 0.4)
            synchrony = self._bounded_feature(feature_summary, "synchrony_index", 0.4)
            viability = self._bounded_feature(feature_summary, "viability_score", 0.8)
            return {
                "in_vitro_activity_proxy": self._round_score((burst_rate + synchrony) / 2.0),
                "organoid_viability_proxy": self._round_score(viability),
            }
        numeric_values = [
            float(value) for value in feature_summary.values() if isinstance(value, (int, float))
        ]
        average = sum(numeric_values) / len(numeric_values) if numeric_values else 0.5
        return {"generic_signal_intensity_proxy": self._round_score(average)}

    def _build_expansion_lanes(self, source_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        sources_by_type = {source["source_type"]: source for source in source_bundle["sources"]}
        lanes = []
        for source_type in NIW_EXPANSION_SOURCE_TYPES:
            source = sources_by_type.get(source_type)
            if source is None:
                lanes.append(
                    {
                        "source_type": source_type,
                        "source_family": self._source_family(source_type),
                        "integration_role": "future-expansion",
                        "source_digest": "",
                        "bound": False,
                    }
                )
                continue
            role = (
                "neurovascular-context"
                if source_type == "fmri_bold"
                else "in-vitro-neural-tissue-context"
            )
            lanes.append(
                {
                    "source_type": source_type,
                    "source_family": source["source_family"],
                    "integration_role": role,
                    "source_digest": source["feature_digest"],
                    "bound": True,
                }
            )
        return lanes

    def _build_upstream_fusion_binding(
        self,
        source_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        for binding in source_bundle.get("upstream_receipt_bindings", []):
            if binding.get("receipt_role") == NIW_BIODATA_FUSION_BINDING_ROLE:
                return {
                    "bound": True,
                    "receipt_role": binding["receipt_role"],
                    "profile_id": binding["profile_id"],
                    "fusion_ref": binding["fusion_ref"],
                    "fusion_receipt_digest": binding["fusion_receipt_digest"],
                    "fused_window_digest": binding["fused_window_digest"],
                    "fusion_axis_summary_digest": binding[
                        "fusion_axis_summary_digest"
                    ],
                    "fusion_confidence": binding["fusion_confidence"],
                    "bound_source_types": list(binding["bound_source_types"]),
                    "fusion_status": binding["fusion_status"],
                    "operator_accessibility_bound": binding[
                        "operator_accessibility_bound"
                    ],
                    "claim_ceiling": binding["claim_ceiling"],
                    "raw_payload_stored": False,
                }
        return self._empty_upstream_fusion_binding()

    def _empty_upstream_fusion_binding(self) -> Dict[str, Any]:
        return {
            "bound": False,
            "receipt_role": NIW_BIODATA_FUSION_BINDING_ROLE,
            "profile_id": NIW_BIODATA_SURVEY_EEG_FUSION_PROFILE_ID,
            "fusion_ref": "",
            "fusion_receipt_digest": "",
            "fused_window_digest": "",
            "fusion_axis_summary_digest": "",
            "fusion_confidence": 0.0,
            "bound_source_types": list(NIW_SEED_SOURCE_TYPES),
            "fusion_status": "not-bound",
            "operator_accessibility_bound": False,
            "claim_ceiling": NIW_BIODATA_SURVEY_EEG_FUSION_CLAIM_CEILING,
            "raw_payload_stored": False,
        }

    def _check_app_receipt(self, app_receipt: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(app_receipt, dict):
            raise ValueError("app_receipt must be a mapping")
        if app_receipt.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("app_receipt.schema_version mismatch")
        if app_receipt.get("profile_id") != NIW_APP_REGISTRY_PROFILE_ID:
            raise ValueError("app_receipt.profile_id mismatch")
        expected_digest = sha256_text(canonical_json(self._app_digest_payload(app_receipt)))
        if app_receipt.get("app_digest") != expected_digest:
            raise ValueError("app_receipt.app_digest mismatch")
        return deepcopy(app_receipt)

    def _check_source_bundle(self, source_bundle: Dict[str, Any]) -> None:
        if not isinstance(source_bundle, dict):
            raise ValueError("source_bundle must be a mapping")
        if source_bundle.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("source_bundle.schema_version mismatch")
        if source_bundle.get("profile_id") != NIW_SOURCE_BUNDLE_PROFILE_ID:
            raise ValueError("source_bundle.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._source_bundle_digest_payload(source_bundle))
        )
        if source_bundle.get("source_bundle_digest") != expected_digest:
            raise ValueError("source_bundle.source_bundle_digest mismatch")
        bindings = source_bundle.get("upstream_receipt_bindings")
        if not isinstance(bindings, list):
            raise ValueError("source_bundle.upstream_receipt_bindings must be a list")
        if any(not isinstance(binding, dict) for binding in bindings):
            raise ValueError("source_bundle.upstream_receipt_bindings must contain mappings")
        if source_bundle.get("upstream_receipt_count") != len(bindings):
            raise ValueError("source_bundle.upstream_receipt_count mismatch")
        expected_upstream_digest_set = self._upstream_receipt_digest_set(bindings)
        if source_bundle.get("upstream_receipt_digest_set") != expected_upstream_digest_set:
            raise ValueError("source_bundle.upstream_receipt_digest_set mismatch")
        expected_fusion_bound = any(
            binding.get("receipt_role") == NIW_BIODATA_FUSION_BINDING_ROLE
            for binding in bindings
            if isinstance(binding, dict)
        )
        if source_bundle.get("survey_eeg_fusion_receipt_bound") != expected_fusion_bound:
            raise ValueError("source_bundle.survey_eeg_fusion_receipt_bound mismatch")

    def _check_workspace(self, workspace: Dict[str, Any]) -> None:
        if not isinstance(workspace, dict):
            raise ValueError("workspace must be a mapping")
        if workspace.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("workspace.schema_version mismatch")
        if workspace.get("profile_id") != NIW_WORKSPACE_PROFILE_ID:
            raise ValueError("workspace.profile_id mismatch")
        expected_digest = sha256_text(canonical_json(self._workspace_digest_payload(workspace)))
        if workspace.get("workspace_digest") != expected_digest:
            raise ValueError("workspace.workspace_digest mismatch")

    def _check_analysis(self, analysis: Dict[str, Any]) -> None:
        if not isinstance(analysis, dict):
            raise ValueError("analysis must be a mapping")
        if analysis.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("analysis.schema_version mismatch")
        if analysis.get("profile_id") != NIW_ANALYSIS_PROFILE_ID:
            raise ValueError("analysis.profile_id mismatch")
        expected_digest = sha256_text(canonical_json(self._analysis_digest_payload(analysis)))
        if analysis.get("analysis_digest") != expected_digest:
            raise ValueError("analysis.analysis_digest mismatch")

    def _check_operator_guide(self, guide: Dict[str, Any]) -> None:
        if not isinstance(guide, dict):
            raise ValueError("operator_guide must be a mapping")
        if guide.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("operator_guide.schema_version mismatch")
        if guide.get("profile_id") != NIW_OPERATOR_GUIDE_PROFILE_ID:
            raise ValueError("operator_guide.profile_id mismatch")
        expected_digest = sha256_text(canonical_json(self._guide_digest_payload(guide)))
        if guide.get("guide_digest") != expected_digest:
            raise ValueError("operator_guide.guide_digest mismatch")

    def _check_replacement_plan(self, plan: Dict[str, Any]) -> None:
        if not isinstance(plan, dict):
            raise ValueError("replacement_plan must be a mapping")
        if plan.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("replacement_plan.schema_version mismatch")
        if plan.get("profile_id") != NIW_REPLACEMENT_PLAN_PROFILE_ID:
            raise ValueError("replacement_plan.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._replacement_plan_digest_payload(plan))
        )
        if plan.get("replacement_plan_digest") != expected_digest:
            raise ValueError("replacement_plan.replacement_plan_digest mismatch")
        if plan.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("replacement_plan.claim_ceiling mismatch")
        if plan.get("storage_policy") != NIW_REPLACEMENT_PLAN_POLICY:
            raise ValueError("replacement_plan.storage_policy mismatch")

    def _check_connector_bundle(self, bundle: Dict[str, Any]) -> None:
        if not isinstance(bundle, dict):
            raise ValueError("connector_bundle must be a mapping")
        if bundle.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("connector_bundle.schema_version mismatch")
        if bundle.get("profile_id") != NIW_CONNECTOR_BUNDLE_PROFILE_ID:
            raise ValueError("connector_bundle.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._connector_bundle_digest_payload(bundle))
        )
        if bundle.get("connector_bundle_digest") != expected_digest:
            raise ValueError("connector_bundle.connector_bundle_digest mismatch")
        if bundle.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("connector_bundle.claim_ceiling mismatch")
        if bundle.get("storage_policy") != NIW_CONNECTOR_BUNDLE_POLICY:
            raise ValueError("connector_bundle.storage_policy mismatch")
        connectors = bundle.get("connectors")
        if not isinstance(connectors, list) or not connectors:
            raise ValueError("connector_bundle.connectors must be a non-empty list")
        if any(not isinstance(connector, dict) for connector in connectors):
            raise ValueError("connector_bundle.connectors must contain mappings")
        if bundle.get("connector_count") != len(connectors):
            raise ValueError("connector_bundle.connector_count must match connectors")
        connector_digests = []
        for connector in connectors:
            expected_connector_digest = sha256_text(
                canonical_json(self._connector_digest_payload(connector))
            )
            if connector.get("connector_digest") != expected_connector_digest:
                raise ValueError("connector.connector_digest mismatch")
            connector_digests.append(expected_connector_digest)
        if bundle.get("connector_digests") != connector_digests:
            raise ValueError("connector_bundle.connector_digests mismatch")
        expected_connector_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_CONNECTOR_BUNDLE_PROFILE_ID,
                    "connector_digests": connector_digests,
                    "replacement_plan_digest": bundle.get(
                        "replacement_plan_digest"
                    ),
                }
            )
        )
        if bundle.get("connector_digest_set") != expected_connector_digest_set:
            raise ValueError("connector_bundle.connector_digest_set mismatch")

    def _normalize_operator_profile(self, operator_profile: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(operator_profile, dict):
            raise ValueError("operator_profile must be a mapping")
        skill_level = str(operator_profile.get("skill_level", "non_ml_operator"))
        if skill_level not in NIW_OPERATOR_SKILL_FLOORS:
            raise ValueError("operator_profile.skill_level is not supported")
        return {
            "skill_level": skill_level,
            "prefers_plain_language": bool(
                operator_profile.get("prefers_plain_language", True)
            ),
            "llm_assistive_mode": bool(operator_profile.get("llm_assistive_mode", True)),
            "can_write_code": bool(operator_profile.get("can_write_code", False)),
        }

    def _normalize_app_kind(self, app_kind: Any) -> str:
        self._require_non_empty_string(app_kind, "app_kind")
        normalized = str(app_kind).strip().lower().replace("_", "-")
        if normalized not in NIW_APP_KINDS:
            raise ValueError("app_kind is not supported")
        return normalized

    def _normalize_connector_kind(self, connector_kind: Any) -> str:
        self._require_non_empty_string(connector_kind, "connector_kind")
        normalized = str(connector_kind).strip().lower().replace("_", "-")
        normalized = normalized.replace(" ", "-")
        if normalized not in NIW_CONNECTOR_KINDS:
            raise ValueError("connector_kind is not supported")
        return normalized

    def _normalize_connector_protocol(self, protocol: Any) -> str:
        self._require_non_empty_string(protocol, "protocol")
        normalized = str(protocol).strip().lower().replace("_", "-")
        normalized = normalized.replace(" ", "-")
        if normalized not in NIW_CONNECTOR_PROTOCOLS:
            raise ValueError("connector protocol is not supported")
        return normalized

    def _normalize_workflow_roles(self, workflow_roles: Sequence[str]) -> List[str]:
        if not workflow_roles:
            raise ValueError("workflow_roles must not be empty")
        normalized = []
        for role in workflow_roles:
            self._require_non_empty_string(role, "workflow_role")
            value = str(role).strip().lower().replace("_", "-")
            if value not in NIW_REQUIRED_REPLACEMENT_LANES:
                raise ValueError(f"workflow role is not supported: {role}")
            if value not in normalized:
                normalized.append(value)
        return normalized

    def _normalize_source_types(
        self,
        source_types: Sequence[str],
        field_name: str,
    ) -> List[str]:
        if not source_types:
            raise ValueError(f"{field_name} must not be empty")
        normalized: List[str] = []
        for source_type in source_types:
            value = self._normalize_source_type(source_type, field_name)
            if value not in normalized:
                normalized.append(value)
        return normalized

    def _normalize_source_type(self, source_type: Any, field_name: str) -> str:
        self._require_non_empty_string(source_type, field_name)
        normalized = str(source_type).strip().lower().replace(" ", "_")
        normalized = normalized.replace("-", "_")
        normalized = NIW_SOURCE_TYPE_ALIASES.get(normalized, normalized)
        if normalized not in NIW_SOURCE_FAMILIES:
            return normalized
        return normalized

    def _source_family(self, source_type: str) -> str:
        return NIW_SOURCE_FAMILIES.get(source_type, "uncatalogued_biological_context")

    def _bounded_feature(
        self,
        features: Dict[str, Any],
        field_name: str,
        default: float,
    ) -> float:
        value = features.get(field_name, default)
        if not isinstance(value, (int, float)):
            return default
        return self._round_score(float(value))

    def _round_score(self, value: float) -> float:
        return round(max(0.0, min(1.0, value)), 3)

    def _require_non_empty_string(self, value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    def _require_sha256_digest(self, value: Any, field_name: str) -> str:
        self._require_non_empty_string(value, field_name)
        digest = str(value)
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"{field_name} must be a sha256 hex digest")
        return digest

    def _connector_payload_redacted(self, connector_bundle: Dict[str, Any]) -> bool:
        bundle_raw_flags = all(
            connector_bundle.get(field_name) is False
            for field_name in connector_bundle
            if field_name.startswith("raw_")
        )
        connector_raw_flags = all(
            connector.get(field_name) is False
            for connector in connector_bundle.get("connectors", [])
            if isinstance(connector, dict)
            for field_name in connector
            if field_name.startswith("raw_")
        )
        return bundle_raw_flags and connector_raw_flags

    def _upstream_receipt_digest_set(
        self,
        upstream_receipt_bindings: Sequence[Dict[str, Any]],
    ) -> str:
        if not upstream_receipt_bindings:
            return ""
        digest_items = [
            {
                "receipt_role": binding.get("receipt_role"),
                "profile_id": binding.get("profile_id"),
                "fusion_receipt_digest": binding.get("fusion_receipt_digest"),
                "fused_window_digest": binding.get("fused_window_digest"),
                "fusion_axis_summary_digest": binding.get(
                    "fusion_axis_summary_digest"
                ),
            }
            for binding in upstream_receipt_bindings
        ]
        digest_items.sort(key=lambda item: str(item.get("fusion_receipt_digest", "")))
        return sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_SOURCE_BUNDLE_PROFILE_ID,
                    "upstream_receipt_bindings": digest_items,
                }
            )
        )

    def _app_digest_payload(self, app_receipt: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": app_receipt.get("profile_id"),
            "app_name": app_receipt.get("app_name"),
            "app_kind": app_receipt.get("app_kind"),
            "supported_source_types": app_receipt.get("supported_source_types"),
            "supported_source_families": app_receipt.get("supported_source_families"),
            "workflow_roles": app_receipt.get("workflow_roles"),
            "replacement_lanes": app_receipt.get("replacement_lanes"),
            "operator_skill_floor": app_receipt.get("operator_skill_floor"),
            "llm_native": app_receipt.get("llm_native"),
        }

    def _connector_digest_payload(self, connector: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "connector_profile_id": connector.get("connector_profile_id"),
            "app_ref": connector.get("app_ref"),
            "app_digest": connector.get("app_digest"),
            "app_kind": connector.get("app_kind"),
            "replacement_lanes": connector.get("replacement_lanes"),
            "connector_kind": connector.get("connector_kind"),
            "protocol": connector.get("protocol"),
            "endpoint_ref": connector.get("endpoint_ref"),
            "credential_ref": connector.get("credential_ref"),
            "permission_ref": connector.get("permission_ref"),
            "data_contract_ref": connector.get("data_contract_ref"),
            "llm_tool_ref": connector.get("llm_tool_ref"),
            "operator_label": connector.get("operator_label"),
            "supported_source_types": connector.get("supported_source_types"),
            "supported_source_families": connector.get("supported_source_families"),
            "credential_scope_digest": connector.get("credential_scope_digest"),
            "dry_run_supported": connector.get("dry_run_supported"),
            "llm_tool_bound": connector.get("llm_tool_bound"),
            "operator_safe_mode": connector.get("operator_safe_mode"),
        }

    def _source_bundle_digest_payload(self, source_bundle: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": source_bundle.get("profile_id"),
            "identity_id": source_bundle.get("identity_id"),
            "source_types": source_bundle.get("source_types"),
            "source_digest_set": source_bundle.get("source_digest_set"),
            "seed_survey_eeg_bound": source_bundle.get("seed_survey_eeg_bound"),
            "upstream_receipt_digest_set": source_bundle.get(
                "upstream_receipt_digest_set"
            ),
            "survey_eeg_fusion_receipt_bound": source_bundle.get(
                "survey_eeg_fusion_receipt_bound"
            ),
            "expansion_source_types_present": source_bundle.get(
                "expansion_source_types_present"
            ),
            "storage_policy": source_bundle.get("storage_policy"),
        }

    def _workspace_digest_payload(self, workspace: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": workspace.get("profile_id"),
            "identity_id": workspace.get("identity_id"),
            "analysis_goal": workspace.get("analysis_goal"),
            "operator_profile": workspace.get("operator_profile"),
            "app_digests": workspace.get("app_digests"),
            "source_bundle_digest": workspace.get("source_bundle_digest"),
            "replacement_lanes": workspace.get("replacement_lanes"),
            "llm_native_workflow_bound": workspace.get("llm_native_workflow_bound"),
            "beginner_operator_supported": workspace.get("beginner_operator_supported"),
            "claim_ceiling": workspace.get("claim_ceiling"),
        }

    def _analysis_digest_payload(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": analysis.get("profile_id"),
            "workspace_digest": analysis.get("workspace_digest"),
            "source_bundle_digest": analysis.get("source_bundle_digest"),
            "seed_pair_digest": analysis.get("seed_pair_digest"),
            "upstream_fusion_binding": analysis.get("upstream_fusion_binding"),
            "derived_axes": analysis.get("derived_axes"),
            "expansion_lanes": analysis.get("expansion_lanes"),
            "claim_ceiling": analysis.get("claim_ceiling"),
        }

    def _guide_digest_payload(self, guide: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": guide.get("profile_id"),
            "workspace_digest": guide.get("workspace_digest"),
            "analysis_digest": guide.get("analysis_digest"),
            "guide_policy": guide.get("guide_policy"),
            "operator_skill_floor": guide.get("operator_skill_floor"),
            "cards": guide.get("cards"),
            "agent_task_templates": guide.get("agent_task_templates"),
            "claim_ceiling": guide.get("claim_ceiling"),
        }

    def _replacement_plan_digest_payload(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": plan.get("profile_id"),
            "workspace_digest": plan.get("workspace_digest"),
            "source_bundle_digest": plan.get("source_bundle_digest"),
            "operator_guide_digest": plan.get("operator_guide_digest"),
            "app_digests": plan.get("app_digests"),
            "source_types": plan.get("source_types"),
            "source_families": plan.get("source_families"),
            "required_replacement_lanes": plan.get("required_replacement_lanes"),
            "lane_coverage": plan.get("lane_coverage"),
            "source_type_coverage": plan.get("source_type_coverage"),
            "coverage_summary": plan.get("coverage_summary"),
            "replacement_plan_bound": plan.get("replacement_plan_bound"),
            "llm_native_workflow_bound": plan.get("llm_native_workflow_bound"),
            "beginner_operator_supported": plan.get("beginner_operator_supported"),
            "coding_agent_ready": plan.get("coding_agent_ready"),
            "operator_handoffs": plan.get("operator_handoffs"),
            "claim_ceiling": plan.get("claim_ceiling"),
        }

    def _connector_bundle_digest_payload(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile_id": bundle.get("profile_id"),
            "replacement_plan_digest": bundle.get("replacement_plan_digest"),
            "workspace_digest": bundle.get("workspace_digest"),
            "source_bundle_digest": bundle.get("source_bundle_digest"),
            "operator_guide_digest": bundle.get("operator_guide_digest"),
            "app_digests": bundle.get("app_digests"),
            "source_types": bundle.get("source_types"),
            "required_replacement_lanes": bundle.get("required_replacement_lanes"),
            "connector_digest_set": bundle.get("connector_digest_set"),
            "lane_connector_coverage": bundle.get("lane_connector_coverage"),
            "source_type_connector_coverage": bundle.get(
                "source_type_connector_coverage"
            ),
            "all_apps_connected": bundle.get("all_apps_connected"),
            "required_lanes_connected": bundle.get("required_lanes_connected"),
            "source_types_connector_bound": bundle.get(
                "source_types_connector_bound"
            ),
            "llm_tooling_bound": bundle.get("llm_tooling_bound"),
            "operator_safe_mode_bound": bundle.get("operator_safe_mode_bound"),
            "connector_bundle_bound": bundle.get("connector_bundle_bound"),
            "claim_ceiling": bundle.get("claim_ceiling"),
        }
