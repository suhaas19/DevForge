---
name: performance-profiling
description: Diagnoses and fixes slow code by measuring first, profiling to find the real bottleneck, changing one thing at a time, and proving the speedup with repeated, statistically honest benchmarks. Use when the user says something is slow, wants to speed up, optimize, reduce latency or memory, fix timeouts, compare two implementations, or asks "why is this taking so long", and before claiming any performance improvement.
license: MIT
metadata:
  version: "1.0.0"
---

# Performance Profiling

Intuition about where time goes is usually wrong, and single timings lie.
Mytkowicz et al. (ASPLOS 2009) showed that innocuous details like environment size
or link order can shift measured performance enough to flip conclusions. So:
measure, profile, change one thing, measure again with repeats, and report
uncertainty.

## When to use

- "This is slow", "speed up X", timeouts, high latency, high memory, CPU spikes.
- Comparing two implementations or library versions.
- Before writing "this is faster" anywhere.
- **Not for:** premature micro-optimization of code nobody reported as slow. Say so and ask whether it matters.

## Workflow

- [ ] 1. **Define the target.** Which operation, on what input size, measured how (wall time, p95 latency, peak RSS, throughput)? What would be good enough? If the user has no target, ask the user for one; "faster" with no goal never ends.
- [ ] 2. **Build a repeatable benchmark** that exercises the slow path with realistic data and runs in seconds to a minute. Then get a baseline: `python3 scripts/bench.py "<command>" --runs 20`. Check the CV it reports; above ~10% the machine or workload is too noisy to detect small wins. Fix that first (close other load, fixed input, warm caches deliberately or flush them deliberately).
- [ ] 3. **Profile, do not guess.** Use the profiler for the stack in [references/profilers.md](references/profilers.md). Look for the top few frames by *inclusive* time, then *self* time. Classify the bottleneck: CPU, I/O wait, lock contention, allocation/GC, N+1 queries, network round trips.
- [ ] 4. **Pick the change with the best expected payoff.** Usually algorithmic (O(n²) → O(n log n), batching, caching, avoiding repeated work) before micro-level. Estimate the ceiling: if the hot function is 30% of runtime, making it free gives at most 1.43x (Amdahl).
- [ ] 5. **Change one thing**, keep the old version reachable (flag, branch, or copy) so you can A/B it.
- [ ] 6. **Verify correctness first**: tests pass and outputs are identical (`safe-refactoring`'s `golden.py` works well for this).
- [ ] 7. **Measure the A/B:** `python3 scripts/bench.py "<baseline cmd>" "<candidate cmd>" --runs 30`. Runs are interleaved; the verdict uses a bootstrap 95% CI on the median ratio. Only claim a win if the interval excludes 1.0x.
- [ ] 8. **Repeat 3-7** until the target is met or the profile is flat. Then report.

### Common bottlenecks and first moves

| Profile shows | First move |
|---|---|
| Many identical DB queries | batch/join (fix N+1), add an index for the filter, select only needed columns |
| Time in JSON/serialization | serialize less, stream, use a faster codec only after reducing volume |
| Time in regex or string building in loops | precompile, use join/builders, avoid repeated parsing |
| High GC/allocation | reuse buffers, avoid per-item temporary objects, use generators/streams |
| Waiting on network/disk | concurrency (bounded), caching, fewer round trips, compression |
| Lock contention | shrink critical sections, shard locks, lock-free structures only as last resort |
| Pure Python numeric loops | vectorize (NumPy/pandas/polars) before reaching for native extensions |

## Output template

```markdown
## Performance: <operation>
**Target:** p95 < 200 ms on 10k-row input. **Result:** met.
| Version | Median | p95 | CV | Notes |
|---|---:|---:|---:|---|
| baseline | 1.84 s | 1.92 s | 2.1% | |
| batch queries | 0.41 s | 0.45 s | 3.0% | 4.49x, 95% CI [4.31, 4.66] |
**Bottleneck found:** `orders/service.py:88`: 1 query per line item (N+1), 71% of wall time in profile.
**Change:** single `IN (...)` query + dict lookup. Outputs identical (golden 20/20).
**Measured on:** machine, Python 3.12, input `bench/orders_10k.json`, 30 interleaved runs.
```

## Gotchas

- **Warm vs cold.** First runs pay for imports, JIT, caches and disk reads. `bench.py` does warmup runs; decide whether the user cares about cold start and measure that separately if so.
- **Benchmark the real path.** A micro-benchmark of one function can improve while the endpoint does not. Confirm end to end.
- **Debug builds, profilers and logging distort timings.** Profile to find the hotspot; benchmark without the profiler.
- **Laptops throttle.** Plugged in, no heavy background apps, and interleaved A/B runs reduce bias.
- **Caching hides problems.** Make sure a "faster" result is not just a warm cache the baseline did not have.
- **Do not trade correctness or readability for tiny gains.** Below ~5% on a non-critical path, mention it and recommend against the change.
