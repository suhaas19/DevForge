---
tags: [test-generation]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

add unit tests for slugify in textutils.py, we use pytest. put them in tests/test_textutils.py

Input files: conftest.py, tests/, textutils.py
