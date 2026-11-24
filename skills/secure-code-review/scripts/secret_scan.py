#!/usr/bin/env python3
"""Scan files for hard-coded secrets (keys, tokens, private keys, credentialed URLs).

Usage:
    secret_scan.py [PATH ...] [--json] [--min-entropy 3.5] [--include-tests]

Defaults to the current directory. Respects .gitignore when run inside a git
repository. Matches are REDACTED in the output so the report itself is safe to
paste into a ticket. Exit code 1 when findings exist, 0 otherwise.

Suppress a reviewed false positive by adding `secret-scan: ignore` on that line.
This is a fast first pass, not a replacement for gitleaks/trufflehog in CI.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

# (rule id, description, regex) -- secret-scan: ignore
RULES = [
    ("aws-access-key", "AWS access key ID", r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("aws-secret-key", "AWS secret access key", r"(?i)aws.{0,20}(secret|private).{0,20}['\"][0-9a-zA-Z/+]{40}['\"]"),
    ("github-token", "GitHub token", r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{60,}\b"),
    ("gitlab-token", "GitLab token", r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    ("slack-token", "Slack token", r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b"),
    ("slack-webhook", "Slack webhook", r"https://hooks\.slack\.com/services/[A-Za-z0-9/]{20,}"),
    ("google-api-key", "Google API key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("stripe-key", "Stripe live key", r"\b(sk|rk)_live_[0-9a-zA-Z]{20,}\b"),
    ("openai-key", "OpenAI API key", r"\bsk-(proj-)?[A-Za-z0-9_-]{32,}\b"),
    ("anthropic-key", "Anthropic API key", r"\bsk-ant-[A-Za-z0-9_-]{32,}\b"),
    ("huggingface-token", "Hugging Face token", r"\bhf_[A-Za-z0-9]{30,}\b"),
    ("twilio-key", "Twilio API key", r"\bSK[0-9a-fA-F]{32}\b"),
    ("sendgrid-key", "SendGrid key", r"\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}\b"),
    ("npm-token", "npm token", r"\bnpm_[A-Za-z0-9]{36}\b"),
    ("private-key", "Private key block", r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY( BLOCK)?-----"),
    ("jwt", "JSON Web Token", r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    ("url-credentials", "Credentials in URL", r"\b[a-z][a-z0-9+.-]*://[^/\s:@'\"]{1,64}:[^/\s:@'\"]{3,128}@[^\s'\"]+"),
    ("azure-conn-string", "Azure storage connection string", r"AccountKey=[A-Za-z0-9+/=]{40,}"),
]
GENERIC = re.compile(
    r"(?i)\b([a-z0-9_.-]*(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)[a-z0-9_.-]*)"
    r"\s*[:=]\s*['\"]([^'\"\s]{8,})['\"]"
)
PLACEHOLDER = re.compile(r"(?i)^(x+|\*+|<.*>|\$\{.*\}|\{\{.*\}\}|%\(.*\)s|changeme|change_me|example|sample|dummy|test|fake|"
                         r"placeholder|your[_-].*|redacted|todo|none|null|password|secret|xxx.*|\.\.\.)$")
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build", "target", "__pycache__", ".tox"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tgz", ".jar", ".woff",
            ".woff2", ".ttf", ".mp4", ".mp3", ".so", ".dylib", ".dll", ".exe", ".bin", ".pyc", ".lock", ".svg"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|testdata|mocks?)/|_test\.|\.test\.|\.spec\.")
IGNORE_MARK = "secret-scan: ignore"
COMPILED = [(rid, desc, re.compile(rx)) for rid, desc, rx in RULES]


def entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def redact(s: str) -> str:
    return s[:4] + "…" + f"({len(s)} chars)" if len(s) > 8 else "…"


def iter_files(paths):
    for root in paths:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, capture_output=True, text=True)
        if out.returncode == 0:
            for f in out.stdout.splitlines():
                p = root / f
                if p.is_file() and not any(part in SKIP_DIRS for part in Path(f).parts):
                    yield p
        else:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    yield Path(dirpath) / fn


def scan_text(text: str, min_entropy: float):
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if IGNORE_MARK in line or len(line) > 5000:
            continue
        hit_spans = []
        for rid, desc, rx in COMPILED:
            for m in rx.finditer(line):
                hit_spans.append(m.span())
                findings.append({"line": lineno, "rule": rid, "description": desc, "match": redact(m.group(0))})
        for m in GENERIC.finditer(line):
            value = m.group(3)
            if any(a <= m.start(3) < b for a, b in hit_spans):
                continue
            if PLACEHOLDER.match(value) or value.startswith(("$", "%", "{", "<", "os.", "process.env")):
                continue
            if entropy(value) < min_entropy:
                continue
            findings.append({"line": lineno, "rule": "generic-secret", "description": f"High-entropy value assigned to '{m.group(1)}'",
                             "match": redact(value), "entropy": round(entropy(value), 2)})
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-entropy", type=float, default=3.5)
    ap.add_argument("--include-tests", action="store_true", help="also report findings in test/fixture paths")
    args = ap.parse_args(argv)

    results = []
    for path in iter_files(args.paths):
        if path.suffix.lower() in SKIP_EXT:
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            raw = path.read_bytes()
        except OSError:
            continue
        if b"\0" in raw[:4096]:
            continue
        rel = path.as_posix()
        in_tests = bool(TEST_PATH.search(rel))
        for f in scan_text(raw.decode("utf-8", errors="ignore"), args.min_entropy):
            if in_tests and not args.include_tests and f["rule"] == "generic-secret":
                continue
            f["file"] = rel
            f["in_test_path"] = in_tests
            results.append(f)

    if args.json:
        print(json.dumps(results, indent=2))
    elif results:
        print(f"{len(results)} potential secret(s):\n")
        for f in results:
            tag = " [test path]" if f["in_test_path"] else ""
            print(f"  {f['file']}:{f['line']}  {f['rule']:<18} {f['match']}{tag}")
        print("\nTriage each: real secrets must be rotated (removing them from git history is not enough).")
    else:
        print("no secrets found")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
