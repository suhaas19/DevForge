# Secure Code Review

> Defensive security review where every finding has a traced source-to-sink flow.

**Category:** Check · **Skill folder:** [`skills/secure-code-review/`](../../skills/secure-code-review/) · **Instructions:** [`SKILL.md`](../../skills/secure-code-review/SKILL.md)

## The problem it solves

LLMs flag lots of code as vulnerable that is not; every model tested in an IEEE S&P 2024 study had a high false-positive rate. This skill uses deterministic scanners for candidates and requires a concrete data-flow trace before anything is reported.

## When it activates

- "Security review", "audit this", "is this safe to ship"
- OWASP / CWE questions
- Changes touching auth, sessions, uploads, shell, SQL, templates, deserialization, outbound HTTP, crypto, payments or secrets

You can also call it directly: `/secure-code-review` (Claude Code, Antigravity) or `/devforge:secure-code-review` when installed as a Claude Code plugin.

## How it works

1. Scope the review and identify trust boundaries
2. Run `secret_scan.py` and `find_sinks.py` (plus semgrep/bandit/gosec/CodeQL if installed)
3. Trace each candidate sink back to its sources; dismiss constant or sanitized ones and record why
4. Review logic flaws scanners miss (IDOR, missing authorization, mass assignment, races)
5. Rate severity by impact and reachability
6. Validate each finding, then report with flow, impact, safe proof and fix

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/secret_scan.py`](../../skills/secure-code-review/scripts/secret_scan.py) | `python3 scripts/secret_scan.py . [--json]` | 18 key/token formats plus entropy-checked generic secrets; output is redacted; `secret-scan: ignore` suppresses reviewed false positives |
| [`scripts/find_sinks.py`](../../skills/secure-code-review/scripts/find_sinks.py) | `python3 scripts/find_sinks.py . [--category sql-injection]` | Candidate sinks across 11 categories (command/code/SQL injection, deserialization, path traversal, SSRF, XSS, XXE, weak crypto, TLS disabled, open redirect) for Python, JS/TS, Go, Java, PHP, Ruby, .NET |
| [`references/checklist.md`](../../skills/secure-code-review/references/checklist.md) | loaded on demand | OWASP Top 10 mapped to CWE IDs |

## What you get back

Findings by severity (Critical-Informational) with CWE, source → sink flow, impact, safe proof and fix; redacted secrets with a rotation reminder; dismissed candidates listed for transparency.

## Try it

```text
can you do a security review of api.py before we ship it?
my linter keeps screaming about shell=True and sql, is any of it real?
```

More test prompts with graders: [`skills/secure-code-review/evals/`](../../skills/secure-code-review/evals/).

## Research basis

- Ullah et al., *LLMs Cannot Reliably Identify and Reason About Security Vulnerabilities (Yet?)* (IEEE S&P 2024)
- OWASP Top 10 (2021); MITRE CWE

---

[← All skills](../../README.md#whats-inside) · [← reviewing-code-changes](reviewing-code-changes.md) · [test-generation →](test-generation.md)
