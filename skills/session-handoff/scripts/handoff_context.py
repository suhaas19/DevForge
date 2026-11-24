#!/usr/bin/env python3
"""Collect the mechanical facts a handoff note needs: branch, commits, uncommitted work, TODOs, recent files.

Usage:
    handoff_context.py [--base REF] [--json]

Prints Markdown (or JSON) that the agent pastes into the "State of the code"
section of HANDOFF.md. It gathers facts only; the decisions, dead ends and next
steps must come from the session itself. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys


def git(*args):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else ""


def default_base():
    for cand in ("origin/main", "main", "origin/master", "master"):
        if git("rev-parse", "--verify", "--quiet", cand):
            mb = git("merge-base", "HEAD", cand)
            if mb and mb != git("rev-parse", "HEAD"):
                return mb
    return ""


def gather(base):
    if not git("rev-parse", "--git-dir"):
        return {"error": "not a git repository"}
    base = base or default_base()
    status = git("status", "--porcelain=v1", "--branch")
    lines = status.splitlines()
    branch_line = lines[0] if lines and lines[0].startswith("##") else ""
    changes = [l for l in lines if not l.startswith("##")]
    added_todos = []
    diff = git("diff", "HEAD", "-U0") + "\n" + (git("diff", f"{base}...HEAD", "-U0") if base else "")
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++") and re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line):
            added_todos.append(f"{current}: {line[1:].strip()[:120]}")
    return {
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "tracking": branch_line[3:] if branch_line else "",
        "base": base[:12] if base else None,
        "head": git("log", "-1", "--format=%h %s"),
        "commits_on_branch": git("log", "--format=%h %s", f"{base}..HEAD").splitlines()[:25] if base else [],
        "uncommitted": changes[:50],
        "diffstat_uncommitted": git("diff", "HEAD", "--stat").splitlines()[-1:] ,
        "stashes": git("stash", "list").splitlines()[:5],
        "todos_added": sorted(set(added_todos))[:25],
        "recently_changed_files": git("log", "-n", "15", "--name-only", "--format=").splitlines()[:30],
    }


def to_markdown(d):
    if "error" in d:
        return f"_{d['error']}_\n"
    out = ["### State of the code (generated)", "",
           f"- Branch: `{d['branch']}`" + (f" ({d['tracking']})" if d["tracking"] else ""),
           f"- HEAD: {d['head']}"]
    if d["base"]:
        out.append(f"- Branched from: `{d['base']}`")
    if d["commits_on_branch"]:
        out += ["", "Commits on this branch:", ""] + [f"- {c}" for c in d["commits_on_branch"]]
    out += ["", "Uncommitted changes:", ""] + ([f"- `{c}`" for c in d["uncommitted"]] or ["- none (working tree clean)"])
    if d["diffstat_uncommitted"] and d["diffstat_uncommitted"][0]:
        out.append(f"- {d['diffstat_uncommitted'][0].strip()}")
    if d["stashes"]:
        out += ["", "Stashes:", ""] + [f"- {s}" for s in d["stashes"]]
    if d["todos_added"]:
        out += ["", "TODO/FIXME added in this work:", ""] + [f"- {t}" for t in d["todos_added"]]
    seen, recent = set(), []
    for f in d["recently_changed_files"]:
        if f and f not in seen:
            seen.add(f)
            recent.append(f)
    if recent:
        out += ["", "Recently changed files:", ""] + [f"- `{f}`" for f in recent[:15]]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    data = gather(args.base)
    print(json.dumps(data, indent=2) if args.json else to_markdown(data))
    return 0 if "error" not in data else 2


if __name__ == "__main__":
    sys.exit(main())
