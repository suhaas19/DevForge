---
tags: [bug-reproduction]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

parse_orders.py crashes with a KeyError on orders.json (its ~400 records). i need the smallest input that still triggers the same crash so i can put it in a bug report. save it as minimal.json

Input files: orders.json, parse_orders.py
