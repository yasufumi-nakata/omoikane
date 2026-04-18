"""TaskGraph reference model with bounded complexity guards."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Set

from ..common import new_id, utc_now_iso


@dataclass(frozen=True)
class TaskGraphComplexityPolicy:
    """Reference-runtime cap for TaskGraph construction and synthesis."""

    policy_id: str = "reference-v0"
    max_nodes: int = 5
    max_edges: int = 4
    max_depth: int = 3
    max_parallelism: int = 3
    max_result_refs: int = 5
    max_dependencies_per_node: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskNode:
    """Serializable DAG node for agent dispatch."""

    id: str
    role: str
    input_spec: Dict[str, Any]
    output_spec: Dict[str, Any]
    deps: List[str] = field(default_factory=list)
    ethics_constraints: List[str] = field(default_factory=list)
    timeout_ms: int = 1_000
    fallback_roles: List[str] = field(default_factory=list)
    status: str = "planned"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskGraphService:
    """Builds, validates, dispatches, and synthesizes bounded TaskGraphs."""

    def __init__(self) -> None:
        self._policy = TaskGraphComplexityPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def build_graph(self, intent: str, required_roles: List[str]) -> Dict[str, Any]:
        normalized_intent = self._normalize_non_empty(intent, "intent")
        roles = self._normalize_roles(required_roles)

        if len(roles) > self._policy.max_parallelism:
            raise ValueError(
                "required_roles exceed reference TaskGraph parallelism limit "
                f"({self._policy.max_parallelism})"
            )

        nodes: List[TaskNode] = []
        for index, role in enumerate(roles, start=1):
            node_id = f"node-{index}"
            nodes.append(
                TaskNode(
                    id=node_id,
                    role=role,
                    input_spec={
                        "intent": normalized_intent,
                        "handoff": "council-approved-brief",
                        "role_brief": f"{role} executes one bounded subtask.",
                    },
                    output_spec={
                        "artifact_ref": f"artifact://{role}",
                        "review_target": "node-council-review",
                    },
                    ethics_constraints=["sandboxed-only", "consensus-bus-only"],
                    timeout_ms=6_000,
                    fallback_roles=["codex-builder"],
                )
            )

        review_node = TaskNode(
            id="node-council-review",
            role="council-review",
            deps=[node.id for node in nodes],
            input_spec={
                "intent": normalized_intent,
                "required_roles": roles,
                "review_mode": "complexity-gated",
            },
            output_spec={
                "resolution": "approved-task-graph",
                "handoff": "node-result-synthesis",
            },
            ethics_constraints=["guardian-visible", "no-direct-apply"],
            timeout_ms=1_500,
            fallback_roles=["integrity-guardian"],
        )
        synthesis_node = TaskNode(
            id="node-result-synthesis",
            role="result-synthesis",
            deps=[review_node.id],
            input_spec={
                "intent": normalized_intent,
                "result_bundle": "approved-builder-artifacts",
            },
            output_spec={
                "artifact_ref": "artifact://task-graph-brief",
                "target": "council-consumable-summary",
            },
            ethics_constraints=["redact-sensitive-memory", "append-ledger-evidence"],
            timeout_ms=2_000,
            fallback_roles=["memory-archivist"],
        )

        graph = {
            "graph_id": new_id("graph"),
            "intent": normalized_intent,
            "required_roles": roles,
            "nodes": [node.to_dict() for node in [*nodes, review_node, synthesis_node]],
            "complexity_policy": self.policy(),
            "created_at": utc_now_iso(),
        }
        self.validate_graph(graph)
        return graph

    def validate_graph(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(graph, dict):
            raise ValueError("graph must be an object")
        graph_id = self._normalize_non_empty(graph.get("graph_id"), "graph_id")
        if "intent" in graph:
            self._normalize_non_empty(graph.get("intent"), "intent")
        if "created_at" in graph:
            self._normalize_non_empty(graph.get("created_at"), "created_at")

        policy = self._parse_policy(graph.get("complexity_policy"))
        nodes = graph.get("nodes")
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("nodes must be a non-empty list")

        role_names = graph.get("required_roles")
        if role_names is not None:
            if not isinstance(role_names, list) or not role_names:
                raise ValueError("required_roles must be a non-empty list")
            if len(role_names) > policy.max_parallelism:
                raise ValueError("required_roles exceed max_parallelism")

        seen_ids: Set[str] = set()
        edge_count = 0
        root_count = 0
        children: Dict[str, List[str]] = {}
        dep_counts: Dict[str, int] = {}

        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError(f"nodes[{index}] must be an object")
            node_id = self._normalize_non_empty(node.get("id"), f"nodes[{index}].id")
            if node_id in seen_ids:
                raise ValueError(f"duplicate node id: {node_id}")
            seen_ids.add(node_id)
            children[node_id] = []

            self._normalize_non_empty(node.get("role"), f"nodes[{index}].role")
            deps = node.get("deps", [])
            if not isinstance(deps, list):
                raise ValueError(f"nodes[{index}].deps must be a list")
            if len(deps) > policy.max_dependencies_per_node:
                raise ValueError(
                    f"nodes[{index}].deps exceed max_dependencies_per_node "
                    f"({policy.max_dependencies_per_node})"
                )
            for dep in deps:
                self._normalize_non_empty(dep, f"nodes[{index}].deps[]")
            dep_counts[node_id] = len(deps)
            edge_count += len(deps)
            if not deps:
                root_count += 1

            if not isinstance(node.get("input_spec"), dict) or not node["input_spec"]:
                raise ValueError(f"nodes[{index}].input_spec must be a non-empty object")
            output_spec = node.get("output_spec")
            if not isinstance(output_spec, (dict, str)) or (
                isinstance(output_spec, str) and not output_spec.strip()
            ):
                raise ValueError(f"nodes[{index}].output_spec must be a non-empty object or string")
            if not isinstance(node.get("timeout_ms"), int) or node["timeout_ms"] < 1:
                raise ValueError(f"nodes[{index}].timeout_ms must be a positive integer")
            status = node.get("status", "planned")
            if status not in {"planned", "dispatched", "running", "complete", "failed", "canceled"}:
                raise ValueError(f"nodes[{index}].status is invalid: {status!r}")

        for index, node in enumerate(nodes):
            node_id = node["id"]
            deps = node.get("deps", [])
            for dep in deps:
                if dep not in seen_ids:
                    raise ValueError(f"nodes[{index}].deps references unknown node: {dep}")
                children[dep].append(node_id)

        if len(nodes) > policy.max_nodes:
            raise ValueError(f"node_count exceeds max_nodes ({policy.max_nodes})")
        if edge_count > policy.max_edges:
            raise ValueError(f"edge_count exceeds max_edges ({policy.max_edges})")
        if root_count > policy.max_parallelism:
            raise ValueError(f"root_count exceeds max_parallelism ({policy.max_parallelism})")

        max_depth = self._max_depth(nodes)
        if max_depth > policy.max_depth:
            raise ValueError(f"max_depth exceeds policy limit ({policy.max_depth})")

        return {
            "ok": True,
            "graph_id": graph_id,
            "policy_id": policy.policy_id,
            "node_count": len(nodes),
            "edge_count": edge_count,
            "root_count": root_count,
            "max_depth": max_depth,
        }

    def dispatch_graph(
        self,
        graph_id: str,
        nodes: List[Dict[str, Any]],
        complexity_policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._normalize_non_empty(graph_id, "graph_id")
        policy = self._parse_policy(complexity_policy)
        self.validate_graph(
            {
                "graph_id": graph_id,
                "nodes": nodes,
                "complexity_policy": policy.to_dict(),
            }
        )

        ready_node_ids: List[str] = []
        for node in nodes:
            if node.get("status", "planned") == "planned" and not node.get("deps", []):
                node["status"] = "dispatched"
                ready_node_ids.append(node["id"])

        if len(ready_node_ids) > policy.max_parallelism:
            raise ValueError(f"ready nodes exceed max_parallelism ({policy.max_parallelism})")

        return {
            "graph_id": graph_id,
            "dispatched_count": len(ready_node_ids),
            "ready_node_ids": ready_node_ids,
        }

    def synthesize_results(
        self,
        graph_id: str,
        result_refs: List[str],
        complexity_policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._normalize_non_empty(graph_id, "graph_id")
        policy = self._parse_policy(complexity_policy)
        refs = self._normalize_result_refs(result_refs)
        if len(refs) > policy.max_result_refs:
            raise ValueError(f"result_refs exceed max_result_refs ({policy.max_result_refs})")
        return {
            "graph_id": graph_id,
            "synthesis_ref": new_id("synthesis"),
            "accepted_result_count": len(refs),
        }

    @staticmethod
    def _normalize_non_empty(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    def _normalize_roles(self, required_roles: List[str]) -> List[str]:
        if not isinstance(required_roles, list) or not required_roles:
            raise ValueError("required_roles must be a non-empty list")
        unique_roles: List[str] = []
        seen: Set[str] = set()
        for index, role in enumerate(required_roles):
            normalized = self._normalize_non_empty(role, f"required_roles[{index}]")
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_roles.append(normalized)
        return unique_roles

    def _normalize_result_refs(self, result_refs: List[str]) -> List[str]:
        if not isinstance(result_refs, list) or not result_refs:
            raise ValueError("result_refs must be a non-empty list")
        refs: List[str] = []
        seen: Set[str] = set()
        for index, ref in enumerate(result_refs):
            normalized = self._normalize_non_empty(ref, f"result_refs[{index}]")
            if normalized in seen:
                continue
            seen.add(normalized)
            refs.append(normalized)
        return refs

    def _parse_policy(self, value: Any) -> TaskGraphComplexityPolicy:
        if not isinstance(value, dict):
            raise ValueError("complexity_policy must be an object")

        policy = TaskGraphComplexityPolicy(
            policy_id=self._normalize_non_empty(value.get("policy_id"), "complexity_policy.policy_id"),
            max_nodes=self._positive_int(value.get("max_nodes"), "complexity_policy.max_nodes"),
            max_edges=self._positive_int(value.get("max_edges"), "complexity_policy.max_edges"),
            max_depth=self._positive_int(value.get("max_depth"), "complexity_policy.max_depth"),
            max_parallelism=self._positive_int(
                value.get("max_parallelism"), "complexity_policy.max_parallelism"
            ),
            max_result_refs=self._positive_int(
                value.get("max_result_refs"), "complexity_policy.max_result_refs"
            ),
            max_dependencies_per_node=self._positive_int(
                value.get("max_dependencies_per_node"),
                "complexity_policy.max_dependencies_per_node",
            ),
        )
        if policy != self._policy:
            raise ValueError("unsupported complexity_policy for reference runtime")
        return policy

    @staticmethod
    def _positive_int(value: Any, field_name: str) -> int:
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"{field_name} must be a positive integer")
        return value

    @staticmethod
    def _max_depth(nodes: List[Dict[str, Any]]) -> int:
        node_map = {node["id"]: node for node in nodes}
        visiting: Set[str] = set()
        depth_cache: Dict[str, int] = {}

        def visit(node_id: str) -> int:
            if node_id in depth_cache:
                return depth_cache[node_id]
            if node_id in visiting:
                raise ValueError(f"cycle detected in TaskGraph at {node_id}")
            visiting.add(node_id)
            deps = node_map[node_id].get("deps", [])
            depth = 1 if not deps else 1 + max(visit(dep) for dep in deps)
            visiting.remove(node_id)
            depth_cache[node_id] = depth
            return depth

        return max(visit(node_id) for node_id in node_map)
