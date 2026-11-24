---
tags: [test-generation]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

users report that feb 29 2024 is rejected as an invalid date by is_valid_date in dates.py. before we fix it, add a regression test that shows the bug. dont fix it yet

Input files: conftest.py, dates.py, tests/
