# About DevForge

> Research-backed engineering skills for AI coding agents, in one portable repository.

**Contents:** [Mission](#mission) · [Who it's for](#who-its-for) · [What makes it different](#what-makes-it-different) · [Anatomy of a skill](#anatomy-of-a-skill) · [The skills, section by section](#the-skills-section-by-section) · [Compatibility](#compatibility) · [Quality and testing](#quality-and-testing) · [Security model](#security-model) · [Roadmap](#roadmap) · [FAQ](#faq) · [Author](#author)

---

## Mission

Coding agents are fast, but speed without discipline produces confident mistakes: reviews full of unverified "possible issues", security reports that flag safe code, tests that never fail, benchmarks run once, packages that do not exist. Experienced engineers avoid these with well-known procedures. DevForge packages those procedures as **Agent Skills** that any compatible agent loads on demand, so the discipline shows up automatically whenever the task calls for it.

## Who it's for

| You are... | DevForge gives you... |
|---|---|
| **A developer using Claude Code, Antigravity, Codex, Cursor, Gemini CLI or Copilot** | Better reviews, tests, debugging, refactors and commit history with no extra prompting |
| **A team lead** | One install (`--project`) that gives every teammate's agent the same review, security and commit standards |
| **A security or platform engineer** | Traced, low-false-positive security reviews and slopsquatting protection before packages are installed |
| **An AI/LLM app builder** | Evals with confidence intervals and prompt-injection threat modeling for agents and RAG |
| **A skill author** | A template, scaffolder, linter and eval layout for publishing your own collection |

## What makes it different

1. **Grounded in evidence.** Every skill's procedure comes from published software-engineering research or long-standing practice, and the format follows the 2026 empirical studies of agent skills. See [RESEARCH.md](RESEARCH.md).
2. **Tools, not just text.** 16 tested scripts do the deterministic work (scanning, parsing, bisecting, shrinking, timing, registry checks), so the agent spends its reasoning on judgment.
3. **Verify before report.** Each skill ends with a validation step; findings come with evidence the reader can re-run.
4. **Focused and short.** One job per skill and SKILL.md files kept compact, because research shows focused skills beat comprehensive ones.
5. **Portable.** Plain Agent Skills plus native manifests for five plugin systems, all generated from one metadata file.
6. **Safe to install.** Standard-library scripts, no hooks, no telemetry, and CI that rejects hidden instructions or exfiltration patterns.

## Anatomy of a skill

```text
skills/secure-code-review/
├── SKILL.md            ← name + description (always visible to the agent) and the procedure (loaded on use)
├── scripts/            ← secret_scan.py, find_sinks.py: run, never loaded into context
├── references/         ← checklist.md: loaded only when the procedure points to it
└── evals/              ← realistic prompts, graders and fixture files
```

Every SKILL.md follows the same structure, chosen to avoid the most common quality problems found in real skills:

| Section | Why it is there |
|---|---|
| **Description** (third person: what + when + keywords) | It is the only thing the agent sees when deciding to load the skill |
| **Why** | Models follow instructions better when they know the reason |
| **When to use / Not for** | Keeps skills from competing with each other |
| **Checklist workflow** | Progress tracking and a guard against skipped steps |
| **Decision table** | A default for each situation instead of an "option buffet" |
| **Ask-the-user points** | The agent stops before irreversible or out-of-scope actions |
| **Output template + example** | Predictable, comparable results |
| **Gotchas** | The mistakes agents actually make, called out explicitly |

## The skills, section by section

### 1. Understand: know the code and the bug before changing anything

**[codebase-onboarding](skills/codebase-onboarding.md).** Maps an unfamiliar repository with `repo_map.py`: languages, layout, manifests, likely build/test commands, entry points, tests, CI, docs, and change hotspots from git history. It reads the agent instruction files and human docs, confirms commands against CI, traces one real request path, and writes a short orientation doc citing only paths that exist.

**[bug-reproduction](skills/bug-reproduction.md).** Turns a bug report into a reproduction that fails every time and runs in seconds. Regressions are bisected with `bisect_run.sh` (build failures are skipped, never blamed); large failing inputs are shrunk with `ddmin.py`, an implementation of Zeller's delta debugging. The result becomes the regression test.

### 2. Build: change code safely

**[test-generation](skills/test-generation.md).** Plans behaviors rather than lines, writes tests in the project's style, and applies Meta-style filters: each test must build, pass three times, and either add coverage (measured with `coverage_gaps.py`) or fail when the code under test is deliberately broken.

**[safe-refactoring](skills/safe-refactoring.md).** Fences current behavior with characterization tests or a golden master (`golden.py` records and verifies outputs per input), then applies named refactorings one committed step at a time. Bugs found along the way are reported, not silently fixed.

**[performance-profiling](skills/performance-profiling.md).** Defines a target, baselines it, profiles with the right tool for the stack, changes one thing, and compares with `bench.py`: interleaved A/B runs and a bootstrap 95% confidence interval. A win is claimed only when the interval excludes "no difference".

### 3. Check: catch problems before they merge

**[reviewing-code-changes](skills/reviewing-code-changes.md).** `review_context.py` ranks changed files by risk (security-sensitive paths, migrations, lockfiles, deleted tests, debug output, source changed without tests). The agent reads flagged code in context, walks a review checklist, and proves each finding before reporting it as Blocker, Major, Minor, Nit or Question.

**[secure-code-review](skills/secure-code-review.md).** `secret_scan.py` (redacted output) and `find_sinks.py` (11 vulnerability categories, 7 languages) produce candidates. Only candidates with a traced source → sink path and no effective sanitization become findings, each with CWE, severity, a safe proof and a fix. Dismissed candidates are listed for transparency.

**[dependency-audit](skills/dependency-audit.md).** Before any new package is installed, `verify_package.py` checks PyPI or npm for existence, age, release history, source repository and typosquat distance, blocking hallucinated names. `audit_deps.py` detects eight ecosystems and runs the right vulnerability and outdated-package audits.

### 4. Ship: leave a clear trail

**[writing-commits-and-prs](skills/writing-commits-and-prs.md).** Summarizes the staged diff, splits unrelated changes, gets the *why* from the conversation instead of inventing it, and validates Conventional Commits with `commit_helper.py` (which can also install a commit-msg hook). PR descriptions cover why, what, how it was tested and risk.

**[session-handoff](skills/session-handoff.md).** Long contexts degrade, so this skill writes a compact `HANDOFF.md`: goal, verified state (from `handoff_context.py`), decisions with reasons, dead ends, ordered next steps and open questions. It never copies secrets into the note.

### 5. AI apps: build LLM features you can trust

**[llm-app-evals](skills/llm-app-evals.md).** Builds case sets from real failure modes, prefers deterministic checks, calibrates any LLM judge against human labels, and compares versions with `eval_harness.py` using Wilson intervals, repeat runs and per-case regression lists.

**[prompt-injection-defense](skills/prompt-injection-defense.md).** Threat-models agents and chatbots for the "lethal trifecta" (untrusted input, private data, an exfiltration channel) and applies architectural defenses (action-selector, plan-then-execute, map-reduce, dual LLM, code-then-execute, context minimization) plus layered controls and injection test cases.

### 6. Meta: build your own

**[skill-authoring](skills/skill-authoring.md).** Captures a real procedure, scaffolds it with `new_skill.py`, writes a description that triggers, and lints with `validate_skill.py` for spec errors, security red flags and 11 documented skill smells. This is the skill to use to grow DevForge or start your own collection.

## Compatibility

| Agent | Install | Status |
|---|---|---|
| Claude Code | `/plugin marketplace add suhaas19/devforge` | Native plugin and marketplace |
| Antigravity | `agy plugin install https://github.com/suhaas19/devforge` | Native plugin |
| Codex | `codex plugin marketplace add suhaas19/devforge` | Native plugin and marketplace |
| Gemini CLI | `gemini extensions install https://github.com/suhaas19/devforge` | Extension |
| Cursor | `npx skills add suhaas19/devforge -a cursor` | Skills + plugin manifest |
| GitHub Copilot | `npx skills add suhaas19/devforge -a github-copilot` | Skills |
| OpenCode, Goose, Amp, others | `npx skills add` or `./install.sh` | Skills |

Requirements: Python 3.9+ and git. Works on macOS, Linux and Windows (WSL or Python on PATH).

## Quality and testing

- **32 automated tests** cover every script and the installer.
- **Skill linter** (`validate_skill.py --strict`) passes with zero errors and zero warnings on all 13 skills.
- **Manifest sync check** guarantees every agent's manifest has the same name, version and URLs.
- **ShellCheck** on all shell scripts; **CI** on Ubuntu and macOS, Python 3.11 and 3.13.
- **26 eval cases** with graders and fixtures. A pilot with-vs-without comparison is reported honestly in the [README](../README.md#evaluation).

## Security model

- No hooks, no background processes, no telemetry.
- Scripts read the project and run git. Only `verify_package.py` uses the network, to query public package registries.
- Scripts that execute commands run only the commands you or your agent pass to them.
- Every skill is linted for hidden Unicode, download-to-shell patterns, credential access and environment exfiltration.
- Vulnerability reports: [SECURITY.md](../SECURITY.md).

## Roadmap

- Larger multi-run benchmark across models, published with the eval viewer.
- More ecosystems in `verify_package.py` (crates.io, Go modules, Maven Central, RubyGems).
- Skills for database migrations, API design review, incident postmortems and CI pipeline debugging.
- Marketplace submissions (Claude plugin directory, Antigravity marketplace).

Ideas and requests are welcome in [GitHub Issues](https://github.com/suhaas19/devforge/issues).

## FAQ

**Does it conflict with Superpowers?** No. Superpowers provides an end-to-end development methodology (brainstorm, plan, TDD, subagents); DevForge provides specialist skills with tools. Their scopes are distinct, so they can be installed together.

**Will it slow my agent down?** Only skill names and descriptions are always loaded (about 100 tokens each). A skill's body loads only when the task needs it, and scripts run without entering the context.

**Do I need to call skills manually?** No; they trigger from what you ask. You can still invoke one with `/<skill-name>`.

**Can I use only some skills?** Yes: `npx skills add suhaas19/devforge --skill <name>` or `./install.sh --skill <name>`.

**How do I make my own collection from this?** Fork it, run `python3 scripts/sync_manifests.py --owner <you>`, and add skills with `skill-authoring`.

## Author

Built by **Suhaas Gupta** ([@suhaas19](https://github.com/suhaas19)), an AI/ML engineer working on agentic AI in information security. Licensed under [MIT](../LICENSE).
