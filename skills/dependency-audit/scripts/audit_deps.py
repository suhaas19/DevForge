#!/usr/bin/env python3
"""Detect a project's package ecosystems and run (or print) the right vulnerability/outdated audits.

Usage:
    audit_deps.py [ROOT] [--run] [--json] [--timeout 300]

Without --run it only prints the plan: which manifests and lockfiles exist,
whether each project pins its dependencies, and which audit commands apply,
marking the tools that are installed. With --run it executes the installed ones
and saves raw output to .dependency-audit/ for the report.

Preferred tools per ecosystem (first installed one wins; osv-scanner covers all):
  Python   pip-audit            Node   npm/pnpm/yarn audit      Go     govulncheck
  Rust     cargo audit          Ruby   bundle-audit             PHP    composer audit
  Java     osv-scanner          .NET   dotnet list package --vulnerable
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ECOSYSTEMS = {
    "python": {
        "manifests": ["pyproject.toml", "requirements.txt", "requirements-dev.txt", "setup.py", "setup.cfg", "Pipfile"],
        "locks": ["poetry.lock", "uv.lock", "Pipfile.lock", "requirements.lock", "pdm.lock"],
        "audit": [("pip-audit", "pip-audit -r {req} --format json" , "requirements"), ("pip-audit", "pip-audit --format json", None)],
        "outdated": [("pip", "pip list --outdated --format json", None)],
    },
    "node": {
        "manifests": ["package.json"],
        "locks": ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock"],
        "audit": [("pnpm", "pnpm audit --json", "pnpm-lock.yaml"), ("yarn", "yarn npm audit --json", "yarn.lock"),
                  ("npm", "npm audit --json", "package-lock.json")],
        "outdated": [("npm", "npm outdated --json", None)],
    },
    "go": {"manifests": ["go.mod"], "locks": ["go.sum"],
           "audit": [("govulncheck", "govulncheck -json ./...", None)], "outdated": [("go", "go list -u -m -json all", None)]},
    "rust": {"manifests": ["Cargo.toml"], "locks": ["Cargo.lock"],
             "audit": [("cargo-audit", "cargo audit --json", None)], "outdated": [("cargo-outdated", "cargo outdated --format json", None)]},
    "ruby": {"manifests": ["Gemfile"], "locks": ["Gemfile.lock"],
             "audit": [("bundle-audit", "bundle-audit check --update", None)], "outdated": [("bundle", "bundle outdated --parseable", None)]},
    "php": {"manifests": ["composer.json"], "locks": ["composer.lock"],
            "audit": [("composer", "composer audit --format=json", None)], "outdated": [("composer", "composer outdated --format=json", None)]},
    "java": {"manifests": ["pom.xml", "build.gradle", "build.gradle.kts"], "locks": ["gradle.lockfile"],
             "audit": [], "outdated": []},
    "dotnet": {"manifests": [], "glob": ["*.csproj", "*.fsproj"], "locks": ["packages.lock.json"],
               "audit": [("dotnet", "dotnet list package --vulnerable --include-transitive", None)],
               "outdated": [("dotnet", "dotnet list package --outdated", None)]},
}
TOOL_BIN = {"cargo-audit": "cargo-audit", "cargo-outdated": "cargo-outdated", "bundle-audit": "bundle-audit"}


def have(tool):
    return shutil.which(TOOL_BIN.get(tool, tool)) is not None


def detect(root: Path):
    found = []
    for eco, spec in ECOSYSTEMS.items():
        manifests = [m for m in spec["manifests"] if (root / m).exists()]
        for pattern in spec.get("glob", []):
            manifests += [p.name for p in root.glob(pattern)]
        if not manifests:
            continue
        locks = [l for l in spec["locks"] if (root / l).exists()]
        plan = []
        for tool, cmd, needs in spec["audit"]:
            if needs == "requirements":
                req = next((m for m in manifests if m.startswith("requirements")), None)
                if not req:
                    continue
                cmd = cmd.format(req=req)
            elif needs and needs not in locks:
                continue
            plan.append({"kind": "vulnerabilities", "tool": tool, "cmd": cmd, "installed": have(tool)})
            break
        for tool, cmd, _ in spec["outdated"]:
            plan.append({"kind": "outdated", "tool": tool, "cmd": cmd, "installed": have(tool)})
        found.append({"ecosystem": eco, "manifests": manifests, "lockfiles": locks,
                      "pinned": bool(locks) or any(_pinned_requirements(root / m) for m in manifests if m.startswith("requirements")),
                      "plan": plan})
    if found:
        osv = {"kind": "vulnerabilities", "tool": "osv-scanner", "cmd": "osv-scanner scan source -r --format json .",
               "installed": have("osv-scanner")}
        found.append({"ecosystem": "all (cross-check)", "manifests": [], "lockfiles": [], "pinned": None, "plan": [osv]})
    return found


def _pinned_requirements(path: Path) -> bool:
    try:
        lines = [l.split("#")[0].strip() for l in path.read_text(encoding="utf-8").splitlines()]
    except OSError:
        return False
    reqs = [l for l in lines if l and not l.startswith(("-", "git+", "http"))]
    return bool(reqs) and all("==" in l for l in reqs)


def run_plan(root: Path, found, timeout):
    outdir = root / ".dependency-audit"
    outdir.mkdir(exist_ok=True)
    for eco in found:
        for step in eco["plan"]:
            if not step["installed"]:
                step["result"] = "skipped: tool not installed"
                continue
            name = f"{eco['ecosystem'].split()[0]}-{step['kind']}-{step['tool']}.txt"
            try:
                res = subprocess.run(step["cmd"], shell=True, cwd=root, capture_output=True, text=True, timeout=timeout)
                (outdir / name).write_text(res.stdout + ("\n--- stderr ---\n" + res.stderr if res.stderr else ""), encoding="utf-8")
                # Most audit tools exit non-zero when they FIND issues; that is not a failure to run.
                step["result"] = f"exit {res.returncode}, output in .dependency-audit/{name}"
            except subprocess.TimeoutExpired:
                step["result"] = f"timed out after {timeout}s"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--run", action="store_true", help="execute installed audit tools")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args(argv)
    root = Path(args.root)
    found = detect(root)
    if not found:
        print("no supported dependency manifests found", file=sys.stderr)
        return 2
    if args.run:
        run_plan(root, found, args.timeout)
    if args.json:
        print(json.dumps(found, indent=2))
        return 0
    for eco in found:
        print(f"## {eco['ecosystem']}")
        if eco["manifests"]:
            print(f"  manifests: {', '.join(eco['manifests'])}")
            print(f"  lockfiles: {', '.join(eco['lockfiles']) or 'NONE (builds are not reproducible; transitive versions float)'}")
        for step in eco["plan"]:
            mark = "✓" if step["installed"] else "✗ not installed"
            print(f"  [{step['kind']}] {step['cmd']}   ({step['tool']} {mark})" + (f"\n      -> {step['result']}" if "result" in step else ""))
        print()
    if not args.run:
        print("Plan only. Re-run with --run to execute the installed tools.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
