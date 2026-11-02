"""
visualizer.py
=============
Generates all visual outputs for Dark Store Placement Intelligence:
  1. Interactive Folium opportunity map
  2. DSOI distribution charts
  3. Coverage gap analysis chart

Author: Ishaan Mankotia
"""

import os
import folium
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from folium.plugins import MiniMap

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

TIER_COLORS = {
    "Covered":             "#2ECC71",
    "Excluded (Low Density)": "#BDC3C7",
    "Low Opportunity":     "#F1C40F",
    "Medium Opportunity":  "#E67E22",
    "High Opportunity":    "#E74C3C",
}

BRAND_COLORS = {
    "Blinkit":   "#FFD700",
    "Zepto":     "#7C3AED",
    "Instamart": "#FF6B35",
    "Unknown":   "#888888",
}


def create_opportunity_map(zones: gpd.GeoDataFrame,
                            stores: gpd.GeoDataFrame,
                            top_zones: gpd.GeoDataFrame,
                            output_path: str = None) -> folium.Map:
    """
    Creates interactive Folium map with:
    - Zone choropleth by DSOI tier
    - Existing dark store markers with delivery radius rings
    - Top 10 expansion zone ranked markers
    """
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "dark_store_opportunity_map.html")

    m = folium.Map(
        location=[28.55, 77.20],
        zoom_start=10,
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        attr="&copy; OpenStreetMap contributors &copy; CARTO"
    )

    # ── Layer 1: Zone choropleth ─────────────────────────────────────
    zone_layer = folium.FeatureGroup(name="Demand Zones (DSOI)", show=True)
    for _, zone in zones.iterrows():
        tier   = str(zone.get("dsoi_tier", "Low Opportunity"))
        score  = float(zone.get("dsoi_score", 0))
        color  = TIER_COLORS.get(tier, "#aaaaaa")
        opacity = {"Covered": 0.10, "Excluded (Low Density)": 0.08, "Low Opportunity": 0.30,
                   "Medium Opportunity": 0.50, "High Opportunity": 0.70}.get(tier, 0.3)

        tooltip_html = f"""
        <b>{zone.get('zone_id', '')}</b><br>
        DSOI Score: <b>{score:.1f} / 100</b> ({tier})<br>
        Pop. density: {int(zone.get('population_density', 0)):,}/km²<br>
        Nearest store: {zone.get('nearest_store_name', '')} ({zone.get('nearest_store_dist_km', 0):.1f} km)<br>
        Income proxy: {zone.get('income_proxy', 0):.2f}
        """
        try:
            folium.GeoJson(
                zone["geometry"].__geo_interface__,
                style_function=lambda x, c=color, o=opacity: {
                    "fillColor": c, "color": "#444", "weight": 0.4, "fillOpacity": o
                },
                tooltip=folium.Tooltip(tooltip_html, sticky=True),
            ).add_to(zone_layer)
        except Exception:
            pass
    zone_layer.add_to(m)

    # ── Layer 2: Existing dark stores ───────────────────────────────
    store_layer = folium.FeatureGroup(name="Existing Dark Stores", show=True)
    for _, store in stores.iterrows():
        lat, lon = store.geometry.y, store.geometry.x
        brand    = store.get("brand", "Unknown")
        color    = BRAND_COLORS.get(brand, "#888888")

        folium.Circle(
            location=[lat, lon], radius=1500,
            color=color, weight=1, fill=True,
            fill_color=color, fill_opacity=0.07,
            tooltip=f"1.5km delivery radius"
        ).add_to(store_layer)

        folium.CircleMarker(
            location=[lat, lon], radius=6,
            color="white", weight=1.5,
            fill=True, fill_color=color, fill_opacity=0.95,
            tooltip=f"🏪 {store.get('name', brand)} ({brand})",
        ).add_to(store_layer)

    store_layer.add_to(m)

    # ── Layer 3: Top expansion zones ────────────────────────────────
    top_layer = folium.FeatureGroup(name="Top 10 Expansion Zones", show=True)
    for _, zone in top_zones.iterrows():
        lat  = zone.get("lat_center", zone.geometry.centroid.y)
        lon  = zone.get("lon_center", zone.geometry.centroid.x)
        rank = int(zone.get("expansion_rank", 0))

        popup_html = f"""
        <div style='font-family:Arial;min-width:210px'>
            <h4 style='color:#C0392B;margin:4px 0'>#{rank} — {zone.get('zone_id','')}</h4>
            <hr style='margin:4px 0'>
            <b>DSOI Score:</b> {zone.get('dsoi_score',0):.1f} / 100<br>
            <b>Zone type:</b> {zone.get('zone_type','')}<br>
            <b>Pop. density:</b> {int(zone.get('population_density',0)):,}/km²<br>
            <b>Nearest store:</b> {zone.get('nearest_store_dist_km',0):.1f} km away<br>
            <b>Income proxy:</b> {zone.get('income_proxy',0):.2f}<br>
            <b>Est. daily orders (1 store):</b> {int(zone.get('est_daily_orders', 0)):,}<br>
            <b>Est. monthly GMV:</b> &#8377;{zone.get('est_monthly_gmv_inr', 0)/1e5:,.1f} L
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f"""<div style='
                    background:#C0392B;color:white;border-radius:50%;
                    width:26px;height:26px;text-align:center;line-height:26px;
                    font-weight:bold;font-size:12px;border:2px solid white;
                    box-shadow:1px 1px 4px rgba(0,0,0,0.4)'>{rank}</div>""",
                icon_size=(26, 26), icon_anchor=(13, 13),
            ),
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"#{rank} Expansion Zone — DSOI: {zone.get('dsoi_score',0):.1f}",
        ).add_to(top_layer)
    top_layer.add_to(m)

    # ── Legend ──────────────────────────────────────────────────────
    legend_html = """
    <div style='position:fixed;bottom:40px;left:40px;z-index:1000;
                background:white;padding:14px 18px;border-radius:8px;
                box-shadow:2px 2px 8px rgba(0,0,0,0.25);font-family:Arial;font-size:13px'>
        <b>Dark Store Opportunity Index</b><br><br>
        <span style='background:#E74C3C;display:inline-block;width:14px;height:14px;border-radius:2px'></span>&nbsp; High Opportunity<br>
        <span style='background:#E67E22;display:inline-block;width:14px;height:14px;border-radius:2px'></span>&nbsp; Medium Opportunity<br>
        <span style='background:#F1C40F;display:inline-block;width:14px;height:14px;border-radius:2px'></span>&nbsp; Low Opportunity<br>
        <span style='background:#2ECC71;display:inline-block;width:14px;height:14px;border-radius:2px'></span>&nbsp; Already Covered (&le;1.5 km)<br>
        <span style='background:#BDC3C7;display:inline-block;width:14px;height:14px;border-radius:2px'></span>&nbsp; Excluded (&lt;3,000/km&sup2;)<br><br>
        <span style='background:#FFD700;display:inline-block;width:10px;height:10px;border-radius:50%'></span>&nbsp; Blinkit &nbsp;
        <span style='background:#7C3AED;display:inline-block;width:10px;height:10px;border-radius:50%'></span>&nbsp; Zepto &nbsp;
        <span style='background:#FF6B35;display:inline-block;width:10px;height:10px;border-radius:50%'></span>&nbsp; Instamart
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    title_html = """
    <div style='position:fixed;top:15px;left:50%;transform:translateX(-50%);z-index:1000;
                background:rgba(255,255,255,0.95);padding:10px 20px;border-radius:8px;
                box-shadow:2px 2px 8px rgba(0,0,0,0.2);font-family:Arial;
                font-size:16px;font-weight:bold;color:#1A252F'>
        🛒 Dark Store Placement Intelligence — Delhi-NCR Opportunity Map
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    folium.LayerControl(collapsed=False).add_to(m)
    MiniMap(toggle_display=True).add_to(m)

    m.save(output_path)
    print(f"🗺️  Interactive map saved: {output_path}")
    return m


def plot_coverage_analysis(zones: gpd.GeoDataFrame,
                            stores: gpd.GeoDataFrame,
                            output_path: str = None) -> None:
    """Bar + pie charts showing coverage gaps by zone type and brand distribution."""
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "coverage_analysis.png")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Dark Store Coverage Analysis — Delhi-NCR", fontsize=14, fontweight="bold")

    # Coverage by zone type
    ax1 = axes[0]
    ct = (zones.groupby(["zone_type", "store_covered"]).size()
          .unstack(fill_value=0).reindex(columns=[False, True], fill_value=0))
    ct.columns = ["Uncovered", "Covered"]
    ct.plot.bar(ax=ax1, color=["#E74C3C", "#2ECC71"], edgecolor="white", stacked=True)
    ax1.set_title("Coverage by Zone Type")
    ax1.set_xlabel(""); ax1.tick_params(rotation=15)
    ax1.legend(loc="upper right")
    ax1.grid(axis="y", alpha=0.3)

    # DSOI tier distribution
    ax2 = axes[1]
    tier_order = ["High Opportunity", "Medium Opportunity", "Low Opportunity",
                  "Excluded (Low Density)", "Covered"]
    counts = zones["dsoi_tier"].value_counts().reindex(tier_order, fill_value=0)
    colors = [TIER_COLORS[t] for t in tier_order]
    bars = ax2.barh(tier_order, counts.values, color=colors, edgecolor="white")
    for bar, val in zip(bars, counts.values):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                 str(val), va="center", fontsize=10)
    ax2.set_title("Zones by DSOI Tier")
    ax2.set_xlabel("Number of Zones")
    ax2.grid(axis="x", alpha=0.3)

    # Brand market share
    ax3 = axes[2]
    brand_counts = stores["brand"].value_counts()
    colors_pie = [BRAND_COLORS.get(b, "#888") for b in brand_counts.index]
    ax3.pie(brand_counts.values, labels=brand_counts.index,
            colors=colors_pie, autopct="%1.0f%%", startangle=90)
    ax3.set_title("Dark Store Brand Distribution")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 Coverage analysis chart saved: {output_path}")


def plot_opportunity_scatter(zones: gpd.GeoDataFrame,
                              top_zones: gpd.GeoDataFrame = None,
                              output_path: str = None) -> None:
    """Scatter: population density vs. distance to nearest store, coloured by DSOI tier."""
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "opportunity_scatter.png")

    fig, ax = plt.subplots(figsize=(10, 6))
    tier_order = ["Excluded (Low Density)", "Covered", "Low Opportunity",
                  "Medium Opportunity", "High Opportunity"]

    for tier in tier_order:
        subset = zones[zones["dsoi_tier"].astype(str) == tier]
        ax.scatter(subset["nearest_store_dist_km"],
                   subset["population_density"] / 1000,
                   c=TIER_COLORS[tier], label=tier,
                   alpha=0.55, s=22, edgecolors="none")

    if top_zones is not None and len(top_zones):
        ax.scatter(top_zones["nearest_store_dist_km"],
                   top_zones["population_density"] / 1000,
                   c="black", s=100, marker="*", zorder=5, label="Top 10 Expansion Zones")
        for _, z in top_zones.iterrows():
            ax.annotate(f"#{int(z['expansion_rank'])}",
                        (z["nearest_store_dist_km"], z["population_density"] / 1000),
                        textcoords="offset points", xytext=(5, 3),
                        fontsize=8, color="#C0392B")

    ax.set_xlabel("Distance to Nearest Dark Store (km)", fontsize=11)
    ax.set_ylabel("Population Density (thousands/km²)", fontsize=11)
    ax.set_title("Population Density vs. Dark Store Accessibility\n"
                 "Top-right quadrant = highest opportunity zones",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, framealpha=0.8)
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📈 Opportunity scatter saved: {output_path}")
