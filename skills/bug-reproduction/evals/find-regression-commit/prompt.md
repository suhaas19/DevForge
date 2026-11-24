---
tags: [bug-reproduction]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

greet.py used to print 'Hello, Ada!' for `python3 greet.py Ada` but now prints something else. it worked at the tag v1.0. figure out which commit broke it
