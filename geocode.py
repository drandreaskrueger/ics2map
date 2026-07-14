import csv
import os
import time
from typing import List, Dict, Optional, Tuple

from geopy.geocoders import Nominatim

from geocodeCache import GeocodeCache, GeocodeResult
from importICS import IcsEvent
from loggingTools import Logger, LogAgg


def _safe_get_country_code(geocode_raw: dict) -> str:
    """
    Extract a country code if available; else return empty string.
    Nominatim 'raw' structure may vary.
    """
    addr = geocode_raw.get("address") or {}
    # Sometimes 'country_code' exists; sometimes only 'country' exists.
    cc = (addr.get("country_code") or "").strip().upper()
    return cc


def geocode_events(
    events: List[IcsEvent],
    allowed_country_codes: List[str],
    rate_limit_seconds: float,
    geocoder_language: str,
    geocode_cache: Optional[GeocodeCache],
    failed_csv_path: str,
    logger: Logger,
    agg: LogAgg,
    dedupe_by_location_text: bool = True
) -> Tuple[List[dict], List[dict]]:
    """
    Main geocoding loop:
    - geocode only unique LOCATION strings (if dedupe_by_location_text=True)
    - reuse cached successful results
    - write per-event failures to geocodeFailed.csv (human readable)
    - return map rows (per event, not per location)
      and a list of review failures if you want later extensions.

    Output row schema used by makeMap:
      summary, uid, date, location_text, lat, lon, display_name, country_code
    """

    # Ensure failed csv exists and has header
    os.makedirs(os.path.dirname(failed_csv_path) or ".", exist_ok=True)
    file_exists = os.path.exists(failed_csv_path)
    if not file_exists:
        with open(failed_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["location_text", "event_date", "event_summary", "error"])
            writer.writeheader()

    geolocator = Nominatim(user_agent="ics-location-to-map")
    # NOTE: we keep user-agent here simple; you can override from geocodeCredentialsFile.toml
    # in a follow-up step. (This is a potential improvement area.)

    allowed_set = set([c.upper() for c in allowed_country_codes])

    # Per LOCATION cache:
    loc_to_success: Dict[str, GeocodeResult] = {}
    loc_to_error: Dict[str, str] = {}

    # Deduplicate location texts to reduce API calls
    if dedupe_by_location_text:
        unique_locs = sorted({ev.location_text for ev in events if ev.location_text})
    else:
        unique_locs = [ev.location_text for ev in events if ev.location_text]

    # Geocode unique locations (or attempts)
    for loc_text in unique_locs:
        if not loc_text:
            continue

        # Check geocode cache first
        if geocode_cache:
            cached = geocode_cache.get(loc_text)
            if cached:
                loc_to_success[loc_text] = cached
                continue

        # Geocode with throttling
        try:
            r = geolocator.geocode(loc_text, timeout=20, language=geocoder_language)
            time.sleep(rate_limit_seconds)

            if not r:
                loc_to_error[loc_text] = "not_found"
                agg.totalGeocodeFailed += 1
                logger.warn(f"Geocode FAIL location='{loc_text}' reason=not_found")
                continue

            raw = (r.raw or {})
            cc = _safe_get_country_code(raw)

            # Country filtering: if we can't determine cc or it doesn't match, mark as failure for review
            # (You can relax this later if needed.)
            if allowed_set and cc and cc not in allowed_set:
                loc_to_error[loc_text] = f"outside_allowed_countries (cc={cc})"
                agg.totalGeocodeFailed += 1
                logger.warn(f"Geocode FAIL location='{loc_text}' reason=outside_allowed_countries cc={cc}")
                continue

            # Accept even if cc is empty (ambiguous) — map will still be generated,
            # but you might prefer strictness. Keeping it workable for now.
            result = GeocodeResult(
                lat=float(r.latitude),
                lon=float(r.longitude),
                display_name=r.address or "",
                country_code=cc
            )

            loc_to_success[loc_text] = result
            if geocode_cache:
                geocode_cache.set(loc_text, result)

            agg.totalGeocodeSucceeded += 1
            logger.info(f"Geocode OK location='{loc_text}' -> ({result.lat},{result.lon}) cc={result.country_code}")

        except Exception as ex:
            # IMPORTANT: record exception name for debugging.
            err_name = type(ex).__name__
            loc_to_error[loc_text] = f"exception:{err_name}"
            agg.totalGeocodeFailed += 1
            logger.error(f"Geocode EX location='{loc_text}' exception={err_name}")

    # Build map rows per event
    map_rows: List[dict] = []
    failed_rows: List[dict] = []

    # Per-event logic (ties errors back to specific events for file outputs)
    for ev in events:
        if not ev.location_text:
            agg.totalGeocodeMissingLocation += 1
            # One line per event with missing location
            logger.warn(f"Missing LOCATION in event uid={ev.uid} date={ev.date}")
            failed_rows.append({
                "location_text": "",
                "event_date": ev.date,
                "event_summary": ev.summary,
                "error": "missing_location_text"
            })
            continue

        loc = ev.location_text
        if loc in loc_to_success:
            s = loc_to_success[loc]
            map_rows.append({
                "summary": ev.summary,
                "uid": ev.uid or "",
                "date": ev.date,
                "location_text": ev.location_text,
                "lat": s.lat,
                "lon": s.lon,
                "display_name": s.display_name,
                "country_code": s.country_code
            })
            continue

        # not in success means failure/ambiguous review
        err = loc_to_error.get(loc, "unknown_error")
        failed_rows.append({
            "location_text": loc,
            "event_date": ev.date,
            "event_summary": ev.summary,
            "error": err
        })

    # Append failures to CSV
    with open(failed_csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["location_text", "event_date", "event_summary", "error"])
        for row in failed_rows:
            writer.writerow(row)

    return map_rows, failed_rows