# Support

## Before reporting a bug

1. Update to the latest version through HACS.
2. Restart Home Assistant.
3. Verify **Blitzer.de → Upstream service** is connected.
4. Check **Last successful update** on the integration device.
5. Try the `blitzerde.refresh` action.
6. Download the integration diagnostics and verify that private location data is redacted.
7. Search existing issues before creating a new report.

## Fast troubleshooting

| Symptom | First checks |
| --- | --- |
| Integration is missing | Confirm `custom_components/blitzerde` exists and restart Home Assistant |
| UI says configuration is unsupported | The custom repository was likely added but the integration was not downloaded/restarted yet |
| No cameras | Use `.*` as city filter, disable confirmed-only temporarily, increase radius/corridor, check ignored IDs |
| Entities are unavailable | Check **Upstream service**, last update time, Home Assistant logs, then try manual refresh |
| Route returns too many-query warning | Increase corridor width or use fewer/shorter route segments |
| Dashboard card is missing | Restart Home Assistant and hard-refresh the frontend after updating the integration |
| One report should never appear | Add its backend/public ID to **Ignored camera IDs** |

## Bug reports

A useful bug report includes:

- Home Assistant version
- integration version
- HACS or manual installation
- Area or Route mode
- expected vs actual behavior
- reproduction steps
- relevant redacted log lines
- redacted diagnostics

Never post precise home coordinates or unrelated Home Assistant secrets.
