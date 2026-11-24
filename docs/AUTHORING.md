# Writing a new DevForge skill

The `skill-authoring` skill contains the full guidance and the research behind it
([best practices](../skills/skill-authoring/references/best-practices.md)). This page is the
short version for contributors.

## 1. Scaffold
```bash
python3 skills/skill-authoring/scripts/new_skill.py <name> --with-scripts --with-references --with-evals
```
`<name>`: lowercase letters, digits and single hyphens, max 64 chars, saying what the skill does
(`migrating-databases`, not `db-helper`).

## 2. Write the description first
It is the only text an agent sees when deciding whether to load the skill.
- Third person: "Generates…", "Reviews…".
- What it does + when to use it + words users actually type.
- 200-600 characters is typical; the hard limit is 1024. No XML tags. Quote it if it contains `: `.

## 3. Write the body (template already in place)
Why → when / not for → checklist workflow (with a planning step and a validation step) →
decision table → when to ask the user → output template → example → `## Gotchas`.
Keep it under ~500 lines. Move long material to `references/`, deterministic work to `scripts/`.

## 4. Scripts
Standard library Python 3.9+ or POSIX bash. Docstring usage block, `--json` output, meaningful
exit codes, readable errors. Add tests in `tests/test_scripts.py`.

## 5. Evals
Each case lives in `skills/<name>/evals/<case>/`:
```text
prompt.md         settings block + the request exactly as a user would type it
case.yaml         schema_version "1.1", name, expected_outcome
graders/NN-*.md   one verifiable statement per file
files/            input files (optional) + place-files.sh
```
Write at least two should-trigger cases. Run them with `claude plugin eval skills/<name>`
(Claude Code) or with the skill-creator workflow, comparing with and without the skill.

## 6. Check and ship
```bash
python3 skills/skill-authoring/scripts/validate_skill.py skills --strict
python3 -m pytest -q
python3 scripts/sync_manifests.py --version <next-version>
```
Add a line to `CHANGELOG.md` and the skill table in `README.md`, then open a PR.

## Style rules
- Explain *why*; avoid ALL-CAPS MUST/NEVER.
- Name tools generically ("run the tests") so the skill works in every agent.
- No dates, version numbers or "newest" claims in skill bodies.
- Never include network installers piped into shells, credential access, or hidden instructions. CI rejects them.
