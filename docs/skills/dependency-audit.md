# Dependency Audit

> Audit dependencies for CVEs, and verify any package before it is installed.

**Category:** Check · **Skill folder:** [`skills/dependency-audit/`](../../skills/dependency-audit/) · **Instructions:** [`SKILL.md`](../../skills/dependency-audit/SKILL.md)

## The problem it solves

Besides known vulnerabilities, LLMs recommend packages that do not exist (19.7% of packages in generated code across 16 models), and attackers register those names (slopsquatting).

## When it activates

- "Check our dependencies", "any CVEs?", "upgrade libraries"
- Reviewing a lockfile change
- Before `pip install` / `npm install` of an AI-suggested or new package

You can also call it directly: `/dependency-audit` (Claude Code, Antigravity) or `/devforge:dependency-audit` when installed as a Claude Code plugin.

## How it works

1. Verify new packages with `verify_package.py` (BLOCK / REVIEW / OK)
2. Plan the audit with `audit_deps.py`; run installed tools with `--run`
3. Triage each vulnerability: runtime vs dev, reachable, fixed version
4. Upgrade smallest-risk first, one logical upgrade per commit
5. Validate: audit clean, tests green, lockfile diff reviewed

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/verify_package.py`](../../skills/dependency-audit/scripts/verify_package.py) | `python3 scripts/verify_package.py flask-jwt-simplez requests -e pypi` | Checks existence, age, release count, source repo, deprecation and typosquat distance on PyPI and npm |
| [`scripts/audit_deps.py`](../../skills/dependency-audit/scripts/audit_deps.py) | `python3 scripts/audit_deps.py . [--run]` | Detects Python, Node, Go, Rust, Ruby, PHP, Java and .NET; plans pip-audit, npm/pnpm/yarn audit, govulncheck, cargo audit, osv-scanner and more |

## What you get back

A vulnerability table (package, version, issue, severity, fixed in, reachable, action), hygiene notes and verified new packages.

## Try it

```text
chatgpt said to pip install flask-jwt-simplez requests, can you install them
audit the deps in requirements.txt, we havent touched them in ages
```

More test prompts with graders: [`skills/dependency-audit/evals/`](../../skills/dependency-audit/evals/).

## Research basis

- Spracklen et al., *We Have a Package for You!* (USENIX Security 2025)
- OSV vulnerability database

---

[← All skills](../../README.md#whats-inside) · [← performance-profiling](performance-profiling.md) · [writing-commits-and-prs →](writing-commits-and-prs.md)
