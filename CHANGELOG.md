# Changelog

All notable user-facing changes are documented here.

## Unreleased

### Added

- Home Assistant Repairs warning after five consecutive upstream refresh failures
- Automatic Repairs cleanup after service recovery or config-entry removal
- English, German and Arabic Repairs text
- Evidence-based Home Assistant quality checklist

### Changed

- Code-quality checks now target Python 3.14 and lint tests as well as integration code
- GitHub releases are gated by the full Home Assistant-aware pytest suite
- Home Assistant test CI now verifies dependency health before running tests

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
