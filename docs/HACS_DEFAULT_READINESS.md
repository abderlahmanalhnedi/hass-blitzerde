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

### GitHub metadata

- [ ] Enable GitHub Issues for the repository.
- [ ] Add repository topics. Suggested topics:
  `home-assistant`, `homeassistant`, `hacs`, `custom-integration`,
  `traffic`, `speed-camera`, `germany`.
- [ ] Resolve repository-wide license provenance so the HACS license validator
  can identify a valid SPDX license **without retroactively licensing
  historical code whose original terms are unknown**.

### Publication gate

- [ ] Remove every HACS Action `ignore` entry.
- [ ] HACS Action passes with no errors and no ignored checks.
- [ ] Hassfest passes for the same commit.
- [ ] All project CI is green.
- [ ] Create a full semantic-versioned GitHub Release after those checks pass.
- [ ] Verify a clean HACS installation/update from that release.
- [ ] Submit the repository to `hacs/default`.
- [ ] After acceptance, change README installation wording/badge from custom
  repository to HACS Default.

## License provenance blocker

The repository contains lineage from the earlier community
`hass-blitzerde` project by Tim Niklas. The historical snapshot available in
this repository did not contain a license file. A modern maintainer cannot
safely grant a new license over that historical code merely to satisfy a
validator.

The HACS Action now validates the repository license and requires a detectable
SPDX identifier. Therefore the safe options are:

1. obtain verifiable licensing/provenance for the historical code; or
2. replace the remaining historical implementation with independently authored
   code whose licensing can be granted unambiguously.

Until one of those is complete, the workflow may keep the `license` ignore,
but the repository must **not** be submitted to HACS Default and must not claim
that the default-inclusion gate is complete.

See `THIRD_PARTY_NOTICES.md` for attribution and provenance notes.

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
