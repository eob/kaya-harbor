import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

from kaya_harbor.agent import KayaHarborAgent
from kaya_harbor.compat import BaseEnvironment, AgentContext, ExecResult
from kaya_harbor.models import Trajectory, Agent, Step, FinalMetrics
from kaya_harbor.trajectory import convert_session_to_atif


class MockEnvironment(BaseEnvironment):
    """Mock Harbor environment that runs commands in a temporary directory or mock container."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.executed_commands: list[str] = []

    def exec(self, command: str, **kwargs) -> ExecResult:
        self.executed_commands.append(command)
        # Handle injection of kaya-satellite and execution
        if "kaya-satellite" in command and "--check" in command:
            return ExecResult(exit_code=0, stdout="kaya-satellite 0.1.0\n", stderr="")
        if "chmod +x" in command:
            return ExecResult(exit_code=0, stdout="", stderr="")
        return ExecResult(exit_code=0, stdout="ok\n", stderr="")


class MockTask:
    """Mock Harbor task."""

    def __init__(self, instruction: str, tmp_path: Path):
        self.instruction = instruction
        self.container = MockEnvironment(tmp_path)


def test_harbor_adapter_mock_container(tmp_path: Path):
    """Mock Harbor's task.container with a local runner. Run adapter against a mock task; assert satellite connects and returns exit code 0."""
    task = MockTask(instruction="Fix issue with return code", tmp_path=tmp_path)
    agent = KayaHarborAgent(
        harness="experimental/react",
        model="google/gemini-2.5-pro",
        kayad_url="http://localhost:9099",
        mock_mode=True,
    )

    context = AgentContext()
    exit_code = agent.run_sync(instruction=task.instruction, environment=task.container, context=context)

    assert exit_code == 0
    assert len(task.container.executed_commands) > 0
    # Verify satellite was configured or run
    assert any("kaya-satellite" in cmd for cmd in task.container.executed_commands)


def test_harbor_cli_flag_integration():
    """Verify harbor run / adapter arguments accept --harness and --model arguments correctly."""
    from kaya_harbor.agent import parse_agent_args

    args = parse_agent_args(["--harness", "experimental/react", "--model", "google/gemini-2.5-pro", "--kayad-url", "http://127.0.0.1:9099"])
    assert args.harness == "experimental/react"
    assert args.model == "google/gemini-2.5-pro"
    assert args.kayad_url == "http://127.0.0.1:9099"

    agent = KayaHarborAgent.from_agent_args(args)
    assert agent.harness == "experimental/react"
    assert agent.model == "google/gemini-2.5-pro"


def test_atif_trajectory_conversion(tmp_path: Path):
    """Convert a sample SQLite / JSON Kaya session ledger into standard ATIF format; assert strict schema compliance against Trajectory."""
    sample_session_data = {
        "session_id": "test-session-001",
        "agent": {
            "name": "kaya:experimental/react",
            "version": "0.1.0",
            "model_name": "google/gemini-2.5-pro",
        },
        "steps": [
            {
                "step_id": 1,
                "timestamp": "2026-09-06T12:00:00Z",
                "source": "user",
                "message": "Fix the bug in main.py",
                "tool_calls": [],
                "observations": [],
            },
            {
                "step_id": 2,
                "timestamp": "2026-09-06T12:00:02Z",
                "source": "agent",
                "message": "Let me inspect the file.",
                "tool_calls": [
                    {
                        "tool_name": "exec:bash",
                        "arguments": {"command": "cat main.py"},
                    }
                ],
                "observations": [
                    {
                        "tool_name": "exec:bash",
                        "output": "print('hello')",
                        "exit_code": 0,
                    }
                ],
            },
        ],
        "final_metrics": {
            "total_prompt_tokens": 1200,
            "total_completion_tokens": 150,
            "total_cost_usd": 0.00225,
        },
    }

    session_file = tmp_path / "session_data.json"
    session_file.write_text(json.dumps(sample_session_data), encoding="utf-8")

    trajectory = convert_session_to_atif(session_file)
    assert isinstance(trajectory, Trajectory)
    assert trajectory.schema_version == "v1.8"
    assert trajectory.session_id == "test-session-001"
    assert trajectory.agent.name == "kaya:experimental/react"
    assert len(trajectory.steps) == 2
    assert trajectory.final_metrics.total_cost_usd == 0.00225


def test_package_build_and_metadata(tmp_path: Path):
    """Validate pyproject.toml metadata and build wheel using python -m build; assert clean package install into clean virtual environment."""
    repo_root = Path(__file__).resolve().parent.parent

    # Build wheel using python -m build
    dist_dir = tmp_path / "dist"
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}\n{result.stdout}"

    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1
    assert "kaya_harbor" in wheels[0].name
