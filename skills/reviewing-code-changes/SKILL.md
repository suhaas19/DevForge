---
name: reviewing-code-changes
description: Reviews a diff, branch, or pull request for correctness, design, test coverage and maintainability, verifying each finding before reporting it and ranking findings by severity. Use when the user asks to review a PR, review my changes, look over a diff or commit, check code before merging, or give feedback on someone else's patch, and when you finish a substantial change of your own and want a self-review before handing it back.
license: MIT
metadata:
  version: "1.0.0"
---

# Reviewing Code Changes

A useful review finds the few things that would actually hurt (wrong behavior,
data loss, security holes, missing tests for risky logic) and says them clearly.
Studies of code review at Microsoft and Google found reviewers spend most of their
effort on understanding the change, and that comments on style rarely matter as
much as comments on behavior. Unverified "possible issue" lists waste the author's time, so
this skill makes you prove each finding before it goes in the report.

## When to use

- Reviewing a PR, branch, commit range, staged changes, or a pasted diff.
- Self-review of your own substantial change before telling the user it is done.
- **Not for:** a security-focused audit (use `secure-code-review`), or style-only formatting (run the formatter).

## Workflow

- [ ] 1. **Get the change set.** In a git repo run `python3 scripts/review_context.py` (or `--base <ref>`, `--staged`). It lists files riskiest first with flags such as security-sensitive paths, migrations, lockfiles, deleted tests, debug output, TODOs, and "source changed but no tests changed". For a pasted diff, read it directly.
- [ ] 2. **Understand intent before judging.** Read the PR description, linked issue, and commit messages. If intent is unclear and the change is large, ask the user what the change is supposed to do before reviewing line by line.
- [ ] 3. **Read the flagged files first, in full context.** Open the surrounding code, not just the hunk: callers, the function's other branches, the tests.
- [ ] 4. **Check each dimension** in [references/checklist.md](references/checklist.md): correctness and edge cases, error handling, concurrency, data and migrations, API compatibility, security basics, performance, tests, readability.
- [ ] 5. **Verify every candidate finding.** For each one, do at least one of: point to the exact line and the input that breaks it; run the relevant test or a quick script; find the caller that relies on the old behavior. Drop findings you cannot support, or downgrade them to a question.
- [ ] 6. **Run the tests** for the touched area when you can (`repo_map.py` from `codebase-onboarding` or the CI config tells you how). A red test is the strongest finding there is.
- [ ] 7. **Write the report** with the template below, most severe first. Validate before sending: every finding has a file:line and a concrete consequence.

### Severity

| Level | Meaning | Examples |
|---|---|---|
| **Blocker** | Must fix before merge | wrong result, crash path, data loss, auth bypass, broken migration |
| **Major** | Should fix before merge | missing test for risky logic, unhandled error path, race, breaking API change without notice |
| **Minor** | Worth fixing, not blocking | unclear naming, duplicated logic, missing log context |
| **Nit** | Optional | style the formatter does not catch; label it as optional |
| **Question** | You are not sure | ask instead of asserting |

## Output template

```markdown
## Review: <PR title or range>
**Verdict:** approve | approve with comments | request changes
**Summary:** 2-3 sentences: what the change does and the overall assessment.

### Blockers
1. `path/file.py:42`: <what is wrong>. **Why it matters:** <consequence>. **Evidence:** <failing input / test output / caller>. **Suggested fix:** <concrete change>.
### Major
### Minor and nits
### Questions
### What is good
- One or two specific things done well (helps the author know what to keep).
```

Omit empty sections. Keep nits to five or fewer; if there are more, say "several style nits; consider running <formatter>".

## Example

**Input:** "review my branch before I open the PR"
**Good finding:** "`billing/invoice.py:88`: `round(total, 2)` runs before tax is added, so a 3-item order of $0.335 each is billed $1.00 instead of $1.01. **Evidence:** `python -c 'from billing.invoice import total; print(total([0.335]*3))'` prints `1.0`. **Fix:** round once, after tax, using `Decimal` with `ROUND_HALF_UP`."
**Bad finding:** "Consider adding error handling." (no location, no consequence, no evidence)

## Gotchas

- **Review the code, not the diff alone.** A hunk that looks fine can break a caller three files away; search for usages of anything whose signature or behavior changed.
- **Deleted tests and loosened assertions** are easy to miss in a diff and are among the most important things to question.
- **Do not rewrite the PR.** Suggest the smallest fix; a large redesign belongs in a separate conversation with the user.
- **Generated files and lockfiles:** skim for unexpected new dependencies (check them with `dependency-audit`), do not review line by line.
- **Your own code gets the same bar.** On self-review, actually run step 5; do not just restate what you did.
