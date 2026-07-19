# importICS.py
import os
import re
import csv
import tomllib  # Python 3.11+
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ics import Calendar

from loggingTools import Logger


@dataclass
class IcsEvent:
    """
    Normalized event data needed for geocoding + map display.
    Time is ignored (YYYY-MM-DD only).
    """
    uid: Optional[str]
    summary: str
    date: str  # YYYY-MM-DD from DTSTART (begin)
    date_end: str  # YYYY-MM-DD from DTEND (end), or "" if missing
    location_text: str  # human LOCATION from ICS


def _norm_ws(s: Optional[str]) -> str:
    """
    Normalize whitespace for stable caching and comparison.
    """
    return re.sub(r"\s+", " ", (s or "").strip())


def _to_yyyy_mm_dd(value: str) -> str:
    """
    Convert ICS begin/end value to YYYY-MM-DD.
    Ignores the time part.

    Potential failure point:
    - ICS libraries may format values differently depending on timezone handling.
    - We use regex patterns as a best-effort approach.
    """
    s = (value or "").strip()

    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = re.search(r"\b(\d{4})(\d{2})(\d{2})\b", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    return ""


def _parse_date_ymd(date_str: str) -> datetime:
    """
    Parse YYYY-MM-DD to datetime for comparisons.
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def _write_import_failed_csv(
    failed_csv_path: str,
    failed_rows: List[dict],
) -> None:
    """
    Write structured import failures into a dedicated CSV file.

    CAREFUL: CSV quoting must be robust for arbitrary ICS text.
    """
    os.makedirs(os.path.dirname(failed_csv_path) or ".", exist_ok=True)
    fieldnames = ["uid", "event_name", "event_date", "event_end", "location_text", "reason"]

    with open(failed_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quotechar='"',
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for row in failed_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def load_events_from_ics(
    ics_path: str,
    date_from: str,
    date_to: str,
    require_location: bool = True,
    failed_csv_path: Optional[str] = None,
    logger: Optional[Logger] = None,
    agg=None,
) -> List[IcsEvent]:
    """
    Import ICS, select events by date (DTSTART only, inclusive), and extract LOCATION + DTSTART/DTEND.

    Does NOT silently drop invalid events when they violate required preconditions.
    Such events are written to `failed_csv_path` (if provided) and counted in `agg`.
    """
    with open(ics_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cal = Calendar(raw_text)

    # date range bounds
    df = _parse_date_ymd(date_from)
    dt = _parse_date_ymd(date_to)

    failed_rows: List[dict] = []
    selected_events: List[IcsEvent] = []

    total_in_source = len(list(cal.events))
    if agg is not None:
        agg.totalImportedEvents = total_in_source

    for e in cal.events:
        summary = _norm_ws(getattr(e, "name", None))  # human title
        uid = getattr(e, "uid", None)

        begin_str = str(getattr(e, "begin", "") or "")
        date = _to_yyyy_mm_dd(begin_str)

        end_str = str(getattr(e, "end", "") or "")
        date_end = _to_yyyy_mm_dd(end_str)

        # ICS "LOCATION"
        location_text = _norm_ws(getattr(e, "location", None))

        # Precondition checks that should be visible (import failures)
        if require_location and not location_text:
            reason = "Missing LOCATION"
            if logger:
                logger.warn(f"Import fail: {reason} uid={uid} name={summary}")
            failed_rows.append({
                "uid": uid or "",
                "event_name": summary,
                "event_date": date or "",
                "event_end": date_end or "",
                "location_text": "",
                "reason": reason,
            })
            if agg is not None:
                agg.totalImportFailed += 1
            continue

        if not date:
            reason = "Invalid DTSTART (BEGIN) date"
            if logger:
                logger.warn(f"Import fail: {reason} uid={uid} name={summary}")
            failed_rows.append({
                "uid": uid or "",
                "event_name": summary,
                "event_date": "",
                "event_end": date_end or "",
                "location_text": location_text,
                "reason": reason,
            })
            if agg is not None:
                agg.totalImportFailed += 1
            continue

        # filter date range (inclusive) — option A: still based on DTSTART only
        d = _parse_date_ymd(date)
        if d < df or d > dt:
            continue

        selected_events.append(IcsEvent(
            uid=uid,
            summary=summary,
            date=date,
            date_end=date_end,
            location_text=location_text,
        ))

    if failed_csv_path and failed_rows:
        _write_import_failed_csv(failed_csv_path, failed_rows)

    return selected_events


# (optional) keep the local debug block; no need to wire failure csv there
if __name__ == "__main__":
    cfg = None
    # CAREFUL: this block isn't used by makeMap.py; keep it minimal.
    with open("config.toml", "rb") as f:
        cfg = tomllib.load(f)

    output_dir = cfg["outputDir"]
    os.makedirs(output_dir, exist_ok=True)

    logger = Logger(os.path.join(output_dir, "log.txt"))
    ics_path = cfg["icsPath"]
    date_from = cfg["importICS"]["dateFrom"]
    date_to = cfg["importICS"]["dateTo"]
    require_location = cfg["importICS"].get("requireLocation", True)

    logger.info(f"Debug importICS: reading {ics_path}")
    events = load_events_from_ics(
        ics_path=ics_path,
        date_from=date_from,
        date_to=date_to,
        require_location=require_location,
        logger=logger,
        agg=None,
        failed_csv_path=os.path.join(output_dir, cfg["importICS"]["importFailedCsv"]),
    )
    logger.info(f"Debug importICS: selected events={len(events)}")
    print(f"Selected events: {len(events)}")
    