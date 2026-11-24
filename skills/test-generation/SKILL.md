---
name: test-generation
description: Writes meaningful unit and integration tests for existing or new code, targeting real behaviors, edge cases and uncovered branches, and keeps only tests that build, pass reliably, and add coverage or catch a real bug. Use when the user asks to add tests, write unit tests, increase coverage, test this function, backfill tests for legacy code, or make a change safer, and whenever you fix a bug (add the regression test first).
license: MIT
metadata:
  version: "1.0.0"
---

# Test Generation

Generated tests are easy to produce and easy to get wrong: tests that do not run,
tests that pass for the wrong reason, and five near-identical tests for one line.
Meta's TestGen-LLM made generated tests useful by filtering hard: in its
Instagram evaluation 75% of generated tests built, 57% passed reliably and
25% increased coverage, and only the survivors were offered to engineers. This
skill applies the same filters to every test you write.

## When to use

- Adding tests to untested or under-tested code; raising coverage for a module or a diff.
- Fixing a bug: write the failing regression test first, then fix.
- Characterizing legacy behavior before a refactor (see also `safe-refactoring`).
- **Not for:** end-to-end UI test suites or load tests (different tooling and trade-offs).

## Workflow

- [ ] 1. **Learn the house style.** Find the test framework, runner command, fixture and mocking conventions, and file naming by reading two or three existing test files next to the code. New tests must look like they belong.
- [ ] 2. **Find the gaps.** If a coverage report exists or is cheap to produce, run `python3 scripts/coverage_gaps.py <report>` (coverage.py JSON, LCOV, Cobertura XML or Go cover profile; `--changed-since main` to focus on a diff). Otherwise list the public behaviors of the unit under test by reading it.
- [ ] 3. **Plan behaviors, not lines.** Write a short list: each item is one behavior with its input class and expected outcome. Use [references/test-design.md](references/test-design.md) for boundary values, equivalence classes, error paths and property ideas. Ask the user to confirm the plan first if it has more than ~10 items or touches code you were not asked about.
- [ ] 4. **Write the tests**, one behavior per test, named for the behavior (`test_refund_rejected_after_30_days`). Arrange-Act-Assert. Assert on outputs and observable effects, not on private internals.
- [ ] 5. **Apply the filters** to every new test:
  1. **Builds/collects:** the runner picks it up.
  2. **Passes reliably:** run it 3 times (or with the framework's repeat option); flaky tests are deleted or fixed, never kept.
  3. **Adds value:** it covers new lines or branches (re-run coverage), or it fails when the behavior it checks is broken. Check the second by temporarily breaking the code (flip a condition, change a constant), confirming the test fails, then restoring. This is a one-off mutation test.
  4. **Not a duplicate:** drop tests whose coverage and assertions are subsumed by another test.
- [ ] 6. **Run the whole suite** to make sure nothing else broke.
- [ ] 7. **Report** using the template.

### What kind of test

| Code under test | Prefer |
|---|---|
| Pure function, parsers, validators, math | Table-driven unit tests plus a property-based test if the project already uses Hypothesis/fast-check/proptest |
| Code with I/O (DB, HTTP, files) | Integration test with the real thing locally (temp dir, SQLite/testcontainers, recorded HTTP) over heavy mocks |
| Code with time, randomness, concurrency | Inject the clock/seed; never `sleep` to wait for something |
| Legacy code with unclear behavior | Characterization tests that pin current behavior, labeled as such |

## Output template

```markdown
## Tests added
| Test | Behavior covered | Proved useful by |
|---|---|---|
| `test_parse_rejects_empty_header` | empty header raises `ParseError` | fails when the guard on `parser.py:41` is removed |
**Coverage:** `parser.py` 62% → 88% (lines 40-58, 77 now covered). Full suite: 214 passed.
**Not covered (and why):** `_legacy_decode` (dead code? asked user).
```

## Example

**Input:** "add tests for `slugify()`"
**Plan:** lowercase conversion; spaces and punctuation to single hyphens; trims leading/trailing hyphens; Unicode transliteration (`"Crème brûlée"` → `"creme-brulee"`); empty string returns `""`; idempotence property `slugify(slugify(s)) == slugify(s)`.

## Gotchas

- **A test that never failed proves nothing.** Do the break-it check in step 5.3 for anything non-trivial.
- **Do not change production code to make a test pass** unless you found a bug. If so, stop and tell the user: that is a bug report, not a test.
- **Over-mocking** tests the mocks. If you mock the thing being tested or every collaborator, write an integration test instead.
- **Snapshot tests** hide intent; use them only for large stable outputs, and review the snapshot content.
- **Asserting on current buggy behavior** in characterization tests is fine, but name the test so it reads as "current behavior" and tell the user.
- **Randomized tests need a fixed or printed seed** so failures can be reproduced.
