# Skill authoring best practices (with evidence)

## Contents
1. [What the research says](#what-the-research-says)
2. [Descriptions](#descriptions)
3. [Body structure](#body-structure)
4. [Scripts](#scripts)
5. [Progressive disclosure](#progressive-disclosure)
6. [Security](#security)
7. [Testing skills](#testing-skills)
8. [Portability across agents](#portability-across-agents)

## What the research says

| Finding | Source | Implication |
|---|---|---|
| Curated skills: +16.2 pp average pass rate; self-generated skills: no reliable gain | SkillsBench, Li et al. 2026 (arXiv:2602.12670) | Write skills from real, expert procedures, not from what the model "already knows" |
| 2-3 focused modules beat 4+; "comprehensive" skills were net negative (-2.9 pp) | SkillsBench | Keep skills focused; split big ones |
| Biggest gains in domains under-represented in pretraining (healthcare, manufacturing, cybersecurity); smallest in general software engineering | SkillsBench | Encode team- or domain-specific knowledge the model cannot infer |
| Smaller models with skills can match larger models without them | SkillsBench | Skills are a cheap capability multiplier |
| In realistic settings agents often do not load relevant skills (49% loaded all curated skills; 31% with distractors) and gains shrink as the pool grows | Liu et al. 2026, "How Well Do Agentic Skills Work in the Wild" (arXiv:2604.04323) | Descriptions must be specific and keyword-rich; avoid overlapping skills |
| Weaker models can be hurt by irrelevant skills | Liu et al. 2026 | Fewer, sharper skills; clear "not for" boundaries |
| >99% of 238 real SKILL.md files contain at least one smell; the most common: no guard against skipping steps (94%), buried gotchas (81%), no plan stage (78%), never asks the human (77%), no progress tracking (71%) | Hong et al. 2026, "From Anatomy to Smells" (arXiv:2607.01456) | Use the template: checklist, decision table, gotchas header, ask-human points |
| 26.1% of community skills had at least one vulnerability (prompt injection, exfiltration, privilege escalation, supply chain) | Liu et al. 2026, "Agent Skills in the Wild" (arXiv:2601.10338) | Lint for security patterns; review third-party skills before installing |
| 157 confirmed malicious skills among 98k scanned; they average 4 vulnerabilities each | Liu et al. 2026, "Malicious Agent Skills in the Wild" (arXiv:2602.06547) | Treat skills as code from a supply chain |
| Small-to-mid open models (~12-30B) benefit substantially; tiny models struggle to select skills | Agent Skill Framework for SLMs (arXiv:2602.16653) | Test on the models your users run |

## Descriptions
The description is loaded for every skill on every turn (~100 tokens each) and is the only
signal for selection.
- **Third person, active:** "Reviews diffs for...", not "I can help you review" or "Use this to".
- **Three parts:** what it does, when to use it, keywords and phrasings users type ("PR", "pull request", "diff", "before merging").
- **Slightly pushy:** agents under-trigger. Add "...and whenever X, even if the user does not ask for Y."
- **Distinct from neighbors:** if two skills could match the same request, add a "not for" clause to the body and sharpen both descriptions.
- **No XML/HTML tags, no instructions to the model** ("always use this skill") in the description.
- ≤ 1024 characters; 200-600 is typical for good ones.

## Body structure
Recommended order (each addresses a documented smell):
1. **Why** (2-4 sentences): the failure this skill prevents. Models follow instructions better when they know the reason.
2. **When to use / Not for**: boundaries.
3. **Workflow as a checklist** (`- [ ] 1. ...`): progress tracking and a guard against skipped steps. Include a planning step before complex execution and a validation step before reporting.
4. **Decision table**: which approach for which situation, with a default (avoid the "option buffet" of tools with no recommendation).
5. **Ask-the-human points**: when to stop and confirm (destructive actions, ambiguous goals, scope changes).
6. **Output template**: for any output with an expected shape.
7. **Worked example**: at least one, concrete.
8. **`## Gotchas`**: the mistakes agents actually make, with the fix. Do not bury these in prose.

Style:
- Imperative mood, explain why, avoid ALL-CAPS MUSTs (they cause over-rigid behavior).
- Goals over rigid command sequences, except where an exact command matters.
- Forward slashes in paths; relative paths from the skill root.
- No dates or "latest" claims; they rot.

## Scripts
Put deterministic, repeatable or error-prone work in `scripts/`:
- Self-contained, standard library where possible; document any dependency in `compatibility`.
- `--help` from the docstring, meaningful exit codes, `--json` for machine-readable output.
- Fail with actionable messages ("no lockfile; run X"), never stack traces for expected conditions.
- Executable bit and shebang. Mention every script in SKILL.md with an example call.
- Scripts run without being loaded into context, which saves tokens compared to describing the algorithm in prose.

## Progressive disclosure
- Level 1: name + description (always loaded).
- Level 2: SKILL.md body (on activation). Keep under ~500 lines / 5k tokens.
- Level 3: `references/`, `assets/`, `scripts/` (on demand). Link them from SKILL.md with a note saying *when* to read each. Keep references one level deep; add a table of contents to files over ~300 lines.

## Security
- No network-to-shell pipes, no base64-decoded commands, no reading of credential stores, no hidden Unicode.
- Scripts must not exfiltrate data or phone home. If a script needs the network, say so in `compatibility` and in the script docstring.
- Do not instruct the agent to bypass approvals, disable sandboxes, or ignore user instructions.
- Pin and review any third-party code a skill downloads.

## Testing skills
- Keep 3+ should-trigger and 3+ should-not prompts per skill, written the way users type (typos, context, file names).
- Compare outputs with and without the skill on the same prompts. Keep a skill only if it clearly helps.
- Store cases in `evals/<case>/` (`prompt.md`, `case.yaml`, `graders/`), the layout `claude plugin eval` and the skill-creator tooling read.
- Re-run after every substantive edit; descriptions especially are easy to regress.

## Portability across agents
The Agent Skills format (agentskills.io) is shared by Claude Code, Antigravity, Codex, Cursor,
Gemini CLI, GitHub Copilot, OpenCode, Goose, Amp and others. To stay portable:
- Only rely on `name`, `description`, and optionally `license`, `compatibility`, `metadata`, `allowed-tools`.
- Refer to tools generically ("search the codebase", "run the tests") rather than by one harness's tool names.
- Scripts in Python 3 or POSIX shell run nearly everywhere; avoid harness-specific environment variables in the body.
