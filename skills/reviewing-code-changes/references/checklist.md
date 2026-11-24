# Review checklist

Use this as a menu, not a form. Spend time where the change carries risk.

## Correctness
- Does the code do what the PR says? Trace one realistic input through the change.
- Boundaries: empty, one, many; zero and negative numbers; max sizes; Unicode; time zones and DST; leap years.
- Off-by-one in loops, slices, pagination, ranges (inclusive vs exclusive).
- Null/None/undefined handling; optional fields that are missing vs present-but-empty.
- Equality and comparison: floats, money (use decimal types), case sensitivity, locale.
- State: is anything mutated that callers assume is immutable? Shared defaults (`def f(x=[])`)?

## Error handling
- Are errors caught at the right level, or swallowed (`except: pass`, empty `catch`)?
- Do error messages include enough context to debug, without leaking secrets or PII?
- Are retries bounded, with backoff, and only on retry-safe (idempotent) operations?
- Resource cleanup on failure: files, connections, locks, temp dirs (`with`, `defer`, `finally`).

## Concurrency and async
- Shared mutable state without locks; check-then-act races (exists → create).
- Missing `await`, unawaited promises, blocking calls inside async code.
- Ordering assumptions between messages, events, or goroutines.

## Data, schemas, migrations
- Migration is reversible or has a rollback plan; safe on a large table (no long locks, batched backfill).
- Old code and new code can run at the same time during deploy (expand → migrate → contract).
- Serialization changes stay backward compatible with stored data and other services.

## API and compatibility
- Public functions, endpoints, CLI flags, config keys, event schemas: renamed or removed? Is it versioned or announced?
- Default values changed silently?

## Security basics (deeper audit: `secure-code-review`)
- New input reaching queries, shell, file paths, templates, redirects, or deserializers.
- Authorization checked on every new endpoint or action, not just authentication.
- Secrets in code, logs, or error messages.

## Performance
- N+1 queries, queries inside loops, missing indexes for new filters.
- Unbounded reads into memory (whole file, whole table), missing pagination or limits.
- Work moved onto a hot path (per request, per item) that used to run once.

## Tests
- Is the risky logic tested, including the failure path? Would the tests fail if the fix were reverted?
- Tests assert behavior, not implementation details; no sleeps for synchronization; no network in unit tests.
- Deleted or skipped tests have a stated reason.

## Readability and design
- Names say what things are; functions do one thing; no dead code or commented-out blocks.
- Duplicated logic that should use an existing helper (search the repo before suggesting a new one).
- Comments explain *why*, not *what*.
