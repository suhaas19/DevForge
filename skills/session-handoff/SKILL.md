---
name: session-handoff
description: Writes a compact, factual handoff note (HANDOFF.md) that lets a fresh agent session, a teammate, or the user resume in-progress work without re-deriving context, covering goal, current state, decisions and why, dead ends, and exact next steps. Use when the user says to wrap up, pause, hand off, save progress, continue tomorrow or in a new chat, when the context window is getting long or about to be compacted, or before delegating work to another agent.
license: MIT
metadata:
  version: "1.0.0"
---

# Session Handoff

Long sessions degrade: Chroma's "Context Rot" study (2025) found that all 18
models tested got less reliable as input length grew, even on simple tasks. Starting
fresh with a short, accurate brief often beats pushing on with a bloated
context, but only if the brief keeps what matters. The two most expensive things
to lose are the **decisions with their reasons** and the **dead ends** (so nobody
re-tries them). This skill captures exactly those, plus verifiable state.

## When to use

- The user is stopping for now, switching machines, or starting a new chat.
- Context is long, the conversation is about to be compacted, or you notice you are re-reading the same files.
- Delegating a sub-task to another agent or a person.
- **Not for:** final project documentation or PR descriptions (use `writing-commits-and-prs`).

## Workflow

- [ ] 1. **Collect mechanical state:** `python3 scripts/handoff_context.py` prints branch, commits on the branch, uncommitted files, stashes, TODOs added, and recently changed files as Markdown. Paste it into the "State" section.
- [ ] 2. **Record verification state:** which test/build commands you ran last and their result (pass/fail counts, the failing test names). Re-run the quick ones now if the last run is stale; a handoff that says "tests pass" must be true.
- [ ] 3. **Write the narrative sections** from the session: goal, decisions (with *why* and alternatives rejected), dead ends (what was tried, why it failed, evidence), open questions for the user, and next steps as concrete, ordered actions with file paths and commands.
- [ ] 4. **Compress.** Target under ~150 lines. Link to files and commits instead of pasting code; one line per decision. Drop exploration that led nowhere unless it is a dead end worth recording.
- [ ] 5. **Save** as `HANDOFF.md` in the repo root (or the path the user prefers). Ask before committing it; many teams do not want it in history. Suggest adding it to `.git/info/exclude` if it should stay local.
- [ ] 6. **Validate with a cold read:** reread the note as if you knew nothing else. Could you run the next step without asking anything? Fix whatever is ambiguous. Then tell the user the opening line for the next session: *"Read HANDOFF.md and continue from Next steps."*

## Template

Use [assets/HANDOFF_TEMPLATE.md](assets/HANDOFF_TEMPLATE.md). Its sections, in order:

1. **Goal**: one or two sentences, plus the definition of done.
2. **Status**: done / in progress / not started, as a checklist.
3. **State of the code**: generated block from step 1, plus the last test results.
4. **Decisions**: `decision: why (rejected: alternative, because ...)`.
5. **Dead ends**: what was tried, what happened, evidence.
6. **Next steps**: ordered, concrete, each with the file or command.
7. **Open questions**: things only the user can answer.
8. **Gotchas for the next session**: environment quirks, flaky tests, slow commands, credentials needed.

## Example (excerpt)

```markdown
## Decisions
- Store sessions in Redis, not Postgres: logout must invalidate across 6 app servers within 1 s (rejected: JWT revocation list, adds a DB read per request).
## Dead ends
- Upgrading `redis-py` to 5.x to fix the timeout: same `ConnectionError` (log in `notes/redis-timeout.txt`); cause is the 1 s socket timeout in `config/redis.py:12`, not the client.
## Next steps
1. Raise `socket_timeout` to 5 s in `config/redis.py:12`; run `pytest tests/session -q` (currently 2 failing: `test_logout_all`, `test_expiry`).
```

## Gotchas

- **Never put secrets in the handoff** (tokens, passwords, connection strings). Say where they live instead ("API key in 1Password: Payments/Staging").
- **State, not story.** Chronological narration ("first I tried...") wastes the next reader's context; keep only decisions and dead ends.
- **Stale claims are worse than none.** Mark anything you did not re-verify as "(unverified)".
- **Uncommitted work is fragile.** Mention it prominently, and suggest a WIP commit or stash if the user is switching machines.
- **The next agent will trust this note.** If you are unsure about something, write it under open questions, not as fact.
