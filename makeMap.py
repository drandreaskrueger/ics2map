import os
import csv
import json
from datetime import datetime

import tomllib  # Python 3.11+
# If you're on older Python, use: pip install tomli then import tomli as tomllib

from importICS import load_events_from_ics
from geocodeCache import GeocodeCache
from geocode import geocode_events
from loggingTools import Logger, LogAgg, load_aggregates_snapshot

MAP_HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>ICS Locations (Filter by date)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
  <style>
    body { margin: 0; }
    #map { height: 100vh; }
    #controls {
      position: absolute;
      top: 10px; left: 10px; z-index: 1000;
      background: rgba(255,255,255,0.95);
      padding: 10px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.15);
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      font-size: 13px;
      line-height: 1.2;
    }
    #controls input { width: 130px; }
    #controls label { margin-right: 8px; }
    button { margin-top: 6px; }
  </style>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
</head>
<body>
  {controls_block}

  <div id="map"></div>

  <script>
    const map = L.map('map', { zoomSnap: 0.25 });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    function escapeHtml(str) {{
      return (str ?? "").toString()
        .replaceAll('&','&amp;')
        .replaceAll('<','&lt;')
        .replaceAll('>','&gt;')
        .replaceAll('"','&quot;')
        .replaceAll("'","&#039;");
    }}

    let allPoints = [];
    let clusterGroup = null;

    function dateInRange(dateStr, fromStr, toStr) {{
      if (!dateStr) return false;
      if (fromStr && dateStr < fromStr) return false;
      if (toStr && dateStr > toStr) return false;
      return true;
    }}

    function renderFiltered(fromStr, toStr) {{
      if (clusterGroup) {{
        map.removeLayer(clusterGroup);
        clusterGroup = null;
      }}

      const filtered = allPoints.filter(p => dateInRange(p.date, fromStr || "", toStr || ""));

      document.getElementById('status').textContent =
        filtered.length ? `Showing ${{filtered.length}} event(s)` : 'No events in range';

      clusterGroup = L.markerClusterGroup({{
        chunkedLoading: true,
        showCoverageOnHover: true,
        maxClusterRadius: 50
      }});

      let bounds = [];

      for (const p of filtered) {{
        const lat = p.lat, lon = p.lon;
        if (typeof lat !== 'number' || typeof lon !== 'number') continue;

        const loc = p.location_text || "";
        const display = p.display_name || "";
        const summary = p.summary || "";
        const date = p.date || "";

        const popupHtml = `
          <div style="max-width:280px;">
            <div style="font-weight:700; margin-bottom:4px;">${{escapeHtml(summary || 'Event')}}</div>
            <div style="font-size:12px;"><b>Date:</b> ${{escapeHtml(date)}}</div>
            <div style="font-size:12px; margin-top:4px;"><b>Location:</b> ${{escapeHtml(loc)}}</div>
            <div style="font-size:12px; margin-top:4px;"><b>Geocoder:</b> ${{escapeHtml(display)}}</div>
          </div>
        `;

        const marker = L.circleMarker([lat, lon], {{
          radius: 7,
          weight: 1,
          color: '#2563eb',
          fillColor: '#3b82f6',
          fillOpacity: 0.85
        }}).bindPopup(popupHtml);

        marker.addTo(clusterGroup);
        bounds.push([lat, lon]);
      }}

      clusterGroup.addTo(map);

      if (bounds.length) map.fitBounds(L.latLngBounds(bounds).pad(0.15));
    }}

    async function loadMapData() {{
      // load mapData.csv converted to JS objects is done by a simple fetch+parse in JS
      const resp = await fetch('mapData.csv');
      const text = await resp.text();
      const lines = text.trim().split('\\n');
      const header = lines.shift().split(',');

      const idx = {{
        summary: header.indexOf('summary'),
        uid: header.indexOf('uid'),
        date: header.indexOf('date'),
        location_text: header.indexOf('location_text'),
        lat: header.indexOf('lat'),
        lon: header.indexOf('lon'),
        display_name: header.indexOf('display_name'),
        country_code: header.indexOf('country_code')
      }};

      allPoints = lines.map(line => {{
        // naive CSV split; safe enough for your expected dataset.
        // Marked: could fail if fields contain commas.
        const parts = line.split(',');
        const lat = parseFloat(parts[idx.lat]);
        const lon = parseFloat(parts[idx.lon]);

        return {{
          summary: parts[idx.summary],
          uid: parts[idx.uid],
          date: parts[idx.date],
          location_text: parts[idx.location_text],
          lat: lat,
          lon: lon,
          display_name: parts[idx.display_name],
          country_code: parts[idx.country_code]
        }};
      }});

      const dates = allPoints.map(p => p.date).filter(Boolean).sort();
      const min = dates[0] || "";
      const max = dates[dates.length - 1] || "";

      if (document.getElementById('fromDate')) document.getElementById('fromDate').value = min;
      if (document.getElementById('toDate')) document.getElementById('toDate').value = max;

      renderFiltered(min, max);

      return allPoints;
    }}

    loadMapData().catch(e => {{
      console.error(e);
      map.setView([51.0, 10.0], 4);
    }});

    {maybe_apply_listener}
  </script>
</body>
</html>
"""


def build_controls_block(enabled: bool) -> str:
    """
    Create date slider controls block.
    """
    if not enabled:
        return '<div id="status" style="display:none"></div>'

    return """
  <div id="controls">
    <div>
      <label>From</label><input id="fromDate" type="date" />
    </div>
    <div style="margin-top:6px;">
      <label>To</label><input id="toDate" type="date" />
    </div>
    <button id="applyBtn" type="button">Apply</button>
    <div id="status" style="margin-top:6px; color:#444;"></div>
  </div>
"""


def main():
    """
    Main pipeline:
    1) read config
    2) load ICS events with date+location selection
    3) geocode with caching + rate limiting
    4) write mapData.csv + map.html
    5) write logs + aggregates
    """
    # Load config.toml
    with open("config.toml", "rb") as f:
        cfg = tomllib.load(f)

    output_dir = cfg["outputDir"]
    os.makedirs(output_dir, exist_ok=True)

    log_path = os.path.join(output_dir, "log.txt")
    logger = Logger(log_path)

    agg = LogAgg()

    # Optional: load credentials file (kept hidden)
    # We’ll only use it in a later step to wire Nomination userAgent properly.
    if os.path.exists("geocodeCredentialsFile.toml"):
        with open("geocodeCredentialsFile.toml", "rb") as f:
            _ = tomllib.load(f)

    # Import ICS selection
    ics_path = cfg["icsPath"]
    date_from = cfg["importICS"]["dateFrom"]
    date_to = cfg["importICS"]["dateTo"]
    require_location = cfg["importICS"].get("requireLocation", True)

    agg.totalImportedEvents = 0
    events = load_events_from_ics(
        ics_path=ics_path,
        date_from=date_from,
        date_to=date_to,
        require_location=require_location,
    )
    agg.totalSelectedEvents = len(events)

    logger.info(f"Imported events selected by date range: {len(events)} from '{ics_path}'")

    # Geocode
    geo_cfg = cfg["geoCode"]
    countries = cfg["importICS"]["countries"]
    rate_limit_seconds = float(geo_cfg["rateLimitSeconds"])
    geocoder_language = geo_cfg.get("geocoderLanguage", "en")

    use_cache = bool(geo_cfg.get("useGeocodeCache", True))
    geocode_cache_csv = os.path.join(output_dir, geo_cfg["geocodeCacheCsv"])
    failed_csv_path = os.path.join(output_dir, geo_cfg["geocodeFailedCsv"])
    map_data_csv_path = os.path.join(output_dir, geo_cfg["mapDataCsv"])

    geocode_cache = GeocodeCache(geocode_cache_csv, logger=logger) if use_cache else None
    if geocode_cache:
        geocode_cache.load()

    dedupe = bool(geo_cfg.get("dedupeByLocationText", True))

    map_rows, failed_rows = geocode_events(
        events=events,
        allowed_country_codes=countries,
        rate_limit_seconds=rate_limit_seconds,
        geocoder_language=geocoder_language,
        geocode_cache=geocode_cache,
        failed_csv_path=failed_csv_path,
        logger=logger,
        agg=agg,
        dedupe_by_location_text=dedupe
    )

    if geocode_cache:
        geocode_cache.save()

    # Write mapData.csv (this drives map.html)
    with open(map_data_csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["summary", "uid", "date", "location_text", "lat", "lon", "display_name", "country_code"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in map_rows:
            writer.writerow(r)

    logger.info(f"Wrote map data rows: {len(map_rows)} to {map_data_csv_path}")

    # Write map.html
    make_cfg = cfg["makeMap"]
    date_slider = make_cfg.get("dateSlider", "ON") == "ON"
    map_html_path = os.path.join(output_dir, make_cfg.get("mapHtml", "map.html"))

    controls_block = build_controls_block(date_slider)
    maybe_apply_listener = """
    document.getElementById('applyBtn')?.addEventListener('click', () => {
      const fromVal = document.getElementById('fromDate').value;
      const toVal = document.getElementById('toDate').value;
      renderFiltered(fromVal, toVal);
    });
    """

    html = MAP_HTML_TEMPLATE.format(
        controls_block=controls_block,
        maybe_apply_listener=maybe_apply_listener
    )

    with open(map_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Aggregate screen output (not per event)
    logger.info("Pipeline complete")
    print(load_aggregates_snapshot(agg))
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()