#!/usr/bin/env python3
"""Generate every harness manifest from plugin-meta.json so names, versions and URLs never drift.

Usage:
    python3 scripts/sync_manifests.py                    # rewrite manifests from plugin-meta.json
    python3 scripts/sync_manifests.py --owner octocat    # set your GitHub user/org everywhere, then sync
    python3 scripts/sync_manifests.py --version 1.2.0    # bump the version everywhere, then sync
    python3 scripts/sync_manifests.py --check            # CI: fail if any manifest is out of date

Writes:
    .claude-plugin/plugin.json, .claude-plugin/marketplace.json     (Claude Code, Copilot CLI)
    .antigravity-plugin/plugin.json                                  (Antigravity: agy / IDE)
    .cursor-plugin/plugin.json                                       (Cursor)
    .codex-plugin/plugin.json, .agents/plugins/marketplace.json      (Codex)
    gemini-extension.json                                            (Gemini CLI)
and replaces the owner placeholder in README.md, docs/ and install.sh.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "plugin-meta.json"
PLACEHOLDER = "YOUR_GITHUB_USERNAME"
TEXT_FILES = ["README.md", "install.sh", "docs/INSTALL.md", "docs/AUTHORING.md", "CONTRIBUTING.md", "SECURITY.md"]


def build(meta: dict) -> dict:
    owner, name = meta["owner"], meta["name"]
    repo = f"https://github.com/{owner}/{name}"
    author = {"name": meta["author"]["name"]}
    if meta["author"].get("email"):
        author["email"] = meta["author"]["email"]
    author_url = dict(author, url=f"https://github.com/{owner}")
    common = {"name": name, "version": meta["version"], "description": meta["description"], "author": author,
              "homepage": repo, "repository": repo, "license": meta["license"], "keywords": meta["keywords"]}
    return {
        ".claude-plugin/plugin.json": dict(common),
        ".claude-plugin/marketplace.json": {
            "name": name, "description": meta["marketplace_description"], "owner": author,
            "plugins": [{"name": name, "displayName": meta["display_name"], "description": meta["description"],
                         "source": "./", "author": author, "category": "development", "tags": meta["keywords"]}],
        },
        ".antigravity-plugin/plugin.json": {
            "$schema": "https://antigravity.google/schemas/v1/plugin.json", "name": name,
            "displayName": meta["display_name"], "version": meta["version"], "description": meta["short_description"],
            "logo": meta["logo"], "suggestedPrompts": meta["suggested_prompts"][:3], "author": author_url,
            "homepage": repo, "repository": repo, "license": meta["license"], "keywords": meta["keywords"],
        },
        ".cursor-plugin/plugin.json": dict(common, displayName=meta["display_name"], skills="./skills/"),
        ".codex-plugin/plugin.json": dict(common, author=author_url, skills="./skills/", interface={
            "displayName": meta["display_name"], "shortDescription": meta["short_description"],
            "longDescription": meta["description"], "developerName": meta["author"]["name"],
            "category": "Developer Tools", "capabilities": ["Interactive", "Read", "Write"],
            "defaultPrompt": meta["suggested_prompts"][:2], "websiteURL": repo,
        }),
        ".agents/plugins/marketplace.json": {
            "name": name, "interface": {"displayName": meta["display_name"]},
            "plugins": [{"name": name, "source": {"source": "local", "path": "./"},
                         "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                         "category": "Developer Tools"}],
        },
        "gemini-extension.json": {"name": name, "version": meta["version"], "description": meta["short_description"],
                                  "contextFileName": "GEMINI.md"},
    }


def dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--owner", help="GitHub user or org that hosts the repo")
    ap.add_argument("--version", help="new semantic version, e.g. 1.2.0")
    ap.add_argument("--check", action="store_true", help="exit 1 if manifests are stale (for CI)")
    args = ap.parse_args(argv)

    meta = json.loads(META.read_text(encoding="utf-8"))
    old_owner = meta["owner"]
    if args.owner:
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", args.owner):
            print(f"error: {args.owner!r} is not a valid GitHub user/org name", file=sys.stderr)
            return 2
        meta["owner"] = args.owner
    if args.version:
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.]+)?", args.version):
            print("error: version must look like 1.2.3", file=sys.stderr)
            return 2
        meta["version"] = args.version

    outputs = build(meta)
    stale = []
    for rel, obj in outputs.items():
        path = ROOT / rel
        text = dump(obj)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(rel)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            print("stale manifests (run scripts/sync_manifests.py): " + ", ".join(stale))
            return 1
        print("manifests in sync")
        return 0

    if args.owner or args.version:
        META.write_text(dump(meta), encoding="utf-8")
    if args.owner:
        for rel in TEXT_FILES:
            path = ROOT / rel
            if path.exists():
                text = path.read_text(encoding="utf-8")
                new = text.replace(PLACEHOLDER, meta["owner"])
                if old_owner != PLACEHOLDER:
                    new = new.replace(f"{old_owner}/{meta['name']}", f"{meta['owner']}/{meta['name']}")
                if new != text:
                    path.write_text(new, encoding="utf-8")
                    print(f"updated owner in {rel}")
    for rel in stale:
        print(f"wrote {rel}")
    print(f"{meta['name']} {meta['version']} (owner: {meta['owner']}): {len(outputs)} manifests in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
