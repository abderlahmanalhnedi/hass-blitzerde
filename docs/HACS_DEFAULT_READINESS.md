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

- [ ] Enable GitHub Issues for the repository.
- [ ] Add repository topics. Suggested topics:
  `home-assistant`, `homeassistant`, `hacs`, `custom-integration`,
  `traffic`, `speed-camera`, `germany`.

These are the only HACS repository checks still ignored. They are repository
administration settings rather than source-controlled files, and the currently
connected GitHub tool does not expose a repository-settings mutation for them.

### Publication gate

- [ ] Remove every HACS Action `ignore` entry after Issues and Topics are enabled.
- [ ] HACS Action passes with no errors and no ignored checks.
- [x] Hassfest currently passes on `main`.
- [x] Current project CI passes on `main`.
- [ ] Create a full semantic-versioned GitHub Release after the no-ignore HACS
  check passes.
- [ ] Verify a clean HACS installation/update from that release.
- [ ] Submit the repository to `hacs/default`.
- [ ] After acceptance, change README installation wording/badge from custom
  repository to HACS Default.

## Remaining repository-admin actions

1. Enable **Issues** for `abderlahmanalhnedi/hass-blitzerde`.
2. Add the repository topics listed above.
3. Remove `ignore: "topics issues"` from
   `.github/workflows/action.yaml`.
4. Require the resulting HACS Action to pass without ignores.
5. Run the release workflow for the manifest version and verify the generated
   GitHub Release/ZIP.
6. Submit the repository to `hacs/default`.

Steps 3–6 are source/release operations and can be completed autonomously once
steps 1–2 are present in GitHub repository metadata.

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
