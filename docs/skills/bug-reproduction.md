# Bug Reproduction

> Minimal, deterministic reproductions, the introducing commit, and the smallest failing input.

**Category:** Understand · **Skill folder:** [`skills/bug-reproduction/`](../../skills/bug-reproduction/) · **Instructions:** [`SKILL.md`](../../skills/bug-reproduction/SKILL.md)

## The problem it solves

A fix without a reproduction is a guess. A minimal, fast, deterministic reproduction usually makes the cause obvious and becomes the regression test.

## When it activates

- Bug reports, crashes, wrong output
- "It worked last week" / regressions after upgrades
- Flaky or intermittent tests
- Huge inputs that trigger a failure

You can also call it directly: `/bug-reproduction` (Claude Code, Antigravity) or `/devforge:bug-reproduction` when installed as a Claude Code plugin.

## How it works

1. Write down expected vs actual, exact error and environment (ask for missing pieces)
2. Reproduce locally and record the command
3. Make it deterministic (seeds, clocks, ordering, concurrency)
4. Turn it into an automated check
5. Bisect regressions with `bisect_run.sh`
6. Shrink large inputs with `ddmin.py`
7. Validate: fails on bad, passes on good, runs in seconds

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/bisect_run.sh`](../../skills/bug-reproduction/scripts/bisect_run.sh) | `bash scripts/bisect_run.sh v1.2.0 HEAD -- pytest -x tests/test_x.py` | Wraps `git bisect run`; build failures become 'skip' (exit 125); always resets bisect state |
| [`scripts/ddmin.py`](../../skills/bug-reproduction/scripts/ddmin.py) | `python3 scripts/ddmin.py input.json --test "python3 repro.py {file} 2>&1 \| grep -q KeyError"` | Zeller's delta-debugging minimizer over lines, tokens or characters |

## What you get back

Expected/actual, a reproduction command with its failure rate, the introducing commit, the minimal input, a labeled hypothesis and a failing regression test.

## Try it

```text
parse_orders.py crashes with a KeyError on orders.json, i need the smallest input that still triggers it
greet.py worked at v1.0 but prints something else now, which commit broke it?
```

More test prompts with graders: [`skills/bug-reproduction/evals/`](../../skills/bug-reproduction/evals/).

## Research basis

- Zeller & Hildebrandt, *Simplifying and Isolating Failure-Inducing Input* (IEEE TSE 2002)

---

[← All skills](../../README.md#whats-inside) · [← test-generation](test-generation.md) · [safe-refactoring →](safe-refactoring.md)
