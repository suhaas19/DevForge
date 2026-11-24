#!/usr/bin/env python3
"""Turn a coverage report into a ranked list of uncovered line ranges to target with new tests.

Usage:
    coverage_gaps.py REPORT [--only FILE ...] [--changed-since REF] [--top N] [--json]

Supported REPORT formats (auto-detected):
  * coverage.py JSON      (`coverage json` -> coverage.json)
  * LCOV                  (lcov.info from Jest/Istanbul/c8/vitest, `cargo llvm-cov --lcov`, etc.)
  * Cobertura XML         (coverage.xml from pytest-cov --cov-report=xml, JaCoCo converters, .NET)
  * Go cover profile      (`go test -coverprofile=cover.out`)

--changed-since REF limits the report to files changed since REF (git), which is
the usual target when adding tests for a change. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def ranges(lines):
    out, start, prev = [], None, None
    for n in sorted(set(lines)):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append((start, prev))
            start = prev = n
    if start is not None:
        out.append((start, prev))
    return out


def parse_coveragepy(data):
    files = {}
    for path, info in data.get("files", {}).items():
        executed = info.get("executed_lines", [])
        missing = info.get("missing_lines", [])
        files[path] = {"covered": len(executed), "total": len(executed) + len(missing), "missing": missing,
                       "missing_branches": info.get("missing_branches", [])}
    return files


def parse_lcov(text):
    files, cur = {}, None
    hits = {}
    for line in text.splitlines():
        if line.startswith("SF:"):
            cur, hits = line[3:].strip(), {}
        elif line.startswith("DA:") and cur:
            n, c = line[3:].split(",")[:2]
            hits[int(n)] = int(c)
        elif line.startswith("end_of_record") and cur:
            missing = [n for n, c in hits.items() if c == 0]
            files[cur] = {"covered": len(hits) - len(missing), "total": len(hits), "missing": missing, "missing_branches": []}
            cur = None
    return files


def parse_cobertura(text):
    root = ET.fromstring(text)
    sources = [s.text for s in root.iter("source") if s.text]
    files = defaultdict(lambda: {"covered": 0, "total": 0, "missing": [], "missing_branches": []})
    for cls in root.iter("class"):
        name = cls.get("filename")
        if sources and not Path(name).is_absolute():
            cand = Path(sources[0]) / name
            name = str(cand) if cand.exists() else name
        f = files[name]
        for ln in cls.iter("line"):
            n, hits = int(ln.get("number")), int(ln.get("hits", "0"))
            f["total"] += 1
            if hits:
                f["covered"] += 1
            else:
                f["missing"].append(n)
            if ln.get("branch") == "true" and ln.get("condition-coverage", "100%").split("%")[0] != "100":
                f["missing_branches"].append(n)
    return dict(files)


def parse_goprofile(text):
    blocks = defaultdict(dict)
    for line in text.splitlines()[1:]:
        try:
            loc, nstmt, count = line.rsplit(" ", 2)
            path, span = loc.rsplit(":", 1)
            start, end = span.split(",")
            s_line, e_line = int(start.split(".")[0]), int(end.split(".")[0])
        except ValueError:
            continue
        for n in range(s_line, e_line + 1):
            blocks[path][n] = max(blocks[path].get(n, 0), int(count))
    return {p: {"covered": sum(1 for c in m.values() if c), "total": len(m),
                "missing": [n for n, c in m.items() if c == 0], "missing_branches": []} for p, m in blocks.items()}


def load(report: Path):
    text = report.read_text(encoding="utf-8", errors="ignore")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return parse_coveragepy(json.loads(text)), "coverage.py json"
    if stripped.startswith("<"):
        return parse_cobertura(text), "cobertura xml"
    if stripped.startswith("mode:"):
        return parse_goprofile(text), "go coverprofile"
    if "SF:" in text and "end_of_record" in text:
        return parse_lcov(text), "lcov"
    raise ValueError("unrecognized coverage format (expected coverage.py JSON, LCOV, Cobertura XML or Go profile)")


def changed_files(ref):
    out = subprocess.run(["git", "diff", "--name-only", f"{ref}...HEAD"], capture_output=True, text=True)
    if out.returncode != 0:
        out = subprocess.run(["git", "diff", "--name-only", ref], capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l]


def matches(path, wanted):
    p = path.replace("\\", "/")
    return any(p == w or p.endswith("/" + w) or w.endswith("/" + p) for w in wanted)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("report")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--changed-since")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        files, fmt = load(Path(args.report))
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    wanted = list(args.only)
    if args.changed_since:
        wanted += changed_files(args.changed_since)
    if wanted:
        files = {p: f for p, f in files.items() if matches(p, wanted)}

    rows = []
    for path, f in files.items():
        pct = 100.0 * f["covered"] / f["total"] if f["total"] else 100.0
        rows.append({"file": path, "percent": round(pct, 1), "covered": f["covered"], "total": f["total"],
                     "uncovered": len(f["missing"]), "ranges": ranges(f["missing"]),
                     "partial_branches": sorted(set(b if isinstance(b, int) else b[0] for b in f["missing_branches"]))})
    rows.sort(key=lambda r: (-r["uncovered"], r["percent"]))
    total_cov = sum(f["covered"] for f in files.values())
    total = sum(f["total"] for f in files.values())
    summary = {"format": fmt, "files": len(rows), "line_coverage": round(100.0 * total_cov / total, 1) if total else None}

    if args.json:
        print(json.dumps({"summary": summary, "files": rows[: args.top]}, indent=2))
        return 0
    print(f"# Coverage gaps ({fmt})\n")
    print(f"Overall line coverage across {summary['files']} file(s): {summary['line_coverage']}%\n")
    print("| File | Cover | Uncovered | Uncovered line ranges | Partial branches |")
    print("|---|---:|---:|---|---|")
    for r in rows[: args.top]:
        if not r["uncovered"] and not r["partial_branches"]:
            continue
        rs = ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in r["ranges"][:12])
        if len(r["ranges"]) > 12:
            rs += ", …"
        pb = ", ".join(map(str, r["partial_branches"][:10]))
        print(f"| `{r['file']}` | {r['percent']}% | {r['uncovered']} | {rs} | {pb} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
