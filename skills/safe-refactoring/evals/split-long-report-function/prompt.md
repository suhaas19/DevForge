---
tags: [safe-refactoring]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

report.py has one giant function, can you refactor it into smaller functions? the output must stay exactly the same, other scripts parse it. sample inputs are in samples/

Input files: report.py, samples/
