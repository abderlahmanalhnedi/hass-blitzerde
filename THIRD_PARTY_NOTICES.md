# Third-party notices

## somansch/blitzer

The Home Assistant integration at `https://github.com/somansch/blitzer` was
reviewed as a working reference while improving this project. Its handling of
dynamic geolocation entities, new-report events, configurable polling,
manual refresh, waypoint route search and bundled dashboard UX informed the
design of equivalent features implemented here. The implementation in this
repository is independently adapted to its own runtime-data architecture,
bounded query budget and card design.

That project is distributed under the MIT License:

> MIT License
>
> Copyright (c) 2026 somansch
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

The archive/report-form and semantic control-kind taxonomy work was informed by
reviewing behavior and upstream type mapping documented by
`somansch/blitzer`. The implementation in this repository is adapted to this
integration's runtime-data, filtering, migration, testing, multilingual UI and
privacy architecture.

## Original hass-blitzerde history

This repository preserves Git history from the earlier community
`hass-blitzerde` project by Tim Niklas.

Historical snapshots inspected in that history did not contain a software
license file. The current root MIT license is therefore deliberately scoped to
the current source tree beginning with the commit that introduces the license
and later contributions. It does **not** retroactively relicense old historical
commits.

See `LICENSE_SCOPE.md` and `docs/PROVENANCE_AUDIT.md` for the exact
provenance policy and audit evidence.
