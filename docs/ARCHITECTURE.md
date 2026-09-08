# Architecture

## Design goals

Blitzer.de is intentionally structured as a small Home Assistant-native integration with a hardened boundary around an undocumented external API.

```
Config Flow / Options
        │
        ▼
ConfigEntry.runtime_data
        │
        ▼
BlitzerdeCoordinator ──────► BlitzerdeAPI ──────► upstream map endpoint
        │
        ├── Sensor entities
        ├── Binary sensor entities
        ├── Geo Location entities
        ├── blitzerde_new_camera event
        ├── blitzerde.refresh action
        └── Bundled Lovelace card
```

## API boundary

`api.py` owns HTTP behavior:

- shared Home Assistant aiohttp session
- timeout handling
- HTTP error mapping
- rate-limit backoff
- JSON validation
- cluster resolution with bounded recursion
- circular radius filtering
- deduplication

External payloads must never be trusted to have stable types.

## Coordinator

`coordinator.py` owns one configured area or route:

- enabled report types
- area or route query
- route query concurrency/budget
- city regex filter
- confirmed-only filter
- ignored camera IDs
- report freshness
- sorting
- operational health metadata

The coordinator is the single runtime-data source used by platforms.

## Entity model

- **Detected speed cameras**: aggregate/current count and discovery metadata
- **Nearest speed camera**: nearest distance
- **Latest speed camera**: latest-looking upstream report ID
- **Last successful update**: timestamp telemetry
- **Upstream service**: connectivity health
- **Speed camera N**: stable binary sensor slots
- **Geo Location**: dynamic map markers for current reports

Legacy unique IDs are preserved where possible to avoid duplicate entities after upgrades.

## Frontend

The dashboard card is bundled under `custom_components/blitzerde/frontend` and registered by `bundle.py`.

The card discovers integration entities through stable metadata rather than hard-coded entity IDs, allowing users to rename entities safely.

## Privacy

Diagnostics redact:

- area location
- route waypoints

The integration does not require an upstream account token. Only geographic query data required for report retrieval is sent to the external endpoint.

## Route safety budget

Route mode samples overlapping circles along waypoint segments and caps a refresh at 120 query centers. Concurrency is bounded. This prevents a badly configured route from turning into uncontrolled upstream traffic.
