# Working in the DevForge repository

This repo is a collection of Agent Skills. When you change it:

- Skills live in `skills/<name>/SKILL.md`; the folder name must equal `name:` in the frontmatter.
- Validate after every skill edit: `python3 skills/skill-authoring/scripts/validate_skill.py skills --strict`.
- Run the tests: `python3 -m pytest -q`.
- Never hand-edit the manifests (`.claude-plugin/`, `.antigravity-plugin/`, `.cursor-plugin/`, `.codex-plugin/`, `.agents/plugins/`, `gemini-extension.json`). Edit `plugin-meta.json` and run `python3 scripts/sync_manifests.py`.
- Scripts must be Python 3.9+ standard library (or POSIX bash), have a usage docstring and a test in `tests/test_scripts.py`.
- To write a new skill, follow `skills/skill-authoring/SKILL.md`.
