---
description: Plan or run one sparse article-loop cycle with explicit safety gates.
argument-hint: "[--cycle-id N] [--run-id ID] [--live]"
---
# /article-run

This is a project-local M11 command. Load `AGENTS.md`, `AI_CONTEXT.md`, and
`.prime/agent/skills/article-loop/SKILL.md`. Validate the root, safe run/cycle
identifiers, and `$ARGUMENTS` before using them as data.

Dry-run is the default: invoke only
`await article_loop.run_cycle(root=root, cycle_id=cycle_id, dry_run=True)` (or
the local `scripts/article_loop_command.py run --dry-run` bridge). A live run
requires a separately authorized Prime session, an explicit
`PrimeRLMAdapter(rlm, agent_message, actor_role="M00", actor_id=..., depth=0)`,
the session command `/rlm-max-depth 2` without `--global`, and all local STOP,
state, and budget checks. Then call the existing `Orchestrator.run_cycle()`;
never infer authorization from JSON or choose `FakeRLMAdapter`.

Show only a bounded result. If children are admitted, report the handles and
end the turn; never poll, use `gather()`, create grandchildren from M00, or
claim completion before the durable state reaches its canonical terminal state.
