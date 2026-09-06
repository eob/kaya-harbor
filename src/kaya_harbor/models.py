"""ATIF (Agent Trajectory Interchange Format) v1.8 data models.

Compatible with harbor.models.trajectories.Trajectory and standard ATIF v1.8 schema.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Agent metadata in an ATIF trajectory."""

    name: str = "kaya-harbor"
    version: str | None = "0.1.0"
    model_name: str | None = None


class ToolCall(BaseModel):
    """A tool invocation emitted by the agent."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolObservation(BaseModel):
    """Result / output of a tool execution."""

    tool_name: str
    output: str | None = None
    exit_code: int | None = None


class Step(BaseModel):
    """An interaction turn/step in the trajectory."""

    step_id: int
    timestamp: str | None = None
    source: str = "agent"  # "user", "agent", or "system"
    message: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    observations: list[ToolObservation] = Field(default_factory=list)


class FinalMetrics(BaseModel):
    """Final operational and cost metrics for the trajectory."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0


class Trajectory(BaseModel):
    """Root model for an ATIF v1.8 trajectory."""

    schema_version: str = "v1.8"
    session_id: str
    agent: Agent = Field(default_factory=Agent)
    steps: list[Step] = Field(default_factory=list)
    final_metrics: FinalMetrics = Field(default_factory=FinalMetrics)

    def to_json_dict(self) -> dict[str, Any]:
        """Convert trajectory to JSON-compatible dictionary."""
        return self.model_dump(exclude_none=True)
