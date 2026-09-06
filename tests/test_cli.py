"""Tests for kaya-harbor CLI."""

import json
from pathlib import Path
from kaya_harbor.cli import main


def test_cli_info(capsys):
    ret = main(["info"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Kaya Harbor Adapter v0.1.0" in captured.out
    assert "Agent Name: kaya-harbor" in captured.out


def test_cli_export(tmp_path: Path, capsys):
    sample = {
        "session_id": "cli-test",
        "agent": {"name": "test"},
        "steps": [],
        "final_metrics": {"total_prompt_tokens": 100, "total_completion_tokens": 10},
    }
    in_file = tmp_path / "session.json"
    in_file.write_text(json.dumps(sample), encoding="utf-8")
    out_file = tmp_path / "trajectory.json"

    ret = main(["export", str(in_file), "-o", str(out_file)])
    assert ret == 0
    assert out_file.exists()
    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert content["schema_version"] == "v1.8"
    assert content["session_id"] == "cli-test"
