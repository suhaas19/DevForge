#!/usr/bin/env python3
"""Draft-ready facts for a commit or PR, and a Conventional Commits message checker.

Usage:
    commit_helper.py summary [--staged | --base REF] [--json]
    commit_helper.py check "feat(api): add pagination"      # or: check --file .git/COMMIT_EDITMSG
    commit_helper.py install-hook                            # installs a commit-msg hook using `check`

`summary` prints the change set grouped by area with a suggested type and scope.
It does not write the message: the "why" has to come from the human or the
conversation, never invented. `check` validates a message and exits 1 with
reasons when it does not conform. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

TYPES = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]
HEADER_RE = re.compile(r"^(?P<type>[a-z]+)(\((?P<scope>[\w./-]+)\))?(?P<bang>!)?: (?P<subject>.+)$")
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_|_test\.|\.(test|spec)\.")
DOC_RE = re.compile(r"\.(md|rst|txt|adoc)$|(^|/)docs?/", re.I)
CI_RE = re.compile(r"^\.github/workflows/|\.gitlab-ci\.yml$|Jenkinsfile|\.circleci/")
BUILD_RE = re.compile(r"(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|pyproject\.toml|requirements[^/]*\.txt|"
                      r"poetry\.lock|uv\.lock|go\.(mod|sum)|Cargo\.(toml|lock)|Dockerfile|Makefile|.*\.gradle(\.kts)?|pom\.xml)$")


def git(*args):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    return res.stdout


def suggest_type(paths):
    if all(DOC_RE.search(p) for p in paths):
        return "docs"
    if all(TEST_RE.search(p) for p in paths):
        return "test"
    if all(CI_RE.search(p) for p in paths):
        return "ci"
    if all(BUILD_RE.search(p) for p in paths):
        return "build"
    return "feat|fix|refactor|perf (decide from the intent, not the diff)"


def suggest_scope(paths):
    parts = []
    for p in paths:
        segs = [s for s in p.split("/")[:-1] if s not in {"src", "lib", "app", "pkg", "internal", "packages"}]
        parts.append(segs[0] if segs else Path(p).stem)
    common = Counter(parts).most_common(1)
    return common[0][0] if common and common[0][1] >= max(1, len(paths) // 2) else None


def summary(args):
    rng = ["--cached"] if args.staged else [f"{args.base}...HEAD"] if args.base else ["--cached"]
    numstat = git("diff", "--numstat", "-M", *rng)
    files = []
    for line in numstat.splitlines():
        a, r, p = line.split("\t", 2)
        files.append({"path": p, "added": 0 if a == "-" else int(a), "removed": 0 if r == "-" else int(r)})
    if not files:
        print("nothing to summarize (stage changes or pass --base REF)", file=sys.stderr)
        return 1
    paths = [f["path"] for f in files]
    info = {
        "files": files, "added": sum(f["added"] for f in files), "removed": sum(f["removed"] for f in files),
        "suggested_type": suggest_type(paths), "suggested_scope": suggest_scope(paths),
        "tests_touched": any(TEST_RE.search(p) for p in paths),
        "breaking_hints": [p for p in paths if re.search(r"(^|/)(api|proto|schema|migrations?)/|openapi|\.proto$", p)],
        "commits": git("log", "--format=%s", f"{args.base}..HEAD").splitlines() if args.base else [],
    }
    if args.json:
        print(json.dumps(info, indent=2))
        return 0
    print(f"{len(files)} file(s), +{info['added']}/-{info['removed']}")
    for f in files:
        print(f"  {f['path']}  +{f['added']}/-{f['removed']}")
    print(f"\nsuggested type : {info['suggested_type']}")
    print(f"suggested scope: {info['suggested_scope'] or '(none obvious; omit or choose the module)'}")
    print(f"tests touched  : {'yes' if info['tests_touched'] else 'no'}")
    if info["breaking_hints"]:
        print(f"check for breaking changes in: {', '.join(info['breaking_hints'])}")
    if info["commits"]:
        print("\ncommits in range:\n  " + "\n  ".join(info["commits"]))
    return 0


def check_message(msg: str):
    lines = [l for l in msg.splitlines() if not l.startswith("#")]
    while lines and not lines[-1].strip():
        lines.pop()
    problems = []
    if not lines or not lines[0].strip():
        return ["message is empty"]
    header = lines[0]
    if re.match(r"^(Merge|Revert \"|fixup!|squash!)", header):
        return []
    m = HEADER_RE.match(header)
    if not m:
        problems.append("header must look like 'type(scope): subject' (scope optional), e.g. 'fix(auth): reject expired tokens'")
    else:
        if m.group("type") not in TYPES:
            problems.append(f"unknown type {m.group('type')!r}; use one of: {', '.join(TYPES)}")
        subj = m.group("subject")
        if subj.endswith("."):
            problems.append("subject should not end with a period")
        if subj[:1].isupper() and not subj[:2].isupper():
            problems.append("subject should start lower-case (imperative mood: 'add', not 'Added')")
        if re.match(r"^(added|fixed|updated|changed|removed|implemented)\b", subj, re.I):
            problems.append("use the imperative mood: 'add' rather than 'added'")
    if len(header) > 72:
        problems.append(f"header is {len(header)} chars; keep it at 72 or fewer (50 is ideal)")
    if len(lines) > 1 and lines[1].strip():
        problems.append("leave a blank line between the header and the body")
    long_body = [i + 1 for i, l in enumerate(lines[2:], 2) if len(l) > 100 and not re.match(r"^\s*(https?://|[\w-]+: )", l)]
    if long_body:
        problems.append(f"wrap body lines at ~72 chars (long lines: {long_body[:5]})")
    if m and m.group("bang") and not any(l.startswith("BREAKING CHANGE:") for l in lines):
        problems.append("'!' marks a breaking change; add a 'BREAKING CHANGE: ...' footer explaining the migration")
    return problems


def check(args):
    msg = Path(args.file).read_text(encoding="utf-8") if args.file else (args.message or "")
    problems = check_message(msg)
    if problems:
        print("commit message does not follow Conventional Commits:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("ok")
    return 0


def install_hook(_args):
    hooks = Path(git("rev-parse", "--git-path", "hooks").strip())
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "commit-msg"
    if hook.exists():
        print(f"error: {hook} already exists; not overwriting", file=sys.stderr)
        return 1
    hook.write_text(f'#!/bin/sh\nexec python3 "{Path(__file__).resolve()}" check --file "$1"\n', encoding="utf-8")
    hook.chmod(0o755)
    print(f"installed {hook}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary")
    s.add_argument("--staged", action="store_true")
    s.add_argument("--base")
    s.add_argument("--json", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("message", nargs="?")
    c.add_argument("--file")
    sub.add_parser("install-hook")
    args = ap.parse_args(argv)
    try:
        return {"summary": summary, "check": check, "install-hook": install_hook}[args.cmd](args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
