---
name: secure-code-review
description: Performs a defensive security review of source code or a diff, finding injection, broken access control, secrets, unsafe deserialization, SSRF, XSS and crypto misuse, and reports only findings backed by a traced source-to-sink data flow. Use when the user asks for a security review, security audit, vulnerability check, "is this code safe", OWASP or CWE review, threat check before release, or when a change touches authentication, authorization, file handling, user input, payments, or secrets.
license: MIT
compatibility: Works offline. Bundled scanners need Python 3.9+ and git.
metadata:
  version: "1.0.0"
---

# Secure Code Review

LLMs flag plenty of code as vulnerable that is not. Ullah et al. (IEEE S&P 2024)
found every model they tested had a high false-positive rate and called patched
code vulnerable. A finding without a traced data flow erodes trust in every
other finding. This skill uses deterministic scanners to produce candidates, then
requires a concrete source → sink trace before anything is reported.

This is for defending code the user owns or is authorized to review. Do not write
working exploits; a minimal proof (an input value, a failing test) is enough.

## When to use

- "Security review", "audit this", "is this safe", "check for vulnerabilities", OWASP/CWE questions.
- Any change touching authn/authz, sessions, file paths, uploads, shell, SQL, templates, deserialization, outbound HTTP, crypto, payments, or secrets.
- **Not for:** dependency CVEs (use `dependency-audit`), LLM/agent prompt-injection design (use `prompt-injection-defense`).

## Workflow

- [ ] 1. **Scope.** Decide what is in scope: a diff (`git diff <base>...HEAD --name-only`) or the whole repo. Identify the trust boundaries: where untrusted data enters (HTTP params, headers, files, queues, env from users, LLM output) and what is valuable (data stores, credentials, admin actions).
- [ ] 2. **Run the scanners** (fast, deterministic, no network):
  - `python3 scripts/secret_scan.py <path>`: hard-coded keys, tokens and private keys, redacted in output.
  - `python3 scripts/find_sinks.py <path>`: candidate dangerous sinks by category (command, code, SQL, deserialization, path traversal, SSRF, XSS, XXE, weak crypto, TLS off, open redirect).
  - If installed, also run the project's real tools (semgrep, bandit, gosec, brakeman, CodeQL) and fold their output into the candidates.
- [ ] 3. **Trace each candidate.** For every sink, walk backwards to its sources. A candidate becomes a finding only if you can write: *source* (file:line) → *transformations* → *sink* (file:line), with no effective sanitization or authorization check on the path. Record dismissed candidates and why (e.g. "constant argument", "parameterized query").
- [ ] 4. **Review what scanners cannot see.** Use [references/checklist.md](references/checklist.md) for logic flaws: missing authorization on new endpoints, IDOR (object IDs not scoped to the caller), mass assignment, race conditions in balance/coupon logic, insecure defaults, verbose errors, missing rate limits on auth.
- [ ] 5. **Rate severity** with the matrix below. Assume the attacker is the least-privileged user who can reach the source.
- [ ] 6. **Validate before reporting.** Re-read each finding and confirm: the trace is real, the line numbers are correct, the fix closes the path. Where a test framework exists, offer a failing test that demonstrates the issue safely.
- [ ] 7. **Report** using the template. Ask the user before making fixes in bulk; small, obvious fixes (parameterizing one query) can go in the same pass if the user asked for fixes.

### Severity matrix

| Impact ↓ / Reachability → | Unauthenticated | Any logged-in user | Admin / internal only |
|---|---|---|---|
| RCE, auth bypass, full data read/write | Critical | Critical | High |
| Read or modify other users' data | High | High | Medium |
| Limited info leak, DoS, CSRF on low-value action | Medium | Low | Low |
| Hardening gap, no direct exploit | Informational | Informational | Informational |

## Output template

```markdown
## Security review: <scope>
**Summary:** N findings (Critical a, High b, Medium c, Low d). Scanners run: ... Candidates dismissed: M.

### [HIGH] SQL injection in order search (CWE-89)
- **Where:** `api/orders.py:57`
- **Flow:** `request.args["q"]` (`api/orders.py:51`) → `build_filter()` (`db/filters.py:12`, string concatenation) → `cursor.execute()` (`api/orders.py:57`)
- **Impact:** any logged-in user can read every customer's orders.
- **Proof (safe):** `q=' OR '1'='1` returns all rows in the test DB.
- **Fix:** use a parameterized query: `cursor.execute("... WHERE name = %s", (q,))`.

### Secrets
- `config/prod.py:3` AWS access key (redacted). **Rotate the key**; deleting it from git does not revoke it.

### Dismissed candidates (for transparency)
- `utils/run.py:20` `subprocess.run(..., shell=True)`: argument is a constant.
```

## Gotchas

- **No trace, no finding.** "This could be vulnerable if..." goes under questions, not findings.
- **Sanitizers must match the sink.** HTML-escaping does not stop SQL injection; a regex allowlist on a path does not stop `..` if it runs before URL decoding.
- **Authorization is per object.** Checking that a user is logged in is not checking that they own `order_id=123`.
- **Secrets in history.** A secret removed in the latest commit still sits in git history and in every clone. The only fix is rotation.
- **Test fixtures and examples** often contain fake keys. `secret_scan.py` skips generic matches in test paths unless `--include-tests` is set; known-format keys are still reported because real keys end up in tests too.
- **Do not paste secret values** into the report, tickets or chat. The scanners redact them; keep it that way.
