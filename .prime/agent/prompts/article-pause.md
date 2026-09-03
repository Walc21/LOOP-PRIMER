---
description: Pause one local article-loop run through its durable API.
argument-hint: "[--run-id ID]"
---
# /article-pause

This is a project-local M11 command. Load `AGENTS.md`, `AI_CONTEXT.md`, and
`.prime/agent/skills/article-loop/SKILL.md`; validate the root and optional
safe run ID from `$ARGUMENTS`.

Invoke only `await article_loop.pause(root=root)` or
`await Orchestrator(root).pause(run_id)` through
`scripts/article_loop_command.py pause`. Let the state machine and STOP rules
decide whether the operation is allowed. Show the bounded JSON result, do not
start or cancel unrelated children, and end the turn without polling.
