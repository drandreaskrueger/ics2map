import csv
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class GeocodeResult:
    """
    Stores successful geocode output.
    """
    lat: float
    lon: float
    display_name: str
    country_code: str


class GeocodeCache:
    """
    Stores successful geocode results in a CSV-based key-value store.
    Key is the exact LOCATION text from the ICS.

    This allows:
    - never repeating successful Nominatim calls
    - re-running fast for future refinements
    """
    def __init__(self, cache_csv_path: str, logger=None):
        self.cache_csv_path = cache_csv_path
        self.logger = logger
        self._db: Dict[str, GeocodeResult] = {}

    def load(self):
        """
        Load existing cache CSV into memory.
        """
        if not os.path.exists(self.cache_csv_path):
            return

        with open(self.cache_csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["location_text"]
                self._db[key] = GeocodeResult(
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    display_name=row.get("display_name", "") or "",
                    country_code=(row.get("country_code", "") or "").strip()
                )

        if self.logger:
            self.logger.info(f"Loaded geocode cache entries: {len(self._db)}")

    def get(self, location_text: str) -> Optional[GeocodeResult]:
        """
        Return cached GeocodeResult if present.
        """
        return self._db.get(location_text)

    def set(self, location_text: str, result: GeocodeResult):
        """
        Store newly geocoded result into memory.
        """
        self._db[location_text] = result

    def save(self):
        """
        Write the full cache back to CSV.
        Note: This overwrites the file with updated content.
        """
        os.makedirs(os.path.dirname(self.cache_csv_path) or ".", exist_ok=True)
        with open(self.cache_csv_path, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["location_text", "lat", "lon", "display_name", "country_code"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for k, v in self._db.items():
                writer.writerow({
                    "location_text": k,
                    "lat": v.lat,
                    "lon": v.lon,
                    "display_name": v.display_name,
                    "country_code": v.country_code
                })