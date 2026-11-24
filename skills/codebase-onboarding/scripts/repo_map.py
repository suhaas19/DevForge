#!/usr/bin/env python3
"""Map an unfamiliar repository: languages, layout, entry points, build/test commands, hotspots.

Usage:
    repo_map.py [ROOT] [--json] [--churn-commits N] [--top N]

Prints a Markdown report (or JSON with --json) that gives an agent a fast,
factual starting point before it reads code. Uses `git ls-files` when ROOT is a
git repository (so .gitignore is respected) and falls back to a filtered walk.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

LANGS = {
    ".py": "Python", ".pyi": "Python", ".ipynb": "Jupyter", ".js": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".fs": "F#", ".c": "C", ".h": "C/C++ header",
    ".cc": "C++", ".cpp": "C++", ".hpp": "C++", ".swift": "Swift", ".m": "Objective-C",
    ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".hs": "Haskell",
    ".lua": "Lua", ".r": "R", ".jl": "Julia", ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell",
    ".sql": "SQL", ".tf": "Terraform", ".vue": "Vue", ".svelte": "Svelte", ".html": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".proto": "Protobuf", ".graphql": "GraphQL", ".zig": "Zig",
}
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "target", ".venv", "venv", "__pycache__",
             ".next", ".nuxt", ".tox", ".mypy_cache", ".pytest_cache", "coverage", ".idea", ".vscode",
             ".gradle", "Pods", ".terraform", "site-packages", ".cache"}
MANIFESTS = {
    "package.json": "Node.js", "pnpm-lock.yaml": "pnpm", "yarn.lock": "Yarn", "package-lock.json": "npm",
    "bun.lockb": "Bun", "pyproject.toml": "Python (pyproject)", "requirements.txt": "pip",
    "setup.py": "setuptools", "Pipfile": "Pipenv", "poetry.lock": "Poetry", "uv.lock": "uv",
    "go.mod": "Go modules", "Cargo.toml": "Cargo", "pom.xml": "Maven", "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle (Kotlin)", "Gemfile": "Bundler", "composer.json": "Composer",
    "mix.exs": "Mix", "Makefile": "Make", "justfile": "just", "Taskfile.yml": "Task",
    "CMakeLists.txt": "CMake", "Dockerfile": "Docker", "docker-compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose", "flake.nix": "Nix", "deno.json": "Deno", "pubspec.yaml": "Dart/Flutter",
    "*.csproj": ".NET", "*.sln": ".NET",
}
ENTRY_PATTERNS = [
    r"(^|/)main\.(py|go|rs|c|cc|cpp|java|kt|swift|dart|ts|js)$", r"(^|/)__main__\.py$",
    r"(^|/)(app|server|index|cli|manage|wsgi|asgi)\.(py|js|ts|mjs)$", r"^cmd/[^/]+/main\.go$",
    r"(^|/)src/(main|lib|index)\.(rs|ts|js|tsx)$", r"(^|/)Program\.cs$", r"(^|/)bin/[^/]+$",
]
TEST_PATTERNS = [r"(^|/)(tests?|__tests__|spec|specs)/", r"(^|/)test_[^/]+\.py$", r"_test\.(py|go)$",
                 r"\.(test|spec)\.(js|ts|jsx|tsx|mjs)$", r"(^|/)src/test/", r"Tests?\.(cs|java|kt|swift)$"]
DOC_FILES = ["README.md", "README.rst", "README", "CONTRIBUTING.md", "ARCHITECTURE.md", "AGENTS.md",
             "CLAUDE.md", "GEMINI.md", "docs/", "CHANGELOG.md", "SECURITY.md", ".github/CODEOWNERS", "CODEOWNERS"]


def run(cmd, cwd):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def list_files(root: Path):
    out = run(["git", "ls-files", "-co", "--exclude-standard"], root)
    if out is not None:
        files = [f for f in out.splitlines() if f and not any(p in SKIP_DIRS for p in f.split("/"))]
        return files, True
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".") or d == ".github"]
        for fn in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/"))
    return files, False


def count_lines(path: Path) -> int:
    try:
        if path.stat().st_size > 2_000_000:
            return 0
        with open(path, "rb") as fh:
            chunk = fh.read()
        if b"\0" in chunk[:4096]:
            return 0
        return chunk.count(b"\n")
    except OSError:
        return 0


def detect_commands(root: Path, files: set) -> dict:
    cmds: dict = defaultdict(list)
    if "package.json" in files:
        try:
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            runner = "pnpm" if "pnpm-lock.yaml" in files else "yarn" if "yarn.lock" in files else \
                "bun" if "bun.lockb" in files else "npm"
            for name, script in (pkg.get("scripts") or {}).items():
                kind = "test" if "test" in name else "build" if "build" in name else \
                    "lint" if re.search(r"lint|format|typecheck|check", name) else \
                    "run" if re.search(r"start|dev|serve", name) else "other"
                cmds[kind].append(f"{runner} run {name}  # {script[:70]}")
        except (OSError, ValueError):
            pass
    if "pyproject.toml" in files:
        text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore")
        if "pytest" in text or any(f.startswith("tests/") for f in files):
            cmds["test"].append("pytest")
        if "ruff" in text:
            cmds["lint"].append("ruff check .")
        if "mypy" in text:
            cmds["lint"].append("mypy .")
        if "[project.scripts]" in text:
            cmds["run"].append("see [project.scripts] in pyproject.toml")
    elif any(f.endswith(".py") for f in files) and any(re.search(TEST_PATTERNS[1], f) for f in files):
        cmds["test"].append("pytest")
    if "go.mod" in files:
        cmds["test"].append("go test ./...")
        cmds["build"].append("go build ./...")
        cmds["lint"].append("go vet ./...")
    if "Cargo.toml" in files:
        cmds["test"].append("cargo test")
        cmds["build"].append("cargo build")
        cmds["lint"].append("cargo clippy")
    if "pom.xml" in files:
        cmds["test"].append("mvn test")
    if "build.gradle" in files or "build.gradle.kts" in files:
        cmds["test"].append("./gradlew test")
    if "Gemfile" in files:
        cmds["test"].append("bundle exec rspec  # or rake test")
    for mk in ("Makefile", "justfile"):
        if mk in files:
            text = (root / mk).read_text(encoding="utf-8", errors="ignore")
            targets = re.findall(r"^([A-Za-z0-9_.-]+):(?!=)", text, re.M)
            tool = "make" if mk == "Makefile" else "just"
            for t in [t for t in targets if not t.startswith(".")][:15]:
                cmds["make"].append(f"{tool} {t}")
    return dict(cmds)


def churn(root: Path, commits: int, top: int):
    out = run(["git", "log", f"-n{commits}", "--name-only", "--pretty=format:"], root)
    if not out:
        return []
    counter = Counter(line for line in out.splitlines() if line.strip())
    return [{"file": f, "commits": n} for f, n in counter.most_common(top)]


def build_report(root: Path, churn_commits: int, top: int) -> dict:
    files, is_git = list_files(root)
    fileset = set(files)
    lang_files, lang_lines = Counter(), Counter()
    sizes = []
    top_dirs = Counter()
    for f in files:
        ext = Path(f).suffix.lower()
        top_dirs[f.split("/")[0] + "/" if "/" in f else "(root files)"] += 1
        lang = LANGS.get(ext)
        if lang:
            n = count_lines(root / f)
            lang_files[lang] += 1
            lang_lines[lang] += n
            sizes.append((n, f))

    manifests = []
    for f in files:
        base = f.split("/")[-1]
        for pat, tool in MANIFESTS.items():
            if (pat.startswith("*") and base.endswith(pat[1:])) or base == pat:
                if f.count("/") <= 2:
                    manifests.append({"file": f, "tool": tool})
    entry = [f for f in files if any(re.search(p, f) for p in ENTRY_PATTERNS)][:top]
    tests = [f for f in files if any(re.search(p, f) for p in TEST_PATTERNS)]
    test_dirs = Counter(f.split("/")[0] for f in tests)
    ci = [f for f in files if f.startswith(".github/workflows/") or f in
          (".gitlab-ci.yml", "Jenkinsfile", ".circleci/config.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml")]
    docs = [d for d in DOC_FILES if (d.endswith("/") and any(f.startswith(d) for f in files)) or d in fileset]
    branch = (run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root) or "").strip() if is_git else None
    last = (run(["git", "log", "-1", "--format=%h %ad %s", "--date=short"], root) or "").strip() if is_git else None

    return {
        "root": str(root.resolve()),
        "git": {"is_repo": is_git, "branch": branch, "last_commit": last},
        "totals": {"files": len(files), "code_files": sum(lang_files.values()), "code_lines": sum(lang_lines.values())},
        "languages": [{"language": l, "files": lang_files[l], "lines": lang_lines[l]} for l, _ in lang_lines.most_common()],
        "top_level": [{"path": p, "files": n} for p, n in sorted(top_dirs.items(), key=lambda x: -x[1])[:25]],
        "manifests": manifests,
        "commands": detect_commands(root, fileset),
        "entry_points": entry,
        "tests": {"files": len(tests), "locations": dict(test_dirs.most_common(8))},
        "ci": ci,
        "docs": docs,
        "largest_files": [{"file": f, "lines": n} for n, f in sorted(sizes, reverse=True)[:top]],
        "hotspots": churn(root, churn_commits, top) if is_git else [],
    }


def to_markdown(r: dict) -> str:
    out = [f"# Repository map: `{Path(r['root']).name}`", ""]
    g = r["git"]
    if g["is_repo"]:
        out.append(f"- Branch: `{g['branch']}`; last commit: {g['last_commit']}")
    t = r["totals"]
    out.append(f"- {t['files']} tracked files, {t['code_files']} source files, ~{t['code_lines']:,} lines of code")
    out += ["", "## Languages", "", "| Language | Files | Lines |", "|---|---:|---:|"]
    out += [f"| {l['language']} | {l['files']} | {l['lines']:,} |" for l in r["languages"][:12]]
    out += ["", "## Top-level layout", ""]
    out += [f"- `{d['path']}` ({d['files']} files)" for d in r["top_level"]]
    out += ["", "## Build tooling", ""]
    out += [f"- `{m['file']}`: {m['tool']}" for m in r["manifests"]] or ["- none detected"]
    out += ["", "## Likely commands (verify before trusting)", ""]
    for kind, cmds in r["commands"].items():
        out += [f"- **{kind}**: " + "; ".join(f"`{c.split('  #')[0]}`" for c in cmds[:8])]
    if not r["commands"]:
        out.append("- none detected; read README/CONTRIBUTING")
    out += ["", "## Entry points", ""] + ([f"- `{e}`" for e in r["entry_points"]] or ["- none matched common patterns"])
    tl = r["tests"]
    out += ["", "## Tests", "", f"- {tl['files']} test files; locations: " +
            (", ".join(f"`{k}` ({v})" for k, v in tl["locations"].items()) or "none")]
    out += ["", "## CI", ""] + ([f"- `{c}`" for c in r["ci"]] or ["- none found"])
    out += ["", "## Docs worth reading first", ""] + ([f"- `{d}`" for d in r["docs"]] or ["- none found"])
    out += ["", "## Largest source files", ""] + [f"- `{f['file']}` ({f['lines']:,} lines)" for f in r["largest_files"]]
    if r["hotspots"]:
        out += ["", "## Change hotspots (most-edited files in recent history)", ""]
        out += [f"- `{h['file']}` ({h['commits']} commits)" for h in r["hotspots"]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--churn-commits", type=int, default=300)
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    report = build_report(root, args.churn_commits, args.top)
    print(json.dumps(report, indent=2) if args.json else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
