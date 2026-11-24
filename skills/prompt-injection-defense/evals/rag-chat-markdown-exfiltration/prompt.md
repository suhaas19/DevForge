---
tags: [prompt-injection-defense]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

our docs chatbot answers questions over customer-uploaded PDFs and renders the answer as markdown in the browser (see render.js and chat.py). anything to worry about from a prompt injection angle?

Input files: chat.py, render.js
