# Traffic hazards architecture

Traffic hazards are intentionally modelled as a separate data half from speed-camera controls.

The upstream map endpoint has a bounded response size while traffic hazards can be much denser than controls. Mixing both families into one request would let a busy hazard layer crowd cameras out of the response. Their freshness also differs: a queue end can become stale within minutes while permanent roadworks can remain relevant for days.

## Supported semantic types

The integration currently models ten opt-in hazard families: queue/tailback end, accident, temporary roadwork, obstacle, slippery road, obstructed view, permanent roadwork, broken-down vehicle, closure, and police/traffic-centre report.

All hazard types default to disabled for future background polling so existing config entries preserve their previous camera-only behaviour.

## Normalization contract

`custom_components/blitzerde/hazards.py` is the canonical normalization layer for hazard POIs. Coordinator, map entity, notification and future Drive Mode code should consume this layer rather than reimplementing upstream quirks.

The model provides:

- semantic `hazard_kind` mapping from raw upstream type codes;
- safe handling of `info` values that may be a mapping, boolean, string or list;
- stable-looking public IDs extracted from backend IDs;
- reason/description fallback across known upstream shapes;
- automation-friendly summaries and MDI icons;
- independent city filtering and blacklist handling;
- freshness metadata (`new`, `age_minutes`);
- backend-ID deduplication preferring the nearest duplicate;
- stable nearest-first ordering even when malformed distance values arrive.

## On-demand runtime

`blitzerde.refresh_hazards` now performs an isolated hazard scan and returns response data directly to Home Assistant automations. It supports both area and route entries without changing or refreshing camera data.

For route entries the action reuses the existing bounded route sampler, limits concurrent upstream calls, recalculates shortest distance to the configured route, collapses duplicates by backend ID and sorts the final result nearest first.

The action accepts an optional `hazard_types` list and optional `count` limit. Older entries do not yet contain hazard configuration, so an explicit on-demand call without a type list scans all supported hazard kinds. Once a hazards mapping exists in an entry, that mapping becomes authoritative.

The response includes the entry ID, area name, search mode, count, and normalized hazard objects with ID, kind, summary, address, coordinates, distance and freshness metadata.

## Runtime target

The next persistent runtime slice should add independent control and hazard polling intervals while exposing hazards as their own Home Assistant map source, count/new-report sensors and `blitzerde_new_hazard` events. The on-demand runtime is intentionally isolated so those features can reuse it without coupling hazard cadence to camera cadence.

Future Drive Mode should reuse the same normalization contract so radius, route and moving-device searches remain behaviorally consistent.

## Privacy and compatibility

Hazard diagnostics must follow the same location-redaction policy as controls and routes. New options must remain migration-safe, and old entries must keep background hazards disabled unless a user explicitly enables them.
