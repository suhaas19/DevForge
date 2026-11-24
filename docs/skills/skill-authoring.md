# Skill Authoring

> Write, lint and publish your own Agent Skills, using what research says works.

**Category:** Meta · **Skill folder:** [`skills/skill-authoring/`](../../skills/skill-authoring/) · **Instructions:** [`SKILL.md`](../../skills/skill-authoring/SKILL.md)

## The problem it solves

Curated skills help (+16.2 points in SkillsBench) but self-generated ones do not, comprehensive skills hurt, and over 99% of real SKILL.md files contain at least one quality smell.

## When it activates

- "Turn this runbook into a skill"
- "My skill never triggers"
- Linting or publishing skills

You can also call it directly: `/skill-authoring` (Claude Code, Antigravity) or `/devforge:skill-authoring` when installed as a Claude Code plugin.

## How it works

1. Capture the procedure from 2-3 real examples
2. Set the boundary: 3 should-trigger and 3 near-miss prompts
3. Scaffold with `new_skill.py`
4. Write the description: third person, what + when + keywords
5. Write the body from the template; move detail to references and scripts
6. Lint with `validate_skill.py`; test with real prompts; iterate

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/new_skill.py`](../../skills/skill-authoring/scripts/new_skill.py) | `python3 scripts/new_skill.py my-skill --with-scripts --with-evals` | Scaffold that already passes the linter, with an evals/ layout |
| [`scripts/validate_skill.py`](../../skills/skill-authoring/scripts/validate_skill.py) | `python3 scripts/validate_skill.py skills --strict` | Spec errors, security errors (hidden Unicode, download-to-shell, credential access) and 11 smell warnings |
| [`references/best-practices.md`](../../skills/skill-authoring/references/best-practices.md) | loaded on demand | The evidence table and authoring rules |

## What you get back

A validated `skills/<name>/` folder with SKILL.md, optional scripts/references, and eval cases.

## Try it

```text
turn our release runbook into an agent skill so claude code and antigravity can both use it
my terraform skill never gets used, can you fix it?
```

More test prompts with graders: [`skills/skill-authoring/evals/`](../../skills/skill-authoring/evals/).

## Research basis

- Li et al., *SkillsBench* (2026), arXiv:2602.12670
- Liu et al., *How Well Do Agentic Skills Work in the Wild* (2026), arXiv:2604.04323
- Hong et al., *From Anatomy to Smells* (2026), arXiv:2607.01456
- Liu et al., *Agent Skills in the Wild* (2026), arXiv:2601.10338

---

[← All skills](../../README.md#whats-inside) · [← session-handoff](session-handoff.md)
