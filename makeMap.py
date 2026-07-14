import os
import csv
import json
from datetime import datetime
import tomllib  # Python 3.11+

from importICS import load_events_from_ics
from geocodeCache import GeocodeCache
from geocode import geocode_events
from loggingTools import Logger, LogAgg, load_aggregates_snapshot

from htmlTools import build_controls_block


def load_config_and_init_logging(logger_output_dir: str):
    """
    Load config.toml and set up logger and aggregates.
    Returns (cfg, output_dir, logger, agg).
    """
    # Marked: could fail if config.toml missing/invalid; keep it obvious at top-level.
    with open("config.toml", "rb") as f:
        cfg = tomllib.load(f)

    output_dir = cfg["outputDir"]
    os.makedirs(output_dir, exist_ok=True)

    log_path = os.path.join(output_dir, "log.txt")
    logger = Logger(log_path)
    agg = LogAgg()
    return cfg, output_dir, logger, agg


def optionally_load_geocode_credentials(_logger):
    """
    Load geocodeCredentialsFile.toml if present.
    (Kept for future use; currently the credentials are not wired into geocode.py.)
    """
    if not os.path.exists("geocodeCredentialsFile.toml"):
        return

    # Marked: currently loaded but not used; still safe to keep.
    with open("geocodeCredentialsFile.toml", "rb") as f:
        _ = tomllib.load(f)


def load_selected_ics_events(cfg, agg, logger):
    """
    Load ICS events filtered by configured date range and location constraints.
    Returns selected events list.
    """
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

    logger.info(
        f"Imported events selected by date range: {len(events)} from '{ics_path}'"
    )
    return events


def run_geocoding_and_write_map_data(cfg, events, agg, logger, output_dir):
    """
    Geocode events with caching + rate limiting, then write mapData.csv.
    Returns map_rows count and/or failed rows.
    """
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

    # Marked: external web access. Keep this try/except for better logs later.
    try:
        map_rows, failed_rows = geocode_events(
            events=events,
            allowed_country_codes=countries,
            rate_limit_seconds=rate_limit_seconds,
            geocoder_language=geocoder_language,
            geocode_cache=geocode_cache,
            failed_csv_path=failed_csv_path,
            logger=logger,
            agg=agg,
            dedupe_by_location_text=dedupe,
        )
    except Exception as e:
        logger.error(f"geocode_events failed: {type(e).__name__}: {e}")
        raise

    if geocode_cache:
        geocode_cache.save()

    # Write mapData.csv (this drives map.html)
    with open(map_data_csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "summary",
            "uid",
            "date",
            "location_text",
            "lat",
            "lon",
            "display_name",
            "country_code",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in map_rows:
            writer.writerow(r)

    logger.info(f"Wrote map data rows: {len(map_rows)} to {map_data_csv_path}")
    return map_rows


def write_map_html(cfg, output_dir, logger):
    """
    Render map.html using mapTemplate.html and write it into the output directory.
    """
    make_cfg = cfg["makeMap"]
    date_slider = make_cfg.get("dateSlider", "ON") == "ON"

    map_html_path = os.path.join(output_dir, make_cfg.get("mapHtml", "map.html"))
    controls_block = build_controls_block(date_slider)

    maybe_apply_listener = """
const applyBtn = document.getElementById('applyBtn');
if (applyBtn) {
  applyBtn.addEventListener('click', () => {
    const fromVal = document.getElementById('fromDate').value;
    const toVal = document.getElementById('toDate').value;
    renderFiltered(fromVal, toVal);
  });
}
"""

    # Marked: could fail if mapTemplate.html missing; log then re-raise.
    try:
        with open("mapTemplate.html", "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        logger.error(f"Failed to read mapTemplate.html: {type(e).__name__}: {e}")
        raise

    html = (
        template
        .replace("__CONTROLS_BLOCK__", controls_block)
        .replace("__MAYBE_APPLY_LISTENER__", maybe_apply_listener)
    )

    with open(map_html_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    """
    Main pipeline orchestrator (kept short):
    1) load config + init logger
    2) load ICS selection
    3) geocode + write mapData.csv
    4) write map.html
    5) write logs + aggregates snapshot output
    """
    cfg, output_dir, logger, agg = load_config_and_init_logging("output")

    optionally_load_geocode_credentials(logger)

    events = load_selected_ics_events(cfg, agg, logger)
    _ = run_geocoding_and_write_map_data(cfg, events, agg, logger, output_dir)
    write_map_html(cfg, output_dir, logger)

    logger.info("Pipeline complete")
    print(load_aggregates_snapshot(agg))
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()
