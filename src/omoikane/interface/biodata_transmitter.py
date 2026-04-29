"""BioData Transmitter reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

BDT_SCHEMA_VERSION = "1.0"
BDT_PROFILE_ID = "person-bound-biodata-transmitter-v0"
BDT_LATENT_PROFILE_ID = "physiology-latent-body-state-v0"
BDT_GENERATOR_PROFILE_ID = "bounded-cross-modal-biosignal-generator-v0"
BDT_CONFLICT_SINK_URL = "https://mind-upload.com/frontiers/biosignal-transmitter"
DEFAULT_SOURCE_MODALITIES = ("eeg", "ecg", "ppg", "eda", "respiration")
DEFAULT_TARGET_MODALITIES = ("ecg", "ppg", "respiration", "eeg", "affect", "thought")
SUPPORTED_MODALITIES = set(DEFAULT_SOURCE_MODALITIES + DEFAULT_TARGET_MODALITIES)
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
            "source_modalities": list(DEFAULT_SOURCE_MODALITIES),
            "target_modalities": list(DEFAULT_TARGET_MODALITIES),
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
