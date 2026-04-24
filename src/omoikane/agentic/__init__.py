"""Agentic orchestration modules."""

from __future__ import annotations

from typing import Any

__all__ = [
    "CognitiveAuditService",
    "CognitiveAuditGovernanceService",
    "ConsensusBus",
    "ConsensusMessage",
    "Council",
    "CouncilMember",
    "CouncilProposal",
    "CouncilVote",
    "DistributedCouncilResolution",
    "DistributedTransportService",
    "DistributedCouncilVote",
    "TaskGraphService",
    "TrustService",
    "TrustThresholds",
    "TrustUpdatePolicy",
    "YaoyorozuRegistryPolicy",
    "YaoyorozuRegistryService",
]


def __getattr__(name: str) -> Any:
    if name == "CognitiveAuditService":
        from .cognitive_audit import CognitiveAuditService

        return CognitiveAuditService
    if name == "CognitiveAuditGovernanceService":
        from .cognitive_audit_governance import CognitiveAuditGovernanceService

        return CognitiveAuditGovernanceService
    if name in {"ConsensusBus", "ConsensusMessage"}:
        from .consensus_bus import ConsensusBus, ConsensusMessage

        return {"ConsensusBus": ConsensusBus, "ConsensusMessage": ConsensusMessage}[name]
    if name in {
        "Council",
        "CouncilMember",
        "CouncilProposal",
        "CouncilVote",
        "DistributedCouncilResolution",
        "DistributedCouncilVote",
    }:
        from .council import (
            Council,
            CouncilMember,
            CouncilProposal,
            CouncilVote,
            DistributedCouncilResolution,
            DistributedCouncilVote,
        )

        return {
            "Council": Council,
            "CouncilMember": CouncilMember,
            "CouncilProposal": CouncilProposal,
            "CouncilVote": CouncilVote,
            "DistributedCouncilResolution": DistributedCouncilResolution,
            "DistributedCouncilVote": DistributedCouncilVote,
        }[name]
    if name == "DistributedTransportService":
        from .distributed_transport import DistributedTransportService

        return DistributedTransportService
    if name == "TaskGraphService":
        from .task_graph import TaskGraphService

        return TaskGraphService
    if name in {"TrustService", "TrustThresholds", "TrustUpdatePolicy"}:
        from .trust import TrustService, TrustThresholds, TrustUpdatePolicy

        return {
            "TrustService": TrustService,
            "TrustThresholds": TrustThresholds,
            "TrustUpdatePolicy": TrustUpdatePolicy,
        }[name]
    if name in {"YaoyorozuRegistryPolicy", "YaoyorozuRegistryService"}:
        from .yaoyorozu import YaoyorozuRegistryPolicy, YaoyorozuRegistryService

        return {
            "YaoyorozuRegistryPolicy": YaoyorozuRegistryPolicy,
            "YaoyorozuRegistryService": YaoyorozuRegistryService,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
