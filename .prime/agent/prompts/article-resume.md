---
description: Resume one paused article-loop run through its durable API.
argument-hint: "[--run-id ID]"
---
# /article-resume

This is a project-local M11 command. Load `AGENTS.md`, `AI_CONTEXT.md`, and
`.prime/agent/skills/article-loop/SKILL.md`; validate the root and optional
safe run ID from `$ARGUMENTS`.

Invoke only `await article_loop.resume(root=root)` or
`await Orchestrator(root).resume(run_id)` through
`scripts/article_loop_command.py resume`. Do not reconstruct plans, alter
hashes, select a fake adapter, or bypass the state machine. Show the bounded
JSON result; if the run remains paused or awaits a child, report that fact and
end the turn without polling.
