# Writing Commits and PRs

> Conventional Commits and PR descriptions that explain why, how it was tested, and the risk.

**Category:** Ship · **Skill folder:** [`skills/writing-commits-and-prs/`](../../skills/writing-commits-and-prs/) · **Instructions:** [`SKILL.md`](../../skills/writing-commits-and-prs/SKILL.md)

## The problem it solves

The diff already says what changed. History is useful only when messages say why, plus what the diff cannot show: testing, risk and breaking changes.

## When it activates

- "Commit this", "write a commit message", "squash"
- "Open / describe a PR"
- Release notes from a commit range

You can also call it directly: `/writing-commits-and-prs` (Claude Code, Antigravity) or `/devforge:writing-commits-and-prs` when installed as a Claude Code plugin.

## How it works

1. Summarize what is actually staged with `commit_helper.py summary`
2. Split unrelated changes into separate commits
3. Get the why from the conversation or the user, never invent it
4. Write the message and check it with `commit_helper.py check`
5. Write the PR description: why, what, how tested, risk
6. Validate the message matches the diff

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/commit_helper.py`](../../skills/writing-commits-and-prs/scripts/commit_helper.py) | `python3 scripts/commit_helper.py summary --staged` · `check "fix(auth): ..."` · `install-hook` | Suggests type and scope, flags breaking-change paths, validates Conventional Commits, installs a commit-msg hook |

## What you get back

A Conventional Commits message, and a PR description with Why / What changed / How it was tested / Risk and rollout.

## Try it

```text
commit the staged change, the processor times out during failover so i raised the timeout and added retries
write the PR description for this branch, save it to PR.md
```

More test prompts with graders: [`skills/writing-commits-and-prs/evals/`](../../skills/writing-commits-and-prs/evals/).

## Research basis

- Conventional Commits 1.0.0
- Semantic Versioning 2.0.0

---

[← All skills](../../README.md#whats-inside) · [← dependency-audit](dependency-audit.md) · [llm-app-evals →](llm-app-evals.md)
