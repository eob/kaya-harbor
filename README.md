# `kaya-harbor`

[![PyPI version](https://img.shields.io/pypi/v/kaya-harbor.svg)](https://pypi.org/project/kaya-harbor/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Public [Harbor](https://github.com/laude-institute/harbor) evaluation adapter for the **Kaya** agentic programming language and runtime.

`kaya-harbor` implements Harbor's `BaseAgent` interface to evaluate Kaya workflows across standard benchmarks (such as **Terminal-Bench** and **SWE-bench**), holding foundation model weights fixed while evaluating the performance, cost, and token efficiency of different agent harnesses.

---

## Strategic Architecture

- **Primary Evaluation LLM**: **Google Gemini** (`google/gemini-2.5-pro` and `google/gemini-2.5-flash`). Running on Google Cloud credits enables exhaustive, reproducible benchmark sweeps across large task datasets without prohibitive API bills.
- **Reference Baseline**: **Google Antigravity (`agy`)**. We benchmark Kaya harnesses directly against `agy` (Google's first-party agent CLI) running the identical Gemini models, isolating the exact performance deltas introduced by workflow scaffolding and verification ratchets.
- **Execution Model**:
  - Evaluation host runs `kayad` (Kaya daemon) and Harbor.
  - Evaluation container receives the lightweight, zero-dependency `kaya-satellite` binary.
  - The container connects back to `kayad` via WebSocket, exposing bash execution and filesystem tools.
- **Durable Trajectories & Cost Accounting**:
  - Exports standard **ATIF v1.8** (`trajectory.json`) for every benchmark run.
  - Translates Kaya's token telemetry into official USD costs via `kaya-utils session export-trajectory`.

---

## Quickstart

### Installation

```bash
pip install kaya-harbor
```

### Running a Benchmark Task

```bash
harbor run \
  -d "terminal-bench@2.0" \
  --agent kaya_harbor:KayaHarborAgent \
  --ak harness=experimental/react \
  --ak model=google/gemini-2.5-pro
```

---

## Harness Resolution

The `--ak harness=<name>` argument resolves harnesses using the following hierarchy:
1. Local directory or file path if it exists.
2. `KAYA_HARNESSES_DIR` environment variable override (for local development).
3. Local cache: `~/.cache/kaya/harnesses/<name>/`.
4. Remote Git registry: `https://github.com/eob/kaya-harnesses` at `harnesses/<name>/`.

---

## Trajectory Output

At session conclusion, the adapter invokes `kaya-utils` to export the session ledger into ATIF format:

```json
{
  "schema_version": "v1.8",
  "session_id": "harbor-session-12345",
  "agent_name": "kaya:experimental/react",
  "context": {
    "model": "google/gemini-2.5-pro",
    "n_input_tokens": 42150,
    "n_output_tokens": 3840,
    "cost_usd": 0.0824
  },
  "steps": [...]
}
```

---

## License

Apache 2.0. See [LICENSE](LICENSE) for details.
