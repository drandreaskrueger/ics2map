import csv
import os
from dataclasses import dataclass
from typing import Dict, Optional


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
    CSV-based cache of successful geocodes.
    """

    def __init__(self, cache_csv_path: str, logger=None):
        self.cache_csv_path = cache_csv_path
        self.logger = logger
        self._db: Dict[str, GeocodeResult] = {}

        # counts for console/debug
        self.hit_count = 0
        self.miss_count = 0
        self.successful_lookup_count = 0

    def _norm_key(self, location_text: str) -> str:
        """
        Normalize cache key to improve hit rate.
        """
        return " ".join((location_text or "").split())

    def load(self):
        """
        Load existing cache CSV into memory.
        """
        abs_path = os.path.abspath(self.cache_csv_path)
        exists = os.path.exists(self.cache_csv_path)

        print(f"GeocodeCache.load(): path={abs_path} exists={exists}", flush=True)

        if not exists:
            self._db = {}
            return

        with open(self.cache_csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            loaded = 0
            for row in reader:
                raw_key = row.get("location_text", "")
                key = self._norm_key(raw_key)
                if not key:
                    continue

                self._db[key] = GeocodeResult(
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    display_name=row.get("display_name", "") or "",
                    country_code=(row.get("country_code", "") or "").strip(),
                )
                loaded += 1

        print(f"GeocodeCache.load(): loaded_entries={loaded}", flush=True)

        # reset counters on load
        self.hit_count = 0
        self.miss_count = 0
        self.successful_lookup_count = 0

    def get(self, location_text: str) -> Optional[GeocodeResult]:
        """
        Return cached GeocodeResult if present.
        """
        key = self._norm_key(location_text)
        if not key:
            self.miss_count += 1
            return None

        cached = self._db.get(key)
        if cached is None:
            self.miss_count += 1
            return None

        self.hit_count += 1
        # This is exactly "successful cache lookup" (we found and return a result)
        self.successful_lookup_count += 1
        return cached

    def set(self, location_text: str, result: GeocodeResult):
        key = self._norm_key(location_text)
        if not key:
            return
        self._db[key] = result

    def save(self):
        """
        Write the full cache back to CSV.
        """
        os.makedirs(os.path.dirname(self.cache_csv_path) or ".", exist_ok=True)
    
        with open(self.cache_csv_path, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["location_text", "lat", "lon", "display_name", "country_code"]
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                quotechar='"',
                quoting=csv.QUOTE_ALL,
            )
            writer.writeheader()
    
            for k, v in self._db.items():
                # CAREFUL: k is the normalized cache key used by get()/set().
                writer.writerow({
                    "location_text": k,
                    "lat": v.lat,
                    "lon": v.lon,
                    "display_name": v.display_name,
                    "country_code": v.country_code,
                })
    
        print(
            "GeocodeCache.save(): "
            f"entries={len(self._db)} hits={self.hit_count} "
            f"misses={self.miss_count} successful_cache_lookups={self.successful_lookup_count}",
            flush=True
        )
        
