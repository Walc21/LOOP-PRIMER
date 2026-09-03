---
description: Request the durable STOP transition for one article-loop run.
argument-hint: "[--run-id ID]"
---
# /article-stop

This is a project-local M11 command. Load `AGENTS.md`, `AI_CONTEXT.md`, and
`.prime/agent/skills/article-loop/SKILL.md`; validate the root and optional
safe run ID from `$ARGUMENTS`.

Invoke only `await article_loop.stop(root=root)` or
`await Orchestrator(root).stop(run_id)` through
`scripts/article_loop_command.py stop`. Treat STOP as a durable safety boundary:
do not delete files, kill unrelated processes, retry in a loop, or claim that
unconfirmed work was refunded. Show only the bounded JSON result and end the
turn.
