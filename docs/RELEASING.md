# Releasing

Releases are intentionally created through the **Create release** GitHub Actions
workflow so the manifest version, tag and downloadable package stay aligned.

For HACS Default publication, a release is the **last** step, not a way to make
an unready repository look publishable.

## Before releasing

1. Merge the release changes to `main`.
2. Confirm all project CI is green:
   - Hassfest
   - HACS validation
   - Code quality/unit tests
   - Home Assistant runtime tests
   - CodeQL
3. Confirm the HACS Action contains **no ignored checks**.
4. Confirm the repository metadata required by HACS is complete:
   - GitHub Issues enabled
   - repository topics present
   - repository license has a valid SPDX ID backed by clear provenance
5. Confirm `custom_components/blitzerde/manifest.json` contains the intended version.
6. Confirm local brand assets exist under `custom_components/blitzerde/brand/`.
7. Move the release notes in `CHANGELOG.md` out of an unreleased state when applicable.

The provenance requirement is deliberate. Do not add a repository-wide license
to historical code merely to make HACS validation green. See
[HACS Default readiness](HACS_DEFAULT_READINESS.md) and
[Third-party notices](../THIRD_PARTY_NOTICES.md).

## Create the release

1. Open **Actions → Create release → Run workflow**.
2. Enter the version without a `v`, for example `1.4.0`.
3. The workflow:
   - checks out `main`
   - refuses to release while the HACS workflow still contains ignored checks
   - verifies GitHub Issues, topics and SPDX license metadata
   - verifies the manifest version matches
   - reruns the test suite
   - packages `custom_components/blitzerde`
   - creates tag `v<version>`
   - uploads `blitzerde-v<version>.zip`
   - creates the GitHub Release

If any release gate fails, fix the repository and rerun the workflow. Do not
bypass the check with a hand-created tag or release.

## After releasing

- Verify the GitHub Release and ZIP are visible.
- Verify HACS can see the release version.
- Perform a clean HACS install/upgrade on a real Home Assistant instance.
- Confirm Hassfest and HACS validation remain green for the released commit.
- If preparing HACS Default inclusion, submit the repository to `hacs/default`
  only after the new release exists.
- Add runtime-only findings to the changelog and issue tracker.
