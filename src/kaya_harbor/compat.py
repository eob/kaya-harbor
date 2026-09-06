"""Harbor compatibility layer.

Provides imports from `harbor` when available, or provides compliant fallback
classes when running standalone or on Python runtimes without `harbor`.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


@dataclass
class ExecResult:
    """Result of executing a command in an environment."""

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""


class BaseEnvironment(ABC):
    """Abstract interface for execution environments."""

    @abstractmethod
    def exec(self, command: str, **kwargs: Any) -> ExecResult:
        """Execute a command in the environment."""
        ...


class AgentContext(BaseModel):
    """Execution context and metadata for an agent."""

    session_id: str = Field(default_factory=lambda: f"session-{uuid4().hex[:8]}")
    context_id: UUID = Field(default_factory=uuid4)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Try importing genuine harbor classes if harbor is installed
try:
    from harbor.agents.base import BaseAgent as _HarborBaseAgent
    from harbor.environments.base import BaseEnvironment as _HarborBaseEnvironment
    from harbor.models.agent.context import AgentContext as _HarborAgentContext

    HAS_HARBOR = True
except ImportError:
    HAS_HARBOR = False
    _HarborBaseAgent = object  # type: ignore


class BaseAgent(ABC):
    """Base class for evaluation agents adhering to Harbor's BaseAgent interface."""

    session_id: str | None = None
    context_id: UUID | None = None
    model_name: str | None = None

    @staticmethod
    def name() -> str:
        """The canonical name of the agent."""
        return "kaya-harbor"

    def version(self) -> str | None:
        """The version of the agent."""
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Run setup commands in the environment before solving tasks."""
        pass

    @abstractmethod
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Run the agent in the environment to solve the given instruction."""
        ...

    def run_sync(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext | None = None,
    ) -> int:
        """Synchronous wrapper for running the agent."""
        if context is None:
            context = AgentContext()
        return asyncio.run(self._run_wrapper(instruction, environment, context))

    async def _run_wrapper(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> int:
        await self.setup(environment)
        await self.run(instruction, environment, context)
        return 0
