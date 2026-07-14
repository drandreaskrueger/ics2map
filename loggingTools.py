import os
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class LogAgg:
    """
    Holds counters to print aggregate screen output at the end.
    """
    totalImportedEvents: int = 0
    totalSelectedEvents: int = 0
    totalGeocodeSucceeded: int = 0
    totalGeocodeFailed: int = 0
    totalGeocodeMissingLocation: int = 0


class Logger:
    """
    Minimal logger:
    - writes a line-per-action log to outputs/log.txt
    - screen output is aggregated (not per event)
    """
    def __init__(self, log_path: str):
        self.log_path = log_path
        self._ensure_parent_dir()

        # Create/overwrite at start
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(f"Log started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    def _ensure_parent_dir(self):
        parent = os.path.dirname(self.log_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def info(self, msg: str):
        """
        Write an informational line to log.txt and flush immediately.
        """
        self._write("INFO", msg)

    def warn(self, msg: str):
        """
        Write a warning line to log.txt.
        """
        self._write("WARN", msg)

    def error(self, msg: str):
        """
        Write an error line to log.txt.
        """
        self._write("ERROR", msg)

    def _write(self, level: str, msg: str):
        line = f"{level} {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)


def load_aggregates_snapshot(agg: LogAgg) -> str:
    """
    Human readable aggregate snapshot for screen output.
    """
    return (
        f"Imported: {agg.totalImportedEvents}, "
        f"Selected: {agg.totalSelectedEvents}, "
        f"Geocode OK: {agg.totalGeocodeSucceeded}, "
        f"Geocode FAIL: {agg.totalGeocodeFailed}, "
        f"Missing location: {agg.totalGeocodeMissingLocation}"
    )