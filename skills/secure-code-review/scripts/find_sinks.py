#!/usr/bin/env python3
"""List dangerous sinks (injection, deserialization, SSRF, XSS, weak crypto) as review candidates.

Usage:
    find_sinks.py [PATH ...] [--json] [--category CAT ...] [--include-tests]

Each hit is a CANDIDATE, not a vulnerability. The point is to give the reviewer
a short list of places where untrusted input could reach something dangerous, so
they can trace data flow from source to sink and confirm or dismiss each one.
LLM-only vulnerability hunting has a high false-positive rate; anchoring on
concrete sinks and traced flows is what keeps findings honest.

Categories: command-injection, code-injection, sql-injection, deserialization,
path-traversal, ssrf, xss, xxe, weak-crypto, tls-disabled, open-redirect.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# secret-scan: ignore  skill-lint: allow   (this file lists patterns on purpose)
SINKS = {
    "command-injection": [
        (r"\bsubprocess\.(run|call|Popen|check_output|check_call)\([^)]*shell\s*=\s*True", "py", "subprocess with shell=True"),
        (r"\bos\.(system|popen)\(", "py", "os.system/os.popen"),
        (r"\bchild_process\.(exec|execSync)\(|\brequire\(['\"]child_process['\"]\)\.exec\(|\bexecSync\(", "js", "child_process.exec"),
        (r"\bexec\.Command\(\s*\"(sh|bash|cmd)\"", "go", "exec.Command via shell"),
        (r"Runtime\.getRuntime\(\)\.exec\(|new ProcessBuilder\(", "java", "Runtime.exec / ProcessBuilder"),
        (r"\b(system|exec|shell_exec|passthru|popen|proc_open)\s*\(", "php", "PHP shell function"),
        (r"`[^`]*#\{|\b%x\(|\bKernel\.(system|exec)\b|\bIO\.popen\(", "rb", "Ruby shell execution"),
    ],
    "code-injection": [
        (r"(?<![\w.])eval\(|(?<![\w.])exec\(", "py", "eval/exec"),
        (r"(?<![\w.])eval\(|new Function\(|setTimeout\(\s*['\"`]", "js", "eval/new Function"),
        (r"\b__import__\(|importlib\.import_module\(", "py", "dynamic import"),
    ],
    "sql-injection": [
        (r"\.(execute|executemany|raw|query)\(\s*f['\"]", "py", "f-string in SQL call"),
        (r"\.(execute|executemany|raw)\([^)]*(%\s*\(|\.format\(|\+\s*\w)", "py", "string-built SQL"),
        (r"\.(query|execute|raw)\(\s*`[^`]*\$\{", "js", "template literal in SQL call"),
        (r"\.(query|execute)\([^)]*['\"]\s*\+\s*\w", "js", "concatenated SQL"),
        (r"\.(Query|QueryRow|Exec)(Context)?\([^)]*(fmt\.Sprintf|\+\s*\w)", "go", "string-built SQL"),
        (r"(createStatement|executeQuery|executeUpdate)\([^)]*\+", "java", "concatenated JDBC SQL"),
        (r"(?i)\b(select|insert|update|delete)\b[^;\n]{0,80}['\"]\s*(\+|\.\s*\$|%)\s*", "any", "SQL text built by concatenation"),
    ],
    "deserialization": [
        (r"\bpickle\.loads?\(|\bcPickle\.loads?\(|\bdill\.loads?\(|\bjoblib\.load\(", "py", "pickle-family load"),
        (r"\byaml\.load\((?![^)]*Loader\s*=\s*(yaml\.)?SafeLoader)", "py", "yaml.load without SafeLoader"),
        (r"\btorch\.load\((?![^)]*weights_only\s*=\s*True)", "py", "torch.load without weights_only=True"),
        (r"\bmarshal\.loads?\(|\bshelve\.open\(", "py", "marshal/shelve"),
        (r"ObjectInputStream|readObject\(\)|XMLDecoder", "java", "Java native deserialization"),
        (r"\bunserialize\(", "php", "PHP unserialize"),
        (r"Marshal\.load|YAML\.load\((?!.*safe)", "rb", "Ruby Marshal/YAML.load"),
        (r"BinaryFormatter|NetDataContractSerializer|LosFormatter", "cs", ".NET unsafe formatter"),
        (r"node-serialize|serialize-javascript.*unserialize", "js", "JS unsafe deserialization"),
    ],
    "path-traversal": [
        (r"\bopen\([^)]*(request\.|req\.|params|args\[|input\()", "py", "open() on request data"),
        (r"\b(send_file|send_from_directory|FileResponse)\(", "py", "file response"),
        (r"\b(fs\.(readFile|createReadStream|writeFile)|res\.sendFile|path\.join)\([^)]*(req\.|params|query|body)", "js", "fs on request data"),
        (r"\b(zipfile|tarfile)\b.*\.extractall\(", "py", "archive extractall (zip slip)"),
    ],
    "ssrf": [
        (r"\brequests\.(get|post|put|request)\([^)]*(request\.|req\.|url\s*=\s*\w|params|args)", "py", "outbound request with variable URL"),
        (r"\burllib\.request\.urlopen\(|\bhttpx\.(get|post)\(\s*\w", "py", "urlopen / httpx with variable URL"),
        (r"\b(fetch|axios\.(get|post)|got|request)\(\s*(req\.|`[^`]*\$\{|\w+Url|url\b)", "js", "outbound fetch with variable URL"),
        (r"\bhttp\.(Get|Post)\(\s*\w", "go", "http.Get with variable URL"),
    ],
    "xss": [
        (r"\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML\(|document\.write\(", "js", "raw HTML sink"),
        (r"dangerouslySetInnerHTML", "js", "React dangerouslySetInnerHTML"),
        (r"v-html=|\[innerHTML\]=|bypassSecurityTrust", "js", "framework raw-HTML binding"),
        (r"\|\s*safe\b|mark_safe\(|Markup\(|autoescape\s+false", "py", "template autoescape bypass"),
        (r"template\.HTML\(", "go", "html/template bypass"),
        (r"\.html_safe\b|raw\(", "rb", "Rails raw output"),
    ],
    "xxe": [
        (r"\b(etree|lxml\.etree)\.(parse|fromstring|XMLParser)\((?![^)]*resolve_entities\s*=\s*False)", "py", "XML parse (check entity resolution)"),
        (r"DocumentBuilderFactory\.newInstance|SAXParserFactory\.newInstance|XMLInputFactory\.newInstance", "java", "Java XML factory (check XXE features)"),
    ],
    "weak-crypto": [
        (r"\b(md5|sha1)\s*\(|hashlib\.(md5|sha1)\(|MessageDigest\.getInstance\(\"(MD5|SHA-?1)\"\)|crypto\.createHash\(['\"](md5|sha1)", "any", "MD5/SHA-1 (fine for checksums, not passwords/signatures)"),
        (r"\bDES\b|\bRC4\b|AES/ECB|MODE_ECB|\"ECB\"", "any", "broken cipher or ECB mode"),
        (r"\brandom\.(random|randint|choice)\(.*(token|secret|password|key|nonce|salt)", "py", "non-cryptographic RNG for secrets"),
        (r"Math\.random\(\).*(token|secret|password|key|nonce|id)", "js", "Math.random for secrets"),
    ],
    "tls-disabled": [
        (r"verify\s*=\s*False|ssl\._create_unverified_context|CERT_NONE", "py", "TLS verification disabled"),
        (r"rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED", "js", "TLS verification disabled"),
        (r"InsecureSkipVerify\s*:\s*true", "go", "TLS verification disabled"),
    ],
    "open-redirect": [
        (r"\bredirect\([^)]*(request\.|req\.|params|args\.get|query)", "any", "redirect to request-controlled URL"),
        (r"res\.redirect\([^)]*req\.", "js", "redirect to request-controlled URL"),
    ],
}
LANG_OF = {".py": "py", ".js": "js", ".jsx": "js", ".ts": "js", ".tsx": "js", ".mjs": "js", ".cjs": "js", ".vue": "js",
           ".svelte": "js", ".go": "go", ".java": "java", ".kt": "java", ".php": "php", ".rb": "rb", ".erb": "rb",
           ".cs": "cs", ".html": "js", ".jinja": "py", ".j2": "py"}
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build", "target", "__pycache__", "site-packages"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|testdata|mocks?)/|_test\.|\.test\.|\.spec\.")
COMPILED = {cat: [(re.compile(rx), lang, why) for rx, lang, why in rules] for cat, rules in SINKS.items()}


def iter_files(paths):
    for root in paths:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, capture_output=True, text=True)
        if out.returncode == 0:
            for f in out.stdout.splitlines():
                if not any(p in SKIP_DIRS for p in Path(f).parts):
                    yield root / f
        else:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    yield Path(dirpath) / fn


def scan(path: Path, cats):
    lang = LANG_OF.get(path.suffix.lower())
    if not lang:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if len(stripped) > 2000 or stripped.startswith(("#", "//", "*", "/*")) or "skill-lint: allow" in line:
            continue
        for cat in cats:
            for rx, rlang, why in COMPILED[cat]:
                if rlang not in (lang, "any"):
                    continue
                if rx.search(line):
                    hits.append({"file": path.as_posix(), "line": lineno, "category": cat, "why": why, "code": stripped[:160]})
                    break
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--category", action="append", choices=sorted(SINKS), help="limit to category (repeatable)")
    ap.add_argument("--include-tests", action="store_true")
    args = ap.parse_args(argv)
    cats = args.category or list(SINKS)
    hits = []
    for p in iter_files(args.paths):
        if not args.include_tests and TEST_PATH.search(p.as_posix()):
            continue
        hits.extend(scan(p, cats))
    if args.json:
        print(json.dumps(hits, indent=2))
        return 0
    if not hits:
        print("no candidate sinks found")
        return 0
    by_cat = Counter(h["category"] for h in hits)
    print(f"{len(hits)} candidate sink(s): " + ", ".join(f"{c}={n}" for c, n in by_cat.most_common()) + "\n")
    for cat in cats:
        group = [h for h in hits if h["category"] == cat]
        if group:
            print(f"## {cat}")
            for h in group:
                print(f"  {h['file']}:{h['line']}  ({h['why']})\n      {h['code']}")
            print()
    print("Next: for each candidate, trace where its input comes from. Report only flows you can show.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
