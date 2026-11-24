#!/usr/bin/env python3
"""Minimal, dependency-free eval harness for LLM features: cases in, pass rates with confidence intervals out.

Usage:
    eval_harness.py run  --cases evals/cases.jsonl --target mypkg.app:answer [--repeats 3] [--out results.jsonl]
    eval_harness.py compare results_a.jsonl results_b.jsonl
    eval_harness.py demo                     # self-contained example run

cases.jsonl: one JSON object per line:
    {"id": "refund-1", "input": "...", "tags": ["refunds"],
     "checks": [{"type": "contains", "value": "30 days"},
                {"type": "not_contains", "value": "I'm not sure"},
                {"type": "regex", "value": "\\\\bREF-\\\\d{6}\\\\b"},
                {"type": "equals", "value": "yes"},
                {"type": "json_keys", "value": ["order_id", "status"]},
                {"type": "max_chars", "value": 600},
                {"type": "judge", "value": "Answer cites the refund policy and gives the deadline"}]}

--target is "module:function"; the function takes the case "input" (str or dict)
and returns a string. A "judge" check calls --judge "module:function", which
receives (criterion, input, output) and returns True/False; keep judges binary
and specific, and spot-check them against human labels before trusting them.

Reports the pass rate per check type and tag with Wilson 95% intervals, lists
failing cases, and writes every result to --out for later comparison.
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path


def wilson(passed, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = passed / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def load_callable(spec):
    if not spec:
        return None
    mod, _, fn = spec.partition(":")
    sys.path.insert(0, str(Path.cwd()))
    return getattr(importlib.import_module(mod), fn)


def run_check(check, case, output, judge):
    kind, val = check["type"], check.get("value")
    out = output if isinstance(output, str) else json.dumps(output)
    if kind == "contains":
        return val.lower() in out.lower()
    if kind == "not_contains":
        return val.lower() not in out.lower()
    if kind == "equals":
        return out.strip() == str(val).strip()
    if kind == "regex":
        return re.search(val, out) is not None
    if kind == "max_chars":
        return len(out) <= int(val)
    if kind == "json_keys":
        try:
            obj = json.loads(out)
        except ValueError:
            return False
        return isinstance(obj, dict) and all(k in obj for k in val)
    if kind == "judge":
        if judge is None:
            raise ValueError("case uses a 'judge' check but no --judge was given")
        return bool(judge(val, case.get("input"), out))
    raise ValueError(f"unknown check type {kind!r}")


def run(args):
    target = load_callable(args.target)
    judge = load_callable(args.judge)
    cases = [json.loads(l) for l in Path(args.cases).read_text(encoding="utf-8").splitlines() if l.strip()]
    results = []
    for case in cases:
        for rep in range(args.repeats):
            t0 = time.perf_counter()
            try:
                output, error = target(case["input"]), None
            except Exception as exc:  # the system under test failing is a result, not a crash
                output, error = "", f"{type(exc).__name__}: {exc}"
            latency = time.perf_counter() - t0
            checks = []
            for chk in case.get("checks", []):
                try:
                    ok = error is None and run_check(chk, case, output, judge)
                except ValueError as exc:
                    print(f"error in case {case.get('id')}: {exc}", file=sys.stderr)
                    return 2
                checks.append({"type": chk["type"], "value": chk.get("value"), "passed": ok})
            results.append({"id": case.get("id"), "repeat": rep, "tags": case.get("tags", []), "output": output,
                            "error": error, "latency_s": round(latency, 4), "checks": checks,
                            "passed": error is None and all(c["passed"] for c in checks)})
    if args.out:
        Path(args.out).write_text("\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")
    report(results)
    return 0


def report(results, label=""):
    n = len(results)
    passed = sum(r["passed"] for r in results)
    lo, hi = wilson(passed, n)
    print(f"{label}overall: {passed}/{n} = {passed / n:.1%}  (95% CI {lo:.1%}-{hi:.1%})")
    lat = [r["latency_s"] for r in results]
    if lat:
        print(f"{label}latency: median {statistics.median(lat):.3f}s, max {max(lat):.3f}s")
    by_type = defaultdict(lambda: [0, 0])
    for r in results:
        for c in r["checks"]:
            by_type[c["type"]][0] += c["passed"]
            by_type[c["type"]][1] += 1
    if by_type:
        print(f"{label}by check type: " + ", ".join(f"{k} {p}/{t}" for k, (p, t) in sorted(by_type.items())))
    by_tag = defaultdict(lambda: [0, 0])
    for r in results:
        for t in r["tags"] or ["(untagged)"]:
            by_tag[t][0] += r["passed"]
            by_tag[t][1] += 1
    if len(by_tag) > 1:
        print(f"{label}by tag: " + ", ".join(f"{k} {p}/{t}" for k, (p, t) in sorted(by_tag.items())))
    flaky = defaultdict(set)
    for r in results:
        flaky[r["id"]].add(r["passed"])
    unstable = [cid for cid, s in flaky.items() if len(s) > 1]
    if unstable:
        print(f"{label}unstable across repeats ({len(unstable)}): {', '.join(map(str, unstable[:10]))}")
    failing = sorted({r["id"] for r in results if not r["passed"]} - set(unstable))
    if failing:
        print(f"{label}always failing ({len(failing)}): {', '.join(map(str, failing[:15]))}")
    return passed, n


def compare(args):
    a = [json.loads(l) for l in Path(args.a).read_text().splitlines() if l.strip()]
    b = [json.loads(l) for l in Path(args.b).read_text().splitlines() if l.strip()]
    pa, na = report(a, "A ")
    print()
    pb, nb = report(b, "B ")
    lo_a, hi_a = wilson(pa, na)
    lo_b, hi_b = wilson(pb, nb)
    print(f"\ndelta B-A: {pb / nb - pa / na:+.1%}", end="  ")
    print("(intervals overlap: not a reliable difference, add cases or repeats)" if lo_b <= hi_a and lo_a <= hi_b
          else "(intervals do not overlap)")
    ra = {(r["id"], r["repeat"]): r["passed"] for r in a}
    regressions = sorted({k[0] for k, v in ra.items() if v and not next((r["passed"] for r in b if (r["id"], r["repeat"]) == k), True)})
    if regressions:
        print(f"regressed in B: {', '.join(map(str, regressions[:20]))}")
    return 0


def demo(_args):
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    (tmp / "demo_app.py").write_text(
        "def answer(q):\n"
        "    if 'refund' in q.lower():\n"
        "        return 'Refunds are accepted within 30 days. Ref REF-123456.'\n"
        "    return '{\"order_id\": 7, \"status\": \"shipped\"}'\n", encoding="utf-8")
    cases = [
        {"id": "refund-window", "input": "What is the refund policy?", "tags": ["refunds"],
         "checks": [{"type": "contains", "value": "30 days"}, {"type": "regex", "value": r"REF-\d{6}"}]},
        {"id": "order-status", "input": "Where is order 7?", "tags": ["orders"],
         "checks": [{"type": "json_keys", "value": ["order_id", "status"]}]},
        {"id": "refund-tone", "input": "refund please", "tags": ["refunds"],
         "checks": [{"type": "not_contains", "value": "accepted"}]},
    ]
    (tmp / "cases.jsonl").write_text("\n".join(json.dumps(c) for c in cases), encoding="utf-8")
    sys.path.insert(0, str(tmp))
    ns = argparse.Namespace(cases=str(tmp / "cases.jsonl"), target="demo_app:answer", judge=None, repeats=2,
                            out=str(tmp / "results.jsonl"))
    print(f"demo files in {tmp}\n")
    return run(ns)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--cases", required=True)
    r.add_argument("--target", required=True, help="module:function under test")
    r.add_argument("--judge", help="module:function(criterion, input, output) -> bool")
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--out")
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    sub.add_parser("demo")
    args = ap.parse_args(argv)
    return {"run": run, "compare": compare, "demo": demo}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
