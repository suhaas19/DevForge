# Codebase Onboarding

> Get a factual map of an unfamiliar repository before touching it.

**Category:** Understand · **Skill folder:** [`skills/codebase-onboarding/`](../../skills/codebase-onboarding/) · **Instructions:** [`SKILL.md`](../../skills/codebase-onboarding/SKILL.md)

## The problem it solves

Most bad changes in unfamiliar code come from editing the wrong place or ignoring a convention the repo already has. Coding-agent research (SWE-agent, Agentless) finds that locating the right files is most of the work.

## When it activates

- "How does this repo work?" / "onboard me"
- "Where is password reset handled?"
- Before planning a change in code the agent has not read

You can also call it directly: `/codebase-onboarding` (Claude Code, Antigravity) or `/devforge:codebase-onboarding` when installed as a Claude Code plugin.

## How it works

1. Run `repo_map.py` for languages, layout, build tooling, likely commands, entry points, tests, CI, docs and git hotspots
2. Read agent instruction files and human docs (AGENTS.md, README, CONTRIBUTING) first
3. Confirm build/test commands against CI config; optionally run the tests once for a baseline
4. Trace one real request or command path end to end
5. Extract conventions (errors, logging, config, tests) with file references
6. Write a short orientation doc, citing only paths that exist

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/repo_map.py`](../../skills/codebase-onboarding/scripts/repo_map.py) | `python3 scripts/repo_map.py . [--json] [--top 10]` | Respects .gitignore; detects npm/pnpm/yarn scripts, pytest, go, cargo, maven, gradle, make/just targets; ranks change hotspots from git history |

## What you get back

An `ORIENTATION.md`-style doc: what it is, layout, verified build/test commands, request/data flow with file:line hops, conventions, hotspots, open questions.

## Try it

```text
i just cloned this repo for my new job, write me an orientation doc i can keep
where does this project handle password resets? dont change anything
```

More test prompts with graders: [`skills/codebase-onboarding/evals/`](../../skills/codebase-onboarding/evals/).

## Research basis

- Yang et al., *SWE-agent* (NeurIPS 2024)
- Xia et al., *Agentless* (2024)

---

[← All skills](../../README.md#whats-inside) · [reviewing-code-changes →](reviewing-code-changes.md)
