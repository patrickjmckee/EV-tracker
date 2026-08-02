"""
Zip-to-zip great-circle distance using the static `zipcodes` dataset
(bundled data, no network). Used to drop out-of-radius "delivery"
listings that the sites return despite the search radius parameter.
"""
import math
from functools import lru_cache

import zipcodes


@lru_cache(maxsize=512)
def _zip_latlong(zip_code: str):
    try:
        matches = zipcodes.matching(str(zip_code).strip()[:5])
    except Exception:
        return None
    if not matches:
        return None
    m = matches[0]
    try:
        return float(m["lat"]), float(m["long"])
    except (KeyError, TypeError, ValueError):
        return None


def zip_distance_miles(zip_a: str, zip_b: str):
    """Miles between two US zips, or None if either can't be resolved."""
    a, b = _zip_latlong(zip_a), _zip_latlong(zip_b)
    if not a or not b:
        return None
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 3958.8 * 2 * math.asin(math.sqrt(h))
