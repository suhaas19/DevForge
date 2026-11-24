#!/usr/bin/env python3
"""Golden-master (characterization) testing: record a program's current behavior, then verify a refactor kept it.

Usage:
    golden.py record --cmd "python report.py {input}" --inputs 'samples/*.csv' [--dir .golden]
    golden.py verify [--dir .golden] [--show-diff]
    golden.py record --cmd "./cli --format json" --stdin-inputs 'cases/*.txt'

`record` runs the command once per input file and stores exit code, stdout and
stderr under --dir (default .golden/) with a manifest. `verify` re-runs the
same commands and fails (exit 1) on any difference. Use it before touching code
that has no tests: record first, refactor, verify after every step.

Put volatile output (timestamps, temp paths, PIDs) behind --scrub REGEX
(repeatable) so it does not cause false failures. Standard library only.
"""
from __future__ import annotations

import argparse
import difflib
import glob
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_SCRUB = [r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?\b", r"/tmp/[\w./-]+",
                 r"\b0x[0-9a-f]{6,}\b"]


def scrub(text, patterns):
    for p in patterns:
        text = re.sub(p, "<SCRUBBED>", text)
    return text


def run_case(case, timeout):
    stdin = Path(case["stdin"]).read_bytes() if case.get("stdin") else None
    res = subprocess.run(case["cmd"], shell=True, input=stdin, capture_output=True, timeout=timeout)
    return res.returncode, res.stdout.decode(errors="replace"), res.stderr.decode(errors="replace")


def case_id(cmd):
    return hashlib.sha1(cmd.encode()).hexdigest()[:12]


def record(args):
    gdir = Path(args.dir)
    gdir.mkdir(parents=True, exist_ok=True)
    cases = []
    if args.inputs:
        for inp in sorted(glob.glob(args.inputs, recursive=True)):
            q = shlex.quote(inp)
            cmd = args.cmd.replace("{input}", q) if "{input}" in args.cmd else f"{args.cmd} {q}"
            cases.append({"cmd": cmd, "input": inp})
    elif args.stdin_inputs:
        for inp in sorted(glob.glob(args.stdin_inputs, recursive=True)):
            cases.append({"cmd": args.cmd, "stdin": inp, "input": inp})
    else:
        cases.append({"cmd": args.cmd, "input": None})
    if not cases:
        print("error: no inputs matched", file=sys.stderr)
        return 2
    patterns = DEFAULT_SCRUB + (args.scrub or [])
    for c in cases:
        c["id"] = case_id(c["cmd"] + (c.get("stdin") or ""))
        code, out, err = run_case(c, args.timeout)
        c["exit"] = code
        (gdir / f"{c['id']}.out").write_text(scrub(out, patterns), encoding="utf-8")
        (gdir / f"{c['id']}.err").write_text(scrub(err, patterns), encoding="utf-8")
    manifest = {"scrub": patterns, "timeout": args.timeout, "cases": cases}
    (gdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"recorded {len(cases)} case(s) in {gdir}/ (exit codes: "
          f"{sorted(set(c['exit'] for c in cases))}). Commit or keep this directory until the refactor is done.")
    return 0


def verify(args):
    gdir = Path(args.dir)
    try:
        manifest = json.loads((gdir / "manifest.json").read_text(encoding="utf-8"))
    except OSError:
        print(f"error: no recording in {gdir}/; run `golden.py record` first", file=sys.stderr)
        return 2
    failures = 0
    for c in manifest["cases"]:
        code, out, err = run_case(c, manifest.get("timeout", 60))
        out, err = scrub(out, manifest["scrub"]), scrub(err, manifest["scrub"])
        exp_out = (gdir / f"{c['id']}.out").read_text(encoding="utf-8")
        exp_err = (gdir / f"{c['id']}.err").read_text(encoding="utf-8")
        problems = []
        if code != c["exit"]:
            problems.append(f"exit {c['exit']} -> {code}")
        if out != exp_out:
            problems.append("stdout differs")
        if err != exp_err and not args.ignore_stderr:
            problems.append("stderr differs")
        if problems:
            failures += 1
            print(f"FAIL {c.get('input') or c['cmd']}: {', '.join(problems)}")
            if args.show_diff and out != exp_out:
                diff = difflib.unified_diff(exp_out.splitlines(), out.splitlines(), "recorded", "now", lineterm="", n=2)
                print("\n".join(list(diff)[:60]))
    total = len(manifest["cases"])
    print(f"\n{total - failures}/{total} case(s) unchanged")
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("record")
    r.add_argument("--cmd", required=True)
    g = r.add_mutually_exclusive_group()
    g.add_argument("--inputs", help="glob of input files substituted for {input}")
    g.add_argument("--stdin-inputs", help="glob of files fed to stdin")
    r.add_argument("--scrub", action="append", help="regex of volatile output to mask (repeatable)")
    r.add_argument("--dir", default=".golden")
    r.add_argument("--timeout", type=float, default=60)
    v = sub.add_parser("verify")
    v.add_argument("--dir", default=".golden")
    v.add_argument("--show-diff", action="store_true")
    v.add_argument("--ignore-stderr", action="store_true")
    args = ap.parse_args(argv)
    return record(args) if args.mode == "record" else verify(args)


if __name__ == "__main__":
    sys.exit(main())
