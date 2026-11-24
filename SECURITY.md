# Security policy

## Reporting
Please report vulnerabilities privately via GitHub Security Advisories on
`suhaas19/devforge` ("Report a vulnerability"), not in public issues.

## What the skills do
- Bundled scripts read files in your project and run `git`; `bisect_run.sh`, `ddmin.py`, `bench.py`
  and `golden.py` run commands **you** (or your agent) pass to them.
- Only `dependency-audit/scripts/verify_package.py` uses the network (pypi.org, registry.npmjs.org), and
  `audit_deps.py --run` runs your installed audit tools.
- No script sends data anywhere else, installs software, or reads credentials.

## Before installing any skill collection
Skills run with your agent's permissions. Read the SKILL.md files and scripts, or run
`python3 skills/skill-authoring/scripts/validate_skill.py <dir>` on them, which flags hidden Unicode,
download-to-shell patterns, credential access and environment exfiltration.
