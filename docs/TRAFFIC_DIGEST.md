# Traffic Digest Blueprint

The `traffic_digest.yaml` automation blueprint creates a nearest-first summary from the Blitzer.de `geo_location` entities already held by Home Assistant. It does **not** perform another API refresh, so camera polling and hazard polling remain independent.

## English

Use the blueprint when you want a compact "what is currently ahead of me?" summary instead of one notification per report. It can include controls, hazards, or both; exclude archive reports by default; limit results by configured area/route name and distance; and cap the final message length.

Triggers supported:

- daily time
- leaving a selected zone with selected people/device trackers
- state changes of optional helper/entities
- the `blitzerde_digest_requested` event for on-demand digests

The blueprint can create a Home Assistant persistent notification without any mobile integration. Additional actions can be added for mobile push, TTS, scripts, or other delivery channels. Those actions can use `digest_title`, `digest_message`, `report_count`, and `reports`.

Direct import source: `blueprints/automation/blitzerde/traffic_digest.yaml`.

## Deutsch

Das Blueprint erstellt eine nach Entfernung sortierte Sammelmeldung aus den aktuell in Home Assistant vorhandenen Blitzer.de-Geo-Entitäten. Es führt **keinen zusätzlichen API-Abruf** aus; Kamera- und Gefahren-Polling bleiben deshalb getrennt.

Kontrollen und Gefahren können getrennt ein- oder ausgeschaltet werden. Archivmeldungen sind standardmäßig deaktiviert. Zusätzlich lassen sich Bereiche/Routen, maximale Entfernung und maximale Anzahl der Meldungen filtern.

Auslöser sind eine tägliche Uhrzeit, das Verlassen einer Zone, Änderungen ausgewählter Entitäten oder das Event `blitzerde_digest_requested`. Neben einer persistenten Home-Assistant-Benachrichtigung können eigene Aktionen für Mobile Push, TTS oder Skripte ergänzt werden.

## العربية

ينشئ الـBlueprint ملخصاً للبلاغات الحالية مرتباً من الأقرب إلى الأبعد اعتماداً على كيانات `geo_location` الموجودة مسبقاً في Home Assistant. وهو **لا يجري طلب API إضافياً**، لذلك يبقى تحديث الرادارات وتحديث المخاطر منفصلين.

يمكن اختيار الرادارات أو المخاطر أو كليهما، واستبعاد بلاغات الأرشيف افتراضياً، وتحديد مناطق/مسارات معيّنة، ووضع حد أقصى للمسافة وعدد البلاغات.

يمكن تشغيل الملخص بوقت يومي، عند مغادرة منطقة محددة، عند تغيّر كيان تختاره، أو عند إطلاق الحدث `blitzerde_digest_requested`. كما يمكن إنشاء إشعار داخل Home Assistant وإضافة إجراءات أخرى لإشعارات الهاتف أو TTS أو السكربتات.
