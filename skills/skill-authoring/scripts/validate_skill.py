#!/usr/bin/env python3
"""Validate Agent Skills against the agentskills.io spec and lint for known "skill smells".

Usage:
    validate_skill.py <skill-dir-or-skills-root> [...] [--strict] [--json] [--no-smells]

A path that contains SKILL.md is treated as one skill; otherwise every child
directory that contains SKILL.md is validated.

Exit codes: 0 = no errors (and no warnings with --strict), 1 = problems found,
2 = bad usage.

Checks
------
Spec errors (agentskills.io specification):
  * SKILL.md exists and starts with a ---delimited YAML frontmatter block
  * name: 1-64 chars, [a-z0-9-], no leading/trailing/double hyphen, equals dir name
  * description: 1-1024 chars;  compatibility: <=500 chars;  metadata: str->str map
  * relative files referenced from the body exist

Security errors (from empirical studies of malicious / vulnerable skills):
  * hidden Unicode (zero-width, bidi overrides) anywhere in the skill
  * XML/HTML-like tags in the description (instruction-injection vector)
  * remote-code patterns such as `curl ... | sh` or base64-decoded shell  # skill-lint: allow
    (a line containing the marker `skill-lint: allow` is exempt, for docs/detectors)

Smell warnings (Hong et al. 2026, "From Anatomy to Smells"):
  CSD confusing description, NTPD non-third-person description, LSB lengthy body,
  BG buried gotchas, NVS no validation step, ME missing example, NPT no progress
  tracking, NAH never asks human, TSS time-sensitive wording, BP backslash paths,
  plus script hygiene (shebang, executable bit, referenced from SKILL.md).

Only the Python standard library is required. PyYAML is used when available.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KNOWN_KEYS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
    # widely supported harness extensions (Claude Code, Antigravity, Codex ...)
    "disable-model-invocation", "user-invocable", "argument-hint", "model", "context",
    "agent", "hooks", "version",
}
ALLOW_MARKER = "skill-lint: allow"
HIDDEN_UNICODE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff\u202a-\u202e\u2066-\u2069]")
TAG_RE = re.compile(r"<\s*/?\s*[A-Za-z][A-Za-z0-9_-]*(\s[^<>]*)?>")
REMOTE_EXEC = [
    (re.compile(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b"), "pipes a download straight into a shell"),
    (re.compile(r"base64\s+(-d|--decode)[^\n]*\|\s*(ba|z)?sh"), "decodes base64 into a shell"),
    (re.compile(r"(~|\$HOME)/\.(ssh|aws|gnupg)/"), "touches credential directories"),
    (re.compile(r"\benv\b[^\n]*\|\s*(curl|nc|wget)\b"), "sends environment variables over the network"),
]
TRIGGER_HINTS = re.compile(r"\b(use (this )?(skill )?(when|whenever|for|if|before|after)|when (the user|you|asked|working)|trigger|invoke)\b", re.I)
FIRST_PERSON = re.compile(r"^\s*(i|we|you)\b|\b(i can|i will|i'll|let me)\b", re.I)
TIME_SENSITIVE = re.compile(r"\b(as of (19|20)\d\d|latest version|currently (the )?(best|newest|latest)|this year)\b", re.I)
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
BARE_PATH_RE = re.compile(r"(?<![\w/.-])((?:scripts|references|assets|examples|resources)/[\w./-]+\.\w+)")


@dataclass
class Report:
    skill: str
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def err(self, code, msg):
        self.errors.append({"code": code, "message": msg})

    def warn(self, code, msg):
        self.warnings.append({"code": code, "message": msg})


# ---------------------------------------------------------------- YAML parsing
def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    return v


def mini_yaml(text: str) -> dict:
    """Parse the flat/one-level-nested YAML subset used in SKILL.md frontmatter."""
    data: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0] in " \t":
            raise ValueError(f"unexpected indentation on line {i + 1}: {line!r}")
        if ":" not in line:
            raise ValueError(f"expected 'key: value' on line {i + 1}: {line!r}")
        key, _, rest = line.partition(":")
        key, rest = key.strip(), rest.strip()
        i += 1
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                block.append(lines[i].strip())
                i += 1
            joiner = "\n" if rest.startswith("|") else " "
            data[key] = joiner.join(b for b in block).strip()
        elif rest == "":
            mapping, items = {}, []
            while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                sub = lines[i].strip()
                i += 1
                if not sub:
                    continue
                if sub.startswith("- "):
                    items.append(_unquote(sub[2:]))
                else:
                    k, _, v = sub.partition(":")
                    mapping[k.strip()] = _unquote(v)
            data[key] = items if items else mapping
        elif rest.startswith("[") and rest.endswith("]"):
            data[key] = [_unquote(x) for x in rest[1:-1].split(",") if x.strip()]
        else:
            if rest[0] not in "'\"" and (": " in rest or rest.endswith(":") or rest[0] in "[{&*!|>%@`"):
                raise ValueError(f"line {i}: unquoted value for {key!r} contains ': ' or starts with a YAML "
                                 "indicator; wrap the value in quotes or use a '>' block")
            if rest[0] not in "'\"" and " #" in rest:
                rest = rest.split(" #", 1)[0]
            data[key] = _unquote(rest)
    return data


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with a '---' frontmatter delimiter")
    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("frontmatter is not closed with a '---' line") from None
    raw = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(raw) or {}
    except ImportError:
        data = mini_yaml(raw)
    except Exception as exc:  # yaml.YAMLError
        raise ValueError(f"invalid YAML frontmatter: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data, body


# ---------------------------------------------------------------- checks
def check_frontmatter(rep: Report, fm: dict, dirname: str) -> None:
    name = fm.get("name")
    if not isinstance(name, str) or not name:
        rep.err("SPEC", "frontmatter 'name' is required")
    else:
        if len(name) > 64:
            rep.err("SPEC", f"name is {len(name)} chars (max 64)")
        if not NAME_RE.match(name):
            rep.err("SPEC", f"name {name!r} must be lowercase a-z, 0-9 and single hyphens, not starting/ending with '-'")
        if name != dirname:
            rep.err("SPEC", f"name {name!r} must match its directory name {dirname!r}")
        if re.search(r"(^|-)(claude|anthropic)(-|$)", name):
            rep.warn("NAME", f"name {name!r} contains a reserved vendor word; some harnesses reject it")

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.err("SPEC", "frontmatter 'description' is required and must be non-empty")
    else:
        if len(desc) > 1024:
            rep.err("SPEC", f"description is {len(desc)} chars (max 1024)")
        if TAG_RE.search(desc):
            rep.err("SEC", "description contains XML/HTML-like tags, which can inject instructions into the system prompt")
        if not TRIGGER_HINTS.search(desc):
            rep.warn("CSD", "description should say WHEN to use the skill (e.g. 'Use when ...')")
        if len(desc) < 80:
            rep.warn("CSD", f"description is only {len(desc)} chars; include what it does, when to use it, and keywords")
        if FIRST_PERSON.search(desc):
            rep.warn("NTPD", "write the description in third person ('Reviews diffs...'), not 'I'/'you'/'we'")

    comp = fm.get("compatibility")
    if comp is not None and (not isinstance(comp, str) or not 1 <= len(comp) <= 500):
        rep.err("SPEC", "compatibility must be a 1-500 character string")

    meta = fm.get("metadata")
    if meta is not None:
        if not isinstance(meta, dict):
            rep.err("SPEC", "metadata must be a mapping of string keys to string values")
        else:
            for k, v in meta.items():
                if not isinstance(v, str):
                    rep.err("SPEC", f"metadata.{k} must be a string (quote numbers such as version: \"1.0\")")

    tools = fm.get("allowed-tools")
    if tools is not None and not isinstance(tools, (str, list)):
        rep.err("SPEC", "allowed-tools must be a space-separated string")

    for key in fm:
        if key not in KNOWN_KEYS:
            rep.warn("KEY", f"unknown frontmatter key {key!r} (ignored or rejected by some harnesses)")


def check_body(rep: Report, body: str, skill_dir: Path) -> None:
    lines = body.splitlines()
    words = len(body.split())
    if len(lines) > 500:
        rep.warn("LSB", f"SKILL.md body is {len(lines)} lines; keep under 500 and move detail to references/")
    if words > 5000:
        rep.warn("LSB", f"SKILL.md body is {words} words; agents load all of it on activation")

    # referenced files must exist
    refs = set(m.group(1) for m in LINK_RE.finditer(body))
    refs |= set(m.group(1) for m in BARE_PATH_RE.finditer(body))
    for ref in sorted(refs):
        if re.match(r"^[a-z]+://", ref) or ref.startswith("mailto:"):
            continue
        if "\\" in ref:
            rep.warn("BP", f"use forward slashes in paths: {ref}")
            continue
        if ref.startswith("/") or ref.startswith("~"):
            continue
        target = (skill_dir / ref).resolve()
        if skill_dir.resolve() not in target.parents and target != skill_dir.resolve():
            rep.err("REF", f"reference escapes the skill directory: {ref}")
        elif not target.exists():
            rep.err("REF", f"referenced file does not exist: {ref}")

    if re.search(r"[A-Za-z]:\\|\w\\\w+\\", body):
        rep.warn("BP", "body contains backslash paths; use forward slashes")

    lower = body.lower()
    if not re.search(r"^#+\s*.*(gotcha|pitfall|caveat|common mistakes|watch out)", body, re.I | re.M):
        rep.warn("BG", "add a '## Gotchas' section so critical caveats are not buried")
    if not re.search(r"\b(verify|validate|validation|check that|confirm that|re-run|rerun)\b", lower):
        rep.warn("NVS", "no validation step found; tell the agent how to check its own output")
    if "```" not in body and "example" not in lower:
        rep.warn("ME", "no example found; include at least one worked example")
    numbered = len(re.findall(r"^\s*\d+\.\s", body, re.M))
    if numbered >= 5 and "- [ ]" not in body and "checklist" not in lower:
        rep.warn("NPT", "multi-step workflow without a checklist; add '- [ ]' items so progress can be tracked")
    if not re.search(r"\b(ask the user|ask the human|confirm with the user|check with the user|ask before)\b", lower):
        rep.warn("NAH", "no point where the agent asks the human; say when to stop and ask")
    if TIME_SENSITIVE.search(body):
        rep.warn("TSS", "time-sensitive wording found; it will go stale")


def check_files(rep: Report, skill_dir: Path, body: str) -> None:
    for path in skill_dir.rglob("*"):
        if path.is_dir() or any(p in {".git", "__pycache__", "node_modules"} for p in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(skill_dir).as_posix()
        if HIDDEN_UNICODE.search(text):
            rep.err("SEC", f"{rel} contains hidden Unicode (zero-width or bidi control characters)")
        if "/evals/" in f"/{rel}" or rel.startswith("tests/"):
            continue
        # Lines that document or detect these patterns opt out with a marker comment.
        scannable = "\n".join(ln for ln in text.splitlines() if ALLOW_MARKER not in ln)
        for pattern, why in REMOTE_EXEC:
            if pattern.search(scannable):
                rep.err("SEC", f"{rel} {why}")

    scripts = skill_dir / "scripts"
    if scripts.is_dir():
        for script in sorted(scripts.iterdir()):
            if script.is_dir() or script.name.startswith((".", "_")) or script.suffix in {".pyc", ".md", ".txt", ".json"}:
                continue
            rel = script.relative_to(skill_dir).as_posix()
            if rel not in body and script.name not in body:
                rep.warn("MUS", f"{rel} is never mentioned in SKILL.md, so the agent will not know to use it")
            head = script.read_text(encoding="utf-8", errors="ignore")[:200]
            if not head.startswith("#!"):
                rep.warn("SCRIPT", f"{rel} has no shebang line")
            if os.name != "nt" and not script.stat().st_mode & stat.S_IXUSR:
                rep.warn("SCRIPT", f"{rel} is not executable (chmod +x)")


def validate(skill_dir: Path, smells: bool = True) -> Report:
    rep = Report(skill=skill_dir.name)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        rep.err("SPEC", "SKILL.md not found")
        return rep
    text = skill_md.read_text(encoding="utf-8")
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as exc:
        rep.err("SPEC", str(exc))
        return rep
    check_frontmatter(rep, fm, skill_dir.name)
    check_body(rep, body, skill_dir)
    check_files(rep, skill_dir, body)
    if not smells:
        rep.warnings = [w for w in rep.warnings if w["code"] in {"KEY", "NAME", "REF"}]
    return rep


def discover(paths) -> list:
    found = []
    for p in paths:
        p = Path(p)
        if (p / "SKILL.md").is_file():
            found.append(p)
        elif p.is_dir():
            found.extend(sorted(c for c in p.iterdir() if c.is_dir() and (c / "SKILL.md").is_file()))
        else:
            print(f"warning: {p} is not a skill or a directory of skills", file=sys.stderr)
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", help="skill directory or directory containing skills")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--no-smells", action="store_true", help="only spec and security checks")
    args = ap.parse_args(argv)

    skills = discover(args.paths)
    if not skills:
        print("no skills found", file=sys.stderr)
        return 2
    reports = [validate(s, smells=not args.no_smells) for s in skills]

    if args.json:
        print(json.dumps([r.__dict__ for r in reports], indent=2))
    else:
        for r in reports:
            status = "FAIL" if r.errors else ("WARN" if r.warnings else "OK")
            print(f"[{status}] {r.skill}")
            for e in r.errors:
                print(f"    error   {e['code']:<6} {e['message']}")
            for w in r.warnings:
                print(f"    warning {w['code']:<6} {w['message']}")
        n_err = sum(len(r.errors) for r in reports)
        n_warn = sum(len(r.warnings) for r in reports)
        print(f"\n{len(reports)} skill(s), {n_err} error(s), {n_warn} warning(s)")

    failed = any(r.errors for r in reports) or (args.strict and any(r.warnings for r in reports))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
