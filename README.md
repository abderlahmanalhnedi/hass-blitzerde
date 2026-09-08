# Blitzer.de for Home Assistant 🚗⚡

[![Hassfest](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/hassfest.yaml)
[![HACS validation](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/action.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/action.yaml)
[![Python quality](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/quality.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/quality.yaml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.12%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-41BDF5)](https://hacs.xyz/)

A modern, resilient Home Assistant custom integration for nearby speed-camera reports from the map data used by Blitzer.de.

> [!IMPORTANT]
> This project is unofficial. It is not endorsed, operated, or supported by Blitzer.de. The upstream map endpoint is undocumented and may change without notice.

## Highlights

- **Home Assistant 2026-ready architecture** using \`ConfigEntry.runtime_data\` and \`DataUpdateCoordinator\`
- **UI configuration and options flow** — no YAML required
- Mobile, trailer, and fixed camera types
- Configurable map center and **radius in meters**
- Optional city regex filter
- Optional confirmed-only filter
- Cameras sorted **nearest first**
- Distance to every result, plus a dedicated **Nearest speed camera** sensor
- Native **Geo Location** entities for the Home Assistant map
- `blitzerde_new_camera` event for genuinely new reports after startup
- Configurable polling interval, including **manual-only** mode
- `blitzerde.refresh` action for on-demand updates and response data
- Up to 50 binary/geolocation camera slots
- Robust timeout, malformed-response, HTTP, and rate-limit handling
- Automatic retry/backoff through Home Assistant's coordinator
- Privacy-conscious downloadable diagnostics
- German and English configuration UI
- HACS and Hassfest validation workflows

## Why this fork exists

The repository was modernized after a broken coordinator change made the integration unloadable. The current code removes that broken duplicate coordinator implementation, restores a single API/coordinator path, and updates the integration to current Home Assistant patterns.

The original community project was created by **Tim Niklas**. This repository contains a substantially modernized maintenance branch by **Abderlahman Al Hnedi**.

## Entities

For every configured area, the integration creates one Home Assistant device and the following entities:

| Entity | Purpose |
| --- | --- |
| **Detected speed cameras** | Number of currently exposed camera slots. Attributes include \`total_detected\`, \`entity_limit\`, and a per-city summary. |
| **Nearest speed camera** | Distance in km to the nearest current report, with camera/address attributes. |
| **Latest speed camera** | Backend ID of the latest-looking upstream report, with camera/address attributes. |
| **Speed camera 1 … N** | Safety binary sensors. Slot 1 is the nearest report, slot 2 the next-nearest, and so on. |
| **Geo Location markers** | One dynamic map marker per exposed camera, automatically added, updated, and removed as reports change. |

Each active camera slot exposes useful attributes such as:

- \`backend\`
- \`vmax\`
- \`counter\`
- \`city\`
- \`street\`
- \`zip_code\`
- \`latitude\` / \`longitude\`
- \`distance_km\`
- \`description\` when provided upstream
- \`entity_picture\`

## Installation

### HACS — recommended

This repository can be installed as a **custom HACS repository**:

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add:

   \`https://github.com/abderlahmanalhnedi/hass-blitzerde\`

4. Select **Integration** as the category.
5. Search for **Blitzer.de** and download it.
6. Restart Home Assistant when HACS asks you to.
7. Go to **Settings → Devices & services → Add integration → Blitzer.de**.

### Manual

Copy the directory:

\`custom_components/blitzerde\`

into:

\`/config/custom_components/blitzerde\`

Then restart Home Assistant and add **Blitzer.de** from **Settings → Devices & services**.

## Configuration

During setup you choose:

- **Display name** — for example \`Dresden\` or \`Commute\`
- **Area** — center point plus radius
- **Camera types** — mobile, trailer, fixed
- **Number of camera slots** — 1 to 50, default 9
- **City filter** — regular expression, default \`.*\`
- **Confirmed only** — enabled by default
- **Update interval** — minutes between polls; set to `0` for manual-only refreshes

The area radius returned by Home Assistant's location selector is interpreted in **meters**. Results from the rectangular upstream API query are then filtered again to the selected circular radius.

### City filter examples

| Goal | Regex |
| --- | --- |
| Everything | \`.*\` |
| Dresden only | \`^Dresden$\` |
| Dresden or Radebeul | \`^(Dresden|Radebeul)$\` |
| Cities beginning with \`Dres\` | \`^Dres.*\` |

Invalid regular expressions are rejected directly in the UI before the configuration is saved.

## Home Assistant map

The integration now exposes current reports as native `geo_location` entities. Add Home Assistant's built-in **Map** card and select the Blitzer.de source for the configured area. Markers use the upstream coordinates, show their distance from the configured center, and carry useful attributes such as street, city, speed limit, report ID, camera type, and a short summary.

Geo Location entities are dynamic: when a report disappears from the current result set, its marker is removed instead of being left behind as an unavailable ghost.

## New-camera event

After the first successful fetch, every camera ID that appears in a later poll fires:

`blitzerde_new_camera`

The first fetch after startup is intentionally treated as the baseline so Home Assistant does not send a burst of "new" notifications after every restart.

Example automation trigger:

```yaml
triggers:
  - trigger: event
    event_type: blitzerde_new_camera
actions:
  - action: notify.mobile_app_YOUR_PHONE
    data:
      title: "New speed camera"
      message: "{{ trigger.event.data.summary }} · {{ trigger.event.data.distance_km }} km"
```

The event payload includes `config_entry_id`, `area`, `id`, `camera_type`, `summary`, address fields, coordinates, `distance_km`, `vmax`, and other available camera metadata.

## Polling and manual refresh

The update interval is configurable per entry in minutes. The default is one minute. Set it to `0` if you want the integration to refresh only when an automation requests it.

Use the Home Assistant action:

`blitzerde.refresh`

Select the integration entry in the action UI. The action refreshes immediately and can return the current camera list to automations that request response data.

## Example automation

Choose one of the generated \`Speed camera N\` binary sensors and use it as the trigger:

\`\`\`yaml
alias: Nearby speed camera appeared
triggers:
  - trigger: state
    entity_id: binary_sensor.YOUR_SPEED_CAMERA_1
    from: "off"
    to: "on"
actions:
  - action: notify.mobile_app_YOUR_PHONE
    data:
      title: "Speed camera nearby"
      message: >-
        {{ state_attr('binary_sensor.YOUR_SPEED_CAMERA_1', 'street') }} ·
        {{ state_attr('binary_sensor.YOUR_SPEED_CAMERA_1', 'distance_km') }} km ·
        {{ state_attr('binary_sensor.YOUR_SPEED_CAMERA_1', 'vmax') }} km/h
mode: single
\`\`\`

## Diagnostics

If something stops working:

1. Go to **Settings → Devices & services → Blitzer.de**.
2. Open the integration entry menu.
3. Download **Diagnostics**.
4. Attach the diagnostics file to a GitHub issue.

The diagnostics implementation intentionally redacts the configured map location.

## Troubleshooting

### Integration does not appear after HACS installation

Restart Home Assistant after downloading the integration. If it still does not appear, clear/reload the browser frontend and verify that this directory exists:

\`/config/custom_components/blitzerde\`

### Setup says it cannot connect

The config flow tests the upstream endpoint before saving. A failure can mean:

- temporary network/DNS problems
- the upstream service is down
- the upstream endpoint changed
- the service rate-limited requests

Home Assistant will also retry runtime failures automatically. HTTP 429 responses use the upstream \`Retry-After\` signal when available.

### No cameras are shown

Check these first:

- increase the selected radius
- temporarily use the city regex \`.*\`
- enable more camera types
- temporarily disable **Confirmed only**

An empty but valid upstream result is not treated as a connection error.

## Data and privacy

The integration sends the selected map bounding box to the upstream map service in order to retrieve nearby reports. No Home Assistant credentials are sent. The integration has no authentication token of its own.

Because the endpoint is unofficial and undocumented, review the relevant service terms and local rules before relying on it.

## Development

The repository validates changes with:

- Home Assistant **Hassfest**
- **HACS Action**
- Python byte-code compilation
- **Ruff** static checks

Pull requests are welcome. For bugs, include your Home Assistant version, integration version, relevant log lines, and the redacted diagnostics file when possible.

The actively maintained [somansch/blitzer](https://github.com/somansch/blitzer) project was reviewed as a working reference for map entities, event-driven notifications, manual refresh and polling controls. See `THIRD_PARTY_NOTICES.md` for attribution and license details.

## Disclaimer

Speed-camera information can be incomplete, delayed, inaccurate, or unavailable. Do not use this integration in a way that distracts you while driving. Always follow applicable road-safety laws and local regulations.
