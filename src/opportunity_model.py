"""
opportunity_model.py
====================
Dark Store Opportunity Index (DSOI) scoring model.

DSOI = 0.35 × density_score
     + 0.35 × distance_score
     + 0.20 × income_score
     + 0.10 × delivery_demand_score

Higher DSOI = bigger whitespace opportunity = higher expansion priority.

Author: Ishaan Mankotia
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.preprocessing import MinMaxScaler

TIER_ORDER = ["Covered", "Excluded (Low Density)", "Low Opportunity",
              "Medium Opportunity", "High Opportunity"]


# ─────────────────────────────────────────────
# COVERAGE DISTANCE
# ─────────────────────────────────────────────

def compute_nearest_store_distance(zones: gpd.GeoDataFrame,
                                   stores: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Computes straight-line distance (km) from each zone centroid
    to the nearest existing dark store.

    Args:
        zones  : Demand zone GeoDataFrame (EPSG:4326)
        stores : Dark store GeoDataFrame (EPSG:4326)

    Returns:
        zones with 'nearest_store_name' and 'nearest_store_dist_km' columns
    """
    zones_proj  = zones.copy().to_crs("EPSG:32643")
    stores_proj = stores.copy().to_crs("EPSG:32643")

    centroids    = zones_proj.geometry.centroid
    store_coords = np.array([(p.x, p.y) for p in stores_proj.geometry])
    store_names  = stores_proj["name"].values

    nearest_names, nearest_dists = [], []

    for centroid in centroids:
        dists = np.sqrt((store_coords[:, 0] - centroid.x) ** 2 +
                        (store_coords[:, 1] - centroid.y) ** 2)
        idx = np.argmin(dists)
        nearest_names.append(store_names[idx])
        nearest_dists.append(round(dists[idx] / 1000, 3))

    zones = zones.copy()
    zones["nearest_store_name"]    = nearest_names
    zones["nearest_store_dist_km"] = nearest_dists
    return zones


def flag_covered_zones(zones: gpd.GeoDataFrame,
                       coverage_radius_km: float = 1.5) -> gpd.GeoDataFrame:
    """
    Marks zones as covered if within coverage_radius_km of a dark store.
    Standard quick-commerce delivery radius is 1.5–2km.
    """
    zones = zones.copy()
    zones["store_covered"] = zones["nearest_store_dist_km"] <= coverage_radius_km
    covered = zones["store_covered"].sum()
    print(f"📍 {covered}/{len(zones)} zones within {coverage_radius_km}km of a dark store.")
    return zones


# ─────────────────────────────────────────────
# DSOI SCORING
# ─────────────────────────────────────────────

def compute_dsoi(zones: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Computes the Dark Store Opportunity Index for each zone.

    Formula:
        DSOI = 0.35 × density_norm
             + 0.35 × distance_norm
             + 0.20 × income_norm
             + 0.10 × delivery_demand_norm

    Covered zones receive DSOI = 0.

    Returns:
        zones with dsoi_score (0–100) and dsoi_tier columns
    """
    zones  = zones.copy()
    scaler = MinMaxScaler()

    # Cap distance at 6km before normalising. Beyond this radius a zone is
    # realistically outside any feasible quick-commerce expansion radius for
    # a single new store, so further distance shouldn't keep inflating the
    # score — otherwise near-empty peri-urban cells at the edge of the NCR
    # bounding box (300-700 people/km², 30km+ from any store) outrank
    # genuinely dense, moderately-underserved metro-core zones.
    DIST_CAP_KM = 6.0
    zones["distance_capped"] = zones["nearest_store_dist_km"].clip(upper=DIST_CAP_KM)

    # Exclude near-empty cells (population_density < 3,000/km²) from ranking.
    # In the synthetic grid these are open land / undeveloped periphery, not
    # real residential catchments a quick-commerce operator would evaluate.
    zones["is_negligible_density"] = zones["population_density"] < 3000

    zones["density_norm"]  = scaler.fit_transform(zones[["population_density"]])
    zones["distance_norm"] = scaler.fit_transform(zones[["distance_capped"]])
    zones["income_norm"]   = scaler.fit_transform(zones[["income_proxy"]])
    zones["demand_norm"]   = scaler.fit_transform(zones[["delivery_demand"]])

    zones["dsoi_raw"] = (
        0.35 * zones["density_norm"]  +
        0.35 * zones["distance_norm"] +
        0.20 * zones["income_norm"]   +
        0.10 * zones["demand_norm"]
    )

    # Zero out covered zones
    zones.loc[zones["store_covered"], "dsoi_raw"] = 0.0
    zones.loc[zones["is_negligible_density"], "dsoi_raw"] = 0.0

    max_dsoi = zones["dsoi_raw"].max()
    zones["dsoi_score"] = (zones["dsoi_raw"] / max_dsoi * 100).round(1)

    tier = pd.cut(
        zones["dsoi_score"],
        bins=[-1, 35, 60, 100],
        labels=["Low Opportunity", "Medium Opportunity", "High Opportunity"]
    ).astype(str)
    # Zeroed zones get an explicit reason instead of a misleading score tier:
    # "Covered" = inside an existing store's radius, "Excluded" = below the
    # density floor (open land / periphery, never a candidate).
    tier[zones["is_negligible_density"]] = "Excluded (Low Density)"
    tier[zones["store_covered"]] = "Covered"
    zones["dsoi_tier"] = pd.Categorical(tier, categories=TIER_ORDER, ordered=True)

    print(f"\n📊 DSOI Tier Distribution:")
    print(zones["dsoi_tier"].value_counts().to_string())
    return zones


# ─────────────────────────────────────────────
# TOP-N EXPANSION ZONES
# ─────────────────────────────────────────────

def get_top_expansion_zones(zones: gpd.GeoDataFrame,
                             n: int = 10) -> gpd.GeoDataFrame:
    """Returns top N zones by DSOI score."""
    top = (zones[~zones["store_covered"] & ~zones["is_negligible_density"]]
           .sort_values("dsoi_score", ascending=False)
           .head(n)
           .copy())
    top["expansion_rank"] = range(1, len(top) + 1)

    print(f"\n🏆 Top {n} Dark Store Expansion Zones:")
    print(top[["expansion_rank", "zone_id", "zone_type",
               "population_density", "nearest_store_dist_km",
               "income_proxy", "dsoi_score"]].to_string(index=False))
    return top


# ─────────────────────────────────────────────
# ORDER DEMAND ESTIMATION
# ─────────────────────────────────────────────

def estimate_order_demand(top_zones: gpd.GeoDataFrame,
                          orders_per_1000_high_income: float = 8.0,
                          orders_per_1000_mid_income: float  = 4.0,
                          avg_order_value_inr: float          = 380.0,
                          catchment_radius_km: float          = 1.5) -> pd.DataFrame:
    """
    Estimates daily order potential and GMV for each top zone at two levels:

    1. Zone potential  : every resident of the ~34 km² grid cell. An upper
                         bound - one store cannot serve all of it.
    2. Single-store    : residents inside ONE new store's delivery radius
       capture         (pi x r² = 7.07 km² at r = 1.5 km). This is the headline
                         figure and the one comparable to a real store.

    Income segmentation:
    - income_proxy >= 0.6 -> high income rate (8 orders/1000/day)
    - income_proxy <  0.6 -> mid income rate  (4 orders/1000/day)
    """
    df = top_zones[["expansion_rank", "zone_id", "zone_type",
                    "lat_center", "lon_center", "nearest_store_name",
                    "nearest_store_dist_km", "population_density", "area_km2",
                    "income_proxy", "dsoi_score"]].copy()

    rate = np.where(df["income_proxy"] >= 0.6,
                    orders_per_1000_high_income, orders_per_1000_mid_income)
    df["daily_order_rate"] = rate

    # Zone-level ceiling (whole grid cell)
    df["zone_population"] = (df["population_density"] * df["area_km2"]).round(0).astype(int)
    df["zone_potential_daily_orders"] = (df["zone_population"] * rate / 1000).round(0).astype(int)

    # Single-store capture (one store's delivery radius)
    catchment_km2 = np.minimum(np.pi * catchment_radius_km ** 2, df["area_km2"])
    df["catchment_km2"]       = catchment_km2.round(2)
    df["est_population"]      = (df["population_density"] * catchment_km2).round(0).astype(int)
    df["est_daily_orders"]    = (df["est_population"] * rate / 1000).round(0).astype(int)
    df["est_daily_gmv_inr"]   = (df["est_daily_orders"] * avg_order_value_inr).round(0).astype(int)
    df["est_monthly_gmv_inr"] = (df["est_daily_gmv_inr"] * 30).round(0).astype(int)
    df["est_annual_gmv_inr"]  = (df["est_daily_gmv_inr"] * 365).round(0).astype(int)

    print(f"\n💰 Order Demand Estimates (one store per zone, {catchment_radius_km} km radius):")
    print(df[["expansion_rank", "zone_id", "est_population", "est_daily_orders",
              "est_monthly_gmv_inr", "zone_potential_daily_orders"]].to_string(index=False))
    print(f"\n  Total est. daily orders (10 new stores): {df['est_daily_orders'].sum():,}")
    print(f"  Total est. monthly GMV: ₹{df['est_monthly_gmv_inr'].sum():,.0f}")
    print(f"  Total est. annual GMV:  ₹{df['est_annual_gmv_inr'].sum():,.0f}")
    print(f"  (Zone-level ceiling: {df['zone_potential_daily_orders'].sum():,} orders/day)")
    return df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import fetch_dark_stores, generate_demand_grid

    print("=" * 60)
    print("  Dark Store Placement Intelligence — Full Pipeline")
    print("=" * 60)

    stores = fetch_dark_stores()
    zones  = generate_demand_grid()
    zones  = compute_nearest_store_distance(zones, stores)
    zones  = flag_covered_zones(zones, coverage_radius_km=1.5)
    zones  = compute_dsoi(zones)
    top10  = get_top_expansion_zones(zones, n=10)
    demand = estimate_order_demand(top10)

    out = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out, exist_ok=True)
    top10.drop(columns="geometry").to_csv(os.path.join(out, "top10_expansion_zones.csv"), index=False)
    demand.to_csv(os.path.join(out, "order_demand_estimates.csv"), index=False)
    print("\n✅ Outputs saved.")
