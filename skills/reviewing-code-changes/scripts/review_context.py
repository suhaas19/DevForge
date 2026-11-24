#!/usr/bin/env python3
"""Summarize a git change set and flag the parts that deserve the closest review.

Usage:
    review_context.py [--base REF] [--staged] [--json]

Default range: merge-base of HEAD with origin/main, main, origin/master or master,
falling back to HEAD~1. --staged reviews the index instead. Use --base to set the
range explicitly (e.g. --base v1.4.0 or --base HEAD~3).

The output is a triage map, not a review: it lists changed files with line
counts, groups them by area, and attaches risk flags (security-sensitive paths,
migrations, lockfiles, deleted tests, source changed without tests, debug
leftovers, TODOs added, very large hunks). Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict

SENSITIVE = [
    (r"auth|login|session|token|oauth|jwt|password|passwd|credential|secret|crypto|cipher|sign|permission|rbac|acl|policy",
     "security-sensitive"),
    (r"migrat|schema|\.sql$|alembic|flyway|liquibase", "database/migration"),
    (r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|uv\.lock|Cargo\.lock|go\.sum|Gemfile\.lock|composer\.lock)$",
     "lockfile"),
    (r"(^|/)(package\.json|pyproject\.toml|requirements[^/]*\.txt|go\.mod|Cargo\.toml|pom\.xml|build\.gradle(\.kts)?|Gemfile)$",
     "dependency manifest"),
    (r"(^|/)(Dockerfile|docker-compose[^/]*|\.github/workflows/|\.gitlab-ci\.yml|Jenkinsfile|terraform|k8s|helm|deploy)",
     "build/deploy/infra"),
    (r"(^|/)\.?env(\.|$)|config|settings|\.ya?ml$|\.toml$|\.ini$", "configuration"),
    (r"(^|/)(api|routes?|controllers?|handlers?|endpoints?|graphql|proto)/|\.proto$|openapi|swagger", "public API surface"),
    (r"concurren|thread|async|lock|mutex|queue|worker|retry|cache", "concurrency/caching"),
]
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]+$|_test\.\w+$|\.(test|spec)\.\w+$|Tests?\.\w+$")
CODE_EXT = re.compile(r"\.(py|js|jsx|ts|tsx|go|rs|java|kt|rb|php|cs|c|cc|cpp|h|hpp|swift|scala|m|dart|ex|exs)$")
DEBUG_RE = re.compile(r"^\+(?!\+\+).*\b(console\.log|print\(|println!|fmt\.Print|debugger;?|pdb\.set_trace|breakpoint\(\)|binding\.pry|var_dump|System\.out\.print)", re.M)
TODO_RE = re.compile(r"^\+(?!\+\+).*\b(TODO|FIXME|XXX|HACK)\b", re.M)
SECRETISH_RE = re.compile(r"^\+(?!\+\+).*(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}", re.I | re.M)


def git(*args, check=True):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or f"git {' '.join(args)} failed")
    return res.stdout if res.returncode == 0 else None


def resolve_base(explicit):
    if explicit:
        return explicit
    for cand in ("origin/main", "main", "origin/master", "master", "origin/develop", "develop"):
        if git("rev-parse", "--verify", "--quiet", cand, check=False):
            mb = git("merge-base", "HEAD", cand, check=False)
            head = git("rev-parse", "HEAD", check=False)
            if mb and mb.strip() != (head or "").strip():
                return mb.strip()
    return "HEAD~1"


def analyze(base, staged):
    rng = ["--cached"] if staged else [f"{base}...HEAD" if "..." not in base else base]
    numstat = git("diff", "--numstat", "-M", *rng)
    status = git("diff", "--name-status", "-M", *rng)
    patch = git("diff", "-U0", "-M", *rng)

    st_map = {}
    for line in status.splitlines():
        parts = line.split("\t")
        if parts:
            st_map[parts[-1]] = parts[0][0]
    files = []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add, rem, path = parts[0], parts[1], parts[-1]
        if " => " in path:
            path = re.sub(r"\{[^}]*=> ([^}]*)\}", r"\1", path).split(" => ")[-1]
        binary = add == "-"
        files.append({
            "path": path,
            "status": {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied"}.get(st_map.get(path, "M"), "modified"),
            "added": 0 if binary else int(add), "removed": 0 if binary else int(rem), "binary": binary,
        })

    per_file_patch = defaultdict(str)
    current = None
    for line in patch.splitlines(keepends=True):
        if line.startswith("diff --git"):
            m = re.search(r" b/(.+)$", line.strip())
            current = m.group(1) if m else None
        elif current:
            per_file_patch[current] += line

    flags_global = []
    src_changed = [f for f in files if CODE_EXT.search(f["path"]) and not TEST_RE.search(f["path"])]
    tests_changed = [f for f in files if TEST_RE.search(f["path"])]
    for f in files:
        flags = [label for rx, label in SENSITIVE if re.search(rx, f["path"], re.I)]
        p = per_file_patch.get(f["path"], "")
        if DEBUG_RE.search(p):
            flags.append("debug output added")
        if TODO_RE.search(p):
            flags.append("TODO/FIXME added")
        if SECRETISH_RE.search(p):
            flags.append("possible hard-coded secret")
        if f["added"] + f["removed"] > 400:
            flags.append("large change (>400 lines): review in slices")
        if f["status"] == "deleted" and TEST_RE.search(f["path"]):
            flags.append("test deleted")
        f["flags"] = flags
    if src_changed and not tests_changed:
        flags_global.append("source files changed but no test files changed")
    if any(f["status"] == "deleted" and TEST_RE.search(f["path"]) for f in files):
        flags_global.append("one or more tests deleted: confirm intent")
    total = sum(f["added"] + f["removed"] for f in files)
    if total > 1000:
        flags_global.append(f"{total} changed lines: consider asking for the change to be split")

    areas = defaultdict(list)
    for f in files:
        areas[f["path"].split("/")[0] if "/" in f["path"] else "(root)"].append(f["path"])

    commits = []
    if not staged:
        log = git("log", "--format=%h %s", f"{base}..HEAD", check=False) or ""
        commits = log.splitlines()[:30]
    order = sorted(files, key=lambda f: (-len(f["flags"]), -(f["added"] + f["removed"])))
    return {
        "range": "staged changes" if staged else f"{base[:12]}...HEAD",
        "summary": {"files": len(files), "added": sum(f["added"] for f in files),
                    "removed": sum(f["removed"] for f in files), "source_files": len(src_changed),
                    "test_files": len(tests_changed)},
        "global_flags": flags_global, "commits": commits, "areas": dict(areas), "files": order,
    }


def to_markdown(r):
    s = r["summary"]
    out = [f"# Review context: {r['range']}", "",
           f"{s['files']} files, +{s['added']}/-{s['removed']} lines "
           f"({s['source_files']} source, {s['test_files']} test)", ""]
    if r["global_flags"]:
        out += ["## Change-level flags", ""] + [f"- {g}" for g in r["global_flags"]] + [""]
    if r["commits"]:
        out += ["## Commits", ""] + [f"- {c}" for c in r["commits"]] + [""]
    out += ["## Files, riskiest first", "", "| File | Status | +/- | Flags |", "|---|---|---:|---|"]
    for f in r["files"]:
        delta = "binary" if f["binary"] else f"+{f['added']}/-{f['removed']}"
        out.append(f"| `{f['path']}` | {f['status']} | {delta} | {', '.join(f['flags']) or ''} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        git("rev-parse", "--git-dir")
        report = analyze(resolve_base(args.base), args.staged)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not report["files"]:
        print("no changes in range", file=sys.stderr)
        return 0
    print(json.dumps(report, indent=2) if args.json else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
