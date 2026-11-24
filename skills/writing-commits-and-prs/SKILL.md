---
name: writing-commits-and-prs
description: Writes clear Conventional Commits messages and pull request descriptions from the actual diff, stating why the change was made, how it was tested, and any risk or breaking change, and splits mixed changes into focused commits. Use when the user asks to commit, write a commit message, squash, open or describe a PR, write release notes from commits, or clean up git history, and whenever you are about to commit work you did.
license: MIT
metadata:
  version: "1.0.0"
---

# Writing Commits and PRs

A commit message is read far more often than it is written: in `git blame`, in
bisect results, in release notes, in review. The diff already says *what*
changed. The message must say *why*, plus anything the diff cannot show: how it
was tested, what it risks, what reviewers should look at. This skill uses the
Conventional Commits format so history is machine-readable (changelogs,
semantic versioning) and human-scannable.

## When to use

- Committing work, writing or fixing a commit message, squashing, rewording.
- Opening a PR or writing its description; drafting release notes from a commit range.
- **Not for:** reviewing the code itself (use `reviewing-code-changes`).

## Workflow

- [ ] 1. **Look at what is actually staged.** `python3 scripts/commit_helper.py summary --staged` (or `--base main` for a whole branch) lists files, line counts, a suggested type and scope, whether tests were touched, and paths that hint at breaking changes.
- [ ] 2. **Split if mixed.** If the diff contains unrelated changes (a refactor and a feature, a formatting sweep and a fix), stage them separately (`git add -p`) and commit each on its own. Ask the user before rewriting history that has already been pushed.
- [ ] 3. **Find the why.** From the conversation, the issue, or the user. If the motivation is unknown, ask; do not invent one. "Update X" with no reason is the most common bad message.
- [ ] 4. **Write the message** in the format below and check it: `python3 scripts/commit_helper.py check "<message>"` (or `--file`). Fix every complaint.
- [ ] 5. **For a PR**, write the description with the PR template below, filling testing and risk honestly ("not tested on Windows" is useful information).
- [ ] 6. **Validate:** the message matches the staged diff (nothing described that is not in it, nothing significant in it left undescribed).
- [ ] 7. Optional: install the checker as a hook for the user: `python3 scripts/commit_helper.py install-hook`. Ask the user first; it refuses to overwrite an existing hook.

### Commit message format

```
<type>(<scope>): <imperative summary, lower case, no period, ≤ 50-72 chars>

<body: why this change, what problem it solves, notable decisions or
alternatives rejected; wrap at ~72 chars>

<footers: Fixes #123 | Refs #456 | BREAKING CHANGE: <what breaks and how to migrate> | Co-authored-by: ...>
```

| Type | Use for |
|---|---|
| `feat` | new user-facing capability (minor version bump) |
| `fix` | bug fix (patch bump) |
| `perf` | performance improvement without behavior change |
| `refactor` | restructuring without behavior change |
| `test` | adding or fixing tests only |
| `docs` | documentation only |
| `build` / `ci` | build system, dependencies / CI configuration |
| `chore` | maintenance that fits nowhere else (keep rare) |
| `revert` | reverting a previous commit (include its hash) |

Add `!` after the type/scope (`feat(api)!:`) and a `BREAKING CHANGE:` footer for incompatible changes.

## PR description template

```markdown
## Why
The problem or goal, with a link to the issue.
## What changed
- Bullet per logical change, pointing reviewers to the important files.
## How it was tested
- Commands run and results; manual checks; what was NOT tested.
## Risk and rollout
- Blast radius, migrations, feature flags, how to roll back.
## Screenshots / output (if UI or CLI behavior changed)
```

## Example

Diff: adds retry with backoff to the payment client and a test.

```
fix(payments): retry transient 5xx from the card processor

The processor returns 502/503 during its nightly failover, which failed
~0.4% of checkouts between 02:00 and 02:10 UTC. Retry up to 3 times with
jittered exponential backoff, only for idempotent capture requests that
carry an idempotency key, so a retry can never double-charge.

Fixes #812
```

## Gotchas

- **Do not describe the diff line by line**; reviewers can read it. Describe intent and consequences.
- **"WIP", "fix stuff", "address review"** are not messages. Squash or reword before merge.
- **Never put secrets, customer data, or internal hostnames in messages**; history is forever and often public.
- **Generated attribution:** follow the project's or user's convention for co-author or AI-assistance trailers; do not add or remove them on your own.
- **Check before amending or force-pushing** anything that might already be shared; ask the user first.
