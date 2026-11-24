# Performance Profiling

> Measure, profile, change one thing, and prove the speedup with statistics.

**Category:** Build · **Skill folder:** [`skills/performance-profiling/`](../../skills/performance-profiling/) · **Instructions:** [`SKILL.md`](../../skills/performance-profiling/SKILL.md)

## The problem it solves

Intuition about where time goes is usually wrong, and single timings lie: innocuous setup details can shift results enough to flip conclusions (Mytkowicz et al., ASPLOS 2009).

## When it activates

- "This is slow", "speed this up", timeouts, high memory
- Comparing two implementations
- Before claiming anything is faster

You can also call it directly: `/performance-profiling` (Claude Code, Antigravity) or `/devforge:performance-profiling` when installed as a Claude Code plugin.

## How it works

1. Define the target metric and the goal (ask if none)
2. Build a repeatable benchmark and baseline it with `bench.py`
3. Profile with the stack's profiler; classify the bottleneck
4. Pick the highest-payoff change (Amdahl ceiling)
5. Change one thing; verify correctness first
6. A/B with interleaved runs; claim a win only if the 95% CI excludes 1.0x

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/bench.py`](../../skills/performance-profiling/scripts/bench.py) | `python3 scripts/bench.py "old cmd" "new cmd" --runs 30` | Warmups, interleaved A/B runs, median/mean/stdev/p95/CV, bootstrap 95% CI on the speedup with a verdict |
| [`references/profilers.md`](../../skills/performance-profiling/references/profilers.md) | loaded on demand | Profiler commands for Python, Node, Go, Rust, JVM, .NET, Ruby, browser, SQL and Linux |

## What you get back

Target vs result, a version table (median, p95, CV, speedup with CI), the bottleneck found, the change, and the environment measured on.

## Try it

```text
dedupe.py takes forever on big inputs, make it faster but keep output identical
i rewrote it with a list comprehension, its way faster right?
```

More test prompts with graders: [`skills/performance-profiling/evals/`](../../skills/performance-profiling/evals/).

## Research basis

- Mytkowicz et al., *Producing Wrong Data Without Doing Anything Obviously Wrong!* (ASPLOS 2009)

---

[← All skills](../../README.md#whats-inside) · [← safe-refactoring](safe-refactoring.md) · [dependency-audit →](dependency-audit.md)
