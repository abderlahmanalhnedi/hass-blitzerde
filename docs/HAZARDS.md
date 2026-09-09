# Traffic hazards architecture

Traffic hazards are intentionally modelled as a separate data half from speed-camera controls.

The upstream map endpoint has a bounded response size while traffic hazards can be much denser than controls. Mixing both families into one request would let a busy hazard layer crowd cameras out of the response. Their freshness also differs: a queue end can become stale within minutes while permanent roadworks can remain relevant for days.

## Supported semantic types

The integration currently models ten opt-in hazard families: queue/tailback end, accident, temporary roadwork, obstacle, slippery road, obstructed view, permanent roadwork, broken-down vehicle, closure, and police/traffic-centre report.

All hazard types default to disabled so existing config entries preserve their previous camera-only behaviour.

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

## Runtime target

The next runtime slice should keep independent control and hazard polling intervals while exposing hazards as their own Home Assistant map source, count/new-report sensors, `blitzerde_new_hazard` events and a dedicated `blitzerde.refresh_hazards` action.

Route mode must apply the same route-distance logic to hazards without allowing hazard requests to consume the control request budget. Future Drive Mode should reuse the same normalization contract so radius, route and moving-device searches remain behaviorally consistent.

## Privacy and compatibility

Hazard diagnostics must follow the same location-redaction policy as controls and routes. New options must remain migration-safe, and old entries must keep hazards disabled unless a user explicitly enables them.
