# Installing DevForge

DevForge is a standard Agent Skills repository: every skill is `skills/<name>/SKILL.md`.
Any agent that supports the format can use it. Native plugin manifests are included for
agents that have a plugin system, so you also get updates through their tooling.

## Where each agent looks for skills

`install.sh` uses these paths. `--project` installs into the current directory instead of your home directory.

| Agent | `--agent` | Global (default) | Project (`--project`) | Native plugin install |
|---|---|---|---|---|
| Claude Code | `claude` | `~/.claude/skills/` | `.claude/skills/` | `/plugin marketplace add suhaas19/devforge` then `/plugin install devforge@devforge` |
| Antigravity (IDE, app, CLI) | `antigravity` | `~/.gemini/config/skills/` (older builds: `~/.gemini/antigravity/skills/`) | `.agents/skills/` (older: `.agent/skills/`) | `agy plugin install https://github.com/suhaas19/devforge` |
| Codex | `codex` | `~/.codex/skills/` | `.agents/skills/` | `codex plugin marketplace add suhaas19/devforge`, then `/plugins` |
| Cursor | `cursor` | `~/.cursor/skills/` | `.cursor/skills/` | via `.cursor-plugin/plugin.json` |
| Gemini CLI | `gemini` | `~/.gemini/skills/` | `.gemini/skills/` | `gemini extensions install https://github.com/suhaas19/devforge` |
| GitHub Copilot | `copilot` | `~/.copilot/skills/` | `.github/skills/` | |
| OpenCode | `opencode` | `~/.config/opencode/skills/` | `.opencode/skills/` | |
| Shared folder read by several agents | `universal` | `~/.agents/skills/` | `.agents/skills/` | |

Agents move these paths between releases. If a skill does not show up, check the agent's
own documentation for its current skills directory, or use `npx skills add`, which tracks
the paths for 40+ agents.

## Option 1: native plugin (recommended where available)
Plugins update with the agent's own update command and keep the skills together.

**Claude Code**
```text
/plugin marketplace add suhaas19/devforge
/plugin install devforge@devforge
/plugin marketplace update devforge     # later, to update
```
Skills appear namespaced, e.g. `/devforge:secure-code-review`.

**Antigravity**
```bash
agy plugin install https://github.com/suhaas19/devforge
agy plugin list
```
Rerun the install command to update. Inside the app, skills are also listed under Customizations in the agent side panel; invoke one explicitly with `/<skill-name>`.

**Gemini CLI**
```bash
gemini extensions install https://github.com/suhaas19/devforge
gemini extensions update devforge
```

## Option 2: `npx skills` (any agent)
```bash
npx skills add suhaas19/devforge --list          # see skills
npx skills add suhaas19/devforge -a claude-code -a antigravity -g
npx skills add suhaas19/devforge --skill skill-authoring
```

## Option 3: `install.sh` (no Node, works offline from a clone)
```bash
git clone https://github.com/suhaas19/devforge && cd devforge
./install.sh --help
```
Prefer reading a script before running it. If you want a one-liner, download first, read, then run:
```bash
curl -fsSL https://raw.githubusercontent.com/suhaas19/devforge/main/install.sh -o devforge-install.sh
less devforge-install.sh && bash devforge-install.sh --agent antigravity
```

## Option 4: manual
Copy any `skills/<name>/` folder into one of the directories in the table. Keep the folder name identical to the `name:` in its `SKILL.md`.

## Verify it works
Start a new session and ask something that should trigger a skill, for example
*"review the changes on this branch before I open a PR"*. The agent should load
`reviewing-code-changes` and run `scripts/review_context.py`. In Claude Code, `/skills`
lists loaded skills; in Antigravity, see Customizations.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Skill never loads | Start a new session after installing; check the folder name matches `name:`; confirm the path for your agent version |
| `permission denied` running a script | `chmod +x <skill>/scripts/*` (install.sh does this for copies) |
| `python3: command not found` (Windows) | Use `py -3 scripts/...` or install Python 3; or run the agent in WSL |
| Duplicate skills after using two install methods | Remove one copy (`./install.sh --uninstall --agent <name>`) |
| Plugin install fails in Claude Code | `claude plugin validate .` in a clone shows manifest errors |
