# Experimental Harnesses (`experimental/`)

> [!WARNING]
> ### WORK IN PROGRESS — DESIGN REFERENCE & PSEUDOCODE CHECK
> **These harnesses are NOT working production contracts or executable code yet.**
> They represent architectural pseudocode, design exploration, and language-evolution targets while developing the **Kaya $\leftrightarrow$ Harbor adapter** (`kaya-harbor`) and extending the Kaya compiler/runtime (`packages/kaya-core-rs`).
>
> We use them to establish:
> 1. How Kaya packages (`harness.toml` + `harness.kaya`) should interface with Harbor task inputs and container environments.
> 2. How the Kaya language needs to evolve to support first-class multi-turn coding choreographies, satellite capability bindings, and agent control flow without thousands of lines of Python runtime boilerplate.

---

## Included Experimental Packages

| Package | Purpose | Strategy |
| :--- | :--- | :--- |
| [`minimal-harness/`](./minimal-harness/) | Plumbing & connectivity smoke test | Single-turn prompt-and-response checking container attachment and exit signaling. |
| [`react/`](./react/) | Classic ReAct coding loop | Multi-turn Thought $\to$ Action $\to$ Observation cycle bound to container tools (`exec:bash`, `fs:read`, `fs:write`). |
| [`opencode-base/`](./opencode-base/) | Standard open-source coding agent baseline | Industry-standard coding prompt (inspired by OpenCode / SWE-agent) with exploration, targeted patching, and verification discipline. |
