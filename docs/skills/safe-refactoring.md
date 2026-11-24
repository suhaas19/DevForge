# Safe Refactoring

> Change structure without changing behavior: fence it, take small steps, verify each one.

**Category:** Build · **Skill folder:** [`skills/safe-refactoring/`](../../skills/safe-refactoring/) · **Instructions:** [`SKILL.md`](../../skills/safe-refactoring/SKILL.md)

## The problem it solves

Large rewrites quietly change edge cases nobody tested. Fowler's discipline and Feathers' characterization tests are the reliable remedy.

## When it activates

- "Refactor", "clean up", "split this module", "remove duplication"
- Modernizing legacy code
- Preparing code for a feature

You can also call it directly: `/safe-refactoring` (Claude Code, Antigravity) or `/devforge:safe-refactoring` when installed as a Claude Code plugin.

## How it works

1. Define the goal and boundary; public interfaces stay unchanged unless agreed
2. Fence behavior with existing tests, characterization tests or a golden master
3. Plan named refactoring steps (Mikado method for tangled changes)
4. Execute one step at a time; green → commit, red → undo
5. Use LSP renames, codemods and formatters for mechanical edits
6. Final validation: tests, linters, types, golden master, public API diff

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/golden.py`](../../skills/safe-refactoring/scripts/golden.py) | `python3 scripts/golden.py record --cmd "python3 report.py {input}" --inputs 'samples/*.csv'` then `golden.py verify` | Records exit codes, stdout and stderr per input, scrubs timestamps and temp paths, and fails on any difference |
| [`references/catalog.md`](../../skills/safe-refactoring/references/catalog.md) | loaded on demand | Refactoring catalog, parallel change, Mikado method, strangler fig, branch by abstraction |

## What you get back

The goal, the behavior fence, each committed step, public API status and verification results.

## Try it

```text
report.py has one giant function, refactor it but the output must stay exactly the same
clean up pricing.py, dont change what it does
```

More test prompts with graders: [`skills/safe-refactoring/evals/`](../../skills/safe-refactoring/evals/).

## Research basis

- Fowler, *Refactoring* (2nd ed., 2018)
- Feathers, *Working Effectively with Legacy Code* (2004)

---

[← All skills](../../README.md#whats-inside) · [← bug-reproduction](bug-reproduction.md) · [performance-profiling →](performance-profiling.md)
