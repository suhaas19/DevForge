---
name: bug-reproduction
description: Turns a vague bug report, flaky failure, or regression into a minimal, deterministic reproduction, then pins down the introducing commit with git bisect and shrinks failing inputs with delta debugging. Use when the user reports a bug, crash, wrong output, flaky or intermittent test, "it worked last week", a regression after an upgrade, or a large input that triggers a failure, before attempting any fix.
license: MIT
compatibility: Requires git for bisecting; scripts need Python 3.9+ and bash.
metadata:
  version: "1.0.0"
---

# Bug Reproduction

A fix without a reproduction is a guess. A reproduction that is minimal, fast and
deterministic usually makes the cause obvious, and it becomes the regression test.
This skill covers getting there: reproduce, make it deterministic, find *when* it
broke (git bisect), and shrink *what* breaks it (delta debugging, Zeller and
Hildebrandt 2002).

## When to use

- A bug report, crash, wrong result, or failing test whose cause is not yet known.
- "It used to work": regressions after a commit, merge, or dependency upgrade.
- Flaky or intermittent failures.
- A huge input (file, request, dataset) that triggers a failure.
- **Not for:** bugs whose cause is already known; go straight to the fix and the regression test.

## Workflow

- [ ] 1. **Write down the claim.** Expected vs actual behavior, exact error text, environment (versions, OS, config, data), and how often it happens. If the report lacks the expected behavior or a way to trigger it, ask the user for them before guessing.
- [ ] 2. **Reproduce it locally**, as close to the report as possible. Record the exact command. If you cannot reproduce after a reasonable effort, stop and report what you tried and what is different between your environment and theirs.
- [ ] 3. **Make it deterministic.** Run it 10-20 times. If it is intermittent, see the flaky table below and fix the source of nondeterminism (seed, clock, ordering, concurrency) until it fails every time, or measure a failure rate you can compare against.
- [ ] 4. **Turn it into an automated check** that exits 0 when the bug is absent and non-zero when present: ideally a failing test in the project's framework, otherwise a small script.
- [ ] 5. **If it is a regression, bisect.** Find a known-good ref (tag, release, last week's commit), then:
  `bash scripts/bisect_run.sh <good> <bad> -- <check command>`
  Set `BUILD="..."` for projects that need a build step; failed builds are skipped (exit 125) instead of being blamed. Read the first bad commit's diff; it usually names the cause.
- [ ] 6. **If the input is large, shrink it.** Write a check that exits 0 while the failure still happens (match the specific error, not just any non-zero exit), then:
  `python3 scripts/ddmin.py input.json --test "python3 repro.py {file} 2>&1 | grep -q 'KeyError: user_id'"`
  It writes `input.json.min`. Use `--unit char` for single-line inputs.
- [ ] 7. **Validate the reproduction**: it fails on the bad version, passes on the good one (or with a reverted suspect change), and runs in seconds.
- [ ] 8. **Report** with the template. Hand off to fixing only after this is done; keep the reproduction as the regression test.

### Flaky failure sources

| Symptom | Likely cause | How to confirm |
|---|---|---|
| Fails only in the full suite | shared state or test-order dependence | run the test alone, then with the previous test file; randomize order with a fixed seed |
| Fails only on CI | timing, time zone, locale, CPU count, missing env | run with `TZ=UTC`, `LANG=C`, limited CPUs, CI's env vars |
| Fails ~1 in N runs | race condition or unseeded randomness | loop it 100 times; add a fixed seed; run under a race detector (`go test -race`, TSAN) |
| Fails after a time or date | clock or date math | freeze the clock at the failing time |
| Fails with real network | external dependency | record and replay, or stub at the boundary |

## Output template

```markdown
## Reproduction: <one-line bug title>
**Expected:** ... **Actual:** ... (exact error)
**Reproduce:** `command` (fails 20/20 on <ref>, passes on <ref>)
**Introduced by:** `abc1234 <subject>` (bisected over N commits) | not a regression
**Minimal input:** `input.min` (from 3.1 MB to 48 bytes) | n/a
**Likely cause:** one or two sentences pointing at `file:line`, labeled as a hypothesis until a fix confirms it.
**Regression test:** `tests/test_x.py::test_...` (currently failing, as intended)
```

## Gotchas

- **Make the check specific.** `grep` for the exact error; otherwise ddmin and bisect happily converge on a *different* failure (a syntax error in the shrunk file, a build break).
- **Bisect needs a clean tree** and a check that runs on old commits too: old commits may lack your new test file, so keep the check outside the repo (e.g. `/tmp/check.sh`) or in a form that works on every commit.
- **Do not fix during reproduction.** Note suspicions, keep going until the reproduction is solid.
- **Flaky does not mean random.** "Retry until green" hides real races; find the cause or report the failure rate.
- **The check runs many times.** Never bisect or shrink with a command that writes to shared databases, sends messages, or deletes data.
