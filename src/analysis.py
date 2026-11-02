"""
analysis.py
===========
Reporting layer for Dark Store Placement Intelligence. Runs on top of the
existing model (opportunity_model.py) and adds:

  * Sensitivity analysis  - 1,000 random weight draws around the base
                            weights, plus coverage-radius and density-floor
                            sweeps, to test how stable the top 10 is.
  * Static figures        - outputs/figures/*.png
  * Excel what-if model   - outputs/excel/Dark_Store_Expansion_Model.xlsx
                            (live formulas: basket size, order rates, radius)
  * PDF strategy brief    - outputs/Dark_Store_Strategy_Brief.pdf

Run everything with:  python src/run_all.py

Author: Ishaan Mankotia
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages

from opportunity_model import (compute_nearest_store_distance, flag_covered_zones,
                               compute_dsoi, get_top_expansion_zones,
                               estimate_order_demand, TIER_ORDER)

ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT     = os.path.join(ROOT, "outputs")
FIG     = os.path.join(OUT, "figures")
XL_DIR  = os.path.join(OUT, "excel")

BASE_WEIGHTS = {"density": 0.35, "distance": 0.35, "income": 0.20, "demand": 0.10}
NORM_COLS    = {"density": "density_norm", "distance": "distance_norm",
                "income": "income_norm", "demand": "demand_norm"}

# ── Palette (validated reference palette; sequential blue for ordinal tiers) ──
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
SURFACE = "#fcfcfb"
TIER_FILL = {
    "Covered":                "#1baf7a",   # aqua: already served
    "Excluded (Low Density)": "#ecebe7",   # neutral: never a candidate
    "Low Opportunity":        "#b7d3f6",   # blue 150
    "Medium Opportunity":     "#5598e7",   # blue 350
    "High Opportunity":       "#1c5cab",   # blue 550
}
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # categorical slots 1-4
ORANGE = "#eb6834"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": False, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "legend.frameon": False,
})


# ─────────────────────────────────────────────
# CORE RUN
# ─────────────────────────────────────────────

def run_model(stores, zones_raw, radius_km=1.5):
    zones = compute_nearest_store_distance(zones_raw, stores)
    zones = flag_covered_zones(zones, coverage_radius_km=radius_km)
    zones = compute_dsoi(zones)
    top10 = get_top_expansion_zones(zones, n=10)
    demand = estimate_order_demand(top10, catchment_radius_km=radius_km)
    top10 = top10.merge(demand[["zone_id", "est_daily_orders", "est_monthly_gmv_inr",
                                "zone_potential_daily_orders"]], on="zone_id")
    return zones, top10, demand


def _rescore(zones, w, density_floor=3000, covered=None):
    """Re-score with arbitrary weights; returns ranked eligible zone_ids."""
    raw = sum(w[k] * zones[NORM_COLS[k]] for k in w)
    covered = zones["store_covered"] if covered is None else covered
    eligible = ~covered & (zones["population_density"] >= density_floor)
    return raw[eligible].sort_values(ascending=False).index


# ─────────────────────────────────────────────
# SENSITIVITY
# ─────────────────────────────────────────────

def weight_sensitivity(zones, base_top_ids, n_draws=1000, concentration=50, seed=7):
    """
    Draws weight vectors from a Dirichlet centred on the base weights
    (concentration 50 -> each weight moves about +/-20% of its value) and
    records how often each zone lands in the top 10.
    """
    rng = np.random.default_rng(seed)
    keys = list(BASE_WEIGHTS)
    alpha = np.array([BASE_WEIGHTS[k] for k in keys]) * concentration
    hits, overlaps = pd.Series(0, index=zones.index, dtype=int), []
    for draw in rng.dirichlet(alpha, n_draws):
        top = _rescore(zones, dict(zip(keys, draw)))[:10]
        hits[top] += 1
        overlaps.append(len(set(zones.loc[top, "zone_id"]) & set(base_top_ids)))
    freq = (zones.assign(top10_share=hits / n_draws)
            .loc[hits > 0, ["zone_id", "zone_type", "top10_share"]]
            .sort_values("top10_share", ascending=False))
    freq["in_base_top10"] = freq["zone_id"].isin(base_top_ids)
    return freq, np.array(overlaps)


def scenario_sensitivity(zones, base_top_ids):
    scenarios = {
        "Baseline (35/35/20/10)":       (0.35, 0.35, 0.20, 0.10),
        "Distance-heavy (25/45/20/10)": (0.25, 0.45, 0.20, 0.10),
        "Income-heavy (30/30/35/05)":   (0.30, 0.30, 0.35, 0.05),
        "Density-heavy (45/35/15/05)":  (0.45, 0.35, 0.15, 0.05),
        "Equal (25/25/25/25)":          (0.25, 0.25, 0.25, 0.25),
    }
    rows = []
    for name, w in scenarios.items():
        top = zones.loc[_rescore(zones, dict(zip(BASE_WEIGHTS, w)))[:10], "zone_id"].tolist()
        rows.append({"scenario": name, "overlap_with_base": len(set(top) & set(base_top_ids)),
                     "top10": ", ".join(top)})
    return pd.DataFrame(rows)


def radius_sensitivity(stores, zones_raw, base_top_ids, radii=(1.0, 1.5, 2.0, 2.5, 3.0)):
    rows = []
    for r in radii:
        z = compute_nearest_store_distance(zones_raw, stores)
        z["store_covered"] = z["nearest_store_dist_km"] <= r
        z = compute_dsoi(z)
        top = get_top_expansion_zones(z, n=10)
        rows.append({"coverage_radius_km": r, "zones_covered": int(z["store_covered"].sum()),
                     "overlap_with_base": len(set(top["zone_id"]) & set(base_top_ids))})
    return pd.DataFrame(rows)


def density_floor_sensitivity(zones, base_top_ids, floors=(0, 2000, 3000, 4000, 5000)):
    rows = []
    for f in floors:
        ids = zones.loc[_rescore(zones, BASE_WEIGHTS, density_floor=f), "zone_id"]
        rows.append({"density_floor": f, "eligible_zones": len(ids),
                     "overlap_with_base": len(set(ids[:10]) & set(base_top_ids))})
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────

def _save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    path = os.path.join(FIG, name)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"📊 {os.path.relpath(path, ROOT)}")
    return path


def fig_map(zones, stores, top10, ax=None):
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(9, 7.4))
    for tier in TIER_ORDER:
        sub = zones[zones["dsoi_tier"].astype(str) == tier]
        if len(sub):
            sub.plot(ax=ax, color=TIER_FILL[tier], edgecolor=SURFACE, linewidth=1.2)
    # 1.5 km delivery rings (in projected metres, then back to lat/lon)
    rings = stores.to_crs("EPSG:32643").buffer(1500).to_crs("EPSG:4326")
    gpd.GeoSeries(rings).plot(ax=ax, facecolor="none", edgecolor=INK, linewidth=0.6, alpha=0.6)
    ax.scatter(stores.geometry.x, stores.geometry.y, s=14, c=INK, edgecolors=SURFACE,
               linewidths=0.8, zorder=4)
    ax.scatter(top10["lon_center"], top10["lat_center"], s=230, c=ORANGE,
               edgecolors=SURFACE, linewidths=2, zorder=5)
    for _, z in top10.iterrows():
        ax.text(z["lon_center"], z["lat_center"], str(int(z["expansion_rank"])),
                ha="center", va="center", color="white", fontsize=8, fontweight="bold", zorder=6)
    for name, (lat, lon) in {"Connaught Place": (28.6315, 77.2167), "Gurgaon": (28.4595, 77.0266),
                             "Noida": (28.5355, 77.3910), "Rohini": (28.7041, 77.1025)}.items():
        off = {"Noida": (-10, -16), "Gurgaon": (-30, -18), "Connaught Place": (-20, 12)}.get(name, (6, 6))
        ax.annotate(name, (lon, lat), xytext=off, textcoords="offset points",
                    fontsize=8, color=INK, style="italic", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.8))
    handles = [Patch(facecolor=TIER_FILL[t], edgecolor=GRID, label=t) for t in reversed(TIER_ORDER)]
    handles += [Line2D([], [], marker="o", ls="", color=INK, markersize=4, label="Existing store (1.5 km ring)"),
                Line2D([], [], marker="o", ls="", color=ORANGE, markersize=10, label="Top-10 expansion zone")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8.5)
    ax.set_title("Where the whitespace is: DSOI tier by demand zone")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.tick_params(labelsize=8)
    if own:
        return _save(fig, "01_dsoi_opportunity_map.png")


def fig_orders(demand, ax=None):
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(9, 5))
    d = demand.sort_values("expansion_rank", ascending=False)
    labels = [f"#{r}  {z}" for r, z in zip(d["expansion_rank"], d["zone_id"])]
    bars = ax.barh(labels, d["est_daily_orders"], color=SERIES[0], height=0.62)
    for b, o, g in zip(bars, d["est_daily_orders"], d["est_monthly_gmv_inr"]):
        ax.text(b.get_width() + 20, b.get_y() + b.get_height() / 2,
                f"{o:,}/day  ·  ₹{g/1e5:,.0f} L/mo", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, d["est_daily_orders"].max() * 1.45)
    ax.set_xlabel("Estimated daily orders, one new store (1.5 km catchment)")
    ax.set_title("Order potential of the top 10 zones (ranked by DSOI)")
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    if own:
        return _save(fig, "02_top10_orders_gmv.png")


def fig_decomposition(top10):
    fig, ax = plt.subplots(figsize=(9, 5))
    t = top10.sort_values("expansion_rank", ascending=False)
    labels = [f"#{r}  {z}" for r, z in zip(t["expansion_rank"], t["zone_id"])]
    left = np.zeros(len(t))
    names = {"density": "Density (35%)", "distance": "Distance to store (35%)",
             "income": "Income (20%)", "demand": "Delivery demand (10%)"}
    for (k, w), c in zip(BASE_WEIGHTS.items(), SERIES):
        vals = (w * t[NORM_COLS[k]]).values
        ax.barh(labels, vals, left=left, color=c, height=0.62, edgecolor=SURFACE,
                linewidth=2, label=names[k])
        left += vals
    ax.set_xlabel("Weighted contribution to raw DSOI (max possible = 1.0)")
    ax.set_title("What drives each top-10 score")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.28), ncol=4, fontsize=8.5)
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    return _save(fig, "03_dsoi_score_decomposition.png")


def fig_stability(freq, n_draws, ax=None):
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(9, 5.2))
    f = freq.head(15).iloc[::-1]
    colors = [SERIES[0] if b else "#b7d3f6" for b in f["in_base_top10"]]
    bars = ax.barh(f["zone_id"], f["top10_share"] * 100, color=colors, height=0.62)
    for b, v in zip(bars, f["top10_share"]):
        ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2, f"{v:.0%}",
                va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, 112)
    ax.set_xlabel(f"Share of {n_draws:,} random weight draws (±~20%) where the zone is in the top 10")
    ax.set_title("Rank stability: how robust is the top 10 to the weights?")
    ax.legend(handles=[Patch(color=SERIES[0], label="In base top 10"),
                       Patch(color="#b7d3f6", label="Not in base top 10")],
              loc="lower right", fontsize=8.5)
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    if own:
        return _save(fig, "04_rank_stability.png")


def fig_radius(rad, floor):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    a = axes[0]
    a.plot(rad["coverage_radius_km"], rad["overlap_with_base"], color=SERIES[0], lw=2,
           marker="o", markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
    for _, r in rad.iterrows():
        a.annotate(f"{int(r.overlap_with_base)}/10\n({int(r.zones_covered)} covered)",
                   (r.coverage_radius_km, r.overlap_with_base), xytext=(0, 10),
                   textcoords="offset points", ha="center", fontsize=8, color=INK)
    a.set_ylim(0, 12.5); a.set_xlabel("Coverage radius assumed for existing stores (km)")
    a.set_ylabel("Top-10 zones unchanged vs base"); a.set_title("Coverage radius")
    a.yaxis.grid(True, color=GRID); a.set_axisbelow(True)
    b = axes[1]
    b.plot(floor["density_floor"], floor["overlap_with_base"], color=SERIES[0], lw=2,
           marker="o", markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
    for _, r in floor.iterrows():
        b.annotate(f"{int(r.overlap_with_base)}/10", (r.density_floor, r.overlap_with_base),
                   xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8, color=INK)
    b.set_ylim(0, 12.5); b.set_xlabel("Density floor (persons / km²)")
    b.set_title("Density floor"); b.yaxis.grid(True, color=GRID); b.set_axisbelow(True)
    fig.suptitle("Sensitivity of the top 10 to the two modelling thresholds",
                 x=0.06, ha="left", fontweight="bold", color=INK)
    fig.tight_layout()
    return _save(fig, "05_threshold_sensitivity.png")


def fig_tiers(zones):
    fig, ax = plt.subplots(figsize=(9, 4))
    counts = zones["dsoi_tier"].value_counts().reindex(TIER_ORDER, fill_value=0)
    bars = ax.barh(counts.index[::-1], counts.values[::-1],
                   color=[TIER_FILL[t] for t in TIER_ORDER[::-1]], height=0.62,
                   edgecolor=[GRID] * len(TIER_ORDER), linewidth=0.8)
    for b, v in zip(bars, counts.values[::-1]):
        ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2, str(v),
                va="center", fontsize=9, color=INK)
    ax.set_xlabel("Number of demand zones (of 150)")
    ax.set_title("How the 150 zones classify")
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    return _save(fig, "06_zone_tier_counts.png")


def fig_scatter(zones, top10):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for tier in TIER_ORDER:
        s = zones[zones["dsoi_tier"].astype(str) == tier]
        ax.scatter(s["nearest_store_dist_km"], s["population_density"] / 1000, s=30,
                   c=TIER_FILL[tier], edgecolors=MUTED if tier.startswith("Excluded") else SURFACE,
                   linewidths=0.6, label=tier)
    ax.scatter(top10["nearest_store_dist_km"], top10["population_density"] / 1000, s=150,
               facecolors="none", edgecolors=ORANGE, linewidths=2, label="Top-10 zone")
    for _, z in top10.iterrows():
        left = int(z.expansion_rank) == 1   # #1 and #7 sit on top of each other
        ax.annotate(f"#{int(z.expansion_rank)}", (z.nearest_store_dist_km, z.population_density / 1000),
                    xytext=(-18 if left else 8, 4), textcoords="offset points", fontsize=8, color=INK)
    ax.axvline(1.5, color=MUTED, ls="--", lw=1); ax.axvline(6, color=MUTED, ls=":", lw=1)
    ax.axhline(3, color=MUTED, ls="--", lw=1)
    ax.text(1.35, 20, "1.5 km: covered", fontsize=8, color=INK2, rotation=90, ha="right")
    ax.text(6.25, 20, "6 km distance cap", fontsize=8, color=INK2, rotation=90, ha="left")
    ax.text(ax.get_xlim()[1] * 0.98, 3.4, "density floor 3,000/km²", fontsize=8, color=INK2, ha="right")
    ax.set_xlabel("Distance to nearest existing store (km)")
    ax.set_ylabel("Population density ('000 / km²)")
    ax.set_title("Density vs distance to the nearest store")
    ax.legend(fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.9))
    return _save(fig, "07_density_vs_distance.png")


# ─────────────────────────────────────────────
# EXCEL WHAT-IF MODEL
# ─────────────────────────────────────────────

def build_excel(zones, demand, freq, scen, rad, floor):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.chart import BarChart, Reference
    from openpyxl.worksheet.table import Table, TableStyleInfo

    os.makedirs(XL_DIR, exist_ok=True)
    wb = Workbook()
    hdr = Font(bold=True, color="FFFFFF"); hfill = PatternFill("solid", fgColor="1C5CAB")
    inp = PatternFill("solid", fgColor="FFF4D6"); bold = Font(bold=True)
    thin = Border(bottom=Side(style="thin", color="E4E3DF"))

    # Inputs
    ws = wb.active; ws.title = "Inputs"
    ws["A1"] = "Dark Store Expansion Model: assumptions (edit the yellow cells)"; ws["A1"].font = Font(bold=True, size=13)
    inputs = [("Average basket size (₹)", 380, "AOV"),
              ("Orders / 1,000 residents / day (high income)", 8, "RateHigh"),
              ("Orders / 1,000 residents / day (mid income)", 4, "RateMid"),
              ("High-income threshold (income proxy)", 0.6, "IncomeThreshold"),
              ("New-store delivery radius (km)", 1.5, "RadiusKm"),
              ("Demand ramp-up achieved (%)", 1.0, "RampPct")]
    from openpyxl.workbook.defined_name import DefinedName
    for i, (label, val, name) in enumerate(inputs, start=3):
        ws.cell(i, 1, label); c = ws.cell(i, 2, val); c.fill = inp
        if name == "RampPct": c.number_format = "0%"
        wb.defined_names[name] = DefinedName(name, attr_text=f"Inputs!$B${i}")
    ws.cell(10, 1, "Catchment area per store (km²)"); ws.cell(10, 2, "=PI()*RadiusKm^2").number_format = "0.00"
    wb.defined_names["CatchKm2"] = DefinedName("CatchKm2", attr_text="Inputs!$B$10")
    ws.cell(12, 1, "Notes").font = bold
    ws.cell(13, 1, "Demand-zone attributes are synthetic (parametric model calibrated to Delhi-NCR); store locations are a 38-store seed list.")
    ws.cell(14, 1, "Ramp-up % scales orders for a store that has not yet reached steady state (100% = mature).")
    ws.column_dimensions["A"].width = 52; ws.column_dimensions["B"].width = 14

    # Top 10 with live formulas
    t = wb.create_sheet("Top10")
    cols = ["Rank", "Zone", "Zone type", "Nearest store", "Dist. to store (km)", "Density (/km²)",
            "Zone area (km²)", "Income proxy", "DSOI", "Order rate", "Catchment pop.",
            "Daily orders", "Daily GMV (₹)", "Monthly GMV (₹ L)", "Annual GMV (₹ Cr)"]
    t.append(cols)
    for _, r in demand.sort_values("expansion_rank").iterrows():
        n = t.max_row + 1
        t.append([int(r.expansion_rank), r.zone_id, r.zone_type, r.nearest_store_name,
                  float(r.nearest_store_dist_km), float(r.population_density), float(r.area_km2),
                  float(r.income_proxy), float(r.dsoi_score),
                  f"=IF(H{n}>=IncomeThreshold,RateHigh,RateMid)",
                  f"=ROUND(F{n}*MIN(CatchKm2,G{n}),0)",
                  f"=ROUND(K{n}*J{n}/1000*RampPct,0)",
                  f"=L{n}*AOV", f"=M{n}*30/100000", f"=M{n}*365/10000000"])
    last = t.max_row
    t.append(["Total", "", "", "", "", "", "", "", "", "", f"=SUM(K2:K{last})", f"=SUM(L2:L{last})",
              f"=SUM(M2:M{last})", f"=SUM(N2:N{last})", f"=SUM(O2:O{last})"])
    for c in t[last + 1]: c.font = bold
    for c in t[1]: c.font = hdr; c.fill = hfill; c.alignment = Alignment(wrap_text=True, vertical="center")
    fmts = {"E": "0.0", "F": "#,##0", "H": "0.00", "I": "0.0", "K": "#,##0", "L": "#,##0",
            "M": "#,##0", "N": "#,##0.0", "O": "#,##0.00"}
    for col, f in fmts.items():
        for row in range(2, last + 2):
            t[f"{col}{row}"].number_format = f
    for col, w in zip("ABCDEFGHIJKLMNO", [6, 8, 12, 24, 10, 11, 10, 9, 7, 8, 12, 10, 13, 12, 12]):
        t.column_dimensions[col].width = w
    t.row_dimensions[1].height = 32; t.freeze_panes = "C2"
    ch = BarChart(); ch.type = "bar"; ch.style = 2; ch.title = "Daily orders per new store"
    ch.add_data(Reference(t, min_col=12, min_row=1, max_row=last), titles_from_data=True)
    ch.set_categories(Reference(t, min_col=2, min_row=2, max_row=last))
    ch.y_axis.title = "Orders / day"; ch.legend = None; ch.height = 9; ch.width = 18
    ch.x_axis.scaling.orientation = "maxMin"
    t.add_chart(ch, "B15")

    # All zones
    a = wb.create_sheet("All_Zones")
    keep = ["zone_id", "zone_type", "lat_center", "lon_center", "population_density", "income_proxy",
            "delivery_demand", "nearest_store_name", "nearest_store_dist_km", "store_covered",
            "is_negligible_density", "dsoi_score", "dsoi_tier"]
    df = zones[keep].copy(); df["dsoi_tier"] = df["dsoi_tier"].astype(str)
    df = df.sort_values("dsoi_score", ascending=False)
    a.append(keep)
    for row in df.itertuples(index=False):
        a.append([bool(v) if isinstance(v, (np.bool_,)) else v for v in row])
    tab = Table(displayName="tblZones", ref=f"A1:M{a.max_row}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    a.add_table(tab); a.freeze_panes = "B2"
    for col in "ABCDEFGHIJKLM": a.column_dimensions[col].width = 15

    # Sensitivity
    s = wb.create_sheet("Sensitivity")
    def block(title, frame, start):
        s.cell(start, 1, title).font = Font(bold=True, size=12)
        for j, c in enumerate(frame.columns, 1):
            cell = s.cell(start + 1, j, c); cell.font = hdr; cell.fill = hfill
        for i, row in enumerate(frame.itertuples(index=False), start + 2):
            for j, v in enumerate(row, 1):
                s.cell(i, j, bool(v) if isinstance(v, np.bool_) else v)
        return start + len(frame) + 3
    r = block("Weight scenarios", scen, 1)
    r = block("Random weight draws: share of draws in top 10", freq.head(15), r)
    r = block("Coverage radius sweep", rad, r)
    block("Density floor sweep", floor, r)
    s.column_dimensions["A"].width = 30; s.column_dimensions["C"].width = 16
    s.column_dimensions["B"].width = 18

    path = os.path.join(XL_DIR, "Dark_Store_Expansion_Model.xlsx")
    wb.save(path)
    print(f"📗 {os.path.relpath(path, ROOT)}")
    return path


# ─────────────────────────────────────────────
# PDF BRIEF
# ─────────────────────────────────────────────

def build_pdf(zones, stores, top10, demand, freq, overlaps, scen, rad, kpis):
    path = os.path.join(OUT, "Dark_Store_Strategy_Brief.pdf")
    with PdfPages(path) as pdf:
        # Page 1: summary + table
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.07, 0.955, "Dark Store Placement Intelligence: Delhi-NCR", fontsize=17,
                 fontweight="bold", color=INK)
        fig.text(0.07, 0.935, "Strategy brief  ·  where to open the next 10 quick-commerce dark stores",
                 fontsize=10, color=INK2)
        tiles = [(f"{kpis['orders']:,}", "est. orders / day\n(10 new stores)"),
                 (f"₹{kpis['monthly_cr']:.1f} Cr", "est. monthly GMV\n(₹380 basket)"),
                 (f"{kpis['robust']}/10", "zones in top 10 in\n≥80% of weight draws"),
                 (f"{kpis['eligible']}", "zones eligible\n(of 150)")]
        for i, (v, l) in enumerate(tiles):
            x = 0.07 + i * 0.225
            fig.patches.append(plt.Rectangle((x, 0.835), 0.205, 0.08, transform=fig.transFigure,
                                             facecolor="#f3f2ef", edgecolor="none"))
            fig.text(x + 0.012, 0.888, v, fontsize=16, fontweight="bold", color=INK)
            fig.text(x + 0.012, 0.845, l, fontsize=8, color=INK2)
        summary = kpis["summary_lines"]
        y = 0.80
        fig.text(0.07, y, "Key findings", fontsize=12, fontweight="bold", color=INK); y -= 0.025
        for line in summary:
            fig.text(0.07, y, "•", fontsize=9.5, color=INK)
            fig.text(0.09, y, line, fontsize=9.5, color=INK, wrap=True, va="top")
            y -= 0.012 * (line.count("\n") + 1) + 0.016
        ax = fig.add_axes([0.07, 0.07, 0.86, y - 0.10]); ax.axis("off")
        d = demand.sort_values("expansion_rank")
        cell = [[int(r.expansion_rank), r.zone_id, r.zone_type, r.nearest_store_name.replace("Instamart ", "Instamart\n") if len(r.nearest_store_name) > 22 else r.nearest_store_name,
                 f"{r.nearest_store_dist_km:.1f}", f"{int(r.population_density):,}", f"{r.dsoi_score:.1f}",
                 f"{r.est_daily_orders:,}", f"{r.est_monthly_gmv_inr/1e5:,.0f}",
                 f"{freq.set_index('zone_id').top10_share.get(r.zone_id, 0):.0%}"] for r in d.itertuples()]
        tb = ax.table(cellText=cell, colLabels=["#", "Zone", "Type", "Nearest store", "km", "Density",
                                                "DSOI", "Orders/day", "GMV ₹L/mo", "Stable"],
                      loc="upper center", cellLoc="center", colLoc="center",
                      colWidths=[0.04, 0.07, 0.11, 0.25, 0.06, 0.09, 0.07, 0.1, 0.11, 0.08])
        tb.auto_set_font_size(False); tb.set_fontsize(8); tb.scale(1, 1.55)
        for (r_, c_), cl in tb.get_celld().items():
            cl.set_edgecolor(GRID)
            if r_ == 0:
                cl.set_facecolor("#1c5cab"); cl.get_text().set_color("white"); cl.get_text().set_fontweight("bold")
        ax.set_title("Top 10 expansion zones (one store per zone, 1.5 km catchment)  ·  'Stable' = share of 1,000 weight draws in top 10",
                     fontsize=8.5, loc="left", color=INK2, fontweight="normal")
        fig.text(0.07, 0.035, "Data: 38-store seed list of named Blinkit/Zepto/Instamart locations; demand-zone density, income and "
                 "delivery-demand are synthetic\n(parametric model calibrated to Delhi-NCR). Methodology demonstration, "
                 "not a validated site-selection tool. Full method: docs/methodology.md", fontsize=7, color=MUTED)
        pdf.savefig(fig); plt.close(fig)

        # Page 2: visuals
        fig = plt.figure(figsize=(8.27, 11.69))
        ax1 = fig.add_axes([0.08, 0.53, 0.58, 0.40]); fig_map(zones, stores, top10, ax=ax1)
        ax1.legend_.set_bbox_to_anchor((1.02, 1.0)); ax1.title.set_fontsize(11)
        ax2 = fig.add_axes([0.15, 0.08, 0.36, 0.38]); fig_orders(demand, ax=ax2)
        ax2.set_title("Orders/day per new store", fontsize=10); ax2.xaxis.label.set_fontsize(7.5)
        for txt in ax2.texts: txt.set_fontsize(6.5)
        ax3 = fig.add_axes([0.64, 0.08, 0.30, 0.38]); fig_stability(freq.head(12), 1000, ax=ax3)
        ax3.set_title("Rank stability", fontsize=10); ax3.set_xlabel("% of weight draws in top 10", fontsize=7.5)
        ax3.legend_.remove()
        for txt in ax3.texts: txt.set_fontsize(6.5)
        pdf.savefig(fig); plt.close(fig)
    print(f"📄 {os.path.relpath(path, ROOT)}")
    return path
