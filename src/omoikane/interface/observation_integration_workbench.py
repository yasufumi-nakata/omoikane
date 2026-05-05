"""Observation integration workbench reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

UOI_SCHEMA_VERSION = "1.0"
UOI_TAXONOMY_PROFILE_ID = "universal-human-observation-taxonomy-v1"
UOI_METHOD_CATALOG_PROFILE_ID = "universal-observation-method-catalog-v1"
UOI_BUNDLE_PROFILE_ID = "universal-observation-source-bundle-v1"
UOI_GRAPH_PROFILE_ID = "universal-observation-integration-graph-v1"
UOI_PLAN_PROFILE_ID = "universal-observation-analysis-plan-v1"
UOI_ANALYSIS_RUN_PROFILE_ID = "universal-observation-analysis-run-v1"
UOI_OPERATOR_GUIDE_PROFILE_ID = "universal-observation-operator-guide-v1"
UOI_CLAIM_CEILING = "cross-domain-feature-integration-plan-only"
UOI_STORAGE_POLICY = "feature-digest+provenance+axis-summary-only"
UOI_ANALYSIS_RUN_POLICY = "lane-digest+bounded-result-summary+operator-review-only"
UOI_CONFLICT_SINK_URL = "https://mind-upload.com/frontiers/universal-observation-integration"
UOI_REQUIRED_ALIGNMENT_AXES = (
    "provenance",
    "rights",
    "time",
    "space",
    "unit",
    "uncertainty",
    "entity",
)
UOI_REQUIRED_ANALYSIS_LANES = (
    "ingest",
    "normalize",
    "align",
    "model",
    "audit",
    "publish-digest",
)
UOI_MEASUREMENT_FAMILIES = {
    "human_biodata": (
        "eeg",
        "ecg",
        "ppg",
        "eda",
        "respiration",
        "wearable_biosignal",
    ),
    "neuroscience": (
        "fmri_bold",
        "meg",
        "connectome",
        "brain_organoid",
        "behavioral_task",
    ),
    "clinical_health": (
        "ehr",
        "imaging_study",
        "lab_result",
        "medication_record",
    ),
    "molecular_omics": (
        "genomics",
        "transcriptomics",
        "proteomics",
        "metabolomics",
        "microbiome",
    ),
    "environmental_earth": (
        "climate_record",
        "weather_station",
        "ocean_sensor",
        "air_quality",
        "hydrology",
    ),
    "geospatial_remote_sensing": (
        "satellite_imagery",
        "lidar",
        "radar",
        "gis_layer",
        "gps_trace",
    ),
    "astronomical_cosmological": (
        "telescope_image",
        "spectrograph",
        "gravitational_wave",
        "cosmic_microwave_background",
    ),
    "physics_particle_wave": (
        "particle_detector",
        "accelerator_run",
        "plasma_diagnostic",
        "quantum_measurement",
    ),
    "chemical_materials": (
        "mass_spectrometry",
        "chromatography",
        "xray_diffraction",
        "materials_assay",
    ),
    "ecology_biodiversity": (
        "species_observation",
        "habitat_survey",
        "camera_trap",
        "bioacoustic_recording",
    ),
    "agriculture_food": (
        "crop_sensor",
        "soil_sample",
        "food_composition",
        "livestock_record",
    ),
    "industrial_iot": (
        "machine_sensor",
        "factory_quality_log",
        "robot_telemetry",
        "energy_meter",
    ),
    "social_economic": (
        "survey",
        "census",
        "transaction_aggregate",
        "mobility_aggregate",
        "market_series",
    ),
    "cultural_text_media": (
        "text_archive",
        "audio_recording",
        "image_archive",
        "video_recording",
        "museum_catalog",
    ),
    "software_digital_telemetry": (
        "log_event",
        "trace_span",
        "metrics_series",
        "version_history",
    ),
    "historical_archival": (
        "manuscript",
        "administrative_record",
        "oral_history",
        "archaeological_context",
    ),
}
UOI_MEASUREMENT_METHOD_FAMILIES = {
    "self_report_and_survey": (
        "questionnaire",
        "interview",
        "diary",
        "psychometric_scale",
        "ecological_momentary_assessment",
    ),
    "electrophysiology_and_biosignal": (
        "eeg_recording",
        "ecg_recording",
        "emg_recording",
        "ppg_recording",
        "eda_recording",
        "respiration_belt",
        "polysomnography",
    ),
    "imaging_and_remote_sensing": (
        "microscopy",
        "xray_imaging",
        "ct_imaging",
        "mri_scan",
        "fmri_scan",
        "ultrasound",
        "optical_satellite",
        "radar",
        "lidar",
        "telescope_imaging",
    ),
    "sequencing_and_omics": (
        "dna_sequencing",
        "rna_seq",
        "single_cell_profiling",
        "mass_spectrometry",
        "metabolomics_assay",
        "microbiome_profiling",
    ),
    "sensor_and_iot": (
        "accelerometer",
        "gyroscope",
        "gps_trace",
        "weather_station",
        "ocean_buoy",
        "particle_detector",
        "industrial_sensor",
        "energy_meter",
    ),
    "archival_and_administrative": (
        "census",
        "registry_extract",
        "transaction_log",
        "manuscript_cataloging",
        "oral_history",
        "museum_cataloging",
    ),
    "experimental_and_behavioral": (
        "randomized_trial",
        "lab_task",
        "field_experiment",
        "psychophysics",
        "longitudinal_cohort",
        "behavioral_tracking",
    ),
    "computational_and_simulation": (
        "simulation_run",
        "model_output",
        "synthetic_benchmark",
        "digital_trace",
        "log_instrumentation",
    ),
}
UOI_ANALYSIS_METHOD_FAMILIES = {
    "descriptive_statistics": (
        "summary_statistics",
        "distribution_profile",
        "stratified_table",
        "visualization_digest",
    ),
    "signal_processing": (
        "filtering",
        "spectral_analysis",
        "time_frequency_analysis",
        "artifact_detection",
        "event_related_average",
    ),
    "spatial_temporal_analysis": (
        "geospatial_overlay",
        "interpolation",
        "time_series_decomposition",
        "spatiotemporal_model",
        "data_assimilation",
    ),
    "statistical_inference": (
        "regression",
        "anova",
        "mixed_effects_model",
        "survival_analysis",
        "causal_sensitivity",
    ),
    "machine_learning": (
        "supervised_model",
        "unsupervised_clustering",
        "representation_learning",
        "anomaly_detection",
        "cross_validation",
    ),
    "network_and_graph": (
        "graph_alignment",
        "community_detection",
        "centrality_analysis",
        "knowledge_graph_linking",
    ),
    "omics_bioinformatics": (
        "sequence_alignment",
        "variant_calling",
        "differential_expression",
        "pathway_enrichment",
        "multi_omics_integration",
    ),
    "image_media_analysis": (
        "segmentation",
        "object_detection",
        "image_registration",
        "feature_extraction",
        "multimodal_annotation",
    ),
    "simulation_and_model_checking": (
        "mechanistic_model",
        "monte_carlo",
        "uncertainty_quantification",
        "sensitivity_analysis",
    ),
    "qualitative_text_analysis": (
        "coding",
        "thematic_analysis",
        "topic_modeling",
        "provenance_annotation",
    ),
    "privacy_rights_audit": (
        "consent_check",
        "license_audit",
        "disclosure_risk_review",
        "deidentification_review",
        "guardian_conflict_review",
    ),
}
UOI_SOURCE_TYPE_ALIASES = {
    "fmri": "fmri_bold",
    "functional_mri": "fmri_bold",
    "ehr_record": "ehr",
    "electronic_health_record": "ehr",
    "remote_sensing": "satellite_imagery",
    "satellite": "satellite_imagery",
    "weather": "weather_station",
    "particle": "particle_detector",
    "iot": "machine_sensor",
    "economic_series": "market_series",
    "text": "text_archive",
    "software_log": "log_event",
}


class ObservationIntegrationWorkbench:
    """Digest-only integrator for human-acquired observations and measurements."""

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": UOI_SCHEMA_VERSION,
            "taxonomy_profile_id": UOI_TAXONOMY_PROFILE_ID,
            "method_catalog_profile_id": UOI_METHOD_CATALOG_PROFILE_ID,
            "source_bundle_profile_id": UOI_BUNDLE_PROFILE_ID,
            "integration_graph_profile_id": UOI_GRAPH_PROFILE_ID,
            "analysis_plan_profile_id": UOI_PLAN_PROFILE_ID,
            "analysis_run_profile_id": UOI_ANALYSIS_RUN_PROFILE_ID,
            "operator_guide_profile_id": UOI_OPERATOR_GUIDE_PROFILE_ID,
            "measurement_families": {
                family: list(source_types)
                for family, source_types in UOI_MEASUREMENT_FAMILIES.items()
            },
            "measurement_method_families": {
                family: list(method_ids)
                for family, method_ids in UOI_MEASUREMENT_METHOD_FAMILIES.items()
            },
            "analysis_method_families": {
                family: list(method_ids)
                for family, method_ids in UOI_ANALYSIS_METHOD_FAMILIES.items()
            },
            "required_alignment_axes": list(UOI_REQUIRED_ALIGNMENT_AXES),
            "required_analysis_lanes": list(UOI_REQUIRED_ANALYSIS_LANES),
            "claim_ceiling": UOI_CLAIM_CEILING,
            "storage_policy": UOI_STORAGE_POLICY,
            "analysis_run_policy": UOI_ANALYSIS_RUN_POLICY,
            "conflict_sink_url": UOI_CONFLICT_SINK_URL,
            "raw_observation_payload_stored": False,
            "raw_personal_payload_stored": False,
            "raw_external_dataset_payload_stored": False,
            "complete_human_knowledge_claimed": False,
            "truth_unification_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }

    def taxonomy(self) -> Dict[str, Any]:
        families = [
            {
                "family_id": family_id,
                "source_types": list(source_types),
                "source_type_count": len(source_types),
            }
            for family_id, source_types in UOI_MEASUREMENT_FAMILIES.items()
        ]
        taxonomy = {
            "schema_version": UOI_SCHEMA_VERSION,
            "taxonomy_ref": f"taxonomy://universal-observation/{new_id('uoi-taxonomy')}",
            "created_at": utc_now_iso(),
            "profile_id": UOI_TAXONOMY_PROFILE_ID,
            "measurement_families": families,
            "family_count": len(families),
            "source_type_count": sum(item["source_type_count"] for item in families),
            "alignment_axes": list(UOI_REQUIRED_ALIGNMENT_AXES),
            "analysis_lanes": list(UOI_REQUIRED_ANALYSIS_LANES),
            "open_world_taxonomy": True,
            "claim_ceiling": UOI_CLAIM_CEILING,
            "storage_policy": UOI_STORAGE_POLICY,
            "raw_taxonomy_payload_stored": False,
            "complete_human_knowledge_claimed": False,
        }
        taxonomy["taxonomy_digest"] = sha256_text(
            canonical_json(self._taxonomy_digest_payload(taxonomy))
        )
        return deepcopy(taxonomy)

    def method_catalog(self) -> Dict[str, Any]:
        measurement_method_families = self._method_family_items(
            UOI_MEASUREMENT_METHOD_FAMILIES
        )
        analysis_method_families = self._method_family_items(
            UOI_ANALYSIS_METHOD_FAMILIES
        )
        catalog = {
            "schema_version": UOI_SCHEMA_VERSION,
            "method_catalog_ref": (
                f"method-catalog://universal-observation/"
                f"{new_id('uoi-method-catalog')}"
            ),
            "created_at": utc_now_iso(),
            "profile_id": UOI_METHOD_CATALOG_PROFILE_ID,
            "measurement_method_families": measurement_method_families,
            "measurement_method_family_count": len(measurement_method_families),
            "measurement_method_count": sum(
                item["method_count"] for item in measurement_method_families
            ),
            "analysis_method_families": analysis_method_families,
            "analysis_method_family_count": len(analysis_method_families),
            "analysis_method_count": sum(
                item["method_count"] for item in analysis_method_families
            ),
            "required_alignment_axes": list(UOI_REQUIRED_ALIGNMENT_AXES),
            "required_analysis_lanes": list(UOI_REQUIRED_ANALYSIS_LANES),
            "open_world_method_taxonomy": True,
            "method_gap_policy": "accept-declared-method-with-frontier-flag",
            "claim_ceiling": UOI_CLAIM_CEILING,
            "storage_policy": UOI_STORAGE_POLICY,
            "raw_method_payload_stored": False,
            "raw_algorithm_payload_stored": False,
            "complete_human_method_coverage_claimed": False,
            "complete_human_knowledge_claimed": False,
            "truth_unification_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        catalog["method_catalog_digest"] = sha256_text(
            canonical_json(self._method_catalog_digest_payload(catalog))
        )
        return deepcopy(catalog)

    def bind_source_bundle(
        self,
        bundle_label: str,
        source_manifests: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self._require_non_empty_string(bundle_label, "bundle_label")
        if len(source_manifests) < 4:
            raise ValueError("source_manifests must contain at least four domains")
        sources = [
            self._normalize_source_manifest(source_manifest)
            for source_manifest in source_manifests
        ]
        family_coverage = sorted({source["measurement_family"] for source in sources})
        source_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": UOI_BUNDLE_PROFILE_ID,
                    "source_digests": [source["feature_digest"] for source in sources],
                    "source_types": [source["source_type"] for source in sources],
                    "families": family_coverage,
                }
            )
        )
        bundle = {
            "schema_version": UOI_SCHEMA_VERSION,
            "source_bundle_ref": f"source-bundle://universal-observation/{new_id('uoi-bundle')}",
            "created_at": utc_now_iso(),
            "profile_id": UOI_BUNDLE_PROFILE_ID,
            "bundle_label": bundle_label,
            "source_count": len(sources),
            "source_types": [source["source_type"] for source in sources],
            "measurement_families": family_coverage,
            "family_coverage_count": len(family_coverage),
            "sources": sources,
            "source_digest_set": source_digest_set,
            "alignment_axes_required": list(UOI_REQUIRED_ALIGNMENT_AXES),
            "alignment_axes_bound": all(
                all(axis in source["axis_refs"] for axis in UOI_REQUIRED_ALIGNMENT_AXES)
                for source in sources
            ),
            "rights_and_consent_bound": all(
                source["rights_ref"] and source["consent_or_public_basis_ref"]
                for source in sources
            ),
            "open_world_taxonomy": True,
            "taxonomy_gap_policy": "accept-declared-family-with-frontier-flag",
            "storage_policy": UOI_STORAGE_POLICY,
            "claim_ceiling": UOI_CLAIM_CEILING,
            "conflict_refs": self._conflict_refs(),
            "mind_upload_conflict_sink_url": UOI_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_feature_payload_stored": False,
            "raw_personal_payload_stored": False,
            "raw_external_dataset_payload_stored": False,
            "complete_human_knowledge_claimed": False,
            "truth_unification_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        bundle["source_bundle_digest"] = sha256_text(
            canonical_json(self._bundle_digest_payload(bundle))
        )
        return deepcopy(bundle)

    def build_integration_graph(self, source_bundle: Dict[str, Any]) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        sources = source_bundle["sources"]
        nodes = [
            {
                "node_ref": f"node://universal-observation/{source['source_type']}",
                "source_ref": source["source_ref"],
                "source_type": source["source_type"],
                "measurement_family": source["measurement_family"],
                "feature_digest": source["feature_digest"],
                "axis_digest": source["axis_digest"],
            }
            for source in sources
        ]
        edges: List[Dict[str, Any]] = []
        for index, source in enumerate(sources):
            other = sources[(index + 1) % len(sources)]
            shared_axes = [
                axis
                for axis in UOI_REQUIRED_ALIGNMENT_AXES
                if axis in source["axis_refs"] and axis in other["axis_refs"]
            ]
            edge = {
                "edge_ref": (
                    f"edge://universal-observation/{source['source_type']}"
                    f"-to-{other['source_type']}"
                ),
                "from_source_type": source["source_type"],
                "to_source_type": other["source_type"],
                "shared_axes": shared_axes,
                "edge_role": self._edge_role(source, other),
                "confidence_proxy": self._round_score(
                    (
                        source["quality_summary"]["integration_readiness"]
                        + other["quality_summary"]["integration_readiness"]
                    )
                    / 2.0
                ),
                "raw_edge_payload_stored": False,
            }
            edge["edge_digest"] = sha256_text(canonical_json(edge))
            edges.append(edge)
        graph = {
            "schema_version": UOI_SCHEMA_VERSION,
            "integration_graph_ref": f"graph://universal-observation/{new_id('uoi-graph')}",
            "created_at": utc_now_iso(),
            "profile_id": UOI_GRAPH_PROFILE_ID,
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "alignment_axes": list(UOI_REQUIRED_ALIGNMENT_AXES),
            "cross_domain_edge_bound": any(
                edge["from_source_type"] != edge["to_source_type"] for edge in edges
            ),
            "uncertainty_propagation_bound": True,
            "rights_boundary_bound": source_bundle["rights_and_consent_bound"],
            "claim_ceiling": UOI_CLAIM_CEILING,
            "storage_policy": UOI_STORAGE_POLICY,
            "raw_graph_payload_stored": False,
            "truth_unification_claimed": False,
            "complete_human_knowledge_claimed": False,
        }
        graph["integration_graph_digest"] = sha256_text(
            canonical_json(self._graph_digest_payload(graph))
        )
        return deepcopy(graph)

    def build_analysis_plan(
        self,
        source_bundle: Dict[str, Any],
        integration_graph: Dict[str, Any],
        analysis_question: str,
        method_catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_integration_graph(integration_graph)
        self._require_non_empty_string(analysis_question, "analysis_question")
        if method_catalog is None:
            method_catalog = self.method_catalog()
        self._check_method_catalog(method_catalog)
        if integration_graph["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("integration_graph.source_bundle_digest must match source bundle")
        lanes = [
            {
                "lane_id": lane,
                "status": "bound",
                "source_bundle_digest": source_bundle["source_bundle_digest"],
                "integration_graph_digest": integration_graph[
                    "integration_graph_digest"
                ],
                "output_policy": "digest-only-receipt",
                "raw_lane_payload_stored": False,
            }
            for lane in UOI_REQUIRED_ANALYSIS_LANES
        ]
        readiness_values = [
            source["quality_summary"]["integration_readiness"]
            for source in source_bundle["sources"]
        ]
        uncertainty_values = [
            source["quality_summary"]["uncertainty_proxy"]
            for source in source_bundle["sources"]
        ]
        planned_analyses = [
            {
                "analysis_id": "provenance-rights-preflight",
                "goal": "Confirm source, consent or public-basis, license, and retention boundaries before analysis.",
                "lane_id": "ingest",
                "measurement_method_ref": "measurement-method://universal-observation/archival_and_administrative/registry_extract",
                "analysis_method_ref": "analysis-method://universal-observation/privacy_rights_audit/consent_check",
            },
            {
                "analysis_id": "unit-coordinate-normalization",
                "goal": "Normalize units, time windows, spatial frames, and entity identifiers without retaining raw records.",
                "lane_id": "normalize",
                "measurement_method_ref": "measurement-method://universal-observation/sensor_and_iot/weather_station",
                "analysis_method_ref": "analysis-method://universal-observation/spatial_temporal_analysis/interpolation",
            },
            {
                "analysis_id": "cross-domain-alignment-graph",
                "goal": "Use shared axis digests to align heterogeneous measurement families.",
                "lane_id": "align",
                "measurement_method_ref": "measurement-method://universal-observation/imaging_and_remote_sensing/optical_satellite",
                "analysis_method_ref": "analysis-method://universal-observation/network_and_graph/graph_alignment",
            },
            {
                "analysis_id": "uncertainty-aware-model-plan",
                "goal": "Propagate uncertainty and evidence ceilings before any modeling claim.",
                "lane_id": "model",
                "measurement_method_ref": "measurement-method://universal-observation/computational_and_simulation/model_output",
                "analysis_method_ref": "analysis-method://universal-observation/simulation_and_model_checking/uncertainty_quantification",
            },
            {
                "analysis_id": "guardian-review-and-conflict-sink",
                "goal": "Route unresolved equivalence, causality, privacy, or identity claims to explicit conflict refs.",
                "lane_id": "audit",
                "measurement_method_ref": "measurement-method://universal-observation/experimental_and_behavioral/longitudinal_cohort",
                "analysis_method_ref": "analysis-method://universal-observation/privacy_rights_audit/guardian_conflict_review",
            },
            {
                "analysis_id": "digest-only-publication",
                "goal": "Publish only receipt digests, coverage summaries, and claim ceilings.",
                "lane_id": "publish-digest",
                "measurement_method_ref": "measurement-method://universal-observation/archival_and_administrative/manuscript_cataloging",
                "analysis_method_ref": "analysis-method://universal-observation/descriptive_statistics/visualization_digest",
            },
        ]
        plan = {
            "schema_version": UOI_SCHEMA_VERSION,
            "analysis_plan_ref": f"analysis-plan://universal-observation/{new_id('uoi-plan')}",
            "created_at": utc_now_iso(),
            "profile_id": UOI_PLAN_PROFILE_ID,
            "analysis_question": analysis_question,
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "integration_graph_ref": integration_graph["integration_graph_ref"],
            "integration_graph_digest": integration_graph["integration_graph_digest"],
            "method_catalog_ref": method_catalog["method_catalog_ref"],
            "method_catalog_digest": method_catalog["method_catalog_digest"],
            "method_catalog_profile_id": method_catalog["profile_id"],
            "measurement_method_family_count": method_catalog[
                "measurement_method_family_count"
            ],
            "measurement_method_count": method_catalog["measurement_method_count"],
            "analysis_method_family_count": method_catalog[
                "analysis_method_family_count"
            ],
            "analysis_method_count": method_catalog["analysis_method_count"],
            "required_analysis_lanes": list(UOI_REQUIRED_ANALYSIS_LANES),
            "analysis_lanes": lanes,
            "all_analysis_lanes_bound": all(lane["status"] == "bound" for lane in lanes),
            "coverage_summary": {
                "source_count": source_bundle["source_count"],
                "family_coverage_count": source_bundle["family_coverage_count"],
                "edge_count": integration_graph["edge_count"],
                "alignment_axis_count": len(UOI_REQUIRED_ALIGNMENT_AXES),
                "average_integration_readiness": self._round_score(
                    sum(readiness_values) / len(readiness_values)
                ),
                "maximum_uncertainty_proxy": self._round_score(max(uncertainty_values)),
            },
            "planned_analyses": planned_analyses,
            "planned_methods_bound": all(
                item["measurement_method_ref"] and item["analysis_method_ref"]
                for item in planned_analyses
            ),
            "claim_ceiling": UOI_CLAIM_CEILING,
            "storage_policy": UOI_STORAGE_POLICY,
            "conflict_refs": self._conflict_refs(),
            "mind_upload_conflict_sink_url": UOI_CONFLICT_SINK_URL,
            "raw_analysis_payload_stored": False,
            "raw_model_payload_stored": False,
            "raw_source_payload_stored": False,
            "raw_method_payload_stored": False,
            "raw_algorithm_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "causal_truth_claimed": False,
            "truth_unification_claimed": False,
            "complete_human_knowledge_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        plan["analysis_plan_digest"] = sha256_text(
            canonical_json(self._plan_digest_payload(plan))
        )
        return deepcopy(plan)

    def build_operator_guide(
        self,
        source_bundle: Dict[str, Any],
        analysis_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_analysis_plan(analysis_plan)
        if analysis_plan["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("analysis_plan.source_bundle_digest must match source bundle")
        guide = {
            "schema_version": UOI_SCHEMA_VERSION,
            "operator_guide_ref": f"operator-guide://universal-observation/{new_id('uoi-guide')}",
            "created_at": utc_now_iso(),
            "profile_id": UOI_OPERATOR_GUIDE_PROFILE_ID,
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "analysis_plan_ref": analysis_plan["analysis_plan_ref"],
            "analysis_plan_digest": analysis_plan["analysis_plan_digest"],
            "operator_cards": [
                {
                    "card_id": "add-source-summary",
                    "plain_language_prompt": "Add only an approved feature summary with source, rights, time, space, unit, uncertainty, and entity refs.",
                    "agent_action": "normalize_source_manifest",
                    "safety_gate": "no-raw-payload",
                },
                {
                    "card_id": "check-cross-domain-coverage",
                    "plain_language_prompt": "Check which measurement families and alignment axes are covered before modeling.",
                    "agent_action": "validate_observation_bundle",
                    "safety_gate": "claim-ceiling-visible",
                },
                {
                    "card_id": "run-integration-plan",
                    "plain_language_prompt": "Run the analysis lanes as receipt-producing steps, not as a truth-unification claim.",
                    "agent_action": "build_analysis_plan",
                    "safety_gate": "guardian-conflict-sink",
                },
            ],
            "coding_agent_task_templates": [
                {
                    "template_id": "schema-bound-ingest",
                    "target_actor": "coding-agent",
                    "prompt_contract": "load manifests, validate public schemas, emit only digest-bound receipts",
                    "output_ref": "analysis-plan://universal-observation/result-receipt",
                },
                {
                    "template_id": "coverage-gap-review",
                    "target_actor": "researcher",
                    "prompt_contract": "identify missing source families or rights evidence without inventing data",
                    "output_ref": "frontier://universal-observation/coverage-gap",
                },
            ],
            "beginner_operator_supported": True,
            "coding_agent_ready": True,
            "claim_ceiling": UOI_CLAIM_CEILING,
            "storage_policy": UOI_STORAGE_POLICY,
            "raw_instruction_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "raw_source_payload_stored": False,
            "truth_unification_claimed": False,
            "complete_human_knowledge_claimed": False,
        }
        guide["operator_guide_digest"] = sha256_text(
            canonical_json(self._guide_digest_payload(guide))
        )
        return deepcopy(guide)

    def execute_analysis_plan(
        self,
        source_bundle: Dict[str, Any],
        integration_graph: Dict[str, Any],
        analysis_plan: Dict[str, Any],
        operator_guide: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._check_source_bundle(source_bundle)
        self._check_integration_graph(integration_graph)
        self._check_analysis_plan(analysis_plan)
        self._check_operator_guide(operator_guide)
        if integration_graph["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("integration_graph.source_bundle_digest must match source bundle")
        if analysis_plan["source_bundle_digest"] != source_bundle["source_bundle_digest"]:
            raise ValueError("analysis_plan.source_bundle_digest must match source bundle")
        if analysis_plan["integration_graph_digest"] != integration_graph["integration_graph_digest"]:
            raise ValueError("analysis_plan.integration_graph_digest must match graph")
        if operator_guide["analysis_plan_digest"] != analysis_plan["analysis_plan_digest"]:
            raise ValueError("operator_guide.analysis_plan_digest must match analysis plan")
        planned_by_lane = {
            item["lane_id"]: item
            for item in analysis_plan.get("planned_analyses", [])
            if isinstance(item, dict)
        }
        lane_results = [
            self._build_lane_result(
                lane,
                planned_by_lane.get(lane["lane_id"], {}),
                source_bundle,
                integration_graph,
                analysis_plan,
                operator_guide,
            )
            for lane in analysis_plan["analysis_lanes"]
        ]
        result_digests = [result["result_digest"] for result in lane_results]
        result_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": UOI_ANALYSIS_RUN_PROFILE_ID,
                    "analysis_plan_digest": analysis_plan["analysis_plan_digest"],
                    "result_digests": result_digests,
                }
            )
        )
        readiness_values = [
            source["quality_summary"]["integration_readiness"]
            for source in source_bundle["sources"]
        ]
        uncertainty_values = [
            source["quality_summary"]["uncertainty_proxy"]
            for source in source_bundle["sources"]
        ]
        all_lane_results_bound = (
            len(lane_results) == len(analysis_plan["analysis_lanes"])
            and all(result["result_bound"] for result in lane_results)
        )
        run = {
            "schema_version": UOI_SCHEMA_VERSION,
            "analysis_run_ref": f"analysis-run://universal-observation/{new_id('uoi-run')}",
            "created_at": utc_now_iso(),
            "profile_id": UOI_ANALYSIS_RUN_PROFILE_ID,
            "source_bundle_ref": source_bundle["source_bundle_ref"],
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "integration_graph_ref": integration_graph["integration_graph_ref"],
            "integration_graph_digest": integration_graph["integration_graph_digest"],
            "analysis_plan_ref": analysis_plan["analysis_plan_ref"],
            "analysis_plan_digest": analysis_plan["analysis_plan_digest"],
            "operator_guide_ref": operator_guide["operator_guide_ref"],
            "operator_guide_digest": operator_guide["operator_guide_digest"],
            "required_analysis_lanes": list(UOI_REQUIRED_ANALYSIS_LANES),
            "analysis_lane_count": len(analysis_plan["analysis_lanes"]),
            "result_count": len(lane_results),
            "lane_results": lane_results,
            "result_digests": result_digests,
            "result_digest_set": result_digest_set,
            "all_lane_results_bound": all_lane_results_bound,
            "operator_review_ready": (
                operator_guide["beginner_operator_supported"] and all_lane_results_bound
            ),
            "coding_agent_review_ready": (
                operator_guide["coding_agent_ready"] and all_lane_results_bound
            ),
            "analysis_run_summary": {
                "result_count": len(lane_results),
                "bounded_result_count": sum(
                    1 for result in lane_results if result["result_bound"]
                ),
                "source_count": source_bundle["source_count"],
                "family_coverage_count": source_bundle["family_coverage_count"],
                "average_integration_readiness": self._round_score(
                    sum(readiness_values) / len(readiness_values)
                ),
                "maximum_uncertainty_proxy": self._round_score(max(uncertainty_values)),
            },
            "observation_analysis_run_bound": (
                analysis_plan["all_analysis_lanes_bound"]
                and integration_graph["cross_domain_edge_bound"]
                and operator_guide["coding_agent_ready"]
                and operator_guide["beginner_operator_supported"]
                and all_lane_results_bound
            ),
            "storage_policy": UOI_ANALYSIS_RUN_POLICY,
            "claim_ceiling": UOI_CLAIM_CEILING,
            "conflict_refs": self._conflict_refs(),
            "mind_upload_conflict_sink_url": UOI_CONFLICT_SINK_URL,
            "raw_source_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "raw_model_payload_stored": False,
            "raw_instruction_payload_stored": False,
            "raw_result_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "causal_truth_claimed": False,
            "truth_unification_claimed": False,
            "complete_human_knowledge_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        run["analysis_run_digest"] = sha256_text(
            canonical_json(self._analysis_run_digest_payload(run))
        )
        return deepcopy(run)

    def validate_observation_package(
        self,
        taxonomy: Dict[str, Any],
        source_bundle: Dict[str, Any],
        integration_graph: Dict[str, Any],
        analysis_plan: Dict[str, Any],
        operator_guide: Dict[str, Any],
        method_catalog: Optional[Dict[str, Any]] = None,
        analysis_run: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if analysis_run is not None:
            try:
                self._check_analysis_run(analysis_run)
            except ValueError as exc:
                errors.append(str(exc))
        analysis_run_checks: Dict[str, bool] = {}
        if analysis_run is not None:
            analysis_run_checks = {
                "analysis_run_digest_bound": analysis_run.get("analysis_run_digest")
                == sha256_text(
                    canonical_json(self._analysis_run_digest_payload(analysis_run))
                ),
                "observation_analysis_run_bound": (
                    analysis_run.get("observation_analysis_run_bound") is True
                    and analysis_run.get("source_bundle_digest")
                    == source_bundle.get("source_bundle_digest")
                    and analysis_run.get("integration_graph_digest")
                    == integration_graph.get("integration_graph_digest")
                    and analysis_run.get("analysis_plan_digest")
                    == analysis_plan.get("analysis_plan_digest")
                    and analysis_run.get("operator_guide_digest")
                    == operator_guide.get("operator_guide_digest")
                ),
                "all_lane_results_bound": (
                    analysis_run.get("all_lane_results_bound") is True
                ),
                "analysis_result_payload_redacted": (
                    self._analysis_run_payload_redacted(analysis_run)
                ),
            }
        artifacts = [
            taxonomy,
            source_bundle,
            integration_graph,
            analysis_plan,
            operator_guide,
        ]
        if method_catalog is not None:
            artifacts.append(method_catalog)
        if analysis_run is not None:
            artifacts.append(analysis_run)
        method_catalog_digest_bound = bool(
            analysis_plan.get("method_catalog_digest")
            and analysis_plan.get("method_catalog_profile_id")
            == UOI_METHOD_CATALOG_PROFILE_ID
        )
        if method_catalog is not None:
            method_catalog_digest_bound = method_catalog.get("method_catalog_digest") == (
                sha256_text(
                    canonical_json(self._method_catalog_digest_payload(method_catalog))
                )
            ) and analysis_plan.get("method_catalog_digest") == method_catalog.get(
                "method_catalog_digest"
            )
        checks = {
            "taxonomy_digest_bound": taxonomy.get("taxonomy_digest")
            == sha256_text(canonical_json(self._taxonomy_digest_payload(taxonomy))),
            "method_catalog_digest_bound": method_catalog_digest_bound,
            "source_bundle_digest_bound": source_bundle.get("source_bundle_digest")
            == sha256_text(canonical_json(self._bundle_digest_payload(source_bundle))),
            "integration_graph_digest_bound": integration_graph.get(
                "integration_graph_digest"
            )
            == sha256_text(canonical_json(self._graph_digest_payload(integration_graph))),
            "analysis_plan_digest_bound": analysis_plan.get("analysis_plan_digest")
            == sha256_text(canonical_json(self._plan_digest_payload(analysis_plan))),
            "operator_guide_digest_bound": operator_guide.get("operator_guide_digest")
            == sha256_text(canonical_json(self._guide_digest_payload(operator_guide))),
            "alignment_axes_bound": source_bundle.get("alignment_axes_bound") is True,
            "rights_and_consent_bound": source_bundle.get("rights_and_consent_bound")
            is True,
            "cross_domain_graph_bound": integration_graph.get("cross_domain_edge_bound")
            is True,
            "all_analysis_lanes_bound": analysis_plan.get("all_analysis_lanes_bound")
            is True,
            "measurement_method_catalog_bound": analysis_plan.get(
                "measurement_method_family_count", 0
            )
            >= len(UOI_MEASUREMENT_METHOD_FAMILIES)
            and analysis_plan.get("measurement_method_count", 0)
            >= sum(len(methods) for methods in UOI_MEASUREMENT_METHOD_FAMILIES.values()),
            "analysis_method_catalog_bound": analysis_plan.get(
                "analysis_method_family_count", 0
            )
            >= len(UOI_ANALYSIS_METHOD_FAMILIES)
            and analysis_plan.get("analysis_method_count", 0)
            >= sum(len(methods) for methods in UOI_ANALYSIS_METHOD_FAMILIES.values()),
            "planned_methods_bound": analysis_plan.get("planned_methods_bound") is True,
            "operator_handoff_bound": operator_guide.get("coding_agent_ready") is True
            and operator_guide.get("beginner_operator_supported") is True,
            "claim_ceiling_bound": all(
                artifact.get("claim_ceiling") == UOI_CLAIM_CEILING
                for artifact in artifacts
            ),
            "raw_payload_redacted": all(
                artifact.get(field_name) is False
                for artifact in artifacts
                for field_name in artifact
                if field_name.startswith("raw_")
            ),
            "no_totality_or_truth_claim": all(
                artifact.get("complete_human_knowledge_claimed", False) is False
                and artifact.get("truth_unification_claimed", False) is False
                for artifact in artifacts
            ),
            "no_identity_or_consciousness_claim": all(
                artifact.get("consciousness_reproduction_claimed", False) is False
                and artifact.get("identity_replacement_claimed", False) is False
                for artifact in artifacts
            ),
            **analysis_run_checks,
        }
        for name, ok in checks.items():
            if not ok:
                errors.append(f"{name} failed")
        return {
            "ok": not errors,
            "errors": errors,
            **checks,
            "source_count": source_bundle.get("source_count", 0),
            "family_coverage_count": source_bundle.get("family_coverage_count", 0),
            "analysis_lane_count": len(analysis_plan.get("analysis_lanes", [])),
            "measurement_method_family_count": analysis_plan.get(
                "measurement_method_family_count", 0
            ),
            "measurement_method_count": analysis_plan.get("measurement_method_count", 0),
            "analysis_method_family_count": analysis_plan.get(
                "analysis_method_family_count", 0
            ),
            "analysis_method_count": analysis_plan.get("analysis_method_count", 0),
            "claim_ceiling": UOI_CLAIM_CEILING,
            "raw_source_payload_stored": False,
            "raw_analysis_payload_stored": False,
            "raw_method_payload_stored": False,
            "analysis_result_count": (
                analysis_run.get("result_count", 0) if analysis_run is not None else 0
            ),
            "raw_result_payload_stored": False,
            "complete_human_knowledge_claimed": False,
            "truth_unification_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }

    def _method_family_items(
        self,
        method_families: Dict[str, Sequence[str]],
    ) -> List[Dict[str, Any]]:
        return [
            {
                "family_id": family_id,
                "method_ids": list(method_ids),
                "method_count": len(method_ids),
            }
            for family_id, method_ids in method_families.items()
        ]

    def _build_lane_result(
        self,
        lane: Dict[str, Any],
        planned_analysis: Dict[str, Any],
        source_bundle: Dict[str, Any],
        integration_graph: Dict[str, Any],
        analysis_plan: Dict[str, Any],
        operator_guide: Dict[str, Any],
    ) -> Dict[str, Any]:
        lane_id = lane["lane_id"]
        readiness_values = [
            source["quality_summary"]["integration_readiness"]
            for source in source_bundle["sources"]
        ]
        uncertainty_values = [
            source["quality_summary"]["uncertainty_proxy"]
            for source in source_bundle["sources"]
        ]
        edge_confidence_values = [
            edge["confidence_proxy"] for edge in integration_graph["edges"]
        ]
        result = {
            "result_ref": (
                f"analysis-result://universal-observation/{new_id('uoi-result')}"
            ),
            "lane_id": lane_id,
            "lane_digest": sha256_text(canonical_json(lane)),
            "planned_analysis_id": planned_analysis.get(
                "analysis_id",
                f"{lane_id}-bounded-result",
            ),
            "result_status": self._lane_result_status(lane_id),
            "source_bundle_digest": source_bundle["source_bundle_digest"],
            "integration_graph_digest": integration_graph["integration_graph_digest"],
            "analysis_plan_digest": analysis_plan["analysis_plan_digest"],
            "result_axis_summary": {
                "source_count": source_bundle["source_count"],
                "family_coverage_count": source_bundle["family_coverage_count"],
                "edge_count": integration_graph["edge_count"],
                "alignment_axis_count": len(UOI_REQUIRED_ALIGNMENT_AXES),
                "average_integration_readiness": self._round_score(
                    sum(readiness_values) / len(readiness_values)
                ),
                "maximum_uncertainty_proxy": self._round_score(max(uncertainty_values)),
                "average_edge_confidence_proxy": self._round_score(
                    sum(edge_confidence_values) / len(edge_confidence_values)
                ),
                "rights_boundary_bound": integration_graph["rights_boundary_bound"],
            },
            "operator_summary": self._operator_lane_summary(
                lane_id,
                planned_analysis.get("goal", ""),
            ),
            "agent_next_action": self._agent_lane_next_action(lane_id),
            "evidence_refs": [
                source_bundle["source_bundle_ref"],
                integration_graph["integration_graph_ref"],
                analysis_plan["analysis_plan_ref"],
                operator_guide["operator_guide_ref"],
            ],
            "requires_ml_expertise": False,
            "result_bound": lane["status"] == "bound",
            "claim_ceiling": UOI_CLAIM_CEILING,
            "raw_lane_payload_stored": False,
            "raw_result_payload_stored": False,
            "clinical_diagnosis_claimed": False,
            "causal_truth_claimed": False,
            "truth_unification_claimed": False,
            "complete_human_knowledge_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }
        result["result_digest"] = sha256_text(
            canonical_json(self._lane_result_digest_payload(result))
        )
        return result

    def _lane_result_status(self, lane_id: str) -> str:
        return f"{lane_id}-result-bound"

    def _operator_lane_summary(self, lane_id: str, goal: str) -> str:
        if lane_id == "model":
            return (
                "Model lane produced only uncertainty-aware feature integration context; "
                "it is not a causal truth, diagnosis, or identity claim."
            )
        if lane_id == "audit":
            return (
                "Audit lane preserved the claim ceiling and routes unresolved rights, "
                "causality, and identity questions to explicit conflict refs."
            )
        if lane_id == "publish-digest":
            return "Publish lane is limited to receipt digests, coverage summaries, and claim ceilings."
        if goal:
            return f"{lane_id} lane completed bounded review: {goal}"
        return f"{lane_id} lane completed bounded digest-only review."

    def _agent_lane_next_action(self, lane_id: str) -> str:
        return {
            "ingest": "verify_source_rights_and_feature_digest_refs",
            "normalize": "verify_units_time_space_and_entity_axis_refs",
            "align": "review_cross_domain_edge_axis_coverage",
            "model": "review_uncertainty_without_causal_or_diagnostic_claim",
            "audit": "route_unresolved_claims_to_guardian_conflict_refs",
            "publish-digest": "publish_receipt_digests_only",
        }.get(lane_id, "review_bounded_lane_summary")

    def _normalize_source_manifest(self, source_manifest: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(source_manifest, dict):
            raise ValueError("source_manifest must be a mapping")
        source_type = self._normalize_source_type(source_manifest.get("source_type"))
        for field_name in (
            "source_ref",
            "measurement_ref",
            "instrument_ref",
            "collector_ref",
            "rights_ref",
            "consent_or_public_basis_ref",
            "license_ref",
            "feature_summary_ref",
            "temporal_ref",
            "spatial_ref",
            "unit_system_ref",
            "entity_ref",
        ):
            self._require_non_empty_string(source_manifest.get(field_name), field_name)
        feature_summary = source_manifest.get("feature_summary")
        if not isinstance(feature_summary, dict) or not feature_summary:
            raise ValueError("feature_summary must be a non-empty mapping")
        uncertainty_summary = source_manifest.get("uncertainty_summary")
        if not isinstance(uncertainty_summary, dict) or not uncertainty_summary:
            raise ValueError("uncertainty_summary must be a non-empty mapping")
        axis_refs = {
            "provenance": str(source_manifest["measurement_ref"]),
            "rights": str(source_manifest["rights_ref"]),
            "time": str(source_manifest["temporal_ref"]),
            "space": str(source_manifest["spatial_ref"]),
            "unit": str(source_manifest["unit_system_ref"]),
            "uncertainty": str(source_manifest.get("uncertainty_ref", "uncertainty://declared")),
            "entity": str(source_manifest["entity_ref"]),
        }
        feature_digest = sha256_text(canonical_json(feature_summary))
        uncertainty_digest = sha256_text(canonical_json(uncertainty_summary))
        quality_summary = self._derive_quality_summary(feature_summary, uncertainty_summary)
        measurement_family = self._measurement_family(source_type)
        normalized = {
            "source_type": source_type,
            "measurement_family": measurement_family,
            "source_ref": str(source_manifest["source_ref"]),
            "measurement_ref": str(source_manifest["measurement_ref"]),
            "instrument_ref": str(source_manifest["instrument_ref"]),
            "collector_ref": str(source_manifest["collector_ref"]),
            "rights_ref": str(source_manifest["rights_ref"]),
            "consent_or_public_basis_ref": str(
                source_manifest["consent_or_public_basis_ref"]
            ),
            "license_ref": str(source_manifest["license_ref"]),
            "feature_summary_ref": str(source_manifest["feature_summary_ref"]),
            "feature_digest": feature_digest,
            "feature_name_digest": sha256_text(
                canonical_json({"feature_names": sorted(feature_summary)})
            ),
            "uncertainty_digest": uncertainty_digest,
            "axis_refs": axis_refs,
            "axis_digest": sha256_text(canonical_json(axis_refs)),
            "quality_summary": quality_summary,
            "numeric_feature_count": sum(
                1 for value in feature_summary.values() if isinstance(value, (int, float))
            ),
            "string_feature_count": sum(
                1 for value in feature_summary.values() if isinstance(value, str)
            ),
            "storage_policy": UOI_STORAGE_POLICY,
            "claim_ceiling": UOI_CLAIM_CEILING,
            "raw_payload_stored": False,
        }
        return normalized

    def _derive_quality_summary(
        self,
        feature_summary: Dict[str, Any],
        uncertainty_summary: Dict[str, Any],
    ) -> Dict[str, float]:
        numeric_values = [
            float(value) for value in feature_summary.values() if isinstance(value, (int, float))
        ]
        completeness = self._round_score(
            float(feature_summary.get("coverage_ratio", 0.75))
            if isinstance(feature_summary.get("coverage_ratio"), (int, float))
            else min(1.0, len(numeric_values) / 4.0)
        )
        uncertainty_values = [
            float(value)
            for value in uncertainty_summary.values()
            if isinstance(value, (int, float))
        ]
        uncertainty = self._round_score(
            sum(uncertainty_values) / len(uncertainty_values)
            if uncertainty_values
            else 0.25
        )
        rights_clarity = self._round_score(
            float(feature_summary.get("rights_clarity", 0.9))
            if isinstance(feature_summary.get("rights_clarity"), (int, float))
            else 0.9
        )
        integration_readiness = self._round_score(
            (completeness + rights_clarity + (1.0 - min(1.0, uncertainty))) / 3.0
        )
        return {
            "completeness_proxy": completeness,
            "uncertainty_proxy": uncertainty,
            "rights_clarity_proxy": rights_clarity,
            "integration_readiness": integration_readiness,
        }

    def _normalize_source_type(self, source_type: Any) -> str:
        self._require_non_empty_string(source_type, "source_type")
        normalized = str(source_type).strip().lower().replace("-", "_").replace(" ", "_")
        return UOI_SOURCE_TYPE_ALIASES.get(normalized, normalized)

    def _measurement_family(self, source_type: str) -> str:
        for family, source_types in UOI_MEASUREMENT_FAMILIES.items():
            if source_type in source_types:
                return family
        return "declared_frontier"

    def _edge_role(self, source: Dict[str, Any], other: Dict[str, Any]) -> str:
        if source["measurement_family"] == other["measurement_family"]:
            return "within-family-calibration"
        if "human" in source["measurement_family"] or "human" in other["measurement_family"]:
            return "human-context-alignment"
        if "environmental" in source["measurement_family"] or "geospatial" in other["measurement_family"]:
            return "planetary-context-alignment"
        return "cross-domain-evidence-context"

    def _check_source_bundle(self, source_bundle: Dict[str, Any]) -> None:
        if source_bundle.get("profile_id") != UOI_BUNDLE_PROFILE_ID:
            raise ValueError("source_bundle.profile_id mismatch")
        if source_bundle.get("source_bundle_digest") != sha256_text(
            canonical_json(self._bundle_digest_payload(source_bundle))
        ):
            raise ValueError("source_bundle_digest mismatch")

    def _check_integration_graph(self, integration_graph: Dict[str, Any]) -> None:
        if integration_graph.get("profile_id") != UOI_GRAPH_PROFILE_ID:
            raise ValueError("integration_graph.profile_id mismatch")
        if integration_graph.get("integration_graph_digest") != sha256_text(
            canonical_json(self._graph_digest_payload(integration_graph))
        ):
            raise ValueError("integration_graph_digest mismatch")

    def _check_analysis_plan(self, analysis_plan: Dict[str, Any]) -> None:
        if analysis_plan.get("profile_id") != UOI_PLAN_PROFILE_ID:
            raise ValueError("analysis_plan.profile_id mismatch")
        if analysis_plan.get("analysis_plan_digest") != sha256_text(
            canonical_json(self._plan_digest_payload(analysis_plan))
        ):
            raise ValueError("analysis_plan_digest mismatch")

    def _check_method_catalog(self, method_catalog: Dict[str, Any]) -> None:
        if method_catalog.get("profile_id") != UOI_METHOD_CATALOG_PROFILE_ID:
            raise ValueError("method_catalog.profile_id mismatch")
        if method_catalog.get("method_catalog_digest") != sha256_text(
            canonical_json(self._method_catalog_digest_payload(method_catalog))
        ):
            raise ValueError("method_catalog_digest mismatch")

    def _check_operator_guide(self, operator_guide: Dict[str, Any]) -> None:
        if operator_guide.get("profile_id") != UOI_OPERATOR_GUIDE_PROFILE_ID:
            raise ValueError("operator_guide.profile_id mismatch")
        if operator_guide.get("operator_guide_digest") != sha256_text(
            canonical_json(self._guide_digest_payload(operator_guide))
        ):
            raise ValueError("operator_guide_digest mismatch")

    def _check_analysis_run(self, analysis_run: Dict[str, Any]) -> None:
        if analysis_run.get("profile_id") != UOI_ANALYSIS_RUN_PROFILE_ID:
            raise ValueError("analysis_run.profile_id mismatch")
        if analysis_run.get("analysis_run_digest") != sha256_text(
            canonical_json(self._analysis_run_digest_payload(analysis_run))
        ):
            raise ValueError("analysis_run_digest mismatch")
        if analysis_run.get("claim_ceiling") != UOI_CLAIM_CEILING:
            raise ValueError("analysis_run.claim_ceiling mismatch")
        if analysis_run.get("storage_policy") != UOI_ANALYSIS_RUN_POLICY:
            raise ValueError("analysis_run.storage_policy mismatch")
        for field_name in (
            "clinical_diagnosis_claimed",
            "causal_truth_claimed",
            "truth_unification_claimed",
            "complete_human_knowledge_claimed",
            "consciousness_reproduction_claimed",
            "identity_replacement_claimed",
        ):
            if analysis_run.get(field_name) is not False:
                raise ValueError(f"analysis_run.{field_name} must be false")
        results = analysis_run.get("lane_results")
        if not isinstance(results, list) or not results:
            raise ValueError("analysis_run.lane_results must be a non-empty list")
        if analysis_run.get("result_count") != len(results):
            raise ValueError("analysis_run.result_count must match lane_results")
        result_digests = []
        for result in results:
            for field_name in (
                "clinical_diagnosis_claimed",
                "causal_truth_claimed",
                "truth_unification_claimed",
                "complete_human_knowledge_claimed",
                "consciousness_reproduction_claimed",
                "identity_replacement_claimed",
            ):
                if result.get(field_name) is not False:
                    raise ValueError(f"analysis_run_result.{field_name} must be false")
            expected_result_digest = sha256_text(
                canonical_json(self._lane_result_digest_payload(result))
            )
            if result.get("result_digest") != expected_result_digest:
                raise ValueError("analysis_run_result.result_digest mismatch")
            result_digests.append(expected_result_digest)
        if analysis_run.get("result_digests") != result_digests:
            raise ValueError("analysis_run.result_digests mismatch")
        expected_result_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": UOI_ANALYSIS_RUN_PROFILE_ID,
                    "analysis_plan_digest": analysis_run.get("analysis_plan_digest"),
                    "result_digests": result_digests,
                }
            )
        )
        if analysis_run.get("result_digest_set") != expected_result_digest_set:
            raise ValueError("analysis_run.result_digest_set mismatch")

    def _taxonomy_digest_payload(self, taxonomy: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: taxonomy[key]
            for key in (
                "schema_version",
                "profile_id",
                "measurement_families",
                "family_count",
                "source_type_count",
                "alignment_axes",
                "analysis_lanes",
                "open_world_taxonomy",
                "claim_ceiling",
                "storage_policy",
                "raw_taxonomy_payload_stored",
                "complete_human_knowledge_claimed",
            )
        }

    def _bundle_digest_payload(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: bundle[key]
            for key in (
                "schema_version",
                "profile_id",
                "bundle_label",
                "source_count",
                "source_types",
                "measurement_families",
                "family_coverage_count",
                "sources",
                "source_digest_set",
                "alignment_axes_required",
                "alignment_axes_bound",
                "rights_and_consent_bound",
                "open_world_taxonomy",
                "taxonomy_gap_policy",
                "storage_policy",
                "claim_ceiling",
                "raw_source_payload_stored",
                "raw_feature_payload_stored",
                "raw_personal_payload_stored",
                "raw_external_dataset_payload_stored",
                "complete_human_knowledge_claimed",
                "truth_unification_claimed",
            )
        }

    def _method_catalog_digest_payload(self, catalog: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: catalog[key]
            for key in (
                "schema_version",
                "profile_id",
                "measurement_method_families",
                "measurement_method_family_count",
                "measurement_method_count",
                "analysis_method_families",
                "analysis_method_family_count",
                "analysis_method_count",
                "required_alignment_axes",
                "required_analysis_lanes",
                "open_world_method_taxonomy",
                "method_gap_policy",
                "claim_ceiling",
                "storage_policy",
                "raw_method_payload_stored",
                "raw_algorithm_payload_stored",
                "complete_human_method_coverage_claimed",
                "complete_human_knowledge_claimed",
                "truth_unification_claimed",
            )
        }

    def _graph_digest_payload(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: graph[key]
            for key in (
                "schema_version",
                "profile_id",
                "source_bundle_digest",
                "node_count",
                "edge_count",
                "nodes",
                "edges",
                "alignment_axes",
                "cross_domain_edge_bound",
                "uncertainty_propagation_bound",
                "rights_boundary_bound",
                "claim_ceiling",
                "storage_policy",
                "raw_graph_payload_stored",
                "truth_unification_claimed",
                "complete_human_knowledge_claimed",
            )
        }

    def _plan_digest_payload(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: plan[key]
            for key in (
                "schema_version",
                "profile_id",
                "analysis_question",
                "source_bundle_digest",
                "integration_graph_digest",
                "method_catalog_digest",
                "method_catalog_profile_id",
                "measurement_method_family_count",
                "measurement_method_count",
                "analysis_method_family_count",
                "analysis_method_count",
                "required_analysis_lanes",
                "analysis_lanes",
                "all_analysis_lanes_bound",
                "coverage_summary",
                "planned_analyses",
                "planned_methods_bound",
                "claim_ceiling",
                "storage_policy",
                "raw_analysis_payload_stored",
                "raw_model_payload_stored",
                "raw_source_payload_stored",
                "raw_method_payload_stored",
                "raw_algorithm_payload_stored",
                "clinical_diagnosis_claimed",
                "causal_truth_claimed",
                "truth_unification_claimed",
                "complete_human_knowledge_claimed",
            )
        }

    def _guide_digest_payload(self, guide: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: guide[key]
            for key in (
                "schema_version",
                "profile_id",
                "source_bundle_digest",
                "analysis_plan_digest",
                "operator_cards",
                "coding_agent_task_templates",
                "beginner_operator_supported",
                "coding_agent_ready",
                "claim_ceiling",
                "storage_policy",
                "raw_instruction_payload_stored",
                "raw_analysis_payload_stored",
                "raw_source_payload_stored",
                "truth_unification_claimed",
                "complete_human_knowledge_claimed",
            )
        }

    def _analysis_run_payload_redacted(self, analysis_run: Dict[str, Any]) -> bool:
        run_raw_flags = all(
            analysis_run.get(field_name) is False
            for field_name in analysis_run
            if field_name.startswith("raw_")
        )
        result_raw_flags = all(
            result.get(field_name) is False
            for result in analysis_run.get("lane_results", [])
            if isinstance(result, dict)
            for field_name in result
            if field_name.startswith("raw_")
        )
        return run_raw_flags and result_raw_flags

    def _lane_result_digest_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "lane_id": result.get("lane_id"),
            "lane_digest": result.get("lane_digest"),
            "planned_analysis_id": result.get("planned_analysis_id"),
            "result_status": result.get("result_status"),
            "source_bundle_digest": result.get("source_bundle_digest"),
            "integration_graph_digest": result.get("integration_graph_digest"),
            "analysis_plan_digest": result.get("analysis_plan_digest"),
            "result_axis_summary": result.get("result_axis_summary"),
            "operator_summary": result.get("operator_summary"),
            "agent_next_action": result.get("agent_next_action"),
            "evidence_refs": result.get("evidence_refs"),
            "requires_ml_expertise": result.get("requires_ml_expertise"),
            "result_bound": result.get("result_bound"),
            "claim_ceiling": result.get("claim_ceiling"),
        }

    def _analysis_run_digest_payload(self, run: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "schema_version": run.get("schema_version"),
            "profile_id": run.get("profile_id"),
            "source_bundle_digest": run.get("source_bundle_digest"),
            "integration_graph_digest": run.get("integration_graph_digest"),
            "analysis_plan_digest": run.get("analysis_plan_digest"),
            "operator_guide_digest": run.get("operator_guide_digest"),
            "required_analysis_lanes": run.get("required_analysis_lanes"),
            "analysis_lane_count": run.get("analysis_lane_count"),
            "result_count": run.get("result_count"),
            "result_digest_set": run.get("result_digest_set"),
            "all_lane_results_bound": run.get("all_lane_results_bound"),
            "operator_review_ready": run.get("operator_review_ready"),
            "coding_agent_review_ready": run.get("coding_agent_review_ready"),
            "analysis_run_summary": run.get("analysis_run_summary"),
            "observation_analysis_run_bound": run.get(
                "observation_analysis_run_bound"
            ),
            "claim_ceiling": run.get("claim_ceiling"),
        }

    def _conflict_refs(self) -> List[Dict[str, str]]:
        return [
            {
                "topic": "complete-human-observation-coverage",
                "status": "open-world-frontier",
                "mind_upload_ref": f"{UOI_CONFLICT_SINK_URL}#coverage",
                "reason": "declared taxonomy can route any source family but does not prove that all data has been collected",
            },
            {
                "topic": "cross-domain-causal-truth",
                "status": "insufficient-evidence",
                "mind_upload_ref": f"{UOI_CONFLICT_SINK_URL}#causality",
                "reason": "integrating feature summaries does not prove causal truth across domains",
            },
            {
                "topic": "identity-or-consciousness-equivalence",
                "status": "forbidden-claim",
                "mind_upload_ref": f"{UOI_CONFLICT_SINK_URL}#identity",
                "reason": "observation integration is not a consciousness or identity replacement proof",
            },
        ]

    def _round_score(self, value: float) -> float:
        return round(max(0.0, min(1.0, value)), 3)

    def _require_non_empty_string(self, value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
