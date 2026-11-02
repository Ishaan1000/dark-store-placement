# Strategy Brief: Dark Store Placement Intelligence
**Prepared by:** Ishaan Mankotia  
**Framed for:** Head of Expansion Strategy, Blinkit (Zomato)  
**Date:** June 2026  
**Classification:** Internal Strategy Document

---

## A note on the underlying data

This brief is generated directly from the model and code in this repository (`src/opportunity_model.py`, run end-to-end). Real dark store locations for Blinkit, Zepto, and Instamart are not published in a structured, scrapeable format, so existing-store coordinates come from a hand-built seed list of ~38 real, named locations across Delhi-NCR (`src/data_loader.py::_fallback_dark_stores()`), checked against publicly known store catalogue/area coverage as of early 2026. Demand-zone population density, income proxy, and delivery-demand signal are from a parametric synthetic model calibrated to Delhi-NCR's actual urban geography (four real city centers: Connaught Place, Gurgaon, Noida, Rohini). **This is a methodology demonstration built on a best-effort approximation of real store coverage, not a validated real-world site-selection tool** — see Caveats for what would need to change before using it to commit real capital.

---

## Executive Summary

Running the Dark Store Opportunity Index (DSOI) model against 150 demand zones and ~38 seeded real store locations surfaces a clear pattern: the highest-opportunity zones are concentrated in **Metro Core areas 3–9km from the nearest existing store** — close enough to be a realistic single-store expansion, far enough to avoid cannibalising the existing network. Six of the top 10 zones fall in the Metro Core category, and every zone in the top 10 has an income proxy above 0.6, meaning none of them are low-basket-size markets.

**Bottom line (updated):** the recommended first wave is Z058, Z020 and Z043, about 2,800 orders/day and ₹3.2 Cr GMV/month, chosen for volume and rank stability (see Recommendation 1). On DSOI alone, the single highest-opportunity zone in this run (Z034, near Palam Vihar/South-West Gurgaon border) combines high density, top-tier income proxy, and an 8.4km gap from the nearest seeded store. The next two zones (Z058, Z020) sit near Noida Sector 44 and the Sohna Road corridor respectively, both with very high density (15,000–22,000/km²) and moderate distance.

---

## Problem Definition

> *"Where in Delhi-NCR should Blinkit open its next 10 dark stores to maximise order volume and GMV per store, while minimising cannibalisation of existing stores?"*

This is a constrained optimisation problem balancing four variables: population density, distance from existing coverage, income/spending power, and a delivery-demand proxy. The model is built to be re-run as real store-location and order data becomes available.

---

## Methodology Summary

| Component | Variable | Weight |
|---|---|---|
| Population Density Score | Persons per km², normalised | 35% |
| Distance to Nearest Dark Store | km from zone centroid, capped at 6km, normalised | 35% |
| Income / Spending Power Proxy | Housing type + income index, normalised | 20% |
| Delivery Demand Proxy | Food delivery POI density + commercial activity | 10% |

Zones within **1.5km of any existing dark store** are classified as covered and excluded. Zones below **3,000 persons/km²** are excluded as non-residential noise. Final DSOI scores run 0–100.

Full methodology and the rationale for the distance cap and density floor: see `docs/methodology.md`.

---

## Actual Top 10 Output (this run)

Orders and GMV are sized to **one new store's 1.5 km catchment** (π × 1.5² ≈ 7.07 km²), not the whole ~30.5 km² grid cell. One store can't serve an entire cell, so the cell-level figure is shown only as a ceiling in `order_demand_estimates.csv` (`zone_potential_daily_orders`). **Stable** is the share of 1,000 random weight draws (each weight varied by about ±20%) in which the zone stays in the top 10.

| Rank | Zone | Type | Nearest store | Distance | Density (/km²) | Income | DSOI | Orders/day | GMV ₹ L/mo | Stable | Approx. area |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Z034 | Urban | Blinkit Palam Vihar | 8.4 km | 9,727 | 1.00 | 100.0 | 550 | 63 | 100% | West of Gurgaon / Palam Vihar |
| 2 | Z058 | Metro Core | Zepto Noida Sec 44 | 4.2 km | 22,451 | 0.73 | 97.9 | 1,270 | 145 | 95% | Noida Sector 44 extended belt |
| 3 | Z020 | Metro Core | Zepto Sohna Road | 4.5 km | 15,532 | 1.00 | 97.1 | 878 | 100 | 99% | Sohna Road corridor, South Gurgaon |
| 4 | Z043 | Metro Core | Zepto Noida Sec 44 | 9.0 km | 11,108 | 0.82 | 91.3 | 628 | 72 | 100% | South Noida periphery |
| 5 | Z052 | Urban | Zepto Dwarka Sec 10 | 5.5 km | 9,026 | 1.00 | 90.9 | 510 | 58 | 100% | Dwarka outer sectors |
| 6 | Z069 | Metro Core | Blinkit Connaught Place | 3.2 km | 26,680 | 0.62 | 90.1 | 1,509 | 172 | 61% | Central Delhi, south of CP |
| 7 | Z059 | Metro Core | Zepto Noida Sec 44 | 8.8 km | 9,659 | 0.83 | 90.0 | 546 | 62 | 96% | Noida far-east periphery |
| 8 | Z014 | Urban | Blinkit Greater Noida | 12.1 km | 8,236 | 0.90 | 88.8 | 466 | 53 | 95% | Greater Noida fringe |
| 9 | Z036 | Metro Core | Blinkit Gurgaon Sec 29 | 3.1 km | 16,566 | 1.00 | 88.6 | 937 | 107 | 63% | Gurgaon Sector 29–40 belt |
| 10 | Z049 | Urban | Blinkit Palam Vihar | 8.3 km | 4,023 | 1.00 | 86.5 | 227 | 26 | 44% | South-West Delhi / Gurgaon border |

*Full data: `outputs/top10_expansion_zones.csv`, `outputs/order_demand_estimates.csv`, `outputs/all_zones_scored.csv`. Live what-if: `outputs/excel/Dark_Store_Expansion_Model.xlsx`.*

---

## Key Findings

### Finding 1: Only 64 of 150 zones are real candidates
6 zones already sit within 1.5 km of a seeded store, and 80 fall below the 3,000/km² density floor (open land or undeveloped periphery). Of the 64 that remain, 50 score as High Opportunity. The model isn't short of whitespace. The question is which whitespace a store can actually monetise.

### Finding 2: DSOI rank is not order rank
Z069 (rank 6) has the highest order potential at 1,509 orders/day because it is the densest zone in the list. Z049 (rank 10) would manage only 227. The 35% weight on distance lifts remote, affluent but thinner zones such as Z034, Z014 and Z049 above denser zones closer to existing stores. DSOI finds *whitespace*. Volume has to be checked separately before a site is picked, which is why this brief reports both.

### Finding 3: The top 10 holds up under sensitivity testing
- **Weights:** across 1,000 random weight draws, the median draw keeps 9 of the 10 zones, and 7 zones stay in the top 10 in at least 90% of draws. The three fragile picks are Z036 (63%), Z069 (61%) and Z049 (44%). Z042 and Z019 are the next zones in line.
- **Thresholds:** changing the existing-store coverage radius from 1.0 to 3.0 km, or the density floor from 0 to 4,000/km², leaves the top 10 unchanged. A 5,000/km² floor swaps out only Z049.
- **Named scenarios:** distance-heavy, income-heavy, density-heavy and equal-weight scenarios keep 8–9 of the base 10.

### Finding 4: All top-10 zones are affluent
Every top-10 zone has an income proxy of at least 0.6, so all of them use the high order rate (8 per 1,000 residents per day). None of them is a low-basket market.

---

## Strategic Recommendations

### Recommendation 1: First wave of Z058, Z020 and Z043
These are the three highest-volume zones among the 7 that stay in the top 10 in at least 90% of weight draws. Together they come to about **2,800 orders/day and ₹3.2 Cr GMV/month**, and they cover two corridors (Noida and Sohna Road/South Gurgaon). Z034 is the model's #1, but its single-store volume (550/day) is modest. Run it in the second wave as a test of the "remote but affluent" thesis.

### Recommendation 2: Treat Z069 and Z036 as capacity signals, not site picks
These are the two highest-volume zones after Z058, but they sit only 3.1–3.3 km from existing stores and are weight-sensitive (about 60% stable). In reality, central Delhi and Gurgaon Sector 29 are heavily served. The real answer there is more likely added capacity at the nearby store than a new site.

### Recommendation 3: Validate the inputs before committing capital
Replace the 38-store seed list with an operator's real store roster, and replace the synthetic demand grid with ward-level population and income data. Then re-run `python src/run_all.py`. The scoring, sensitivity and reporting code doesn't change.

---

## Financial Impact Summary (top 10 zones, one store each)

| Metric | Total |
|---|---|
| Estimated daily orders | 7,521 (≈752 per store) |
| Estimated monthly GMV | ₹8.57 Cr |
| Estimated annual GMV | ₹104.3 Cr |
| Cell-level ceiling (if a store served its whole ~30.5 km² cell) | 32,471 orders/day |

*Assumptions: 8 orders per 1,000 residents per day where the income proxy is ≥ 0.6 (all 10 zones), a ₹380 average basket, and a 1.5 km delivery radius at steady state. Every assumption is an editable input in the Excel model.*

> **Correction to the earlier version of this brief:** it reported 36,530 orders/day and ₹41.6 Cr/month. Those figures assumed each new store serves its entire grid cell. The cell areas were also overstated by ~14% (no cos-latitude correction); with both fixed, the cell-level figure (32,471/day) is shown only as a ceiling.

---

## Caveats and Limitations

- **Existing store locations come from a hand-built seed list of 38 real, named locations**, not a comprehensive feed. The real networks are much larger, so a fuller list would close some of these gaps, especially Z069 and Z036.
- **Demand-zone density, income and delivery demand are synthetic.** They come from a parametric model calibrated to Delhi-NCR's multi-centre structure (CP, Gurgaon, Noida, Rohini), not from the Census or any official dataset.
- Distances are straight-line, not road-network.
- The 1.5 km radius, order rates and ₹380 basket are stated assumptions, not any operator's disclosed unit economics.
- Area labels are approximate: each zone's lat/lon was matched to known geography by eye.

---

## Next Steps

1. Swap in verified store locations for all three operators.
2. Replace the synthetic grid with ward/sector-level population and income data.
3. Pilot Z058, Z020 and Z043 with a 90-day tracked rollout and calibrate the order rate to actual results.
4. Extend the bounding box to Faridabad and Ghaziabad.

---

*Produced as an independent analytics project, generated from the code in this repository (`python src/run_all.py`). See the caveats above before treating any number as a real-world recommendation.*
