(() => {
  const CARD_TYPE = "blitzerde-card";
  const CARD_NAME = "Blitzer.de Radar";
  const SOURCE_PREFIX = "blitzerde_";

  const TEXT = {
    en: {
      title: "Blitzer.de Radar",
      cameras: "cameras",
      camera: "camera",
      nearest: "Nearest",
      noCameras: "No speed cameras currently in range",
      noCamerasHint: "The card will update automatically when a report appears.",
      refresh: "Refresh",
      map: "Open map",
      route: "Route",
      area: "Area",
      fixed: "Fixed",
      trailer: "Trailer",
      mobile: "Mobile",
      redlight: "Red light",
      limit: "Limit",
      distance: "Distance",
      source: "Source",
      allSources: "Automatic / all sources",
      maxItems: "Maximum cameras",
      showMap: "Show map button",
      showRefresh: "Show refresh button",
      compact: "Compact layout",
      customTitle: "Card title",
      editorHint: "The card discovers Blitzer.de entities automatically.",
      refreshFailed: "Refresh failed",
    },
    de: {
      title: "Blitzer.de Radar",
      cameras: "Blitzer",
      camera: "Blitzer",
      nearest: "Nächster",
      noCameras: "Aktuell keine Blitzer im Suchbereich",
      noCamerasHint: "Die Karte aktualisiert sich automatisch, sobald eine Meldung erscheint.",
      refresh: "Aktualisieren",
      map: "Karte öffnen",
      route: "Route",
      area: "Bereich",
      fixed: "Fest",
      trailer: "Anhänger",
      mobile: "Mobil",
      redlight: "Rotlicht",
      limit: "Limit",
      distance: "Entfernung",
      source: "Quelle",
      allSources: "Automatisch / alle Quellen",
      maxItems: "Maximale Blitzer",
      showMap: "Karten-Schaltfläche anzeigen",
      showRefresh: "Aktualisieren anzeigen",
      compact: "Kompaktes Layout",
      customTitle: "Kartentitel",
      editorHint: "Die Karte findet Blitzer.de-Entitäten automatisch.",
      refreshFailed: "Aktualisierung fehlgeschlagen",
    },
    ar: {
      title: "رادار Blitzer.de",
      cameras: "رادارات",
      camera: "رادار",
      nearest: "الأقرب",
      noCameras: "لا توجد رادارات حالياً ضمن نطاق البحث",
      noCamerasHint: "ستتحدث البطاقة تلقائياً عند ظهور بلاغ جديد.",
      refresh: "تحديث",
      map: "فتح الخريطة",
      route: "مسار",
      area: "منطقة",
      fixed: "ثابت",
      trailer: "مقطورة",
      mobile: "متحرك",
      redlight: "إشارة حمراء",
      limit: "السرعة",
      distance: "المسافة",
      source: "المصدر",
      allSources: "تلقائي / كل المصادر",
      maxItems: "أقصى عدد للرادارات",
      showMap: "إظهار زر الخريطة",
      showRefresh: "إظهار زر التحديث",
      compact: "عرض مضغوط",
      customTitle: "عنوان البطاقة",
      editorHint: "تكتشف البطاقة كيانات Blitzer.de تلقائياً.",
      refreshFailed: "فشل التحديث",
    },
  };

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const numeric = (value, fallback = Infinity) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  };

  const sourceLabel = (source) =>
    String(source || "")
      .replace(/^blitzerde_/, "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());

  class BlitzerdeCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._hass = null;
      this._config = {};
      this._busy = false;
      this._error = "";
    }

    static getStubConfig() {
      return {
        title: "Blitzer.de Radar",
        max_items: 5,
        show_map: true,
        show_refresh: true,
        compact: false,
      };
    }

    static getConfigElement() {
      return document.createElement("blitzerde-card-editor");
    }

    static getGridOptions() {
      return {
        columns: 6,
        rows: 5,
        min_columns: 3,
        min_rows: 3,
      };
    }

    setConfig(config) {
      this._config = {
        max_items: 5,
        show_map: true,
        show_refresh: true,
        compact: false,
        ...config,
      };
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    getCardSize() {
      return this._config.compact ? 3 : 5;
    }

    _language() {
      const raw = String(this._hass?.language || "en").toLowerCase();
      if (raw.startsWith("de")) return "de";
      if (raw.startsWith("ar")) return "ar";
      return "en";
    }

    _strings() {
      return TEXT[this._language()];
    }

    _geoEntities() {
      if (!this._hass) return [];
      const configuredSource = this._config.source;

      return Object.values(this._hass.states)
        .filter((state) => {
          if (!state.entity_id.startsWith("geo_location.")) return false;
          const source = state.attributes?.source;
          if (!String(source || "").startsWith(SOURCE_PREFIX)) return false;
          return !configuredSource || source === configuredSource;
        })
        .sort((left, right) => {
          const leftDistance = numeric(
            left.attributes?.distance_km,
            numeric(left.state)
          );
          const rightDistance = numeric(
            right.attributes?.distance_km,
            numeric(right.state)
          );
          return leftDistance - rightDistance;
        });
    }

    _countEntities() {
      if (!this._hass) return [];
      const configuredSource = this._config.source;

      return Object.values(this._hass.states).filter((state) => {
        if (!state.entity_id.startsWith("sensor.")) return false;
        const source = state.attributes?.blitzerde_source;
        if (!String(source || "").startsWith(SOURCE_PREFIX)) return false;
        return !configuredSource || source === configuredSource;
      });
    }

    _source() {
      if (this._config.source) return this._config.source;
      const firstGeo = this._geoEntities()[0];
      if (firstGeo?.attributes?.source) return firstGeo.attributes.source;
      const firstCount = this._countEntities()[0];
      return firstCount?.attributes?.blitzerde_source || "";
    }

    _configEntryId(items) {
      const fromGeo = items.find(
        (item) => item.attributes?.config_entry_id
      )?.attributes?.config_entry_id;
      if (fromGeo) return fromGeo;

      const source = this._source();
      const count = this._countEntities().find(
        (state) => !source || state.attributes?.blitzerde_source === source
      );
      return count?.attributes?.config_entry_id || "";
    }

    _cameraType(item, text) {
      if (String(item.attributes?.vmax) === "/") return text.redlight;
      const type = item.attributes?.camera_type;
      return text[type] || type || text.camera;
    }

    _cameraIcon(item) {
      if (String(item.attributes?.vmax) === "/") return "🚦";
      switch (item.attributes?.camera_type) {
        case "fixed":
          return "📷";
        case "trailer":
          return "🚛";
        default:
          return "⚡";
      }
    }

    _distance(item) {
      const value = numeric(
        item.attributes?.distance_km,
        numeric(item.state, NaN)
      );
      if (!Number.isFinite(value)) return "—";
      return value < 1
        ? `${Math.round(value * 1000)} m`
        : `${value.toFixed(value < 10 ? 1 : 0)} km`;
    }

    _speed(item) {
      const speed = item.attributes?.vmax;
      if (speed === "/" || speed === "?" || speed == null || speed === "") {
        return speed === "/" ? "🚦" : "—";
      }
      return `${escapeHtml(speed)} km/h`;
    }

    _place(item) {
      const street = item.attributes?.street;
      const city = item.attributes?.city;
      if (street && city) return `${street}, ${city}`;
      return street || city || item.attributes?.summary || item.name || "";
    }

    async _refresh() {
      if (!this._hass || this._busy) return;
      const items = this._geoEntities();
      const entryId = this._configEntryId(items);
      if (!entryId) return;

      this._busy = true;
      this._error = "";
      this._render();
      try {
        await this._hass.callService("blitzerde", "refresh", {
          config_entry_id: entryId,
        });
      } catch (error) {
        this._error = String(error?.message || error || "");
      } finally {
        this._busy = false;
        this._render();
      }
    }

    _openMap() {
      history.pushState(null, "", "/map");
      window.dispatchEvent(new Event("location-changed"));
    }

    _render() {
      if (!this.shadowRoot || !this._hass) return;

      const text = this._strings();
      const rtl = this._language() === "ar";
      const items = this._geoEntities();
      const source = this._source();
      const maxItems = Math.max(1, Number(this._config.max_items || 5));
      const visible = items.slice(0, maxItems);
      const nearest = visible[0];
      const title = this._config.title || text.title;
      const searchMode =
        nearest?.attributes?.search_mode ||
        this._countEntities()[0]?.attributes?.search_mode ||
        "area";
      const modeLabel = searchMode === "route" ? text.route : text.area;
      const entryId = this._configEntryId(items);

      const cameraRows = visible
        .map((item, index) => {
          const distance = this._distance(item);
          const place = escapeHtml(this._place(item));
          const summary = escapeHtml(
            item.attributes?.summary || this._cameraType(item, text)
          );
          const speed = this._speed(item);
          const type = escapeHtml(this._cameraType(item, text));
          return `
            <div class="camera-row ${index === 0 ? "nearest-row" : ""}">
              <div class="camera-icon" aria-hidden="true">${this._cameraIcon(item)}</div>
              <div class="camera-main">
                <div class="camera-place">${place || summary}</div>
                <div class="camera-meta">
                  <span>${type}</span>
                  ${summary && summary !== place ? `<span class="dot">•</span><span class="summary">${summary}</span>` : ""}
                </div>
              </div>
              <div class="camera-values">
                <strong>${distance}</strong>
                <span>${speed}</span>
              </div>
            </div>
          `;
        })
        .join("");

      const empty = `
        <div class="empty">
          <div class="empty-icon">🛰️</div>
          <strong>${escapeHtml(text.noCameras)}</strong>
          <span>${escapeHtml(text.noCamerasHint)}</span>
        </div>
      `;

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            direction: ${rtl ? "rtl" : "ltr"};
          }
          ha-card {
            overflow: hidden;
            position: relative;
            border-radius: var(--ha-card-border-radius, 18px);
          }
          .shell {
            position: relative;
            padding: ${this._config.compact ? "16px" : "20px"};
          }
          .glow {
            position: absolute;
            inset: -80px auto auto -80px;
            width: 210px;
            height: 210px;
            border-radius: 999px;
            background: color-mix(in srgb, var(--primary-color) 20%, transparent);
            filter: blur(32px);
            pointer-events: none;
          }
          .header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            position: relative;
          }
          .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            font-size: 12px;
            line-height: 1;
            padding: 7px 10px;
            border-radius: 999px;
            background: color-mix(in srgb, var(--primary-color) 12%, var(--card-background-color));
            color: var(--primary-color);
            font-weight: 700;
          }
          .pulse {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 0 5px color-mix(in srgb, currentColor 14%, transparent);
          }
          h2 {
            margin: 10px 0 3px;
            font-size: ${this._config.compact ? "20px" : "24px"};
            line-height: 1.15;
            letter-spacing: -0.02em;
          }
          .subtitle {
            color: var(--secondary-text-color);
            font-size: 13px;
          }
          .count {
            min-width: 64px;
            text-align: center;
            border-radius: 16px;
            padding: 10px 12px;
            background: color-mix(in srgb, var(--primary-color) 10%, var(--card-background-color));
            border: 1px solid color-mix(in srgb, var(--primary-color) 18%, var(--divider-color));
          }
          .count strong {
            display: block;
            font-size: 26px;
            line-height: 1;
          }
          .count span {
            display: block;
            margin-top: 5px;
            color: var(--secondary-text-color);
            font-size: 11px;
          }
          .hero {
            margin-top: 18px;
            padding: 16px;
            border-radius: 18px;
            background:
              linear-gradient(135deg,
                color-mix(in srgb, var(--primary-color) 16%, var(--card-background-color)),
                color-mix(in srgb, var(--primary-color) 4%, var(--card-background-color)));
            border: 1px solid color-mix(in srgb, var(--primary-color) 18%, var(--divider-color));
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 14px;
            align-items: center;
          }
          .hero-icon {
            width: 46px;
            height: 46px;
            display: grid;
            place-items: center;
            border-radius: 15px;
            font-size: 23px;
            background: var(--card-background-color);
            box-shadow: var(--ha-card-box-shadow);
          }
          .hero-label {
            color: var(--secondary-text-color);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
          }
          .hero-place {
            margin-top: 3px;
            font-weight: 700;
            font-size: 15px;
          }
          .hero-distance {
            text-align: end;
          }
          .hero-distance strong {
            display: block;
            font-size: 21px;
          }
          .hero-distance span {
            color: var(--secondary-text-color);
            font-size: 12px;
          }
          .list {
            margin-top: 12px;
            display: grid;
            gap: 7px;
          }
          .camera-row {
            display: grid;
            grid-template-columns: 38px minmax(0, 1fr) auto;
            align-items: center;
            gap: 11px;
            padding: 10px 8px;
            border-radius: 14px;
            transition: background 120ms ease;
          }
          .camera-row:hover {
            background: color-mix(in srgb, var(--primary-color) 6%, transparent);
          }
          .nearest-row {
            display: ${this._config.compact ? "grid" : "none"};
          }
          .camera-icon {
            width: 36px;
            height: 36px;
            display: grid;
            place-items: center;
            border-radius: 12px;
            background: color-mix(in srgb, var(--secondary-background-color) 85%, transparent);
            font-size: 18px;
          }
          .camera-main {
            min-width: 0;
          }
          .camera-place {
            font-weight: 650;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .camera-meta {
            margin-top: 3px;
            color: var(--secondary-text-color);
            font-size: 11px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .dot {
            padding: 0 5px;
          }
          .camera-values {
            text-align: end;
          }
          .camera-values strong {
            display: block;
            font-size: 13px;
          }
          .camera-values span {
            color: var(--secondary-text-color);
            font-size: 11px;
          }
          .empty {
            min-height: 150px;
            display: grid;
            place-items: center;
            align-content: center;
            text-align: center;
            gap: 7px;
            color: var(--secondary-text-color);
          }
          .empty strong {
            color: var(--primary-text-color);
          }
          .empty span {
            max-width: 320px;
            font-size: 12px;
          }
          .empty-icon {
            font-size: 32px;
          }
          .actions {
            margin-top: 14px;
            padding-top: 13px;
            border-top: 1px solid var(--divider-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
          }
          .source {
            min-width: 0;
            color: var(--secondary-text-color);
            font-size: 11px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .buttons {
            display: flex;
            gap: 7px;
          }
          button {
            appearance: none;
            border: 1px solid var(--divider-color);
            border-radius: 11px;
            background: var(--secondary-background-color);
            color: var(--primary-text-color);
            min-height: 36px;
            padding: 0 12px;
            cursor: pointer;
            font: inherit;
            font-size: 12px;
            font-weight: 650;
          }
          button.primary {
            border-color: color-mix(in srgb, var(--primary-color) 30%, var(--divider-color));
            color: var(--primary-color);
          }
          button:disabled {
            opacity: 0.55;
            cursor: default;
          }
          .error {
            margin-top: 8px;
            color: var(--error-color);
            font-size: 11px;
          }
          @media (max-width: 420px) {
            .summary { display: none; }
            .hero { grid-template-columns: auto minmax(0, 1fr) auto; }
            .shell { padding: 16px; }
          }
        </style>
        <ha-card>
          <div class="shell">
            <div class="glow"></div>
            <div class="header">
              <div>
                <span class="eyebrow"><span class="pulse"></span>${escapeHtml(modeLabel)}</span>
                <h2>${escapeHtml(title)}</h2>
                <div class="subtitle">${escapeHtml(sourceLabel(source) || "Blitzer.de")}</div>
              </div>
              <div class="count">
                <strong>${items.length}</strong>
                <span>${escapeHtml(items.length === 1 ? text.camera : text.cameras)}</span>
              </div>
            </div>

            ${
              nearest && !this._config.compact
                ? `
                  <div class="hero">
                    <div class="hero-icon">${this._cameraIcon(nearest)}</div>
                    <div>
                      <div class="hero-label">${escapeHtml(text.nearest)}</div>
                      <div class="hero-place">${escapeHtml(this._place(nearest))}</div>
                    </div>
                    <div class="hero-distance">
                      <strong>${this._distance(nearest)}</strong>
                      <span>${this._speed(nearest)}</span>
                    </div>
                  </div>
                `
                : ""
            }

            ${visible.length ? `<div class="list">${cameraRows}</div>` : empty}

            <div class="actions">
              <div class="source">${escapeHtml(text.source)} · ${escapeHtml(sourceLabel(source) || "Blitzer.de")}</div>
              <div class="buttons">
                ${
                  this._config.show_map !== false
                    ? `<button id="map-btn">🗺️ ${escapeHtml(text.map)}</button>`
                    : ""
                }
                ${
                  this._config.show_refresh !== false
                    ? `<button id="refresh-btn" class="primary" ${!entryId || this._busy ? "disabled" : ""}>↻ ${escapeHtml(this._busy ? "…" : text.refresh)}</button>`
                    : ""
                }
              </div>
            </div>
            ${this._error ? `<div class="error">${escapeHtml(text.refreshFailed)}: ${escapeHtml(this._error)}</div>` : ""}
          </div>
        </ha-card>
      `;

      this.shadowRoot
        .getElementById("refresh-btn")
        ?.addEventListener("click", () => this._refresh());
      this.shadowRoot
        .getElementById("map-btn")
        ?.addEventListener("click", () => this._openMap());
    }
  }

  class BlitzerdeCardEditor extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._hass = null;
      this._config = {};
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    setConfig(config) {
      this._config = { ...config };
      this._render();
    }

    _language() {
      const raw = String(this._hass?.language || "en").toLowerCase();
      if (raw.startsWith("de")) return "de";
      if (raw.startsWith("ar")) return "ar";
      return "en";
    }

    _sources() {
      if (!this._hass) return [];
      const values = new Set();
      for (const state of Object.values(this._hass.states)) {
        const geoSource = state.entity_id.startsWith("geo_location.")
          ? state.attributes?.source
          : null;
        const sensorSource = state.entity_id.startsWith("sensor.")
          ? state.attributes?.blitzerde_source
          : null;
        const source = geoSource || sensorSource;
        if (String(source || "").startsWith(SOURCE_PREFIX)) values.add(source);
      }
      return [...values].sort();
    }

    _changed(key, value) {
      const config = { ...this._config, [key]: value };
      if (value === "" || value == null) delete config[key];
      this._config = config;
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config },
          bubbles: true,
          composed: true,
        })
      );
    }

    _render() {
      if (!this.shadowRoot || !this._hass) return;
      const text = TEXT[this._language()];
      const rtl = this._language() === "ar";
      const sources = this._sources();

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            direction: ${rtl ? "rtl" : "ltr"};
          }
          .editor {
            display: grid;
            gap: 14px;
            padding: 8px 0;
          }
          .hint {
            color: var(--secondary-text-color);
            font-size: 12px;
          }
          label {
            display: grid;
            gap: 6px;
            font-size: 12px;
            font-weight: 650;
          }
          input, select {
            box-sizing: border-box;
            width: 100%;
            min-height: 42px;
            padding: 0 11px;
            border: 1px solid var(--divider-color);
            border-radius: 10px;
            background: var(--card-background-color);
            color: var(--primary-text-color);
            font: inherit;
          }
          .checks {
            display: grid;
            gap: 10px;
          }
          .check {
            display: flex;
            align-items: center;
            gap: 9px;
            font-weight: 500;
          }
          .check input {
            width: 18px;
            min-height: 18px;
          }
        </style>
        <div class="editor">
          <div class="hint">${escapeHtml(text.editorHint)}</div>
          <label>
            ${escapeHtml(text.customTitle)}
            <input id="title" value="${escapeHtml(this._config.title || "")}" placeholder="${escapeHtml(text.title)}">
          </label>
          <label>
            ${escapeHtml(text.source)}
            <select id="source">
              <option value="">${escapeHtml(text.allSources)}</option>
              ${sources
                .map(
                  (source) =>
                    `<option value="${escapeHtml(source)}" ${this._config.source === source ? "selected" : ""}>${escapeHtml(sourceLabel(source))}</option>`
                )
                .join("")}
            </select>
          </label>
          <label>
            ${escapeHtml(text.maxItems)}
            <input id="max-items" type="number" min="1" max="20" value="${Number(this._config.max_items || 5)}">
          </label>
          <div class="checks">
            <label class="check">
              <input id="show-map" type="checkbox" ${this._config.show_map !== false ? "checked" : ""}>
              <span>${escapeHtml(text.showMap)}</span>
            </label>
            <label class="check">
              <input id="show-refresh" type="checkbox" ${this._config.show_refresh !== false ? "checked" : ""}>
              <span>${escapeHtml(text.showRefresh)}</span>
            </label>
            <label class="check">
              <input id="compact" type="checkbox" ${this._config.compact ? "checked" : ""}>
              <span>${escapeHtml(text.compact)}</span>
            </label>
          </div>
        </div>
      `;

      this.shadowRoot.getElementById("title")?.addEventListener("change", (event) =>
        this._changed("title", event.target.value.trim())
      );
      this.shadowRoot.getElementById("source")?.addEventListener("change", (event) =>
        this._changed("source", event.target.value)
      );
      this.shadowRoot.getElementById("max-items")?.addEventListener("change", (event) =>
        this._changed("max_items", Math.max(1, Math.min(20, Number(event.target.value || 5))))
      );
      this.shadowRoot.getElementById("show-map")?.addEventListener("change", (event) =>
        this._changed("show_map", event.target.checked)
      );
      this.shadowRoot.getElementById("show-refresh")?.addEventListener("change", (event) =>
        this._changed("show_refresh", event.target.checked)
      );
      this.shadowRoot.getElementById("compact")?.addEventListener("change", (event) =>
        this._changed("compact", event.target.checked)
      );
    }
  }

  if (!customElements.get(CARD_TYPE)) {
    customElements.define(CARD_TYPE, BlitzerdeCard);
  }
  if (!customElements.get("blitzerde-card-editor")) {
    customElements.define("blitzerde-card-editor", BlitzerdeCardEditor);
  }

  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
    window.customCards.push({
      type: CARD_TYPE,
      name: CARD_NAME,
      description: "Modern speed-camera radar card for the Blitzer.de integration.",
      preview: true,
      documentationURL: "https://github.com/abderlahmanalhnedi/hass-blitzerde",
    });
  }
})();
