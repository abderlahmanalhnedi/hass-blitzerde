<div align="center">

[🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch)

<a id="english"></a>

# 🚗⚡ Blitzer.de for Home Assistant

**Area and route-based speed-camera awareness, built natively for Home Assistant.**

Monitor a radius around home, a commute corridor, or both — with map entities, useful automations, a polished dashboard card, and privacy-conscious diagnostics.

[![Version](https://img.shields.io/badge/version-1.4.3-4c8bf5)](CHANGELOG.md)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.12%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-41BDF5)](https://hacs.xyz/)
[![Hassfest](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/hassfest.yaml)
[![Code quality](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/quality.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/quality.yaml)
[![CodeQL](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/codeql.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/codeql.yaml)
[![Languages](https://img.shields.io/badge/UI-DE%20%7C%20EN%20%7C%20AR-8a63d2)](#configuration)

[![Open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=abderlahmanalhnedi&repository=hass-blitzerde&category=integration)

</div>

> [!IMPORTANT]
> This is an **unofficial community integration** and is not endorsed or supported by Blitzer.de. The upstream map endpoint is undocumented and can change. The integration is designed to fail safely, surface health clearly, and avoid hiding upstream problems.

## Why install it?

| 🗺️ Useful | 🛡️ Trust-focused | ⚡ Home Assistant-native | 🎨 Polished |
| --- | --- | --- | --- |
| Area + route corridor monitoring | No upstream account/token required | Config Flow + Options Flow | Built-in Radar card |
| Nearest + new report awareness | Location/waypoints redacted in diagnostics | Geo Location map entities | Mobile responsive |
| Ignore persistent false-positive IDs | Bounded API requests + rate-limit handling | Events + manual refresh action | DE / EN / AR |
| New-report time window | Hassfest, HACS, Ruff, tests, CodeQL | Stable entity unique IDs | Online/offline + last update |

### Trust at a glance

- **No YAML required** for normal setup.
- **No Blitzer.de credentials** are stored or transmitted.
- **Health is visible**: upstream connectivity, last successful update, request duration, and failure count.
- **Home Assistant Repairs** warns after repeated upstream failures and clears automatically after recovery.
- **Privacy-aware diagnostics** redact area coordinates and route waypoints.
- **API abuse protection**: timeouts, rate-limit backoff, bounded route query count, and bounded concurrency.
- **Regression protection**: unit tests for timestamp parsing and route geometry plus Home Assistant/HACS validation.
- **Transparent maintenance**: [Changelog](CHANGELOG.md), [Roadmap](ROADMAP.md), [Security policy](SECURITY.md), [Support guide](SUPPORT.md), and [Architecture](docs/ARCHITECTURE.md).

> [!NOTE]
> The HACS button opens/adds the custom repository. You must still **Download Blitzer.de in HACS and restart Home Assistant** before starting the integration setup.

## Highlights

- **Home Assistant 2026-ready architecture** using `ConfigEntry.runtime_data` and `DataUpdateCoordinator`
- **UI configuration and options flow** — no YAML required
- Mobile, trailer, fixed **and explicit archive** report forms
- **17 semantic control kinds**: speed, red light, section control, tunnel, distance, weight, height, lane, access, police and more
- Two search modes: **Area / radius** and **Route / corridor**
- Multi-step waypoint editor for commute and travel routes
- Bounded, deduplicated route sampling with accurate distance-to-route calculation
- Optional city regex filter
- Optional confirmed-only filter
- Cameras sorted **nearest first**
- Distance to every result, plus a dedicated **Nearest speed camera** sensor
- Native **Geo Location** entities for the Home Assistant map
- `blitzerde_new_camera` event for genuinely new reports after startup
- Configurable polling interval, including **manual-only** mode
- Configurable **new report** window with `new` / `age_minutes` attributes
- Camera ID **ignore list** for persistent false positives
- Visible **upstream health** and **last successful update** entities
- Home Assistant **Repairs** warning after repeated upstream failures, with automatic recovery cleanup
- `blitzerde.refresh` action for on-demand updates and response data
- Built-in **Blitzer.de Radar** Lovelace card — no manual resource installation
- Responsive card editor, map/refresh actions, compact mode and source selection
- German, English **and Arabic** UI/card language support
- Up to 50 binary/geolocation camera slots
- Robust timeout, malformed-response, HTTP, and rate-limit handling
- Automatic retry/backoff through Home Assistant's coordinator
- Privacy-conscious downloadable diagnostics
- Privacy-conscious diagnostics for both area centers and route waypoints
- HACS, Hassfest, Ruff, Python compilation, unit tests, JavaScript validation and CodeQL security scanning

## Screenshots

### Live Home Assistant map

Real-world test data from a Dresden area entry, rendered through Home Assistant's native Map card. Only this integration's source, `blitzerde_dresden`, is selected in the screenshot.

![Blitzer.de live map in Home Assistant showing three speed-camera reports around Dresden](docs/screenshots/live-map-dresden.jpg)

## Why this fork exists

The repository was modernized after a broken coordinator change made the integration unloadable. The current code removes that broken duplicate coordinator implementation, restores a single API/coordinator path, and updates the integration to current Home Assistant patterns.

The original community project was created by **Tim Niklas**. This repository contains a substantially modernized maintenance branch by **Abdelrahman Al Hnedi**.

## Entities

For every configured area, the integration creates one Home Assistant device and the following entities:

| Entity | Purpose |
| --- | --- |
| **Detected speed cameras** | Number of currently exposed camera slots. Attributes include `total_detected`, `entity_limit`, and a per-city summary. |
| **Nearest speed camera** | Distance in km to the nearest current report, with camera/address attributes. |
| **Latest speed camera** | Human-readable street/city or description of the freshest report. The backend ID remains available as an attribute. |
| **New speed cameras** | Automation-friendly count of reports inside the configured freshness window. |
| **Last successful update** | Timestamp of the most recent successful upstream refresh. |
| **Upstream service** | Connectivity health with duration, failure count, interval, and search-mode telemetry. |
| **Speed camera 1 … N** | Safety binary sensors. Active slots represent current reports nearest-first; configured slots without a current report are unavailable rather than reported as safe. |
| **Geo Location markers** | One dynamic map marker per exposed camera, automatically added, updated, and removed as reports change. |

Each active camera slot exposes useful attributes such as:

- `backend`
- `vmax`
- `counter`
- `city`
- `street`
- `zip_code`
- `latitude` / `longitude`
- `distance_km`
- `description` when provided upstream
- `entity_picture`

## Installation

### HACS — recommended

[![Open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=abderlahmanalhnedi&repository=hass-blitzerde&category=integration)

This repository can be installed as a **custom HACS repository**:

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add:

   `https://github.com/abderlahmanalhnedi/hass-blitzerde`

4. Select **Integration** as the category.
5. Search for **Blitzer.de** and click **Download**.
6. Wait until HACS confirms the integration has been downloaded.
7. **Restart Home Assistant completely.**
8. After the restart, go to **Settings → Devices & services → Add integration → Blitzer.de**.

Only after steps 5–7 are complete, this shortcut should work:

[![Add Blitzer.de to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=blitzerde)

> [!NOTE]
> If Home Assistant shows **“This integration does not support configuration via the UI”**, the custom integration has not been loaded yet. Usually this means it was only added as a HACS custom repository but not downloaded, or Home Assistant has not been restarted after the download.

### Manual

Copy the directory:

`custom_components/blitzerde`

into:

`/config/custom_components/blitzerde`

Then restart Home Assistant and add **Blitzer.de** from **Settings → Devices & services**.

## Configuration

During setup you choose:

- **Display name** — for example `Dresden` or `Commute`
- **Area** — center point plus radius
- **Installation forms** — mobile, trailer, fixed, archive
- **Control kinds** — choose what the control measures (17 semantic categories)
- **Number of camera slots** — 1 to 50, default 9
- **City filter** — regular expression, default `.*`
- **Confirmed only** — enabled by default
- **Update interval** — minutes between polls; set to `0` for manual-only refreshes
- **Counts as new for** — freshness window in minutes; set to `0` to disable new-report highlighting
- **Ignored camera IDs** — comma-separated backend/public IDs that should never be exposed for this entry

The area radius returned by Home Assistant's location selector is interpreted in **meters**. Results from the rectangular upstream API query are then filtered again to the selected circular radius.

## Route / corridor mode

Route mode is designed for commutes and regularly travelled roads. Add waypoints one by one on the Home Assistant map. The integration connects them as straight segments and searches overlapping circles along the resulting polyline.

The configured **corridor width** is interpreted as the search distance from the route in meters. Results from overlapping requests are merged by the upstream camera ID, deduplicated, and then given an accurate shortest distance to the route before sorting.

To avoid accidentally issuing hundreds of requests every minute, a route is limited to **120 query points per refresh**. If a very long route exceeds that budget, the setup flow asks you to increase the corridor width or shorten the route. This is intentionally safer than silently hammering the upstream service.

> Route segments are straight lines between your waypoints. Put an extra waypoint on important bends or highway changes so the search corridor follows the road closely.

You can later open **Configure** on the integration entry and either change route settings or redraw the waypoints.

### City filter examples

- **Everything:** `.*`
- **Dresden only:** `^Dresden$`
- **Dresden or Radebeul:** `^(Dresden|Radebeul)$`
- **Cities beginning with `Dres`:** `^Dres.*`

Invalid regular expressions are rejected directly in the UI before the configuration is saved.

## Built-in Blitzer.de Radar card

The integration ships a dashboard card **inside the integration**. Home Assistant serves and registers it automatically, so there is no JavaScript file to copy into `www` and no Lovelace resource to add manually.

In dashboard edit mode, add a manual/custom card with:

```yaml
type: custom:blitzerde-card
title: Blitzer.de Radar
max_items: 6
show_map: true
show_refresh: true
compact: false
```

The visual editor can also configure the title, source, maximum rows, map button, refresh button and compact mode.

The card automatically discovers this integration's `geo_location` and count entities. It shows:

- current camera count
- nearest camera as a highlighted hero item
- distance and speed limit
- street/city and camera type
- Area vs Route mode
- direct **Refresh** action
- direct link to the Home Assistant map
- responsive layout for mobile dashboards
- German, English and Arabic labels based on the Home Assistant frontend language

If you configure several Blitzer.de entries, choose a specific source in the card editor.

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

## Ready-made notification blueprint

Want a useful automation without writing templates? Import the bundled **New camera nearby** blueprint:

[![Import Blitzer.de notification blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fabderlahmanalhnedi%2Fhass-blitzerde%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fblitzerde%2Fnew_camera_mobile_notification.yaml)

It lets you choose:

- the Home Assistant Companion App device to notify
- a maximum distance from the configured area/route
- an optional exact area/route name filter

The notification includes the report summary, distance, and speed limit when available. It listens to `blitzerde_new_camera`, so the first refresh after a Home Assistant restart is treated as a baseline instead of producing a notification storm.

## Example automation

Choose one of the generated `Speed camera N` binary sensors and use it as the trigger:

```yaml
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
```

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

`/config/custom_components/blitzerde`

### Setup says it cannot connect

The config flow tests the upstream endpoint before saving. A failure can mean:

- temporary network/DNS problems
- the upstream service is down
- the upstream endpoint changed
- the service rate-limited requests

Home Assistant will also retry runtime failures automatically. HTTP 429 responses use the upstream `Retry-After` signal when available.

### No cameras are shown

Check these first:

- increase the selected radius
- temporarily use the city regex `.*`
- enable more camera types
- temporarily disable **Confirmed only**

An empty but valid upstream result is not treated as a connection error.

## Removal

To remove the integration cleanly:

1. Go to **Settings → Devices & services → Blitzer.de**.
2. Open the menu for the entry you want to remove and choose **Delete**.
3. Remove any dashboard cards or automations that reference that entry's Blitzer.de entities.
4. If you installed the integration through HACS and no Blitzer.de entries remain, remove the repository from **HACS → Blitzer.de** and restart Home Assistant.

Deleting a config entry unloads its sensor, binary-sensor and geo-location platforms. Dynamic camera markers owned by that entry are removed with the entry; Home Assistant does not need a manual entity-registry cleanup.

## Data and privacy

In area mode, the integration sends the selected map bounding box to the upstream map service in order to retrieve nearby reports. In route mode, it sends a bounded series of overlapping bounding-box requests along the waypoint route. No Home Assistant credentials are sent. The integration has no authentication token of its own.

Because the endpoint is unofficial and undocumented, review the relevant service terms and local rules before relying on it.

## Development

The repository validates changes with:

- Home Assistant **Hassfest**
- **HACS Action**
- Python byte-code compilation
- unit tests for pure freshness and route geometry
- **Ruff** static checks
- Node.js syntax validation for the bundled dashboard card
- **CodeQL** security analysis
- Dependabot for GitHub Actions

Pull requests are welcome. For bugs, include your Home Assistant version, integration version, relevant log lines, and the redacted diagnostics file when possible.

Project documentation:

- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)
- [Security policy](SECURITY.md)
- [Support guide](SUPPORT.md)
- [Contributing](CONTRIBUTING.md)
- [Architecture](docs/ARCHITECTURE.md)

The actively maintained [somansch/blitzer](https://github.com/somansch/blitzer) project was reviewed as a working reference for map entities, event-driven notifications, manual refresh, polling controls, route search and bundled dashboard UX. See `THIRD_PARTY_NOTICES.md` for attribution and license details.

## Disclaimer

Speed-camera information can be incomplete, delayed, inaccurate, or unavailable. Do not use this integration in a way that distracts you while driving. Always follow applicable road-safety laws and local regulations.

---

<a id="deutsch"></a>

# 🇩🇪 Deutsche Dokumentation

<div align="center">

# 🚗⚡ Blitzer.de für Home Assistant

**Blitzer-Warnungen für Bereiche und Routen – nativ in Home Assistant integriert.**

Überwache einen Radius rund um dein Zuhause, einen Pendelweg oder beides – mit Karten-Entitäten, Automationen, einer integrierten Dashboard-Karte und datenschutzbewussten Diagnosedaten.

[![Version](https://img.shields.io/badge/version-1.4.3-4c8bf5)](CHANGELOG.md)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.12%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-41BDF5)](https://hacs.xyz/)
[![Hassfest](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/hassfest.yaml)
[![Code quality](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/quality.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/quality.yaml)
[![CodeQL](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/codeql.yaml/badge.svg)](https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/workflows/codeql.yaml)
[![Sprachen](https://img.shields.io/badge/UI-DE%20%7C%20EN%20%7C%20AR-8a63d2)](#konfiguration)

[![Repository in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=abderlahmanalhnedi&repository=hass-blitzerde&category=integration)

</div>

> [!IMPORTANT]
> Dies ist eine **inoffizielle Community-Integration** und wird nicht von Blitzer.de unterstützt oder betrieben. Der verwendete Karten-Endpunkt ist nicht offiziell dokumentiert und kann sich ändern. Die Integration ist deshalb so aufgebaut, dass Fehler sicher behandelt, Zustände sichtbar gemacht und Probleme mit dem Upstream-Dienst nicht versteckt werden.

## Warum diese Integration?

| 🗺️ Praktisch | 🛡️ Vertrauenswürdig aufgebaut | ⚡ Home-Assistant-nativ | 🎨 Modern |
| --- | --- | --- | --- |
| Bereichs- und Routenkorridor-Überwachung | Kein Blitzer.de-Konto oder Token nötig | Config Flow + Options Flow | Integrierte Radar-Karte |
| Nächster und neuer Blitzer | Standort/Wegpunkte in Diagnosen geschwärzt | Geo-Location-Entitäten | Für Mobilgeräte optimiert |
| Dauerhafte Fehlmeldungen ignorierbar | Begrenzte API-Abfragen + Rate-Limit-Handling | Events + manuelle Aktualisierung | DE / EN / AR |
| Zeitfenster für neue Meldungen | Hassfest, HACS, Ruff, Tests, CodeQL | Stabile Unique IDs | Online/Offline + letztes Update |

### Vertrauen auf einen Blick

- **Kein YAML erforderlich** für die normale Einrichtung.
- **Keine Blitzer.de-Zugangsdaten** werden gespeichert oder übertragen.
- **Zustand sichtbar**: Upstream-Erreichbarkeit, letztes erfolgreiches Update, Request-Dauer und Fehlerzähler.
- **Home Assistant Reparaturen** warnt nach wiederholten Upstream-Fehlern und verschwindet nach erfolgreicher Erholung automatisch.
- **Datenschutzbewusste Diagnosen**: Bereichskoordinaten und Routen-Wegpunkte werden geschwärzt.
- **Schutz vor API-Missbrauch**: Timeouts, Rate-Limit-Backoff, begrenzte Anzahl von Routenabfragen und begrenzte Parallelität.
- **Schutz vor Regressionen**: Unit-Tests für Zeitstempel und Routengeometrie plus Home-Assistant-/HACS-Validierung.
- **Transparente Wartung**: [Changelog](CHANGELOG.md), [Roadmap](ROADMAP.md), [Security Policy](SECURITY.md), [Support](SUPPORT.md) und [Architektur](docs/ARCHITECTURE.md).

> [!NOTE]
> Der HACS-Button öffnet bzw. fügt das Custom Repository hinzu. Danach musst du **Blitzer.de in HACS herunterladen und Home Assistant neu starten**, bevor du die Integration einrichten kannst.

## Highlights

- **Für Home Assistant 2026 vorbereitet** mit `ConfigEntry.runtime_data` und `DataUpdateCoordinator`
- Vollständige Einrichtung und Optionen über die Benutzeroberfläche
- Mobile, Trailer-, feste Blitzer **und explizite Archiv-Meldungen**
- **17 semantische Kontrollarten**: Geschwindigkeit, Rotlicht, Abschnittskontrolle, Tunnel, Abstand, Gewicht, Höhe, Spur, Zufahrt, Polizei und mehr
- Zwei Suchmodi: **Bereich / Radius** und **Route / Korridor**
- Mehrstufiger Wegpunkt-Editor für Pendel- und Reiserouten
- Begrenzte und deduplizierte Routenabfragen mit genauer Distanz zur Route
- Optionaler Städtefilter per regulärem Ausdruck
- Optional nur bestätigte Meldungen
- Blitzer nach Entfernung sortiert
- Eigener Sensor für den **nächsten Blitzer**
- Native **Geo Location**-Entitäten für die Home-Assistant-Karte
- Event `blitzerde_new_camera` für neu auftauchende Meldungen
- Einstellbares Polling inklusive **nur manuell**
- Konfigurierbares Zeitfenster für **neue Meldungen**
- Ignore-Liste für bekannte Fehlmeldungs-IDs
- Sichtbare Upstream-Gesundheit und letztes erfolgreiches Update
- Home-Assistant-**Reparaturhinweis** nach wiederholten Upstream-Fehlern mit automatischer Bereinigung nach der Erholung
- Action `blitzerde.refresh` für sofortige Aktualisierung
- Integrierte **Blitzer.de Radar** Lovelace-Karte
- Responsiver Karteneditor mit Map-/Refresh-Buttons und Compact Mode
- Benutzeroberfläche und Karte auf Deutsch, Englisch und Arabisch
- Bis zu 50 Binary-/Geo-Location-Slots
- Robuste Behandlung von Timeouts, fehlerhaften Antworten, HTTP-Fehlern und Rate Limits
- Automatisches Retry/Backoff über den Home-Assistant-Coordinator
- Datenschutzbewusste Diagnosedaten
- HACS, Hassfest, Ruff, Python-Kompilierung, Unit-Tests, JavaScript-Prüfung und CodeQL

## Screenshots

### Live-Karte in Home Assistant

Reale Testdaten eines Dresden-Bereichs, dargestellt mit der nativen Home-Assistant-Map-Karte. Im Screenshot ist ausschließlich die Quelle dieser Integration, `blitzerde_dresden`, ausgewählt.

![Blitzer.de Live-Karte in Home Assistant mit drei Blitzer-Meldungen rund um Dresden](docs/screenshots/live-map-dresden.jpg)

## Warum gibt es diesen Fork?

Das Repository wurde modernisiert, nachdem eine fehlerhafte Coordinator-Änderung die Integration unbrauchbar gemacht hatte. Die aktuelle Implementierung entfernt den defekten doppelten Coordinator, stellt einen klaren API-/Coordinator-Pfad wieder her und aktualisiert die Integration auf aktuelle Home-Assistant-Muster.

Das ursprüngliche Community-Projekt wurde von **Tim Niklas** erstellt. Dieses Repository enthält eine umfangreich modernisierte und gepflegte Weiterentwicklung von **Abdelrahman Al Hnedi**.

## Entitäten

Für jeden konfigurierten Bereich bzw. jede Route erstellt die Integration ein Home-Assistant-Gerät mit folgenden Entitäten:

| Entität | Zweck |
| --- | --- |
| **Detected speed cameras** | Anzahl der aktuell bereitgestellten Blitzer-Slots. Enthält u. a. `total_detected`, `entity_limit` und eine Zusammenfassung nach Stadt. |
| **Nearest speed camera** | Entfernung in km zur nächsten aktuellen Meldung inklusive Kamera-/Adressattributen. |
| **Latest speed camera** | Lesbare Straße/Stadt oder Beschreibung der aktuellsten Meldung. Die Backend-ID bleibt als Attribut verfügbar. |
| **New speed cameras** | Anzahl der Meldungen innerhalb des konfigurierten Neu-Zeitfensters. |
| **Last successful update** | Zeitpunkt der letzten erfolgreichen Aktualisierung. |
| **Upstream service** | Verbindungsstatus mit Dauer, Fehleranzahl, Intervall und Suchmodus. |
| **Speed camera 1 … N** | Safety-Binary-Sensoren. Belegte Slots zeigen aktuelle Meldungen nach Entfernung; konfigurierte Slots ohne aktuelle Meldung sind nicht verfügbar statt fälschlich als sicher markiert. |
| **Geo Location markers** | Dynamische Kartenmarker für aktuelle Blitzer, die automatisch hinzugefügt, aktualisiert und entfernt werden. |

Typische Attribute eines aktiven Blitzers:

- `backend`
- `vmax`
- `counter`
- `city`
- `street`
- `zip_code`
- `latitude` / `longitude`
- `distance_km`
- `description`, sofern vorhanden
- `entity_picture`

## Installation

### HACS — empfohlen

[![Repository in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=abderlahmanalhnedi&repository=hass-blitzerde&category=integration)

Installation als **Custom HACS Repository**:

1. Öffne **HACS** in Home Assistant.
2. Öffne das Drei-Punkte-Menü und wähle **Custom repositories**.
3. Füge dieses Repository hinzu:

   `https://github.com/abderlahmanalhnedi/hass-blitzerde`

4. Wähle **Integration** als Kategorie.
5. Suche nach **Blitzer.de** und klicke auf **Download**.
6. Warte, bis HACS den Download bestätigt.
7. **Starte Home Assistant vollständig neu.**
8. Gehe danach zu **Einstellungen → Geräte & Dienste → Integration hinzufügen → Blitzer.de**.

Erst nachdem die Schritte 5–7 abgeschlossen sind, funktioniert dieser Direktlink zuverlässig:

[![Blitzer.de zu Home Assistant hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=blitzerde)

> [!NOTE]
> Wenn Home Assistant meldet **„Diese Integration unterstützt keine Konfiguration über die Benutzeroberfläche“**, wurde die Custom Integration noch nicht geladen. Meist wurde sie nur als HACS-Repository hinzugefügt, aber noch nicht heruntergeladen oder Home Assistant wurde danach noch nicht neu gestartet.

### Manuell

Kopiere den Ordner:

`custom_components/blitzerde`

nach:

`/config/custom_components/blitzerde`

Starte Home Assistant anschließend neu und füge **Blitzer.de** unter **Einstellungen → Geräte & Dienste** hinzu.

## Konfiguration

Während der Einrichtung wählst du:

- **Anzeigename** — zum Beispiel `Dresden` oder `Arbeitsweg`
- **Suchmodus** — Bereich/Radius oder Route/Korridor
- **Bereich** — Mittelpunkt und Radius
- **Installationsformen** — mobil, Trailer, fest, Archiv
- **Kontrollarten** — wähle, was tatsächlich kontrolliert wird (17 semantische Kategorien)
- **Anzahl der Slots** — 1 bis 50, Standard 9
- **Städtefilter** — regulärer Ausdruck, Standard `.*`
- **Nur bestätigte Meldungen** — standardmäßig aktiviert
- **Update-Intervall** — Minuten zwischen Aktualisierungen; `0` = nur manuell
- **Als neu zählen für** — Zeitfenster in Minuten; `0` = deaktiviert
- **Ignorierte Blitzer-IDs** — kommagetrennte IDs, die dauerhaft ignoriert werden

Der Radius des Home-Assistant-Location-Selectors wird in **Metern** interpretiert. Ergebnisse der rechteckigen Upstream-Abfrage werden anschließend noch einmal auf den tatsächlich gewählten Kreis gefiltert.

## Route / Korridor

Der Routenmodus ist für Pendelwege und regelmäßig gefahrene Strecken gedacht. Du fügst auf der Home-Assistant-Karte mehrere Wegpunkte hinzu. Die Integration verbindet diese als gerade Segmente und durchsucht überlappende Kreise entlang der Route.

Die **Korridorbreite** definiert den maximalen Suchabstand zur Route in Metern. Ergebnisse aus überlappenden Abfragen werden anhand der Kamera-ID zusammengeführt, dedupliziert und nach dem kürzesten Abstand zur Route sortiert.

Zum Schutz des Upstream-Dienstes ist eine Route auf **120 Query Points pro Aktualisierung** begrenzt. Wenn eine sehr lange Route diese Grenze überschreitet, fordert die Einrichtung dazu auf, den Korridor zu verbreitern oder die Route zu verkürzen.

> Die Segmente zwischen den Wegpunkten sind gerade Linien. Setze deshalb zusätzliche Wegpunkte an wichtigen Kurven, Autobahnwechseln oder Abzweigungen.

Später kannst du unter **Konfigurieren** entweder die Routeneinstellungen ändern oder die Wegpunkte neu zeichnen.

### Beispiele für den Städtefilter

- **Alles:** `.*`
- **Nur Dresden:** `^Dresden$`
- **Dresden oder Radebeul:** `^(Dresden|Radebeul)$`
- **Alle Städte, die mit Dres beginnen:** `^Dres.*`

Ungültige reguläre Ausdrücke werden bereits in der Benutzeroberfläche abgelehnt.

## Integrierte Blitzer.de Radar-Karte

Die Integration enthält eine Dashboard-Karte **direkt in der Integration**. Es muss keine JavaScript-Datei nach `www` kopiert und keine Lovelace-Ressource manuell angelegt werden.

Beispiel:

```yaml
type: custom:blitzerde-card
title: Blitzer.de Radar
max_items: 6
show_map: true
show_refresh: true
compact: false
```

Über den visuellen Editor kannst du zusätzlich Titel, Quelle, maximale Anzahl von Zeilen, Map-Button, Refresh-Button und Compact Mode einstellen.

Die Karte erkennt automatisch die `geo_location`- und Count-Entitäten dieser Integration und zeigt unter anderem:

- aktuelle Anzahl der Blitzer
- nächsten Blitzer hervorgehoben
- Entfernung und Geschwindigkeitslimit
- Straße, Stadt und Blitzer-Typ
- Bereichs- oder Routenmodus
- direkten **Refresh**
- Link zur Home-Assistant-Karte
- responsives Layout
- deutsche, englische und arabische Texte passend zur Home-Assistant-Sprache

Bei mehreren Blitzer.de-Einträgen kannst du im Karteneditor eine bestimmte Quelle auswählen.

## Home-Assistant-Karte

Aktuelle Meldungen werden als native `geo_location`-Entitäten bereitgestellt. Füge die eingebaute **Map**-Karte von Home Assistant hinzu und wähle die Blitzer.de-Quelle des gewünschten Bereichs bzw. der Route.

Die Marker enthalten unter anderem:

- Koordinaten
- Entfernung
- Straße und Stadt
- Geschwindigkeitslimit
- Report-ID
- Blitzer-Typ
- Kurzbeschreibung

Die Entitäten sind dynamisch. Verschwindet eine Meldung aus den aktuellen Ergebnissen, wird der entsprechende Marker entfernt und bleibt nicht als verwaiste `unavailable`-Entität zurück.

## Event für neue Blitzer

Nach der ersten erfolgreichen Abfrage erzeugt jede neu auftauchende Kamera-ID das Event:

`blitzerde_new_camera`

Die erste Abfrage nach einem Neustart dient absichtlich als Baseline. Dadurch erzeugt Home Assistant nach jedem Neustart nicht sofort eine Flut vermeintlich neuer Meldungen.

Beispiel:

```yaml
triggers:
  - trigger: event
    event_type: blitzerde_new_camera
actions:
  - action: notify.mobile_app_YOUR_PHONE
    data:
      title: "Neuer Blitzer"
      message: "{{ trigger.event.data.summary }} · {{ trigger.event.data.distance_km }} km"
```

Der Event-Payload enthält unter anderem `config_entry_id`, `area`, `id`, `camera_type`, `summary`, Adressdaten, Koordinaten, `distance_km` und `vmax`.

## Polling und manuelle Aktualisierung

Das Update-Intervall wird pro Eintrag in Minuten konfiguriert. Standard ist eine Minute. Mit `0` wird nur dann aktualisiert, wenn eine Automation oder der Benutzer eine Aktualisierung auslöst.

Dafür gibt es die Home-Assistant-Action:

`blitzerde.refresh`

Sie aktualisiert den gewählten Integrationseintrag sofort und kann die aktuelle Trefferliste als Response Data an Automationen zurückgeben.

## Fertige Notification-Blueprint

Für Benachrichtigungen ohne eigene Templates gibt es die enthaltene **New camera nearby** Blueprint:

[![Blitzer.de Notification Blueprint importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fabderlahmanalhnedi%2Fhass-blitzerde%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fblitzerde%2Fnew_camera_mobile_notification.yaml)

Du kannst festlegen:

- welches Home-Assistant-Companion-App-Gerät benachrichtigt wird
- maximale Entfernung
- optional einen exakten Bereichs-/Routennamen

Die Benachrichtigung enthält Kurzbeschreibung, Entfernung und – sofern verfügbar – das Geschwindigkeitslimit.

## Beispiel-Automation

Du kannst einen der erzeugten `Speed camera N`-Binary-Sensoren als Trigger verwenden:

```yaml
alias: Blitzer in der Nähe erkannt
triggers:
  - trigger: state
    entity_id: binary_sensor.YOUR_SPEED_CAMERA_1
    from: "off"
    to: "on"
actions:
  - action: notify.mobile_app_YOUR_PHONE
    data:
      title: "Blitzer in der Nähe"
      message: >-
        {{ state_attr('binary_sensor.YOUR_SPEED_CAMERA_1', 'street') }} ·
        {{ state_attr('binary_sensor.YOUR_SPEED_CAMERA_1', 'distance_km') }} km ·
        {{ state_attr('binary_sensor.YOUR_SPEED_CAMERA_1', 'vmax') }} km/h
mode: single
```

## Diagnosedaten

Wenn etwas nicht funktioniert:

1. Gehe zu **Einstellungen → Geräte & Dienste → Blitzer.de**.
2. Öffne das Menü des Integrationseintrags.
3. Lade **Diagnosedaten** herunter.
4. Hänge die Datei an ein GitHub-Issue an.

Standortdaten und Routen-Wegpunkte werden dabei absichtlich geschwärzt.

## Fehlerbehebung

### Integration erscheint nach der HACS-Installation nicht

Starte Home Assistant nach dem Download der Integration vollständig neu. Falls sie weiterhin nicht erscheint, lade das Browser-Frontend neu und prüfe, ob dieser Ordner existiert:

`/config/custom_components/blitzerde`

### Einrichtung meldet, dass keine Verbindung möglich ist

Der Config Flow prüft den Upstream-Endpunkt vor dem Speichern. Mögliche Ursachen:

- temporäre Netzwerk- oder DNS-Probleme
- Upstream-Dienst nicht erreichbar
- Upstream-Endpunkt wurde geändert
- Rate Limit wurde ausgelöst

Auch zur Laufzeit versucht Home Assistant Aktualisierungen automatisch erneut. HTTP-429-Antworten berücksichtigen `Retry-After`, sofern vorhanden.

### Keine Blitzer sichtbar

Prüfe zuerst:

- Radius erhöhen
- testweise Städtefilter auf `.*` setzen
- weitere Blitzer-Typen aktivieren
- testweise **Nur bestätigte Meldungen** deaktivieren

Ein gültiges, aber leeres Ergebnis wird nicht als Verbindungsfehler gewertet.

## Entfernen

So entfernst du die Integration sauber:

1. Gehe zu **Einstellungen → Geräte & Dienste → Blitzer.de**.
2. Öffne das Menü des gewünschten Eintrags und wähle **Löschen**.
3. Entferne Dashboard-Karten und Automationen, die Entitäten dieses Eintrags verwenden.
4. Wenn keine Blitzer.de-Einträge mehr vorhanden sind, kannst du die Integration anschließend aus HACS entfernen und Home Assistant neu starten.

Beim Löschen eines Config Entries werden Sensor-, Binary-Sensor- und Geo-Location-Plattformen entladen. Dynamische Kartenmarker dieses Eintrags werden ebenfalls entfernt.

## Daten und Datenschutz

Im Bereichsmodus sendet die Integration den gewählten Kartenbereich an den Upstream-Kartendienst, um Meldungen in der Nähe abzurufen. Im Routenmodus werden mehrere begrenzte Bounding-Box-Abfragen entlang der Wegpunkte durchgeführt.

Es werden **keine Home-Assistant-Zugangsdaten** übertragen. Die Integration besitzt auch keinen eigenen Login-Token.

Da der verwendete Endpunkt inoffiziell und nicht dokumentiert ist, solltest du die jeweils geltenden Nutzungsbedingungen und lokalen Regeln beachten.

## Entwicklung

Das Repository validiert Änderungen unter anderem mit:

- Home Assistant **Hassfest**
- **HACS Action**
- Python-Kompilierung
- Unit-Tests für Zeitstempel und Routengeometrie
- Home-Assistant-aware Config-/Runtime-Tests
- **Ruff**
- Node.js-Syntaxprüfung der Dashboard-Karte
- **CodeQL**
- Dependabot

Beiträge sind willkommen. Bei Fehlern sollten möglichst Home-Assistant-Version, Integrationsversion, relevante Log-Zeilen und die geschwärzte Diagnosedatei angegeben werden.

Weitere Projektdokumentation:

- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)
- [Security Policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Contributing](CONTRIBUTING.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Core Readiness](docs/CORE_READINESS.md)

Das aktiv gepflegte Projekt [somansch/blitzer](https://github.com/somansch/blitzer) wurde als technische Referenz für Geo-Location-Entitäten, Events, Polling, manuelle Aktualisierung, Routensuche und Dashboard-UX betrachtet. Details zur Attribution und zu Lizenzen stehen in `THIRD_PARTY_NOTICES.md`.

## Hinweis

Blitzerinformationen können unvollständig, verspätet, falsch oder zeitweise nicht verfügbar sein. Verwende die Integration nicht auf eine Weise, die dich während der Fahrt ablenkt. Beachte immer die geltenden Verkehrsregeln und lokalen Vorschriften.

[⬆️ Zurück zur englischen Version](#english)

