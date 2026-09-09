# Provenance audit

Date: 2026-09-09

Purpose: determine whether adding an OSI-approved license to the current
`hass-blitzerde` source tree would incorrectly imply that historical Tim
Niklas code was being relicensed.

This is an engineering provenance audit, not legal advice.

## Historical baseline

The preserved historical snapshot inspected was:

`08eda41ff5585cfbaf27ee9127cf8df976e9be69`

That commit belongs to the original Tim Niklas history preserved in this
repository.

At that snapshot, GitHub content inspection found no:

- `LICENSE`
- `LICENSE.md`
- `COPYING`

The historical README also did not state an explicit software license.

## Files compared

The historical integration contained these implementation/metadata files:

- `__init__.py`
- `api.py`
- `binary_sensor.py`
- `config_flow.py`
- `const.py`
- `coordinator.py`
- `item_utils.py`
- `manifest.json`
- `sensor.py`
- German and English translation JSON

Each was compared with the current source tree.

## Literal-overlap result

The current implementation is substantially larger and structurally different.
The remaining exact matches that were not comments/blank lines were dominated
by standard framework or language expressions, for example:

- Home Assistant imports and entity base-class names
- `await coordinator.async_config_entry_first_refresh()`
- `response.raise_for_status()`
- `if user_input is not None:`
- `_attr_should_poll = False`
- standard Material Design icon identifiers
- JSON structure keys such as `title`, `name`, `sections`
- product labels such as `Mobile`, `Trailer`, `Anhänger`

No non-trivial block of historical business logic was found as verbatim
retained implementation in this audit.

Examples of measured old-line retention before excluding generic boilerplate:

| File | Approx. exact retained old lines |
| --- | ---: |
| `__init__.py` | 14 |
| `api.py` | 11 |
| `binary_sensor.py` | 17 |
| `config_flow.py` | 19 |
| `coordinator.py` | 19 |
| `item_utils.py` | 1 |
| `sensor.py` | 16 |

Those counts include imports, declarations and framework idioms; they are not a
claim that those lines are independently copyrightable.

## Current licensing decision

The project therefore licenses the **current source tree from the LICENSE
introduction commit forward** under MIT, while explicitly leaving historical
commits under whatever terms applied to those commits at the time.

This is intentionally different from saying that the original Tim Niklas
repository was MIT-licensed. The project makes no such claim.

Third-party MIT material and reference-derived work remain attributed in
`THIRD_PARTY_NOTICES.md`.
