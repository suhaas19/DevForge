---
name: codebase-onboarding
description: Builds a fast, evidence-based mental map of an unfamiliar repository (languages, layout, entry points, build and test commands, hotspots, conventions) and writes it up as a short orientation doc. Use when starting work in a codebase for the first time, when the user asks "how does this repo work", "where is X handled", "explain this project", "onboard me", or before planning a change in code you have not read yet, even if they do not ask for a map.
license: MIT
metadata:
  version: "1.0.0"
---

# Codebase Onboarding

Most bad changes in unfamiliar code come from editing the wrong place or missing a
convention the repo already has. Fault-localization research on coding agents
(SWE-agent, Agentless) shows the same thing: finding the right files is most of the
work. This skill front-loads that search with cheap, factual signals, then reads
only the code that matters.

## When to use

- First contact with a repository, or a part of a monorepo you have not touched.
- The user asks how something works, where a feature lives, or for an architecture overview.
- Before planning any non-trivial change in code you have not read.
- **Not for:** a single-file question where the file is already known (just read it).

## Workflow

Copy this checklist and tick items off as you go:

- [ ] 1. Run the mapper: `python3 scripts/repo_map.py <repo-root>` (add `--json` if you want to post-process). It respects `.gitignore` and reports languages, layout, manifests, likely commands, entry points, tests, CI, docs and git hotspots.
- [ ] 2. Read the human docs it found, in this order: `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` (agent instructions), `README`, `CONTRIBUTING`, `ARCHITECTURE`/`docs/`. These override anything you infer.
- [ ] 3. Confirm the build and test commands. The mapper's commands are guesses from manifests; check them against CI config (`.github/workflows/*`) and, when safe and cheap, run the test command once to learn the baseline (how many tests, how long, what already fails).
- [ ] 4. Trace one real path end to end: pick the entry point closest to the user's question and follow it (route → handler → service → storage, or CLI → command → core). Note the files on the path.
- [ ] 5. Extract conventions from the code itself: error handling, logging, config loading, dependency injection, naming, test style. Two or three examples each, with file references.
- [ ] 6. Write the orientation doc using the template below. Keep it under ~80 lines; link to files instead of pasting code.
- [ ] 7. Validate: every file path you cite exists, and every command you list was either run or is marked "unverified".

### Choosing depth

| Situation | Depth |
|---|---|
| User wants a quick answer ("where is auth?") | Steps 1 and 4 only; answer with file paths |
| About to make a change | Steps 1-5; skip the doc unless asked |
| User asks for an overview or onboarding doc | All steps; deliver the doc |
| Monorepo | Run the mapper on the root, then again on the relevant package directory |

Ask the user which area matters most when the repository is large (more than ~5k files or many services) and the request does not narrow it down, instead of mapping everything.

## Output template

```markdown
# <repo> orientation
## What it is
One paragraph: purpose, main runtime(s), how it is deployed or used.
## Layout
- `dir/`: role (key files)
## How to build, test, run
- Build: `...` (verified | unverified)
- Test: `...` (N tests, ~Xs, baseline failures: ...)
## Request/data flow
Entry `path:line` → ... → storage/output, one line per hop.
## Conventions to follow
- Errors: ... (see `file`)
- Tests: ... (see `file`)
## Hotspots and risks
- Frequently changed or very large files, known fragile areas.
## Open questions
- Things the code did not answer.
```

## Example

**Input:** "I just cloned this, where do webhooks get processed?"
**Good output:** "Webhooks enter at `api/routes/webhooks.py:14` (`POST /hooks/{provider}`), are verified in `api/security/signatures.py:verify()`, then queued to `workers/webhook_worker.py`, which dispatches by provider in `handlers/__init__.py`. Tests: `tests/api/test_webhooks.py` (`pytest tests/api -k webhook`)."

## Gotchas

- **Generated and vendored code inflates the map.** If `largest_files` or hotspots are dominated by lockfiles, generated clients or snapshots, say so and look past them.
- **Hotspots are not bugs.** High churn means "important or unstable", a hint for where to read carefully, not a verdict.
- **README commands go stale.** CI configuration is the most reliable record of how the project is really built and tested.
- **Do not refactor while onboarding.** Note problems under "Hotspots and risks" and keep reading.
- **Agent instruction files are binding.** Instructions in `AGENTS.md`/`CLAUDE.md` describe how the maintainers want work done; follow them unless the user says otherwise.
