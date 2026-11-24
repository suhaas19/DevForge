---
name: safe-refactoring
description: Restructures code without changing its behavior, by pinning current behavior with characterization or golden-master tests first and then moving in small, verified, individually revertible steps. Use when the user asks to refactor, clean up, restructure, extract, rename across files, split a large module, remove duplication, modernize legacy code, or "make this more maintainable", especially in code with weak or no test coverage.
license: MIT
metadata:
  version: "1.0.0"
---

# Safe Refactoring

Refactoring means changing structure while keeping behavior identical. The risk is
the "while keeping behavior" part: large rewrites by agents (and people) quietly
change edge cases nobody tested. The remedy is old and reliable (Fowler's
refactoring discipline, Feathers' characterization tests): fence the behavior,
take small steps, verify after each one.

## When to use

- Requests to refactor, clean up, extract functions/classes/modules, rename widely, split files, deduplicate, or modernize syntax and APIs.
- Preparing code for a feature ("make the change easy, then make the easy change").
- **Not for:** changes that intentionally alter behavior. Split those: refactor first (behavior-preserving), then change behavior in a separate step and commit.

## Workflow

- [ ] 1. **Define the goal and the boundary.** What should be better afterwards (one sentence) and which files/APIs are in scope. Public interfaces (exported functions, endpoints, CLI flags, config keys, DB schema) stay the same unless the user agrees to change them. Ask before touching anything outside the boundary.
- [ ] 2. **Fence the behavior.** Run the existing tests and record the baseline (pass/fail counts). If the code in scope is not well covered:
  - add characterization tests for its public behavior (see `test-generation`), or
  - for CLIs, scripts and batch jobs, record a golden master: `python3 scripts/golden.py record --cmd "python3 report.py {input}" --inputs 'samples/*.csv'`. Use `--scrub REGEX` for timestamps or other volatile output.
- [ ] 3. **Plan small steps.** List the sequence of named refactorings from [references/catalog.md](references/catalog.md) (extract function, move, rename, introduce parameter object, replace conditional with polymorphism...). Each step should leave the code compiling and passing. For a tangled change, use the Mikado method in the catalog to find the order.
- [ ] 4. **Execute one step at a time.** After each step: run the fast tests (and `python3 scripts/golden.py verify` if you recorded one). Green → commit (or checkpoint) with a message like `refactor: extract parse_header from load`. Red → undo that step, do not debug forward.
- [ ] 5. **Use tools for mechanical changes** when available: IDE/LSP rename, `gofmt -r`, `comby`, codemods, `sed` on a precise pattern followed by a review of every hunk. They are more reliable than hand-editing many files.
- [ ] 6. **Final validation:** full test suite, linters, type checker, golden master all match the baseline. Diff the public API surface (exports, routes) before vs after.
- [ ] 7. **Report** with the template; clean up `.golden/` unless the user wants to keep it as a regression check.

### Step size

| Code has... | Step size |
|---|---|
| Good tests, static types | Larger steps are fine; still commit per refactoring |
| Few tests | Characterize first, then very small steps |
| Dynamic code paths (reflection, string dispatch, templates, serialization) | Search for string references before renaming; add tests for those paths |
| Concurrency or performance sensitivity | Benchmark before and after (`performance-profiling`) |

## Output template

```markdown
## Refactor: <goal>
**Behavior fence:** existing tests (N) + 6 new characterization tests + golden master (14 cases)
**Steps (each committed, all green):**
1. `refactor: extract validate_row from import_csv`
2. ...
**Public API:** unchanged (or: changes agreed with user: ...)
**Verification:** tests 214/214, golden 14/14 identical, mypy clean.
**Follow-ups not done:** ...
```

## Gotchas

- **Never mix refactoring and behavior change in one step.** If you find a bug mid-refactor, write it down, finish or revert the step, and ask the user how to handle the bug.
- **"While I'm here" scope creep** is the main way refactors break things. Stay inside the boundary from step 1.
- **Renames miss dynamic references:** string-based lookups, dependency-injection names, serialized field names, SQL, templates, docs, and other repositories that import this one.
- **Formatting churn hides real changes.** Run the formatter as its own commit first, or not at all.
- **Deleting "dead" code:** confirm it is unused (search, coverage, logs) and check for reflection or external callers before removing.
- **Golden masters pin bugs too.** That is intended: behavior is preserved, bugs included. Fix them later, deliberately.
