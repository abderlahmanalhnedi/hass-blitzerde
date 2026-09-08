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

## Original hass-blitzerde lineage

This repository also contains code descended from the earlier community
`hass-blitzerde` project by Tim Niklas. The historical repository snapshot
available in this repository did not contain a license file. Nothing in this
notice changes or expands the rights granted by that original code.


The current archive/report-form and semantic control-kind taxonomy work was informed by reviewing the behavior and upstream type mapping documented by `somansch/blitzer`. The implementation in this repository is independently adapted to this integration's runtime-data, filtering, migration, testing, and multilingual UI architecture; the existing MIT attribution above remains applicable to reference-derived ideas and mappings.
