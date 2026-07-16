import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import os
import tomllib  # Python 3.11+
from loggingTools import Logger

from ics import Calendar


@dataclass
class IcsEvent:
    """
    Normalized event data needed for geocoding + map display.
    Time is ignored (YYYY-MM-DD only).
    """
    uid: Optional[str]
    summary: str
    date: str            # YYYY-MM-DD
    location_text: str  # human LOCATION from ICS


def _norm_ws(s: Optional[str]) -> str:
    """
    Normalize whitespace for stable caching and comparison.
    """
    return re.sub(r"\s+", " ", (s or "").strip())


def _to_yyyy_mm_dd(begin_value: str) -> str:
    """
    Convert ICS begin value to YYYY-MM-DD.
    Ignores the time part.

    Potential failure point:
    - ICS libraries may format begin_value differently depending on timezone handling.
    - We use regex patterns as a best-effort approach.
    """
    s = (begin_value or "").strip()

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


def load_events_from_ics(
    ics_path: str,
    date_from: str,
    date_to: str,
    require_location: bool = True,
) -> List[IcsEvent]:
    """
    Import ICS, select events by date, and extract LOCATION + date.
    """
    raw_text = open(ics_path, "r", encoding="utf-8").read()
    cal = Calendar(raw_text)

    df = _parse_date_ymd(date_from)
    dt = _parse_date_ymd(date_to)

    events: List[IcsEvent] = []

    for e in cal.events:
        summary = _norm_ws(getattr(e, "name", None))  # human title
        uid = getattr(e, "uid", None)

        location_text = _norm_ws(getattr(e, "location", None))
        if require_location and not location_text:
            continue

        begin_str = str(getattr(e, "begin", "") or "")
        date = _to_yyyy_mm_dd(begin_str)
        if not date:
            continue

        # filter date range (inclusive)
        d = _parse_date_ymd(date)
        if d < df or d > dt:
            continue

        events.append(IcsEvent(
            uid=uid,
            summary=summary,
            date=date,
            location_text=location_text
        ))

    return events

def _load_config():
    with open("config.toml", "rb") as f:
        return tomllib.load(f)

if __name__ == "__main__":
    cfg = _load_config()
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
    )
    logger.info(f"Debug importICS: selected events={len(events)}")
    print(f"Selected events: {len(events)}")
