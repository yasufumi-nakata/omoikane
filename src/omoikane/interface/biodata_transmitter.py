"""BioData Transmitter reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

BDT_SCHEMA_VERSION = "1.0"
BDT_PROFILE_ID = "person-bound-biodata-transmitter-v0"
BDT_LATENT_PROFILE_ID = "physiology-latent-body-state-v0"
BDT_GENERATOR_PROFILE_ID = "bounded-cross-modal-biosignal-generator-v0"
BDT_CALIBRATION_PROFILE_ID = "multi-day-personal-biodata-calibration-v1"
BDT_CONFIDENCE_GATE_PROFILE_ID = "biodata-calibration-confidence-gate-v1"
BDT_DATASET_ADAPTER_PROFILE_ID = "biodata-dataset-feature-window-adapter-v1"
BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID = "biodata-circadian-phase-verifier-v1"
BDT_FEATURE_WINDOW_SERIES_PROFILE_ID = "biodata-feature-window-series-profile-v1"
BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID = "biodata-feature-window-series-drift-gate-v1"
BDT_CONFLICT_SINK_URL = "https://mind-upload.com/frontiers/biosignal-transmitter"
DEFAULT_SOURCE_MODALITIES = ("eeg", "ecg", "ppg", "eda", "respiration")
DEFAULT_TARGET_MODALITIES = ("ecg", "ppg", "respiration", "eeg", "affect", "thought")
SUPPORTED_MODALITIES = set(DEFAULT_SOURCE_MODALITIES + DEFAULT_TARGET_MODALITIES)
CONFIDENCE_GATE_TARGET_THRESHOLDS = {
    "identity-confirmation": 0.8,
    "sensory-loopback": 0.7,
}
FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS = {
    "heart_rate_bpm": 12.0,
    "autonomic_arousal": 0.18,
    "cortical_load_proxy": 0.18,
    "valence_proxy": 0.16,
    "thought_pressure_proxy": 0.18,
    "interoceptive_confidence": 0.05,
}
CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES = ("external-clock", "sleep-diary", "wearable")
REQUIRED_LITERATURE_REFS = (
    {
        "ref_id": "physionet-2000",
        "title": "PhysioBank, PhysioToolkit, and PhysioNet",
        "url": "https://doi.org/10.1161/01.CIR.101.23.e215",
        "claim": "open physiological signal corpora and tools are a baseline for cross-signal validation",
        "claim_status": "supports-signal-grounding",
    },
    {
        "ref_id": "neurokit2-2021",
        "title": "NeuroKit2: A Python toolbox for neurophysiological signal processing",
        "url": "https://doi.org/10.3758/s13428-020-01516-y",
        "claim": "ECG, PPG, EDA, respiration, and EEG features can share a reproducible processing vocabulary",
        "claim_status": "supports-feature-extraction",
    },
    {
        "ref_id": "deap-2012",
        "title": "DEAP: A Database for Emotion Analysis Using Physiological Signals",
        "url": "https://doi.org/10.1109/T-AFFC.2011.15",
        "claim": "EEG and peripheral physiology can be paired with bounded affect labels",
        "claim_status": "supports-affect-proxy",
    },
    {
        "ref_id": "barrett-simmons-2015",
        "title": "Interoceptive predictions in the brain",
        "url": "https://doi.org/10.1038/nrn3950",
        "claim": "body-state predictions constrain affective and embodied self representations",
        "claim_status": "supports-interoceptive-latent",
    },
    {
        "ref_id": "cebra-2023",
        "title": "Learnable latent embeddings for joint behavioural and neural analysis",
        "url": "https://doi.org/10.1038/s41586-023-06031-6",
        "claim": "joint neural and behavioural data can be embedded into hypothesis-guided latent spaces",
        "claim_status": "supports-latent-embedding",
    },
)
DEFAULT_CONFLICT_REFS = (
    {
        "topic": "biosignal-to-qualia-equivalence",
        "status": "unresolved",
        "mind_upload_ref": f"{BDT_CONFLICT_SINK_URL}#qualia-equivalence",
        "reason": "biosignal feature alignment does not prove subjective sameness",
    },
    {
        "topic": "thought-content-from-biosignals",
        "status": "insufficient-evidence",
        "mind_upload_ref": f"{BDT_CONFLICT_SINK_URL}#thought-content",
        "reason": "the reference runtime may emit thought-pressure proxies but not semantic thought content",
    },
)


class BioDataTransmitter:
    """Deterministic L6 transmitter for bounded biosignal-to-biosignal checks."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": BDT_SCHEMA_VERSION,
            "profile_id": BDT_PROFILE_ID,
            "latent_profile_id": BDT_LATENT_PROFILE_ID,
            "generator_profile_id": BDT_GENERATOR_PROFILE_ID,
            "calibration_profile_id": BDT_CALIBRATION_PROFILE_ID,
            "confidence_gate_profile_id": BDT_CONFIDENCE_GATE_PROFILE_ID,
            "dataset_adapter_profile_id": BDT_DATASET_ADAPTER_PROFILE_ID,
            "circadian_phase_verifier_profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
            "feature_window_series_profile_id": BDT_FEATURE_WINDOW_SERIES_PROFILE_ID,
            "feature_window_series_drift_gate_profile_id": (
                BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID
            ),
            "source_modalities": list(DEFAULT_SOURCE_MODALITIES),
            "target_modalities": list(DEFAULT_TARGET_MODALITIES),
            "confidence_gate_target_thresholds": dict(CONFIDENCE_GATE_TARGET_THRESHOLDS),
            "feature_window_series_drift_thresholds": dict(FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS),
            "intermediate_representation": "internal-body-state-latent",
            "literature_refs": deepcopy(list(REQUIRED_LITERATURE_REFS)),
            "conflict_sink_url": BDT_CONFLICT_SINK_URL,
            "conflict_policy": "route-unresolved-equivalence-and-thought-claims-to-mind-upload.com",
            "storage_policy": "feature-digest+latent-summary-only",
            "raw_source_payload_stored": False,
            "raw_generated_waveform_stored": False,
            "subjective_equivalence_claimed": False,
        }

    def open_session(
        self,
        identity_id: str,
        source_modalities: Sequence[str] = DEFAULT_SOURCE_MODALITIES,
        target_modalities: Sequence[str] = DEFAULT_TARGET_MODALITIES,
    ) -> Dict[str, Any]:
        self._require_non_empty_string(identity_id, "identity_id")
        sources = self._normalize_modalities(source_modalities, "source_modalities")
        targets = self._normalize_modalities(target_modalities, "target_modalities")
        session_id = new_id("bdt")
        opened_at = utc_now_iso()
        session = {
            "schema_version": BDT_SCHEMA_VERSION,
            "session_id": session_id,
            "identity_id": identity_id,
            "opened_at": opened_at,
            "profile_id": BDT_PROFILE_ID,
            "latent_profile_id": BDT_LATENT_PROFILE_ID,
            "generator_profile_id": BDT_GENERATOR_PROFILE_ID,
            "source_modalities": sources,
            "target_modalities": targets,
            "literature_refs": deepcopy(list(REQUIRED_LITERATURE_REFS)),
            "conflict_refs": deepcopy(list(DEFAULT_CONFLICT_REFS)),
            "mind_upload_conflict_sink_url": BDT_CONFLICT_SINK_URL,
            "storage_policy": "feature-digest+latent-summary-only",
            "raw_source_payload_stored": False,
            "raw_generated_waveform_stored": False,
            "subjective_equivalence_claimed": False,
            "last_latent_ref": "",
            "last_generated_bundle_ref": "",
        }
        self.sessions[session_id] = session
        return deepcopy(session)

    def adapt_dataset_feature_window(
        self,
        session_id: str,
        dataset_manifest: Dict[str, Any],
        window_feature_summaries: Dict[str, Dict[str, Any]],
        context_label: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        self._require_non_empty_string(context_label, "context_label")
        manifest = self._normalize_dataset_manifest(dataset_manifest)
        features = self._normalize_biosignal_features(window_feature_summaries)
        observed_modalities = [modality for modality in session["source_modalities"] if modality in features]
        if not observed_modalities:
            raise ValueError("at least one source modality must be present in window_feature_summaries")
        missing_manifest_modalities = [
            modality for modality in observed_modalities if modality not in manifest["modality_file_refs"]
        ]
        if missing_manifest_modalities:
            raise ValueError(
                "dataset_manifest.modality_file_refs must cover observed modalities: "
                f"{missing_manifest_modalities}"
            )

        latent_state = self.encode_body_state(
            session_id,
            biosignal_features=features,
            context_label=context_label,
        )
        required_modalities_bound = sorted(observed_modalities) == sorted(DEFAULT_SOURCE_MODALITIES)
        adapter_receipt = {
            "schema_version": BDT_SCHEMA_VERSION,
            "adapter_ref": f"dataset-adapter://biodata/{new_id('bdt-dataset-adapter')}",
            "created_at": utc_now_iso(),
            "profile_id": BDT_DATASET_ADAPTER_PROFILE_ID,
            "session_id": session_id,
            "identity_id": session["identity_id"],
            "dataset_ref": manifest["dataset_ref"],
            "participant_ref": manifest["participant_ref"],
            "license_ref": manifest["license_ref"],
            "window_ref": manifest["window_ref"],
            "dataset_manifest_digest": sha256_text(canonical_json(manifest)),
            "source_feature_digest": latent_state["source_feature_digest"],
            "source_modalities_observed": observed_modalities,
            "source_modalities_required": list(DEFAULT_SOURCE_MODALITIES),
            "required_modalities_bound": required_modalities_bound,
            "latent_ref": latent_state["latent_ref"],
            "latent_digest": latent_state["latent_digest"],
            "latent_profile_id": latent_state["profile_id"],
            "feature_window_policy": "dataset-window-feature-summary-digest-only-v1",
            "storage_policy": "dataset-manifest-digest+feature-window-digest+latent-ref-only",
            "literature_refs": deepcopy(session["literature_refs"]),
            "conflict_refs": deepcopy(session["conflict_refs"]),
            "mind_upload_conflict_sink_url": session["mind_upload_conflict_sink_url"],
            "raw_dataset_payload_stored": False,
            "raw_signal_samples_stored": False,
            "raw_feature_window_payload_stored": False,
            "raw_source_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        adapter_receipt["adapter_receipt_digest"] = sha256_text(
            canonical_json(self._dataset_adapter_digest_payload(adapter_receipt))
        )
        return {
            "adapter_receipt": deepcopy(adapter_receipt),
            "latent_state": deepcopy(latent_state),
        }

    def validate_dataset_adapter_receipt(
        self,
        session: Dict[str, Any],
        dataset_manifest: Dict[str, Any],
        latent_state: Dict[str, Any],
        adapter_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_session_mapping_for_errors(session, errors)
        manifest: Dict[str, Any] = {}
        try:
            manifest = self._normalize_dataset_manifest(dataset_manifest)
        except ValueError as exc:
            errors.append(str(exc))
        self._check_non_empty_string(adapter_receipt.get("adapter_ref"), "adapter_receipt.adapter_ref", errors)
        if adapter_receipt.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("adapter_receipt.schema_version mismatch")
        if adapter_receipt.get("profile_id") != BDT_DATASET_ADAPTER_PROFILE_ID:
            errors.append("adapter_receipt.profile_id mismatch")
        if adapter_receipt.get("session_id") != session.get("session_id"):
            errors.append("adapter_receipt.session_id must match session.session_id")
        if adapter_receipt.get("identity_id") != session.get("identity_id"):
            errors.append("adapter_receipt.identity_id must match session.identity_id")
        if latent_state.get("session_id") != session.get("session_id"):
            errors.append("latent_state.session_id must match session.session_id")
        if latent_state.get("identity_id") != session.get("identity_id"):
            errors.append("latent_state.identity_id must match session.identity_id")
        if adapter_receipt.get("latent_ref") != latent_state.get("latent_ref"):
            errors.append("adapter_receipt.latent_ref must match latent_state.latent_ref")
        if adapter_receipt.get("latent_digest") != latent_state.get("latent_digest"):
            errors.append("adapter_receipt.latent_digest must match latent_state.latent_digest")
        if adapter_receipt.get("source_feature_digest") != latent_state.get("source_feature_digest"):
            errors.append("adapter_receipt.source_feature_digest must match latent_state.source_feature_digest")

        expected_manifest_digest = sha256_text(canonical_json(manifest)) if manifest else ""
        manifest_digest_bound = (
            bool(expected_manifest_digest)
            and adapter_receipt.get("dataset_manifest_digest") == expected_manifest_digest
        )
        if not manifest_digest_bound:
            errors.append("adapter_receipt.dataset_manifest_digest mismatch")

        required_modalities_bound = (
            adapter_receipt.get("source_modalities_required") == list(DEFAULT_SOURCE_MODALITIES)
            and sorted(adapter_receipt.get("source_modalities_observed", []))
            == sorted(DEFAULT_SOURCE_MODALITIES)
            and adapter_receipt.get("required_modalities_bound") is True
        )
        if not required_modalities_bound:
            errors.append("adapter_receipt must bind all required source modalities")
        expected_adapter_digest = sha256_text(
            canonical_json(self._dataset_adapter_digest_payload(adapter_receipt))
        )
        adapter_receipt_digest_bound = (
            adapter_receipt.get("adapter_receipt_digest") == expected_adapter_digest
        )
        if not adapter_receipt_digest_bound:
            errors.append("adapter_receipt.adapter_receipt_digest mismatch")
        for field_name in (
            "raw_dataset_payload_stored",
            "raw_signal_samples_stored",
            "raw_feature_window_payload_stored",
            "raw_source_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if adapter_receipt.get(field_name) is not False:
                errors.append(f"adapter_receipt.{field_name} must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": adapter_receipt.get("profile_id"),
            "person_bound": session.get("identity_id") == adapter_receipt.get("identity_id") == latent_state.get("identity_id"),
            "dataset_manifest_digest_bound": manifest_digest_bound,
            "source_feature_digest_bound": (
                adapter_receipt.get("source_feature_digest") == latent_state.get("source_feature_digest")
            ),
            "latent_digest_bound": (
                adapter_receipt.get("latent_digest") == latent_state.get("latent_digest")
            ),
            "required_modalities_bound": required_modalities_bound,
            "adapter_receipt_digest_bound": adapter_receipt_digest_bound,
            "feature_window_policy_bound": (
                adapter_receipt.get("feature_window_policy")
                == "dataset-window-feature-summary-digest-only-v1"
            ),
            "raw_dataset_payload_stored": False,
            "raw_signal_samples_stored": False,
            "raw_feature_window_payload_stored": False,
            "raw_source_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def build_feature_window_series_profile(
        self,
        session: Dict[str, Any],
        adapter_receipts: Sequence[Dict[str, Any]],
        latent_states: Sequence[Dict[str, Any]],
        circadian_phase_refs: Sequence[str],
        circadian_phase_verifier_receipt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._check_session_mapping(session)
        if not isinstance(adapter_receipts, (list, tuple)) or len(adapter_receipts) < 2:
            raise ValueError("adapter_receipts must contain at least two dataset adapter receipts")
        if not isinstance(latent_states, (list, tuple)) or len(latent_states) != len(adapter_receipts):
            raise ValueError("latent_states must align with adapter_receipts")
        if not isinstance(circadian_phase_refs, (list, tuple)) or len(circadian_phase_refs) != len(adapter_receipts):
            raise ValueError("circadian_phase_refs must align with adapter_receipts")

        normalized_phase_refs: List[str] = []
        adapter_refs: List[str] = []
        adapter_receipt_digests: List[str] = []
        window_refs: List[str] = []
        dataset_refs: List[str] = []
        latent_refs: List[str] = []
        latent_digests: List[str] = []
        source_feature_digests: List[str] = []
        source_modalities = set()
        phase_summaries: List[Dict[str, Any]] = []
        axis_samples: Dict[str, List[float]] = {
            "heart_rate_bpm": [],
            "autonomic_arousal": [],
            "cortical_load_proxy": [],
            "valence_proxy": [],
            "thought_pressure_proxy": [],
            "interoceptive_confidence": [],
        }

        for index, adapter_receipt in enumerate(adapter_receipts):
            latent_state = latent_states[index]
            self._validate_dataset_adapter_window_for_series(session, adapter_receipt, latent_state)
            phase_ref = str(circadian_phase_refs[index]).strip()
            self._require_non_empty_string(phase_ref, "circadian_phase_ref")
            normalized_phase_refs.append(phase_ref)
            adapter_refs.append(str(adapter_receipt["adapter_ref"]))
            adapter_receipt_digests.append(str(adapter_receipt["adapter_receipt_digest"]))
            window_refs.append(str(adapter_receipt["window_ref"]))
            dataset_refs.append(str(adapter_receipt["dataset_ref"]))
            latent_refs.append(str(latent_state["latent_ref"]))
            latent_digests.append(str(latent_state["latent_digest"]))
            source_feature_digests.append(str(adapter_receipt["source_feature_digest"]))
            source_modalities.update(str(item) for item in adapter_receipt["source_modalities_observed"])
            axes = latent_state["physiological_axes"]
            axis_samples["heart_rate_bpm"].append(float(axes["cardiac"]["heart_rate_bpm"]))
            axis_samples["autonomic_arousal"].append(float(axes["autonomic"]["arousal"]))
            axis_samples["cortical_load_proxy"].append(float(axes["neural"]["cortical_load_proxy"]))
            axis_samples["valence_proxy"].append(float(axes["affect"]["valence_proxy"]))
            axis_samples["thought_pressure_proxy"].append(
                float(axes["thought"]["attention_pressure_proxy"])
            )
            axis_samples["interoceptive_confidence"].append(
                float(latent_state["interoceptive_confidence"])
            )
            phase_summaries.append(
                {
                    "phase_ref": phase_ref,
                    "window_ref": adapter_receipt["window_ref"],
                    "adapter_ref": adapter_receipt["adapter_ref"],
                    "adapter_receipt_digest": adapter_receipt["adapter_receipt_digest"],
                    "latent_ref": latent_state["latent_ref"],
                    "latent_digest": latent_state["latent_digest"],
                    "source_feature_digest": adapter_receipt["source_feature_digest"],
                    "normalized_window_index": index,
                }
            )

        if len(set(normalized_phase_refs)) < 2:
            raise ValueError("circadian_phase_refs must cover at least two unique phases")
        digest_set_payload = {
            "profile_id": BDT_FEATURE_WINDOW_SERIES_PROFILE_ID,
            "adapter_receipt_digests": adapter_receipt_digests,
            "latent_digests": latent_digests,
            "circadian_phase_refs": normalized_phase_refs,
        }
        phase_verifier_ref = ""
        phase_verifier_digest = ""
        phase_verifier_source_digest_set = ""
        phase_verifier_status = "not-bound"
        phase_verifier_bound = False
        if circadian_phase_verifier_receipt is not None:
            verifier_validation = self.validate_circadian_phase_verifier(
                session,
                normalized_phase_refs,
                circadian_phase_verifier_receipt,
            )
            if not verifier_validation["ok"]:
                raise ValueError(
                    "circadian_phase_verifier_receipt is invalid: "
                    + "; ".join(verifier_validation["errors"])
                )
            phase_verifier_ref = str(circadian_phase_verifier_receipt["phase_verifier_ref"])
            phase_verifier_digest = str(circadian_phase_verifier_receipt["phase_verifier_digest"])
            phase_verifier_source_digest_set = str(
                circadian_phase_verifier_receipt["verifier_source_digest_set"]
            )
            phase_verifier_status = str(circadian_phase_verifier_receipt["verifier_quorum_status"])
            phase_verifier_bound = True
        digest_set_payload["circadian_phase_verifier_digest"] = phase_verifier_digest
        drift_summary = {
            axis_name: self._summarize_axis_drift(values)
            for axis_name, values in axis_samples.items()
        }
        profile = {
            "schema_version": BDT_SCHEMA_VERSION,
            "series_ref": f"feature-window-series://biodata/{new_id('bdt-window-series')}",
            "created_at": utc_now_iso(),
            "profile_id": BDT_FEATURE_WINDOW_SERIES_PROFILE_ID,
            "session_id": session["session_id"],
            "identity_id": session["identity_id"],
            "adapter_refs": adapter_refs,
            "adapter_receipt_digests": adapter_receipt_digests,
            "window_refs": window_refs,
            "dataset_refs": dataset_refs,
            "latent_refs": latent_refs,
            "latent_digests": latent_digests,
            "source_feature_digests": source_feature_digests,
            "series_digest_set_digest": sha256_text(canonical_json(digest_set_payload)),
            "window_count": len(adapter_receipts),
            "dataset_count": len(set(dataset_refs)),
            "source_modalities_covered": sorted(source_modalities),
            "required_modalities_bound": sorted(source_modalities) == sorted(DEFAULT_SOURCE_MODALITIES),
            "circadian_phase_refs": normalized_phase_refs,
            "circadian_phase_summary": phase_summaries,
            "circadian_profile_bound": len(set(normalized_phase_refs)) >= 2,
            "circadian_phase_verifier_ref": phase_verifier_ref,
            "circadian_phase_verifier_digest": phase_verifier_digest,
            "circadian_phase_verifier_source_digest_set": phase_verifier_source_digest_set,
            "circadian_phase_verifier_status": phase_verifier_status,
            "circadian_phase_verifier_bound": phase_verifier_bound,
            "axis_drift_summary": drift_summary,
            "drift_policy": "ordered-feature-window-latent-drift-digest-only-v1",
            "storage_policy": "adapter-receipt-digest+latent-digest+phase-verifier-ref-only",
            "literature_refs": deepcopy(session["literature_refs"]),
            "conflict_refs": deepcopy(session["conflict_refs"]),
            "mind_upload_conflict_sink_url": session["mind_upload_conflict_sink_url"],
            "raw_dataset_payload_stored": False,
            "raw_signal_samples_stored": False,
            "raw_feature_window_payload_stored": False,
            "raw_latent_payload_stored": False,
            "raw_series_payload_stored": False,
            "raw_phase_verifier_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        profile["series_profile_digest"] = sha256_text(
            canonical_json(self._feature_window_series_digest_payload(profile))
        )
        return deepcopy(profile)

    def validate_feature_window_series_profile(
        self,
        session: Dict[str, Any],
        adapter_receipts: Sequence[Dict[str, Any]],
        latent_states: Sequence[Dict[str, Any]],
        series_profile: Dict[str, Any],
        circadian_phase_verifier_receipt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_session_mapping_for_errors(session, errors)
        if series_profile.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("series_profile.schema_version mismatch")
        if series_profile.get("profile_id") != BDT_FEATURE_WINDOW_SERIES_PROFILE_ID:
            errors.append("series_profile.profile_id mismatch")
        if series_profile.get("session_id") != session.get("session_id"):
            errors.append("series_profile.session_id must match session.session_id")
        if series_profile.get("identity_id") != session.get("identity_id"):
            errors.append("series_profile.identity_id must match session.identity_id")
        self._check_non_empty_string(series_profile.get("series_ref"), "series_profile.series_ref", errors)

        adapter_receipt_digests = [str(item.get("adapter_receipt_digest", "")) for item in adapter_receipts]
        latent_digests = [str(item.get("latent_digest", "")) for item in latent_states]
        phase_refs = [str(item) for item in series_profile.get("circadian_phase_refs", [])]
        expected_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_FEATURE_WINDOW_SERIES_PROFILE_ID,
                    "adapter_receipt_digests": adapter_receipt_digests,
                    "latent_digests": latent_digests,
                    "circadian_phase_refs": phase_refs,
                    "circadian_phase_verifier_digest": series_profile.get(
                        "circadian_phase_verifier_digest",
                        "",
                    ),
                }
            )
        )
        if series_profile.get("adapter_receipt_digests") != adapter_receipt_digests:
            errors.append("series_profile.adapter_receipt_digests must match adapter receipts")
        if series_profile.get("latent_digests") != latent_digests:
            errors.append("series_profile.latent_digests must match latent states")
        if series_profile.get("series_digest_set_digest") != expected_digest_set:
            errors.append("series_profile.series_digest_set_digest mismatch")

        expected_profile_digest = sha256_text(
            canonical_json(self._feature_window_series_digest_payload(series_profile))
        )
        if series_profile.get("series_profile_digest") != expected_profile_digest:
            errors.append("series_profile.series_profile_digest mismatch")

        required_modalities_bound = (
            sorted(series_profile.get("source_modalities_covered", [])) == sorted(DEFAULT_SOURCE_MODALITIES)
            and series_profile.get("required_modalities_bound") is True
        )
        if not required_modalities_bound:
            errors.append("series_profile.required_modalities_bound must be true")
        circadian_profile_bound = (
            isinstance(phase_refs, list)
            and len(phase_refs) >= 2
            and len(set(phase_refs)) >= 2
            and series_profile.get("circadian_profile_bound") is True
        )
        if not circadian_profile_bound:
            errors.append("series_profile.circadian_profile_bound must be true")
        phase_verifier_bound = series_profile.get("circadian_phase_verifier_bound") is True
        phase_verifier_status = str(
            series_profile.get("circadian_phase_verifier_status", "not-bound")
        )
        phase_verifier_digest_bound = False
        if phase_verifier_bound:
            if phase_verifier_status != "complete":
                errors.append("series_profile.circadian_phase_verifier_status must be complete")
            self._check_non_empty_string(
                series_profile.get("circadian_phase_verifier_ref"),
                "series_profile.circadian_phase_verifier_ref",
                errors,
            )
            self._check_non_empty_string(
                series_profile.get("circadian_phase_verifier_digest"),
                "series_profile.circadian_phase_verifier_digest",
                errors,
            )
            self._check_non_empty_string(
                series_profile.get("circadian_phase_verifier_source_digest_set"),
                "series_profile.circadian_phase_verifier_source_digest_set",
                errors,
            )
            if circadian_phase_verifier_receipt is not None:
                verifier_validation = self.validate_circadian_phase_verifier(
                    session,
                    phase_refs,
                    circadian_phase_verifier_receipt,
                )
                if not verifier_validation["ok"]:
                    errors.extend(
                        f"circadian_phase_verifier_receipt.{error}"
                        for error in verifier_validation["errors"]
                    )
                phase_verifier_digest_bound = (
                    series_profile.get("circadian_phase_verifier_ref")
                    == circadian_phase_verifier_receipt.get("phase_verifier_ref")
                    and series_profile.get("circadian_phase_verifier_digest")
                    == circadian_phase_verifier_receipt.get("phase_verifier_digest")
                    and series_profile.get("circadian_phase_verifier_source_digest_set")
                    == circadian_phase_verifier_receipt.get("verifier_source_digest_set")
                )
            else:
                phase_verifier_digest_bound = bool(
                    series_profile.get("circadian_phase_verifier_digest")
                )
        elif phase_verifier_status != "not-bound":
            errors.append("unbound circadian phase verifier must use not-bound status")
        axis_drift_summary = series_profile.get("axis_drift_summary", {})
        axis_drift_summary_bound = (
            isinstance(axis_drift_summary, dict)
            and set(axis_drift_summary)
            == {
                "heart_rate_bpm",
                "autonomic_arousal",
                "cortical_load_proxy",
                "valence_proxy",
                "thought_pressure_proxy",
                "interoceptive_confidence",
            }
        )
        if not axis_drift_summary_bound:
            errors.append("series_profile.axis_drift_summary must include required axes")
        if series_profile.get("window_count") != len(adapter_receipts):
            errors.append("series_profile.window_count must match adapter receipt count")

        for field_name in (
            "raw_dataset_payload_stored",
            "raw_signal_samples_stored",
            "raw_feature_window_payload_stored",
            "raw_latent_payload_stored",
            "raw_series_payload_stored",
            "raw_phase_verifier_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if series_profile.get(field_name) is not False:
                errors.append(f"series_profile.{field_name} must be false")

        for adapter_receipt, latent_state in zip(adapter_receipts, latent_states):
            try:
                self._validate_dataset_adapter_window_for_series(session, adapter_receipt, latent_state)
            except ValueError as exc:
                errors.append(str(exc))

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": series_profile.get("profile_id"),
            "person_bound": series_profile.get("identity_id") == session.get("identity_id"),
            "series_digest_set_bound": (
                series_profile.get("series_digest_set_digest") == expected_digest_set
            ),
            "series_profile_digest_bound": (
                series_profile.get("series_profile_digest") == expected_profile_digest
            ),
            "adapter_receipt_digest_set_bound": (
                series_profile.get("adapter_receipt_digests") == adapter_receipt_digests
            ),
            "latent_digest_set_bound": series_profile.get("latent_digests") == latent_digests,
            "required_modalities_bound": required_modalities_bound,
            "circadian_profile_bound": circadian_profile_bound,
            "circadian_phase_verifier_bound": phase_verifier_bound,
            "circadian_phase_verifier_digest_bound": phase_verifier_digest_bound,
            "axis_drift_summary_bound": axis_drift_summary_bound,
            "raw_dataset_payload_stored": False,
            "raw_signal_samples_stored": False,
            "raw_feature_window_payload_stored": False,
            "raw_latent_payload_stored": False,
            "raw_series_payload_stored": False,
            "raw_phase_verifier_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def bind_circadian_phase_verifier(
        self,
        session: Dict[str, Any],
        circadian_phase_refs: Sequence[str],
        verifier_sources: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self._check_session_mapping(session)
        phase_refs = self._normalize_circadian_phase_refs(circadian_phase_refs)
        sources = self._normalize_circadian_verifier_sources(verifier_sources, phase_refs)
        source_digests = [source["source_digest"] for source in sources]
        phase_ref_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
                    "circadian_phase_refs": phase_refs,
                }
            )
        )
        verifier_source_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
                    "source_digests": source_digests,
                }
            )
        )
        receipt = {
            "schema_version": BDT_SCHEMA_VERSION,
            "phase_verifier_ref": f"circadian-phase-verifier://biodata/{new_id('bdt-phase-verifier')}",
            "created_at": utc_now_iso(),
            "profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
            "session_id": session["session_id"],
            "identity_id": session["identity_id"],
            "circadian_phase_refs": phase_refs,
            "phase_ref_digest_set": phase_ref_digest_set,
            "required_source_types": list(CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES),
            "verifier_source_types": [source["source_type"] for source in sources],
            "verifier_sources": sources,
            "verifier_source_digest_set": verifier_source_digest_set,
            "verifier_quorum_status": "complete",
            "phase_alignment_policy": "external-clock-sleep-diary-wearable-quorum-v1",
            "phase_verifier_bound": True,
            "storage_policy": "phase-ref+verifier-source-digest-only",
            "raw_clock_payload_stored": False,
            "raw_sleep_diary_payload_stored": False,
            "raw_wearable_payload_stored": False,
            "raw_phase_payload_stored": False,
            "raw_verifier_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        receipt["phase_verifier_digest"] = sha256_text(
            canonical_json(self._circadian_phase_verifier_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def validate_circadian_phase_verifier(
        self,
        session: Dict[str, Any],
        circadian_phase_refs: Sequence[str],
        verifier_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_session_mapping_for_errors(session, errors)
        phase_refs: List[str] = []
        try:
            phase_refs = self._normalize_circadian_phase_refs(circadian_phase_refs)
        except ValueError as exc:
            errors.append(str(exc))
        if not isinstance(verifier_receipt, dict):
            errors.append("verifier_receipt must be a mapping")
            verifier_receipt = {}
        self._check_non_empty_string(
            verifier_receipt.get("phase_verifier_ref"),
            "verifier_receipt.phase_verifier_ref",
            errors,
        )
        if verifier_receipt.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("verifier_receipt.schema_version mismatch")
        if verifier_receipt.get("profile_id") != BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID:
            errors.append("verifier_receipt.profile_id mismatch")
        if verifier_receipt.get("session_id") != session.get("session_id"):
            errors.append("verifier_receipt.session_id must match session.session_id")
        if verifier_receipt.get("identity_id") != session.get("identity_id"):
            errors.append("verifier_receipt.identity_id must match session.identity_id")
        if verifier_receipt.get("circadian_phase_refs") != phase_refs:
            errors.append("verifier_receipt.circadian_phase_refs must match requested phases")
        expected_phase_ref_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
                    "circadian_phase_refs": phase_refs,
                }
            )
        )
        phase_ref_digest_set_bound = (
            verifier_receipt.get("phase_ref_digest_set") == expected_phase_ref_digest_set
        )
        if not phase_ref_digest_set_bound:
            errors.append("verifier_receipt.phase_ref_digest_set mismatch")
        sources = verifier_receipt.get("verifier_sources", [])
        normalized_sources: List[Dict[str, Any]] = []
        try:
            normalized_sources = self._normalize_circadian_verifier_sources(
                sources,
                phase_refs,
            )
        except ValueError as exc:
            errors.append(str(exc))
        expected_source_digests = [source["source_digest"] for source in normalized_sources]
        expected_source_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
                    "source_digests": expected_source_digests,
                }
            )
        )
        source_digest_set_bound = (
            verifier_receipt.get("verifier_source_digest_set") == expected_source_digest_set
        )
        if not source_digest_set_bound:
            errors.append("verifier_receipt.verifier_source_digest_set mismatch")
        if verifier_receipt.get("verifier_sources") != normalized_sources:
            errors.append("verifier_receipt.verifier_sources mismatch")
        required_source_types_bound = (
            verifier_receipt.get("required_source_types")
            == list(CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES)
            and verifier_receipt.get("verifier_source_types")
            == list(CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES)
        )
        if not required_source_types_bound:
            errors.append("verifier_receipt must bind external-clock, sleep-diary, and wearable sources")
        if verifier_receipt.get("verifier_quorum_status") != "complete":
            errors.append("verifier_receipt.verifier_quorum_status must be complete")
        if verifier_receipt.get("phase_verifier_bound") is not True:
            errors.append("verifier_receipt.phase_verifier_bound must be true")
        expected_digest = sha256_text(
            canonical_json(self._circadian_phase_verifier_digest_payload(verifier_receipt))
        )
        phase_verifier_digest_bound = (
            verifier_receipt.get("phase_verifier_digest") == expected_digest
        )
        if not phase_verifier_digest_bound:
            errors.append("verifier_receipt.phase_verifier_digest mismatch")
        for field_name in (
            "raw_clock_payload_stored",
            "raw_sleep_diary_payload_stored",
            "raw_wearable_payload_stored",
            "raw_phase_payload_stored",
            "raw_verifier_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if verifier_receipt.get(field_name) is not False:
                errors.append(f"verifier_receipt.{field_name} must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": verifier_receipt.get("profile_id"),
            "phase_ref_digest_set_bound": phase_ref_digest_set_bound,
            "verifier_source_digest_set_bound": source_digest_set_bound,
            "required_source_types_bound": required_source_types_bound,
            "verifier_quorum_status": verifier_receipt.get("verifier_quorum_status"),
            "phase_verifier_digest_bound": phase_verifier_digest_bound,
            "raw_clock_payload_stored": False,
            "raw_sleep_diary_payload_stored": False,
            "raw_wearable_payload_stored": False,
            "raw_phase_payload_stored": False,
            "raw_verifier_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def bind_feature_window_series_drift_gate(
        self,
        session: Dict[str, Any],
        series_profile: Dict[str, Any],
        calibration_profile: Dict[str, Any],
        axis_thresholds: Dict[str, float] | None = None,
    ) -> Dict[str, Any]:
        self._check_session_mapping(session)
        thresholds = self._normalize_series_drift_thresholds(axis_thresholds)
        self._validate_series_and_calibration_for_drift_gate(
            session,
            series_profile,
            calibration_profile,
        )
        axis_drift_summary = series_profile["axis_drift_summary"]
        drift_checks = []
        for axis_name in sorted(FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS):
            absolute_delta = abs(float(axis_drift_summary[axis_name]["absolute_delta"]))
            max_absolute_delta = thresholds[axis_name]
            within_threshold = absolute_delta <= max_absolute_delta
            drift_checks.append(
                {
                    "axis": axis_name,
                    "absolute_delta": round(absolute_delta, 3),
                    "max_absolute_delta": max_absolute_delta,
                    "within_threshold": within_threshold,
                    "status": "pass" if within_threshold else "blocked",
                }
            )
        drift_threshold_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID,
                    "series_profile_digest": series_profile["series_profile_digest"],
                    "calibration_digest": calibration_profile["calibration_digest"],
                    "axis_thresholds": thresholds,
                    "axis_drift_checks": drift_checks,
                }
            )
        )
        drift_gate_status = (
            "pass" if all(check["within_threshold"] for check in drift_checks) else "blocked"
        )
        receipt = {
            "schema_version": BDT_SCHEMA_VERSION,
            "drift_gate_ref": f"feature-window-drift-gate://biodata/{new_id('bdt-window-drift-gate')}",
            "created_at": utc_now_iso(),
            "profile_id": BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID,
            "session_id": session["session_id"],
            "identity_id": session["identity_id"],
            "series_ref": series_profile["series_ref"],
            "series_profile_digest": series_profile["series_profile_digest"],
            "series_digest_set_digest": series_profile["series_digest_set_digest"],
            "calibration_ref": calibration_profile["calibration_ref"],
            "calibration_digest": calibration_profile["calibration_digest"],
            "source_latent_digest_set_digest": calibration_profile[
                "source_latent_digest_set_digest"
            ],
            "series_calibration_latent_set_bound": (
                series_profile["latent_digests"] == calibration_profile["source_latent_digests"]
            ),
            "axis_threshold_policy": "feature-window-series-drift-thresholds-v1",
            "axis_thresholds": thresholds,
            "axis_drift_checks": drift_checks,
            "drift_threshold_digest": drift_threshold_digest,
            "drift_gate_status": drift_gate_status,
            "series_profile_bound": True,
            "calibration_profile_bound": True,
            "drift_thresholds_bound": True,
            "raw_series_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        receipt["drift_gate_digest"] = sha256_text(
            canonical_json(self._series_drift_gate_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def validate_feature_window_series_drift_gate(
        self,
        session: Dict[str, Any],
        series_profile: Dict[str, Any],
        calibration_profile: Dict[str, Any],
        drift_gate_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_session_mapping_for_errors(session, errors)
        self._check_non_empty_string(
            drift_gate_receipt.get("drift_gate_ref"),
            "drift_gate_receipt.drift_gate_ref",
            errors,
        )
        if drift_gate_receipt.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("drift_gate_receipt.schema_version mismatch")
        if drift_gate_receipt.get("profile_id") != BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID:
            errors.append("drift_gate_receipt.profile_id mismatch")
        if drift_gate_receipt.get("session_id") != session.get("session_id"):
            errors.append("drift_gate_receipt.session_id must match session.session_id")
        if drift_gate_receipt.get("identity_id") != session.get("identity_id"):
            errors.append("drift_gate_receipt.identity_id must match session.identity_id")
        try:
            self._validate_series_and_calibration_for_drift_gate(
                session,
                series_profile,
                calibration_profile,
            )
        except ValueError as exc:
            errors.append(str(exc))

        thresholds: Dict[str, float] = {}
        try:
            thresholds = self._normalize_series_drift_thresholds(
                drift_gate_receipt.get("axis_thresholds")
            )
        except ValueError as exc:
            errors.append(str(exc))
        expected_checks: List[Dict[str, Any]] = []
        if thresholds and isinstance(series_profile.get("axis_drift_summary"), dict):
            for axis_name in sorted(FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS):
                axis_summary = series_profile["axis_drift_summary"].get(axis_name, {})
                absolute_delta = abs(float(axis_summary.get("absolute_delta", 0.0)))
                max_absolute_delta = thresholds[axis_name]
                within_threshold = absolute_delta <= max_absolute_delta
                expected_checks.append(
                    {
                        "axis": axis_name,
                        "absolute_delta": round(absolute_delta, 3),
                        "max_absolute_delta": max_absolute_delta,
                        "within_threshold": within_threshold,
                        "status": "pass" if within_threshold else "blocked",
                    }
                )
        drift_checks_bound = drift_gate_receipt.get("axis_drift_checks") == expected_checks
        if not drift_checks_bound:
            errors.append("drift_gate_receipt.axis_drift_checks mismatch")
        expected_threshold_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID,
                    "series_profile_digest": series_profile.get("series_profile_digest"),
                    "calibration_digest": calibration_profile.get("calibration_digest"),
                    "axis_thresholds": thresholds,
                    "axis_drift_checks": expected_checks,
                }
            )
        )
        drift_threshold_digest_bound = (
            drift_gate_receipt.get("drift_threshold_digest") == expected_threshold_digest
        )
        if not drift_threshold_digest_bound:
            errors.append("drift_gate_receipt.drift_threshold_digest mismatch")
        expected_status = (
            "pass"
            if expected_checks and all(check["within_threshold"] for check in expected_checks)
            else "blocked"
        )
        if drift_gate_receipt.get("drift_gate_status") != expected_status:
            errors.append("drift_gate_receipt.drift_gate_status mismatch")
        expected_gate_digest = sha256_text(
            canonical_json(self._series_drift_gate_digest_payload(drift_gate_receipt))
        )
        drift_gate_digest_bound = (
            drift_gate_receipt.get("drift_gate_digest") == expected_gate_digest
        )
        if not drift_gate_digest_bound:
            errors.append("drift_gate_receipt.drift_gate_digest mismatch")
        series_profile_bound = (
            drift_gate_receipt.get("series_ref") == series_profile.get("series_ref")
            and drift_gate_receipt.get("series_profile_digest")
            == series_profile.get("series_profile_digest")
            and drift_gate_receipt.get("series_digest_set_digest")
            == series_profile.get("series_digest_set_digest")
            and drift_gate_receipt.get("series_profile_bound") is True
        )
        calibration_profile_bound = (
            drift_gate_receipt.get("calibration_ref") == calibration_profile.get("calibration_ref")
            and drift_gate_receipt.get("calibration_digest")
            == calibration_profile.get("calibration_digest")
            and drift_gate_receipt.get("source_latent_digest_set_digest")
            == calibration_profile.get("source_latent_digest_set_digest")
            and drift_gate_receipt.get("calibration_profile_bound") is True
        )
        latent_set_bound = (
            series_profile.get("latent_digests") == calibration_profile.get("source_latent_digests")
            and drift_gate_receipt.get("series_calibration_latent_set_bound") is True
        )
        if not series_profile_bound:
            errors.append("drift_gate_receipt must bind the feature-window series profile")
        if not calibration_profile_bound:
            errors.append("drift_gate_receipt must bind the calibration profile")
        if not latent_set_bound:
            errors.append("drift_gate_receipt must bind the same latent set as calibration")
        if drift_gate_receipt.get("drift_thresholds_bound") is not True:
            errors.append("drift_gate_receipt.drift_thresholds_bound must be true")
        for field_name in (
            "raw_series_payload_stored",
            "raw_calibration_payload_stored",
            "raw_drift_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if drift_gate_receipt.get(field_name) is not False:
                errors.append(f"drift_gate_receipt.{field_name} must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": drift_gate_receipt.get("profile_id"),
            "drift_gate_status": drift_gate_receipt.get("drift_gate_status"),
            "series_profile_bound": series_profile_bound,
            "calibration_profile_bound": calibration_profile_bound,
            "series_calibration_latent_set_bound": latent_set_bound,
            "drift_checks_bound": drift_checks_bound,
            "drift_threshold_digest_bound": drift_threshold_digest_bound,
            "drift_gate_digest_bound": drift_gate_digest_bound,
            "drift_thresholds_bound": drift_gate_receipt.get("drift_thresholds_bound") is True,
            "raw_series_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def encode_body_state(
        self,
        session_id: str,
        biosignal_features: Dict[str, Dict[str, Any]],
        context_label: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        self._require_non_empty_string(context_label, "context_label")
        features = self._normalize_biosignal_features(biosignal_features)
        observed_modalities = [modality for modality in session["source_modalities"] if modality in features]
        if not observed_modalities:
            raise ValueError("at least one source modality must be present in biosignal_features")

        eeg = features.get("eeg", {})
        ecg = features.get("ecg", {})
        ppg = features.get("ppg", {})
        eda = features.get("eda", {})
        respiration = features.get("respiration", {})

        heart_rate_bpm = self._coalesce_number(
            ecg.get("heart_rate_bpm"),
            ppg.get("pulse_rate_bpm"),
            default=72.0,
        )
        hrv_rmssd_ms = self._coalesce_number(ecg.get("hrv_rmssd_ms"), default=42.0)
        respiration_rate_bpm = self._coalesce_number(respiration.get("rate_bpm"), default=15.0)
        skin_conductance = self._coalesce_number(
            eda.get("skin_conductance_microsiemens"),
            default=4.0,
        )
        alpha_power = self._coalesce_number(eeg.get("alpha_power"), default=0.42)
        theta_power = self._coalesce_number(eeg.get("theta_power"), default=0.26)
        beta_power = self._coalesce_number(eeg.get("beta_power"), default=0.31)

        cardiac_load = self._clamp((heart_rate_bpm - 55.0) / 65.0)
        parasympathetic_tone = self._clamp(hrv_rmssd_ms / 90.0)
        sympathetic_tone = self._clamp(
            0.45 * cardiac_load
            + 0.35 * self._clamp(skin_conductance / 12.0)
            + 0.20 * self._clamp(respiration_rate_bpm / 28.0)
        )
        autonomic_arousal = self._clamp(0.65 * sympathetic_tone + 0.35 * (1.0 - parasympathetic_tone))
        alpha_suppression = self._clamp(1.0 - alpha_power)
        theta_beta_ratio = round(theta_power / max(beta_power, 0.01), 3)
        cortical_load_proxy = self._clamp(
            0.55 * alpha_suppression + 0.45 * self._clamp(theta_beta_ratio / 3.0)
        )
        valence_proxy = self._clamp(
            0.52 + 0.32 * (parasympathetic_tone - 0.5) - 0.28 * (sympathetic_tone - 0.5)
        )
        thought_pressure_proxy = self._clamp(
            0.58 * cortical_load_proxy + 0.42 * autonomic_arousal
        )
        interoceptive_confidence = round(len(observed_modalities) / len(session["source_modalities"]), 3)

        feature_digest = sha256_text(canonical_json(features))
        latent_id = new_id("body-latent")
        latent = {
            "schema_version": BDT_SCHEMA_VERSION,
            "latent_ref": f"latent://body-state/{latent_id}",
            "session_id": session_id,
            "identity_id": session["identity_id"],
            "recorded_at": utc_now_iso(),
            "profile_id": BDT_LATENT_PROFILE_ID,
            "context_label": context_label,
            "source_modalities": observed_modalities,
            "source_feature_digest": feature_digest,
            "physiological_axes": {
                "cardiac": {
                    "heart_rate_bpm": round(heart_rate_bpm, 3),
                    "hrv_rmssd_ms": round(hrv_rmssd_ms, 3),
                    "cardiac_load": round(cardiac_load, 3),
                },
                "autonomic": {
                    "sympathetic_tone": round(sympathetic_tone, 3),
                    "parasympathetic_tone": round(parasympathetic_tone, 3),
                    "arousal": round(autonomic_arousal, 3),
                },
                "respiratory": {
                    "rate_bpm": round(respiration_rate_bpm, 3),
                    "phase": str(respiration.get("phase", "phase-unknown")),
                },
                "neural": {
                    "alpha_suppression": round(alpha_suppression, 3),
                    "theta_beta_ratio": theta_beta_ratio,
                    "cortical_load_proxy": round(cortical_load_proxy, 3),
                },
                "affect": {
                    "valence_proxy": round(valence_proxy, 3),
                    "arousal_proxy": round(autonomic_arousal, 3),
                    "model": "circumplex-proxy",
                },
                "thought": {
                    "attention_pressure_proxy": round(thought_pressure_proxy, 3),
                    "semantic_content_generated": False,
                    "content_policy": "no-semantic-thought-content-from-biosignal-only",
                },
            },
            "interoceptive_confidence": interoceptive_confidence,
            "literature_refs": deepcopy(session["literature_refs"]),
            "conflict_refs": deepcopy(session["conflict_refs"]),
            "mind_upload_conflict_sink_url": session["mind_upload_conflict_sink_url"],
            "raw_source_payload_stored": False,
            "subjective_equivalence_claimed": False,
        }
        latent["latent_digest"] = sha256_text(canonical_json(latent))
        session["last_latent_ref"] = latent["latent_ref"]
        return deepcopy(latent)

    def generate_biosignal_bundle(
        self,
        session_id: str,
        latent_state: Dict[str, Any],
        target_modalities: Sequence[str] | None = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        self._validate_latent_for_session(session, latent_state)
        targets = (
            self._normalize_modalities(target_modalities, "target_modalities")
            if target_modalities is not None
            else list(session["target_modalities"])
        )
        unsupported_targets = [target for target in targets if target not in session["target_modalities"]]
        if unsupported_targets:
            raise ValueError(f"target modalities are not part of this session: {unsupported_targets}")

        axes = latent_state["physiological_axes"]
        cardiac = axes["cardiac"]
        autonomic = axes["autonomic"]
        respiratory = axes["respiratory"]
        neural = axes["neural"]
        affect = axes["affect"]
        thought = axes["thought"]

        bundle_id = new_id("bdt-bundle")
        signal_summaries: Dict[str, Dict[str, Any]] = {}
        if "ecg" in targets:
            signal_summaries["ecg"] = {
                "synthetic_ref": f"synthetic://biosignal/ecg/{bundle_id}",
                "heart_rate_bpm": cardiac["heart_rate_bpm"],
                "hrv_rmssd_ms": cardiac["hrv_rmssd_ms"],
                "confidence": self._clamp(latent_state["interoceptive_confidence"] * 0.92),
            }
        if "ppg" in targets:
            signal_summaries["ppg"] = {
                "synthetic_ref": f"synthetic://biosignal/ppg/{bundle_id}",
                "pulse_rate_bpm": cardiac["heart_rate_bpm"],
                "pulse_amplitude_proxy": round(self._clamp(1.0 - autonomic["sympathetic_tone"] * 0.4), 3),
                "confidence": self._clamp(latent_state["interoceptive_confidence"] * 0.88),
            }
        if "respiration" in targets:
            signal_summaries["respiration"] = {
                "synthetic_ref": f"synthetic://biosignal/respiration/{bundle_id}",
                "rate_bpm": respiratory["rate_bpm"],
                "phase": respiratory["phase"],
                "confidence": self._clamp(latent_state["interoceptive_confidence"] * 0.9),
            }
        if "eeg" in targets:
            signal_summaries["eeg"] = {
                "synthetic_ref": f"synthetic://biosignal/eeg/{bundle_id}",
                "alpha_power_proxy": round(self._clamp(1.0 - neural["alpha_suppression"]), 3),
                "theta_beta_ratio": neural["theta_beta_ratio"],
                "cortical_load_proxy": neural["cortical_load_proxy"],
                "confidence": self._clamp(latent_state["interoceptive_confidence"] * 0.72),
            }
        if "affect" in targets:
            signal_summaries["affect"] = {
                "synthetic_ref": f"synthetic://biosignal/affect/{bundle_id}",
                "valence_proxy": affect["valence_proxy"],
                "arousal_proxy": affect["arousal_proxy"],
                "label_policy": "valence-arousal-only-no-discrete-emotion-assertion",
                "confidence": self._clamp(latent_state["interoceptive_confidence"] * 0.66),
            }
        if "thought" in targets:
            signal_summaries["thought"] = {
                "synthetic_ref": f"synthetic://biosignal/thought-pressure/{bundle_id}",
                "attention_pressure_proxy": thought["attention_pressure_proxy"],
                "semantic_content_generated": False,
                "content_ref": "not-generated://thought-content",
                "confidence": self._clamp(latent_state["interoceptive_confidence"] * 0.34),
            }

        bundle = {
            "schema_version": BDT_SCHEMA_VERSION,
            "bundle_ref": f"synthetic://biosignal-bundle/{bundle_id}",
            "session_id": session_id,
            "identity_id": session["identity_id"],
            "generated_at": utc_now_iso(),
            "generator_profile_id": BDT_GENERATOR_PROFILE_ID,
            "source_latent_ref": latent_state["latent_ref"],
            "source_latent_digest": latent_state["latent_digest"],
            "target_modalities": targets,
            "signals": signal_summaries,
            "literature_refs": deepcopy(session["literature_refs"]),
            "conflict_refs": deepcopy(session["conflict_refs"]),
            "mind_upload_conflict_sink_url": session["mind_upload_conflict_sink_url"],
            "raw_source_payload_stored": False,
            "raw_generated_waveform_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        bundle["bundle_digest"] = sha256_text(canonical_json(bundle))
        session["last_generated_bundle_ref"] = bundle["bundle_ref"]
        return deepcopy(bundle)

    def build_calibration_profile(
        self,
        session_id: str,
        latent_states: Sequence[Dict[str, Any]],
        calibration_day_refs: Sequence[str],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if not isinstance(latent_states, (list, tuple)) or len(latent_states) < 2:
            raise ValueError("latent_states must contain at least two body-state latents")
        if not isinstance(calibration_day_refs, (list, tuple)) or len(calibration_day_refs) != len(latent_states):
            raise ValueError("calibration_day_refs must align with latent_states")

        normalized_day_refs: List[str] = []
        source_modalities = set()
        latent_refs: List[str] = []
        latent_digests: List[str] = []
        axis_samples: Dict[str, List[float]] = {
            "heart_rate_bpm": [],
            "hrv_rmssd_ms": [],
            "autonomic_arousal": [],
            "cortical_load_proxy": [],
            "valence_proxy": [],
            "thought_pressure_proxy": [],
            "interoceptive_confidence": [],
        }
        for index, latent_state in enumerate(latent_states):
            self._validate_latent_for_session(session, latent_state)
            day_ref = str(calibration_day_refs[index]).strip()
            self._require_non_empty_string(day_ref, "calibration_day_ref")
            normalized_day_refs.append(day_ref)
            source_modalities.update(str(item) for item in latent_state.get("source_modalities", []))
            latent_refs.append(str(latent_state["latent_ref"]))
            latent_digests.append(str(latent_state["latent_digest"]))
            axes = latent_state["physiological_axes"]
            axis_samples["heart_rate_bpm"].append(float(axes["cardiac"]["heart_rate_bpm"]))
            axis_samples["hrv_rmssd_ms"].append(float(axes["cardiac"]["hrv_rmssd_ms"]))
            axis_samples["autonomic_arousal"].append(float(axes["autonomic"]["arousal"]))
            axis_samples["cortical_load_proxy"].append(float(axes["neural"]["cortical_load_proxy"]))
            axis_samples["valence_proxy"].append(float(axes["affect"]["valence_proxy"]))
            axis_samples["thought_pressure_proxy"].append(
                float(axes["thought"]["attention_pressure_proxy"])
            )
            axis_samples["interoceptive_confidence"].append(
                float(latent_state["interoceptive_confidence"])
            )
        if len(set(normalized_day_refs)) < 2:
            raise ValueError("calibration_day_refs must cover at least two unique days")

        digest_set_payload = {
            "profile_id": BDT_CALIBRATION_PROFILE_ID,
            "source_latent_digests": latent_digests,
            "calibration_day_refs": normalized_day_refs,
        }
        axis_baselines = {
            key: round(sum(values) / len(values), 3)
            for key, values in axis_samples.items()
        }
        calibration = {
            "schema_version": BDT_SCHEMA_VERSION,
            "calibration_ref": f"calibration://biodata/{new_id('bdt-calibration')}",
            "session_id": session_id,
            "identity_id": session["identity_id"],
            "created_at": utc_now_iso(),
            "profile_id": BDT_CALIBRATION_PROFILE_ID,
            "latent_profile_id": BDT_LATENT_PROFILE_ID,
            "source_latent_refs": latent_refs,
            "source_latent_digests": latent_digests,
            "source_latent_digest_set_digest": sha256_text(canonical_json(digest_set_payload)),
            "calibration_day_refs": normalized_day_refs,
            "days_covered_count": len(set(normalized_day_refs)),
            "latent_count": len(latent_states),
            "source_modalities_covered": sorted(source_modalities),
            "axis_baselines": axis_baselines,
            "baseline_policy": "multi-day-mean-baseline-digest-only-v1",
            "minimum_latent_count": 2,
            "calibration_complete": len(latent_states) >= 2 and len(set(normalized_day_refs)) >= 2,
            "literature_refs": deepcopy(session["literature_refs"]),
            "conflict_refs": deepcopy(session["conflict_refs"]),
            "mind_upload_conflict_sink_url": session["mind_upload_conflict_sink_url"],
            "raw_source_payload_stored": False,
            "raw_latent_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        calibration["calibration_digest"] = sha256_text(
            canonical_json(self._calibration_digest_payload(calibration))
        )
        return deepcopy(calibration)

    def validate_calibration_profile(
        self,
        session: Dict[str, Any],
        latent_states: Sequence[Dict[str, Any]],
        calibration_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_non_empty_string(session.get("session_id"), "session.session_id", errors)
        self._check_non_empty_string(
            calibration_profile.get("calibration_ref"),
            "calibration_profile.calibration_ref",
            errors,
        )
        if calibration_profile.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("calibration_profile.schema_version mismatch")
        if calibration_profile.get("profile_id") != BDT_CALIBRATION_PROFILE_ID:
            errors.append("calibration_profile.profile_id mismatch")
        if calibration_profile.get("session_id") != session.get("session_id"):
            errors.append("calibration_profile.session_id must match session.session_id")
        if calibration_profile.get("identity_id") != session.get("identity_id"):
            errors.append("calibration_profile.identity_id must match session.identity_id")

        latent_digests = [str(latent.get("latent_digest", "")) for latent in latent_states]
        day_refs = calibration_profile.get("calibration_day_refs", [])
        expected_digest_set = sha256_text(
            canonical_json(
                {
                    "profile_id": BDT_CALIBRATION_PROFILE_ID,
                    "source_latent_digests": latent_digests,
                    "calibration_day_refs": day_refs,
                }
            )
        )
        if calibration_profile.get("source_latent_digests") != latent_digests:
            errors.append("calibration_profile.source_latent_digests must match latent states")
        if calibration_profile.get("source_latent_digest_set_digest") != expected_digest_set:
            errors.append("calibration_profile.source_latent_digest_set_digest mismatch")
        expected_profile_digest = sha256_text(
            canonical_json(self._calibration_digest_payload(calibration_profile))
        )
        if calibration_profile.get("calibration_digest") != expected_profile_digest:
            errors.append("calibration_profile.calibration_digest mismatch")
        if calibration_profile.get("raw_source_payload_stored") is not False:
            errors.append("calibration_profile.raw_source_payload_stored must be false")
        if calibration_profile.get("raw_latent_payload_stored") is not False:
            errors.append("calibration_profile.raw_latent_payload_stored must be false")
        if calibration_profile.get("raw_calibration_payload_stored") is not False:
            errors.append("calibration_profile.raw_calibration_payload_stored must be false")
        if calibration_profile.get("subjective_equivalence_claimed") is not False:
            errors.append("calibration_profile.subjective_equivalence_claimed must be false")
        if calibration_profile.get("semantic_thought_content_generated") is not False:
            errors.append("calibration_profile.semantic_thought_content_generated must be false")

        conflict_refs = calibration_profile.get("conflict_refs", [])
        conflict_sink_bound = (
            isinstance(conflict_refs, list)
            and bool(conflict_refs)
            and all(str(ref.get("mind_upload_ref", "")).startswith(BDT_CONFLICT_SINK_URL) for ref in conflict_refs)
        )
        days_covered = calibration_profile.get("days_covered_count")
        latent_count = calibration_profile.get("latent_count")
        multi_day_calibration_bound = days_covered >= 2 if isinstance(days_covered, int) else False
        minimum_latent_count_bound = latent_count >= 2 if isinstance(latent_count, int) else False
        if not multi_day_calibration_bound:
            errors.append("calibration_profile.days_covered_count must be at least two")
        if not minimum_latent_count_bound:
            errors.append("calibration_profile.latent_count must be at least two")
        if calibration_profile.get("calibration_complete") is not True:
            errors.append("calibration_profile.calibration_complete must be true")
        axis_baselines = calibration_profile.get("axis_baselines", {})
        axis_baselines_bound = (
            isinstance(axis_baselines, dict)
            and set(axis_baselines.keys())
            == {
                "heart_rate_bpm",
                "hrv_rmssd_ms",
                "autonomic_arousal",
                "cortical_load_proxy",
                "valence_proxy",
                "thought_pressure_proxy",
                "interoceptive_confidence",
            }
        )
        if not axis_baselines_bound:
            errors.append("calibration_profile.axis_baselines must include the required baseline axes")
        if not conflict_sink_bound:
            errors.append("calibration_profile.conflict_refs must bind to the BioData conflict sink")
        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": calibration_profile.get("profile_id"),
            "person_bound": calibration_profile.get("identity_id") == session.get("identity_id"),
            "multi_day_calibration_bound": multi_day_calibration_bound,
            "minimum_latent_count_bound": minimum_latent_count_bound,
            "source_latent_digest_set_bound": (
                calibration_profile.get("source_latent_digest_set_digest") == expected_digest_set
            ),
            "calibration_digest_bound": (
                calibration_profile.get("calibration_digest") == expected_profile_digest
            ),
            "axis_baselines_bound": axis_baselines_bound,
            "literature_backed_intermediate": len(calibration_profile.get("literature_refs", []))
            >= len(REQUIRED_LITERATURE_REFS),
            "mind_upload_conflict_sink_bound": conflict_sink_bound,
            "raw_source_payload_stored": False,
            "raw_latent_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def bind_calibration_confidence_gate(
        self,
        session: Dict[str, Any],
        calibration_profile: Dict[str, Any],
        target_gate_refs: Dict[str, str],
        feature_window_series_drift_gate_receipt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._check_session_mapping(session)
        normalized_target_refs = self._normalize_confidence_gate_refs(target_gate_refs)
        if calibration_profile.get("session_id") != session.get("session_id"):
            raise ValueError("calibration_profile.session_id must match session.session_id")
        if calibration_profile.get("identity_id") != session.get("identity_id"):
            raise ValueError("calibration_profile.identity_id must match session.identity_id")
        axis_baselines = calibration_profile.get("axis_baselines", {})
        if not isinstance(axis_baselines, dict):
            raise ValueError("calibration_profile.axis_baselines must be a mapping")
        confidence_score = self._bounded_score(
            axis_baselines.get("interoceptive_confidence"),
            "calibration_profile.axis_baselines.interoceptive_confidence",
        )
        expected_calibration_digest = sha256_text(
            canonical_json(self._calibration_digest_payload(calibration_profile))
        )
        calibration_digest_bound = (
            calibration_profile.get("calibration_digest") == expected_calibration_digest
        )
        required_modalities_bound = sorted(calibration_profile.get("source_modalities_covered", [])) == sorted(
            DEFAULT_SOURCE_MODALITIES
        )
        drift_gate_ref = ""
        drift_gate_digest = ""
        drift_threshold_digest = ""
        drift_gate_status = "not-bound"
        drift_gate_bound = False
        drift_gate_ready = True
        if feature_window_series_drift_gate_receipt is not None:
            self._validate_drift_gate_receipt_for_confidence(
                session,
                calibration_profile,
                feature_window_series_drift_gate_receipt,
            )
            drift_gate_ref = str(feature_window_series_drift_gate_receipt["drift_gate_ref"])
            drift_gate_digest = str(feature_window_series_drift_gate_receipt["drift_gate_digest"])
            drift_threshold_digest = str(
                feature_window_series_drift_gate_receipt["drift_threshold_digest"]
            )
            drift_gate_status = str(feature_window_series_drift_gate_receipt["drift_gate_status"])
            drift_gate_bound = True
            drift_gate_ready = drift_gate_status == "pass"
        common_gate_ready = (
            calibration_profile.get("profile_id") == BDT_CALIBRATION_PROFILE_ID
            and calibration_profile.get("calibration_complete") is True
            and calibration_digest_bound
            and required_modalities_bound
            and drift_gate_ready
            and calibration_profile.get("raw_source_payload_stored") is False
            and calibration_profile.get("raw_latent_payload_stored") is False
            and calibration_profile.get("raw_calibration_payload_stored") is False
            and calibration_profile.get("subjective_equivalence_claimed") is False
            and calibration_profile.get("semantic_thought_content_generated") is False
        )

        target_gate_bindings: List[Dict[str, Any]] = []
        for target_gate, target_ref in sorted(normalized_target_refs.items()):
            minimum_confidence = CONFIDENCE_GATE_TARGET_THRESHOLDS[target_gate]
            threshold_met = confidence_score >= minimum_confidence
            binding = {
                "target_gate": target_gate,
                "target_ref": target_ref,
                "minimum_confidence": minimum_confidence,
                "confidence_score": confidence_score,
                "calibration_ref": calibration_profile["calibration_ref"],
                "calibration_digest": calibration_profile["calibration_digest"],
                "feature_window_series_drift_gate_ref": drift_gate_ref,
                "feature_window_series_drift_gate_digest": drift_gate_digest,
                "feature_window_series_drift_gate_bound": drift_gate_bound,
                "feature_window_series_drift_gate_status": drift_gate_status,
                "status": "pass" if common_gate_ready and threshold_met else "fail",
            }
            target_gate_bindings.append(binding)

        target_gate_set_digest = sha256_text(
            canonical_json({"target_gate_bindings": target_gate_bindings})
        )
        gate_status = (
            "bound"
            if common_gate_ready and all(binding["status"] == "pass" for binding in target_gate_bindings)
            else "blocked"
        )
        receipt = {
            "schema_version": BDT_SCHEMA_VERSION,
            "gate_ref": f"confidence-gate://biodata/{new_id('bdt-confidence-gate')}",
            "created_at": utc_now_iso(),
            "profile_id": BDT_CONFIDENCE_GATE_PROFILE_ID,
            "session_id": session["session_id"],
            "identity_id": session["identity_id"],
            "calibration_ref": calibration_profile["calibration_ref"],
            "calibration_digest": calibration_profile["calibration_digest"],
            "calibration_digest_bound": calibration_digest_bound,
            "source_latent_digest_set_digest": calibration_profile[
                "source_latent_digest_set_digest"
            ],
            "source_modalities_required": list(DEFAULT_SOURCE_MODALITIES),
            "source_modalities_covered": sorted(calibration_profile["source_modalities_covered"]),
            "required_modalities_bound": required_modalities_bound,
            "confidence_score": confidence_score,
            "target_gate_bindings": target_gate_bindings,
            "target_gate_set_digest": target_gate_set_digest,
            "confidence_gate_status": gate_status,
            "feature_window_series_drift_gate_ref": drift_gate_ref,
            "feature_window_series_drift_gate_digest": drift_gate_digest,
            "feature_window_series_drift_threshold_digest": drift_threshold_digest,
            "feature_window_series_drift_gate_status": drift_gate_status,
            "feature_window_series_drift_gate_bound": drift_gate_bound,
            "identity_confirmation_gate_bound": any(
                binding["target_gate"] == "identity-confirmation"
                and binding["status"] == "pass"
                for binding in target_gate_bindings
            ),
            "sensory_loopback_gate_bound": any(
                binding["target_gate"] == "sensory-loopback"
                and binding["status"] == "pass"
                for binding in target_gate_bindings
            ),
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_gate_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        receipt["gate_receipt_digest"] = sha256_text(
            canonical_json(self._confidence_gate_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def validate_calibration_confidence_gate(
        self,
        session: Dict[str, Any],
        calibration_profile: Dict[str, Any],
        gate_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_non_empty_string(session.get("session_id"), "session.session_id", errors)
        self._check_non_empty_string(gate_receipt.get("gate_ref"), "gate_receipt.gate_ref", errors)
        if gate_receipt.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("gate_receipt.schema_version mismatch")
        if gate_receipt.get("profile_id") != BDT_CONFIDENCE_GATE_PROFILE_ID:
            errors.append("gate_receipt.profile_id mismatch")
        if gate_receipt.get("session_id") != session.get("session_id"):
            errors.append("gate_receipt.session_id must match session.session_id")
        if gate_receipt.get("identity_id") != session.get("identity_id"):
            errors.append("gate_receipt.identity_id must match session.identity_id")
        if gate_receipt.get("calibration_ref") != calibration_profile.get("calibration_ref"):
            errors.append("gate_receipt.calibration_ref must match calibration_profile")
        if gate_receipt.get("calibration_digest") != calibration_profile.get("calibration_digest"):
            errors.append("gate_receipt.calibration_digest must match calibration_profile")

        expected_calibration_digest = sha256_text(
            canonical_json(self._calibration_digest_payload(calibration_profile))
        )
        calibration_digest_bound = (
            calibration_profile.get("calibration_digest") == expected_calibration_digest
            and gate_receipt.get("calibration_digest_bound") is True
        )
        if not calibration_digest_bound:
            errors.append("gate_receipt must bind the calibration profile digest")
        required_modalities_bound = (
            gate_receipt.get("source_modalities_required") == list(DEFAULT_SOURCE_MODALITIES)
            and sorted(gate_receipt.get("source_modalities_covered", []))
            == sorted(DEFAULT_SOURCE_MODALITIES)
            and gate_receipt.get("required_modalities_bound") is True
        )
        if not required_modalities_bound:
            errors.append("gate_receipt must bind all required source modalities")
        drift_gate_bound = gate_receipt.get("feature_window_series_drift_gate_bound") is True
        drift_gate_status = str(gate_receipt.get("feature_window_series_drift_gate_status", "not-bound"))
        drift_gate_ready = drift_gate_status == "pass" if drift_gate_bound else True
        if drift_gate_bound:
            self._check_non_empty_string(
                gate_receipt.get("feature_window_series_drift_gate_ref"),
                "gate_receipt.feature_window_series_drift_gate_ref",
                errors,
            )
            self._check_non_empty_string(
                gate_receipt.get("feature_window_series_drift_gate_digest"),
                "gate_receipt.feature_window_series_drift_gate_digest",
                errors,
            )
            self._check_non_empty_string(
                gate_receipt.get("feature_window_series_drift_threshold_digest"),
                "gate_receipt.feature_window_series_drift_threshold_digest",
                errors,
            )
        elif drift_gate_status != "not-bound":
            errors.append("unbound feature-window series drift gate must use not-bound status")

        bindings = gate_receipt.get("target_gate_bindings", [])
        if not isinstance(bindings, list) or not bindings:
            errors.append("gate_receipt.target_gate_bindings must be a non-empty list")
            bindings = []
        valid_bindings = True
        for binding in bindings:
            if not isinstance(binding, dict):
                valid_bindings = False
                continue
            target_gate = binding.get("target_gate")
            minimum_confidence = CONFIDENCE_GATE_TARGET_THRESHOLDS.get(str(target_gate))
            expected_status = (
                "pass"
                if isinstance(minimum_confidence, (int, float))
                and gate_receipt.get("confidence_score", 0) >= minimum_confidence
                and calibration_digest_bound
                and required_modalities_bound
                and drift_gate_ready
                else "fail"
            )
            if (
                target_gate not in CONFIDENCE_GATE_TARGET_THRESHOLDS
                or binding.get("minimum_confidence") != minimum_confidence
                or binding.get("confidence_score") != gate_receipt.get("confidence_score")
                or binding.get("calibration_ref") != calibration_profile.get("calibration_ref")
                or binding.get("calibration_digest") != calibration_profile.get("calibration_digest")
                or binding.get("feature_window_series_drift_gate_ref")
                != gate_receipt.get("feature_window_series_drift_gate_ref")
                or binding.get("feature_window_series_drift_gate_digest")
                != gate_receipt.get("feature_window_series_drift_gate_digest")
                or binding.get("feature_window_series_drift_gate_bound") != drift_gate_bound
                or binding.get("feature_window_series_drift_gate_status") != drift_gate_status
                or binding.get("status") != expected_status
            ):
                valid_bindings = False
        expected_target_gate_set_digest = sha256_text(
            canonical_json({"target_gate_bindings": bindings})
        )
        target_gate_set_digest_bound = (
            gate_receipt.get("target_gate_set_digest") == expected_target_gate_set_digest
        )
        if not target_gate_set_digest_bound:
            errors.append("gate_receipt.target_gate_set_digest mismatch")
        if not valid_bindings:
            errors.append("gate_receipt.target_gate_bindings contain invalid gate bindings")

        expected_gate_status = (
            "bound"
            if valid_bindings
            and calibration_digest_bound
            and required_modalities_bound
            and drift_gate_ready
            and all(binding.get("status") == "pass" for binding in bindings)
            else "blocked"
        )
        if gate_receipt.get("confidence_gate_status") != expected_gate_status:
            errors.append("gate_receipt.confidence_gate_status mismatch")
        expected_gate_digest = sha256_text(
            canonical_json(self._confidence_gate_digest_payload(gate_receipt))
        )
        gate_receipt_digest_bound = gate_receipt.get("gate_receipt_digest") == expected_gate_digest
        if not gate_receipt_digest_bound:
            errors.append("gate_receipt.gate_receipt_digest mismatch")

        identity_confirmation_gate_bound = any(
            binding.get("target_gate") == "identity-confirmation"
            and binding.get("status") == "pass"
            for binding in bindings
        )
        sensory_loopback_gate_bound = any(
            binding.get("target_gate") == "sensory-loopback"
            and binding.get("status") == "pass"
            for binding in bindings
        )
        if gate_receipt.get("identity_confirmation_gate_bound") != identity_confirmation_gate_bound:
            errors.append("gate_receipt.identity_confirmation_gate_bound mismatch")
        if gate_receipt.get("sensory_loopback_gate_bound") != sensory_loopback_gate_bound:
            errors.append("gate_receipt.sensory_loopback_gate_bound mismatch")
        for field_name in (
            "raw_calibration_payload_stored",
            "raw_drift_payload_stored",
            "raw_gate_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if gate_receipt.get(field_name) is not False:
                errors.append(f"gate_receipt.{field_name} must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": gate_receipt.get("profile_id"),
            "confidence_gate_status": gate_receipt.get("confidence_gate_status"),
            "confidence_score": gate_receipt.get("confidence_score"),
            "calibration_profile_bound": calibration_digest_bound,
            "required_modalities_bound": required_modalities_bound,
            "target_gate_set_digest_bound": target_gate_set_digest_bound,
            "gate_receipt_digest_bound": gate_receipt_digest_bound,
            "feature_window_series_drift_gate_bound": drift_gate_bound,
            "feature_window_series_drift_gate_status": drift_gate_status,
            "identity_confirmation_gate_bound": identity_confirmation_gate_bound,
            "sensory_loopback_gate_bound": sensory_loopback_gate_bound,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_gate_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def validate_transmission(
        self,
        session: Dict[str, Any],
        latent_state: Dict[str, Any],
        generated_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_non_empty_string(session.get("session_id"), "session.session_id", errors)
        self._check_non_empty_string(latent_state.get("latent_ref"), "latent_state.latent_ref", errors)
        self._check_non_empty_string(generated_bundle.get("bundle_ref"), "generated_bundle.bundle_ref", errors)
        if session.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("session.schema_version mismatch")
        if latent_state.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("latent_state.schema_version mismatch")
        if generated_bundle.get("schema_version") != BDT_SCHEMA_VERSION:
            errors.append("generated_bundle.schema_version mismatch")
        if latent_state.get("session_id") != session.get("session_id"):
            errors.append("latent_state.session_id must match session.session_id")
        if generated_bundle.get("session_id") != session.get("session_id"):
            errors.append("generated_bundle.session_id must match session.session_id")
        if generated_bundle.get("source_latent_digest") != latent_state.get("latent_digest"):
            errors.append("generated_bundle.source_latent_digest must match latent_state.latent_digest")
        if session.get("raw_source_payload_stored") is not False:
            errors.append("session.raw_source_payload_stored must be false")
        if latent_state.get("raw_source_payload_stored") is not False:
            errors.append("latent_state.raw_source_payload_stored must be false")
        if generated_bundle.get("raw_generated_waveform_stored") is not False:
            errors.append("generated_bundle.raw_generated_waveform_stored must be false")
        if generated_bundle.get("semantic_thought_content_generated") is not False:
            errors.append("generated_bundle.semantic_thought_content_generated must be false")

        literature_count = len(latent_state.get("literature_refs", []))
        conflict_refs = latent_state.get("conflict_refs", [])
        conflict_sink_bound = (
            isinstance(conflict_refs, list)
            and bool(conflict_refs)
            and all(str(ref.get("mind_upload_ref", "")).startswith(BDT_CONFLICT_SINK_URL) for ref in conflict_refs)
        )
        signals = generated_bundle.get("signals", {})
        all_targets_generated = isinstance(signals, dict) and set(generated_bundle.get("target_modalities", [])) == set(signals.keys())
        confidence = latent_state.get("interoceptive_confidence")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": session.get("profile_id"),
            "latent_profile_id": latent_state.get("profile_id"),
            "generator_profile_id": generated_bundle.get("generator_profile_id"),
            "person_bound": session.get("identity_id") == latent_state.get("identity_id") == generated_bundle.get("identity_id"),
            "intermediate_representation": "internal-body-state-latent",
            "literature_backed_intermediate": literature_count >= len(REQUIRED_LITERATURE_REFS),
            "literature_ref_count": literature_count,
            "mind_upload_conflict_sink_bound": conflict_sink_bound,
            "source_feature_digest_bound": bool(latent_state.get("source_feature_digest")),
            "latent_digest_bound": bool(latent_state.get("latent_digest")),
            "generated_bundle_digest_bound": bool(generated_bundle.get("bundle_digest")),
            "target_modalities_generated": all_targets_generated,
            "raw_source_payload_stored": False,
            "raw_generated_waveform_stored": False,
            "semantic_thought_content_generated": False,
            "subjective_equivalence_claimed": False,
            "interoceptive_confidence": confidence,
        }

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"unknown BioDataTransmitter session: {session_id}")
        return session

    def _validate_latent_for_session(self, session: Dict[str, Any], latent_state: Dict[str, Any]) -> None:
        if not isinstance(latent_state, dict):
            raise ValueError("latent_state must be a mapping")
        if latent_state.get("session_id") != session["session_id"]:
            raise ValueError("latent_state session_id does not match session")
        if latent_state.get("identity_id") != session["identity_id"]:
            raise ValueError("latent_state identity_id does not match session")
        if latent_state.get("profile_id") != BDT_LATENT_PROFILE_ID:
            raise ValueError("latent_state profile_id mismatch")
        if "physiological_axes" not in latent_state:
            raise ValueError("latent_state must include physiological_axes")

    def _validate_dataset_adapter_window_for_series(
        self,
        session: Dict[str, Any],
        adapter_receipt: Dict[str, Any],
        latent_state: Dict[str, Any],
    ) -> None:
        if not isinstance(adapter_receipt, dict):
            raise ValueError("adapter_receipt must be a mapping")
        self._validate_latent_for_session(session, latent_state)
        if adapter_receipt.get("schema_version") != BDT_SCHEMA_VERSION:
            raise ValueError("adapter_receipt.schema_version mismatch")
        if adapter_receipt.get("profile_id") != BDT_DATASET_ADAPTER_PROFILE_ID:
            raise ValueError("adapter_receipt.profile_id mismatch")
        if adapter_receipt.get("session_id") != session["session_id"]:
            raise ValueError("adapter_receipt.session_id must match session.session_id")
        if adapter_receipt.get("identity_id") != session["identity_id"]:
            raise ValueError("adapter_receipt.identity_id must match session.identity_id")
        if adapter_receipt.get("latent_ref") != latent_state.get("latent_ref"):
            raise ValueError("adapter_receipt.latent_ref must match latent_state.latent_ref")
        if adapter_receipt.get("latent_digest") != latent_state.get("latent_digest"):
            raise ValueError("adapter_receipt.latent_digest must match latent_state.latent_digest")
        if adapter_receipt.get("source_feature_digest") != latent_state.get("source_feature_digest"):
            raise ValueError("adapter_receipt.source_feature_digest must match latent_state.source_feature_digest")
        expected_adapter_digest = sha256_text(
            canonical_json(self._dataset_adapter_digest_payload(adapter_receipt))
        )
        if adapter_receipt.get("adapter_receipt_digest") != expected_adapter_digest:
            raise ValueError("adapter_receipt.adapter_receipt_digest mismatch")
        if adapter_receipt.get("required_modalities_bound") is not True:
            raise ValueError("adapter_receipt.required_modalities_bound must be true")
        for field_name in (
            "raw_dataset_payload_stored",
            "raw_signal_samples_stored",
            "raw_feature_window_payload_stored",
            "raw_source_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if adapter_receipt.get(field_name) is not False:
                raise ValueError(f"adapter_receipt.{field_name} must be false")

    def _validate_series_and_calibration_for_drift_gate(
        self,
        session: Dict[str, Any],
        series_profile: Dict[str, Any],
        calibration_profile: Dict[str, Any],
    ) -> None:
        if not isinstance(series_profile, dict):
            raise ValueError("series_profile must be a mapping")
        if not isinstance(calibration_profile, dict):
            raise ValueError("calibration_profile must be a mapping")
        if series_profile.get("schema_version") != BDT_SCHEMA_VERSION:
            raise ValueError("series_profile.schema_version mismatch")
        if series_profile.get("profile_id") != BDT_FEATURE_WINDOW_SERIES_PROFILE_ID:
            raise ValueError("series_profile.profile_id mismatch")
        if series_profile.get("session_id") != session["session_id"]:
            raise ValueError("series_profile.session_id must match session.session_id")
        if series_profile.get("identity_id") != session["identity_id"]:
            raise ValueError("series_profile.identity_id must match session.identity_id")
        expected_series_digest = sha256_text(
            canonical_json(self._feature_window_series_digest_payload(series_profile))
        )
        if series_profile.get("series_profile_digest") != expected_series_digest:
            raise ValueError("series_profile.series_profile_digest mismatch")
        if calibration_profile.get("schema_version") != BDT_SCHEMA_VERSION:
            raise ValueError("calibration_profile.schema_version mismatch")
        if calibration_profile.get("profile_id") != BDT_CALIBRATION_PROFILE_ID:
            raise ValueError("calibration_profile.profile_id mismatch")
        if calibration_profile.get("session_id") != session["session_id"]:
            raise ValueError("calibration_profile.session_id must match session.session_id")
        if calibration_profile.get("identity_id") != session["identity_id"]:
            raise ValueError("calibration_profile.identity_id must match session.identity_id")
        expected_calibration_digest = sha256_text(
            canonical_json(self._calibration_digest_payload(calibration_profile))
        )
        if calibration_profile.get("calibration_digest") != expected_calibration_digest:
            raise ValueError("calibration_profile.calibration_digest mismatch")
        if series_profile.get("latent_digests") != calibration_profile.get("source_latent_digests"):
            raise ValueError("series_profile latent digests must match calibration source latents")
        if series_profile.get("required_modalities_bound") is not True:
            raise ValueError("series_profile.required_modalities_bound must be true")
        if calibration_profile.get("calibration_complete") is not True:
            raise ValueError("calibration_profile.calibration_complete must be true")
        for field_name in (
            "raw_dataset_payload_stored",
            "raw_signal_samples_stored",
            "raw_feature_window_payload_stored",
            "raw_latent_payload_stored",
            "raw_series_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if series_profile.get(field_name) is not False:
                raise ValueError(f"series_profile.{field_name} must be false")
        for field_name in (
            "raw_source_payload_stored",
            "raw_latent_payload_stored",
            "raw_calibration_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if calibration_profile.get(field_name) is not False:
                raise ValueError(f"calibration_profile.{field_name} must be false")

    def _validate_drift_gate_receipt_for_confidence(
        self,
        session: Dict[str, Any],
        calibration_profile: Dict[str, Any],
        drift_gate_receipt: Dict[str, Any],
    ) -> None:
        if not isinstance(drift_gate_receipt, dict):
            raise ValueError("feature_window_series_drift_gate_receipt must be a mapping")
        if drift_gate_receipt.get("schema_version") != BDT_SCHEMA_VERSION:
            raise ValueError("drift_gate_receipt.schema_version mismatch")
        if drift_gate_receipt.get("profile_id") != BDT_FEATURE_WINDOW_SERIES_DRIFT_GATE_PROFILE_ID:
            raise ValueError("drift_gate_receipt.profile_id mismatch")
        if drift_gate_receipt.get("session_id") != session["session_id"]:
            raise ValueError("drift_gate_receipt.session_id must match session.session_id")
        if drift_gate_receipt.get("identity_id") != session["identity_id"]:
            raise ValueError("drift_gate_receipt.identity_id must match session.identity_id")
        if drift_gate_receipt.get("calibration_ref") != calibration_profile.get("calibration_ref"):
            raise ValueError("drift_gate_receipt.calibration_ref must match calibration_profile")
        if drift_gate_receipt.get("calibration_digest") != calibration_profile.get("calibration_digest"):
            raise ValueError("drift_gate_receipt.calibration_digest must match calibration_profile")
        if drift_gate_receipt.get("drift_gate_status") != "pass":
            raise ValueError("drift_gate_receipt.drift_gate_status must be pass")
        expected_gate_digest = sha256_text(
            canonical_json(self._series_drift_gate_digest_payload(drift_gate_receipt))
        )
        if drift_gate_receipt.get("drift_gate_digest") != expected_gate_digest:
            raise ValueError("drift_gate_receipt.drift_gate_digest mismatch")
        for field_name in (
            "raw_series_payload_stored",
            "raw_calibration_payload_stored",
            "raw_drift_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if drift_gate_receipt.get(field_name) is not False:
                raise ValueError(f"drift_gate_receipt.{field_name} must be false")

    def _normalize_modalities(self, values: Sequence[str] | None, field_name: str) -> List[str]:
        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError(f"{field_name} must be a non-empty sequence")
        normalized: List[str] = []
        seen = set()
        for value in values:
            self._require_non_empty_string(value, field_name)
            text = str(value).strip().lower()
            if text not in SUPPORTED_MODALITIES:
                raise ValueError(f"unsupported modality for {field_name}: {text}")
            if text not in seen:
                normalized.append(text)
                seen.add(text)
        return normalized

    def _normalize_biosignal_features(
        self,
        biosignal_features: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        if not isinstance(biosignal_features, dict) or not biosignal_features:
            raise ValueError("biosignal_features must be a non-empty mapping")
        normalized: Dict[str, Dict[str, Any]] = {}
        for modality, features in biosignal_features.items():
            modality_key = str(modality).strip().lower()
            if modality_key not in SUPPORTED_MODALITIES:
                raise ValueError(f"unsupported biosignal modality: {modality_key}")
            if not isinstance(features, dict) or not features:
                raise ValueError(f"features for {modality_key} must be a non-empty mapping")
            normalized_features: Dict[str, Any] = {}
            for feature_name, value in features.items():
                self._require_non_empty_string(str(feature_name), "feature_name")
                if isinstance(value, (int, float)):
                    normalized_features[str(feature_name)] = round(float(value), 6)
                elif isinstance(value, str):
                    self._require_non_empty_string(value, str(feature_name))
                    normalized_features[str(feature_name)] = value
                else:
                    raise ValueError(f"unsupported feature value for {modality_key}.{feature_name}")
            normalized[modality_key] = normalized_features
        return normalized

    def _normalize_dataset_manifest(self, dataset_manifest: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(dataset_manifest, dict):
            raise ValueError("dataset_manifest must be a mapping")
        normalized: Dict[str, Any] = {}
        for field_name in ("dataset_ref", "participant_ref", "license_ref", "window_ref"):
            value = dataset_manifest.get(field_name)
            self._require_non_empty_string(value, f"dataset_manifest.{field_name}")
            normalized[field_name] = str(value).strip()
        modality_file_refs = dataset_manifest.get("modality_file_refs")
        if not isinstance(modality_file_refs, dict) or not modality_file_refs:
            raise ValueError("dataset_manifest.modality_file_refs must be a non-empty mapping")
        normalized_refs: Dict[str, str] = {}
        for modality, file_ref in modality_file_refs.items():
            modality_key = str(modality).strip().lower()
            if modality_key not in DEFAULT_SOURCE_MODALITIES:
                raise ValueError(f"unsupported dataset modality: {modality_key}")
            self._require_non_empty_string(file_ref, f"dataset_manifest.modality_file_refs.{modality_key}")
            normalized_refs[modality_key] = str(file_ref).strip()
        normalized["modality_file_refs"] = normalized_refs
        return normalized

    def _normalize_circadian_phase_refs(
        self,
        circadian_phase_refs: Sequence[str],
    ) -> List[str]:
        if not isinstance(circadian_phase_refs, (list, tuple)) or len(circadian_phase_refs) < 2:
            raise ValueError("circadian_phase_refs must contain at least two phase refs")
        normalized: List[str] = []
        for phase_ref in circadian_phase_refs:
            self._require_non_empty_string(phase_ref, "circadian_phase_ref")
            normalized.append(str(phase_ref).strip())
        if len(set(normalized)) < 2:
            raise ValueError("circadian_phase_refs must cover at least two unique phases")
        return normalized

    def _normalize_circadian_verifier_sources(
        self,
        verifier_sources: Sequence[Dict[str, Any]],
        circadian_phase_refs: Sequence[str],
    ) -> List[Dict[str, Any]]:
        if not isinstance(verifier_sources, (list, tuple)):
            raise ValueError("verifier_sources must be a sequence")
        sources_by_type: Dict[str, Dict[str, Any]] = {}
        phase_refs = [str(item).strip() for item in circadian_phase_refs]
        for source in verifier_sources:
            if not isinstance(source, dict):
                raise ValueError("each verifier source must be a mapping")
            source_type = str(source.get("source_type", "")).strip().lower()
            if source_type not in CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES:
                raise ValueError(f"unsupported circadian verifier source type: {source_type}")
            if source_type in sources_by_type:
                raise ValueError(f"duplicate circadian verifier source type: {source_type}")
            normalized_source: Dict[str, Any] = {"source_type": source_type}
            for field_name in ("source_ref", "evidence_ref", "verifier_key_ref"):
                value = source.get(field_name)
                self._require_non_empty_string(value, f"verifier_sources.{source_type}.{field_name}")
                normalized_source[field_name] = str(value).strip()
            source_digest_payload = {
                "profile_id": BDT_CIRCADIAN_PHASE_VERIFIER_PROFILE_ID,
                "circadian_phase_refs": phase_refs,
                "source_type": normalized_source["source_type"],
                "source_ref": normalized_source["source_ref"],
                "evidence_ref": normalized_source["evidence_ref"],
                "verifier_key_ref": normalized_source["verifier_key_ref"],
            }
            normalized_source["source_digest"] = sha256_text(canonical_json(source_digest_payload))
            sources_by_type[source_type] = normalized_source
        missing_source_types = [
            source_type
            for source_type in CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES
            if source_type not in sources_by_type
        ]
        if missing_source_types:
            raise ValueError(f"missing circadian verifier source types: {missing_source_types}")
        return [
            sources_by_type[source_type]
            for source_type in CIRCADIAN_PHASE_VERIFIER_SOURCE_TYPES
        ]

    @staticmethod
    def _normalize_series_drift_thresholds(
        axis_thresholds: Dict[str, float] | None,
    ) -> Dict[str, float]:
        if axis_thresholds is None:
            return dict(FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS)
        if not isinstance(axis_thresholds, dict):
            raise ValueError("axis_thresholds must be a mapping")
        unknown_axes = sorted(set(axis_thresholds) - set(FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS))
        if unknown_axes:
            raise ValueError(f"unsupported drift threshold axes: {unknown_axes}")
        normalized = dict(FEATURE_WINDOW_SERIES_DRIFT_THRESHOLDS)
        for axis_name, value in axis_thresholds.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"axis_thresholds.{axis_name} must be a positive number")
            threshold = round(float(value), 3)
            if threshold < 0.0:
                raise ValueError(f"axis_thresholds.{axis_name} must be non-negative")
            normalized[str(axis_name)] = threshold
        return normalized

    @staticmethod
    def _coalesce_number(*values: Any, default: float) -> float:
        for value in values:
            if isinstance(value, (int, float)):
                return float(value)
        return default

    @staticmethod
    def _clamp(value: float) -> float:
        return round(min(1.0, max(0.0, float(value))), 3)

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _calibration_digest_payload(calibration_profile: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(calibration_profile)
        payload.pop("calibration_digest", None)
        return payload

    @staticmethod
    def _feature_window_series_digest_payload(series_profile: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(series_profile)
        payload.pop("series_profile_digest", None)
        return payload

    @staticmethod
    def _summarize_axis_drift(values: Sequence[float]) -> Dict[str, Any]:
        first = round(float(values[0]), 3)
        last = round(float(values[-1]), 3)
        absolute_delta = round(last - first, 3)
        if absolute_delta > 0:
            direction = "increased"
        elif absolute_delta < 0:
            direction = "decreased"
        else:
            direction = "stable"
        return {
            "first": first,
            "last": last,
            "minimum": round(min(float(value) for value in values), 3),
            "maximum": round(max(float(value) for value in values), 3),
            "absolute_delta": absolute_delta,
            "direction": direction,
        }

    @staticmethod
    def _confidence_gate_digest_payload(gate_receipt: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(gate_receipt)
        payload.pop("gate_receipt_digest", None)
        return payload

    @staticmethod
    def _series_drift_gate_digest_payload(drift_gate_receipt: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(drift_gate_receipt)
        payload.pop("drift_gate_digest", None)
        return payload

    @staticmethod
    def _circadian_phase_verifier_digest_payload(
        verifier_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = dict(verifier_receipt)
        payload.pop("phase_verifier_digest", None)
        return payload

    @staticmethod
    def _dataset_adapter_digest_payload(adapter_receipt: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(adapter_receipt)
        payload.pop("adapter_receipt_digest", None)
        return payload

    @staticmethod
    def _bounded_score(value: Any, field_name: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{field_name} must be a number between 0.0 and 1.0")
        score = float(value)
        if score < 0.0 or score > 1.0:
            raise ValueError(f"{field_name} must be between 0.0 and 1.0")
        return round(score, 3)

    @staticmethod
    def _check_session_mapping(session: Dict[str, Any]) -> None:
        if not isinstance(session, dict):
            raise ValueError("session must be a mapping")
        if not isinstance(session.get("session_id"), str) or not session["session_id"].strip():
            raise ValueError("session.session_id must be a non-empty string")
        if not isinstance(session.get("identity_id"), str) or not session["identity_id"].strip():
            raise ValueError("session.identity_id must be a non-empty string")

    @staticmethod
    def _check_session_mapping_for_errors(session: Dict[str, Any], errors: List[str]) -> None:
        if not isinstance(session, dict):
            errors.append("session must be a mapping")
            return
        if not isinstance(session.get("session_id"), str) or not session["session_id"].strip():
            errors.append("session.session_id must be a non-empty string")
        if not isinstance(session.get("identity_id"), str) or not session["identity_id"].strip():
            errors.append("session.identity_id must be a non-empty string")

    @staticmethod
    def _normalize_confidence_gate_refs(target_gate_refs: Dict[str, str]) -> Dict[str, str]:
        if not isinstance(target_gate_refs, dict) or not target_gate_refs:
            raise ValueError("target_gate_refs must be a non-empty mapping")
        normalized: Dict[str, str] = {}
        for target_gate, target_ref in target_gate_refs.items():
            gate_key = str(target_gate).strip().lower().replace("_", "-")
            if gate_key not in CONFIDENCE_GATE_TARGET_THRESHOLDS:
                raise ValueError(f"unsupported confidence gate target: {target_gate}")
            if not isinstance(target_ref, str) or not target_ref.strip():
                raise ValueError("target_gate_refs values must be non-empty strings")
            normalized[gate_key] = target_ref.strip()
        if set(normalized) != set(CONFIDENCE_GATE_TARGET_THRESHOLDS):
            raise ValueError("target_gate_refs must include identity-confirmation and sensory-loopback")
        return normalized
