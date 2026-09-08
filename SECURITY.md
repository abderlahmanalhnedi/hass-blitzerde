# Security Policy

## Supported versions

Security fixes are applied to the latest version on the `main` branch. Users should keep the integration up to date through HACS and restart Home Assistant after updating.

## Reporting a vulnerability

Please **do not publish security-sensitive details, precise home coordinates, access tokens, or private diagnostics in a public issue**.

Preferred reporting order:

1. Use GitHub's private vulnerability reporting flow from the repository **Security** tab when it is available.
2. If private reporting is not available, contact the maintainer through the GitHub profile linked from this repository and keep the initial message limited to a short description until a private channel is established.

Include:

- affected integration version
- Home Assistant version
- installation method
- clear reproduction steps
- the smallest relevant, redacted logs
- expected security impact

## Data handling

This integration does not require a Blitzer.de account or Home Assistant credentials for the upstream map request. It sends only the geographic query needed to retrieve reports:

- **Area mode:** a bounding box around the configured center/radius
- **Route mode:** bounded, overlapping geographic queries along configured waypoints

Diagnostics redact configured area locations and route waypoints.

The upstream map endpoint is unofficial and undocumented, so users should treat it as an external third-party dependency.

## Scope

Examples that are security-relevant:

- leaking Home Assistant credentials or secrets
- exposing precise configured coordinates in diagnostics unexpectedly
- arbitrary code execution through integration data
- cross-site scripting in the bundled dashboard card
- unsafe static-file handling

Ordinary upstream downtime, missing cameras, inaccurate reports, or rate limiting are reliability issues rather than security vulnerabilities.
