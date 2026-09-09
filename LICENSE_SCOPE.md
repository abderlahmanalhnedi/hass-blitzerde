# License scope and historical provenance

The root `LICENSE` applies to the **current source tree beginning with the
commit that introduces that LICENSE and to later contributions made under it**.

It does **not** retroactively change the licensing status of historical commits
that remain reachable through Git history.

## Historical lineage

This repository preserves Git history from the earlier community
`timniklas/hass-blitzerde` project. Historical snapshots inspected in that
history did not contain `LICENSE`, `LICENSE.md`, or `COPYING` files. Nothing
in the current MIT license grants or claims rights over an old commit merely
because that commit remains in repository history.

The current implementation was substantially reworked and extended. A
literal-overlap audit against the last preserved Tim Niklas snapshot found that
remaining verbatim matches in the current files are overwhelmingly generic
Home Assistant/Python/API boilerplate, metadata keys, imports, and short
functional idioms. The audit is recorded in
[`docs/PROVENANCE_AUDIT.md`](docs/PROVENANCE_AUDIT.md).

## Third-party material

Material informed by or derived from other explicitly licensed projects remains
subject to the notices in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
In particular, `somansch/blitzer` is MIT-licensed and its attribution is
preserved there.

This document exists to prevent the root LICENSE from being read as an attempt
to relicense old repository history.
