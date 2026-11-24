# Contributing

Thanks for improving DevForge.

1. Fork `suhaas19/devforge` and create a branch.
2. For a new skill, follow [docs/AUTHORING.md](docs/AUTHORING.md). One skill = one job.
3. Before opening a PR:
   ```bash
   python3 skills/skill-authoring/scripts/validate_skill.py skills --strict
   python3 -m pytest -q
   python3 scripts/sync_manifests.py --check
   ```
4. Use Conventional Commits (`feat(skill-name): ...`, `fix(install): ...`). `skills/writing-commits-and-prs/scripts/commit_helper.py install-hook` checks this locally.
5. In the PR, include the eval prompts you tried and what changed in the agent's behavior with and without the skill.

Skills that add network access, install software, or touch credentials need a clear reason in the PR and will be reviewed closely.
