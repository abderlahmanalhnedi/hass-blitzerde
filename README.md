# Blitzer.de Integration for Home Assistant 🏠

[![GitHub Release](https://img.shields.io/github/v/release/timniklas/hass-blitzerde?sort=semver&style=for-the-badge&color=green)](https://github.com/timniklas/hass-blitzerde/releases/)
[![GitHub Release Date](https://img.shields.io/github/release-date/timniklas/hass-blitzerde?style=for-the-badge&color=green)](https://github.com/timniklas/hass-blitzerde/releases/)
![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/timniklas/hass-blitzerde/latest/total?style=for-the-badge&label=Downloads%20latest%20Release)
![HA Analytics](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.blitzerde.total&style=for-the-badge&label=Active%20Installations&color=red)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/timniklas/hass-blitzerde?style=for-the-badge)
[![hacs](https://img.shields.io/badge/HACS-Integration-blue.svg?style=for-the-badge)](https://github.com/hacs/integration)

## Overview

The Blitzer.de Home Assistant Custom Integration allows you to integrate the Blitzer.de App with your Home Assistant setup.

## Example Markdown Card

### Code
*Simply replace "**YOURCITY**" with your chosen entity name.*

```
<h1><img src="https://www.blitzer.de/wp-content/uploads/logo-1.svg"  height="23" > Achtung!</h1>
<!--- **YOURCITY** -->
{%- set anzahl_aktuelle_warnungen = states("sensor.blitzerde_blitzerde_**YOURCITY**_total") | int(0) %}
{%- if anzahl_aktuelle_warnungen > 0 %}
<b>Blitzer **YOURCITY**</b><br>
{%- for i in range(int(anzahl_aktuelle_warnungen)) %}
{%- set blitzer_backend = state_attr("binary_sensor.blitzerde_blitzerde_**YOURCITY**_map"~ loop.index, "backend") %}
{%- set blitzer_vmax = state_attr("binary_sensor.blitzerde_blitzerde_**YOURCITY**_map"~ loop.index, "vmax") %}
{%- set blitzer_street = state_attr("binary_sensor.blitzerde_blitzerde_**YOURCITY**_map"~ loop.index, "street") %}
{%- set blitzer_counter = state_attr("binary_sensor.blitzerde_blitzerde_**YOURCITY**_map"~ loop.index, "counter") %}
<a href="https://map.blitzer.de/v5/ID/{{blitzer_backend}}/">{{blitzer_street}}</a> bei {{blitzer_vmax}} km/h&nbsp;&nbsp;
{%- for i in range(int(blitzer_counter)) %}
<img src="https://map.blitzer.de//v5/images/star_full.svg" width="12">
{%- endfor %}
{%- for i in range(3-int(blitzer_counter)) %}
<img src="https://map.blitzer.de/v5/images/star_contour.svg" width="12">
{%- endfor %}
<br>
{%- endfor %}
<br>
{%- endif %}
```

### Screenshot

![image](https://github.com/user-attachments/assets/5bb856ac-b7c2-41a6-83d1-b6edcb966f87)

## Installation

### HACS (recommended)

This integration is available in HACS (Home Assistant Community Store).

1. Install HACS if you don't have it already
2. Open HACS in Home Assistant
3. Go to any of the sections (integrations, frontend, automation).
4. Click on the 3 dots in the top right corner.
5. Select "Custom repositories"
6. Add following URL to the repository `https://github.com/timniklas/hass-blitzerde`.
7. Select Integration as category.
8. Click the "ADD" button
9. Search for "Blitzer.de"
10. Click the "Download" button

### Manual

To install this integration manually you have to download [_blitzerde.zip_](https://github.com/timniklas/hass-blitzerde/releases/latest/) and extract its contents to `config/custom_components/blitzerde` directory:

```bash
mkdir -p custom_components/blitzerde
cd custom_components/blitzerde
wget https://github.com/timniklas/hass-blitzerde/releases/latest/download/blitzerde.zip
unzip blitzerde.zip
rm blitzerde.zip
```

## Configuration

### Using UI

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=blitzerde)

From the Home Assistant front page go to `Configuration` and then select `Devices & Services` from the list.
Use the `Add Integration` button in the bottom right to add a new integration called `Blitzer.de`.

## Help and Contribution

If you find a problem, feel free to report it and I will do my best to help you.
If you have something to contribute, your help is greatly appreciated!
If you want to add a new feature, add a pull request first so we can discuss the details.

## Disclaimer

This custom integration is not officially endorsed or supported by Blitzer.de.
Use it at your own risk and ensure that you comply with all relevant terms of service and privacy policies.
