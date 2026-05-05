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
NIW_COLLECTION_PROTOCOL_PROFILE_ID = "neuro-collection-protocol-v1"
NIW_COLLECTION_RUN_PROFILE_ID = "neuro-collection-run-v1"
NIW_MEASUREMENT_QUALITY_GATE_PROFILE_ID = "neuro-measurement-quality-gate-v1"
NIW_CROSS_MODAL_ANALYSIS_PLAN_PROFILE_ID = "neuro-cross-modal-analysis-plan-v1"
NIW_CROSS_MODAL_ANALYSIS_RUN_PROFILE_ID = "neuro-cross-modal-analysis-run-v1"
NIW_INTERPRETATION_SYNTHESIS_PROFILE_ID = (
    "neuro-operator-interpretation-synthesis-v1"
)
NIW_LONGITUDINAL_TIMELINE_PROFILE_ID = (
    "neuro-longitudinal-integration-timeline-v1"
)
NIW_OPERATOR_RUNBOOK_PROFILE_ID = "neuro-operator-runbook-v1"
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
NIW_COLLECTION_PROTOCOL_POLICY = (
    "source-consent+measurement-connector+collection-window-digest-only"
)
NIW_COLLECTION_RUN_POLICY = (
    "collection-step-digest+bounded-quality-summary+operator-review-only"
)
NIW_MEASUREMENT_QUALITY_GATE_POLICY = (
    "collection-result-digest+calibration-artifact-consent-quality-gate-only"
)
NIW_CROSS_MODAL_ANALYSIS_PLAN_POLICY = (
    "source-pair-feature-digest+connector-ref-analysis-plan-only"
)
NIW_CROSS_MODAL_ANALYSIS_RUN_POLICY = (
    "pair-digest+bounded-result-summary+operator-review-only"
)
NIW_INTERPRETATION_SYNTHESIS_POLICY = (
    "analysis-result-digest+plain-language-action-summary-only"
)
NIW_LONGITUDINAL_TIMELINE_POLICY = (
    "source-bundle-digest+axis-drift-summary-only"
)
NIW_OPERATOR_RUNBOOK_POLICY = (
    "receipt-digest+plain-language-workflow-step-only"
)
NIW_SEED_SOURCE_TYPES = ("questionnaire", "eeg")
NIW_EXPANSION_SOURCE_TYPES = ("fmri_bold", "brain_organoid")
NIW_OPEN_BIODATA_SOURCE_TYPES = (
    "biosensor",
    "behavioral_task",
    "omics",
    "clinical_metadata",
)
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
NIW_ANALYSIS_RECIPE_IDS = (
    "survey-eeg-feature-alignment",
    "neural-electrical-hemodynamic-context",
    "organoid-context-comparison",
    "biosignal-autonomic-context-screen",
    "behavioral-performance-context-screen",
    "omics-physiology-context-screen",
    "omics-clinical-context-screen",
    "clinical-context-modulator-screen",
    "feature-summary-cross-modal-screen",
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
            "collection_protocol_profile_id": NIW_COLLECTION_PROTOCOL_PROFILE_ID,
            "collection_run_profile_id": NIW_COLLECTION_RUN_PROFILE_ID,
            "measurement_quality_gate_profile_id": (
                NIW_MEASUREMENT_QUALITY_GATE_PROFILE_ID
            ),
            "cross_modal_analysis_plan_profile_id": (
                NIW_CROSS_MODAL_ANALYSIS_PLAN_PROFILE_ID
            ),
            "cross_modal_analysis_run_profile_id": (
                NIW_CROSS_MODAL_ANALYSIS_RUN_PROFILE_ID
            ),
            "interpretation_synthesis_profile_id": (
                NIW_INTERPRETATION_SYNTHESIS_PROFILE_ID
            ),
            "longitudinal_timeline_profile_id": (
                NIW_LONGITUDINAL_TIMELINE_PROFILE_ID
            ),
            "operator_runbook_profile_id": NIW_OPERATOR_RUNBOOK_PROFILE_ID,
            "biodata_survey_eeg_fusion_profile_id": (
                NIW_BIODATA_SURVEY_EEG_FUSION_PROFILE_ID
            ),
            "seed_source_types": list(NIW_SEED_SOURCE_TYPES),
            "expansion_source_types": list(NIW_EXPANSION_SOURCE_TYPES),
            "open_biodata_source_types": list(NIW_OPEN_BIODATA_SOURCE_TYPES),
            "source_families": dict(NIW_SOURCE_FAMILIES),
            "required_replacement_lanes": list(NIW_REQUIRED_REPLACEMENT_LANES),
            "operator_skill_floors": list(NIW_OPERATOR_SKILL_FLOORS),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "source_storage_policy": NIW_SOURCE_STORAGE_POLICY,
            "workspace_storage_policy": NIW_WORKSPACE_STORAGE_POLICY,
            "operator_guide_policy": NIW_GUIDE_POLICY,
            "replacement_plan_policy": NIW_REPLACEMENT_PLAN_POLICY,
            "connector_bundle_policy": NIW_CONNECTOR_BUNDLE_POLICY,
            "collection_protocol_policy": NIW_COLLECTION_PROTOCOL_POLICY,
            "collection_run_policy": NIW_COLLECTION_RUN_POLICY,
            "measurement_quality_gate_policy": (
                NIW_MEASUREMENT_QUALITY_GATE_POLICY
            ),
            "cross_modal_analysis_plan_policy": (
                NIW_CROSS_MODAL_ANALYSIS_PLAN_POLICY
            ),
            "cross_modal_analysis_run_policy": NIW_CROSS_MODAL_ANALYSIS_RUN_POLICY,
            "interpretation_synthesis_policy": (
                NIW_INTERPRETATION_SYNTHESIS_POLICY
            ),
            "longitudinal_timeline_policy": NIW_LONGITUDINAL_TIMELINE_POLICY,
            "operator_runbook_policy": NIW_OPERATOR_RUNBOOK_POLICY,
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

    def build_cross_modal_analysis_plan(
        self,
        source_bundle: Dict[str, Any],
        analysis: Dict[str, Any],
        operator_guide: Dict[str, Any],
        replacement_plan: Dict[str, Any],
        connector_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_analysis(analysis)
        self._check_operator_guide(operator_guide)
        self._check_replacement_plan(replacement_plan)
        self._check_connector_bundle(connector_bundle)
        if analysis["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("analysis.source_bundle_digest must match source bundle")
        if operator_guide["analysis_digest"] != analysis["analysis_digest"]:
            raise ValueError("operator_guide.analysis_digest must match analysis")
        if replacement_plan["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("replacement_plan.source_bundle_digest must match source bundle")
        if replacement_plan["operator_guide_digest"] != operator_guide["guide_digest"]:
            raise ValueError("replacement_plan.operator_guide_digest must match guide")
        if connector_bundle["replacement_plan_digest"] != replacement_plan[
            "replacement_plan_digest"
        ]:
            raise ValueError("connector_bundle.replacement_plan_digest must match plan")

        source_types = list(source_bundle["source_types"])
        if len(source_types) < 2:
            raise ValueError("source_bundle must contain at least two source types")
        sources_by_type = {
            source["source_type"]: source for source in source_bundle["sources"]
        }
        connector_coverage_by_source = {
            item["source_type"]: item
            for item in connector_bundle["source_type_connector_coverage"]
        }
        analysis_pairs: List[Dict[str, Any]] = []
        for index, left_source_type in enumerate(source_types):
            for right_source_type in source_types[index + 1 :]:
                analysis_pairs.append(
                    self._build_cross_modal_analysis_pair(
                        left_source_type,
                        right_source_type,
                        sources_by_type,
                        connector_coverage_by_source,
                        analysis,
                    )
                )
        pair_digests = [pair["pair_digest"] for pair in analysis_pairs]
        pair_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_CROSS_MODAL_ANALYSIS_PLAN_PROFILE_ID,
                    "pair_digests": pair_digests,
                    "connector_bundle_digest": connector_bundle[
                        "connector_bundle_digest"
                    ],
                }
            )
        )
        recipe_catalog = self._build_analysis_recipe_catalog(analysis_pairs)
        represented_source_types = sorted(
            {
                source_type
                for pair in analysis_pairs
                for source_type in pair["source_types"]
            }
        )
        expected_pair_count = len(source_types) * (len(source_types) - 1) // 2
        all_source_types_represented = represented_source_types == sorted(source_types)
        source_pair_coverage_bound = (
            len(analysis_pairs) == expected_pair_count
            and all(pair["all_required_connectors_bound"] for pair in analysis_pairs)
        )
        survey_eeg_seed_analysis_bound = any(
            pair["source_types"] == list(NIW_SEED_SOURCE_TYPES)
            and pair["analysis_recipe_id"] == "survey-eeg-feature-alignment"
            for pair in analysis_pairs
        ) and analysis["seed_survey_eeg_bound"]
        non_ml_operator_ready = (
            operator_guide["beginner_operator_supported"]
            and all(
                pair["requires_ml_expertise"] is False for pair in analysis_pairs
            )
        )
        plan = {
            "schema_version": NIW_SCHEMA_VERSION,
            "cross_modal_analysis_plan_ref": (
                "cross-modal-analysis-plan://neuro-integration/"
                f"{new_id('niw-cross-modal-plan')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_CROSS_MODAL_ANALYSIS_PLAN_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "analysis_ref": analysis["analysis_ref"],
            "analysis_digest": analysis["analysis_digest"],
            "operator_guide_ref": operator_guide["guide_ref"],
            "operator_guide_digest": operator_guide["guide_digest"],
            "replacement_plan_ref": replacement_plan["replacement_plan_ref"],
            "replacement_plan_digest": replacement_plan["replacement_plan_digest"],
            "connector_bundle_ref": connector_bundle["connector_bundle_ref"],
            "connector_bundle_digest": connector_bundle["connector_bundle_digest"],
            "source_types": source_types,
            "source_families": dict(source_bundle["source_families"]),
            "source_type_count": len(source_types),
            "analysis_pair_count": len(analysis_pairs),
            "expected_analysis_pair_count": expected_pair_count,
            "analysis_pairs": analysis_pairs,
            "pair_digests": pair_digests,
            "pair_digest_set": pair_digest_set,
            "recipe_catalog": recipe_catalog,
            "all_source_types_represented": all_source_types_represented,
            "source_pair_coverage_bound": source_pair_coverage_bound,
            "survey_eeg_seed_analysis_bound": survey_eeg_seed_analysis_bound,
            "connector_bundle_bound": connector_bundle["connector_bundle_bound"],
            "non_ml_operator_ready": non_ml_operator_ready,
            "coding_agent_ready": operator_guide["coding_agent_ready"],
            "cross_modal_analysis_plan_bound": (
                all_source_types_represented
                and source_pair_coverage_bound
                and survey_eeg_seed_analysis_bound
                and connector_bundle["connector_bundle_bound"]
                and replacement_plan["replacement_plan_bound"]
                and non_ml_operator_ready
                and operator_guide["coding_agent_ready"]
            ),
            "planning_scope": "all-current-source-type-pairs",
            "storage_policy": NIW_CROSS_MODAL_ANALYSIS_PLAN_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "raw_connector_payload_stored": False,
            "raw_plan_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        plan["cross_modal_analysis_plan_digest"] = sha256_text(
            canonical_json(self._cross_modal_analysis_plan_digest_payload(plan))
        )
        return deepcopy(plan)

    def build_collection_protocol(
        self,
        source_bundle: Dict[str, Any],
        replacement_plan: Dict[str, Any],
        connector_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_replacement_plan(replacement_plan)
        self._check_connector_bundle(connector_bundle)
        if replacement_plan["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("replacement_plan.source_bundle_digest must match source bundle")
        if connector_bundle["replacement_plan_digest"] != replacement_plan[
            "replacement_plan_digest"
        ]:
            raise ValueError("connector_bundle.replacement_plan_digest must match plan")
        connector_coverage_by_source = {
            item["source_type"]: item
            for item in connector_bundle["source_type_connector_coverage"]
        }
        collection_steps = [
            self._build_collection_step(source, connector_coverage_by_source)
            for source in source_bundle["sources"]
        ]
        step_digests = [step["collection_step_digest"] for step in collection_steps]
        step_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_COLLECTION_PROTOCOL_PROFILE_ID,
                    "source_bundle_digest": source_bundle["source_bundle_digest"],
                    "connector_bundle_digest": connector_bundle["connector_bundle_digest"],
                    "collection_step_digests": step_digests,
                }
            )
        )
        all_sources_collection_bound = (
            len(collection_steps) == source_bundle["source_count"]
            and all(step["collection_step_bound"] for step in collection_steps)
        )
        seed_collection_bound = all(
            any(
                step["source_type"] == source_type and step["collection_step_bound"]
                for step in collection_steps
            )
            for source_type in NIW_SEED_SOURCE_TYPES
        )
        expansion_collection_bound = all(
            any(
                step["source_type"] == source_type and step["collection_step_bound"]
                for step in collection_steps
            )
            for source_type in source_bundle["expansion_source_types_present"]
        )
        protocol = {
            "schema_version": NIW_SCHEMA_VERSION,
            "collection_protocol_ref": (
                f"collection-protocol://neuro-integration/{new_id('niw-collection')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_COLLECTION_PROTOCOL_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "replacement_plan_ref": replacement_plan["replacement_plan_ref"],
            "replacement_plan_digest": replacement_plan["replacement_plan_digest"],
            "connector_bundle_ref": connector_bundle["connector_bundle_ref"],
            "connector_bundle_digest": connector_bundle["connector_bundle_digest"],
            "source_types": list(source_bundle["source_types"]),
            "source_type_count": len(source_bundle["source_types"]),
            "collection_step_count": len(collection_steps),
            "collection_steps": collection_steps,
            "collection_step_digests": step_digests,
            "collection_step_digest_set": step_digest_set,
            "all_sources_collection_bound": all_sources_collection_bound,
            "seed_survey_eeg_collection_bound": seed_collection_bound,
            "expansion_collection_bound": expansion_collection_bound,
            "measurement_connector_coverage_bound": all(
                step["measurement_connector_bound"] for step in collection_steps
            ),
            "non_ml_operator_ready": replacement_plan["beginner_operator_supported"],
            "coding_agent_ready": replacement_plan["coding_agent_ready"],
            "collection_protocol_bound": (
                all_sources_collection_bound
                and seed_collection_bound
                and expansion_collection_bound
                and connector_bundle["connector_bundle_bound"]
                and replacement_plan["replacement_plan_bound"]
            ),
            "storage_policy": NIW_COLLECTION_PROTOCOL_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_collection_payload_stored": False,
            "raw_connector_payload_stored": False,
            "raw_credential_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        protocol["collection_protocol_digest"] = sha256_text(
            canonical_json(self._collection_protocol_digest_payload(protocol))
        )
        return deepcopy(protocol)

    def execute_collection_protocol(
        self,
        source_bundle: Dict[str, Any],
        connector_bundle: Dict[str, Any],
        collection_protocol: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_connector_bundle(connector_bundle)
        self._check_collection_protocol(collection_protocol)
        if collection_protocol["source_bundle_digest"] != source_bundle[
            "source_bundle_digest"
        ]:
            raise ValueError("collection_protocol.source_bundle_digest must match source bundle")
        if collection_protocol["connector_bundle_digest"] != connector_bundle[
            "connector_bundle_digest"
        ]:
            raise ValueError(
                "collection_protocol.connector_bundle_digest must match connector bundle"
            )
        collection_results = [
            self._build_collection_result(step)
            for step in collection_protocol["collection_steps"]
        ]
        result_digests = [
            result["collection_result_digest"] for result in collection_results
        ]
        result_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_COLLECTION_RUN_PROFILE_ID,
                    "collection_protocol_digest": collection_protocol[
                        "collection_protocol_digest"
                    ],
                    "result_digests": result_digests,
                }
            )
        )
        all_collection_results_bound = (
            len(collection_results) == collection_protocol["collection_step_count"]
            and all(result["collection_result_bound"] for result in collection_results)
        )
        seed_collection_result_bound = all(
            any(
                result["source_type"] == source_type
                and result["collection_result_bound"]
                for result in collection_results
            )
            for source_type in NIW_SEED_SOURCE_TYPES
        )
        expansion_collection_result_bound = all(
            any(
                result["source_type"] == source_type
                and result["collection_result_bound"]
                for result in collection_results
            )
            for source_type in source_bundle["expansion_source_types_present"]
        )
        summary = {
            "result_count": len(collection_results),
            "bounded_result_count": sum(
                1
                for result in collection_results
                if result["collection_result_bound"]
            ),
            "average_collection_quality_score": self._round_score(
                sum(
                    result["collection_quality_summary"][
                        "bounded_quality_score"
                    ]
                    for result in collection_results
                )
                / max(len(collection_results), 1)
            ),
            "max_collection_risk_proxy": self._round_score(
                max(
                    (
                        result["collection_quality_summary"][
                            "collection_risk_proxy"
                        ]
                        for result in collection_results
                    ),
                    default=0.0,
                )
            ),
        }
        run = {
            "schema_version": NIW_SCHEMA_VERSION,
            "collection_run_ref": (
                f"collection-run://neuro-integration/{new_id('niw-collection-run')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_COLLECTION_RUN_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "connector_bundle_ref": connector_bundle["connector_bundle_ref"],
            "connector_bundle_digest": connector_bundle["connector_bundle_digest"],
            "collection_protocol_ref": collection_protocol[
                "collection_protocol_ref"
            ],
            "collection_protocol_digest": collection_protocol[
                "collection_protocol_digest"
            ],
            "collection_step_count": collection_protocol["collection_step_count"],
            "result_count": len(collection_results),
            "collection_results": collection_results,
            "result_digests": result_digests,
            "result_digest_set": result_digest_set,
            "all_collection_results_bound": all_collection_results_bound,
            "seed_survey_eeg_collection_result_bound": (
                seed_collection_result_bound
            ),
            "expansion_collection_result_bound": (
                expansion_collection_result_bound
            ),
            "operator_review_ready": collection_protocol["non_ml_operator_ready"]
            and all_collection_results_bound,
            "coding_agent_review_ready": collection_protocol["coding_agent_ready"]
            and all_collection_results_bound,
            "collection_summary": summary,
            "collection_run_bound": (
                collection_protocol["collection_protocol_bound"]
                and connector_bundle["connector_bundle_bound"]
                and all_collection_results_bound
                and seed_collection_result_bound
                and expansion_collection_result_bound
            ),
            "storage_policy": NIW_COLLECTION_RUN_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_collection_payload_stored": False,
            "raw_connector_payload_stored": False,
            "raw_result_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        run["collection_run_digest"] = sha256_text(
            canonical_json(self._collection_run_digest_payload(run))
        )
        return deepcopy(run)

    def bind_measurement_quality_gate(
        self,
        source_bundle: Dict[str, Any],
        collection_run: Dict[str, Any],
        quality_manifests: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_collection_run(collection_run)
        if collection_run["source_bundle_digest"] != source_bundle[
            "source_bundle_digest"
        ]:
            raise ValueError("collection_run.source_bundle_digest must match source bundle")
        if not quality_manifests:
            raise ValueError("quality_manifests must not be empty")
        manifests = [
            self._normalize_quality_manifest(manifest)
            for manifest in quality_manifests
        ]
        manifest_by_source = {manifest["source_type"]: manifest for manifest in manifests}
        missing_source_types = [
            source_type
            for source_type in source_bundle["source_types"]
            if source_type not in manifest_by_source
        ]
        if missing_source_types:
            raise ValueError("quality_manifests must cover every source type")
        results_by_source = {
            result["source_type"]: result
            for result in collection_run["collection_results"]
        }
        quality_items = [
            self._build_quality_item(
                source,
                results_by_source[source["source_type"]],
                manifest_by_source[source["source_type"]],
            )
            for source in source_bundle["sources"]
        ]
        item_digests = [item["quality_item_digest"] for item in quality_items]
        item_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_MEASUREMENT_QUALITY_GATE_PROFILE_ID,
                    "collection_run_digest": collection_run[
                        "collection_run_digest"
                    ],
                    "quality_item_digests": item_digests,
                }
            )
        )
        all_quality_items_bound = (
            len(quality_items) == source_bundle["source_count"]
            and all(item["quality_item_bound"] for item in quality_items)
        )
        seed_quality_bound = all(
            any(
                item["source_type"] == source_type and item["quality_item_bound"]
                for item in quality_items
            )
            for source_type in NIW_SEED_SOURCE_TYPES
        )
        expansion_quality_bound = all(
            any(
                item["source_type"] == source_type and item["quality_item_bound"]
                for item in quality_items
            )
            for source_type in source_bundle["expansion_source_types_present"]
        )
        summary = {
            "quality_item_count": len(quality_items),
            "bounded_quality_item_count": sum(
                1 for item in quality_items if item["quality_item_bound"]
            ),
            "average_measurement_quality_score": self._round_score(
                sum(
                    item["quality_axis_summary"][
                        "measurement_quality_score"
                    ]
                    for item in quality_items
                )
                / max(len(quality_items), 1)
            ),
            "max_measurement_risk_proxy": self._round_score(
                max(
                    (
                        item["quality_axis_summary"][
                            "measurement_risk_proxy"
                        ]
                        for item in quality_items
                    ),
                    default=0.0,
                )
            ),
        }
        gate = {
            "schema_version": NIW_SCHEMA_VERSION,
            "measurement_quality_gate_ref": (
                "quality-gate://neuro-integration/"
                f"{new_id('niw-quality-gate')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_MEASUREMENT_QUALITY_GATE_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "collection_run_ref": collection_run["collection_run_ref"],
            "collection_run_digest": collection_run["collection_run_digest"],
            "source_types": list(source_bundle["source_types"]),
            "source_type_count": len(source_bundle["source_types"]),
            "quality_item_count": len(quality_items),
            "quality_items": quality_items,
            "quality_item_digests": item_digests,
            "quality_item_digest_set": item_digest_set,
            "all_quality_items_bound": all_quality_items_bound,
            "seed_survey_eeg_quality_bound": seed_quality_bound,
            "expansion_quality_bound": expansion_quality_bound,
            "calibration_refs_bound": all(
                bool(item["calibration_ref"]) for item in quality_items
            ),
            "artifact_qc_refs_bound": all(
                bool(item["artifact_qc_ref"]) for item in quality_items
            ),
            "consent_freshness_bound": all(
                item["consent_freshness_score"] >= 0.8
                for item in quality_items
            ),
            "operator_review_ready": collection_run["operator_review_ready"]
            and all_quality_items_bound,
            "coding_agent_review_ready": collection_run[
                "coding_agent_review_ready"
            ]
            and all_quality_items_bound,
            "quality_summary": summary,
            "measurement_quality_gate_bound": (
                collection_run["collection_run_bound"]
                and all_quality_items_bound
                and seed_quality_bound
                and expansion_quality_bound
            ),
            "storage_policy": NIW_MEASUREMENT_QUALITY_GATE_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_quality_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_artifact_payload_stored": False,
            "raw_consent_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        gate["measurement_quality_gate_digest"] = sha256_text(
            canonical_json(self._measurement_quality_gate_digest_payload(gate))
        )
        return deepcopy(gate)

    def execute_cross_modal_analysis_plan(
        self,
        source_bundle: Dict[str, Any],
        connector_bundle: Dict[str, Any],
        cross_modal_analysis_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_connector_bundle(connector_bundle)
        self._check_cross_modal_analysis_plan(cross_modal_analysis_plan)
        if cross_modal_analysis_plan["source_bundle_digest"] != source_bundle[
            "source_bundle_digest"
        ]:
            raise ValueError("cross_modal_analysis_plan.source_bundle_digest must match source bundle")
        if cross_modal_analysis_plan["connector_bundle_digest"] != connector_bundle[
            "connector_bundle_digest"
        ]:
            raise ValueError(
                "cross_modal_analysis_plan.connector_bundle_digest must match connector bundle"
            )
        sources_by_type = {
            source["source_type"]: source for source in source_bundle["sources"]
        }
        pair_results = [
            self._build_cross_modal_pair_result(pair, sources_by_type)
            for pair in cross_modal_analysis_plan["analysis_pairs"]
        ]
        result_digests = [result["result_digest"] for result in pair_results]
        result_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_CROSS_MODAL_ANALYSIS_RUN_PROFILE_ID,
                    "result_digests": result_digests,
                    "cross_modal_analysis_plan_digest": cross_modal_analysis_plan[
                        "cross_modal_analysis_plan_digest"
                    ],
                }
            )
        )
        all_pair_results_bound = (
            len(pair_results) == cross_modal_analysis_plan["analysis_pair_count"]
            and all(result["result_bound"] for result in pair_results)
        )
        seed_survey_eeg_result_bound = any(
            result["source_types"] == list(NIW_SEED_SOURCE_TYPES)
            and result["analysis_recipe_id"] == "survey-eeg-feature-alignment"
            and result["result_bound"]
            for result in pair_results
        )
        summary = {
            "result_count": len(pair_results),
            "bounded_result_count": sum(
                1 for result in pair_results if result["result_bound"]
            ),
            "average_compatibility_score": self._round_score(
                sum(
                    result["result_axis_summary"]["bounded_compatibility_score"]
                    for result in pair_results
                )
                / max(len(pair_results), 1)
            ),
            "max_uncertainty_proxy": self._round_score(
                max(
                    (
                        result["result_axis_summary"]["uncertainty_proxy"]
                        for result in pair_results
                    ),
                    default=0.0,
                )
            ),
        }
        run = {
            "schema_version": NIW_SCHEMA_VERSION,
            "cross_modal_analysis_run_ref": (
                "cross-modal-analysis-run://neuro-integration/"
                f"{new_id('niw-cross-modal-run')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_CROSS_MODAL_ANALYSIS_RUN_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "connector_bundle_ref": connector_bundle["connector_bundle_ref"],
            "connector_bundle_digest": connector_bundle["connector_bundle_digest"],
            "cross_modal_analysis_plan_ref": cross_modal_analysis_plan[
                "cross_modal_analysis_plan_ref"
            ],
            "cross_modal_analysis_plan_digest": cross_modal_analysis_plan[
                "cross_modal_analysis_plan_digest"
            ],
            "analysis_pair_count": cross_modal_analysis_plan["analysis_pair_count"],
            "result_count": len(pair_results),
            "pair_results": pair_results,
            "result_digests": result_digests,
            "result_digest_set": result_digest_set,
            "all_pair_results_bound": all_pair_results_bound,
            "seed_survey_eeg_result_bound": seed_survey_eeg_result_bound,
            "operator_review_ready": cross_modal_analysis_plan[
                "non_ml_operator_ready"
            ]
            and all_pair_results_bound,
            "coding_agent_review_ready": cross_modal_analysis_plan[
                "coding_agent_ready"
            ]
            and all_pair_results_bound,
            "result_summary": summary,
            "cross_modal_analysis_run_bound": (
                cross_modal_analysis_plan["cross_modal_analysis_plan_bound"]
                and connector_bundle["connector_bundle_bound"]
                and all_pair_results_bound
                and seed_survey_eeg_result_bound
            ),
            "storage_policy": NIW_CROSS_MODAL_ANALYSIS_RUN_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "raw_connector_payload_stored": False,
            "raw_result_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        run["cross_modal_analysis_run_digest"] = sha256_text(
            canonical_json(self._cross_modal_analysis_run_digest_payload(run))
        )
        return deepcopy(run)

    def synthesize_operator_interpretation(
        self,
        source_bundle: Dict[str, Any],
        operator_guide: Dict[str, Any],
        measurement_quality_gate: Dict[str, Any],
        cross_modal_analysis_run: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_operator_guide(operator_guide)
        self._check_measurement_quality_gate(measurement_quality_gate)
        self._check_cross_modal_analysis_run(cross_modal_analysis_run)
        if (
            measurement_quality_gate["source_bundle_digest"]
            != source_bundle["source_bundle_digest"]
        ):
            raise ValueError("measurement_quality_gate must bind source_bundle")
        if (
            cross_modal_analysis_run["source_bundle_digest"]
            != source_bundle["source_bundle_digest"]
        ):
            raise ValueError("cross_modal_analysis_run must bind source_bundle")

        quality_by_source_type = {
            item["source_type"]: item
            for item in measurement_quality_gate["quality_items"]
        }
        synthesis_cards = [
            self._build_interpretation_card(pair_result, quality_by_source_type)
            for pair_result in cross_modal_analysis_run["pair_results"]
        ]
        synthesis_card_digests = [
            card["synthesis_card_digest"] for card in synthesis_cards
        ]
        synthesis_card_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_INTERPRETATION_SYNTHESIS_PROFILE_ID,
                    "cross_modal_analysis_run_digest": cross_modal_analysis_run[
                        "cross_modal_analysis_run_digest"
                    ],
                    "synthesis_card_digests": synthesis_card_digests,
                }
            )
        )
        all_cards_bound = all(
            card["synthesis_card_bound"] for card in synthesis_cards
        )
        seed_synthesis_bound = any(
            set(card["source_types"]) == set(NIW_SEED_SOURCE_TYPES)
            and card["interpretation_status"] == "seed-interpretation-bound"
            and card["synthesis_card_bound"]
            for card in synthesis_cards
        )
        expansion_synthesis_bound = any(
            any(source_type in NIW_EXPANSION_SOURCE_TYPES for source_type in card["source_types"])
            and card["synthesis_card_bound"]
            for card in synthesis_cards
        )
        result_summary = cross_modal_analysis_run["result_summary"]
        quality_summary = measurement_quality_gate["quality_summary"]
        synthesis_summary = {
            "synthesis_card_count": len(synthesis_cards),
            "bounded_card_count": sum(
                1 for card in synthesis_cards if card["synthesis_card_bound"]
            ),
            "analysis_result_count": cross_modal_analysis_run["result_count"],
            "quality_item_count": measurement_quality_gate["quality_item_count"],
            "average_interpretation_confidence_proxy": self._round_score(
                (
                    result_summary["average_compatibility_score"]
                    + quality_summary["average_measurement_quality_score"]
                    + (1.0 - result_summary["max_uncertainty_proxy"])
                )
                / 3.0
            ),
            "max_uncertainty_proxy": result_summary["max_uncertainty_proxy"],
        }
        synthesis = {
            "schema_version": NIW_SCHEMA_VERSION,
            "interpretation_synthesis_ref": (
                "interpretation-synthesis://neuro-integration/"
                f"{new_id('niw-synthesis')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_INTERPRETATION_SYNTHESIS_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "operator_guide_ref": operator_guide["guide_ref"],
            "operator_guide_digest": operator_guide["guide_digest"],
            "measurement_quality_gate_ref": measurement_quality_gate[
                "measurement_quality_gate_ref"
            ],
            "measurement_quality_gate_digest": measurement_quality_gate[
                "measurement_quality_gate_digest"
            ],
            "cross_modal_analysis_run_ref": cross_modal_analysis_run[
                "cross_modal_analysis_run_ref"
            ],
            "cross_modal_analysis_run_digest": cross_modal_analysis_run[
                "cross_modal_analysis_run_digest"
            ],
            "source_types": list(source_bundle["source_types"]),
            "source_type_count": source_bundle["source_count"],
            "synthesis_card_count": len(synthesis_cards),
            "synthesis_cards": synthesis_cards,
            "synthesis_card_digests": synthesis_card_digests,
            "synthesis_card_digest_set": synthesis_card_digest_set,
            "all_synthesis_cards_bound": all_cards_bound,
            "seed_survey_eeg_synthesis_bound": seed_synthesis_bound,
            "expansion_synthesis_bound": expansion_synthesis_bound,
            "operator_action_ready": (
                operator_guide["beginner_operator_supported"]
                and cross_modal_analysis_run["operator_review_ready"]
                and measurement_quality_gate["operator_review_ready"]
                and all_cards_bound
            ),
            "coding_agent_action_ready": (
                operator_guide["coding_agent_ready"]
                and cross_modal_analysis_run["coding_agent_review_ready"]
                and measurement_quality_gate["coding_agent_review_ready"]
                and all_cards_bound
            ),
            "beginner_operator_supported": operator_guide[
                "beginner_operator_supported"
            ],
            "llm_native_workflow_bound": operator_guide[
                "llm_native_workflow_bound"
            ],
            "synthesis_summary": synthesis_summary,
            "interpretation_synthesis_bound": (
                source_bundle["seed_survey_eeg_bound"]
                and measurement_quality_gate["measurement_quality_gate_bound"]
                and cross_modal_analysis_run["cross_modal_analysis_run_bound"]
                and all_cards_bound
                and seed_synthesis_bound
                and expansion_synthesis_bound
            ),
            "storage_policy": NIW_INTERPRETATION_SYNTHESIS_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_quality_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "raw_interpretation_payload_stored": False,
            "raw_agent_task_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        synthesis["interpretation_synthesis_digest"] = sha256_text(
            canonical_json(self._interpretation_synthesis_digest_payload(synthesis))
        )
        return deepcopy(synthesis)

    def build_longitudinal_integration_timeline(
        self,
        identity_id: str,
        source_bundles: Sequence[Dict[str, Any]],
        operator_guide: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._require_non_empty_string(identity_id, "identity_id")
        if len(source_bundles) < 2:
            raise ValueError("source_bundles must include at least two windows")
        bundles = [deepcopy(source_bundle) for source_bundle in source_bundles]
        for bundle in bundles:
            self._check_source_bundle(bundle)
            if bundle.get("identity_id") != identity_id:
                raise ValueError("source_bundle.identity_id must match identity_id")
        self._check_operator_guide(operator_guide)

        bundle_source_type_sets = [
            set(bundle["source_types"]) for bundle in bundles
        ]
        represented_source_types = sorted(
            {
                source_type
                for source_types in bundle_source_type_sets
                for source_type in source_types
            }
        )
        stable_source_types = [
            source_type
            for source_type in represented_source_types
            if all(source_type in source_types for source_types in bundle_source_type_sets)
        ]
        missing_source_types_by_window = []
        for index, bundle in enumerate(bundles):
            missing = [
                source_type
                for source_type in represented_source_types
                if source_type not in bundle["source_types"]
            ]
            missing_source_types_by_window.append(
                {
                    "window_index": index,
                    "source_bundle_ref": bundle["source_bundle_ref"],
                    "missing_source_types": missing,
                    "bound": not missing,
                }
            )

        sources_by_window = [
            {
                source["source_type"]: source
                for source in bundle["sources"]
                if isinstance(source, dict)
            }
            for bundle in bundles
        ]
        source_type_axis_drifts = [
            self._build_longitudinal_axis_drift(
                source_type,
                sources_by_window,
                len(bundles),
            )
            for source_type in stable_source_types
        ]
        max_axis_drift_proxy = self._round_score(
            max(
                (
                    item["axis_drift_summary"]["max_axis_delta"]
                    for item in source_type_axis_drifts
                ),
                default=0.0,
            )
        )
        average_stability_score = self._round_score(
            sum(
                item["axis_drift_summary"]["stability_score"]
                for item in source_type_axis_drifts
            )
            / max(len(source_type_axis_drifts), 1)
        )
        all_windows_bound = all(
            bundle.get("raw_source_payload_stored") is False
            and bundle.get("consciousness_reproduction_claimed") is False
            and bundle.get("identity_replacement_claimed") is False
            for bundle in bundles
        )
        seed_timeline_bound = all(
            all(source_type in bundle["source_types"] for source_type in NIW_SEED_SOURCE_TYPES)
            for bundle in bundles
        )
        source_type_timeline_coverage_bound = all(
            item["bound"] for item in missing_source_types_by_window
        )
        upstream_fusion_timeline_bound = all(
            bundle.get("survey_eeg_fusion_receipt_bound") is True
            for bundle in bundles
        )
        all_axis_drifts_bound = (
            len(source_type_axis_drifts) == len(stable_source_types)
            and all(item["axis_drift_bound"] for item in source_type_axis_drifts)
        )
        summary = {
            "window_count": len(bundles),
            "source_type_count": len(represented_source_types),
            "stable_source_type_count": len(stable_source_types),
            "axis_drift_item_count": len(source_type_axis_drifts),
            "max_axis_drift_proxy": max_axis_drift_proxy,
            "average_stability_score": average_stability_score,
            "drift_review_required": max_axis_drift_proxy >= 0.25,
        }
        timeline = {
            "schema_version": NIW_SCHEMA_VERSION,
            "longitudinal_timeline_ref": (
                "longitudinal-timeline://neuro-integration/"
                f"{new_id('niw-timeline')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_LONGITUDINAL_TIMELINE_PROFILE_ID,
            "identity_id": identity_id,
            "operator_guide_ref": operator_guide["guide_ref"],
            "operator_guide_digest": operator_guide["guide_digest"],
            "source_bundle_refs": [
                bundle["source_bundle_ref"] for bundle in bundles
            ],
            "source_bundle_digests": [
                bundle["source_bundle_digest"] for bundle in bundles
            ],
            "window_count": len(bundles),
            "source_types": represented_source_types,
            "stable_source_types": stable_source_types,
            "missing_source_types_by_window": missing_source_types_by_window,
            "source_type_axis_drifts": source_type_axis_drifts,
            "timeline_summary": summary,
            "all_windows_bound": all_windows_bound,
            "seed_survey_eeg_timeline_bound": seed_timeline_bound,
            "source_type_timeline_coverage_bound": (
                source_type_timeline_coverage_bound
            ),
            "upstream_fusion_timeline_bound": upstream_fusion_timeline_bound,
            "all_axis_drifts_bound": all_axis_drifts_bound,
            "operator_review_ready": operator_guide["beginner_operator_supported"],
            "coding_agent_review_ready": operator_guide["coding_agent_ready"],
            "longitudinal_timeline_bound": (
                all_windows_bound
                and seed_timeline_bound
                and source_type_timeline_coverage_bound
                and upstream_fusion_timeline_bound
                and all_axis_drifts_bound
                and operator_guide["beginner_operator_supported"]
                and operator_guide["coding_agent_ready"]
            ),
            "storage_policy": NIW_LONGITUDINAL_TIMELINE_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_timeline_payload_stored": False,
            "raw_axis_payload_stored": False,
            "raw_operator_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        timeline["longitudinal_timeline_digest"] = sha256_text(
            canonical_json(self._longitudinal_timeline_digest_payload(timeline))
        )
        return deepcopy(timeline)

    def build_operator_runbook(
        self,
        source_bundle: Dict[str, Any],
        workspace: Dict[str, Any],
        analysis: Dict[str, Any],
        operator_guide: Dict[str, Any],
        replacement_plan: Dict[str, Any],
        connector_bundle: Dict[str, Any],
        collection_protocol: Dict[str, Any],
        collection_run: Dict[str, Any],
        measurement_quality_gate: Dict[str, Any],
        cross_modal_analysis_plan: Dict[str, Any],
        cross_modal_analysis_run: Dict[str, Any],
        interpretation_synthesis: Dict[str, Any],
        longitudinal_timeline: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_workspace(workspace)
        self._check_analysis(analysis)
        self._check_operator_guide(operator_guide)
        self._check_replacement_plan(replacement_plan)
        self._check_connector_bundle(connector_bundle)
        self._check_collection_protocol(collection_protocol)
        self._check_collection_run(collection_run)
        self._check_measurement_quality_gate(measurement_quality_gate)
        self._check_cross_modal_analysis_plan(cross_modal_analysis_plan)
        self._check_cross_modal_analysis_run(cross_modal_analysis_run)
        self._check_interpretation_synthesis(interpretation_synthesis)
        self._check_longitudinal_timeline(longitudinal_timeline)

        if workspace["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("workspace.source_bundle_digest must match source bundle")
        if analysis["workspace_digest"] != workspace["workspace_digest"]:
            raise ValueError("analysis.workspace_digest must match workspace")
        if operator_guide["analysis_digest"] != analysis["analysis_digest"]:
            raise ValueError("operator_guide.analysis_digest must match analysis")
        if replacement_plan["operator_guide_digest"] != operator_guide["guide_digest"]:
            raise ValueError("replacement_plan.operator_guide_digest must match guide")
        if connector_bundle["replacement_plan_digest"] != replacement_plan[
            "replacement_plan_digest"
        ]:
            raise ValueError("connector_bundle.replacement_plan_digest must match plan")
        if collection_protocol["connector_bundle_digest"] != connector_bundle[
            "connector_bundle_digest"
        ]:
            raise ValueError("collection_protocol.connector_bundle_digest must match connector bundle")
        if collection_run["collection_protocol_digest"] != collection_protocol[
            "collection_protocol_digest"
        ]:
            raise ValueError("collection_run.collection_protocol_digest must match protocol")
        if measurement_quality_gate["collection_run_digest"] != collection_run[
            "collection_run_digest"
        ]:
            raise ValueError("measurement_quality_gate.collection_run_digest must match collection run")
        if cross_modal_analysis_plan["connector_bundle_digest"] != connector_bundle[
            "connector_bundle_digest"
        ]:
            raise ValueError("cross_modal_analysis_plan.connector_bundle_digest must match connector bundle")
        if cross_modal_analysis_run["cross_modal_analysis_plan_digest"] != cross_modal_analysis_plan[
            "cross_modal_analysis_plan_digest"
        ]:
            raise ValueError("cross_modal_analysis_run.cross_modal_analysis_plan_digest must match plan")
        if interpretation_synthesis["cross_modal_analysis_run_digest"] != cross_modal_analysis_run[
            "cross_modal_analysis_run_digest"
        ]:
            raise ValueError("interpretation_synthesis.cross_modal_analysis_run_digest must match run")
        if longitudinal_timeline["operator_guide_digest"] != operator_guide["guide_digest"]:
            raise ValueError("longitudinal_timeline.operator_guide_digest must match guide")

        receipt_bindings = [
            self._operator_runbook_receipt_binding(
                "source-bundle",
                source_bundle["source_bundle_ref"],
                source_bundle["source_bundle_digest"],
                source_bundle["profile_id"],
                source_bundle["seed_survey_eeg_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "workspace",
                workspace["workspace_ref"],
                workspace["workspace_digest"],
                workspace["profile_id"],
                workspace["llm_native_workflow_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "survey-eeg-analysis",
                analysis["analysis_ref"],
                analysis["analysis_digest"],
                analysis["profile_id"],
                analysis["seed_survey_eeg_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "operator-guide",
                operator_guide["guide_ref"],
                operator_guide["guide_digest"],
                operator_guide["profile_id"],
                operator_guide["beginner_operator_supported"],
            ),
            self._operator_runbook_receipt_binding(
                "replacement-plan",
                replacement_plan["replacement_plan_ref"],
                replacement_plan["replacement_plan_digest"],
                replacement_plan["profile_id"],
                replacement_plan["replacement_plan_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "connector-bundle",
                connector_bundle["connector_bundle_ref"],
                connector_bundle["connector_bundle_digest"],
                connector_bundle["profile_id"],
                connector_bundle["connector_bundle_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "collection-protocol",
                collection_protocol["collection_protocol_ref"],
                collection_protocol["collection_protocol_digest"],
                collection_protocol["profile_id"],
                collection_protocol["collection_protocol_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "collection-run",
                collection_run["collection_run_ref"],
                collection_run["collection_run_digest"],
                collection_run["profile_id"],
                collection_run["collection_run_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "measurement-quality-gate",
                measurement_quality_gate["measurement_quality_gate_ref"],
                measurement_quality_gate["measurement_quality_gate_digest"],
                measurement_quality_gate["profile_id"],
                measurement_quality_gate["measurement_quality_gate_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "cross-modal-analysis-plan",
                cross_modal_analysis_plan["cross_modal_analysis_plan_ref"],
                cross_modal_analysis_plan["cross_modal_analysis_plan_digest"],
                cross_modal_analysis_plan["profile_id"],
                cross_modal_analysis_plan["cross_modal_analysis_plan_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "cross-modal-analysis-run",
                cross_modal_analysis_run["cross_modal_analysis_run_ref"],
                cross_modal_analysis_run["cross_modal_analysis_run_digest"],
                cross_modal_analysis_run["profile_id"],
                cross_modal_analysis_run["cross_modal_analysis_run_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "interpretation-synthesis",
                interpretation_synthesis["interpretation_synthesis_ref"],
                interpretation_synthesis["interpretation_synthesis_digest"],
                interpretation_synthesis["profile_id"],
                interpretation_synthesis["interpretation_synthesis_bound"],
            ),
            self._operator_runbook_receipt_binding(
                "longitudinal-timeline",
                longitudinal_timeline["longitudinal_timeline_ref"],
                longitudinal_timeline["longitudinal_timeline_digest"],
                longitudinal_timeline["profile_id"],
                longitudinal_timeline["longitudinal_timeline_bound"],
            ),
        ]
        source_types = list(source_bundle["source_types"])
        steps = self._build_operator_runbook_steps(
            source_types,
            receipt_bindings,
            source_bundle,
            workspace,
            analysis,
            operator_guide,
            replacement_plan,
            connector_bundle,
            collection_protocol,
            collection_run,
            measurement_quality_gate,
            cross_modal_analysis_plan,
            cross_modal_analysis_run,
            interpretation_synthesis,
            longitudinal_timeline,
        )
        step_digests = [step["runbook_step_digest"] for step in steps]
        step_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_OPERATOR_RUNBOOK_PROFILE_ID,
                    "step_digests": step_digests,
                    "longitudinal_timeline_digest": longitudinal_timeline[
                        "longitudinal_timeline_digest"
                    ],
                }
            )
        )
        receipt_digest_set = self._operator_runbook_receipt_digest_set(
            receipt_bindings
        )
        all_required_receipts_bound = all(
            binding["bound"] for binding in receipt_bindings
        )
        all_steps_bound = len(steps) == 9 and all(
            step["runbook_step_bound"] for step in steps
        )
        runbook_summary = {
            "step_count": len(steps),
            "bound_step_count": sum(
                1 for step in steps if step["runbook_step_bound"]
            ),
            "source_type_count": len(source_types),
            "replacement_lane_count": len(NIW_REQUIRED_REPLACEMENT_LANES),
            "operator_card_count": len(steps),
            "coding_agent_task_count": len(steps),
            "receipt_binding_count": len(receipt_bindings),
            "unsupported_step_count": sum(
                1 for step in steps if step["runbook_step_bound"] is not True
            ),
        }
        runbook = {
            "schema_version": NIW_SCHEMA_VERSION,
            "operator_runbook_ref": (
                "operator-runbook://neuro-integration/"
                f"{new_id('niw-runbook')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": NIW_OPERATOR_RUNBOOK_PROFILE_ID,
            "identity_id": source_bundle["identity_id"],
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "workspace_ref": workspace["workspace_ref"],
            "workspace_digest": workspace["workspace_digest"],
            "analysis_ref": analysis["analysis_ref"],
            "analysis_digest": analysis["analysis_digest"],
            "operator_guide_ref": operator_guide["guide_ref"],
            "operator_guide_digest": operator_guide["guide_digest"],
            "replacement_plan_ref": replacement_plan["replacement_plan_ref"],
            "replacement_plan_digest": replacement_plan["replacement_plan_digest"],
            "connector_bundle_ref": connector_bundle["connector_bundle_ref"],
            "connector_bundle_digest": connector_bundle["connector_bundle_digest"],
            "collection_protocol_ref": collection_protocol[
                "collection_protocol_ref"
            ],
            "collection_protocol_digest": collection_protocol[
                "collection_protocol_digest"
            ],
            "collection_run_ref": collection_run["collection_run_ref"],
            "collection_run_digest": collection_run["collection_run_digest"],
            "measurement_quality_gate_ref": measurement_quality_gate[
                "measurement_quality_gate_ref"
            ],
            "measurement_quality_gate_digest": measurement_quality_gate[
                "measurement_quality_gate_digest"
            ],
            "cross_modal_analysis_plan_ref": cross_modal_analysis_plan[
                "cross_modal_analysis_plan_ref"
            ],
            "cross_modal_analysis_plan_digest": cross_modal_analysis_plan[
                "cross_modal_analysis_plan_digest"
            ],
            "cross_modal_analysis_run_ref": cross_modal_analysis_run[
                "cross_modal_analysis_run_ref"
            ],
            "cross_modal_analysis_run_digest": cross_modal_analysis_run[
                "cross_modal_analysis_run_digest"
            ],
            "interpretation_synthesis_ref": interpretation_synthesis[
                "interpretation_synthesis_ref"
            ],
            "interpretation_synthesis_digest": interpretation_synthesis[
                "interpretation_synthesis_digest"
            ],
            "longitudinal_timeline_ref": longitudinal_timeline[
                "longitudinal_timeline_ref"
            ],
            "longitudinal_timeline_digest": longitudinal_timeline[
                "longitudinal_timeline_digest"
            ],
            "source_types": source_types,
            "source_type_count": len(source_types),
            "required_replacement_lanes": list(NIW_REQUIRED_REPLACEMENT_LANES),
            "receipt_bindings": receipt_bindings,
            "receipt_digest_set": receipt_digest_set,
            "workflow_steps": steps,
            "workflow_step_count": len(steps),
            "workflow_step_digests": step_digests,
            "workflow_step_digest_set": step_digest_set,
            "all_required_receipts_bound": all_required_receipts_bound,
            "all_workflow_steps_bound": all_steps_bound,
            "operator_cards_bound": all(
                bool(step["operator_card"]) for step in steps
            ),
            "coding_agent_tasks_bound": all(
                bool(step["coding_agent_task"]) for step in steps
            ),
            "beginner_operator_supported": (
                workspace["beginner_operator_supported"]
                and operator_guide["beginner_operator_supported"]
            ),
            "llm_native_workflow_bound": (
                workspace["llm_native_workflow_bound"]
                and operator_guide["llm_native_workflow_bound"]
            ),
            "coding_agent_ready": (
                workspace["coding_agent_ready"]
                and operator_guide["coding_agent_ready"]
            ),
            "operator_runbook_summary": runbook_summary,
            "operator_runbook_bound": (
                all_required_receipts_bound
                and all_steps_bound
                and workspace["beginner_operator_supported"]
                and operator_guide["coding_agent_ready"]
                and interpretation_synthesis["operator_action_ready"]
                and longitudinal_timeline["operator_review_ready"]
            ),
            "storage_policy": NIW_OPERATOR_RUNBOOK_POLICY,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "conflict_refs": deepcopy(list(NIW_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": NIW_CONFLICT_SINK_URL,
            "raw_receipt_payload_stored": False,
            "raw_runbook_payload_stored": False,
            "raw_operator_payload_stored": False,
            "raw_agent_task_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        runbook["operator_runbook_digest"] = sha256_text(
            canonical_json(self._operator_runbook_digest_payload(runbook))
        )
        return deepcopy(runbook)

    def validate_integration_bundle(
        self,
        app_receipts: Sequence[Dict[str, Any]],
        source_bundle: Dict[str, Any],
        workspace: Dict[str, Any],
        analysis: Dict[str, Any],
        operator_guide: Dict[str, Any],
        replacement_plan: Dict[str, Any] | None = None,
        connector_bundle: Dict[str, Any] | None = None,
        cross_modal_analysis_plan: Dict[str, Any] | None = None,
        cross_modal_analysis_run: Dict[str, Any] | None = None,
        collection_protocol: Dict[str, Any] | None = None,
        collection_run: Dict[str, Any] | None = None,
        measurement_quality_gate: Dict[str, Any] | None = None,
        interpretation_synthesis: Dict[str, Any] | None = None,
        longitudinal_timeline: Dict[str, Any] | None = None,
        operator_runbook: Dict[str, Any] | None = None,
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
        if cross_modal_analysis_plan is not None:
            try:
                self._check_cross_modal_analysis_plan(cross_modal_analysis_plan)
            except ValueError as exc:
                errors.append(str(exc))
            if connector_bundle is None:
                errors.append("cross_modal_analysis_plan requires connector_bundle")
        if cross_modal_analysis_run is not None:
            try:
                self._check_cross_modal_analysis_run(cross_modal_analysis_run)
            except ValueError as exc:
                errors.append(str(exc))
            if cross_modal_analysis_plan is None:
                errors.append("cross_modal_analysis_run requires cross_modal_analysis_plan")
        if collection_protocol is not None:
            try:
                self._check_collection_protocol(collection_protocol)
            except ValueError as exc:
                errors.append(str(exc))
            if connector_bundle is None:
                errors.append("collection_protocol requires connector_bundle")
        if collection_run is not None:
            try:
                self._check_collection_run(collection_run)
            except ValueError as exc:
                errors.append(str(exc))
            if collection_protocol is None:
                errors.append("collection_run requires collection_protocol")
        if measurement_quality_gate is not None:
            try:
                self._check_measurement_quality_gate(measurement_quality_gate)
            except ValueError as exc:
                errors.append(str(exc))
            if collection_run is None:
                errors.append("measurement_quality_gate requires collection_run")
        if interpretation_synthesis is not None:
            try:
                self._check_interpretation_synthesis(interpretation_synthesis)
            except ValueError as exc:
                errors.append(str(exc))
            if measurement_quality_gate is None:
                errors.append("interpretation_synthesis requires measurement_quality_gate")
            if cross_modal_analysis_run is None:
                errors.append("interpretation_synthesis requires cross_modal_analysis_run")
        if longitudinal_timeline is not None:
            try:
                self._check_longitudinal_timeline(longitudinal_timeline)
            except ValueError as exc:
                errors.append(str(exc))
            if operator_guide is None:
                errors.append("longitudinal_timeline requires operator_guide")
        if operator_runbook is not None:
            try:
                self._check_operator_runbook(operator_runbook)
            except ValueError as exc:
                errors.append(str(exc))
            if longitudinal_timeline is None:
                errors.append("operator_runbook requires longitudinal_timeline")
            if interpretation_synthesis is None:
                errors.append("operator_runbook requires interpretation_synthesis")

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
            and artifact.get("semantic_thought_content_generated", False) is False
            and artifact.get("consciousness_reproduction_claimed") is False
            and artifact.get("identity_replacement_claimed") is False
            for artifact in (source_bundle, workspace, analysis, operator_guide)
        )
        no_semantic_thought_content_claim = all(
            artifact.get("semantic_thought_content_generated", False) is False
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
        collection_protocol_checks: Dict[str, bool] = {}
        if collection_protocol is not None:
            collection_protocol_digest_bound = (
                collection_protocol.get("collection_protocol_digest")
                == sha256_text(
                    canonical_json(
                        self._collection_protocol_digest_payload(
                            collection_protocol
                        )
                    )
                )
            )
            expected_replacement_digest = (
                replacement_plan.get("replacement_plan_digest")
                if replacement_plan is not None
                else ""
            )
            expected_connector_digest = (
                connector_bundle.get("connector_bundle_digest")
                if connector_bundle is not None
                else ""
            )
            collection_protocol_checks = {
                "collection_protocol_digest_bound": (
                    collection_protocol_digest_bound
                ),
                "collection_protocol_bound": (
                    collection_protocol.get("collection_protocol_bound") is True
                    and collection_protocol.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and collection_protocol.get("replacement_plan_digest")
                    == expected_replacement_digest
                    and collection_protocol.get("connector_bundle_digest")
                    == expected_connector_digest
                ),
                "source_collection_coverage_bound": (
                    collection_protocol.get("all_sources_collection_bound") is True
                    and collection_protocol.get("collection_step_count")
                    == source_bundle.get("source_count")
                ),
                "seed_collection_bound": (
                    collection_protocol.get("seed_survey_eeg_collection_bound")
                    is True
                ),
                "collection_payload_redacted": (
                    self._collection_protocol_payload_redacted(collection_protocol)
                ),
                "collection_semantic_thought_claim_redacted": (
                    collection_protocol.get("semantic_thought_content_generated")
                    is False
                    and all(
                        step.get("semantic_thought_content_generated") is False
                        for step in collection_protocol.get("collection_steps", [])
                        if isinstance(step, dict)
                    )
                ),
            }
        collection_run_checks: Dict[str, bool] = {}
        if collection_run is not None:
            collection_run_digest_bound = (
                collection_run.get("collection_run_digest")
                == sha256_text(
                    canonical_json(
                        self._collection_run_digest_payload(collection_run)
                    )
                )
            )
            expected_collection_protocol_digest = (
                collection_protocol.get("collection_protocol_digest")
                if collection_protocol is not None
                else ""
            )
            expected_connector_digest = (
                connector_bundle.get("connector_bundle_digest")
                if connector_bundle is not None
                else ""
            )
            collection_run_checks = {
                "collection_run_digest_bound": collection_run_digest_bound,
                "collection_run_bound": (
                    collection_run.get("collection_run_bound") is True
                    and collection_run.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and collection_run.get("collection_protocol_digest")
                    == expected_collection_protocol_digest
                    and collection_run.get("connector_bundle_digest")
                    == expected_connector_digest
                ),
                "collection_results_bound": (
                    collection_run.get("all_collection_results_bound") is True
                    and collection_run.get("result_count")
                    == collection_run.get("collection_step_count")
                ),
                "collection_result_payload_redacted": (
                    self._collection_run_payload_redacted(collection_run)
                ),
                "collection_result_semantic_thought_claim_redacted": (
                    collection_run.get("semantic_thought_content_generated")
                    is False
                    and all(
                        result.get("semantic_thought_content_generated") is False
                        for result in collection_run.get("collection_results", [])
                        if isinstance(result, dict)
                    )
                ),
            }
        measurement_quality_gate_checks: Dict[str, bool] = {}
        if measurement_quality_gate is not None:
            measurement_quality_gate_digest_bound = (
                measurement_quality_gate.get("measurement_quality_gate_digest")
                == sha256_text(
                    canonical_json(
                        self._measurement_quality_gate_digest_payload(
                            measurement_quality_gate
                        )
                    )
                )
            )
            expected_collection_run_digest = (
                collection_run.get("collection_run_digest")
                if collection_run is not None
                else ""
            )
            measurement_quality_gate_checks = {
                "measurement_quality_gate_digest_bound": (
                    measurement_quality_gate_digest_bound
                ),
                "measurement_quality_gate_bound": (
                    measurement_quality_gate.get(
                        "measurement_quality_gate_bound"
                    )
                    is True
                    and measurement_quality_gate.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and measurement_quality_gate.get("collection_run_digest")
                    == expected_collection_run_digest
                ),
                "measurement_quality_items_bound": (
                    measurement_quality_gate.get("all_quality_items_bound")
                    is True
                    and measurement_quality_gate.get("quality_item_count")
                    == source_bundle.get("source_count")
                ),
                "measurement_quality_payload_redacted": (
                    self._measurement_quality_gate_payload_redacted(
                        measurement_quality_gate
                    )
                ),
            }
        cross_modal_plan_checks: Dict[str, bool] = {}
        if cross_modal_analysis_plan is not None:
            cross_modal_analysis_plan_digest_bound = (
                cross_modal_analysis_plan.get("cross_modal_analysis_plan_digest")
                == sha256_text(
                    canonical_json(
                        self._cross_modal_analysis_plan_digest_payload(
                            cross_modal_analysis_plan
                        )
                    )
                )
            )
            expected_replacement_digest = (
                replacement_plan.get("replacement_plan_digest")
                if replacement_plan is not None
                else ""
            )
            expected_connector_digest = (
                connector_bundle.get("connector_bundle_digest")
                if connector_bundle is not None
                else ""
            )
            expected_pair_count = (
                len(source_bundle.get("source_types", []))
                * (len(source_bundle.get("source_types", [])) - 1)
                // 2
            )
            cross_modal_plan_checks = {
                "cross_modal_analysis_plan_digest_bound": (
                    cross_modal_analysis_plan_digest_bound
                ),
                "cross_modal_analysis_plan_bound": (
                    cross_modal_analysis_plan.get(
                        "cross_modal_analysis_plan_bound"
                    )
                    is True
                    and cross_modal_analysis_plan.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and cross_modal_analysis_plan.get("analysis_digest")
                    == analysis.get("analysis_digest")
                    and cross_modal_analysis_plan.get("operator_guide_digest")
                    == operator_guide.get("guide_digest")
                    and cross_modal_analysis_plan.get("replacement_plan_digest")
                    == expected_replacement_digest
                    and cross_modal_analysis_plan.get("connector_bundle_digest")
                    == expected_connector_digest
                ),
                "cross_modal_source_pair_coverage_bound": (
                    cross_modal_analysis_plan.get("source_pair_coverage_bound")
                    is True
                    and cross_modal_analysis_plan.get("analysis_pair_count")
                    == expected_pair_count
                ),
                "cross_modal_analysis_payload_redacted": (
                    self._cross_modal_analysis_payload_redacted(
                        cross_modal_analysis_plan
                    )
                ),
            }
        cross_modal_run_checks: Dict[str, bool] = {}
        if cross_modal_analysis_run is not None:
            cross_modal_analysis_run_digest_bound = (
                cross_modal_analysis_run.get("cross_modal_analysis_run_digest")
                == sha256_text(
                    canonical_json(
                        self._cross_modal_analysis_run_digest_payload(
                            cross_modal_analysis_run
                        )
                    )
                )
            )
            expected_plan_digest = (
                cross_modal_analysis_plan.get("cross_modal_analysis_plan_digest")
                if cross_modal_analysis_plan is not None
                else ""
            )
            expected_connector_digest = (
                connector_bundle.get("connector_bundle_digest")
                if connector_bundle is not None
                else ""
            )
            cross_modal_run_checks = {
                "cross_modal_analysis_run_digest_bound": (
                    cross_modal_analysis_run_digest_bound
                ),
                "cross_modal_analysis_run_bound": (
                    cross_modal_analysis_run.get("cross_modal_analysis_run_bound")
                    is True
                    and cross_modal_analysis_run.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and cross_modal_analysis_run.get(
                        "cross_modal_analysis_plan_digest"
                    )
                    == expected_plan_digest
                    and cross_modal_analysis_run.get("connector_bundle_digest")
                    == expected_connector_digest
                ),
                "cross_modal_pair_results_bound": (
                    cross_modal_analysis_run.get("all_pair_results_bound") is True
                    and cross_modal_analysis_run.get("result_count")
                    == cross_modal_analysis_run.get("analysis_pair_count")
                ),
                "cross_modal_result_payload_redacted": (
                    self._cross_modal_analysis_run_payload_redacted(
                        cross_modal_analysis_run
                    )
                ),
            }
        interpretation_synthesis_checks: Dict[str, bool] = {}
        if interpretation_synthesis is not None:
            interpretation_synthesis_digest_bound = (
                interpretation_synthesis.get("interpretation_synthesis_digest")
                == sha256_text(
                    canonical_json(
                        self._interpretation_synthesis_digest_payload(
                            interpretation_synthesis
                        )
                    )
                )
            )
            expected_guide_digest = operator_guide.get("guide_digest")
            expected_gate_digest = (
                measurement_quality_gate.get("measurement_quality_gate_digest")
                if measurement_quality_gate is not None
                else ""
            )
            expected_run_digest = (
                cross_modal_analysis_run.get("cross_modal_analysis_run_digest")
                if cross_modal_analysis_run is not None
                else ""
            )
            interpretation_synthesis_checks = {
                "interpretation_synthesis_digest_bound": (
                    interpretation_synthesis_digest_bound
                ),
                "interpretation_synthesis_bound": (
                    interpretation_synthesis.get(
                        "interpretation_synthesis_bound"
                    )
                    is True
                    and interpretation_synthesis.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and interpretation_synthesis.get("operator_guide_digest")
                    == expected_guide_digest
                    and interpretation_synthesis.get(
                        "measurement_quality_gate_digest"
                    )
                    == expected_gate_digest
                    and interpretation_synthesis.get(
                        "cross_modal_analysis_run_digest"
                    )
                    == expected_run_digest
                ),
                "interpretation_synthesis_cards_bound": (
                    interpretation_synthesis.get("all_synthesis_cards_bound")
                    is True
                    and interpretation_synthesis.get("synthesis_card_count")
                    == (
                        cross_modal_analysis_run.get("result_count", 0)
                        if cross_modal_analysis_run is not None
                        else 0
                    )
                ),
                "interpretation_operator_action_ready": (
                    interpretation_synthesis.get("operator_action_ready") is True
                    and interpretation_synthesis.get("coding_agent_action_ready")
                    is True
                ),
                "interpretation_payload_redacted": (
                    self._interpretation_synthesis_payload_redacted(
                        interpretation_synthesis
                    )
                ),
            }
        longitudinal_timeline_checks: Dict[str, bool] = {}
        if longitudinal_timeline is not None:
            longitudinal_timeline_digest_bound = (
                longitudinal_timeline.get("longitudinal_timeline_digest")
                == sha256_text(
                    canonical_json(
                        self._longitudinal_timeline_digest_payload(
                            longitudinal_timeline
                        )
                    )
                )
            )
            longitudinal_timeline_checks = {
                "longitudinal_timeline_digest_bound": (
                    longitudinal_timeline_digest_bound
                ),
                "longitudinal_timeline_bound": (
                    longitudinal_timeline.get("longitudinal_timeline_bound")
                    is True
                    and longitudinal_timeline.get("identity_id")
                    == source_bundle.get("identity_id")
                    and source_bundle.get("source_bundle_digest")
                    in longitudinal_timeline.get("source_bundle_digests", [])
                    and longitudinal_timeline.get("operator_guide_digest")
                    == operator_guide.get("guide_digest")
                ),
                "longitudinal_source_type_coverage_bound": (
                    longitudinal_timeline.get(
                        "source_type_timeline_coverage_bound"
                    )
                    is True
                ),
                "longitudinal_axis_drifts_bound": (
                    longitudinal_timeline.get("all_axis_drifts_bound") is True
                ),
                "longitudinal_payload_redacted": (
                    self._longitudinal_timeline_payload_redacted(
                        longitudinal_timeline
                    )
                ),
                "longitudinal_no_identity_or_upload_claim": (
                    longitudinal_timeline.get("clinical_diagnosis_claimed")
                    is False
                    and longitudinal_timeline.get(
                        "semantic_thought_content_generated"
                    )
                    is False
                    and longitudinal_timeline.get(
                        "consciousness_reproduction_claimed"
                    )
                    is False
                    and longitudinal_timeline.get("identity_replacement_claimed")
                    is False
                    and longitudinal_timeline.get("upload_readiness_claimed")
                    is False
                ),
            }

        operator_runbook_checks: Dict[str, bool] = {}
        if operator_runbook is not None:
            operator_runbook_digest_bound = (
                operator_runbook.get("operator_runbook_digest")
                == sha256_text(
                    canonical_json(
                        self._operator_runbook_digest_payload(operator_runbook)
                    )
                )
            )
            expected_replacements = {
                "source_bundle_digest": source_bundle.get("source_bundle_digest"),
                "workspace_digest": workspace.get("workspace_digest"),
                "analysis_digest": analysis.get("analysis_digest"),
                "operator_guide_digest": operator_guide.get("guide_digest"),
                "replacement_plan_digest": (
                    replacement_plan.get("replacement_plan_digest")
                    if replacement_plan is not None
                    else ""
                ),
                "connector_bundle_digest": (
                    connector_bundle.get("connector_bundle_digest")
                    if connector_bundle is not None
                    else ""
                ),
                "collection_protocol_digest": (
                    collection_protocol.get("collection_protocol_digest")
                    if collection_protocol is not None
                    else ""
                ),
                "collection_run_digest": (
                    collection_run.get("collection_run_digest")
                    if collection_run is not None
                    else ""
                ),
                "measurement_quality_gate_digest": (
                    measurement_quality_gate.get(
                        "measurement_quality_gate_digest"
                    )
                    if measurement_quality_gate is not None
                    else ""
                ),
                "cross_modal_analysis_plan_digest": (
                    cross_modal_analysis_plan.get(
                        "cross_modal_analysis_plan_digest"
                    )
                    if cross_modal_analysis_plan is not None
                    else ""
                ),
                "cross_modal_analysis_run_digest": (
                    cross_modal_analysis_run.get(
                        "cross_modal_analysis_run_digest"
                    )
                    if cross_modal_analysis_run is not None
                    else ""
                ),
                "interpretation_synthesis_digest": (
                    interpretation_synthesis.get(
                        "interpretation_synthesis_digest"
                    )
                    if interpretation_synthesis is not None
                    else ""
                ),
                "longitudinal_timeline_digest": (
                    longitudinal_timeline.get("longitudinal_timeline_digest")
                    if longitudinal_timeline is not None
                    else ""
                ),
            }
            runbook_digest_chain_bound = all(
                operator_runbook.get(field_name) == expected_digest
                for field_name, expected_digest in expected_replacements.items()
            )
            operator_runbook_checks = {
                "operator_runbook_digest_bound": operator_runbook_digest_bound,
                "operator_runbook_bound": (
                    operator_runbook.get("operator_runbook_bound") is True
                    and runbook_digest_chain_bound
                ),
                "operator_runbook_receipt_chain_bound": (
                    operator_runbook.get("all_required_receipts_bound") is True
                    and runbook_digest_chain_bound
                ),
                "operator_runbook_steps_bound": (
                    operator_runbook.get("all_workflow_steps_bound") is True
                    and operator_runbook.get("workflow_step_count")
                    == len(operator_runbook.get("workflow_steps", []))
                ),
                "operator_runbook_payload_redacted": (
                    self._operator_runbook_payload_redacted(operator_runbook)
                ),
                "operator_runbook_no_identity_or_upload_claim": (
                    operator_runbook.get("clinical_diagnosis_claimed") is False
                    and operator_runbook.get(
                        "semantic_thought_content_generated"
                    )
                    is False
                    and operator_runbook.get(
                        "consciousness_reproduction_claimed"
                    )
                    is False
                    and operator_runbook.get("identity_replacement_claimed")
                    is False
                    and operator_runbook.get("upload_readiness_claimed")
                    is False
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
            "no_semantic_thought_content_claim": no_semantic_thought_content_claim,
            **replacement_plan_checks,
            **connector_bundle_checks,
            **collection_protocol_checks,
            **collection_run_checks,
            **measurement_quality_gate_checks,
            **cross_modal_plan_checks,
            **cross_modal_run_checks,
            **interpretation_synthesis_checks,
            **longitudinal_timeline_checks,
            **operator_runbook_checks,
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
            "collection_step_count": (
                collection_protocol.get("collection_step_count", 0)
                if collection_protocol is not None
                else 0
            ),
            "collection_result_count": (
                collection_run.get("result_count", 0)
                if collection_run is not None
                else 0
            ),
            "measurement_quality_item_count": (
                measurement_quality_gate.get("quality_item_count", 0)
                if measurement_quality_gate is not None
                else 0
            ),
            "analysis_pair_count": (
                cross_modal_analysis_plan.get("analysis_pair_count", 0)
                if cross_modal_analysis_plan is not None
                else 0
            ),
            "analysis_result_count": (
                cross_modal_analysis_run.get("result_count", 0)
                if cross_modal_analysis_run is not None
                else 0
            ),
            "interpretation_card_count": (
                interpretation_synthesis.get("synthesis_card_count", 0)
                if interpretation_synthesis is not None
                else 0
            ),
            "longitudinal_window_count": (
                longitudinal_timeline.get("window_count", 0)
                if longitudinal_timeline is not None
                else 0
            ),
            "longitudinal_stable_source_type_count": (
                longitudinal_timeline.get("timeline_summary", {}).get(
                    "stable_source_type_count",
                    0,
                )
                if longitudinal_timeline is not None
                else 0
            ),
            "longitudinal_axis_drift_item_count": (
                longitudinal_timeline.get("timeline_summary", {}).get(
                    "axis_drift_item_count",
                    0,
                )
                if longitudinal_timeline is not None
                else 0
            ),
            "operator_runbook_step_count": (
                operator_runbook.get("workflow_step_count", 0)
                if operator_runbook is not None
                else 0
            ),
            "operator_runbook_receipt_binding_count": (
                operator_runbook.get("operator_runbook_summary", {}).get(
                    "receipt_binding_count",
                    0,
                )
                if operator_runbook is not None
                else 0
            ),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_questionnaire_payload_stored": False,
            "raw_eeg_payload_stored": False,
            "raw_neuroimaging_payload_stored": False,
            "raw_organoid_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }

    def _operator_runbook_receipt_binding(
        self,
        receipt_role: str,
        receipt_ref: str,
        receipt_digest: str,
        profile_id: str,
        bound: bool,
    ) -> Dict[str, Any]:
        binding = {
            "receipt_role": receipt_role,
            "receipt_ref": receipt_ref,
            "receipt_digest": receipt_digest,
            "profile_id": profile_id,
            "bound": bool(bound),
            "raw_receipt_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        binding["receipt_binding_digest"] = sha256_text(
            canonical_json(
                {
                    "receipt_role": receipt_role,
                    "receipt_ref": receipt_ref,
                    "receipt_digest": receipt_digest,
                    "profile_id": profile_id,
                    "bound": bool(bound),
                }
            )
        )
        return binding

    def _operator_runbook_receipt_digest_set(
        self,
        receipt_bindings: Sequence[Dict[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_OPERATOR_RUNBOOK_PROFILE_ID,
                    "receipt_binding_digests": [
                        binding["receipt_binding_digest"]
                        for binding in receipt_bindings
                    ],
                    "receipt_roles": [
                        binding["receipt_role"] for binding in receipt_bindings
                    ],
                }
            )
        )

    def _build_operator_runbook_steps(
        self,
        source_types: Sequence[str],
        receipt_bindings: Sequence[Dict[str, Any]],
        source_bundle: Dict[str, Any],
        workspace: Dict[str, Any],
        analysis: Dict[str, Any],
        operator_guide: Dict[str, Any],
        replacement_plan: Dict[str, Any],
        connector_bundle: Dict[str, Any],
        collection_protocol: Dict[str, Any],
        collection_run: Dict[str, Any],
        measurement_quality_gate: Dict[str, Any],
        cross_modal_analysis_plan: Dict[str, Any],
        cross_modal_analysis_run: Dict[str, Any],
        interpretation_synthesis: Dict[str, Any],
        longitudinal_timeline: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        bindings_by_role = {
            binding["receipt_role"]: binding for binding in receipt_bindings
        }

        def selected_bindings(*roles: str) -> List[Dict[str, Any]]:
            return [bindings_by_role[role] for role in roles]

        return [
            self._operator_runbook_step(
                position=1,
                step_id="bind-seed-and-source-bundle",
                stage_kind="source-import",
                source_types=source_types,
                receipt_bindings=selected_bindings(
                    "source-bundle",
                    "survey-eeg-analysis",
                ),
                operator_card=(
                    "Start with questionnaire and EEG summaries, confirm the "
                    "BioData survey+EEG fusion receipt is bound, then review "
                    "expansion source summaries as context only."
                ),
                coding_agent_task=(
                    "verify_seed_source_bundle_and_upstream_fusion_digests"
                ),
                required_checks=[
                    "seed_survey_eeg_bound",
                    "survey_eeg_fusion_receipt_bound",
                    "raw_source_payload_redacted",
                ],
                bound=(
                    source_bundle["seed_survey_eeg_bound"]
                    and source_bundle["survey_eeg_fusion_receipt_bound"]
                    and analysis["seed_survey_eeg_bound"]
                    and analysis["upstream_fusion_binding"]["bound"]
                ),
            ),
            self._operator_runbook_step(
                position=2,
                step_id="open-llm-native-workspace",
                stage_kind="workspace-orientation",
                source_types=source_types,
                receipt_bindings=selected_bindings(
                    "workspace",
                    "operator-guide",
                ),
                operator_card=(
                    "Use the plain-language workspace guide before running "
                    "analysis; no machine-learning expertise is required for "
                    "the bounded review steps."
                ),
                coding_agent_task="verify_workspace_guide_and_beginner_safe_mode",
                required_checks=[
                    "llm_native_workflow_bound",
                    "beginner_operator_supported",
                    "coding_agent_ready",
                ],
                bound=(
                    workspace["llm_native_workflow_bound"]
                    and workspace["beginner_operator_supported"]
                    and operator_guide["coding_agent_ready"]
                ),
            ),
            self._operator_runbook_step(
                position=3,
                step_id="replace-application-lanes",
                stage_kind="application-replacement",
                source_types=source_types,
                receipt_bindings=selected_bindings(
                    "replacement-plan",
                    "connector-bundle",
                ),
                operator_card=(
                    "Confirm each source type has measurement, analysis, "
                    "curation, operator-copilot, and coding-agent lane coverage "
                    "before treating external tools as replaceable."
                ),
                coding_agent_task=(
                    "verify_replacement_lane_and_connector_coverage"
                ),
                required_checks=[
                    "replacement_plan_bound",
                    "source_type_lane_coverage_bound",
                    "connector_bundle_bound",
                ],
                bound=(
                    replacement_plan["replacement_plan_bound"]
                    and replacement_plan["source_type_lane_coverage_bound"]
                    and connector_bundle["connector_bundle_bound"]
                ),
            ),
            self._operator_runbook_step(
                position=4,
                step_id="bind-collection-protocol",
                stage_kind="collection-protocol",
                source_types=source_types,
                receipt_bindings=selected_bindings("collection-protocol"),
                operator_card=(
                    "Review collection windows, consent refs, and measurement "
                    "connector refs for every biological summary before any "
                    "analysis result is considered."
                ),
                coding_agent_task="verify_collection_protocol_step_digests",
                required_checks=[
                    "collection_protocol_bound",
                    "seed_survey_eeg_collection_bound",
                    "measurement_connector_coverage_bound",
                ],
                bound=collection_protocol["collection_protocol_bound"],
            ),
            self._operator_runbook_step(
                position=5,
                step_id="review-collection-run",
                stage_kind="collection-run",
                source_types=source_types,
                receipt_bindings=selected_bindings("collection-run"),
                operator_card=(
                    "Review bounded per-source collection quality and risk "
                    "summaries; do not request raw device streams."
                ),
                coding_agent_task="verify_collection_result_digest_set",
                required_checks=[
                    "collection_run_bound",
                    "all_collection_results_bound",
                    "operator_review_ready",
                ],
                bound=collection_run["collection_run_bound"],
            ),
            self._operator_runbook_step(
                position=6,
                step_id="gate-measurement-quality",
                stage_kind="measurement-quality",
                source_types=source_types,
                receipt_bindings=selected_bindings("measurement-quality-gate"),
                operator_card=(
                    "Check calibration, artifact/QC, consent freshness, and "
                    "quality authority refs before downstream analysis planning."
                ),
                coding_agent_task="verify_measurement_quality_gate_digests",
                required_checks=[
                    "measurement_quality_gate_bound",
                    "all_quality_items_bound",
                    "consent_freshness_bound",
                ],
                bound=measurement_quality_gate["measurement_quality_gate_bound"],
            ),
            self._operator_runbook_step(
                position=7,
                step_id="run-cross-modal-analysis",
                stage_kind="cross-modal-analysis",
                source_types=source_types,
                receipt_bindings=selected_bindings(
                    "cross-modal-analysis-plan",
                    "cross-modal-analysis-run",
                ),
                operator_card=(
                    "Use all current source-type pairs only as bounded feature "
                    "compatibility screens, starting from questionnaire+EEG."
                ),
                coding_agent_task="verify_cross_modal_pair_plan_and_run_digests",
                required_checks=[
                    "cross_modal_analysis_plan_bound",
                    "source_pair_coverage_bound",
                    "cross_modal_analysis_run_bound",
                ],
                bound=(
                    cross_modal_analysis_plan["cross_modal_analysis_plan_bound"]
                    and cross_modal_analysis_run["cross_modal_analysis_run_bound"]
                ),
            ),
            self._operator_runbook_step(
                position=8,
                step_id="review-interpretation-synthesis",
                stage_kind="interpretation-review",
                source_types=source_types,
                receipt_bindings=selected_bindings("interpretation-synthesis"),
                operator_card=(
                    "Read plain-language synthesis cards as review context only; "
                    "do not report diagnosis, semantic thought content, or upload "
                    "readiness."
                ),
                coding_agent_task="verify_interpretation_synthesis_cards",
                required_checks=[
                    "interpretation_synthesis_bound",
                    "operator_action_ready",
                    "coding_agent_action_ready",
                ],
                bound=interpretation_synthesis["interpretation_synthesis_bound"],
            ),
            self._operator_runbook_step(
                position=9,
                step_id="review-longitudinal-stability",
                stage_kind="longitudinal-review",
                source_types=source_types,
                receipt_bindings=selected_bindings("longitudinal-timeline"),
                operator_card=(
                    "Review repeated-window axis drift as a stability proxy only; "
                    "it is not identity proof and not upload readiness evidence."
                ),
                coding_agent_task="verify_longitudinal_axis_drift_summaries",
                required_checks=[
                    "longitudinal_timeline_bound",
                    "source_type_timeline_coverage_bound",
                    "all_axis_drifts_bound",
                ],
                bound=longitudinal_timeline["longitudinal_timeline_bound"],
            ),
        ]

    def _operator_runbook_step(
        self,
        *,
        position: int,
        step_id: str,
        stage_kind: str,
        source_types: Sequence[str],
        receipt_bindings: Sequence[Dict[str, Any]],
        operator_card: str,
        coding_agent_task: str,
        required_checks: Sequence[str],
        bound: bool,
    ) -> Dict[str, Any]:
        receipt_digests = [
            binding["receipt_digest"] for binding in receipt_bindings
        ]
        receipt_refs = [binding["receipt_ref"] for binding in receipt_bindings]
        step = {
            "runbook_step_ref": (
                "runbook-step://neuro-integration/"
                f"{new_id('niw-runbook-step')}"
            ),
            "position": position,
            "step_id": step_id,
            "stage_kind": stage_kind,
            "source_types": list(source_types),
            "input_receipt_refs": receipt_refs,
            "input_receipt_digests": receipt_digests,
            "operator_card": operator_card,
            "coding_agent_task": coding_agent_task,
            "required_checks": list(required_checks),
            "requires_ml_expertise": False,
            "runbook_step_bound": (
                bool(bound)
                and bool(receipt_digests)
                and all(binding["bound"] for binding in receipt_bindings)
            ),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_receipt_payload_stored": False,
            "raw_operator_payload_stored": False,
            "raw_agent_task_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        step["runbook_step_digest"] = sha256_text(
            canonical_json(self._operator_runbook_step_digest_payload(step))
        )
        return step

    def _build_longitudinal_axis_drift(
        self,
        source_type: str,
        sources_by_window: Sequence[Dict[str, Dict[str, Any]]],
        expected_window_count: int,
    ) -> Dict[str, Any]:
        sources = [
            window[source_type]
            for window in sources_by_window
            if source_type in window
        ]
        axis_sets = [set(source["analysis_axes"]) for source in sources]
        common_axes = sorted(set.intersection(*axis_sets)) if axis_sets else []
        axis_deltas: Dict[str, float] = {}
        for axis_name in common_axes:
            values = [
                float(source["analysis_axes"].get(axis_name, 0.0))
                for source in sources
            ]
            axis_deltas[axis_name] = self._round_score(
                max(values) - min(values) if values else 0.0
            )
        max_axis_delta = self._round_score(max(axis_deltas.values(), default=0.0))
        average_axis_delta = self._round_score(
            sum(axis_deltas.values()) / max(len(axis_deltas), 1)
        )
        drift_summary = {
            "common_axis_count": len(common_axes),
            "max_axis_delta": max_axis_delta,
            "average_axis_delta": average_axis_delta,
            "stability_score": self._round_score(1.0 - max_axis_delta),
            "drift_review_required": max_axis_delta >= 0.25,
        }
        item = {
            "source_type": source_type,
            "source_family": self._source_family(source_type),
            "window_count": len(sources),
            "source_refs": [source["source_ref"] for source in sources],
            "feature_digests": [source["feature_digest"] for source in sources],
            "common_analysis_axes": common_axes,
            "axis_delta_summary": axis_deltas,
            "axis_drift_summary": drift_summary,
            "axis_drift_bound": (
                len(sources) == expected_window_count
                and bool(common_axes)
                and all(source["raw_payload_stored"] is False for source in sources)
            ),
            "operator_summary": self._longitudinal_operator_summary(
                source_type,
                drift_summary["stability_score"],
                max_axis_delta,
            ),
            "agent_next_action": self._longitudinal_agent_next_action(
                source_type,
                max_axis_delta,
            ),
            "requires_ml_expertise": False,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_axis_payload_stored": False,
            "raw_source_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        item["axis_drift_digest"] = sha256_text(
            canonical_json(self._axis_drift_digest_payload(item))
        )
        return item

    def _longitudinal_operator_summary(
        self,
        source_type: str,
        stability_score: float,
        max_axis_delta: float,
    ) -> str:
        label = {
            "questionnaire": "Questionnaire",
            "eeg": "EEG",
            "fmri_bold": "fMRI BOLD",
            "brain_organoid": "Organoid",
            "biosensor": "Biosensor",
            "behavioral_task": "Behavioral task",
            "omics": "Omics",
            "clinical_metadata": "Clinical metadata",
        }.get(source_type, "Biological source")
        return (
            f"{label} timeline stability proxy is {stability_score:.3f}; "
            f"max axis drift {max_axis_delta:.3f} is review context only."
        )

    def _longitudinal_agent_next_action(
        self,
        source_type: str,
        max_axis_delta: float,
    ) -> str:
        if max_axis_delta >= 0.25:
            return f"review_{source_type}_timeline_drift_and_quality_refs"
        return f"record_{source_type}_timeline_stability_summary"

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

    def _build_cross_modal_analysis_pair(
        self,
        left_source_type: str,
        right_source_type: str,
        sources_by_type: Dict[str, Dict[str, Any]],
        connector_coverage_by_source: Dict[str, Dict[str, Any]],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        left_source = sources_by_type[left_source_type]
        right_source = sources_by_type[right_source_type]
        recipe_id = self._analysis_recipe_for_pair(left_source_type, right_source_type)
        connector_support = self._connector_support_for_pair(
            left_source_type,
            right_source_type,
            connector_coverage_by_source,
        )
        target_constructs = self._analysis_target_constructs(
            recipe_id,
            left_source_type,
            right_source_type,
        )
        source_types = [left_source_type, right_source_type]
        pair = {
            "pair_ref": (
                f"analysis-pair://neuro-integration/{new_id('niw-analysis-pair')}"
            ),
            "source_types": source_types,
            "source_families": {
                left_source_type: left_source["source_family"],
                right_source_type: right_source["source_family"],
            },
            "source_feature_digests": {
                left_source_type: left_source["feature_digest"],
                right_source_type: right_source["feature_digest"],
            },
            "analysis_recipe_id": recipe_id,
            "target_constructs": target_constructs,
            "plain_language_question": self._analysis_plain_language_question(
                recipe_id,
                left_source_type,
                right_source_type,
            ),
            "agent_action": self._analysis_agent_action(recipe_id),
            "seed_analysis_digest": (
                analysis["analysis_digest"]
                if source_types == list(NIW_SEED_SOURCE_TYPES)
                else ""
            ),
            "connector_support": connector_support,
            "all_required_connectors_bound": all(
                item["bound"] for item in connector_support
            ),
            "requires_ml_expertise": False,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_pair_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        pair["pair_digest"] = sha256_text(
            canonical_json(self._analysis_pair_digest_payload(pair))
        )
        return pair

    def _connector_support_for_pair(
        self,
        left_source_type: str,
        right_source_type: str,
        connector_coverage_by_source: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        left_coverage = connector_coverage_by_source.get(left_source_type, {})
        right_coverage = connector_coverage_by_source.get(right_source_type, {})
        support: List[Dict[str, Any]] = []
        for lane in NIW_REQUIRED_REPLACEMENT_LANES:
            refs = sorted(
                set(left_coverage.get("lane_connector_refs", {}).get(lane, []))
                | set(right_coverage.get("lane_connector_refs", {}).get(lane, []))
            )
            digests = sorted(
                set(left_coverage.get("lane_connector_digests", {}).get(lane, []))
                | set(right_coverage.get("lane_connector_digests", {}).get(lane, []))
            )
            support.append(
                {
                    "replacement_lane": lane,
                    "connector_refs": refs,
                    "connector_digests": digests,
                    "bound": bool(refs) and bool(digests),
                }
            )
        return support

    def _analysis_recipe_for_pair(
        self,
        left_source_type: str,
        right_source_type: str,
    ) -> str:
        pair = {left_source_type, right_source_type}
        if pair == set(NIW_SEED_SOURCE_TYPES):
            return "survey-eeg-feature-alignment"
        if pair == {"eeg", "fmri_bold"}:
            return "neural-electrical-hemodynamic-context"
        if "brain_organoid" in pair:
            return "organoid-context-comparison"
        if pair == {"omics", "clinical_metadata"}:
            return "omics-clinical-context-screen"
        if "clinical_metadata" in pair:
            return "clinical-context-modulator-screen"
        if "omics" in pair:
            return "omics-physiology-context-screen"
        if "behavioral_task" in pair:
            return "behavioral-performance-context-screen"
        if "biosensor" in pair:
            return "biosignal-autonomic-context-screen"
        return "feature-summary-cross-modal-screen"

    def _analysis_target_constructs(
        self,
        recipe_id: str,
        left_source_type: str,
        right_source_type: str,
    ) -> List[str]:
        if recipe_id == "survey-eeg-feature-alignment":
            return [
                "distress-load-alignment",
                "attention-load-alignment",
                "upstream-fusion-reconciliation",
            ]
        if recipe_id == "neural-electrical-hemodynamic-context":
            return [
                "cortical-load-context",
                "neurovascular-activation-context",
                "network-coupling-context",
            ]
        if recipe_id == "organoid-context-comparison":
            return [
                "in-vitro-neural-activity-context",
                "viability-boundary-context",
                "no-personhood-or-identity-inference",
            ]
        if recipe_id == "biosignal-autonomic-context-screen":
            return [
                "autonomic-state-context",
                "body-signal-quality-context",
                "no-clinical-diagnosis-inference",
            ]
        if recipe_id == "behavioral-performance-context-screen":
            return [
                "task-performance-context",
                "attention-and-fatigue-context",
                "no-ability-or-diagnosis-inference",
            ]
        if recipe_id == "omics-physiology-context-screen":
            return [
                "molecular-physiology-context",
                "sampling-quality-context",
                "no-causal-diagnosis-inference",
            ]
        if recipe_id == "omics-clinical-context-screen":
            return [
                "molecular-clinical-context",
                "screening-and-sampling-context",
                "no-diagnostic-or-treatment-inference",
            ]
        if recipe_id == "clinical-context-modulator-screen":
            return [
                "clinical-context-modulator",
                "medication-and-sleep-context",
                "no-clinical-diagnosis-inference",
            ]
        return [
            f"{left_source_type}-feature-summary-context",
            f"{right_source_type}-feature-summary-context",
        ]

    def _analysis_plain_language_question(
        self,
        recipe_id: str,
        left_source_type: str,
        right_source_type: str,
    ) -> str:
        if recipe_id == "survey-eeg-feature-alignment":
            return "Do questionnaire scores and EEG load proxies move together in this approved window?"
        if recipe_id == "neural-electrical-hemodynamic-context":
            return "Do EEG load proxies and fMRI BOLD context point to compatible neural activity summaries?"
        if recipe_id == "organoid-context-comparison":
            return "How should the organoid summary be kept as in-vitro context without treating it as the person?"
        if recipe_id == "biosignal-autonomic-context-screen":
            return "How does the biosensor summary contextualize autonomic state without making a clinical claim?"
        if recipe_id == "behavioral-performance-context-screen":
            return "How does the behavioral task summary contextualize performance, attention, or fatigue?"
        if recipe_id == "omics-physiology-context-screen":
            return "How does the omics summary contextualize physiology while preserving sampling uncertainty?"
        if recipe_id == "omics-clinical-context-screen":
            return "How do omics and clinical metadata summaries contextualize each other without diagnosis or treatment claims?"
        if recipe_id == "clinical-context-modulator-screen":
            return "How should clinical metadata modulate interpretation without becoming a diagnosis?"
        return (
            f"What bounded relationship can be screened between {left_source_type} "
            f"and {right_source_type} feature summaries?"
        )

    def _analysis_agent_action(self, recipe_id: str) -> str:
        if recipe_id == "survey-eeg-feature-alignment":
            return "reuse_seed_survey_eeg_alignment_receipt"
        if recipe_id == "neural-electrical-hemodynamic-context":
            return "plan_eeg_fmri_feature_context_screen"
        if recipe_id == "organoid-context-comparison":
            return "plan_organoid_context_boundary_screen"
        if recipe_id == "biosignal-autonomic-context-screen":
            return "plan_biosignal_autonomic_context_screen"
        if recipe_id == "behavioral-performance-context-screen":
            return "plan_behavioral_performance_context_screen"
        if recipe_id == "omics-physiology-context-screen":
            return "plan_omics_physiology_context_screen"
        if recipe_id == "omics-clinical-context-screen":
            return "plan_omics_clinical_context_screen"
        if recipe_id == "clinical-context-modulator-screen":
            return "plan_clinical_context_modulator_screen"
        return "plan_generic_feature_summary_screen"

    def _build_analysis_recipe_catalog(
        self,
        analysis_pairs: Sequence[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        catalog: List[Dict[str, Any]] = []
        for recipe_id in NIW_ANALYSIS_RECIPE_IDS:
            recipe_pairs = [
                pair for pair in analysis_pairs if pair["analysis_recipe_id"] == recipe_id
            ]
            if not recipe_pairs:
                continue
            catalog.append(
                {
                    "analysis_recipe_id": recipe_id,
                    "pair_count": len(recipe_pairs),
                    "requires_ml_expertise": False,
                    "claim_ceiling": NIW_CLAIM_CEILING,
                }
            )
        return catalog

    def _build_cross_modal_pair_result(
        self,
        pair: Dict[str, Any],
        sources_by_type: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        left_source_type, right_source_type = pair["source_types"]
        left_source = sources_by_type[left_source_type]
        right_source = sources_by_type[right_source_type]
        left_axis_mean = self._axis_mean(left_source["analysis_axes"])
        right_axis_mean = self._axis_mean(right_source["analysis_axes"])
        compatibility = self._round_score(1.0 - abs(left_axis_mean - right_axis_mean))
        coverage = self._round_score(
            (
                len(left_source["construct_coverage"])
                + len(right_source["construct_coverage"])
            )
            / 8.0
        )
        uncertainty = self._round_score(1.0 - min(compatibility, coverage))
        if pair["analysis_recipe_id"] == "survey-eeg-feature-alignment":
            result_status = "seed-survey-eeg-result-bound"
        elif pair["analysis_recipe_id"] == "organoid-context-comparison":
            result_status = "in-vitro-context-result-bound"
        elif pair["analysis_recipe_id"] == "biosignal-autonomic-context-screen":
            result_status = "biosignal-context-result-bound"
        elif pair["analysis_recipe_id"] == "behavioral-performance-context-screen":
            result_status = "behavioral-context-result-bound"
        elif pair["analysis_recipe_id"] in (
            "omics-physiology-context-screen",
            "omics-clinical-context-screen",
        ):
            result_status = "omics-context-result-bound"
        elif pair["analysis_recipe_id"] == "clinical-context-modulator-screen":
            result_status = "clinical-context-result-bound"
        else:
            result_status = "cross-modal-context-result-bound"
        result = {
            "result_ref": (
                f"analysis-result://neuro-integration/{new_id('niw-analysis-result')}"
            ),
            "pair_ref": pair["pair_ref"],
            "pair_digest": pair["pair_digest"],
            "source_types": list(pair["source_types"]),
            "analysis_recipe_id": pair["analysis_recipe_id"],
            "result_status": result_status,
            "result_axis_summary": {
                "left_axis_mean": left_axis_mean,
                "right_axis_mean": right_axis_mean,
                "bounded_compatibility_score": compatibility,
                "construct_coverage_proxy": coverage,
                "uncertainty_proxy": uncertainty,
            },
            "operator_summary": self._operator_result_summary(
                pair["analysis_recipe_id"],
                compatibility,
                uncertainty,
            ),
            "agent_next_action": self._agent_result_next_action(
                pair["analysis_recipe_id"]
            ),
            "evidence_refs": [
                pair["pair_ref"],
                *[
                    connector_ref
                    for support in pair["connector_support"]
                    for connector_ref in support["connector_refs"]
                ],
            ],
            "requires_ml_expertise": False,
            "result_bound": pair["all_required_connectors_bound"],
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_result_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        result["result_digest"] = sha256_text(
            canonical_json(self._analysis_result_digest_payload(result))
        )
        return result

    def _build_collection_step(
        self,
        source: Dict[str, Any],
        connector_coverage_by_source: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        source_type = source["source_type"]
        connector_coverage = connector_coverage_by_source.get(source_type, {})
        measurement_connector_refs = connector_coverage.get(
            "lane_connector_refs",
            {},
        ).get("measurement", [])
        measurement_connector_digests = connector_coverage.get(
            "lane_connector_digests",
            {},
        ).get("measurement", [])
        measurement_connector_bound = bool(measurement_connector_refs)
        step = {
            "collection_step_ref": (
                f"collection-step://neuro-integration/{new_id('niw-collection-step')}"
            ),
            "source_type": source_type,
            "source_family": source["source_family"],
            "source_ref": source["source_ref"],
            "participant_ref": source["participant_ref"],
            "consent_ref": source["consent_ref"],
            "license_ref": source["license_ref"],
            "feature_summary_ref": source["feature_summary_ref"],
            "feature_digest": source["feature_digest"],
            "collection_window_ref": (
                "collection-window://neuro-integration/"
                f"{source_type}/{new_id('niw-window')}"
            ),
            "collection_method_id": self._collection_method_id(source_type),
            "measurement_connector_refs": measurement_connector_refs,
            "measurement_connector_digests": measurement_connector_digests,
            "measurement_connector_bound": measurement_connector_bound,
            "collection_axis_summary": {
                "numeric_feature_count": source["numeric_feature_count"],
                "string_feature_count": source["string_feature_count"],
                "construct_axis_count": len(source["construct_coverage"]),
                "raw_payload_stored": source["raw_payload_stored"],
            },
            "operator_summary": self._collection_operator_summary(source_type),
            "agent_next_action": self._collection_agent_next_action(source_type),
            "requires_ml_expertise": False,
            "collection_step_bound": (
                measurement_connector_bound
                and bool(source["consent_ref"])
                and source["raw_payload_stored"] is False
            ),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_source_payload_stored": False,
            "raw_collection_payload_stored": False,
            "raw_connector_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        step["collection_step_digest"] = sha256_text(
            canonical_json(self._collection_step_digest_payload(step))
        )
        return step

    def _build_collection_result(self, step: Dict[str, Any]) -> Dict[str, Any]:
        quality_summary = self._collection_quality_summary(step)
        result = {
            "collection_result_ref": (
                "collection-result://neuro-integration/"
                f"{new_id('niw-collection-result')}"
            ),
            "collection_step_ref": step["collection_step_ref"],
            "collection_step_digest": step["collection_step_digest"],
            "source_type": step["source_type"],
            "source_family": step["source_family"],
            "source_ref": step["source_ref"],
            "feature_summary_ref": step["feature_summary_ref"],
            "feature_digest": step["feature_digest"],
            "collection_window_ref": step["collection_window_ref"],
            "collection_method_id": step["collection_method_id"],
            "measurement_connector_refs": list(
                step["measurement_connector_refs"]
            ),
            "measurement_connector_digests": list(
                step["measurement_connector_digests"]
            ),
            "collection_status": self._collection_result_status(
                step["source_type"]
            ),
            "collection_quality_summary": quality_summary,
            "operator_summary": self._collection_result_operator_summary(
                step["source_type"],
                quality_summary["bounded_quality_score"],
                quality_summary["collection_risk_proxy"],
            ),
            "agent_next_action": self._collection_result_next_action(
                step["source_type"]
            ),
            "evidence_refs": [
                step["collection_step_ref"],
                step["source_ref"],
                step["feature_summary_ref"],
                *step["measurement_connector_refs"],
            ],
            "requires_ml_expertise": False,
            "collection_result_bound": (
                step["collection_step_bound"]
                and quality_summary["bounded_quality_score"] >= 0.0
            ),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_source_payload_stored": False,
            "raw_collection_payload_stored": False,
            "raw_connector_payload_stored": False,
            "raw_result_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "semantic_thought_content_generated": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        result["collection_result_digest"] = sha256_text(
            canonical_json(self._collection_result_digest_payload(result))
        )
        return result

    def _collection_quality_summary(self, step: Dict[str, Any]) -> Dict[str, float]:
        axis_summary = step["collection_axis_summary"]
        feature_count = (
            axis_summary["numeric_feature_count"]
            + axis_summary["string_feature_count"]
        )
        completeness_score = self._round_score(min(1.0, feature_count / 4.0))
        construct_score = self._round_score(
            min(1.0, axis_summary["construct_axis_count"] / 4.0)
        )
        connector_score = 1.0 if step["measurement_connector_bound"] else 0.0
        consent_score = (
            1.0
            if step["consent_ref"] and axis_summary["raw_payload_stored"] is False
            else 0.0
        )
        quality_score = self._round_score(
            (
                completeness_score
                + construct_score
                + connector_score
                + consent_score
            )
            / 4.0
        )
        return {
            "feature_completeness_score": completeness_score,
            "construct_coverage_score": construct_score,
            "connector_binding_score": connector_score,
            "consent_binding_score": consent_score,
            "bounded_quality_score": quality_score,
            "collection_risk_proxy": self._round_score(1.0 - quality_score),
        }

    def _normalize_quality_manifest(
        self,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(manifest, dict):
            raise ValueError("quality_manifest must be a mapping")
        source_type = self._normalize_source_type(
            manifest.get("source_type"),
            "source_type",
        )
        for field_name in (
            "calibration_ref",
            "artifact_qc_ref",
            "consent_freshness_ref",
            "operator_review_ref",
            "quality_authority_ref",
        ):
            self._require_non_empty_string(manifest.get(field_name), field_name)
        calibration_score = self._bounded_feature(
            manifest,
            "calibration_score",
            1.0,
        )
        artifact_acceptance_score = self._bounded_feature(
            manifest,
            "artifact_acceptance_score",
            1.0,
        )
        consent_freshness_score = self._bounded_feature(
            manifest,
            "consent_freshness_score",
            1.0,
        )
        sampling_completeness_score = self._bounded_feature(
            manifest,
            "sampling_completeness_score",
            1.0,
        )
        return {
            "source_type": source_type,
            "calibration_ref": str(manifest["calibration_ref"]),
            "artifact_qc_ref": str(manifest["artifact_qc_ref"]),
            "consent_freshness_ref": str(manifest["consent_freshness_ref"]),
            "operator_review_ref": str(manifest["operator_review_ref"]),
            "quality_authority_ref": str(manifest["quality_authority_ref"]),
            "calibration_score": calibration_score,
            "artifact_acceptance_score": artifact_acceptance_score,
            "consent_freshness_score": consent_freshness_score,
            "sampling_completeness_score": sampling_completeness_score,
            "raw_quality_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_artifact_payload_stored": False,
            "raw_consent_payload_stored": False,
        }

    def _build_quality_item(
        self,
        source: Dict[str, Any],
        collection_result: Dict[str, Any],
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        collection_quality_score = collection_result["collection_quality_summary"][
            "bounded_quality_score"
        ]
        measurement_quality_score = self._round_score(
            (
                collection_quality_score
                + manifest["calibration_score"]
                + manifest["artifact_acceptance_score"]
                + manifest["consent_freshness_score"]
                + manifest["sampling_completeness_score"]
            )
            / 5.0
        )
        quality_axis_summary = {
            "collection_quality_score": collection_quality_score,
            "calibration_score": manifest["calibration_score"],
            "artifact_acceptance_score": manifest["artifact_acceptance_score"],
            "consent_freshness_score": manifest["consent_freshness_score"],
            "sampling_completeness_score": manifest["sampling_completeness_score"],
            "measurement_quality_score": measurement_quality_score,
            "measurement_risk_proxy": self._round_score(
                1.0 - measurement_quality_score
            ),
        }
        item_bound = (
            collection_result["collection_result_bound"]
            and measurement_quality_score >= 0.75
            and manifest["calibration_score"] >= 0.8
            and manifest["artifact_acceptance_score"] >= 0.8
            and manifest["consent_freshness_score"] >= 0.8
        )
        item = {
            "quality_item_ref": (
                "quality-item://neuro-integration/"
                f"{new_id('niw-quality-item')}"
            ),
            "source_type": source["source_type"],
            "source_family": source["source_family"],
            "source_ref": source["source_ref"],
            "feature_summary_ref": source["feature_summary_ref"],
            "feature_digest": source["feature_digest"],
            "collection_result_ref": collection_result["collection_result_ref"],
            "collection_result_digest": collection_result[
                "collection_result_digest"
            ],
            "collection_window_ref": collection_result["collection_window_ref"],
            "measurement_connector_refs": list(
                collection_result["measurement_connector_refs"]
            ),
            "measurement_connector_digests": list(
                collection_result["measurement_connector_digests"]
            ),
            "calibration_ref": manifest["calibration_ref"],
            "artifact_qc_ref": manifest["artifact_qc_ref"],
            "consent_freshness_ref": manifest["consent_freshness_ref"],
            "operator_review_ref": manifest["operator_review_ref"],
            "quality_authority_ref": manifest["quality_authority_ref"],
            "calibration_score": manifest["calibration_score"],
            "artifact_acceptance_score": manifest["artifact_acceptance_score"],
            "consent_freshness_score": manifest["consent_freshness_score"],
            "sampling_completeness_score": manifest[
                "sampling_completeness_score"
            ],
            "quality_axis_summary": quality_axis_summary,
            "quality_gate_status": self._quality_gate_status(
                source["source_type"]
            ),
            "operator_summary": self._quality_gate_operator_summary(
                source["source_type"],
                measurement_quality_score,
                quality_axis_summary["measurement_risk_proxy"],
            ),
            "agent_next_action": self._quality_gate_next_action(
                source["source_type"]
            ),
            "evidence_refs": [
                collection_result["collection_result_ref"],
                manifest["calibration_ref"],
                manifest["artifact_qc_ref"],
                manifest["consent_freshness_ref"],
                manifest["operator_review_ref"],
                manifest["quality_authority_ref"],
            ],
            "requires_ml_expertise": False,
            "quality_item_bound": item_bound,
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_source_payload_stored": False,
            "raw_quality_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_artifact_payload_stored": False,
            "raw_consent_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        item["quality_item_digest"] = sha256_text(
            canonical_json(self._quality_item_digest_payload(item))
        )
        return item

    def _build_interpretation_card(
        self,
        pair_result: Dict[str, Any],
        quality_by_source_type: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        source_types = list(pair_result["source_types"])
        quality_items = [
            quality_by_source_type[source_type]
            for source_type in source_types
            if source_type in quality_by_source_type
        ]
        average_quality = self._round_score(
            sum(
                item["quality_axis_summary"]["measurement_quality_score"]
                for item in quality_items
            )
            / max(len(quality_items), 1)
        )
        compatibility = pair_result["result_axis_summary"][
            "bounded_compatibility_score"
        ]
        uncertainty = pair_result["result_axis_summary"]["uncertainty_proxy"]
        confidence = self._round_score(
            (average_quality + compatibility + (1.0 - uncertainty)) / 3.0
        )
        interpretation_status = self._interpretation_status(
            source_types,
            pair_result["analysis_recipe_id"],
        )
        card = {
            "synthesis_card_ref": (
                "synthesis-card://neuro-integration/"
                f"{new_id('niw-synthesis-card')}"
            ),
            "result_ref": pair_result["result_ref"],
            "result_digest": pair_result["result_digest"],
            "source_types": source_types,
            "analysis_recipe_id": pair_result["analysis_recipe_id"],
            "interpretation_status": interpretation_status,
            "plain_language_summary": self._interpretation_plain_summary(
                source_types,
                confidence,
                uncertainty,
            ),
            "operator_next_action": self._interpretation_operator_action(
                source_types,
                uncertainty,
            ),
            "coding_agent_task": self._interpretation_agent_task(
                source_types,
                pair_result["analysis_recipe_id"],
            ),
            "quality_item_digests": [
                item["quality_item_digest"] for item in quality_items
            ],
            "interpretation_axis_summary": {
                "bounded_compatibility_score": compatibility,
                "average_measurement_quality_score": average_quality,
                "uncertainty_proxy": uncertainty,
                "interpretation_confidence_proxy": confidence,
            },
            "evidence_refs": [
                pair_result["result_ref"],
                *pair_result["evidence_refs"],
                *[item["quality_item_ref"] for item in quality_items],
                *[item["quality_authority_ref"] for item in quality_items],
            ],
            "requires_ml_expertise": False,
            "synthesis_card_bound": (
                pair_result["result_bound"]
                and len(quality_items) == len(source_types)
                and all(item["quality_item_bound"] for item in quality_items)
                and confidence >= 0.5
            ),
            "claim_ceiling": NIW_CLAIM_CEILING,
            "raw_interpretation_payload_stored": False,
            "raw_quality_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
            "upload_readiness_claimed": False,
        }
        card["synthesis_card_digest"] = sha256_text(
            canonical_json(self._synthesis_card_digest_payload(card))
        )
        return card

    def _collection_method_id(self, source_type: str) -> str:
        return {
            "questionnaire": "self-report-questionnaire-feature-window",
            "eeg": "eeg-feature-window-ingest",
            "fmri_bold": "fmri-bold-feature-summary-ingest",
            "brain_organoid": "organoid-neural-tissue-summary-ingest",
            "biosensor": "human-biosignal-feature-window-ingest",
            "behavioral_task": "behavioral-task-feature-summary-ingest",
            "omics": "molecular-omics-feature-summary-ingest",
            "clinical_metadata": "clinical-context-feature-summary-ingest",
        }.get(source_type, "generic-biodata-feature-summary-ingest")

    def _collection_operator_summary(self, source_type: str) -> str:
        if source_type == "questionnaire":
            return "Collect only approved questionnaire score summaries and consent refs."
        if source_type == "eeg":
            return "Collect only EEG feature-window summaries and artifact flags."
        if source_type == "fmri_bold":
            return "Collect only fMRI BOLD feature summaries, motion QC refs, and consent refs."
        if source_type == "brain_organoid":
            return "Collect organoid summaries only as in-vitro neural tissue context."
        if source_type == "biosensor":
            return "Collect biosensor summaries as autonomic context without raw wearable streams."
        if source_type == "behavioral_task":
            return "Collect behavioral task summaries as performance context without raw event logs."
        if source_type == "omics":
            return "Collect omics summaries as molecular context with sampling quality refs."
        if source_type == "clinical_metadata":
            return "Collect clinical metadata summaries as interpretation context, not diagnosis."
        return "Collect a digest-bound biological feature summary without raw payloads."

    def _collection_agent_next_action(self, source_type: str) -> str:
        return {
            "questionnaire": "verify_questionnaire_scores_consent_and_feature_digest",
            "eeg": "verify_eeg_feature_window_artifact_flags_and_digest",
            "fmri_bold": "verify_fmri_summary_motion_qc_and_digest",
            "brain_organoid": "verify_organoid_context_boundary_and_digest",
            "biosensor": "verify_biosensor_feature_window_quality_and_digest",
            "behavioral_task": "verify_behavioral_task_summary_timing_and_digest",
            "omics": "verify_omics_sampling_quality_and_digest",
            "clinical_metadata": "verify_clinical_metadata_context_without_diagnosis",
        }.get(source_type, "verify_generic_biodata_summary_digest")

    def _collection_result_status(self, source_type: str) -> str:
        return {
            "questionnaire": "seed-questionnaire-collection-bound",
            "eeg": "seed-eeg-collection-bound",
            "fmri_bold": "neuroimaging-collection-context-bound",
            "brain_organoid": "in-vitro-collection-context-bound",
            "biosensor": "biosignal-collection-context-bound",
            "behavioral_task": "behavioral-collection-context-bound",
            "omics": "omics-collection-context-bound",
            "clinical_metadata": "clinical-metadata-collection-context-bound",
        }.get(source_type, "generic-biodata-collection-bound")

    def _collection_result_operator_summary(
        self,
        source_type: str,
        quality_score: float,
        risk_proxy: float,
    ) -> str:
        if source_type == "questionnaire":
            label = "Questionnaire collection"
        elif source_type == "eeg":
            label = "EEG feature-window collection"
        elif source_type == "fmri_bold":
            label = "fMRI BOLD summary collection"
        elif source_type == "brain_organoid":
            label = "Organoid context collection"
        elif source_type == "biosensor":
            label = "Biosensor autonomic-context collection"
        elif source_type == "behavioral_task":
            label = "Behavioral task context collection"
        elif source_type == "omics":
            label = "Omics molecular-context collection"
        elif source_type == "clinical_metadata":
            label = "Clinical metadata context collection"
        else:
            label = "Biological feature-summary collection"
        return (
            f"{label} is bounded with quality {quality_score:.3f}; "
            f"review risk proxy {risk_proxy:.3f} before analysis."
        )

    def _collection_result_next_action(self, source_type: str) -> str:
        return {
            "questionnaire": "review_questionnaire_collection_quality",
            "eeg": "review_eeg_collection_artifact_context",
            "fmri_bold": "review_fmri_collection_motion_context",
            "brain_organoid": "review_organoid_collection_boundary",
            "biosensor": "review_biosensor_collection_quality_context",
            "behavioral_task": "review_behavioral_task_collection_context",
            "omics": "review_omics_collection_sampling_context",
            "clinical_metadata": "review_clinical_metadata_collection_context",
        }.get(source_type, "review_generic_biodata_collection_quality")

    def _quality_gate_status(self, source_type: str) -> str:
        return {
            "questionnaire": "seed-questionnaire-quality-gate-bound",
            "eeg": "seed-eeg-quality-gate-bound",
            "fmri_bold": "neuroimaging-quality-context-bound",
            "brain_organoid": "in-vitro-quality-context-bound",
            "biosensor": "biosignal-quality-context-bound",
            "behavioral_task": "behavioral-quality-context-bound",
            "omics": "omics-quality-context-bound",
            "clinical_metadata": "clinical-metadata-quality-context-bound",
        }.get(source_type, "generic-biodata-quality-gate-bound")

    def _quality_gate_operator_summary(
        self,
        source_type: str,
        quality_score: float,
        risk_proxy: float,
    ) -> str:
        if source_type == "questionnaire":
            label = "Questionnaire measurement quality"
        elif source_type == "eeg":
            label = "EEG measurement quality"
        elif source_type == "fmri_bold":
            label = "fMRI measurement quality"
        elif source_type == "brain_organoid":
            label = "Organoid context quality"
        elif source_type == "biosensor":
            label = "Biosensor signal quality"
        elif source_type == "behavioral_task":
            label = "Behavioral task quality"
        elif source_type == "omics":
            label = "Omics sampling quality"
        elif source_type == "clinical_metadata":
            label = "Clinical metadata context quality"
        else:
            label = "Biological measurement quality"
        return (
            f"{label} is gated at {quality_score:.3f}; "
            f"risk proxy {risk_proxy:.3f} must remain review context."
        )

    def _quality_gate_next_action(self, source_type: str) -> str:
        return {
            "questionnaire": "review_questionnaire_consent_and_scale_quality_refs",
            "eeg": "review_eeg_calibration_artifact_and_consent_refs",
            "fmri_bold": "review_fmri_motion_calibration_and_consent_refs",
            "brain_organoid": "review_organoid_provenance_quality_boundary",
            "biosensor": "review_biosensor_calibration_artifact_and_consent_refs",
            "behavioral_task": "review_behavioral_task_timing_accuracy_and_consent_refs",
            "omics": "review_omics_sampling_calibration_and_consent_refs",
            "clinical_metadata": "review_clinical_metadata_context_quality_without_diagnosis",
        }.get(source_type, "review_generic_biodata_quality_refs")

    def _axis_mean(self, axes: Dict[str, Any]) -> float:
        values = [float(value) for value in axes.values() if isinstance(value, (int, float))]
        if not values:
            return 0.0
        return self._round_score(sum(values) / len(values))

    def _operator_result_summary(
        self,
        recipe_id: str,
        compatibility: float,
        uncertainty: float,
    ) -> str:
        if recipe_id == "survey-eeg-feature-alignment":
            return (
                "Questionnaire and EEG summaries have a bounded alignment score "
                f"of {compatibility:.3f}; treat uncertainty {uncertainty:.3f} as review context."
            )
        if recipe_id == "organoid-context-comparison":
            return (
                "Organoid data is bound only as in-vitro neural tissue context; "
                f"compatibility {compatibility:.3f} is not a personhood or identity signal."
            )
        if recipe_id == "biosignal-autonomic-context-screen":
            return (
                "Biosensor data is bounded as autonomic context; "
                f"compatibility {compatibility:.3f} and uncertainty {uncertainty:.3f} "
                "are not clinical signals."
            )
        if recipe_id == "behavioral-performance-context-screen":
            return (
                "Behavioral task data is bounded as performance context; "
                f"compatibility {compatibility:.3f} and uncertainty {uncertainty:.3f} "
                "do not establish ability, diagnosis, or identity."
            )
        if recipe_id == "omics-physiology-context-screen":
            return (
                "Omics data is bounded as molecular physiology context; "
                f"compatibility {compatibility:.3f} keeps sampling uncertainty "
                f"{uncertainty:.3f} visible."
            )
        if recipe_id == "omics-clinical-context-screen":
            return (
                "Omics and clinical metadata are bounded as context only; "
                f"compatibility {compatibility:.3f} is not a diagnosis or treatment recommendation."
            )
        if recipe_id == "clinical-context-modulator-screen":
            return (
                "Clinical metadata modulates interpretation context only; "
                f"compatibility {compatibility:.3f} and uncertainty {uncertainty:.3f} "
                "must not be reported as diagnosis."
            )
        return (
            "This source pair has a bounded feature-summary compatibility score "
            f"of {compatibility:.3f} with uncertainty {uncertainty:.3f}."
        )

    def _agent_result_next_action(self, recipe_id: str) -> str:
        if recipe_id == "survey-eeg-feature-alignment":
            return "review_seed_alignment_and_quality_flags"
        if recipe_id == "neural-electrical-hemodynamic-context":
            return "review_eeg_fmri_context_without_diagnosis"
        if recipe_id == "organoid-context-comparison":
            return "review_organoid_context_boundary"
        if recipe_id == "biosignal-autonomic-context-screen":
            return "review_biosensor_autonomic_context_without_diagnosis"
        if recipe_id == "behavioral-performance-context-screen":
            return "review_behavioral_performance_context_without_ability_claim"
        if recipe_id == "omics-physiology-context-screen":
            return "review_omics_sampling_context_without_causal_claim"
        if recipe_id == "omics-clinical-context-screen":
            return "review_omics_clinical_context_without_treatment_claim"
        if recipe_id == "clinical-context-modulator-screen":
            return "review_clinical_context_modulator_without_diagnosis"
        return "review_generic_cross_modal_result_summary"

    def _interpretation_status(
        self,
        source_types: Sequence[str],
        recipe_id: str,
    ) -> str:
        source_type_set = set(source_types)
        if source_type_set == set(NIW_SEED_SOURCE_TYPES):
            return "seed-interpretation-bound"
        if "brain_organoid" in source_type_set:
            return "in-vitro-context-interpretation-bound"
        if "clinical_metadata" in source_type_set:
            return "clinical-context-interpretation-bound"
        if "omics" in source_type_set:
            return "omics-context-interpretation-bound"
        if "behavioral_task" in source_type_set:
            return "behavioral-context-interpretation-bound"
        if "biosensor" in source_type_set:
            return "biosignal-context-interpretation-bound"
        if "fmri_bold" in source_type_set:
            return "neuroimaging-context-interpretation-bound"
        if recipe_id == "feature-summary-cross-modal-screen":
            return "generic-biodata-interpretation-bound"
        return "cross-modal-context-interpretation-bound"

    def _interpretation_plain_summary(
        self,
        source_types: Sequence[str],
        confidence: float,
        uncertainty: float,
    ) -> str:
        label = " + ".join(source_types)
        if set(source_types) == set(NIW_SEED_SOURCE_TYPES):
            return (
                f"{label} can be reviewed as the seed alignment with confidence "
                f"proxy {confidence:.3f} and uncertainty {uncertainty:.3f}."
            )
        if "brain_organoid" in source_types:
            return (
                f"{label} is context only; confidence proxy {confidence:.3f} "
                "does not indicate personhood, identity, or subjective sameness."
            )
        if "clinical_metadata" in source_types:
            return (
                f"{label} uses clinical metadata only as interpretation context; "
                f"confidence proxy {confidence:.3f} and uncertainty {uncertainty:.3f} "
                "must not be treated as diagnosis."
            )
        if "omics" in source_types:
            return (
                f"{label} is molecular context only; confidence proxy "
                f"{confidence:.3f} keeps sampling uncertainty {uncertainty:.3f} visible."
            )
        if "behavioral_task" in source_types:
            return (
                f"{label} is behavioral performance context; confidence proxy "
                f"{confidence:.3f} does not establish ability or diagnosis."
            )
        if "biosensor" in source_types:
            return (
                f"{label} is autonomic biosignal context; confidence proxy "
                f"{confidence:.3f} remains bounded by uncertainty {uncertainty:.3f}."
            )
        return (
            f"{label} has a bounded interpretation confidence proxy "
            f"{confidence:.3f}; keep uncertainty {uncertainty:.3f} visible."
        )

    def _interpretation_operator_action(
        self,
        source_types: Sequence[str],
        uncertainty: float,
    ) -> str:
        if set(source_types) == set(NIW_SEED_SOURCE_TYPES):
            return "review_seed_questionnaire_eeg_card_before_expansion_context"
        if uncertainty >= 0.35:
            return "ask_operator_to_review_uncertainty_and_quality_refs"
        if "brain_organoid" in source_types:
            return "confirm_organoid_context_boundary_before_reporting"
        if "clinical_metadata" in source_types:
            return "confirm_clinical_context_is_not_reported_as_diagnosis"
        if "omics" in source_types:
            return "confirm_omics_sampling_context_before_reporting"
        if "behavioral_task" in source_types:
            return "confirm_behavioral_task_context_before_reporting"
        if "biosensor" in source_types:
            return "confirm_biosensor_context_before_reporting"
        return "accept_bounded_summary_for_non_ml_review"

    def _interpretation_agent_task(
        self,
        source_types: Sequence[str],
        recipe_id: str,
    ) -> str:
        source_label = "_".join(source_types)
        if recipe_id == "survey-eeg-feature-alignment":
            return f"prepare_plain_language_seed_review_for_{source_label}"
        if recipe_id == "organoid-context-comparison":
            return f"prepare_context_boundary_review_for_{source_label}"
        if recipe_id == "biosignal-autonomic-context-screen":
            return f"prepare_biosignal_context_review_for_{source_label}"
        if recipe_id == "behavioral-performance-context-screen":
            return f"prepare_behavioral_context_review_for_{source_label}"
        if recipe_id == "omics-physiology-context-screen":
            return f"prepare_omics_context_review_for_{source_label}"
        if recipe_id == "omics-clinical-context-screen":
            return f"prepare_omics_clinical_context_review_for_{source_label}"
        if recipe_id == "clinical-context-modulator-screen":
            return f"prepare_clinical_context_modulator_review_for_{source_label}"
        return f"prepare_bounded_interpretation_review_for_{source_label}"

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
        if source_type == "biosensor":
            heart_rate_variability = self._bounded_feature(
                feature_summary,
                "heart_rate_variability",
                0.5,
            )
            skin_conductance = self._bounded_feature(
                feature_summary,
                "skin_conductance",
                0.5,
            )
            respiration_regular = self._bounded_feature(
                feature_summary,
                "respiration_regular",
                0.5,
            )
            temperature_stability = self._bounded_feature(
                feature_summary,
                "temperature_stability",
                0.5,
            )
            physiological_stability = self._round_score(
                (
                    heart_rate_variability
                    + respiration_regular
                    + temperature_stability
                )
                / 3.0
            )
            return {
                "autonomic_balance_proxy": physiological_stability,
                "autonomic_arousal_proxy": self._round_score(skin_conductance),
                "respiration_regular_proxy": self._round_score(respiration_regular),
                "body_signal_quality_proxy": self._round_score(
                    (physiological_stability + (1.0 - skin_conductance)) / 2.0
                ),
            }
        if source_type == "behavioral_task":
            reaction_time_stability = self._bounded_feature(
                feature_summary,
                "reaction_time_stability",
                0.5,
            )
            attention_accuracy = self._bounded_feature(
                feature_summary,
                "attention_accuracy",
                0.5,
            )
            fatigue_error = self._bounded_feature(
                feature_summary,
                "fatigue_error_proxy",
                0.5,
            )
            return {
                "behavioral_attention_proxy": self._round_score(attention_accuracy),
                "response_stability_proxy": self._round_score(
                    reaction_time_stability
                ),
                "fatigue_burden_proxy": self._round_score(fatigue_error),
                "task_performance_quality_proxy": self._round_score(
                    (
                        reaction_time_stability
                        + attention_accuracy
                        + (1.0 - fatigue_error)
                    )
                    / 3.0
                ),
            }
        if source_type == "omics":
            inflammation = self._bounded_feature(
                feature_summary,
                "inflammation_marker_proxy",
                0.5,
            )
            metabolic_stability = self._bounded_feature(
                feature_summary,
                "metabolic_stability_proxy",
                0.5,
            )
            sampling_quality = self._bounded_feature(
                feature_summary,
                "sampling_quality_proxy",
                0.5,
            )
            return {
                "inflammation_context_proxy": self._round_score(inflammation),
                "metabolic_stability_proxy": self._round_score(metabolic_stability),
                "molecular_sampling_quality_proxy": self._round_score(
                    sampling_quality
                ),
                "molecular_burden_proxy": self._round_score(
                    (inflammation + (1.0 - metabolic_stability)) / 2.0
                ),
            }
        if source_type == "clinical_metadata":
            medication_context = self._bounded_feature(
                feature_summary,
                "medication_context_proxy",
                0.5,
            )
            sleep_history = self._bounded_feature(
                feature_summary,
                "sleep_history_proxy",
                0.5,
            )
            screening_completeness = self._bounded_feature(
                feature_summary,
                "screening_completeness",
                0.5,
            )
            return {
                "medication_context_proxy": self._round_score(medication_context),
                "sleep_context_proxy": self._round_score(sleep_history),
                "clinical_screening_completeness_proxy": self._round_score(
                    screening_completeness
                ),
                "clinical_context_risk_proxy": self._round_score(
                    (
                        medication_context
                        + sleep_history
                        + (1.0 - screening_completeness)
                    )
                    / 3.0
                ),
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

    def _check_collection_protocol(self, protocol: Dict[str, Any]) -> None:
        if not isinstance(protocol, dict):
            raise ValueError("collection_protocol must be a mapping")
        if protocol.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("collection_protocol.schema_version mismatch")
        if protocol.get("profile_id") != NIW_COLLECTION_PROTOCOL_PROFILE_ID:
            raise ValueError("collection_protocol.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._collection_protocol_digest_payload(protocol))
        )
        if protocol.get("collection_protocol_digest") != expected_digest:
            raise ValueError(
                "collection_protocol.collection_protocol_digest mismatch"
            )
        if protocol.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("collection_protocol.claim_ceiling mismatch")
        if protocol.get("storage_policy") != NIW_COLLECTION_PROTOCOL_POLICY:
            raise ValueError("collection_protocol.storage_policy mismatch")
        steps = protocol.get("collection_steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(
                "collection_protocol.collection_steps must be a non-empty list"
            )
        if protocol.get("collection_step_count") != len(steps):
            raise ValueError(
                "collection_protocol.collection_step_count must match steps"
            )
        step_digests = []
        for step in steps:
            for field_name in (
                "clinical_diagnosis_claimed",
                "semantic_thought_content_generated",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
            ):
                if step.get(field_name) is not False:
                    raise ValueError(f"collection_step.{field_name} must be false")
            expected_step_digest = sha256_text(
                canonical_json(self._collection_step_digest_payload(step))
            )
            if step.get("collection_step_digest") != expected_step_digest:
                raise ValueError("collection_step.collection_step_digest mismatch")
            step_digests.append(expected_step_digest)
        if protocol.get("collection_step_digests") != step_digests:
            raise ValueError("collection_protocol.collection_step_digests mismatch")
        expected_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_COLLECTION_PROTOCOL_PROFILE_ID,
                    "source_bundle_digest": protocol.get("source_bundle_digest"),
                    "connector_bundle_digest": protocol.get(
                        "connector_bundle_digest"
                    ),
                    "collection_step_digests": step_digests,
                }
            )
        )
        if protocol.get("collection_step_digest_set") != expected_digest_set:
            raise ValueError("collection_protocol.collection_step_digest_set mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "semantic_thought_content_generated",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if protocol.get(field_name) is not False:
                raise ValueError(f"collection_protocol.{field_name} must be false")

    def _check_collection_run(self, run: Dict[str, Any]) -> None:
        if not isinstance(run, dict):
            raise ValueError("collection_run must be a mapping")
        if run.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("collection_run.schema_version mismatch")
        if run.get("profile_id") != NIW_COLLECTION_RUN_PROFILE_ID:
            raise ValueError("collection_run.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._collection_run_digest_payload(run))
        )
        if run.get("collection_run_digest") != expected_digest:
            raise ValueError("collection_run.collection_run_digest mismatch")
        if run.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("collection_run.claim_ceiling mismatch")
        if run.get("storage_policy") != NIW_COLLECTION_RUN_POLICY:
            raise ValueError("collection_run.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "semantic_thought_content_generated",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if run.get(field_name) is not False:
                raise ValueError(f"collection_run.{field_name} must be false")
        results = run.get("collection_results")
        if not isinstance(results, list) or not results:
            raise ValueError(
                "collection_run.collection_results must be a non-empty list"
            )
        if any(not isinstance(result, dict) for result in results):
            raise ValueError(
                "collection_run.collection_results must contain mappings"
            )
        if run.get("result_count") != len(results):
            raise ValueError("collection_run.result_count must match results")
        result_digests = []
        for result in results:
            for field_name in (
                "clinical_diagnosis_claimed",
                "semantic_thought_content_generated",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
            ):
                if result.get(field_name) is not False:
                    raise ValueError(
                        f"collection_result.{field_name} must be false"
                    )
            expected_result_digest = sha256_text(
                canonical_json(self._collection_result_digest_payload(result))
            )
            if result.get("collection_result_digest") != expected_result_digest:
                raise ValueError(
                    "collection_result.collection_result_digest mismatch"
                )
            result_digests.append(expected_result_digest)
        if run.get("result_digests") != result_digests:
            raise ValueError("collection_run.result_digests mismatch")
        expected_result_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_COLLECTION_RUN_PROFILE_ID,
                    "collection_protocol_digest": run.get(
                        "collection_protocol_digest"
                    ),
                    "result_digests": result_digests,
                }
            )
        )
        if run.get("result_digest_set") != expected_result_digest_set:
            raise ValueError("collection_run.result_digest_set mismatch")

    def _check_measurement_quality_gate(self, gate: Dict[str, Any]) -> None:
        if not isinstance(gate, dict):
            raise ValueError("measurement_quality_gate must be a mapping")
        if gate.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("measurement_quality_gate.schema_version mismatch")
        if gate.get("profile_id") != NIW_MEASUREMENT_QUALITY_GATE_PROFILE_ID:
            raise ValueError("measurement_quality_gate.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._measurement_quality_gate_digest_payload(gate))
        )
        if gate.get("measurement_quality_gate_digest") != expected_digest:
            raise ValueError(
                "measurement_quality_gate.measurement_quality_gate_digest mismatch"
            )
        if gate.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("measurement_quality_gate.claim_ceiling mismatch")
        if gate.get("storage_policy") != NIW_MEASUREMENT_QUALITY_GATE_POLICY:
            raise ValueError("measurement_quality_gate.storage_policy mismatch")
        items = gate.get("quality_items")
        if not isinstance(items, list) or not items:
            raise ValueError(
                "measurement_quality_gate.quality_items must be a non-empty list"
            )
        if gate.get("quality_item_count") != len(items):
            raise ValueError(
                "measurement_quality_gate.quality_item_count must match items"
            )
        item_digests = []
        for item in items:
            for field_name in (
                "clinical_diagnosis_claimed",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
            ):
                if item.get(field_name) is not False:
                    raise ValueError(f"quality_item.{field_name} must be false")
            expected_item_digest = sha256_text(
                canonical_json(self._quality_item_digest_payload(item))
            )
            if item.get("quality_item_digest") != expected_item_digest:
                raise ValueError("quality_item.quality_item_digest mismatch")
            item_digests.append(expected_item_digest)
        if gate.get("quality_item_digests") != item_digests:
            raise ValueError(
                "measurement_quality_gate.quality_item_digests mismatch"
            )
        expected_item_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_MEASUREMENT_QUALITY_GATE_PROFILE_ID,
                    "collection_run_digest": gate.get("collection_run_digest"),
                    "quality_item_digests": item_digests,
                }
            )
        )
        if gate.get("quality_item_digest_set") != expected_item_digest_set:
            raise ValueError(
                "measurement_quality_gate.quality_item_digest_set mismatch"
            )
        for field_name in (
            "clinical_diagnosis_claimed",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if gate.get(field_name) is not False:
                raise ValueError(f"measurement_quality_gate.{field_name} must be false")

    def _check_cross_modal_analysis_plan(self, plan: Dict[str, Any]) -> None:
        if not isinstance(plan, dict):
            raise ValueError("cross_modal_analysis_plan must be a mapping")
        if plan.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("cross_modal_analysis_plan.schema_version mismatch")
        if plan.get("profile_id") != NIW_CROSS_MODAL_ANALYSIS_PLAN_PROFILE_ID:
            raise ValueError("cross_modal_analysis_plan.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._cross_modal_analysis_plan_digest_payload(plan))
        )
        if plan.get("cross_modal_analysis_plan_digest") != expected_digest:
            raise ValueError(
                "cross_modal_analysis_plan.cross_modal_analysis_plan_digest mismatch"
            )
        if plan.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("cross_modal_analysis_plan.claim_ceiling mismatch")
        if plan.get("storage_policy") != NIW_CROSS_MODAL_ANALYSIS_PLAN_POLICY:
            raise ValueError("cross_modal_analysis_plan.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if plan.get(field_name) is not False:
                raise ValueError(f"cross_modal_analysis_plan.{field_name} must be false")
        pairs = plan.get("analysis_pairs")
        if not isinstance(pairs, list) or not pairs:
            raise ValueError(
                "cross_modal_analysis_plan.analysis_pairs must be a non-empty list"
            )
        if any(not isinstance(pair, dict) for pair in pairs):
            raise ValueError(
                "cross_modal_analysis_plan.analysis_pairs must contain mappings"
            )
        if plan.get("analysis_pair_count") != len(pairs):
            raise ValueError(
                "cross_modal_analysis_plan.analysis_pair_count must match pairs"
            )
        pair_digests = []
        for pair in pairs:
            for field_name in (
                "clinical_diagnosis_claimed",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
            ):
                if pair.get(field_name) is not False:
                    raise ValueError(
                        f"cross_modal_analysis_pair.{field_name} must be false"
                    )
            expected_pair_digest = sha256_text(
                canonical_json(self._analysis_pair_digest_payload(pair))
            )
            if pair.get("pair_digest") != expected_pair_digest:
                raise ValueError("cross_modal_analysis_pair.pair_digest mismatch")
            pair_digests.append(expected_pair_digest)
        if plan.get("pair_digests") != pair_digests:
            raise ValueError("cross_modal_analysis_plan.pair_digests mismatch")
        expected_pair_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_CROSS_MODAL_ANALYSIS_PLAN_PROFILE_ID,
                    "pair_digests": pair_digests,
                    "connector_bundle_digest": plan.get("connector_bundle_digest"),
                }
            )
        )
        if plan.get("pair_digest_set") != expected_pair_digest_set:
            raise ValueError("cross_modal_analysis_plan.pair_digest_set mismatch")

    def _check_cross_modal_analysis_run(self, run: Dict[str, Any]) -> None:
        if not isinstance(run, dict):
            raise ValueError("cross_modal_analysis_run must be a mapping")
        if run.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("cross_modal_analysis_run.schema_version mismatch")
        if run.get("profile_id") != NIW_CROSS_MODAL_ANALYSIS_RUN_PROFILE_ID:
            raise ValueError("cross_modal_analysis_run.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._cross_modal_analysis_run_digest_payload(run))
        )
        if run.get("cross_modal_analysis_run_digest") != expected_digest:
            raise ValueError(
                "cross_modal_analysis_run.cross_modal_analysis_run_digest mismatch"
            )
        if run.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("cross_modal_analysis_run.claim_ceiling mismatch")
        if run.get("storage_policy") != NIW_CROSS_MODAL_ANALYSIS_RUN_POLICY:
            raise ValueError("cross_modal_analysis_run.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if run.get(field_name) is not False:
                raise ValueError(f"cross_modal_analysis_run.{field_name} must be false")
        results = run.get("pair_results")
        if not isinstance(results, list) or not results:
            raise ValueError(
                "cross_modal_analysis_run.pair_results must be a non-empty list"
            )
        if any(not isinstance(result, dict) for result in results):
            raise ValueError(
                "cross_modal_analysis_run.pair_results must contain mappings"
            )
        if run.get("result_count") != len(results):
            raise ValueError("cross_modal_analysis_run.result_count must match results")
        result_digests = []
        for result in results:
            for field_name in (
                "clinical_diagnosis_claimed",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
            ):
                if result.get(field_name) is not False:
                    raise ValueError(
                        f"cross_modal_analysis_result.{field_name} must be false"
                    )
            expected_result_digest = sha256_text(
                canonical_json(self._analysis_result_digest_payload(result))
            )
            if result.get("result_digest") != expected_result_digest:
                raise ValueError("cross_modal_analysis_result.result_digest mismatch")
            result_digests.append(expected_result_digest)
        if run.get("result_digests") != result_digests:
            raise ValueError("cross_modal_analysis_run.result_digests mismatch")
        expected_result_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_CROSS_MODAL_ANALYSIS_RUN_PROFILE_ID,
                    "result_digests": result_digests,
                    "cross_modal_analysis_plan_digest": run.get(
                        "cross_modal_analysis_plan_digest"
                    ),
                }
            )
        )
        if run.get("result_digest_set") != expected_result_digest_set:
            raise ValueError("cross_modal_analysis_run.result_digest_set mismatch")

    def _check_interpretation_synthesis(
        self,
        synthesis: Dict[str, Any],
    ) -> None:
        if not isinstance(synthesis, dict):
            raise ValueError("interpretation_synthesis must be a mapping")
        if synthesis.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("interpretation_synthesis.schema_version mismatch")
        if synthesis.get("profile_id") != NIW_INTERPRETATION_SYNTHESIS_PROFILE_ID:
            raise ValueError("interpretation_synthesis.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._interpretation_synthesis_digest_payload(synthesis))
        )
        if synthesis.get("interpretation_synthesis_digest") != expected_digest:
            raise ValueError(
                "interpretation_synthesis.interpretation_synthesis_digest mismatch"
            )
        if synthesis.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("interpretation_synthesis.claim_ceiling mismatch")
        if synthesis.get("storage_policy") != NIW_INTERPRETATION_SYNTHESIS_POLICY:
            raise ValueError("interpretation_synthesis.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
            "upload_readiness_claimed",
        ):
            if synthesis.get(field_name) is not False:
                raise ValueError(f"interpretation_synthesis.{field_name} must be false")
        cards = synthesis.get("synthesis_cards")
        if not isinstance(cards, list) or not cards:
            raise ValueError(
                "interpretation_synthesis.synthesis_cards must be a non-empty list"
            )
        if any(not isinstance(card, dict) for card in cards):
            raise ValueError(
                "interpretation_synthesis.synthesis_cards must contain mappings"
            )
        if synthesis.get("synthesis_card_count") != len(cards):
            raise ValueError(
                "interpretation_synthesis.synthesis_card_count must match cards"
            )
        card_digests = []
        for card in cards:
            for field_name in (
                "clinical_diagnosis_claimed",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
                "upload_readiness_claimed",
            ):
                if card.get(field_name) is not False:
                    raise ValueError(f"synthesis_card.{field_name} must be false")
            expected_card_digest = sha256_text(
                canonical_json(self._synthesis_card_digest_payload(card))
            )
            if card.get("synthesis_card_digest") != expected_card_digest:
                raise ValueError("synthesis_card.synthesis_card_digest mismatch")
            card_digests.append(expected_card_digest)
        if synthesis.get("synthesis_card_digests") != card_digests:
            raise ValueError("interpretation_synthesis.synthesis_card_digests mismatch")
        expected_card_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_INTERPRETATION_SYNTHESIS_PROFILE_ID,
                    "cross_modal_analysis_run_digest": synthesis.get(
                        "cross_modal_analysis_run_digest"
                    ),
                    "synthesis_card_digests": card_digests,
                }
            )
        )
        if synthesis.get("synthesis_card_digest_set") != expected_card_digest_set:
            raise ValueError(
                "interpretation_synthesis.synthesis_card_digest_set mismatch"
            )

    def _check_longitudinal_timeline(
        self,
        timeline: Dict[str, Any],
    ) -> None:
        if not isinstance(timeline, dict):
            raise ValueError("longitudinal_timeline must be a mapping")
        if timeline.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("longitudinal_timeline.schema_version mismatch")
        if timeline.get("profile_id") != NIW_LONGITUDINAL_TIMELINE_PROFILE_ID:
            raise ValueError("longitudinal_timeline.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._longitudinal_timeline_digest_payload(timeline))
        )
        if timeline.get("longitudinal_timeline_digest") != expected_digest:
            raise ValueError(
                "longitudinal_timeline.longitudinal_timeline_digest mismatch"
            )
        if timeline.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("longitudinal_timeline.claim_ceiling mismatch")
        if timeline.get("storage_policy") != NIW_LONGITUDINAL_TIMELINE_POLICY:
            raise ValueError("longitudinal_timeline.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "semantic_thought_content_generated",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
            "upload_readiness_claimed",
        ):
            if timeline.get(field_name) is not False:
                raise ValueError(f"longitudinal_timeline.{field_name} must be false")
        if timeline.get("window_count", 0) < 2:
            raise ValueError("longitudinal_timeline.window_count must be at least two")
        if len(timeline.get("source_bundle_refs", [])) != timeline.get("window_count"):
            raise ValueError("longitudinal_timeline.source_bundle_refs mismatch")
        if len(timeline.get("source_bundle_digests", [])) != timeline.get("window_count"):
            raise ValueError("longitudinal_timeline.source_bundle_digests mismatch")
        items = timeline.get("source_type_axis_drifts")
        if not isinstance(items, list) or not items:
            raise ValueError(
                "longitudinal_timeline.source_type_axis_drifts must be a non-empty list"
            )
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(
                    "longitudinal_timeline.source_type_axis_drifts must contain mappings"
                )
            for field_name in (
                "clinical_diagnosis_claimed",
                "semantic_thought_content_generated",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
                "upload_readiness_claimed",
            ):
                if item.get(field_name) is not False:
                    raise ValueError(f"axis_drift.{field_name} must be false")
            expected_item_digest = sha256_text(
                canonical_json(self._axis_drift_digest_payload(item))
            )
            if item.get("axis_drift_digest") != expected_item_digest:
                raise ValueError("axis_drift.axis_drift_digest mismatch")

    def _check_operator_runbook(
        self,
        runbook: Dict[str, Any],
    ) -> None:
        if not isinstance(runbook, dict):
            raise ValueError("operator_runbook must be a mapping")
        if runbook.get("schema_version") != NIW_SCHEMA_VERSION:
            raise ValueError("operator_runbook.schema_version mismatch")
        if runbook.get("profile_id") != NIW_OPERATOR_RUNBOOK_PROFILE_ID:
            raise ValueError("operator_runbook.profile_id mismatch")
        expected_digest = sha256_text(
            canonical_json(self._operator_runbook_digest_payload(runbook))
        )
        if runbook.get("operator_runbook_digest") != expected_digest:
            raise ValueError("operator_runbook.operator_runbook_digest mismatch")
        if runbook.get("claim_ceiling") != NIW_CLAIM_CEILING:
            raise ValueError("operator_runbook.claim_ceiling mismatch")
        if runbook.get("storage_policy") != NIW_OPERATOR_RUNBOOK_POLICY:
            raise ValueError("operator_runbook.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "semantic_thought_content_generated",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
            "upload_readiness_claimed",
        ):
            if runbook.get(field_name) is not False:
                raise ValueError(f"operator_runbook.{field_name} must be false")
        bindings = runbook.get("receipt_bindings")
        if not isinstance(bindings, list) or not bindings:
            raise ValueError("operator_runbook.receipt_bindings must be non-empty")
        binding_digests = []
        for binding in bindings:
            if not isinstance(binding, dict):
                raise ValueError(
                    "operator_runbook.receipt_bindings must contain mappings"
                )
            for field_name in (
                "clinical_diagnosis_claimed",
                "semantic_thought_content_generated",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
                "upload_readiness_claimed",
            ):
                if binding.get(field_name) is not False:
                    raise ValueError(f"receipt_binding.{field_name} must be false")
            expected_binding_digest = sha256_text(
                canonical_json(
                    {
                        "receipt_role": binding.get("receipt_role"),
                        "receipt_ref": binding.get("receipt_ref"),
                        "receipt_digest": binding.get("receipt_digest"),
                        "profile_id": binding.get("profile_id"),
                        "bound": binding.get("bound"),
                    }
                )
            )
            if binding.get("receipt_binding_digest") != expected_binding_digest:
                raise ValueError("receipt_binding.receipt_binding_digest mismatch")
            binding_digests.append(expected_binding_digest)
        expected_receipt_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_OPERATOR_RUNBOOK_PROFILE_ID,
                    "receipt_binding_digests": binding_digests,
                    "receipt_roles": [
                        binding.get("receipt_role") for binding in bindings
                    ],
                }
            )
        )
        if runbook.get("receipt_digest_set") != expected_receipt_digest_set:
            raise ValueError("operator_runbook.receipt_digest_set mismatch")
        steps = runbook.get("workflow_steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError("operator_runbook.workflow_steps must be non-empty")
        if runbook.get("workflow_step_count") != len(steps):
            raise ValueError("operator_runbook.workflow_step_count mismatch")
        step_digests = []
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError(
                    "operator_runbook.workflow_steps must contain mappings"
                )
            for field_name in (
                "clinical_diagnosis_claimed",
                "semantic_thought_content_generated",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
                "upload_readiness_claimed",
            ):
                if step.get(field_name) is not False:
                    raise ValueError(f"runbook_step.{field_name} must be false")
            expected_step_digest = sha256_text(
                canonical_json(self._operator_runbook_step_digest_payload(step))
            )
            if step.get("runbook_step_digest") != expected_step_digest:
                raise ValueError("runbook_step.runbook_step_digest mismatch")
            step_digests.append(expected_step_digest)
        if runbook.get("workflow_step_digests") != step_digests:
            raise ValueError("operator_runbook.workflow_step_digests mismatch")
        expected_step_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": NIW_OPERATOR_RUNBOOK_PROFILE_ID,
                    "step_digests": step_digests,
                    "longitudinal_timeline_digest": runbook.get(
                        "longitudinal_timeline_digest"
                    ),
                }
            )
        )
        if runbook.get("workflow_step_digest_set") != expected_step_digest_set:
            raise ValueError("operator_runbook.workflow_step_digest_set mismatch")

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

    def _collection_protocol_payload_redacted(self, protocol: Dict[str, Any]) -> bool:
        protocol_raw_flags = all(
            protocol.get(field_name) is False
            for field_name in protocol
            if field_name.startswith("raw_")
        )
        step_raw_flags = all(
            step.get(field_name) is False
            for step in protocol.get("collection_steps", [])
            if isinstance(step, dict)
            for field_name in step
            if field_name.startswith("raw_")
        )
        return protocol_raw_flags and step_raw_flags

    def _collection_run_payload_redacted(self, run: Dict[str, Any]) -> bool:
        run_raw_flags = all(
            run.get(field_name) is False
            for field_name in run
            if field_name.startswith("raw_")
        )
        result_raw_flags = all(
            result.get(field_name) is False
            for result in run.get("collection_results", [])
            if isinstance(result, dict)
            for field_name in result
            if field_name.startswith("raw_")
        )
        return run_raw_flags and result_raw_flags

    def _measurement_quality_gate_payload_redacted(
        self,
        gate: Dict[str, Any],
    ) -> bool:
        gate_raw_flags = all(
            gate.get(field_name) is False
            for field_name in gate
            if field_name.startswith("raw_")
        )
        item_raw_flags = all(
            item.get(field_name) is False
            for item in gate.get("quality_items", [])
            if isinstance(item, dict)
            for field_name in item
            if field_name.startswith("raw_")
        )
        return gate_raw_flags and item_raw_flags

    def _cross_modal_analysis_payload_redacted(self, plan: Dict[str, Any]) -> bool:
        plan_raw_flags = all(
            plan.get(field_name) is False
            for field_name in plan
            if field_name.startswith("raw_")
        )
        pair_raw_flags = all(
            pair.get(field_name) is False
            for pair in plan.get("analysis_pairs", [])
            if isinstance(pair, dict)
            for field_name in pair
            if field_name.startswith("raw_")
        )
        return plan_raw_flags and pair_raw_flags

    def _cross_modal_analysis_run_payload_redacted(self, run: Dict[str, Any]) -> bool:
        run_raw_flags = all(
            run.get(field_name) is False
            for field_name in run
            if field_name.startswith("raw_")
        )
        result_raw_flags = all(
            result.get(field_name) is False
            for result in run.get("pair_results", [])
            if isinstance(result, dict)
            for field_name in result
            if field_name.startswith("raw_")
        )
        return run_raw_flags and result_raw_flags

    def _interpretation_synthesis_payload_redacted(
        self,
        synthesis: Dict[str, Any],
    ) -> bool:
        synthesis_raw_flags = all(
            synthesis.get(field_name) is False
            for field_name in synthesis
            if field_name.startswith("raw_")
        )
        card_raw_flags = all(
            card.get(field_name) is False
            for card in synthesis.get("synthesis_cards", [])
            if isinstance(card, dict)
            for field_name in card
            if field_name.startswith("raw_")
        )
        return synthesis_raw_flags and card_raw_flags

    def _longitudinal_timeline_payload_redacted(
        self,
        timeline: Dict[str, Any],
    ) -> bool:
        timeline_raw_flags = all(
            timeline.get(field_name) is False
            for field_name in timeline
            if field_name.startswith("raw_")
        )
        item_raw_flags = all(
            item.get(field_name) is False
            for item in timeline.get("source_type_axis_drifts", [])
            if isinstance(item, dict)
            for field_name in item
            if field_name.startswith("raw_")
        )
        return timeline_raw_flags and item_raw_flags

    def _operator_runbook_payload_redacted(
        self,
        runbook: Dict[str, Any],
    ) -> bool:
        runbook_raw_flags = all(
            runbook.get(field_name) is False
            for field_name in runbook
            if field_name.startswith("raw_")
        )
        binding_raw_flags = all(
            binding.get(field_name) is False
            for binding in runbook.get("receipt_bindings", [])
            if isinstance(binding, dict)
            for field_name in binding
            if field_name.startswith("raw_")
        )
        step_raw_flags = all(
            step.get(field_name) is False
            for step in runbook.get("workflow_steps", [])
            if isinstance(step, dict)
            for field_name in step
            if field_name.startswith("raw_")
        )
        return runbook_raw_flags and binding_raw_flags and step_raw_flags

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

    def _analysis_pair_digest_payload(self, pair: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source_types": pair.get("source_types"),
            "source_families": pair.get("source_families"),
            "source_feature_digests": pair.get("source_feature_digests"),
            "analysis_recipe_id": pair.get("analysis_recipe_id"),
            "target_constructs": pair.get("target_constructs"),
            "plain_language_question": pair.get("plain_language_question"),
            "agent_action": pair.get("agent_action"),
            "seed_analysis_digest": pair.get("seed_analysis_digest"),
            "connector_support": pair.get("connector_support"),
            "all_required_connectors_bound": pair.get(
                "all_required_connectors_bound"
            ),
            "requires_ml_expertise": pair.get("requires_ml_expertise"),
            "claim_ceiling": pair.get("claim_ceiling"),
        }

    def _analysis_result_digest_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "pair_digest": result.get("pair_digest"),
            "source_types": result.get("source_types"),
            "analysis_recipe_id": result.get("analysis_recipe_id"),
            "result_status": result.get("result_status"),
            "result_axis_summary": result.get("result_axis_summary"),
            "operator_summary": result.get("operator_summary"),
            "agent_next_action": result.get("agent_next_action"),
            "evidence_refs": result.get("evidence_refs"),
            "requires_ml_expertise": result.get("requires_ml_expertise"),
            "result_bound": result.get("result_bound"),
            "claim_ceiling": result.get("claim_ceiling"),
        }

    def _synthesis_card_digest_payload(self, card: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "result_digest": card.get("result_digest"),
            "source_types": card.get("source_types"),
            "analysis_recipe_id": card.get("analysis_recipe_id"),
            "interpretation_status": card.get("interpretation_status"),
            "plain_language_summary": card.get("plain_language_summary"),
            "operator_next_action": card.get("operator_next_action"),
            "coding_agent_task": card.get("coding_agent_task"),
            "quality_item_digests": card.get("quality_item_digests"),
            "interpretation_axis_summary": card.get(
                "interpretation_axis_summary"
            ),
            "evidence_refs": card.get("evidence_refs"),
            "requires_ml_expertise": card.get("requires_ml_expertise"),
            "synthesis_card_bound": card.get("synthesis_card_bound"),
            "claim_ceiling": card.get("claim_ceiling"),
        }

    def _axis_drift_digest_payload(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source_type": item.get("source_type"),
            "source_family": item.get("source_family"),
            "window_count": item.get("window_count"),
            "source_refs": item.get("source_refs"),
            "feature_digests": item.get("feature_digests"),
            "common_analysis_axes": item.get("common_analysis_axes"),
            "axis_delta_summary": item.get("axis_delta_summary"),
            "axis_drift_summary": item.get("axis_drift_summary"),
            "axis_drift_bound": item.get("axis_drift_bound"),
            "operator_summary": item.get("operator_summary"),
            "agent_next_action": item.get("agent_next_action"),
            "requires_ml_expertise": item.get("requires_ml_expertise"),
            "claim_ceiling": item.get("claim_ceiling"),
            "semantic_thought_content_generated": item.get(
                "semantic_thought_content_generated"
            ),
        }

    def _operator_runbook_step_digest_payload(
        self,
        step: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "position": step.get("position"),
            "step_id": step.get("step_id"),
            "stage_kind": step.get("stage_kind"),
            "source_types": step.get("source_types"),
            "input_receipt_digests": step.get("input_receipt_digests"),
            "operator_card": step.get("operator_card"),
            "coding_agent_task": step.get("coding_agent_task"),
            "required_checks": step.get("required_checks"),
            "requires_ml_expertise": step.get("requires_ml_expertise"),
            "runbook_step_bound": step.get("runbook_step_bound"),
            "claim_ceiling": step.get("claim_ceiling"),
            "semantic_thought_content_generated": step.get(
                "semantic_thought_content_generated"
            ),
        }

    def _collection_step_digest_payload(self, step: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source_type": step.get("source_type"),
            "source_family": step.get("source_family"),
            "source_ref": step.get("source_ref"),
            "participant_ref": step.get("participant_ref"),
            "consent_ref": step.get("consent_ref"),
            "license_ref": step.get("license_ref"),
            "feature_summary_ref": step.get("feature_summary_ref"),
            "feature_digest": step.get("feature_digest"),
            "collection_window_ref": step.get("collection_window_ref"),
            "collection_method_id": step.get("collection_method_id"),
            "measurement_connector_refs": step.get("measurement_connector_refs"),
            "measurement_connector_digests": step.get(
                "measurement_connector_digests"
            ),
            "measurement_connector_bound": step.get("measurement_connector_bound"),
            "collection_axis_summary": step.get("collection_axis_summary"),
            "operator_summary": step.get("operator_summary"),
            "agent_next_action": step.get("agent_next_action"),
            "requires_ml_expertise": step.get("requires_ml_expertise"),
            "collection_step_bound": step.get("collection_step_bound"),
            "claim_ceiling": step.get("claim_ceiling"),
            "semantic_thought_content_generated": step.get(
                "semantic_thought_content_generated"
            ),
        }

    def _collection_result_digest_payload(
        self,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "collection_step_digest": result.get("collection_step_digest"),
            "source_type": result.get("source_type"),
            "source_family": result.get("source_family"),
            "source_ref": result.get("source_ref"),
            "feature_summary_ref": result.get("feature_summary_ref"),
            "feature_digest": result.get("feature_digest"),
            "collection_window_ref": result.get("collection_window_ref"),
            "collection_method_id": result.get("collection_method_id"),
            "measurement_connector_refs": result.get(
                "measurement_connector_refs"
            ),
            "measurement_connector_digests": result.get(
                "measurement_connector_digests"
            ),
            "collection_status": result.get("collection_status"),
            "collection_quality_summary": result.get(
                "collection_quality_summary"
            ),
            "operator_summary": result.get("operator_summary"),
            "agent_next_action": result.get("agent_next_action"),
            "evidence_refs": result.get("evidence_refs"),
            "requires_ml_expertise": result.get("requires_ml_expertise"),
            "collection_result_bound": result.get("collection_result_bound"),
            "claim_ceiling": result.get("claim_ceiling"),
            "semantic_thought_content_generated": result.get(
                "semantic_thought_content_generated"
            ),
        }

    def _quality_item_digest_payload(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "source_type": item.get("source_type"),
            "source_family": item.get("source_family"),
            "source_ref": item.get("source_ref"),
            "feature_summary_ref": item.get("feature_summary_ref"),
            "feature_digest": item.get("feature_digest"),
            "collection_result_digest": item.get(
                "collection_result_digest"
            ),
            "collection_window_ref": item.get("collection_window_ref"),
            "measurement_connector_refs": item.get(
                "measurement_connector_refs"
            ),
            "measurement_connector_digests": item.get(
                "measurement_connector_digests"
            ),
            "calibration_ref": item.get("calibration_ref"),
            "artifact_qc_ref": item.get("artifact_qc_ref"),
            "consent_freshness_ref": item.get("consent_freshness_ref"),
            "operator_review_ref": item.get("operator_review_ref"),
            "quality_authority_ref": item.get("quality_authority_ref"),
            "quality_axis_summary": item.get("quality_axis_summary"),
            "quality_gate_status": item.get("quality_gate_status"),
            "operator_summary": item.get("operator_summary"),
            "agent_next_action": item.get("agent_next_action"),
            "evidence_refs": item.get("evidence_refs"),
            "requires_ml_expertise": item.get("requires_ml_expertise"),
            "quality_item_bound": item.get("quality_item_bound"),
            "claim_ceiling": item.get("claim_ceiling"),
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

    def _collection_protocol_digest_payload(
        self,
        protocol: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": protocol.get("profile_id"),
            "identity_id": protocol.get("identity_id"),
            "source_bundle_digest": protocol.get("source_bundle_digest"),
            "replacement_plan_digest": protocol.get("replacement_plan_digest"),
            "connector_bundle_digest": protocol.get("connector_bundle_digest"),
            "source_types": protocol.get("source_types"),
            "source_type_count": protocol.get("source_type_count"),
            "collection_step_count": protocol.get("collection_step_count"),
            "collection_step_digest_set": protocol.get(
                "collection_step_digest_set"
            ),
            "all_sources_collection_bound": protocol.get(
                "all_sources_collection_bound"
            ),
            "seed_survey_eeg_collection_bound": protocol.get(
                "seed_survey_eeg_collection_bound"
            ),
            "expansion_collection_bound": protocol.get(
                "expansion_collection_bound"
            ),
            "measurement_connector_coverage_bound": protocol.get(
                "measurement_connector_coverage_bound"
            ),
            "non_ml_operator_ready": protocol.get("non_ml_operator_ready"),
            "coding_agent_ready": protocol.get("coding_agent_ready"),
            "collection_protocol_bound": protocol.get(
                "collection_protocol_bound"
            ),
            "storage_policy": protocol.get("storage_policy"),
            "claim_ceiling": protocol.get("claim_ceiling"),
            "semantic_thought_content_generated": protocol.get(
                "semantic_thought_content_generated"
            ),
        }

    def _collection_run_digest_payload(
        self,
        run: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": run.get("profile_id"),
            "identity_id": run.get("identity_id"),
            "source_bundle_digest": run.get("source_bundle_digest"),
            "connector_bundle_digest": run.get("connector_bundle_digest"),
            "collection_protocol_digest": run.get(
                "collection_protocol_digest"
            ),
            "collection_step_count": run.get("collection_step_count"),
            "result_count": run.get("result_count"),
            "result_digest_set": run.get("result_digest_set"),
            "all_collection_results_bound": run.get(
                "all_collection_results_bound"
            ),
            "seed_survey_eeg_collection_result_bound": run.get(
                "seed_survey_eeg_collection_result_bound"
            ),
            "expansion_collection_result_bound": run.get(
                "expansion_collection_result_bound"
            ),
            "operator_review_ready": run.get("operator_review_ready"),
            "coding_agent_review_ready": run.get("coding_agent_review_ready"),
            "collection_summary": run.get("collection_summary"),
            "collection_run_bound": run.get("collection_run_bound"),
            "claim_ceiling": run.get("claim_ceiling"),
            "semantic_thought_content_generated": run.get(
                "semantic_thought_content_generated"
            ),
        }

    def _measurement_quality_gate_digest_payload(
        self,
        gate: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": gate.get("profile_id"),
            "identity_id": gate.get("identity_id"),
            "source_bundle_digest": gate.get("source_bundle_digest"),
            "collection_run_digest": gate.get("collection_run_digest"),
            "source_types": gate.get("source_types"),
            "source_type_count": gate.get("source_type_count"),
            "quality_item_count": gate.get("quality_item_count"),
            "quality_item_digest_set": gate.get("quality_item_digest_set"),
            "all_quality_items_bound": gate.get("all_quality_items_bound"),
            "seed_survey_eeg_quality_bound": gate.get(
                "seed_survey_eeg_quality_bound"
            ),
            "expansion_quality_bound": gate.get("expansion_quality_bound"),
            "calibration_refs_bound": gate.get("calibration_refs_bound"),
            "artifact_qc_refs_bound": gate.get("artifact_qc_refs_bound"),
            "consent_freshness_bound": gate.get("consent_freshness_bound"),
            "operator_review_ready": gate.get("operator_review_ready"),
            "coding_agent_review_ready": gate.get("coding_agent_review_ready"),
            "quality_summary": gate.get("quality_summary"),
            "measurement_quality_gate_bound": gate.get(
                "measurement_quality_gate_bound"
            ),
            "storage_policy": gate.get("storage_policy"),
            "claim_ceiling": gate.get("claim_ceiling"),
        }

    def _cross_modal_analysis_plan_digest_payload(
        self,
        plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": plan.get("profile_id"),
            "identity_id": plan.get("identity_id"),
            "source_bundle_digest": plan.get("source_bundle_digest"),
            "analysis_digest": plan.get("analysis_digest"),
            "operator_guide_digest": plan.get("operator_guide_digest"),
            "replacement_plan_digest": plan.get("replacement_plan_digest"),
            "connector_bundle_digest": plan.get("connector_bundle_digest"),
            "source_types": plan.get("source_types"),
            "source_families": plan.get("source_families"),
            "analysis_pair_count": plan.get("analysis_pair_count"),
            "expected_analysis_pair_count": plan.get(
                "expected_analysis_pair_count"
            ),
            "pair_digest_set": plan.get("pair_digest_set"),
            "recipe_catalog": plan.get("recipe_catalog"),
            "all_source_types_represented": plan.get(
                "all_source_types_represented"
            ),
            "source_pair_coverage_bound": plan.get(
                "source_pair_coverage_bound"
            ),
            "survey_eeg_seed_analysis_bound": plan.get(
                "survey_eeg_seed_analysis_bound"
            ),
            "connector_bundle_bound": plan.get("connector_bundle_bound"),
            "non_ml_operator_ready": plan.get("non_ml_operator_ready"),
            "coding_agent_ready": plan.get("coding_agent_ready"),
            "cross_modal_analysis_plan_bound": plan.get(
                "cross_modal_analysis_plan_bound"
            ),
            "planning_scope": plan.get("planning_scope"),
            "claim_ceiling": plan.get("claim_ceiling"),
        }

    def _cross_modal_analysis_run_digest_payload(
        self,
        run: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": run.get("profile_id"),
            "identity_id": run.get("identity_id"),
            "source_bundle_digest": run.get("source_bundle_digest"),
            "connector_bundle_digest": run.get("connector_bundle_digest"),
            "cross_modal_analysis_plan_digest": run.get(
                "cross_modal_analysis_plan_digest"
            ),
            "analysis_pair_count": run.get("analysis_pair_count"),
            "result_count": run.get("result_count"),
            "result_digest_set": run.get("result_digest_set"),
            "all_pair_results_bound": run.get("all_pair_results_bound"),
            "seed_survey_eeg_result_bound": run.get(
                "seed_survey_eeg_result_bound"
            ),
            "operator_review_ready": run.get("operator_review_ready"),
            "coding_agent_review_ready": run.get("coding_agent_review_ready"),
            "result_summary": run.get("result_summary"),
            "cross_modal_analysis_run_bound": run.get(
                "cross_modal_analysis_run_bound"
            ),
            "claim_ceiling": run.get("claim_ceiling"),
        }

    def _interpretation_synthesis_digest_payload(
        self,
        synthesis: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": synthesis.get("profile_id"),
            "identity_id": synthesis.get("identity_id"),
            "source_bundle_digest": synthesis.get("source_bundle_digest"),
            "operator_guide_digest": synthesis.get("operator_guide_digest"),
            "measurement_quality_gate_digest": synthesis.get(
                "measurement_quality_gate_digest"
            ),
            "cross_modal_analysis_run_digest": synthesis.get(
                "cross_modal_analysis_run_digest"
            ),
            "source_types": synthesis.get("source_types"),
            "source_type_count": synthesis.get("source_type_count"),
            "synthesis_card_count": synthesis.get("synthesis_card_count"),
            "synthesis_card_digest_set": synthesis.get(
                "synthesis_card_digest_set"
            ),
            "all_synthesis_cards_bound": synthesis.get(
                "all_synthesis_cards_bound"
            ),
            "seed_survey_eeg_synthesis_bound": synthesis.get(
                "seed_survey_eeg_synthesis_bound"
            ),
            "expansion_synthesis_bound": synthesis.get(
                "expansion_synthesis_bound"
            ),
            "operator_action_ready": synthesis.get("operator_action_ready"),
            "coding_agent_action_ready": synthesis.get(
                "coding_agent_action_ready"
            ),
            "beginner_operator_supported": synthesis.get(
                "beginner_operator_supported"
            ),
            "llm_native_workflow_bound": synthesis.get(
                "llm_native_workflow_bound"
            ),
            "synthesis_summary": synthesis.get("synthesis_summary"),
            "interpretation_synthesis_bound": synthesis.get(
                "interpretation_synthesis_bound"
            ),
            "storage_policy": synthesis.get("storage_policy"),
            "claim_ceiling": synthesis.get("claim_ceiling"),
        }

    def _longitudinal_timeline_digest_payload(
        self,
        timeline: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": timeline.get("profile_id"),
            "identity_id": timeline.get("identity_id"),
            "operator_guide_digest": timeline.get("operator_guide_digest"),
            "source_bundle_digests": timeline.get("source_bundle_digests"),
            "window_count": timeline.get("window_count"),
            "source_types": timeline.get("source_types"),
            "stable_source_types": timeline.get("stable_source_types"),
            "missing_source_types_by_window": timeline.get(
                "missing_source_types_by_window"
            ),
            "source_type_axis_drifts": [
                {
                    "source_type": item.get("source_type"),
                    "axis_drift_digest": item.get("axis_drift_digest"),
                    "axis_drift_bound": item.get("axis_drift_bound"),
                }
                for item in timeline.get("source_type_axis_drifts", [])
                if isinstance(item, dict)
            ],
            "timeline_summary": timeline.get("timeline_summary"),
            "all_windows_bound": timeline.get("all_windows_bound"),
            "seed_survey_eeg_timeline_bound": timeline.get(
                "seed_survey_eeg_timeline_bound"
            ),
            "source_type_timeline_coverage_bound": timeline.get(
                "source_type_timeline_coverage_bound"
            ),
            "upstream_fusion_timeline_bound": timeline.get(
                "upstream_fusion_timeline_bound"
            ),
            "all_axis_drifts_bound": timeline.get("all_axis_drifts_bound"),
            "operator_review_ready": timeline.get("operator_review_ready"),
            "coding_agent_review_ready": timeline.get("coding_agent_review_ready"),
            "longitudinal_timeline_bound": timeline.get(
                "longitudinal_timeline_bound"
            ),
            "storage_policy": timeline.get("storage_policy"),
            "claim_ceiling": timeline.get("claim_ceiling"),
            "semantic_thought_content_generated": timeline.get(
                "semantic_thought_content_generated"
            ),
        }

    def _operator_runbook_digest_payload(
        self,
        runbook: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": runbook.get("profile_id"),
            "identity_id": runbook.get("identity_id"),
            "source_bundle_digest": runbook.get("source_bundle_digest"),
            "workspace_digest": runbook.get("workspace_digest"),
            "analysis_digest": runbook.get("analysis_digest"),
            "operator_guide_digest": runbook.get("operator_guide_digest"),
            "replacement_plan_digest": runbook.get("replacement_plan_digest"),
            "connector_bundle_digest": runbook.get("connector_bundle_digest"),
            "collection_protocol_digest": runbook.get(
                "collection_protocol_digest"
            ),
            "collection_run_digest": runbook.get("collection_run_digest"),
            "measurement_quality_gate_digest": runbook.get(
                "measurement_quality_gate_digest"
            ),
            "cross_modal_analysis_plan_digest": runbook.get(
                "cross_modal_analysis_plan_digest"
            ),
            "cross_modal_analysis_run_digest": runbook.get(
                "cross_modal_analysis_run_digest"
            ),
            "interpretation_synthesis_digest": runbook.get(
                "interpretation_synthesis_digest"
            ),
            "longitudinal_timeline_digest": runbook.get(
                "longitudinal_timeline_digest"
            ),
            "source_types": runbook.get("source_types"),
            "source_type_count": runbook.get("source_type_count"),
            "required_replacement_lanes": runbook.get(
                "required_replacement_lanes"
            ),
            "receipt_digest_set": runbook.get("receipt_digest_set"),
            "workflow_step_count": runbook.get("workflow_step_count"),
            "workflow_step_digest_set": runbook.get(
                "workflow_step_digest_set"
            ),
            "all_required_receipts_bound": runbook.get(
                "all_required_receipts_bound"
            ),
            "all_workflow_steps_bound": runbook.get(
                "all_workflow_steps_bound"
            ),
            "operator_cards_bound": runbook.get("operator_cards_bound"),
            "coding_agent_tasks_bound": runbook.get(
                "coding_agent_tasks_bound"
            ),
            "beginner_operator_supported": runbook.get(
                "beginner_operator_supported"
            ),
            "llm_native_workflow_bound": runbook.get(
                "llm_native_workflow_bound"
            ),
            "coding_agent_ready": runbook.get("coding_agent_ready"),
            "operator_runbook_summary": runbook.get(
                "operator_runbook_summary"
            ),
            "operator_runbook_bound": runbook.get("operator_runbook_bound"),
            "storage_policy": runbook.get("storage_policy"),
            "claim_ceiling": runbook.get("claim_ceiling"),
            "semantic_thought_content_generated": runbook.get(
                "semantic_thought_content_generated"
            ),
        }
