"""
data_loader.py
==============
Data ingestion for the Dark Store Placement Intelligence project.
Loads existing dark store locations and generates ward demand data
for Delhi-NCR.

Author: Ishaan Mankotia
"""

import os
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

# Delhi-NCR bounding box (wider than Delhi-only to include Gurgaon, Noida)
DELHI_NCR_BBOX = (28.35, 76.78, 28.92, 77.52)


# ─────────────────────────────────────────────
# DARK STORE LOCATIONS
# ─────────────────────────────────────────────

def fetch_dark_stores() -> gpd.GeoDataFrame:
    """
    Fetches existing quick-commerce dark store / fulfillment centre
    locations in Delhi-NCR from OpenStreetMap.
    Falls back to a realistic seed dataset if OSM is unavailable.

    Returns:
        GeoDataFrame with columns: name, brand, lat, lon, geometry
    """
    query = """
    [out:json][timeout:30];
    (
      node["shop"="supermarket"]["brand"~"Blinkit|Zepto|Instamart|BigBasket|JioMart",i]
          (28.35,76.78,28.92,77.52);
      node["amenity"="fast_food"]["brand"~"Blinkit|Zepto|Swiggy",i]
          (28.35,76.78,28.92,77.52);
    );
    out body;
    """
    try:
        print("📡 Fetching dark store locations from OpenStreetMap...")
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=35)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])

        if len(elements) >= 5:
            records = []
            for el in elements:
                tags = el.get("tags", {})
                records.append({
                    "name":   tags.get("name", "Dark Store"),
                    "brand":  tags.get("brand", "Unknown"),
                    "lat":    el["lat"],
                    "lon":    el["lon"],
                })
            gdf = gpd.GeoDataFrame(
                records,
                geometry=[Point(r["lon"], r["lat"]) for r in records],
                crs="EPSG:4326"
            )
            print(f"✅ Loaded {len(gdf)} dark stores from OSM.")
            return gdf

    except Exception as e:
        print(f"⚠️  OSM fetch failed ({e}). Using fallback seed data.")

    return _fallback_dark_stores()


def _fallback_dark_stores() -> gpd.GeoDataFrame:
    """
    Realistic seed of ~80 dark store locations across Delhi-NCR
    reflecting approximate Blinkit / Zepto / Instamart coverage
    as of early 2026. Concentrated in South Delhi, Central Delhi,
    Noida Sector 18–62 corridor, and Gurgaon Sector 29–56.
    """
    stores = [
        # ── South Delhi (dense coverage) ────────────────────────────────
        {"name": "Blinkit Saket",          "brand": "Blinkit",  "lat": 28.5244, "lon": 77.2165},
        {"name": "Blinkit Malviya Nagar",  "brand": "Blinkit",  "lat": 28.5328, "lon": 77.2101},
        {"name": "Zepto Hauz Khas",        "brand": "Zepto",    "lat": 28.5433, "lon": 77.2070},
        {"name": "Instamart GK-1",         "brand": "Instamart","lat": 28.5497, "lon": 77.2291},
        {"name": "Blinkit GK-2",           "brand": "Blinkit",  "lat": 28.5390, "lon": 77.2393},
        {"name": "Zepto Lajpat Nagar",     "brand": "Zepto",    "lat": 28.5675, "lon": 77.2434},
        {"name": "Blinkit Kalkaji",        "brand": "Blinkit",  "lat": 28.5500, "lon": 77.2573},
        {"name": "Zepto Nehru Place",      "brand": "Zepto",    "lat": 28.5481, "lon": 77.2520},
        {"name": "Instamart Sarita Vihar", "brand": "Instamart","lat": 28.5299, "lon": 77.2891},
        {"name": "Blinkit Vasant Kunj",    "brand": "Blinkit",  "lat": 28.5199, "lon": 77.1585},
        {"name": "Zepto Vasant Vihar",     "brand": "Zepto",    "lat": 28.5655, "lon": 77.1676},
        {"name": "Blinkit RK Puram",       "brand": "Blinkit",  "lat": 28.5670, "lon": 77.1850},
        # ── Central Delhi ───────────────────────────────────────────────
        {"name": "Blinkit Connaught Place","brand": "Blinkit",  "lat": 28.6315, "lon": 77.2167},
        {"name": "Zepto Karol Bagh",       "brand": "Zepto",    "lat": 28.6519, "lon": 77.1903},
        {"name": "Instamart Laxmi Nagar",  "brand": "Instamart","lat": 28.6285, "lon": 77.2760},
        {"name": "Blinkit Janakpuri",      "brand": "Blinkit",  "lat": 28.6290, "lon": 77.0814},
        {"name": "Zepto Dwarka Sec 10",    "brand": "Zepto",    "lat": 28.5850, "lon": 77.0610},
        {"name": "Blinkit Punjabi Bagh",   "brand": "Blinkit",  "lat": 28.6674, "lon": 77.1315},
        {"name": "Zepto Rajouri Garden",   "brand": "Zepto",    "lat": 28.6476, "lon": 77.1219},
        # ── North Delhi ─────────────────────────────────────────────────
        {"name": "Blinkit Rohini Sec 7",   "brand": "Blinkit",  "lat": 28.7025, "lon": 77.1209},
        {"name": "Zepto Pitampura",        "brand": "Zepto",    "lat": 28.7005, "lon": 77.1336},
        {"name": "Instamart Model Town",   "brand": "Instamart","lat": 28.7025, "lon": 77.1916},
        # ── East Delhi ──────────────────────────────────────────────────
        {"name": "Blinkit Preet Vihar",    "brand": "Blinkit",  "lat": 28.6400, "lon": 77.2978},
        {"name": "Zepto Patparganj",       "brand": "Zepto",    "lat": 28.6233, "lon": 77.2980},
        {"name": "Instamart Mayur Vihar",  "brand": "Instamart","lat": 28.6083, "lon": 77.2958},
        {"name": "Blinkit Shahdara",       "brand": "Blinkit",  "lat": 28.6673, "lon": 77.2893},
        # ── Noida ───────────────────────────────────────────────────────
        {"name": "Blinkit Noida Sec 18",   "brand": "Blinkit",  "lat": 28.5706, "lon": 77.3210},
        {"name": "Zepto Noida Sec 62",     "brand": "Zepto",    "lat": 28.6249, "lon": 77.3702},
        {"name": "Instamart Noida Sec 50", "brand": "Instamart","lat": 28.5991, "lon": 77.3476},
        {"name": "Blinkit Noida Sec 29",   "brand": "Blinkit",  "lat": 28.5782, "lon": 77.3346},
        {"name": "Zepto Noida Sec 44",     "brand": "Zepto",    "lat": 28.5657, "lon": 77.3577},
        {"name": "Blinkit Greater Noida",  "brand": "Blinkit",  "lat": 28.4744, "lon": 77.5040},
        # ── Gurgaon ─────────────────────────────────────────────────────
        {"name": "Blinkit Gurgaon Sec 29", "brand": "Blinkit",  "lat": 28.4728, "lon": 77.0740},
        {"name": "Zepto Gurgaon Sec 56",   "brand": "Zepto",    "lat": 28.4204, "lon": 77.0899},
        {"name": "Instamart Golf Course Rd","brand":"Instamart", "lat": 28.4596, "lon": 77.0982},
        {"name": "Blinkit DLF Cyber City", "brand": "Blinkit",  "lat": 28.4953, "lon": 77.0884},
        {"name": "Zepto Sohna Road",       "brand": "Zepto",    "lat": 28.4198, "lon": 77.0441},
        {"name": "Blinkit Palam Vihar",    "brand": "Blinkit",  "lat": 28.5219, "lon": 77.0315},
    ]

    gdf = gpd.GeoDataFrame(
        stores,
        geometry=[Point(s["lon"], s["lat"]) for s in stores],
        crs="EPSG:4326"
    )
    print(f"✅ Loaded {len(gdf)} dark stores from fallback seed data.")
    return gdf


# ─────────────────────────────────────────────
# DEMAND ZONE GRID
# ─────────────────────────────────────────────

def generate_demand_grid(n_zones: int = 150) -> gpd.GeoDataFrame:
    """
    Generates a grid of demand zones across Delhi-NCR with:
    - Population density (parametric model)
    - Income/spending power proxy (0–1)
    - Delivery demand proxy (food delivery density signal)
    - Zone classification

    Args:
        n_zones: Approximate number of grid cells

    Returns:
        GeoDataFrame of zone polygons with demand attributes
    """
    south, west, north, east = DELHI_NCR_BBOX
    np.random.seed(42)

    lat_steps = int(np.sqrt(n_zones * (north - south) / (east - west)))
    lon_steps = int(n_zones / lat_steps)

    lats = np.linspace(south, north, lat_steps + 1)
    lons = np.linspace(west, east, lon_steps + 1)

    # Key city centers for density model
    centers = [
        (28.6139, 77.2090, 1.0),   # Delhi CP — highest
        (28.4595, 77.0266, 0.85),  # Gurgaon
        (28.5355, 77.3910, 0.80),  # Noida
        (28.7041, 77.1025, 0.60),  # Rohini
    ]

    records = []
    zone_id = 1

    for i in range(len(lats) - 1):
        for j in range(len(lons) - 1):
            lat_c = (lats[i] + lats[i + 1]) / 2
            lon_c = (lons[j] + lons[j + 1]) / 2

            # Multi-center density model
            density = 0
            for clat, clon, weight in centers:
                dist = ((lat_c - clat) ** 2 + (lon_c - clon) ** 2) ** 0.5
                density += weight * 30000 * np.exp(-dist * 18)

            density = max(300, density + np.random.normal(0, 2500))
            density = min(density, 75000)

            # Income proxy: higher in South Delhi, Gurgaon, Noida SEC A
            dist_cp = ((lat_c - 28.6139) ** 2 + (lon_c - 77.2090) ** 2) ** 0.5
            dist_ggn = ((lat_c - 28.4595) ** 2 + (lon_c - 77.0266) ** 2) ** 0.5
            income = max(0.1, min(1.0,
                0.5 + 0.3 * (lat_c < 28.57) +   # South Delhi
                0.25 * (dist_ggn < 0.12) +        # Gurgaon core
                np.random.normal(0, 0.08)
            ))

            # Delivery demand proxy (correlated with income + density)
            delivery_demand = max(0, income * density / 25000 + np.random.exponential(0.4))

            # Zone type
            dist_any_center = min(
                ((lat_c - clat) ** 2 + (lon_c - clon) ** 2) ** 0.5
                for clat, clon, _ in centers
            )
            if dist_any_center < 0.08:      zone_type = "Metro Core"
            elif dist_any_center < 0.20:    zone_type = "Urban"
            elif dist_any_center < 0.35:    zone_type = "Suburban"
            else:                            zone_type = "Peri-urban"

            poly = Polygon([
                (lons[j],     lats[i]),
                (lons[j + 1], lats[i]),
                (lons[j + 1], lats[i + 1]),
                (lons[j],     lats[i + 1]),
            ])

            records.append({
                "zone_id":          f"Z{zone_id:03d}",
                "lat_center":       round(lat_c, 5),
                "lon_center":       round(lon_c, 5),
                "zone_type":        zone_type,
                "population_density": round(density, 0),
                "income_proxy":     round(income, 3),
                "delivery_demand":  round(delivery_demand, 3),
                "area_km2":         round(110 * (lats[i+1]-lats[i]) * 111 * (lons[j+1]-lons[j]), 2),
                "geometry":         poly,
            })
            zone_id += 1

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    print(f"✅ Generated {len(gdf)} demand zones across Delhi-NCR.")
    return gdf


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    stores = fetch_dark_stores()
    zones  = generate_demand_grid()
    print(f"\nBrand breakdown:\n{stores['brand'].value_counts().to_string()}")
    print(f"\nZone type breakdown:\n{zones['zone_type'].value_counts().to_string()}")
