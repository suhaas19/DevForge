# Reviewing Code Changes

> Code review that reports only verified findings, ranked by severity.

**Category:** Check · **Skill folder:** [`skills/reviewing-code-changes/`](../../skills/reviewing-code-changes/) · **Instructions:** [`SKILL.md`](../../skills/reviewing-code-changes/SKILL.md)

## The problem it solves

Reviews full of unverified "possible issues" waste the author's time and bury the real bugs. Studies at Microsoft and Google found understanding the change is most of a reviewer's effort, and behavior matters far more than style.

## When it activates

- "Review my branch / this PR / this diff"
- "Check this before I merge"
- Self-review after the agent finishes a substantial change

You can also call it directly: `/reviewing-code-changes` (Claude Code, Antigravity) or `/devforge:reviewing-code-changes` when installed as a Claude Code plugin.

## How it works

1. Run `review_context.py` to list changed files riskiest-first with flags
2. Understand intent from the PR description, issue and commits (ask if unclear)
3. Read flagged files in full context: callers, other branches, tests
4. Walk the checklist: correctness, errors, concurrency, data/migrations, API compatibility, security, performance, tests, readability
5. Verify every candidate finding with a failing input, a test run or a caller
6. Report Blocker / Major / Minor / Nit / Question with file:line, consequence, evidence and fix

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/review_context.py`](../../skills/reviewing-code-changes/scripts/review_context.py) | `python3 scripts/review_context.py [--base main] [--staged] [--json]` | Flags security-sensitive paths, migrations, lockfiles, deleted tests, debug output, TODOs, possible secrets, huge hunks, and source changed without tests |
| [`references/checklist.md`](../../skills/reviewing-code-changes/references/checklist.md) | loaded on demand | Review checklist by dimension |

## What you get back

A review with a verdict (approve / approve with comments / request changes), findings by severity with evidence, and what is good.

## Try it

```text
can u review this diff before i merge it? its the new invoice total logic
quick review of my branch pls, its just cleanup
```

More test prompts with graders: [`skills/reviewing-code-changes/evals/`](../../skills/reviewing-code-changes/evals/).

## Research basis

- Bacchelli & Bird, *Expectations, Outcomes, and Challenges of Modern Code Review* (ICSE 2013)
- Sadowski et al., *Modern Code Review: A Case Study at Google* (ICSE-SEIP 2018)

---

[← All skills](../../README.md#whats-inside) · [← codebase-onboarding](codebase-onboarding.md) · [secure-code-review →](secure-code-review.md)
