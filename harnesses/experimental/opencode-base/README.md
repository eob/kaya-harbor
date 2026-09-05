# `experimental/opencode-base`

> [!WARNING]
> **WORK IN PROGRESS — ARCHITECTURAL PSEUDOCODE**
> This harness is not a working contract. It serves as an architectural design check for expressing open-source coding agent prompt structures (OpenCode, SWE-agent, Aider) and phased error-recovery within Kaya.

## Concept & Architecture

The `opencode-base` harness mirrors the standard prompt engineering and phased execution used in popular open-source coding agents:
1. **Phased Prompts**: Separates the initial workspace discovery phase from active editing and diff capture.
2. **Error Recovery**: Automatically feeds runtime tool errors back to the model for self-repair instead of crashing the harness.
3. **Diff Verification**: Captures `git diff HEAD` at session completion to provide clear patch artifacts for evaluation scorecards.

## Capabilities

Requires the following satellite capabilities:
- `exec:bash`: Shell command execution for tests, grep, git.
- `fs:read`: File reading.
- `fs:write`: File writing/editing.

## Expected Invocation

```bash
harbor run -d "terminal-bench@2.0" --agent kaya_harbor:KayaHarborAgent --ak harness=experimental/opencode-base
```
