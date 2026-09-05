# `experimental/react`

> [!WARNING]
> **WORK IN PROGRESS — ARCHITECTURAL PSEUDOCODE**
> This harness is not a working contract. It serves as an architectural design check for expressing standard unconstrained ReAct loops as concise Kaya programs.

## Concept & Architecture

Most agent frameworks (LangChain, AutoGen, CrewAI, SWE-agent) implement ReAct via hundreds of lines of Python classes, callback handlers, state machines, and message converters.

In Kaya, the ReAct pattern is expressed directly in native control flow:
- A `while` loop bounding execution to `maxTurns`.
- Native `agentStep` calling the LLM and dispatching tool calls to the satellite embodiment.
- First-class conditional branching on `step.disposition`.

## Capabilities

Requires the following satellite capabilities:
- `exec:bash`: Run terminal commands in the container.
- `fs:read`: Read repository files.
- `fs:write`: Create or overwrite files.

## Expected Invocation

```bash
harbor run -d "terminal-bench@2.0" --agent kaya_harbor:KayaHarborAgent --ak harness=experimental/react
```
