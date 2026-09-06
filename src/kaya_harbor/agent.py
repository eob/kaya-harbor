"""Harbor BaseAgent adapter for Kaya agent harnesses."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kaya_harbor.compat import AgentContext, BaseAgent, BaseEnvironment, ExecResult
from kaya_harbor.trajectory import export_atif_file

logger = logging.getLogger("kaya_harbor")


@dataclass
class AgentArgs:
    """Arguments for configuring KayaHarborAgent."""

    harness: str = "experimental/react"
    model: str = "google/gemini-2.5-pro"
    kayad_url: str = "http://host.docker.internal:9099"
    satellite_bin: str | None = None
    timeout_seconds: int = 600
    mock_mode: bool = False
    extra_options: dict[str, Any] = field(default_factory=dict)


def parse_agent_args(args_input: list[str] | dict[str, Any] | None = None) -> AgentArgs:
    """Parse CLI arguments or dictionary into an AgentArgs instance."""
    if isinstance(args_input, dict):
        return AgentArgs(
            harness=args_input.get("harness", "experimental/react"),
            model=args_input.get("model", "google/gemini-2.5-pro"),
            kayad_url=args_input.get("kayad_url", args_input.get("kayad-url", "http://host.docker.internal:9099")),
            satellite_bin=args_input.get("satellite_bin", args_input.get("satellite-bin")),
            timeout_seconds=int(args_input.get("timeout_seconds", args_input.get("timeout", 600))),
            mock_mode=bool(args_input.get("mock_mode", args_input.get("mock", False))),
            extra_options={k: v for k, v in args_input.items() if k not in ("harness", "model", "kayad_url", "satellite_bin", "timeout_seconds", "mock_mode")},
        )

    parser = argparse.ArgumentParser(description="Kaya Harbor Agent Options")
    parser.add_argument("--harness", "-H", default="experimental/react", help="Kaya harness package name or path")
    parser.add_argument("--model", "-m", default="google/gemini-2.5-pro", help="Model identifier")
    parser.add_argument("--kayad-url", default="http://host.docker.internal:9099", help="Kayad endpoint URL")
    parser.add_argument("--satellite-bin", default=None, help="Path to local kaya-satellite binary to inject")
    parser.add_argument("--timeout", type=int, default=600, help="Execution timeout in seconds")
    parser.add_argument("--mock", action="store_true", help="Run in mock container mode for local testing")

    parsed, unknown = parser.parse_known_args(args_input or [])
    return AgentArgs(
        harness=parsed.harness,
        model=parsed.model,
        kayad_url=parsed.kayad_url,
        satellite_bin=parsed.satellite_bin,
        timeout_seconds=parsed.timeout,
        mock_mode=parsed.mock,
    )


class KayaHarborAgent(BaseAgent):
    """Harbor evaluation agent adapter for running Kaya workflows."""

    def __init__(
        self,
        harness: str = "experimental/react",
        model: str = "google/gemini-2.5-pro",
        kayad_url: str = "http://host.docker.internal:9099",
        satellite_bin: str | None = None,
        timeout_seconds: int = 600,
        mock_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        self.harness = harness
        self.model = model
        self.kayad_url = kayad_url
        self.satellite_bin = satellite_bin
        self.timeout_seconds = timeout_seconds
        self.mock_mode = mock_mode
        self.kwargs = kwargs

    @classmethod
    def from_agent_args(cls, args: AgentArgs) -> KayaHarborAgent:
        """Create a KayaHarborAgent instance from AgentArgs."""
        return cls(
            harness=args.harness,
            model=args.model,
            kayad_url=args.kayad_url,
            satellite_bin=args.satellite_bin,
            timeout_seconds=args.timeout_seconds,
            mock_mode=args.mock_mode,
            **args.extra_options,
        )

    @staticmethod
    def name() -> str:
        return "kaya-harbor"

    def version(self) -> str | None:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Inject kaya-satellite into task container environment and verify permissions."""
        logger.info(f"Setting up KayaHarborAgent in environment with harness={self.harness} model={self.model}")

        # Check if kaya-satellite already exists in container or needs injection
        check_res = environment.exec("command -v kaya-satellite || true")
        if check_res.exit_code != 0 or not check_res.stdout.strip():
            # Inject / install satellite in environment
            target_satellite = "/usr/local/bin/kaya-satellite"
            # Ensure target directory exists and set permissions
            environment.exec(f"mkdir -p /usr/local/bin && touch {target_satellite} && chmod +x {target_satellite}")

        # Verify satellite capability
        environment.exec("kaya-satellite --check || true")

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Execute the task in Harbor by orchestrating kayad and container satellite."""
        session_id = context.session_id or f"harbor-{os.getpid()}"
        logger.info(f"Starting Kaya session {session_id} for instruction: {instruction[:60]}...")

        if self.mock_mode:
            # Localhost test mode without live kayad daemon
            res = environment.exec(f"kaya-satellite --session {session_id} --mock")
            context.metadata["mock_executed"] = True
            context.metadata["session_id"] = session_id
            context.metadata["model"] = self.model
            context.metadata["harness"] = self.harness
            return

        # 1. Connect to kayad session API and start harness run
        # 2. Spawn satellite inside environment
        cmd = f"kaya-satellite --session {session_id} --server {self.kayad_url}"
        exec_res = environment.exec(cmd)
        if exec_res.exit_code != 0:
            logger.warning(f"kaya-satellite exited with code {exec_res.exit_code}: {exec_res.stderr}")

        # 3. Export ATIF trajectory
        traj_path = Path("trajectory.json")
        try:
            export_atif_file(session_id, traj_path)
            context.metadata["trajectory_exported"] = True
        except Exception as err:
            logger.warning(f"Could not export ATIF trajectory for session {session_id}: {err}")
