# HACS Default readiness

This document is the release gate for publishing `abderlahmanalhnedi/hass-blitzerde`
as a default HACS integration rather than requiring users to add a custom
repository.

## Current checklist

### Repository and integration

- [x] Public GitHub repository.
- [x] Repository description is present.
- [x] Single integration below `custom_components/blitzerde`.
- [x] Root `hacs.json`.
- [x] Integration `manifest.json` includes domain, name, version,
  documentation, issue tracker and code owners.
- [x] README contains installation and usage documentation.
- [x] Hassfest workflow.
- [x] HACS Action workflow.
- [x] Home Assistant runtime tests, quality checks and CodeQL.
- [x] Local Home Assistant brand assets.
- [x] Current-tree license provenance audited and documented.
- [x] GitHub detects the default-branch license as SPDX `MIT`.
- [x] HACS license validator passes.

### GitHub metadata

- [x] GitHub Issues enabled.
- [x] Repository topics configured.

### Publication gate

- [x] Remove every HACS Action `ignore` entry.
- [x] HACS Action passes with no errors and no ignored checks on `main`.
- [x] Hassfest passes on the same release commit.
- [x] Home Assistant tests, code quality and CodeQL pass on the release commit.
- [x] Create semantic-versioned GitHub Release `v1.4.3`.
- [x] Publish installable release asset `blitzerde-v1.4.3.zip`.
- [ ] Verify a clean HACS installation and update from `v1.4.3` on a real Home
  Assistant instance.
- [ ] Create a maintainer fork of `hacs/default` under
  `abderlahmanalhnedi/default`.
- [ ] Submit the repository to `hacs/default`.
- [ ] After acceptance, change README installation wording/badge from custom
  repository to HACS Default.

Submission details and exact upstream patch:
[HACS_DEFAULT_SUBMISSION.md](HACS_DEFAULT_SUBMISSION.md).

## Validation evidence for v1.4.3

Release commit: `9874a91ba8782c885911b20ccfc079684ffcd27d`.

- Release:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/releases/tag/v1.4.3
- Release asset:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/releases/download/v1.4.3/blitzerde-v1.4.3.zip
- HACS Action without ignores:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861502
- Hassfest:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861714
- Home Assistant tests:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861584
- Code quality:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861963
- CodeQL:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861511
- Release workflow:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861614

The same validation suite also passes on current `main` after the README
screenshot fixes. The latest HACS and Hassfest runs are:

- HACS Action:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34363691818
- Hassfest:
  https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34363691732

## Release automation

The release workflow can be started manually or by changing
`.github/release-request.json`. Before publishing it independently:

1. confirms the normal HACS workflow contains no ignored checks;
2. runs full HACS validation again;
3. verifies Issues, Topics and SPDX license metadata;
4. verifies manifest version and local brand assets;
5. refuses duplicate tags/releases;
6. runs the complete Home Assistant test suite;
7. packages the integration and creates the tag and GitHub Release.

## License provenance

The repository preserves historical commits from the earlier Tim Niklas
`hass-blitzerde` project. The current-tree licensing scope and provenance are
documented in:

- `LICENSE_SCOPE.md`
- `docs/PROVENANCE_AUDIT.md`
- `THIRD_PARTY_NOTICES.md`

The root MIT license applies from its introduction commit forward and does not
retroactively alter the status of historical commits.

## Brand assets

The local icon is original neutral artwork created for this integration. It
does not reproduce the Blitzer.de corporate logo and does not use Home
Assistant branding.

The source of truth is:

- `custom_components/blitzerde/brand/icon.png` — 256 × 256
- `custom_components/blitzerde/brand/icon@2x.png` — 512 × 512
