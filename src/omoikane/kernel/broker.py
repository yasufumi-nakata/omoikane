"""Deterministic substrate broker for L1 reference runtime coordination."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from ..substrate.adapter import (
    ClassicalSiliconAdapter,
    EnergyFloor,
    SubstrateAllocation,
    SubstrateAttestation,
    SubstrateTransferRecord,
)

BROKER_POLICY_ID = "deterministic-substrate-neutrality-broker-v1"
STANDBY_PROBE_POLICY_ID = "deterministic-standby-health-probe-v1"
ATTESTATION_CHAIN_POLICY_ID = "bounded-cross-substrate-attestation-window-v1"
MINIMUM_HEALTH_SCORE = 0.6
CRITICAL_HEALTH_SCORE = 0.4
NEUTRALITY_WINDOW = 2
ATTESTATION_CHAIN_WINDOW = 3
ATTESTATION_CHAIN_CADENCE_MS = 250


@dataclass(frozen=True)
class BrokerRegistryEntry:
    """Public metadata for one broker-manageable substrate."""

    substrate_id: str
    substrate_kind: str
    capability_score: float
    health_score: float
    attestation_valid: bool
    energy_capacity_jps: int
    method_priorities: Dict[str, float]
    standby_class: str

    def to_candidate(self, neutrality_index: int) -> Dict[str, Any]:
        return {
            "substrate_id": self.substrate_id,
            "substrate_kind": self.substrate_kind,
            "capability_score": round(self.capability_score, 3),
            "health_score": round(self.health_score, 3),
            "attestation_valid": self.attestation_valid,
            "energy_capacity_jps": self.energy_capacity_jps,
            "method_priorities": dict(self.method_priorities),
            "standby_class": self.standby_class,
            "substrate_kind_neutrality_index": neutrality_index,
        }


@dataclass(frozen=True)
class StandbyHealthProbe:
    """Bounded readiness probe for the pre-bound standby candidate."""

    probe_id: str
    identity_id: str
    active_substrate_id: str
    standby_substrate_id: str
    standby_class: str
    workload_class: str
    health_score: float
    attestation_valid: bool
    observed_capacity_jps: int
    required_energy_floor_jps: int
    energy_headroom_jps: int
    probe_status: str
    ready_for_migrate: bool
    observed_at: str
    kind: str = "standby_health_probe"
    schema_version: str = "1.0.0"


@dataclass(frozen=True)
class SubstrateAttestationChain:
    """Deterministic attestation bridge between active and standby substrates."""

    chain_id: str
    identity_id: str
    allocation_id: str
    active_substrate_id: str
    standby_substrate_id: str
    source_attestation_id: str
    standby_probe_id: str
    continuity_mode: str
    policy_id: str
    window_size: int
    cadence_ms: int
    expected_state_digest: str
    expected_destination_substrate: str
    chain_status: str
    handoff_ready: bool
    observations: List[Dict[str, Any]]
    blocking_reasons: List[str]
    chain_digest: str
    opened_at: str
    kind: str = "substrate_attestation_chain"
    schema_version: str = "1.0.0"


class SubstrateBrokerService:
    """Select, lease, and migrate substrates while preserving neutrality rotation."""

    def __init__(
        self,
        *,
        adapters: Mapping[str, ClassicalSiliconAdapter],
        registry: Sequence[BrokerRegistryEntry],
    ) -> None:
        self._adapters = dict(adapters)
        self._registry = {entry.substrate_id: entry for entry in registry}
        if set(self._registry) != set(self._adapters):
            raise ValueError("registry and adapters must cover the same substrate ids")
        self._leases: Dict[str, Dict[str, Any]] = {}
        self._selection_history: List[str] = []

    @classmethod
    def reference_service(
        cls,
        primary_adapter: Optional[ClassicalSiliconAdapter] = None,
    ) -> "SubstrateBrokerService":
        primary = primary_adapter or ClassicalSiliconAdapter("classical_silicon")
        neuromorphic = ClassicalSiliconAdapter("neuromorphic_mesh.alpha")
        photonic = ClassicalSiliconAdapter("photonic_array.standby")
        adapters = {
            primary.substrate_id: primary,
            neuromorphic.substrate_id: neuromorphic,
            photonic.substrate_id: photonic,
        }
        registry = [
            BrokerRegistryEntry(
                substrate_id=primary.substrate_id,
                substrate_kind="classical-silicon",
                capability_score=0.96,
                health_score=0.94,
                attestation_valid=True,
                energy_capacity_jps=64,
                method_priorities={"A": 0.96, "B": 0.91, "C": 0.72},
                standby_class="hot-standby",
            ),
            BrokerRegistryEntry(
                substrate_id=neuromorphic.substrate_id,
                substrate_kind="neuromorphic",
                capability_score=0.96,
                health_score=0.94,
                attestation_valid=True,
                energy_capacity_jps=64,
                method_priorities={"A": 0.96, "B": 0.91, "C": 0.72},
                standby_class="hot-standby",
            ),
            BrokerRegistryEntry(
                substrate_id=photonic.substrate_id,
                substrate_kind="photonic",
                capability_score=0.88,
                health_score=0.81,
                attestation_valid=True,
                energy_capacity_jps=48,
                method_priorities={"A": 0.82, "B": 0.86, "C": 0.77},
                standby_class="cold-standby",
            ),
        ]
        return cls(adapters=adapters, registry=registry)

    def profile(self) -> Dict[str, Any]:
        return {
            "policy_id": BROKER_POLICY_ID,
            "minimum_health_score": MINIMUM_HEALTH_SCORE,
            "critical_health_score": CRITICAL_HEALTH_SCORE,
            "neutrality_window": NEUTRALITY_WINDOW,
            "rotation_tie_breaker": "substrate_kind_neutrality_index",
            "required_steps": [
                "lease",
                "probe-standby",
                "attest",
                "bridge-attestation-chain",
                "migrate",
                "release",
            ],
            "energy_floor_failover_action": "migrate-standby",
            "standby_probe_policy": {
                "policy_id": STANDBY_PROBE_POLICY_ID,
                "minimum_ready_health_score": MINIMUM_HEALTH_SCORE,
                "required_attestation_valid": True,
            },
            "attestation_chain_policy": {
                "policy_id": ATTESTATION_CHAIN_POLICY_ID,
                "window_size": ATTESTATION_CHAIN_WINDOW,
                "cadence_ms": ATTESTATION_CHAIN_CADENCE_MS,
                "required_source_status": "healthy",
            },
        }

    def registry_snapshot(self) -> List[Dict[str, Any]]:
        return [
            self._registry[substrate_id].to_candidate(
                self._neutrality_index(self._registry[substrate_id].substrate_kind)
            )
            for substrate_id in sorted(self._registry)
        ]

    def select(
        self,
        *,
        identity_id: str,
        method: str,
        required_capability: float,
        workload_class: str,
    ) -> Dict[str, Any]:
        if not isinstance(identity_id, str) or not identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")
        required_floor = ClassicalSiliconAdapter.minimum_energy_floor_for(workload_class)
        candidates: List[Dict[str, Any]] = []
        for entry in self._registry.values():
            method_priority = float(entry.method_priorities.get(method, 0.0))
            if entry.capability_score < float(required_capability):
                continue
            if entry.health_score < MINIMUM_HEALTH_SCORE:
                continue
            if not entry.attestation_valid:
                continue
            if entry.energy_capacity_jps < required_floor:
                continue
            neutrality_index = self._neutrality_index(entry.substrate_kind)
            candidates.append(
                {
                    **entry.to_candidate(neutrality_index),
                    "method_priority": round(method_priority, 3),
                }
            )
        if not candidates:
            raise ValueError("no-candidate")

        ranked = sorted(
            candidates,
            key=lambda item: (
                -float(item["method_priority"]),
                -float(item["health_score"]),
                int(item["substrate_kind_neutrality_index"]),
                str(item["substrate_id"]),
            ),
        )
        active = ranked[0]
        standby = self._select_standby(active, ranked[1:])
        last_kind = self._selection_history[-1] if self._selection_history else None
        return {
            "selection_id": new_id("broker-selection"),
            "identity_id": identity_id,
            "method": method,
            "required_capability": round(float(required_capability), 3),
            "required_energy_floor_jps": required_floor,
            "active_substrate": dict(active),
            "standby_substrate": dict(standby) if standby else None,
            "ranked_candidates": [dict(candidate) for candidate in ranked],
            "neutrality_rotation_applied": bool(
                last_kind
                and active["substrate_kind"] != last_kind
                and any(candidate["substrate_kind"] == last_kind for candidate in ranked)
            ),
            "selected_at": utc_now_iso(),
        }

    def lease(
        self,
        *,
        identity_id: str,
        units: int,
        purpose: str,
        method: str,
        required_capability: float,
        workload_class: str,
    ) -> SubstrateAllocation:
        existing = self._leases.get(identity_id)
        if existing and existing["release"] is None:
            raise PermissionError("same identity may not hold 2 active leases")
        selection = self.select(
            identity_id=identity_id,
            method=method,
            required_capability=required_capability,
            workload_class=workload_class,
        )
        active_substrate_id = str(selection["active_substrate"]["substrate_id"])
        adapter = self._adapters[active_substrate_id]
        allocation = adapter.allocate(units=units, purpose=purpose, identity_id=identity_id)
        energy_floor = adapter.energy_floor(identity_id, workload_class=workload_class)
        self._selection_history.append(str(selection["active_substrate"]["substrate_kind"]))
        self._leases[identity_id] = {
            "selection": deepcopy(selection),
            "allocation": allocation,
            "energy_floor": energy_floor,
            "active_substrate_id": active_substrate_id,
            "standby_substrate_id": (
                str(selection["standby_substrate"]["substrate_id"])
                if selection["standby_substrate"] is not None
                else None
            ),
            "method": method,
            "workload_class": workload_class,
            "last_attestation": None,
            "last_standby_probe": None,
            "last_attestation_chain": None,
            "transfer": None,
            "release": None,
        }
        return allocation

    def attest(
        self,
        identity_id: str,
        integrity: Mapping[str, Any],
    ) -> SubstrateAttestation:
        lease = self._require_open_lease(identity_id)
        attestation = self._adapters[lease["active_substrate_id"]].attest(
            lease["allocation"].allocation_id,
            dict(integrity),
        )
        lease["last_attestation"] = attestation
        return attestation

    def probe_standby(
        self,
        identity_id: str,
        *,
        workload_class: Optional[str] = None,
    ) -> StandbyHealthProbe:
        lease = self._require_open_lease(identity_id)
        standby_substrate_id = lease["standby_substrate_id"]
        if not isinstance(standby_substrate_id, str) or not standby_substrate_id.strip():
            raise ValueError("standby probe requires a pre-bound standby candidate")
        workload = workload_class or str(lease["workload_class"])
        required_floor = ClassicalSiliconAdapter.minimum_energy_floor_for(workload)
        standby_entry = self._registry[standby_substrate_id]
        energy_headroom = int(standby_entry.energy_capacity_jps) - int(required_floor)
        ready_for_migrate = bool(
            standby_entry.health_score >= MINIMUM_HEALTH_SCORE
            and standby_entry.attestation_valid
            and energy_headroom >= 0
        )
        probe = StandbyHealthProbe(
            probe_id=new_id("standby-probe"),
            identity_id=identity_id,
            active_substrate_id=str(lease["active_substrate_id"]),
            standby_substrate_id=standby_substrate_id,
            standby_class=standby_entry.standby_class,
            workload_class=workload,
            health_score=round(float(standby_entry.health_score), 3),
            attestation_valid=bool(standby_entry.attestation_valid),
            observed_capacity_jps=int(standby_entry.energy_capacity_jps),
            required_energy_floor_jps=int(required_floor),
            energy_headroom_jps=int(energy_headroom),
            probe_status="ready" if ready_for_migrate else "blocked",
            ready_for_migrate=ready_for_migrate,
            observed_at=utc_now_iso(),
        )
        lease["last_standby_probe"] = probe
        return probe

    def bridge_attestation_chain(
        self,
        identity_id: str,
        *,
        state: Mapping[str, Any],
        continuity_mode: str = "warm-standby",
    ) -> SubstrateAttestationChain:
        lease = self._require_open_lease(identity_id)
        if not state:
            raise ValueError("state must not be empty")
        attestation = lease["last_attestation"]
        if attestation is None or attestation.status != "healthy":
            raise PermissionError("healthy attestation required before bridging attestation chain")
        probe = lease["last_standby_probe"]
        if probe is None:
            probe = self.probe_standby(identity_id)

        blocking_reasons: List[str] = []
        if not probe.ready_for_migrate:
            blocking_reasons.append("standby probe must be ready before attestation chain bridging")
        if continuity_mode == "warm-standby" and probe.standby_class == "cold-standby":
            blocking_reasons.append("warm-standby continuity requires a hot-standby candidate")

        expected_state_digest = sha256_text(canonical_json(dict(state)))
        observations: List[Dict[str, Any]] = []
        for sequence in range(1, ATTESTATION_CHAIN_WINDOW + 1):
            observations.append(
                {
                    "sequence": sequence,
                    "source_substrate_id": str(lease["active_substrate_id"]),
                    "standby_substrate_id": probe.standby_substrate_id,
                    "source_attestation_id": attestation.attestation_id,
                    "source_status": attestation.status,
                    "standby_probe_id": probe.probe_id,
                    "standby_status": probe.probe_status,
                    "energy_headroom_jps": probe.energy_headroom_jps,
                    "expected_destination_substrate": probe.standby_substrate_id,
                    "expected_state_digest": expected_state_digest,
                    "observed_at": utc_now_iso(),
                }
            )

        handoff_ready = not blocking_reasons
        chain_status = "handoff-ready" if handoff_ready else "blocked"
        chain_payload = {
            "identity_id": identity_id,
            "allocation_id": lease["allocation"].allocation_id,
            "active_substrate_id": lease["active_substrate_id"],
            "standby_substrate_id": probe.standby_substrate_id,
            "source_attestation_id": attestation.attestation_id,
            "standby_probe_id": probe.probe_id,
            "continuity_mode": continuity_mode,
            "policy_id": ATTESTATION_CHAIN_POLICY_ID,
            "window_size": ATTESTATION_CHAIN_WINDOW,
            "cadence_ms": ATTESTATION_CHAIN_CADENCE_MS,
            "expected_state_digest": expected_state_digest,
            "expected_destination_substrate": probe.standby_substrate_id,
            "chain_status": chain_status,
            "handoff_ready": handoff_ready,
            "observations": observations,
            "blocking_reasons": list(blocking_reasons),
        }
        chain = SubstrateAttestationChain(
            chain_id=new_id("attestation-chain"),
            identity_id=identity_id,
            allocation_id=lease["allocation"].allocation_id,
            active_substrate_id=str(lease["active_substrate_id"]),
            standby_substrate_id=probe.standby_substrate_id,
            source_attestation_id=attestation.attestation_id,
            standby_probe_id=probe.probe_id,
            continuity_mode=continuity_mode,
            policy_id=ATTESTATION_CHAIN_POLICY_ID,
            window_size=ATTESTATION_CHAIN_WINDOW,
            cadence_ms=ATTESTATION_CHAIN_CADENCE_MS,
            expected_state_digest=expected_state_digest,
            expected_destination_substrate=probe.standby_substrate_id,
            chain_status=chain_status,
            handoff_ready=handoff_ready,
            observations=observations,
            blocking_reasons=list(blocking_reasons),
            chain_digest=sha256_text(canonical_json(chain_payload)),
            opened_at=utc_now_iso(),
        )
        lease["last_attestation_chain"] = chain
        return chain

    def migrate(
        self,
        identity_id: str,
        *,
        state: Mapping[str, Any],
        destination_substrate: Optional[str] = None,
        continuity_mode: str = "warm-standby",
    ) -> SubstrateTransferRecord:
        lease = self._require_open_lease(identity_id)
        attestation = lease["last_attestation"]
        if attestation is None or attestation.status != "healthy":
            raise PermissionError("healthy attestation required before migrate")
        target_substrate = destination_substrate or lease["standby_substrate_id"]
        if not isinstance(target_substrate, str) or not target_substrate.strip():
            raise ValueError("destination_substrate must resolve to a non-empty standby target")
        transfer = self._adapters[lease["active_substrate_id"]].transfer(
            lease["allocation"].allocation_id,
            dict(state),
            destination_substrate=target_substrate,
            continuity_mode=continuity_mode,
        )
        lease["transfer"] = transfer
        return transfer

    def release(self, identity_id: str, reason: str) -> Dict[str, Any]:
        lease = self._require_open_lease(identity_id)
        release = self._adapters[lease["active_substrate_id"]].release(
            lease["allocation"].allocation_id,
            reason=reason,
        )
        lease["release"] = dict(release)
        return dict(release)

    def handle_energy_floor_signal(
        self,
        identity_id: str,
        *,
        current_joules_per_second: int,
    ) -> Dict[str, Any]:
        lease = self._require_open_lease(identity_id)
        minimum = int(lease["energy_floor"].minimum_joules_per_second)
        shortfall = minimum - int(current_joules_per_second)
        severity = "watch"
        status = "within-floor"
        if shortfall > 0:
            severity = "critical"
            status = "standby-required"
        elif int(current_joules_per_second) <= minimum + 2:
            severity = "degraded"
            status = "standby-advised"
        return {
            "signal_id": new_id("broker-signal"),
            "identity_id": identity_id,
            "source_substrate": lease["active_substrate_id"],
            "standby_substrate": lease["standby_substrate_id"],
            "severity": severity,
            "reason": "energy-floor-violated" if shortfall > 0 else "energy-floor-margin-thin",
            "status": status,
            "current_joules_per_second": int(current_joules_per_second),
            "minimum_joules_per_second": minimum,
            "recommended_action": "migrate-standby" if shortfall > 0 else "pause-and-review",
            "scheduler_input": {
                "severity": severity,
                "source_substrate": lease["active_substrate_id"],
                "reason": "energy floor below minimum" if shortfall > 0 else "energy floor near minimum",
            },
            "recorded_at": utc_now_iso(),
        }

    def observe(self, identity_id: str) -> Dict[str, Any]:
        lease = self._leases.get(identity_id)
        if lease is None:
            raise ValueError("unknown broker identity")
        return {
            "identity_id": identity_id,
            "policy": self.profile(),
            "selection": deepcopy(lease["selection"]),
            "allocation": asdict(lease["allocation"]),
            "energy_floor": asdict(lease["energy_floor"]),
            "active_substrate_id": lease["active_substrate_id"],
            "standby_substrate_id": lease["standby_substrate_id"],
            "last_attestation": (
                asdict(lease["last_attestation"]) if lease["last_attestation"] is not None else None
            ),
            "last_standby_probe": (
                asdict(lease["last_standby_probe"])
                if lease["last_standby_probe"] is not None
                else None
            ),
            "last_attestation_chain": (
                asdict(lease["last_attestation_chain"])
                if lease["last_attestation_chain"] is not None
                else None
            ),
            "transfer": asdict(lease["transfer"]) if lease["transfer"] is not None else None,
            "release": deepcopy(lease["release"]),
            "selection_history": list(self._selection_history),
        }

    def snapshot(self) -> Dict[str, Any]:
        active_leases: List[Dict[str, Any]] = []
        for identity_id in sorted(self._leases):
            active_leases.append(self.observe(identity_id))
        return {
            "policy": self.profile(),
            "registry": self.registry_snapshot(),
            "active_leases": active_leases,
        }

    def _neutrality_index(self, substrate_kind: str) -> int:
        recent = self._selection_history[-NEUTRALITY_WINDOW:]
        return sum(1 for kind in recent if kind == substrate_kind)

    @staticmethod
    def _select_standby(
        active: Mapping[str, Any],
        remaining: Sequence[Mapping[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not remaining:
            return None
        for candidate in remaining:
            if candidate["substrate_kind"] != active["substrate_kind"]:
                return dict(candidate)
        return dict(remaining[0])

    def _require_open_lease(self, identity_id: str) -> Dict[str, Any]:
        lease = self._leases.get(identity_id)
        if lease is None:
            raise ValueError("unknown broker identity")
        if lease["release"] is not None:
            raise ValueError("lease already released")
        return lease


def reference_broker_components(
    primary_adapter: Optional[ClassicalSiliconAdapter] = None,
) -> Tuple[Dict[str, ClassicalSiliconAdapter], List[BrokerRegistryEntry]]:
    """Expose the reference registry for tests and runtime bootstrap."""

    service = SubstrateBrokerService.reference_service(primary_adapter)
    return dict(service._adapters), list(service._registry.values())
