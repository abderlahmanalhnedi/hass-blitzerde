# Home Assistant Core readiness

This document tracks the deliberate path from the full HACS edition to a
reviewable Home Assistant Core integration.

## Baseline

The custom integration is developed against current Home Assistant behavior and
is runtime-tested in CI with the Home Assistant 2026.9 test harness on Python
3.14.

The HACS edition is intentionally richer than an initial Core contribution. It
contains area and route modes, several platforms, diagnostics, an action,
events, a blueprint and a bundled Lovelace card.

## Why the first Core PR must be smaller

Home Assistant asks new integrations to start with the minimum useful scope and
a single platform. Diagnostics, custom actions, reconfiguration and other
non-essential features belong in follow-up pull requests.

The proposed first Core contribution is therefore:

```
homeassistant/components/blitzerde/
├── __init__.py
├── config_flow.py
├── const.py
├── coordinator.py
├── geo_location.py
├── manifest.json
├── quality_scale.yaml
├── strings.json
└── translations/
```

Initial functionality:

- UI setup
- one area/radius search
- cloud polling coordinator
- native Geo Location camera markers
- unique config entry
- connection test before saving
- unload support
- complete config-flow tests

Route mode, sensors, binary sensors, diagnostics, actions, Repairs and the
dashboard card remain in the HACS edition until follow-up Core PRs.

## Remaining Core blockers

### 1. External async client package

Home Assistant Core requires transparent dependencies. Network communication
must be moved into an independently licensed async Python package that is:

- available from an open source repository
- licensed with an OSI-approved license
- published to PyPI from public CI
- released with Git tags matching PyPI versions
- able to accept an injected aiohttp ClientSession

The current in-integration API client is intentionally kept isolated in
`api.py` so that extraction is mechanical once the package repository and
license are ready.

### 2. License provenance

Historical hass-blitzerde code did not include a license file. Before a Core
submission, code included in the minimal Core implementation must have clear
license provenance compatible with Home Assistant Core.

New clean-room client code should carry an explicit OSI-approved license from
its first commit.

### 3. Upstream endpoint status

The integration currently uses the map endpoint served by atudo/Blitzer.de.
The endpoint is undocumented. Before requesting Core inclusion, confirm that
third-party automated access is permitted and sufficiently stable for a
built-in integration.

### 4. Brands and official documentation

A Core contribution needs:

- brand assets through the Home Assistant brands repository
- official documentation in home-assistant.io
- installation, removal, update behavior and known-limitations documentation

## Quality strategy

The repository does not claim an official Home Assistant quality tier yet.
Instead, every Core-quality rule is treated as an engineering checklist and is
only marked complete when there is code and/or a test proving it.

Current strong points:

- config flow
- connection test before configure
- runtime_data
- coordinator
- unique IDs
- unloading
- diagnostics
- service action setup in async_setup
- explicit integration_type
- privacy-safe diagnostics
- Home Assistant runtime CI

The next quality target is full config/options-flow coverage, followed by
broad coordinator/entity coverage.
