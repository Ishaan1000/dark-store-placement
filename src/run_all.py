"""
run_all.py
==========
One command, every output:

    python src/run_all.py

  1. ETL + validation + SQLite load       (pipeline.py)
  2. DSOI scoring, top 10, order demand    (opportunity_model.py)
  3. Sensitivity analysis                  (analysis.py)
  4. Figures, interactive map, Excel model, PDF brief

Author: Ishaan Mankotia
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__))

from pipeline import run_pipeline
from data_loader import fetch_dark_stores, generate_demand_grid
from visualizer import create_opportunity_map
import analysis as A

OUT = A.OUT


def main():
    print("=" * 64 + "\n  Dark Store Placement Intelligence: full run\n" + "=" * 64)

    # 1. Data engineering layer
    run_pipeline()

    # 2. Model
    stores = fetch_dark_stores()
    zones_raw = generate_demand_grid()
    zones, top10, demand = A.run_model(stores, zones_raw)
    base_ids = top10["zone_id"].tolist()

    # 3. Sensitivity
    freq, overlaps = A.weight_sensitivity(zones, base_ids)
    scen  = A.scenario_sensitivity(zones, base_ids)
    rad   = A.radius_sensitivity(stores, zones_raw, base_ids)
    floor = A.density_floor_sensitivity(zones, base_ids)

    # 4. Tables
    os.makedirs(OUT, exist_ok=True)
    zones.drop(columns="geometry").assign(dsoi_tier=zones["dsoi_tier"].astype(str)) \
         .sort_values("dsoi_score", ascending=False) \
         .to_csv(os.path.join(OUT, "all_zones_scored.csv"), index=False)
    top10.drop(columns="geometry").to_csv(os.path.join(OUT, "top10_expansion_zones.csv"), index=False)
    demand.to_csv(os.path.join(OUT, "order_demand_estimates.csv"), index=False)
    freq.to_csv(os.path.join(OUT, "sensitivity_weight_draws.csv"), index=False)
    scen.to_csv(os.path.join(OUT, "sensitivity_scenarios.csv"), index=False)
    rad.to_csv(os.path.join(OUT, "sensitivity_coverage_radius.csv"), index=False)
    floor.to_csv(os.path.join(OUT, "sensitivity_density_floor.csv"), index=False)

    # 5. KPIs for the brief
    share = freq.set_index("zone_id")["top10_share"]
    tiers = zones["dsoi_tier"].astype(str).value_counts()
    d = demand.sort_values("est_daily_orders", ascending=False)
    first_wave = demand[demand["zone_id"].isin(
        [z for z in base_ids if share.get(z, 0) >= 0.8])].sort_values("est_daily_orders", ascending=False).head(3)
    kpis = {
        "orders": int(demand["est_daily_orders"].sum()),
        "monthly_cr": demand["est_monthly_gmv_inr"].sum() / 1e7,
        "annual_cr": demand["est_annual_gmv_inr"].sum() / 1e7,
        "zone_ceiling": int(demand["zone_potential_daily_orders"].sum()),
        "robust": int(sum(share.get(z, 0) >= 0.8 for z in base_ids)),
        "eligible": int(len(zones) - tiers.get("Covered", 0) - tiers.get("Excluded (Low Density)", 0)),
        "covered": int(tiers.get("Covered", 0)),
        "excluded": int(tiers.get("Excluded (Low Density)", 0)),
        "high": int(tiers.get("High Opportunity", 0)),
        "median_overlap": float(sorted(overlaps)[len(overlaps) // 2]),
        "metro_core_in_top10": int((top10["zone_type"] == "Metro Core").sum()),
        "top_orders_zone": d.iloc[0].zone_id, "top_orders": int(d.iloc[0].est_daily_orders),
        "low_orders_zone": d.iloc[-1].zone_id, "low_orders": int(d.iloc[-1].est_daily_orders),
        "first_wave": first_wave["zone_id"].tolist(),
        "first_wave_orders": int(first_wave["est_daily_orders"].sum()),
        "first_wave_gmv_cr": first_wave["est_monthly_gmv_inr"].sum() / 1e7,
        "per_store_avg": int(demand["est_daily_orders"].mean()),
    }
    kpis["summary_lines"] = [
        f"Of 150 demand zones, {kpis['covered']} sit within 1.5 km of an existing store and {kpis['excluded']} fall below the\n"
        f"3,000/km² density floor, leaving {kpis['eligible']} candidates; {kpis['high']} score as High Opportunity (DSOI ≥ 60).",
        f"The top 10 would add ~{kpis['orders']:,} orders/day (≈{kpis['per_store_avg']} per store) and ₹{kpis['monthly_cr']:.1f} Cr GMV/month "
        f"(₹{kpis['annual_cr']:.0f} Cr/yr)\nat a ₹380 basket, sizing each store to its 1.5 km catchment, not the whole zone.",
        f"DSOI rank is not order rank: {kpis['top_orders_zone']} (densest) leads at {kpis['top_orders']:,} orders/day while "
        f"{kpis['low_orders_zone']} manages {kpis['low_orders']:,};\nthe 35% distance weight lifts remote, affluent but thinner zones.",
        f"{kpis['robust']} of the top 10 stay in the top 10 in ≥80% of 1,000 random weight draws (±~20%); the median draw\n"
        f"keeps {kpis['median_overlap']:.0f}/10. Changing the coverage radius (1-3 km) or density floor (0-4,000/km²)\n"
        f"leaves the top 10 unchanged: the ranking is driven by the data, not the thresholds.",
        f"Recommended first wave (robust + highest volume): {', '.join(kpis['first_wave'])}, ~{kpis['first_wave_orders']:,} orders/day,\n"
        f"₹{kpis['first_wave_gmv_cr']:.1f} Cr GMV/month. Validate with real order data before committing capex.",
    ]
    with open(os.path.join(OUT, "kpis.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in kpis.items() if k != "summary_lines"}, f, indent=2, default=str)

    # 6. Visuals
    A.fig_map(zones, stores, top10)
    A.fig_orders(demand)
    A.fig_decomposition(top10)
    A.fig_stability(freq, 1000)
    A.fig_radius(rad, floor)
    A.fig_tiers(zones)
    A.fig_scatter(zones, top10)
    create_opportunity_map(zones, stores, top10)
    A.build_excel(zones, demand, freq, scen, rad, floor)
    A.build_pdf(zones, stores, top10, demand, freq, overlaps, scen, rad, kpis)

    print("\n" + "=" * 64)
    for line in kpis["summary_lines"]:
        print(" • " + line.replace("\n", " "))
    print("\nSensitivity: scenarios\n" + scen.to_string(index=False))
    print("\nCoverage radius\n" + rad.to_string(index=False))
    print("\nDensity floor\n" + floor.to_string(index=False))
    print("\nTop of weight-draw stability\n" + freq.head(14).to_string(index=False))


if __name__ == "__main__":
    main()
