# Roadmap

The roadmap prioritizes features that improve daily usefulness, trust, and Home Assistant-native behavior.

## Next

### Reliability and onboarding

- Add Home Assistant Repairs issues for repeated upstream failures.
- Add a setup-success screen with direct links to the device, map, and dashboard-card instructions.
- Add broader config-flow tests with Home Assistant's test helpers.
- Establish tagged GitHub releases once runtime validation is complete.

### Notifications

- Ship optional automation blueprints for:
  - new report within a configurable distance
  - route/corridor report alert
  - notify only when selected person/device tracker is away from home or travelling

### Dashboard

- Add optional grouping by camera type.
- Add user-selectable sort order: nearest / newest / speed limit.
- Add configurable new-report highlighting window directly in the card editor.
- Improve keyboard accessibility and screen-reader labels.

## Exploring

- Hazards/traffic reports if the upstream data can be consumed reliably without making the integration noisy.
- Dynamic search centered on a Home Assistant person/device tracker.
- Better route geometry using a routing provider only if it can be implemented without requiring an unsafe or expensive default external dependency.

## Explicitly not planned

- Any feature that encourages interacting with Home Assistant while driving.
- Automatic reporting/submission of cameras to third-party services.
- Features that require storing Home Assistant credentials outside Home Assistant.
- High-frequency polling that risks abusing the upstream service.
