# `experimental/minimal-harness`

> [!WARNING]
> **WORK IN PROGRESS — ARCHITECTURAL PSEUDOCODE**
> This harness is not a working contract. It serves as an architectural design check for verifying the plumbing between Harbor, `kaya-harbor`, the `kayad` daemon, and the container satellite binary.

## Concept & Purpose

The `minimal-harness` is the simplest possible Kaya harness. Its sole responsibility is to verify the execution pipeline:
1. Harbor spins up an evaluation container.
2. `kaya-harbor` injects `kaya-satellite` and initiates a WebSocket handshake to `kayad`.
3. `kayad` starts `minimal-harness/harness.kaya`.
4. The workflow receives the task instruction, triggers a single LLM turn, and terminates cleanly with exit code 0.

## Expected Invocation

```bash
harbor run -d "terminal-bench@2.0" --agent kaya_harbor:KayaHarborAgent --ak harness=experimental/minimal-harness
```
