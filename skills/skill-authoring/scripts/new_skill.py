#!/usr/bin/env python3
"""Scaffold a new Agent Skill that already passes validate_skill.py.

Usage:
    new_skill.py <name> [--dir skills] [--description "..."] [--with-scripts]
                 [--with-references] [--with-evals]

Creates <dir>/<name>/SKILL.md from assets/SKILL_TEMPLATE.md and, optionally,
scripts/, references/ and an evals/ test-case folder in the layout that
`claude plugin eval` and skill-creator read.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "SKILL_TEMPLATE.md"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SCRIPT_STUB = '''#!/usr/bin/env python3
"""{title}: one-line summary of what this script does.

Usage:
    {script}.py <input> [--json]
"""
import argparse
import json
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = {{"input": args.input, "ok": True}}
    print(json.dumps(result, indent=2) if args.json else f"ok: {{args.input}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

PROMPT_MD = """---
tags: [{name}]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Replace this line with a realistic request a user would type for this skill.
"""

CASE_YAML = """schema_version: "1.1"
name: {case}
expected_outcome: |
  Describe what a good result looks like.
"""

GRADER = """---
type: llm
focus: trace
weight: 1
---

The response completes the task the prompt asks for.
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name")
    ap.add_argument("--dir", default="skills", help="parent directory (default: skills)")
    ap.add_argument("--description", default="")
    ap.add_argument("--with-scripts", action="store_true")
    ap.add_argument("--with-references", action="store_true")
    ap.add_argument("--with-evals", action="store_true")
    args = ap.parse_args(argv)

    name = args.name
    if not NAME_RE.match(name) or len(name) > 64:
        print(f"error: {name!r} must be 1-64 chars of a-z, 0-9 and single hyphens", file=sys.stderr)
        return 2
    target = Path(args.dir) / name
    if target.exists():
        print(f"error: {target} already exists", file=sys.stderr)
        return 1

    title = name.replace("-", " ").title()
    description = args.description or (
        f"TODO: say what {title} does in third person, then when to use it. "
        "Use when the user asks to ... or mentions ..., even if they do not name the skill."
    )
    body = TEMPLATE.read_text(encoding="utf-8")
    body = body.replace("{{name}}", name).replace("{{title}}", title).replace("{{description}}", description)

    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(body, encoding="utf-8")
    created = [target / "SKILL.md"]

    if args.with_scripts:
        sdir = target / "scripts"
        sdir.mkdir()
        script = sdir / "run.py"
        script.write_text(SCRIPT_STUB.format(title=title, script="run"), encoding="utf-8")
        script.chmod(0o755)
        created.append(script)
    if args.with_references:
        rdir = target / "references"
        rdir.mkdir()
        ref = rdir / "details.md"
        ref.write_text(f"# {title}: details\n\nMove long reference material here.\n", encoding="utf-8")
        created.append(ref)
    if args.with_evals:
        case = f"{name}-basic"
        cdir = target / "evals" / case
        (cdir / "graders").mkdir(parents=True)
        (cdir / "prompt.md").write_text(PROMPT_MD.format(name=name), encoding="utf-8")
        (cdir / "case.yaml").write_text(CASE_YAML.format(case=case), encoding="utf-8")
        (cdir / "graders" / "01-expected-output.md").write_text(GRADER, encoding="utf-8")
        created.append(cdir)

    for path in created:
        print(f"created {path}")
    print(f"\nNext: edit {target / 'SKILL.md'}, then run validate_skill.py {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
