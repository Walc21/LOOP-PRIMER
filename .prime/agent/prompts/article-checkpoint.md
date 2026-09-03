---
description: Persist one local article-loop checkpoint for recovery.
argument-hint: "[--run-id ID]"
---
# /article-checkpoint

This is a project-local M11 command. Load `AGENTS.md`, `AI_CONTEXT.md`, and
`.prime/agent/skills/article-loop/SKILL.md`. Validate the root and optional
safe run ID from `$ARGUMENTS`; reject unknown options.

Invoke only `await article_loop.checkpoint(root=root)` or
`await Orchestrator(root).checkpoint(run_id)` through
`scripts/article_loop_command.py checkpoint`. Preserve the durable event log,
use the existing atomic API, show only the bounded result, and never edit a
champion or create a Prime child. If recovery is pending, report it and end
the turn instead of polling.
