---
name: skill-authoring
description: Creates, improves and validates Agent Skills (SKILL.md packages) that work across Claude Code, Antigravity, Codex, Cursor, Gemini CLI and other agents, applying empirical findings on what makes skills trigger and help. Includes a scaffolder and a linter for spec errors, security red flags and common skill smells. Use when the user wants to write a new skill, turn a workflow into a skill, fix a skill that does not trigger or is ignored, review or lint SKILL.md files, or publish a skill collection on GitHub.
license: MIT
metadata:
  version: "1.0.0"
---

# Skill Authoring

Skills help most when they carry procedural knowledge the model does not already
have, in a focused, verifiable form. SkillsBench (Li et al., 2026) found curated
skills raised pass rates by 16.2 points on average while self-generated skills
gave no reliable benefit, and that focused skills beat comprehensive documentation. A
study of 238 real SKILL.md files (Hong et al., 2026) found that over 99% contain at
least one quality "smell". This skill encodes those findings into a workflow and a linter.

## When to use

- Writing a new skill, or converting a repeated workflow, runbook or prompt into one.
- A skill is not triggering, is triggered for the wrong tasks, or is loaded but ignored.
- Reviewing or linting skills before publishing them.
- **Not for:** one-off instructions for a single task (put them in the prompt) or always-on project rules (put them in `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`).

## Workflow

- [ ] 1. **Capture the procedure from real use.** Get 2-3 concrete examples of the task done well (from the conversation, the user, or existing runbooks): inputs, steps, tools, the output, and the mistakes to avoid. Do not write a skill from general knowledge alone; that is the "self-generated" case that does not help.
- [ ] 2. **Decide the boundary.** One skill = one job. If you are listing more than ~3 distinct jobs, split it. Write down 3 requests that should trigger it and 3 near-misses that should not.
- [ ] 3. **Scaffold:** `python3 scripts/new_skill.py <name> --dir skills [--with-scripts] [--with-references] [--with-evals]`. Names: lowercase, hyphens, ≤ 64 chars, a verb-ish phrase that says what it does (`reviewing-code-changes`, not `helper`).
- [ ] 4. **Write the description** (the only part the agent sees before deciding): third person, *what it does* + *when to use it* + the words users actually type. Make it slightly pushy ("...even if they do not say 'X'"), since agents under-trigger skills. Max 1024 chars; no XML tags. See [references/best-practices.md](references/best-practices.md#descriptions).
- [ ] 5. **Write the body** from the template: why it matters, when not to use, a checklist workflow, a decision table, an output template, one worked example, a validation step, when to ask the human, and a `## Gotchas` section. Explain *why* instead of shouting MUST. Keep it under ~500 lines; move detail to `references/` (one level deep) and deterministic work to `scripts/`.
- [ ] 6. **Add scripts for anything deterministic** (parsing, scanning, formatting, validation). Standard library where possible, `--help` text, clear errors, `--json` output, exit codes that mean something. Mention each script in SKILL.md with an example invocation.
- [ ] 7. **Lint:** `python3 scripts/validate_skill.py <skill-dir>` (or a whole `skills/` folder; `--strict` in CI). Fix all errors; fix or consciously accept each warning.
- [ ] 8. **Test with real prompts.** Run the 3 should-trigger and 3 should-not prompts in a fresh session; check it loads when it should, and that the output is better than without the skill. Add the cases under `evals/` so they can be re-run (`--with-evals` creates the layout).
- [ ] 9. **Iterate** on what you saw: if the agent skipped a step, explain why that step matters; if it wasted time, cut that part; if every run rewrote the same helper, bundle it as a script.

Ask the user to review the description and the trigger/near-miss prompts before step 8: they know how they phrase requests better than you do.

## Linter checks (validate_skill.py)

| Kind | Checks |
|---|---|
| Spec errors | frontmatter present and valid; `name` format and equals directory; `description` 1-1024 chars; `compatibility` ≤ 500; `metadata` values are strings; referenced files exist and stay inside the skill |
| Security errors | hidden Unicode (zero-width, bidi), XML tags in description, download-piped-to-shell, base64-to-shell, credential directories, env exfiltration |
| Smell warnings | missing trigger phrase (CSD), non-third-person description (NTPD), lengthy body (LSB), no gotchas header (BG), no validation step (NVS), no example (ME), no checklist for long workflows (NPT), never asks human (NAH), time-sensitive wording (TSS), backslash paths (BP), unreferenced or non-executable scripts (MUS) |

## Publishing a collection

Put skills under `skills/<name>/SKILL.md` in a GitHub repo. That single layout is installable by `npx skills add <owner>/<repo>` (40+ agents), by Gemini CLI as an extension, and, with the manifests this repository ships (`.claude-plugin/`, `.antigravity-plugin/`, `.cursor-plugin/`, `.codex-plugin/`, `gemini-extension.json`), as a native plugin in Claude Code, Antigravity, Cursor and Codex. See the repository README for the exact commands.

## Example

**Before:** `description: Helps with PDFs.`
**After:** `description: Extracts text and tables from PDFs, fills PDF forms, and merges or splits PDF files. Use when the user mentions PDFs, forms, scanned documents, or needs data pulled out of a document, even if they do not say "PDF".`

## Gotchas

- **The description does the triggering; the body does the work.** "When to use" information in the body is invisible at selection time; put trigger words in the description.
- **More skills is not better.** Overlapping descriptions act as distractors and lower performance, especially for smaller models. Merge or sharpen near-duplicates.
- **Comprehensive documentation hurts.** Exhaustive references dilute the procedure; SkillsBench saw *negative* gains for comprehensive skills. Keep the core procedure short and stepwise, with at least one working example.
- **Skills run with the agent's permissions.** Never include network installers piped to shells, credential access, or hidden instructions; reviewers and linters look for exactly these patterns.
- **Rigid command lists break on real repos.** State goals and let the agent choose the invocation, except where an exact command is the point.
- **Facts go stale.** Avoid version numbers, "newest" claims and dates in the body; point to where to check instead.
