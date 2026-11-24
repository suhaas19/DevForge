# Test Generation

> Tests that build, pass reliably and prove they would catch a bug.

**Category:** Build · **Skill folder:** [`skills/test-generation/`](../../skills/test-generation/) · **Instructions:** [`SKILL.md`](../../skills/test-generation/SKILL.md)

## The problem it solves

Generated tests are easy to produce and easy to get wrong. Meta's TestGen-LLM made them useful by filtering hard: in its Instagram evaluation 75% built, 57% passed reliably and 25% raised coverage, and only survivors were kept.

## When it activates

- "Add tests", "increase coverage", "test this function"
- Backfilling tests for legacy code
- Fixing a bug (regression test first)

You can also call it directly: `/test-generation` (Claude Code, Antigravity) or `/devforge:test-generation` when installed as a Claude Code plugin.

## How it works

1. Learn the house test style from existing tests
2. Find gaps with `coverage_gaps.py` or by listing public behaviors
3. Plan behaviors (boundaries, error paths, properties), not lines
4. Write one behavior per test, Arrange-Act-Assert
5. Filter: builds, passes 3x, adds coverage or fails when the code is broken (one-off mutation check), not a duplicate
6. Run the whole suite and report coverage before/after

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/coverage_gaps.py`](../../skills/test-generation/scripts/coverage_gaps.py) | `python3 scripts/coverage_gaps.py coverage.json [--changed-since main]` | Reads coverage.py JSON, LCOV, Cobertura XML and Go cover profiles; ranks uncovered line ranges and partial branches |
| [`references/test-design.md`](../../skills/test-generation/references/test-design.md) | loaded on demand | Boundary values, equivalence classes, properties, test doubles, flakiness sources |

## What you get back

A table of tests added, the behavior each covers, and how it was proved useful, plus coverage before and after.

## Try it

```text
add unit tests for slugify in textutils.py, we use pytest
feb 29 2024 is rejected as invalid, add a regression test that shows the bug, dont fix it yet
```

More test prompts with graders: [`skills/test-generation/evals/`](../../skills/test-generation/evals/).

## Research basis

- Alshahwan et al., *Automated Unit Test Improvement using Large Language Models at Meta* (FSE 2024)

---

[← All skills](../../README.md#whats-inside) · [← secure-code-review](secure-code-review.md) · [bug-reproduction →](bug-reproduction.md)
