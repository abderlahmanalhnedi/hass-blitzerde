# Changelog

All notable user-facing changes are documented here.

## Unreleased

## 1.4.0 — 2026-09-09

### Added

- Archive reports as an explicit opt-in installation form, clearly marked as
  historical rather than live.
- Seventeen semantic control-kind filters independent of installation form,
  including speed, red light, section control, tunnel, distance, weight,
  height, lane, access and police-related control types.
- `control_kind`, `archived`, and raw `type_code` metadata on exposed
  control reports.
- Ten opt-in traffic-hazard types with production normalization, filtering,
  freshness handling, deduplication and safe upstream-shape handling.
- Independent traffic-hazard coordinator and `blitzerde.refresh_hazards`
  action with Area and Route support.
- Independent opt-in background polling for hazards, separate from control
  polling.
- Native hazard `geo_location` entities with dynamic marker lifecycle and
  `blitzerde_new_hazard` events.
- Traffic-hazard summary sensors for total hazards, nearest hazard and
  fresh/new hazard count.
- Dashboard-friendly hazard breakdown attributes by semantic hazard kind.
- Smart Drive Alerts blueprint with camera/hazard filtering, distance-aware
  urgency, quiet hours, optional TTS and English/German/Arabic UI.
- Traffic Digest blueprint for scheduled, zone-triggered, entity-triggered or
  on-demand summaries of current controls and hazards, with
  English/German/Arabic UI.
- Home Assistant Repairs warning after five consecutive upstream refresh
  failures, with automatic cleanup after recovery or entry removal.
- Original local Home Assistant brand assets for the custom integration.
- Evidence-based Home Assistant Core-readiness and HACS Default-readiness
  documentation.

### Changed

- Config-entry schema includes migration for archive and semantic control-kind
  configuration.
- Code-quality checks target Python 3.14 and lint tests as well as integration
  code.
- GitHub releases are gated by the full Home Assistant-aware pytest suite.
- Release publishing now independently re-validates HACS, repository metadata,
  SPDX license metadata, brand assets, manifest version and duplicate tags
  before creating a release.
- HACS validation now runs with **no ignored checks**.
- Repository Issues, Topics and SPDX-detectable MIT licensing are configured
  for HACS Default submission readiness.
- Home Assistant test CI verifies dependency health before running tests.

## 1.3.0

### Added

- Upstream connectivity health binary sensor
- Last successful update timestamp sensor
- Update duration and consecutive-failure telemetry
- Configurable **Counts as new for** window
- `new` and `age_minutes` report attributes
- New-report count on the aggregate sensor and dashboard card
- Camera ID ignore list for persistent false positives
- Automation-friendly **New speed cameras** sensor
- One-click mobile notification blueprint with distance and area/route filters
- Online/offline and last-update status in the Blitzer.de Radar card
- Unit tests for upstream timestamp freshness parsing
- CodeQL security scanning, Dependabot, CODEOWNERS and PR quality checklist
- Security, support, contribution, architecture and roadmap documentation

### Changed

- Diagnostics now include operational health metadata without exposing route/location details.
- Config-entry schema moves to version 8.
- Integration version moves to 1.3.0.

## 1.2.0

- Added Area vs Route/Corridor search.
- Added multi-step route waypoints, bounded route query budget and distance-to-route sorting.
- Added built-in responsive `custom:blitzerde-card` with visual editor.
- Added Arabic UI/card support.

## 1.1.0

- Added native Home Assistant Geo Location markers.
- Added `blitzerde_new_camera` event.
- Added configurable polling and manual-only mode.
- Added `blitzerde.refresh` action.
- Hardened irregular upstream `info` payload handling.

## 1.0.0

- Rebuilt the broken coordinator path.
- Migrated runtime state to `ConfigEntry.runtime_data`.
- Added resilient timeout/HTTP/rate-limit handling.
- Added nearest-camera distance and diagnostics.
- Modernized HACS, Hassfest and Python quality validation.
