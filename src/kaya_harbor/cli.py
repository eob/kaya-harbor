"""CLI entrypoint for kaya-harbor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kaya_harbor.agent import KayaHarborAgent, parse_agent_args
from kaya_harbor.trajectory import convert_session_to_atif


def main(argv: list[str] | None = None) -> int:
    """Run kaya-harbor CLI."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="kaya-harbor",
        description="Harbor evaluation adapter and ATIF tools for Kaya harnesses",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Command: info
    subparsers.add_parser("info", help="Show adapter information and version")

    # Command: export
    export_parser = subparsers.add_parser("export", help="Export session to ATIF trajectory")
    export_parser.add_argument("session", help="Path to session directory or JSON file")
    export_parser.add_argument("-o", "--output", help="Output file path", default="trajectory.json")

    args, remaining = parser.parse_known_args(argv)

    if args.command == "info" or not args.command:
        agent = KayaHarborAgent()
        print(f"Kaya Harbor Adapter v{agent.version()}")
        print(f"Agent Name: {agent.name()}")
        print(f"Default Model: {agent.model}")
        print(f"Default Harness: {agent.harness}")
        return 0

    if args.command == "export":
        traj = convert_session_to_atif(args.session)
        out_path = Path(args.output)
        out_path.write_text(traj.model_dump_json(indent=2), encoding="utf-8")
        print(f"Exported ATIF trajectory to {out_path} ({len(traj.steps)} steps)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
