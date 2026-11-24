# Profilers by stack

Start with the default in each row; the alternatives are for when it is not available
or when you need a different view.

| Stack | CPU (default first) | Memory | Notes |
|---|---|---|---|
| Python | `py-spy record -o prof.svg -- python app.py` (sampling, low overhead, attach with `--pid`) · `python -m cProfile -o prof.out app.py` then `python -m pstats prof.out` (`sort cumtime`, `stats 25`) · `scalene` (CPU + memory + GPU) | `tracemalloc` snapshots · `memray run app.py` · `scalene` | `pyinstrument` gives readable call trees for web requests |
| Node.js | `node --cpu-prof app.js` (open `.cpuprofile` in Chrome DevTools) · `0x app.js` (flame graph) · `clinic flame` | `node --heap-prof` · `--inspect` + DevTools heap snapshot | `clinic doctor` triages event-loop delay vs I/O vs GC |
| Go | `go test -bench . -cpuprofile cpu.out` then `go tool pprof -http=: cpu.out` · `net/http/pprof` for live services | `-memprofile mem.out` · `pprof -sample_index=alloc_space` | `go test -bench . -benchmem -count 10` + `benchstat` for A/B |
| Rust | `cargo flamegraph` · `perf record -g` + `perf report` | `heaptrack` · `dhat` crate | Benchmark with `criterion` (has statistics built in) |
| JVM | async-profiler (`asprof -d 30 -f flame.html <pid>`) · JDK Flight Recorder (`-XX:StartFlightRecording`) | JFR allocation events · heap dump + Eclipse MAT | JMH for micro-benchmarks; never hand-roll JVM timing loops |
| .NET | `dotnet-trace collect` · Visual Studio profiler | `dotnet-counters` · `dotnet-gcdump` | BenchmarkDotNet for micro-benchmarks |
| Ruby | `stackprof` · `rbspy` | `memory_profiler` | `benchmark-ips` for A/B |
| Browser/frontend | DevTools Performance panel (record, look for long tasks > 50 ms) · Lighthouse | DevTools Memory (heap snapshots, allocation timeline) | React Profiler for re-render storms |
| SQL | `EXPLAIN (ANALYZE, BUFFERS)` (Postgres) · `EXPLAIN ANALYZE` (MySQL 8) · query log with durations | | Look for seq scans on large tables, row-estimate mismatches, sorts spilling to disk |
| Whole system (Linux) | `perf top` / `perf record -g` · `htop` · `pidstat 1` | `vmstat 1` · `/usr/bin/time -v cmd` (peak RSS) | `iostat -x 1` for disk, `ss -s` for sockets |

## Reading a profile
1. Sort by **inclusive** (cumulative) time to find which high-level operation is expensive.
2. Then by **self** time to find the leaf doing the work.
3. Many small calls each cheap but called millions of times → reduce the call count (algorithm, batching), not the per-call cost.
4. Flame graphs: width is time; look for wide plateaus near the top.

## Reporting environment
Always record: hardware (CPU model, cores), OS, runtime version, input used, number of runs, and whether caches were warm.
