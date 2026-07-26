# ADR-007: Computation Tool

## Context
Standard RAG systems fail when asked to compute math, sort complex columns, or calculate date diffs, as LLMs are poor calculators. We needed a mechanism to execute precise mathematical operations safely.

## Decision
We implemented a restricted `ComputationTool` (`graph/nodes/computation_tool.py`) that writes code to a temporary file, executes it in a Python subprocess with a 3-second timeout, disables environment variables (`env={}`) to block network calls, and overrides `__import__` to restrict imports to `math`, `datetime`, and `json`.

## Alternatives Considered
1. **Docker Container Execution**: Spawn code inside a sandbox Docker container. Rejected because container startup overhead is slow (~500ms) and introduces operational dependencies on the client host.
2. **Unrestricted exec()**: Rejected because running code in the main web server process exposes the host system to remote code execution (RCE) vulnerabilities.

## Why Chosen
Subprocess sandboxing provides near-zero startup overhead, isolates memory, and blocks dangerous system calls effectively without relying on host container orchestration.

## Consequences
* User code execution is strictly limited to math, datetime, and json parsing.
* Any attempt to use `os`, `sys`, `subprocess`, or file writing raises an instant sandbox error.
