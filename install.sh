#!/usr/bin/env bash
# DevForge skills installer: copies (or symlinks) skills into the skill folders of the
# coding agents you use. Works without Node; for a GUI-less, multi-agent alternative see
# `npx skills add suhaas19/devforge`.
#
# Usage:
#   ./install.sh [options]
#   bash install.sh --agent claude --agent antigravity
#
# Options:
#   -a, --agent NAME   claude | antigravity | codex | cursor | gemini | copilot | opencode |
#                      universal (~/.agents/skills) | all.  Repeatable. Default: auto-detect.
#   -s, --skill NAME   install only this skill (repeatable). Default: all skills.
#   -p, --project      install into the current project (e.g. ./.claude/skills) instead of your home dir
#   -l, --link         symlink instead of copy (stays in sync with this checkout; good for development)
#       --source DIR   use an existing checkout instead of downloading
#       --ref REF      git branch/tag to download (default: main)
#       --list         list available skills and exit
#       --uninstall    remove DevForge skills from the selected agents
#   -n, --dry-run      show what would happen
#   -y, --yes          overwrite existing skills with the same name without asking
#   -h, --help
set -euo pipefail

REPO_URL="https://github.com/suhaas19/devforge.git"
REF="main"
AGENTS=()
SKILLS=()
SCOPE="global"
MODE="copy"
SOURCE=""
ACTION="install"
DRY=0
YES=0

say()  { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
run()  { if [[ $DRY -eq 1 ]]; then say "  [dry-run] $*"; else "$@"; fi; }

usage() { sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -a|--agent)   [[ $# -ge 2 ]] || die "$1 needs a value"; AGENTS+=("$2"); shift 2 ;;
    -s|--skill)   [[ $# -ge 2 ]] || die "$1 needs a value"; SKILLS+=("$2"); shift 2 ;;
    -p|--project) SCOPE="project"; shift ;;
    -l|--link)    MODE="link"; shift ;;
    --source)     [[ $# -ge 2 ]] || die "$1 needs a value"; SOURCE="$2"; shift 2 ;;
    --ref)        [[ $# -ge 2 ]] || die "$1 needs a value"; REF="$2"; shift 2 ;;
    --list)       ACTION="list"; shift ;;
    --uninstall)  ACTION="uninstall"; shift ;;
    -n|--dry-run) DRY=1; shift ;;
    -y|--yes)     YES=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
done

# Skill directory per agent: "global|project"
target_dir() {
  local agent="$1" scope="$2"
  case "$agent:$scope" in
    claude:global)      echo "$HOME/.claude/skills" ;;
    claude:project)     echo "$PWD/.claude/skills" ;;
    antigravity:global) echo "$HOME/.gemini/config/skills" ;;
    antigravity:project) echo "$PWD/.agents/skills" ;;
    codex:global)       echo "${CODEX_HOME:-$HOME/.codex}/skills" ;;
    codex:project)      echo "$PWD/.agents/skills" ;;
    cursor:global)      echo "$HOME/.cursor/skills" ;;
    cursor:project)     echo "$PWD/.cursor/skills" ;;
    gemini:global)      echo "$HOME/.gemini/skills" ;;
    gemini:project)     echo "$PWD/.gemini/skills" ;;
    copilot:global)     echo "$HOME/.copilot/skills" ;;
    copilot:project)    echo "$PWD/.github/skills" ;;
    opencode:global)    echo "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills" ;;
    opencode:project)   echo "$PWD/.opencode/skills" ;;
    universal:global)   echo "$HOME/.agents/skills" ;;
    universal:project)  echo "$PWD/.agents/skills" ;;
    *) return 1 ;;
  esac
}
ALL_AGENTS=(claude antigravity codex cursor gemini copilot opencode universal)

detect_agents() {
  local found=()
  [[ -d "$HOME/.claude" ]] && found+=(claude)
  [[ -d "$HOME/.gemini/config" || -d "$HOME/.gemini/antigravity" || -d "$HOME/.gemini/antigravity-cli" ]] && found+=(antigravity)
  [[ -d "${CODEX_HOME:-$HOME/.codex}" ]] && found+=(codex)
  [[ -d "$HOME/.cursor" ]] && found+=(cursor)
  { [[ -d "$HOME/.gemini" ]] && command -v gemini >/dev/null 2>&1; } && found+=(gemini)
  [[ -d "$HOME/.copilot" ]] && found+=(copilot)
  [[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/opencode" ]] && found+=(opencode)
  [[ ${#found[@]} -eq 0 ]] && found=(universal)
  printf '%s\n' "${found[@]}"
}

# ---- resolve source checkout
CLEANUP=""
if [[ -z "$SOURCE" ]]; then
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
  if [[ -n "$here" && -d "$here/skills" && -f "$here/plugin-meta.json" ]]; then
    SOURCE="$here"
  else
    command -v git >/dev/null 2>&1 || die "git is required to download the skills (or pass --source DIR)"
    [[ "$REPO_URL" == *suhaas19* ]] && die "REPO_URL is not configured; run scripts/sync_manifests.py --owner <you> first, or pass --source DIR"
    tmp="$(mktemp -d "${TMPDIR:-/tmp}/devforge.XXXXXX")"
    CLEANUP="$tmp"
    say "Downloading $REPO_URL ($REF)..."
    git clone --quiet --depth 1 --branch "$REF" "$REPO_URL" "$tmp/devforge" || die "clone failed"
    SOURCE="$tmp/devforge"
    [[ "$MODE" == "link" ]] && { warn "--link needs a persistent checkout; falling back to copy"; MODE="copy"; }
  fi
fi
trap '[[ -n "$CLEANUP" ]] && rm -rf "$CLEANUP"' EXIT
[[ -d "$SOURCE/skills" ]] || die "no skills/ directory in $SOURCE"
SOURCE="$(cd "$SOURCE" && pwd)"

AVAILABLE=()
for d in "$SOURCE"/skills/*/; do
  [[ -f "$d/SKILL.md" ]] && AVAILABLE+=("$(basename "$d")")
done

[[ ${#AVAILABLE[@]} -gt 0 ]] || die "no skills found in $SOURCE/skills"

if [[ "$ACTION" == "list" ]]; then
  for s in "${AVAILABLE[@]}"; do
    desc="$(sed -n 's/^description: *//p' "$SOURCE/skills/$s/SKILL.md" | head -1 | cut -c1-110)"
    printf '  %-26s %s...\n' "$s" "$desc"
  done
  exit 0
fi

if [[ ${#SKILLS[@]} -eq 0 ]]; then
  SKILLS=("${AVAILABLE[@]}")
else
  for s in "${SKILLS[@]}"; do
    [[ -f "$SOURCE/skills/$s/SKILL.md" ]] || die "unknown skill '$s' (see --list)"
  done
fi

if [[ ${#AGENTS[@]} -eq 0 ]]; then
  while IFS= read -r a; do AGENTS+=("$a"); done < <(detect_agents)
  say "Detected agents: ${AGENTS[*]}  (override with --agent)"
elif [[ " ${AGENTS[*]} " == *" all "* ]]; then
  AGENTS=("${ALL_AGENTS[@]}")
fi

# Several agents can share a project folder (.agents/skills); install there once.
# (A plain string, not an associative array, so this runs on macOS's bash 3.2.)
SEEN_DIRS="|"
changed=0
for agent in "${AGENTS[@]}"; do
  dest="$(target_dir "$agent" "$SCOPE")" || die "unknown agent '$agent' (choose from: ${ALL_AGENTS[*]} all)"
  [[ "$SEEN_DIRS" == *"|$dest|"* ]] && continue
  SEEN_DIRS="$SEEN_DIRS$dest|"
  say ""
  say "==> $agent: $dest"
  [[ "$ACTION" == "install" ]] && run mkdir -p "$dest"
  for s in "${SKILLS[@]}"; do
    target="$dest/$s"
    if [[ "$ACTION" == "uninstall" ]]; then
      if [[ -L "$target" || -f "$target/SKILL.md" ]]; then
        run rm -rf "$target"; say "  removed $s"; changed=$((changed+1))
      fi
      continue
    fi
    if [[ -e "$target" || -L "$target" ]]; then
      if [[ $YES -ne 1 ]]; then
        if [[ -t 0 ]]; then
          read -r -p "  $s exists in $dest. Overwrite? [y/N] " ans
          [[ "$ans" =~ ^[Yy]$ ]] || { say "  skipped $s"; continue; }
        else
          say "  skipped $s (exists; pass --yes to overwrite)"; continue
        fi
      fi
      run rm -rf "$target"
    fi
    if [[ "$MODE" == "link" ]]; then
      run ln -s "$SOURCE/skills/$s" "$target"
    else
      run cp -R "$SOURCE/skills/$s" "$target"
      run find "$target" -path '*/scripts/*' -type f \( -name '*.py' -o -name '*.sh' \) -exec chmod +x {} +
    fi
    say "  installed $s"; changed=$((changed+1))
  done
done

say ""
if [[ "$ACTION" == "uninstall" ]]; then
  say "Removed $changed skill folder(s)."
else
  verb="copied"; [[ "$MODE" == "link" ]] && verb="linked"
  say "Done: $changed skill(s) $verb. Restart your agent (or start a new session) to load them."
  say "Tip: in Claude Code, /plugin marketplace add suhaas19/devforge gives you auto-updates instead."
fi
