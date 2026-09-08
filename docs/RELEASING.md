# Releasing

Releases are intentionally created through the **Create release** GitHub Actions workflow so the version, tag, and downloadable package stay aligned.

## Before releasing

1. Merge the release changes to `main`.
2. Confirm all required CI checks are green:
   - Hassfest
   - HACS validation
   - Code quality/unit tests
   - CodeQL
3. Confirm `custom_components/blitzerde/manifest.json` contains the intended version.
4. Move the release notes in `CHANGELOG.md` out of an unreleased state when applicable.

## Create the release

1. Open **Actions → Create release → Run workflow**.
2. Enter the version without a `v`, for example `1.3.0`.
3. The workflow:
   - checks out `main`
   - verifies the manifest version matches
   - reruns unit tests
   - packages `custom_components/blitzerde`
   - creates tag `v<version>`
   - uploads `blitzerde-v<version>.zip`
   - creates GitHub release notes

If the version does not match the manifest or a tag already exists, the workflow fails instead of publishing an inconsistent release.

## After releasing

- Verify the release and ZIP are visible on GitHub.
- Verify HACS can see the version.
- Perform a clean HACS upgrade on a real Home Assistant instance.
- Add any runtime-only findings to the changelog and issue tracker.
