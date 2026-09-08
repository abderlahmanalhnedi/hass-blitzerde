# Home Assistant Core readiness

This document tracks the work required to move the integration from a HACS
custom integration toward an official Home Assistant Core integration without
reducing the feature set of the HACS edition.

## Strategy

The repository remains the full-featured edition. A first Core contribution
should be intentionally smaller and follow Home Assistant's new-integration
review guidance:

1. external async client dependency
2. UI config flow
3. coordinator/runtime setup
4. one initial platform
5. full Bronze quality-scale compliance
6. focused tests and official documentation

Additional platforms and advanced features can follow in later pull requests.

## Phase 1 — in progress

- [x] Inject Home Assistant's shared aiohttp session into the API client.
- [x] Remove Home Assistant imports from the low-level HTTP client.
- [x] Classify the integration as a cloud service.
- [x] Add a Home Assistant-aware pytest harness.
- [x] Add config-flow happy-path, failure-recovery, duplicate and route tests.
- [x] Track Bronze rules in `quality_scale.yaml`.
- [ ] Reach verified 100% config/options-flow coverage.
- [ ] Add setup/unload/coordinator/entity tests.
- [ ] Add explicit config-flow `data_description` strings.

## Phase 2 — external client library

The code in `custom_components/blitzerde/api.py` is now intentionally close
to a standalone library: it depends on aiohttp and an injected ClientSession,
not on Home Assistant.

Before a Core pull request it should move to a dedicated public package and be
published to PyPI from GitHub Actions using Trusted Publishing.

Required properties:

- asynchronous API
- injected `aiohttp.ClientSession`
- semantically versioned releases and matching Git tags
- public source repository
- explicit Apache-2.0-compatible license
- PyPI license metadata matching the repository license
- unit tests for timeout, invalid JSON, HTTP errors, 429/Retry-After, clusters,
  deduplication and radius filtering

The current repository cannot safely assign a new license to historical code
whose original licensing was unclear. The external client should therefore be
implemented as a clean, independently licensed package.

## Phase 3 — Core-minimal integration

The first proposed Core version should avoid sending the entire HACS feature
set in one review. The proposed initial platform is `geo_location`, because a
speed-camera report maps naturally to a geographic event.

Keep in the first Core PR:

- config flow
- shared coordinator
- external PyPI client
- area/radius search
- geo-location entities
- safe polling and availability behavior

Defer to follow-up PRs:

- route/corridor mode
- aggregate and operational sensors
- binary sensor slots
- custom refresh action
- custom new-camera event
- diagnostics
- bundled Lovelace card
- blueprints

The HACS edition does not need to lose any of those features.

## External-service acceptance risk

The largest non-code risk is the upstream map endpoint. It is not documented as
a public third-party API. Before asking Home Assistant Core to accept the
integration, we should obtain or identify clear evidence that automated
third-party use of the endpoint is permitted and stable enough for a built-in
integration.

If that cannot be established, the project can still remain a strong HACS
integration even after the technical Core-readiness work is complete.

## Remaining Bronze blockers

At the time this document was added:

- official Home Assistant brand assets
- external transparent PyPI dependency
- verified 100% config/options-flow coverage
- config-flow field descriptions
- explicit removal documentation

The current status is kept machine-readable in
`custom_components/blitzerde/quality_scale.yaml`.
