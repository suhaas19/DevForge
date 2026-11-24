#!/usr/bin/env python3
"""Shrink a failure-inducing input to a minimal one with delta debugging (Zeller's ddmin).

Usage:
    ddmin.py INPUT_FILE --test "CMD {file}" [--unit line|char|token] [--out FILE]
             [--interesting-exit 0] [--timeout 30] [--max-tests 5000]

The test command receives a candidate file path in place of `{file}` (or as the
last argument when `{file}` is absent). A candidate is "interesting" (still
reproduces the bug) when the command exits with --interesting-exit (default 0).
Write the test so that exit 0 means "the bug still happens", for example:

    ddmin.py crash.json --test "python repro.py {file} 2>&1 | grep -q 'KeyError: id'"

The command runs through the shell, so pipes and grep work. Never point it at
anything destructive: it runs many times. Result goes to INPUT.min (or --out).
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


def split(text, unit):
    if unit == "line":
        return text.splitlines(keepends=True)
    if unit == "token":
        return re.findall(r"\s+|\w+|[^\w\s]", text)
    return list(text)


class Tester:
    def __init__(self, cmd, exit_code, timeout, max_tests, suffix):
        self.cmd, self.exit_code, self.timeout, self.max_tests = cmd, exit_code, timeout, max_tests
        self.suffix, self.cache, self.runs = suffix, {}, 0

    def __call__(self, parts):
        key = "".join(parts)
        if key in self.cache:
            return self.cache[key]
        if self.runs >= self.max_tests:
            raise RuntimeError("max-tests reached")
        self.runs += 1
        fd, path = tempfile.mkstemp(suffix=self.suffix)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(key)
            quoted = shlex.quote(path)
            cmd = self.cmd.replace("{file}", quoted) if "{file}" in self.cmd else f"{self.cmd} {quoted}"
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, timeout=self.timeout)
                ok = res.returncode == self.exit_code
            except subprocess.TimeoutExpired:
                ok = False
        finally:
            os.unlink(path)
        self.cache[key] = ok
        return ok


def ddmin(parts, test, log=lambda *_: None):
    """Classic ddmin: returns a 1-minimal subsequence that still passes `test`."""
    n = 2
    while len(parts) >= 2:
        chunk = max(1, len(parts) // n)
        subsets = [parts[i:i + chunk] for i in range(0, len(parts), chunk)]
        reduced = False
        for i, subset in enumerate(subsets):                      # try each subset alone
            if test(subset):
                parts, n, reduced = subset, 2, True
                break
        if not reduced:
            for i in range(len(subsets)):                        # try each complement
                complement = [x for j, s in enumerate(subsets) if j != i for x in s]
                if test(complement):
                    parts, n, reduced = complement, max(n - 1, 2), True
                    break
        if reduced:
            log(len(parts))
            continue
        if n >= len(parts):
            break
        n = min(len(parts), n * 2)
    return parts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input")
    ap.add_argument("--test", required=True, help='shell command; "{file}" is replaced by the candidate path')
    ap.add_argument("--unit", choices=["line", "char", "token"], default="line")
    ap.add_argument("--out")
    ap.add_argument("--interesting-exit", type=int, default=0)
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--max-tests", type=int, default=5000)
    args = ap.parse_args(argv)

    src = Path(args.input)
    text = src.read_text(encoding="utf-8", errors="surrogateescape")
    tester = Tester(args.test, args.interesting_exit, args.timeout, args.max_tests, src.suffix)
    parts = split(text, args.unit)
    if not tester(parts):
        print("error: the original input is not interesting (the test does not reproduce the failure). "
              "Fix the test command first.", file=sys.stderr)
        return 2
    print(f"start: {len(parts)} {args.unit}s")
    try:
        result = ddmin(parts, tester, log=lambda n: print(f"  reduced to {n} {args.unit}s (tests run: {tester.runs})"))
        if args.unit == "line" and len(result) > 1:  # refine inside lines too
            result = split("".join(result), "token")
            result = ddmin(result, tester, log=lambda n: print(f"  reduced to {n} tokens (tests run: {tester.runs})"))
    except RuntimeError as exc:
        print(f"stopped early: {exc}; writing best result so far", file=sys.stderr)
        result = parts
    out = Path(args.out or f"{src}.min")
    out.write_text("".join(result), encoding="utf-8", errors="surrogateescape")
    print(f"done: {len(''.join(result))} chars (from {len(text)}), {tester.runs} test runs -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
