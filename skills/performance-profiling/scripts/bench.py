#!/usr/bin/env python3
"""Benchmark one command, or compare two, with warmups, repeats and honest statistics.

Usage:
    bench.py "CMD" [--runs 20] [--warmup 3] [--json]
    bench.py "BASELINE_CMD" "CANDIDATE_CMD" [--runs 30] [--warmup 3] [--json]

Reports min / median / mean / stdev / p95 and the coefficient of variation for
each command. With two commands it runs them interleaved (A B A B ...) so drift
in machine state hits both equally, then reports the median speedup with a 95%
bootstrap confidence interval. If the interval crosses 1.0x the difference is
not distinguishable from noise: say so instead of claiming a win.

Commands run through the shell. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import subprocess
import sys
import time


def run_once(cmd, timeout):
    t0 = time.perf_counter()
    res = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout)
    dt = time.perf_counter() - t0
    if res.returncode != 0:
        raise RuntimeError(f"command failed (exit {res.returncode}): {cmd}\n{res.stderr.decode(errors='ignore')[-500:]}")
    return dt


def describe(samples):
    s = sorted(samples)
    mean = statistics.fmean(s)
    sd = statistics.stdev(s) if len(s) > 1 else 0.0
    p95 = s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]
    return {"n": len(s), "min": s[0], "median": statistics.median(s), "mean": mean, "stdev": sd,
            "p95": p95, "max": s[-1], "cv_percent": 100 * sd / mean if mean else 0.0}


def bootstrap_speedup(a, b, iters=5000, seed=7):
    """Ratio median(a)/median(b): >1 means b (candidate) is faster."""
    rng = random.Random(seed)
    ratios = []
    for _ in range(iters):
        ra = [rng.choice(a) for _ in a]
        rb = [rng.choice(b) for _ in b]
        ratios.append(statistics.median(ra) / statistics.median(rb))
    ratios.sort()
    return statistics.median(a) / statistics.median(b), ratios[int(0.025 * iters)], ratios[int(0.975 * iters)]


def fmt(t):
    return f"{t * 1e3:.2f} ms" if t < 1 else f"{t:.3f} s"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("commands", nargs="+", help="one command, or baseline and candidate")
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if len(args.commands) > 2:
        ap.error("give one command or two (baseline, candidate)")

    samples = {c: [] for c in args.commands}
    try:
        for c in args.commands:
            for _ in range(args.warmup):
                run_once(c, args.timeout)
        for _ in range(args.runs):
            for c in args.commands:  # interleave to spread drift evenly
                samples[c].append(run_once(c, args.timeout))
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = {"runs": args.runs, "warmup": args.warmup, "commands": {c: describe(s) for c, s in samples.items()}}
    if len(args.commands) == 2:
        a, b = samples[args.commands[0]], samples[args.commands[1]]
        sp, lo, hi = bootstrap_speedup(a, b)
        verdict = ("candidate faster" if lo > 1 else "candidate slower" if hi < 1 else "no significant difference")
        result["comparison"] = {"speedup_median": sp, "ci95": [lo, hi], "verdict": verdict}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    for c, d in result["commands"].items():
        print(f"{c}\n  median {fmt(d['median'])}  mean {fmt(d['mean'])} ± {fmt(d['stdev'])}  "
              f"min {fmt(d['min'])}  p95 {fmt(d['p95'])}  CV {d['cv_percent']:.1f}%  (n={d['n']})")
        if d["cv_percent"] > 10:
            print("  ! CV above 10%: noisy machine or workload; close other programs, pin CPU, or raise --runs")
    if "comparison" in result:
        cmp_ = result["comparison"]
        print(f"\nspeedup (baseline/candidate medians): {cmp_['speedup_median']:.3f}x  "
              f"95% CI [{cmp_['ci95'][0]:.3f}, {cmp_['ci95'][1]:.3f}]  -> {cmp_['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
