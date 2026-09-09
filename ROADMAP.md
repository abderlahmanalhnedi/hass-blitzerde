# Roadmap

The roadmap prioritizes features that improve daily usefulness, trust, and Home Assistant-native behavior.

## Next

### Distribution and HACS Default

- ✅ Add HACS and Hassfest validation workflows.
- ✅ Add a release workflow that packages only the integration.
- ✅ Add a dedicated HACS Default readiness gate and provenance policy.
- ✅ Add local Home Assistant brand assets for the custom integration.
- Enable GitHub Issues and add repository topics required by HACS.
- Resolve repository-wide license provenance without assigning a new license to
  historical code whose original terms are unclear.
- Remove every HACS Action `ignore` and require the unmodified validator to pass.
- Publish the first full semantic-versioned GitHub Release only after the
  no-ignore HACS gate and all project CI are green.
- Verify a clean HACS install/update from the release.
- Submit `abderlahmanalhnedi/hass-blitzerde` to `hacs/default`.
- After acceptance, update the README badge/install instructions to HACS Default.

Detailed status: [docs/HACS_DEFAULT_READINESS.md](docs/HACS_DEFAULT_READINESS.md).

### Reliability and onboarding

- Continue expanding Home Assistant runtime coverage beyond config-flow and Repairs paths.
- Add a setup-success screen with direct links to the device, map, and dashboard-card instructions.
- ✅ Add Home Assistant-aware config/options-flow tests with enforced 100% coverage.
- ✅ Add coordinator and extraction-ready API client tests.
- Establish tagged GitHub releases once HACS Default release gates are satisfied.

### Notifications

- Expand the shipped notification blueprint with optional:
  - person/device-tracker presence conditions
  - quiet hours
  - camera-type filtering
- Add a second route-focused blueprint if it provides behavior that cannot be expressed cleanly through the existing distance/area filter

### Dashboard

- Add optional grouping by camera type.
- Add user-selectable sort order: nearest / newest / speed limit.
- Add configurable new-report highlighting window directly in the card editor.
- Improve keyboard accessibility and screen-reader labels.

### Home Assistant Core readiness

- ✅ Decouple the low-level API client from Home Assistant and inject the shared aiohttp session.
- ✅ Add a current Home Assistant 2026.9 runtime test harness on Python 3.14.
- ✅ Add Core-style source strings and field descriptions.
- ✅ Track Bronze requirements in `quality_scale.yaml`.
- Extract the HTTP client into a separately licensed public PyPI package.
- Keep local custom-integration branding separate from any later Core branding submission.
- Prepare a deliberately minimal first Core contribution based on area search + `geo_location`.
- Confirm that automated third-party use of the upstream map endpoint is acceptable before submitting to Core.

## Exploring

- Drive Mode with direction-aware alerts and route-relative confidence.
- Multi-provider traffic intelligence behind a provider-neutral internal model.
- Cache/stale-data UX and richer upstream health telemetry.
- Dynamic search centered on a Home Assistant person/device tracker.
- Better route geometry using a routing provider only if it can be implemented without requiring an unsafe or expensive default external dependency.

## Explicitly not planned

- Any feature that encourages interacting with Home Assistant while driving.
- Automatic reporting/submission of cameras to third-party services.
- Features that require storing Home Assistant credentials outside Home Assistant.
- High-frequency polling that risks abusing the upstream service.
