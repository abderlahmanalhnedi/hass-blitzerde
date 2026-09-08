# Contributing

Thanks for helping improve Blitzer.de for Home Assistant.

## Development principles

Changes should be:

- useful to Home Assistant users, not feature-count padding
- resilient to malformed/undocumented upstream data
- privacy-conscious
- compatible with current Home Assistant config-entry patterns
- safe for existing entity unique IDs whenever possible
- available in German, English, and Arabic when user-facing text changes

## Pull request workflow

1. Branch from `main`.
2. Keep one coherent feature/fix per pull request.
3. Update tests for pure logic.
4. Update translations for user-facing changes.
5. Update README and CHANGELOG when behavior changes.
6. Confirm diagnostics do not expose newly introduced private data.

Required CI gates:

- Python compilation
- unit tests
- Ruff
- dashboard JavaScript syntax
- Hassfest
- HACS validation
- CodeQL for supported code paths

## Architecture

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before changing coordinator, config-flow, routing, or frontend registration behavior.

## Upstream API

The Blitzer.de/atudo endpoint used by this project is unofficial and undocumented. Never assume optional fields are present or consistently typed. Normalize and validate external data before exposing it to Home Assistant.

## Attribution

Some design ideas were informed by the MIT-licensed `somansch/blitzer` project. Keep `THIRD_PARTY_NOTICES.md` accurate when borrowing substantial ideas or code.
