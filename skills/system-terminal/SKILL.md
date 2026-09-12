---
name: system-terminal
description: Execute terminal commands and inspect or terminate running processes on the host.
---

# System Terminal & Process Execution Skill

## Capabilities
- Execute shell/PowerShell commands with timeout and output capture (`exec` tool).
- Enumerate running system processes with PID and memory consumption (`process.list`).
- Terminate unresponsive or target processes by name or PID (`process.kill`).
- Query running status of any executable (`process.status`).

## Workflow Guidelines
1. Prefer fast, non-blocking commands.
2. Use `process.status` or `process.list` to verify state before attempting process termination.
3. Always inspect command output and exit codes; report failures truthfully.
