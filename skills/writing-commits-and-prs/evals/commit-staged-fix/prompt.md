---
tags: [writing-commits-and-prs]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

commit the staged change. context: the processor times out after 2s during their nightly failover and checkouts were failing, so i raised the client timeout and added retries
