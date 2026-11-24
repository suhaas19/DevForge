#!/usr/bin/env python3
"""Check that package names exist and look trustworthy BEFORE adding them (guards against slopsquatting).

Usage:
    verify_package.py NAME [NAME ...] --ecosystem pypi|npm [--json] [--offline]
    verify_package.py --from-file requirements.txt --ecosystem pypi

LLMs regularly suggest packages that do not exist; attackers register those
names. For each name this reports:
  * exists on the registry? (a missing package is a red flag, never "just install it")
  * first release date and number of releases (brand-new single-release packages are suspicious)
  * latest version, whether a source repository is listed
  * typosquat risk: edit distance <= 2 from a popular package name in assets/
Verdicts: OK, REVIEW (look closer before installing), BLOCK (do not install).
Needs network access to pypi.org / registry.npmjs.org; --offline runs only the
typosquat check. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
UA = {"User-Agent": "devforge-verify-package/1.0"}


def normalize(name, eco):
    return re.sub(r"[-_.]+", "-", name).lower() if eco == "pypi" else name.lower()


def popular(eco):
    path = ASSETS / f"popular-{eco}.txt"
    try:
        return [normalize(l.strip(), eco) for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    except OSError:
        return []


def distance(a, b, limit=3):
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def registry_info(name, eco):
    try:
        if eco == "pypi":
            data = fetch_json(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
            releases = {v: files for v, files in data.get("releases", {}).items() if files}
            dates = sorted(f["upload_time_iso_8601"] for files in releases.values() for f in files if f.get("upload_time_iso_8601"))
            info = data.get("info", {})
            urls = info.get("project_urls") or {}
            repo = next((u for k, u in urls.items() if re.search(r"source|repo|github|gitlab|code", k, re.I)), info.get("home_page"))
            return {"exists": True, "latest": info.get("version"), "releases": len(releases),
                    "first_release": dates[0][:10] if dates else None, "repository": repo or None,
                    "summary": (info.get("summary") or "")[:120]}
        data = fetch_json(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}")
        times = data.get("time", {})
        repo = data.get("repository")
        repo = repo.get("url") if isinstance(repo, dict) else repo
        return {"exists": True, "latest": (data.get("dist-tags") or {}).get("latest"),
                "releases": len(data.get("versions", {})), "first_release": (times.get("created") or "")[:10] or None,
                "repository": repo, "summary": (data.get("description") or "")[:120],
                "deprecated": bool(((data.get("versions") or {}).get((data.get("dist-tags") or {}).get("latest"), {}) or {}).get("deprecated"))}
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"exists": False}
        return {"error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"error": f"network: {exc}"}


def assess(name, eco, offline):
    norm = normalize(name, eco)
    pops = popular(eco)
    near = sorted({p for p in pops if p != norm and distance(norm, p) <= (1 if len(norm) <= 5 else 2)})
    result = {"name": name, "ecosystem": eco, "similar_to_popular": near[:5], "reasons": []}
    if not offline:
        result.update(registry_info(name, eco))
    verdict = "OK"
    if result.get("error"):
        verdict = "REVIEW"
        result["reasons"].append(f"could not reach registry ({result['error']})")
    elif result.get("exists") is False:
        verdict = "BLOCK"
        result["reasons"].append("package does not exist on the registry (possibly hallucinated; an attacker could register it)")
    elif not offline:
        first = result.get("first_release")
        if first:
            age = (dt.date.today() - dt.date.fromisoformat(first)).days
            result["age_days"] = age
            if age < 90:
                verdict = "REVIEW"
                result["reasons"].append(f"first published {age} days ago")
        if (result.get("releases") or 0) <= 1:
            verdict = "REVIEW"
            result["reasons"].append("only one release")
        if not result.get("repository"):
            verdict = "REVIEW" if verdict == "OK" else verdict
            result["reasons"].append("no source repository listed")
        if result.get("deprecated"):
            verdict = "REVIEW" if verdict == "OK" else verdict
            result["reasons"].append("latest version is deprecated")
    if near and norm not in pops:
        verdict = "BLOCK" if verdict == "BLOCK" else "REVIEW"
        result["reasons"].append(f"name is very close to popular package(s): {', '.join(near[:3])} (typosquat?)")
    result["verdict"] = verdict
    return result


def names_from_file(path):
    names = []
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith("package.json"):
        pkg = json.loads(text)
        for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            names += list((pkg.get(key) or {}).keys())
        return names
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if m:
            names.append(m.group(1))
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--ecosystem", "-e", choices=["pypi", "npm"], required=True)
    ap.add_argument("--from-file", help="requirements.txt or package.json")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    names = list(args.names) + (names_from_file(args.from_file) if args.from_file else [])
    if not names:
        ap.error("give package names or --from-file")
    results = [assess(n, args.ecosystem, args.offline) for n in names]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            meta = ""
            if r.get("exists"):
                meta = f" latest={r.get('latest')} releases={r.get('releases')} first={r.get('first_release')}"
            print(f"[{r['verdict']:<6}] {r['name']}{meta}")
            for reason in r["reasons"]:
                print(f"           - {reason}")
    return 1 if any(r["verdict"] == "BLOCK" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
