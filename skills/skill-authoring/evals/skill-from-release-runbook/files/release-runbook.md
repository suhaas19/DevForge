# Release runbook
1. Make sure main is green in CI.
2. Update CHANGELOG.md: move Unreleased items under the new version heading. (People forget this; then the tag has no notes.)
3. Bump version in pyproject.toml.
4. Commit "chore(release): vX.Y.Z", then tag vX.Y.Z (tag AFTER the changelog commit, never before).
5. Push commit and tag: git push && git push --tags
6. CI publishes to PyPI on tag. Check the Actions run; if it fails, do NOT re-tag, fix forward with a patch release.
7. Announce in #releases with the changelog section.
