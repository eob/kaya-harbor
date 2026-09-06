"""Trajectory export and ATIF v1.8 conversion utilities."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from kaya_harbor.models import Agent, FinalMetrics, Step, ToolCall, ToolObservation, Trajectory
from kaya_harbor.pricing import calculate_cost_usd


def convert_session_to_atif(source: Path | str | dict[str, Any]) -> Trajectory:
    """Convert a session ledger, JSON dump, or dictionary into a validated ATIF Trajectory.

    Handles:
    - Raw dictionary matching ATIF or Kaya session format
    - Path to a JSON file (exported by kaya-utils or recorded session)
    - Path to a session directory containing ledger.sqlite or events.jsonl (via kaya-utils export-trajectory)
    """
    if isinstance(source, dict):
        raw_data = source
    else:
        path = Path(source)
        if path.is_file() and path.suffix == ".json":
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        elif path.is_dir() or (path.is_file() and path.suffix in (".sqlite", ".jsonl")):
            # Attempt to invoke kaya-utils if available
            raw_data = _invoke_kaya_utils_export(path)
        else:
            raise ValueError(f"Unsupported session source: {source}")

    return _parse_raw_to_trajectory(raw_data)


def export_atif_file(
    session_ref: str | Path,
    output_path: Path | str,
    kaya_utils_bin: str = "kaya-utils",
) -> Path:
    """Export a session directly to an ATIF JSON file using kaya-utils or internal parser."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # If kaya-utils is available on PATH or specified, run CLI export
    bin_path = shutil.which(kaya_utils_bin)
    if bin_path:
        proc = subprocess.run(
            [bin_path, "session", "export-trajectory", str(session_ref), "--format", "atif", "-o", str(out_file)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and out_file.exists():
            return out_file

    # Fallback: convert directly
    trajectory = convert_session_to_atif(session_ref)
    out_file.write_text(json.dumps(trajectory.to_json_dict(), indent=2), encoding="utf-8")
    return out_file


def _invoke_kaya_utils_export(session_path: Path) -> dict[str, Any]:
    """Invoke kaya-utils to export a trajectory to stdout and parse the result."""
    bin_path = shutil.which("kaya-utils")
    if bin_path:
        proc = subprocess.run(
            [bin_path, "session", "export-trajectory", str(session_path), "--format", "atif"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout)

    # Fallback basic extraction if kaya-utils is not on PATH
    session_id = session_path.stem
    return {
        "schema_version": "v1.8",
        "session_id": session_id,
        "agent": {"name": "kaya-harbor", "version": "0.1.0"},
        "steps": [],
        "final_metrics": {"total_prompt_tokens": 0, "total_completion_tokens": 0, "total_cost_usd": 0.0},
    }


def _parse_raw_to_trajectory(raw: dict[str, Any]) -> Trajectory:
    """Parse dictionary into Trajectory Pydantic model."""
    schema_version = raw.get("schema_version", "v1.8")
    session_id = raw.get("session_id", raw.get("id", "unknown-session"))

    # Agent metadata
    raw_agent = raw.get("agent", {})
    if isinstance(raw_agent, str):
        agent = Agent(name=raw_agent)
    else:
        agent = Agent(
            name=raw_agent.get("name", "kaya-harbor"),
            version=raw_agent.get("version", "0.1.0"),
            model_name=raw_agent.get("model_name", raw.get("context", {}).get("model")),
        )

    # Steps
    raw_steps = raw.get("steps", [])
    steps: list[Step] = []
    for idx, s in enumerate(raw_steps, start=1):
        step_id = s.get("step_id", s.get("turn", idx))
        timestamp = s.get("timestamp")
        source = s.get("source", "agent")
        message = s.get("message", s.get("model_output", s.get("model_input")))

        tool_calls: list[ToolCall] = []
        for tc in s.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    tool_name=tc.get("tool_name", tc.get("name", "unknown_tool")),
                    arguments=tc.get("arguments", tc.get("input", {})),
                )
            )

        observations: list[ToolObservation] = []
        for obs in s.get("observations", s.get("tool_results", [])):
            observations.append(
                ToolObservation(
                    tool_name=obs.get("tool_name", "exec:bash"),
                    output=obs.get("output", obs.get("stdout")),
                    exit_code=obs.get("exit_code"),
                )
            )

        steps.append(
            Step(
                step_id=step_id,
                timestamp=timestamp,
                source=source,
                message=message,
                tool_calls=tool_calls,
                observations=observations,
            )
        )

    # Final Metrics & Cost calculation
    raw_metrics = raw.get("final_metrics", {})
    context = raw.get("context", {})
    prompt_tokens = raw_metrics.get("total_prompt_tokens", context.get("n_input_tokens", 0))
    completion_tokens = raw_metrics.get("total_completion_tokens", context.get("n_output_tokens", 0))
    cost_usd = raw_metrics.get("total_cost_usd", context.get("cost_usd"))

    if cost_usd is None:
        model_name = agent.model_name or "google/gemini-2.5-pro"
        cost_usd = calculate_cost_usd(model_name, prompt_tokens, completion_tokens)

    final_metrics = FinalMetrics(
        total_prompt_tokens=prompt_tokens,
        total_completion_tokens=completion_tokens,
        total_cost_usd=round(float(cost_usd), 6),
    )

    return Trajectory(
        schema_version=schema_version,
        session_id=session_id,
        agent=agent,
        steps=steps,
        final_metrics=final_metrics,
    )
