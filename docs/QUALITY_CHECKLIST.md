# Home Assistant quality checklist

This is an internal readiness checklist. It is deliberately stricter than the
HACS validation result and does **not** claim an official Home Assistant quality
tier.

## Bronze target

- [x] Action setup happens in `async_setup`
- [x] Polling interval is explicit and configurable
- [ ] Brand assets accepted in home-assistant/brands
- [x] Shared behavior is split into common modules
- [ ] 100% config + options flow coverage
- [x] UI config flow
- [ ] External dependency transparency (PyPI client extraction)
- [x] Actions documented
- [x] High-level integration documentation
- [x] Step-by-step HACS installation documentation
- [x] Removal/troubleshooting guidance
- [x] Entity unique IDs
- [x] `has_entity_name = True`
- [x] `ConfigEntry.runtime_data`
- [x] Connection test before configuration is saved
- [x] First refresh verifies runtime connectivity
- [x] Duplicate config entries are blocked

## Silver preparation

- [x] Config entry unloading
- [x] Entity availability follows coordinator state
- [x] Integration owner/codeowner declared
- [x] Platform parallel-update behavior declared
- [ ] >95% integration test coverage

## Gold preparation already present in HACS edition

- [x] Device grouping
- [x] Diagnostics
- [x] Troubleshooting documentation
- [x] Known limitations documentation
- [x] Repairs for repeated upstream failure
- [x] Privacy redaction for location and route waypoints

## Core submission gates

- [ ] Cleanly licensed external async client
- [ ] Public PyPI release from CI with matching Git tag
- [ ] Confirmed acceptable use of upstream endpoint
- [ ] Home Assistant brands PR
- [ ] home-assistant.io documentation PR
- [ ] Minimal one-platform Core patch prepared
