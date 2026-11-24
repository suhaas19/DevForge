#!/usr/bin/env bash
# Find the commit that introduced a regression with `git bisect run`.
#
# Usage:
#   bisect_run.sh GOOD_REF BAD_REF -- TEST_COMMAND...
#   bisect_run.sh v1.2.0 HEAD -- pytest -x tests/test_parser.py::test_unicode
#   BUILD="npm ci" bisect_run.sh abc123 main -- npm test -- parser
#
# TEST_COMMAND must exit 0 when the bug is ABSENT and non-zero when it is present.
# If $BUILD is set it runs first at each step; a build failure marks the commit
# as untestable (exit 125) instead of bad, so broken intermediate commits do not
# mislead the search. The working tree must be clean. Always ends with
# `git bisect reset`, even on Ctrl-C.
set -euo pipefail

if [[ $# -lt 4 || "$3" != "--" ]]; then
  sed -n '2,13p' "$0"; exit 2
fi
GOOD="$1"; BAD="$2"; shift 3

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "error: working tree has uncommitted changes; commit or stash them first" >&2; exit 2
fi

step="$(mktemp "${TMPDIR:-/tmp}/bisect-step.XXXXXX")"
trap 'git bisect reset >/dev/null 2>&1 || true; rm -f "$step"' EXIT
{
  echo '#!/usr/bin/env bash'
  if [[ -n "${BUILD:-}" ]]; then
    printf '%s >/dev/null 2>&1 || exit 125\n' "$BUILD"
  fi
  printf '%q ' "$@"; echo
  # shellcheck disable=SC2016  # written literally into the step script
  echo 'rc=$?; if [[ $rc -ge 125 ]]; then exit 1; fi; exit $rc'
} > "$step"
chmod +x "$step"

git bisect start "$BAD" "$GOOD"
git bisect run "$step"
# Print our own summary: git's wording and output stream vary between versions.
echo
echo "First bad commit: $(git log -1 --format='%h %s' refs/bisect/bad)"
git show --stat --format='%H%n%an <%ae>%n%ad%n%n%s%n%n%b' refs/bisect/bad | head -40
