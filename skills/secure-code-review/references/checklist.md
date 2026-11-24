# Security review checklist

Organized by OWASP Top 10 (2021) categories with the most relevant CWE IDs. Use it to
find logic flaws the scanners cannot see. Each item is a question to answer with code
references.

## A01 Broken access control (CWE-284, 285, 639, 862, 863)
- Every new route, RPC, GraphQL resolver, or background job that acts for a user: where is authorization enforced? Is it enforced server-side?
- Object references (IDs in URLs, bodies, filenames): is the object scoped to the caller's tenant/user (IDOR)?
- Role checks: default-deny? Can a user change their own role via a profile update (mass assignment, CWE-915)?
- CORS: is `Access-Control-Allow-Origin` reflected from the request together with credentials?
- Path traversal (CWE-22): user input joined into paths. Is the resolved path checked to be inside the intended directory *after* normalization?

## A02 Cryptographic failures (CWE-327, 328, 330, 916)
- Passwords hashed with bcrypt/scrypt/argon2 (not MD5/SHA-x, not unsalted).
- Tokens, reset codes, session IDs from a CSPRNG (`secrets`, `crypto.randomBytes`, `crypto/rand`).
- No ECB mode, no static IVs/nonces, no home-grown crypto; TLS verification on.
- Sensitive data encrypted at rest where required; keys not stored next to the data.

## A03 Injection (CWE-78, 79, 89, 94, 917, 943)
- SQL/NoSQL: parameterized queries or a safe query builder; no string formatting into queries, including `ORDER BY` and table names (allowlist those).
- OS commands: argument arrays, not shell strings; no user input in `shell=True`.
- Templates: autoescaping on; any `|safe`, `mark_safe`, `dangerouslySetInnerHTML`, `v-html` justified.
- LDAP, XPath, expression languages, regex built from input (ReDoS, CWE-1333).

## A04 Insecure design
- Business logic: can steps be skipped or replayed (checkout without payment, coupon reuse)?
- Race conditions on balances, inventory, single-use tokens (use transactions/row locks/idempotency keys).
- Rate limiting on login, password reset, OTP, and expensive endpoints.

## A05 Security misconfiguration (CWE-16, 209, 611)
- Debug mode, stack traces, or verbose errors in production responses.
- Default credentials, sample apps, open admin consoles.
- XML parsers with external entities enabled (XXE).
- Security headers for web apps: CSP, HSTS, X-Content-Type-Options, frame-ancestors.

## A06 Vulnerable components
- Delegate to `dependency-audit`. Note any newly added dependency in the diff.

## A07 Identification and authentication failures (CWE-287, 384, 613)
- Session fixation (session ID rotated on login), session expiry, logout invalidates server-side.
- JWT: algorithm pinned (no `alg: none`, no HS/RS confusion), `exp` checked, signature verified before use.
- Password reset tokens single-use and short-lived; no user enumeration via different error messages.

## A08 Software and data integrity failures (CWE-502, 494, 829)
- Deserializing untrusted data: pickle, `yaml.load`, Java `ObjectInputStream`, PHP `unserialize`, .NET `BinaryFormatter`, `torch.load` without `weights_only=True`.
- CI/CD: workflows triggered by forks with secrets (`pull_request_target`), unpinned third-party actions, `curl | sh` installers.  <!-- skill-lint: allow -->
- Auto-update or plugin loading without signature verification.

## A09 Logging and monitoring failures (CWE-117, 532, 778)
- Secrets, tokens, passwords, or full PII written to logs.
- Log injection (newlines from user input in log lines).
- Security-relevant events (login failures, permission denials) logged at all?

## A10 Server-side request forgery (CWE-918)
- Any outbound request whose URL, host, or redirect target comes from input.
- Mitigation: allowlist hosts; resolve DNS and block private/link-local/metadata ranges (169.254.169.254, fd00::/8, 127.0.0.0/8, 10/8, 172.16/12, 192.168/16) *after* resolution; disable redirects or re-check each hop.

## File uploads
- Type checked by content, not extension; size limits; stored outside the web root with random names; served with `Content-Disposition: attachment` when not meant to render.
- Archive extraction checks each member path (zip slip).
