# HACS Default readiness

This document is the release gate for publishing `abderlahmanalhnedi/hass-blitzerde`
as a default HACS integration rather than requiring users to add a custom
repository.

The goal is **not** to weaken validation until the repository passes. HACS
Default requires the HACS Action to complete without ignored checks, followed
by a real GitHub Release.

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
- [x] Local Home Assistant brand assets under
  `custom_components/blitzerde/brand/`.
- [x] Current-tree license provenance audited and documented.
- [x] Root MIT license added without retroactively relicensing historical
  commits.
- [x] GitHub detects the default-branch license as SPDX `MIT`.
- [x] HACS license validator passes without a license ignore.

### GitHub metadata

- [x] GitHub Issues enabled.
- [x] Repository topics added:
  `home-assistant`, `homeassistant`, `hacs`, `custom-integration`,
  `traffic`, `speed-cameras`, `germany`.

### Publication gate

- [x] Remove every HACS Action `ignore` entry.
- [ ] HACS Action passes with no errors and no ignored checks on the
  no-ignore readiness PR and then on `main`.
- [x] Hassfest currently passes on `main`.
- [x] Current project CI passes on `main`.
- [ ] Create a full semantic-versioned GitHub Release after the no-ignore HACS
  check passes.
- [ ] Verify a clean HACS installation/update from that release.
- [ ] Submit the repository to `hacs/default`.
- [ ] After acceptance, change README installation wording/badge from custom
  repository to HACS Default.

## Release automation

The release workflow can be started manually or by merging a change to
`.github/release-request.json`. The file contains only the requested semantic
version, for example:

```json
{
  "version": "1.4.0"
}
```

Before creating a tag or GitHub Release, the workflow independently:

1. confirms the normal HACS workflow contains no ignored checks;
2. runs the full HACS Action again;
3. verifies Issues, Topics and SPDX license metadata;
4. verifies the manifest version and local brand assets;
5. refuses duplicate tags/releases;
6. runs the complete Home Assistant test suite.

This makes a release-request PR a safe auditable trigger rather than requiring
a manual Actions button.

## License provenance

The repository preserves historical commits from the earlier Tim Niklas
`hass-blitzerde` project. Inspected historical snapshots contained no explicit
license file.

The current tree has since been substantially reworked. A literal-overlap audit
found only generic framework/language idioms, metadata and short functional
expressions as exact matches in the current implementation; no non-trivial
historical business-logic block was found verbatim.

The root MIT license therefore applies from its introduction commit forward.
It does not retroactively alter the status of historical commits.

See:

- `LICENSE_SCOPE.md`
- `docs/PROVENANCE_AUDIT.md`
- `THIRD_PARTY_NOTICES.md`

GitHub reports the repository license as `MIT` with SPDX ID `MIT`, and the
HACS license validator has passed with the license check enabled.

## Brand assets

The local icon is original neutral artwork created for this integration. It
does not copy the Blitzer.de trademark/logo and does not use Home Assistant
branding. This avoids implying endorsement by either project.

Home Assistant 2026.3+ supports brand images directly inside a custom
integration. The source of truth is the PNG pair in
`custom_components/blitzerde/brand/`:

- `icon.png` — 256 × 256
- `icon@2x.png` — 512 × 512

## Release policy

The release workflow must remain stricter than development CI:

1. version in `manifest.json` matches the requested release;
2. full test suite passes;
3. HACS Default readiness has no ignored validation checks;
4. only then create the tag, release and installable ZIP.

A tag without a GitHub Release is not sufficient for the HACS Default
submission gate.
