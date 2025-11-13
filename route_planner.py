# route_planner.py
# Simple greedy nearest-neighbor route planner for a list of bins with lat/lon.
# Not a full TSP solver, but suitable for small fleets and on-the-fly prioritization.

from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict, Tuple

def haversine_distance(lat1, lon1, lat2, lon2):
    # returns kilometers
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def plan_route(start: Tuple[float,float], bins: List[Dict], top_n: int = None) -> List[Dict]:
    """
    start: (lat, lon) starting point (e.g., depot)
    bins: list of dicts with keys: bin_id, latitude, longitude, fill_percent
    returns ordered list of bins to visit
    Greedy nearest neighbor, picks next closest bin from current position.
    """
    if not bins:
        return []

    remaining = [b for b in bins if b.get("latitude") is not None and b.get("longitude") is not None]
    route = []
    current = {"latitude": start[0], "longitude": start[1]}

    # optionally sort by fill_percent first to prioritize the fullest bins; then greedy
    remaining.sort(key=lambda x: -float(x.get("fill_percent", 0)))
    if top_n:
        remaining = remaining[:top_n]

    while remaining:
        # find nearest
        nearest = min(remaining, key=lambda b: haversine_distance(current["latitude"], current["longitude"], b["latitude"], b["longitude"]))
        route.append(nearest)
        current = {"latitude": nearest["latitude"], "longitude": nearest["longitude"]}
        remaining.remove(nearest)

    return route
