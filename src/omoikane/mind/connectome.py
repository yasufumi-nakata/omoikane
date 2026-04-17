"""Substrate-neutral connectome reference model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from ..common import utc_now_iso


CONNECTOME_SCHEMA_VERSION = "1.0"
POSITION_FRAMES = {"anatomical", "abstract"}
NODE_KINDS = {"neuron", "circuit", "module"}
NODE_TYPES = {"excitatory", "inhibitory", "modulatory"}


def _uuid_text() -> str:
    return str(uuid4())


def _ensure_uuid(value: str, field_name: str) -> None:
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UUID") from exc


@dataclass
class ConnectomePosition:
    x: float
    y: float
    z: float
    frame: str


@dataclass
class PlasticitySpec:
    rule: str
    params: Dict[str, float]
    enabled: bool = True


@dataclass
class ConnectomeNode:
    id: str
    kind: str
    type: str
    position: ConnectomePosition
    properties: Dict[str, Any]
    substrate_hint: Optional[str] = None


@dataclass
class ConnectomeEdge:
    id: str
    source: str
    target: str
    weight: float
    delay_ms: float
    plasticity: PlasticitySpec


@dataclass
class ConnectomeHierarchy:
    id: str
    kind: str
    members: List[str]
    description: Optional[str] = None


@dataclass
class ConnectomeInvariant:
    invariant_id: str
    expression: str
    scope: str


@dataclass
class ConnectomeDocument:
    identity_id: str
    nodes: List[ConnectomeNode]
    edges: List[ConnectomeEdge]
    hierarchies: List[ConnectomeHierarchy]
    invariants: List[ConnectomeInvariant]
    schema_version: str = CONNECTOME_SCHEMA_VERSION
    snapshot_id: str = field(default_factory=_uuid_text)
    snapshot_time: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConnectomeModel:
    """Builds and validates minimal connectome snapshots."""

    def build_reference_snapshot(self, identity_id: Optional[str] = None) -> Dict[str, Any]:
        snapshot_identity = identity_id or f"identity-{uuid4().hex[:12]}"
        sensory_node = ConnectomeNode(
            id=_uuid_text(),
            kind="circuit",
            type="excitatory",
            position=ConnectomePosition(x=0.0, y=1.0, z=0.0, frame="abstract"),
            properties={
                "label": "sensory_ingress",
                "role": "captures external state transitions",
            },
            substrate_hint="classical_silicon",
        )
        integration_node = ConnectomeNode(
            id=_uuid_text(),
            kind="neuron",
            type="modulatory",
            position=ConnectomePosition(x=1.0, y=1.5, z=0.2, frame="abstract"),
            properties={
                "label": "continuity_integrator",
                "role": "binds current state with ledger-backed identity constraints",
            },
        )
        ethics_node = ConnectomeNode(
            id=_uuid_text(),
            kind="module",
            type="inhibitory",
            position=ConnectomePosition(x=2.0, y=1.2, z=0.4, frame="abstract"),
            properties={
                "label": "ethics_gate",
                "role": "suppresses unsafe self-modification paths",
            },
        )

        document = ConnectomeDocument(
            identity_id=snapshot_identity,
            nodes=[sensory_node, integration_node, ethics_node],
            edges=[
                ConnectomeEdge(
                    id=_uuid_text(),
                    source=sensory_node.id,
                    target=integration_node.id,
                    weight=0.82,
                    delay_ms=1.5,
                    plasticity=PlasticitySpec(
                        rule="hebbian-windowed",
                        params={"learning_rate": 0.03, "window_ms": 25.0},
                    ),
                ),
                ConnectomeEdge(
                    id=_uuid_text(),
                    source=integration_node.id,
                    target=ethics_node.id,
                    weight=0.94,
                    delay_ms=0.8,
                    plasticity=PlasticitySpec(
                        rule="homeostatic-clamp",
                        params={"target_activity": 0.55, "gain": 0.2},
                    ),
                ),
            ],
            hierarchies=[
                ConnectomeHierarchy(
                    id=_uuid_text(),
                    kind="reference_control_loop",
                    members=[sensory_node.id, integration_node.id, ethics_node.id],
                    description="Minimal loop for observation, continuity integration, and safety gating.",
                )
            ],
            invariants=[
                ConnectomeInvariant(
                    invariant_id="ledger_diff_required",
                    expression="Every structural mutation must emit a continuity diff entry.",
                    scope="document",
                ),
                ConnectomeInvariant(
                    invariant_id="ethics_gate_in_path",
                    expression="Unsafe self-modification routes must traverse an inhibitory ethics gate.",
                    scope="reference_control_loop",
                ),
            ],
        )
        return document.to_dict()

    def validate(self, document: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(document, dict):
            raise ValueError("document must be a mapping")
        self._require_non_empty_string(document.get("identity_id"), "identity_id")
        self._require_non_empty_string(document.get("snapshot_id"), "snapshot_id")
        self._require_non_empty_string(document.get("snapshot_time"), "snapshot_time")
        _ensure_uuid(document["snapshot_id"], "snapshot_id")

        schema_version = document.get("schema_version")
        if schema_version != CONNECTOME_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {CONNECTOME_SCHEMA_VERSION}, got {schema_version!r}"
            )

        nodes = self._require_list(document.get("nodes"), "nodes")
        edges = self._require_list(document.get("edges"), "edges")
        hierarchies = self._require_list(document.get("hierarchies"), "hierarchies")
        invariants = self._require_list(document.get("invariants"), "invariants")

        if not nodes:
            raise ValueError("nodes must not be empty")
        if not edges:
            raise ValueError("edges must not be empty")
        if not invariants:
            raise ValueError("invariants must not be empty")

        node_ids = self._validate_nodes(nodes)
        edge_ids = self._validate_edges(edges, node_ids)
        self._validate_hierarchies(hierarchies, node_ids)
        invariant_ids = self._validate_invariants(invariants)

        return {
            "ok": True,
            "schema_version": schema_version,
            "identity_id": document["identity_id"],
            "node_count": len(node_ids),
            "edge_count": len(edge_ids),
            "hierarchy_count": len(hierarchies),
            "invariant_count": len(invariant_ids),
        }

    @staticmethod
    def _require_list(value: Any, field_name: str) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a list")
        return value

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    def _validate_nodes(self, nodes: List[Dict[str, Any]]) -> Set[str]:
        seen: Set[str] = set()
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError(f"nodes[{index}] must be an object")
            node_id = node.get("id")
            self._require_non_empty_string(node_id, f"nodes[{index}].id")
            _ensure_uuid(node_id, f"nodes[{index}].id")
            if node_id in seen:
                raise ValueError(f"duplicate node id: {node_id}")
            seen.add(node_id)

            kind = node.get("kind")
            if kind not in NODE_KINDS:
                raise ValueError(f"nodes[{index}].kind must be one of {sorted(NODE_KINDS)}")
            node_type = node.get("type")
            if node_type not in NODE_TYPES:
                raise ValueError(f"nodes[{index}].type must be one of {sorted(NODE_TYPES)}")

            position = node.get("position")
            if not isinstance(position, dict):
                raise ValueError(f"nodes[{index}].position must be an object")
            frame = position.get("frame")
            if frame not in POSITION_FRAMES:
                raise ValueError(
                    f"nodes[{index}].position.frame must be one of {sorted(POSITION_FRAMES)}"
                )
            for axis in ("x", "y", "z"):
                coordinate = position.get(axis)
                if not isinstance(coordinate, (int, float)):
                    raise ValueError(f"nodes[{index}].position.{axis} must be numeric")

            properties = node.get("properties")
            if not isinstance(properties, dict) or not properties:
                raise ValueError(f"nodes[{index}].properties must be a non-empty object")

        return seen

    def _validate_edges(self, edges: List[Dict[str, Any]], node_ids: Set[str]) -> Set[str]:
        seen: Set[str] = set()
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                raise ValueError(f"edges[{index}] must be an object")
            edge_id = edge.get("id")
            self._require_non_empty_string(edge_id, f"edges[{index}].id")
            _ensure_uuid(edge_id, f"edges[{index}].id")
            if edge_id in seen:
                raise ValueError(f"duplicate edge id: {edge_id}")
            seen.add(edge_id)

            source = edge.get("source")
            target = edge.get("target")
            self._require_non_empty_string(source, f"edges[{index}].source")
            self._require_non_empty_string(target, f"edges[{index}].target")
            if source not in node_ids:
                raise ValueError(f"edges[{index}].source references unknown node: {source}")
            if target not in node_ids:
                raise ValueError(f"edges[{index}].target references unknown node: {target}")

            for numeric_field in ("weight", "delay_ms"):
                value = edge.get(numeric_field)
                if not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f"edges[{index}].{numeric_field} must be >= 0")

            plasticity = edge.get("plasticity")
            if not isinstance(plasticity, dict):
                raise ValueError(f"edges[{index}].plasticity must be an object")
            self._require_non_empty_string(plasticity.get("rule"), f"edges[{index}].plasticity.rule")
            params = plasticity.get("params")
            if not isinstance(params, dict) or not params:
                raise ValueError(
                    f"edges[{index}].plasticity.params must be a non-empty object"
                )

        return seen

    def _validate_hierarchies(self, hierarchies: List[Dict[str, Any]], node_ids: Set[str]) -> None:
        seen: Set[str] = set()
        for index, hierarchy in enumerate(hierarchies):
            if not isinstance(hierarchy, dict):
                raise ValueError(f"hierarchies[{index}] must be an object")
            hierarchy_id = hierarchy.get("id")
            self._require_non_empty_string(hierarchy_id, f"hierarchies[{index}].id")
            _ensure_uuid(hierarchy_id, f"hierarchies[{index}].id")
            if hierarchy_id in seen:
                raise ValueError(f"duplicate hierarchy id: {hierarchy_id}")
            seen.add(hierarchy_id)
            self._require_non_empty_string(hierarchy.get("kind"), f"hierarchies[{index}].kind")
            members = hierarchy.get("members")
            if not isinstance(members, list) or not members:
                raise ValueError(f"hierarchies[{index}].members must be a non-empty list")
            if len(set(members)) != len(members):
                raise ValueError(f"hierarchies[{index}].members must be unique")
            for member in members:
                self._require_non_empty_string(member, f"hierarchies[{index}].member")
                if member not in node_ids:
                    raise ValueError(
                        f"hierarchies[{index}].members references unknown node: {member}"
                    )

    def _validate_invariants(self, invariants: List[Dict[str, Any]]) -> Set[str]:
        seen: Set[str] = set()
        for index, invariant in enumerate(invariants):
            if not isinstance(invariant, dict):
                raise ValueError(f"invariants[{index}] must be an object")
            invariant_id = invariant.get("invariant_id")
            self._require_non_empty_string(invariant_id, f"invariants[{index}].invariant_id")
            if invariant_id in seen:
                raise ValueError(f"duplicate invariant_id: {invariant_id}")
            seen.add(invariant_id)
            self._require_non_empty_string(
                invariant.get("expression"), f"invariants[{index}].expression"
            )
            self._require_non_empty_string(invariant.get("scope"), f"invariants[{index}].scope")
        return seen
