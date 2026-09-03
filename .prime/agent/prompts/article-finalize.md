---
description: Apply a previously authorized M10 decision through finalization.
argument-hint: "[--run-id ID] [--cycle-id N]"
---
# /article-finalize

This is a project-local M11 command. Load `AGENTS.md`, `AI_CONTEXT.md`, and
`.prime/agent/skills/article-loop/SKILL.md`; validate the root, safe run ID,
and non-negative cycle ID from `$ARGUMENTS`.

Invoke only `await article_loop.finalize(root=root)` or the existing
`finalize_decision(root, run_id, cycle_id=cycle_id)` through
`scripts/article_loop_command.py finalize`. Never reconstruct a challenger,
edit a champion, skip M10, infer approval, or accept a fake receipt. The M10
finalizer must revalidate every hash and precondition. Show the bounded JSON
receipt; after a crash report the durable recovery state and end the turn
without polling or starting M12.
