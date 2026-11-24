# Test design techniques

## Equivalence classes and boundaries
Split each input into classes that should behave the same, then test one value per
class plus the values at every boundary.

| Input | Classes | Boundary values |
|---|---|---|
| integer in [1, 100] | below, inside, above | 0, 1, 2, 99, 100, 101 |
| string length ≤ 255 | empty, typical, max, over max | "", "a", 255 chars, 256 chars |
| collection | empty, one, many, duplicates | [], [x], [x, y, z], [x, x] |
| date | past, today, future, DST change, Feb 29 | midnight, 23:59:59, leap day |
| money | zero, negative, rounding edge | 0, -0.01, 0.005, very large |

## Error paths
- Every `raise`/`throw`/error return in the unit gets at least one test.
- Downstream failure: dependency times out, returns 500, returns malformed data, returns empty.
- Invalid types or missing fields at the boundary of the module (not deep inside).

## State and sequences
- Operations in a different order (close before open, double close, retry after failure).
- Idempotency: calling twice has the same effect as once, where it should.

## Properties (property-based testing)
Good properties for generated inputs:
- **Round trip:** `decode(encode(x)) == x`, `parse(format(x)) == x`.
- **Idempotence:** `f(f(x)) == f(x)` (normalizers, formatters, dedupe).
- **Invariants:** output sorted, length preserved, sum preserved, no duplicates.
- **Oracle:** compare against a slow but obviously correct reference implementation.
- **Metamorphic:** a known change to the input causes a known change to the output (adding a filter never returns more rows).

Use the project's existing library (Hypothesis, fast-check, proptest, QuickCheck, jqwik). If none exists, ask before adding one.

## Test doubles: which one
- **Fake** (in-memory implementation): best for repositories, queues, clocks.
- **Stub** (canned answers): for simple dependencies with no behavior you care about.
- **Mock** (verifies interactions): only when the interaction *is* the behavior (an email was sent, a payment was captured exactly once).
- Prefer real lightweight dependencies (temp directories, SQLite, local servers) when they are fast.

## Naming
`test_<unit>_<condition>_<expected>`, or a sentence in frameworks that allow it:
`it("rejects refunds after 30 days")`. The name should tell a reader what broke when it fails.

## Flakiness sources to eliminate
Real time and `sleep`, random seeds, test order dependence, shared global state,
network, file system leftovers, unordered collection comparisons, floating-point
equality (use approx), time zones on CI.
