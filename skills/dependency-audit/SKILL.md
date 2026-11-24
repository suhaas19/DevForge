---
name: dependency-audit
description: Audits a project's third-party dependencies for known vulnerabilities, outdated or unpinned versions, and risky new packages, and verifies that any package an agent proposes to install actually exists and is not a typosquat. Use when the user asks to check dependencies, audit packages, find CVEs, update or upgrade libraries, review a lockfile or requirements change, or before running pip install, npm install, cargo add, or similar for a package that was suggested by an AI or is new to the project.
license: MIT
compatibility: verify_package.py needs network access to pypi.org and registry.npmjs.org. audit_deps.py uses whichever audit tools are installed (pip-audit, npm, govulncheck, cargo-audit, osv-scanner...).
metadata:
  version: "1.0.0"
---

# Dependency Audit

Two risks dominate. Known vulnerabilities in what you already depend on, and
**package hallucination**: code-generating LLMs recommend packages that do not
exist (19.7% of the packages referenced in code from 16 models in Spracklen
et al., USENIX Security 2025), and attackers register those names ("slopsquatting").
This skill handles both: audit what is installed, and verify before installing
anything new.

## When to use

- Auditing dependencies, checking for CVEs, preparing an upgrade, reviewing a lockfile diff.
- **Before installing any package the agent (or another AI) suggested**, or any package new to this project.
- **Not for:** vulnerabilities in first-party code (use `secure-code-review`).

## Workflow A: verify before installing (always, for new packages)

- [ ] 1. Run `python3 scripts/verify_package.py <name> [<name>...] -e pypi|npm` (or `--from-file requirements.txt` / `package.json`).
- [ ] 2. Act on the verdict:
  - **BLOCK** (does not exist): do not install. The name was probably hallucinated; find the real package (search the registry or the library's docs) and verify that one.
  - **REVIEW** (new, single release, no repository, deprecated, or one edit away from a popular name): show the user the reasons and ask before installing. Check the repository, maintainers and download counts.
  - **OK**: proceed, pinning a version.
- [ ] 3. For ecosystems the script does not cover (crates.io, Go, Maven, RubyGems), check the registry page manually for the same signals.

## Workflow B: audit the project

- [ ] 1. **Plan:** `python3 scripts/audit_deps.py <root>` lists ecosystems, manifests, lockfiles, whether versions are pinned, and the audit commands that apply (✓ = tool installed).
- [ ] 2. **Run:** `python3 scripts/audit_deps.py <root> --run` executes the installed tools and saves raw output in `.dependency-audit/`. If no audit tool is installed, ask the user before installing one (`pipx install pip-audit`, `go install golang.org/x/vuln/cmd/govulncheck@latest`, `cargo install cargo-audit`, osv-scanner release binary).
- [ ] 3. **Triage each vulnerability**, not just count them:
  - Is the vulnerable package actually used at runtime (vs dev/test only)?
  - Is the vulnerable function reachable? (`govulncheck` answers this for Go; elsewhere search for imports and calls.)
  - Is there a fixed version, and is it a patch, minor or major bump?
- [ ] 4. **Plan upgrades** smallest-risk first: patch bumps, then minors, then majors with changelog review. One logical upgrade per commit.
- [ ] 5. **Validate:** re-run the audit (the finding is gone), run the test suite, and check the lockfile diff for unexpected new transitive packages.
- [ ] 6. **Report** with the template.

### Fix options when no clean upgrade exists

| Situation | Option |
|---|---|
| Fix only in a new major | upgrade with migration notes, or pin and document the accepted risk |
| Transitive dependency | override/resolution (`overrides` in npm, `resolutions` in yarn, constraints file in pip) |
| Unmaintained package | replace it; list alternatives for the user to choose |
| Not reachable in your usage | document why and set a reminder to revisit; do not silently ignore |

## Output template

```markdown
## Dependency audit: <project>
**Ecosystems:** Python (uv.lock), Node (pnpm-lock.yaml). **Tools:** pip-audit 2.x, pnpm audit.
| Package | Installed | Issue | Severity | Fixed in | Reachable? | Action |
|---|---|---|---|---|---|---|
| jinja2 | 3.1.2 | CVE-XXXX-YYYY sandbox escape | High | 3.1.4 | yes (templates) | upgrade (patch) |
**Hygiene:** `requirements.txt` unpinned (flask); no lockfile for `tools/`.
**New packages verified:** `httpx` OK; `fastapi-utilz` BLOCK (does not exist; meant `fastapi-utils`).
**Validation:** audit re-run clean for fixed items; tests 312/312.
```

## Gotchas

- **Never "just try installing" an unknown package to see if it exists.** Installing runs the package's install scripts; that is exactly how slopsquatting attacks execute.
- **Audit tools exit non-zero when they find issues.** That is a result, not a tool failure.
- **No lockfile means no reproducible audit.** Transitive versions float between installs; recommend a lockfile. `npm audit` needs `package-lock.json` (`npm install --package-lock-only` creates one without installing).
- **Severity is not priority.** A critical CVE in an unused dev tool matters less than a medium one on the request path.
- **Do not bulk-upgrade everything** in one commit; when tests break you will not know which upgrade did it.
- The popular-package lists in `assets/` are a small sample for typosquat checks; extend them for your ecosystem.
