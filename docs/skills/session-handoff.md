# Session Handoff

> A compact HANDOFF.md so a fresh session, teammate or agent can resume immediately.

**Category:** Ship · **Skill folder:** [`skills/session-handoff/`](../../skills/session-handoff/) · **Instructions:** [`SKILL.md`](../../skills/session-handoff/SKILL.md)

## The problem it solves

Long contexts degrade: Chroma's Context Rot study found reliability falls with input length in all 18 models tested. A short, accurate brief beats a bloated context, if it keeps decisions, reasons and dead ends.

## When it activates

- "Wrap up", "continue tomorrow", "new chat"
- Context getting long or about to compact
- Delegating to another agent

You can also call it directly: `/session-handoff` (Claude Code, Antigravity) or `/devforge:session-handoff` when installed as a Claude Code plugin.

## How it works

1. Collect git state with `handoff_context.py`
2. Record the last verification results (re-run stale ones)
3. Write goal, decisions with reasons, dead ends, next steps, open questions
4. Compress to under ~150 lines
5. Save HANDOFF.md (ask before committing it)
6. Cold-read it: could you start the next step without asking?

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/handoff_context.py`](../../skills/session-handoff/scripts/handoff_context.py) | `python3 scripts/handoff_context.py [--json]` | Branch, commits on branch, uncommitted files, stashes, TODOs added, recently changed files |
| [`assets/HANDOFF_TEMPLATE.md`](../../skills/session-handoff/assets/HANDOFF_TEMPLATE.md) | template | Goal, status, state, decisions, dead ends, next steps, questions, gotchas |

## What you get back

HANDOFF.md, plus the line to start the next session: "Read HANDOFF.md and continue from Next steps."

## Try it

```text
im done for today, set things up so tomorrows session can pick up right away
context is getting long, write a handoff so a fresh agent can take over
```

More test prompts with graders: [`skills/session-handoff/evals/`](../../skills/session-handoff/evals/).

## Research basis

- Hong, Troynikov & Huber, *Context Rot* (Chroma, 2025)

---

[← All skills](../../README.md#whats-inside) · [← prompt-injection-defense](prompt-injection-defense.md) · [skill-authoring →](skill-authoring.md)
