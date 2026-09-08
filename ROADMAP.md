# Roadmap

The roadmap prioritizes features that improve daily usefulness, trust, and Home Assistant-native behavior.

## Next

### Reliability and onboarding

- Continue expanding Home Assistant runtime coverage beyond config-flow and Repairs paths.
- Add a setup-success screen with direct links to the device, map, and dashboard-card instructions.
- ✅ Add Home Assistant-aware config/options-flow tests with enforced 100% coverage.
- ✅ Add coordinator and extraction-ready API client tests.
- Establish tagged GitHub releases once runtime validation is complete.

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
- Add official Home Assistant brand assets through `home-assistant/brands`.
- Prepare a deliberately minimal first Core contribution based on area search + `geo_location`.
- Confirm that automated third-party use of the upstream map endpoint is acceptable before submitting to Core.

## Exploring

- Hazards/traffic reports if the upstream data can be consumed reliably without making the integration noisy.
- Dynamic search centered on a Home Assistant person/device tracker.
- Better route geometry using a routing provider only if it can be implemented without requiring an unsafe or expensive default external dependency.

## Explicitly not planned

- Any feature that encourages interacting with Home Assistant while driving.
- Automatic reporting/submission of cameras to third-party services.
- Features that require storing Home Assistant credentials outside Home Assistant.
- High-frequency polling that risks abusing the upstream service.
