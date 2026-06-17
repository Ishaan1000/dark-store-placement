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

**Bottom line:** the single highest-opportunity zone in this run (Z034, near Palam Vihar/South-West Gurgaon border) combines high density, top-tier income proxy, and an 8.4km gap from the nearest seeded store. The next two zones (Z058, Z020) sit near Noida Sector 44 and the Sohna Road corridor respectively, both with very high density (15,000–22,000/km²) and moderate distance — strong candidates for the next wave after Z034.

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

| Rank | Zone ID | Type | Nearest Store | Distance | Density (/km²) | Income Proxy | DSOI | Est. Daily Orders | Approx. Area |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Z034 | Urban | Blinkit Palam Vihar | 8.4 km | 9,727 | 1.00 | 100.0 | 2,671 | South-West Gurgaon / Palam Vihar periphery |
| 2 | Z058 | Metro Core | Zepto Noida Sec 44 | 4.2 km | 22,451 | 0.73 | 97.9 | 6,166 | Noida Sector 44 extended belt |
| 3 | Z020 | Metro Core | Zepto Sohna Road | 4.5 km | 15,532 | 1.00 | 97.1 | 4,266 | Sohna Road corridor, South Gurgaon |
| 4 | Z043 | Metro Core | Zepto Noida Sec 44 | 9.0 km | 11,108 | 0.82 | 91.3 | 3,051 | Noida Sector 62+ periphery |
| 5 | Z052 | Urban | Zepto Dwarka Sec 10 | 5.5 km | 9,026 | 1.00 | 90.9 | 2,479 | Dwarka outer sectors |
| 6 | Z069 | Metro Core | Blinkit Connaught Place | 3.3 km | 26,680 | 0.62 | 90.1 | 7,327 | Central Delhi, near CP |
| 7 | Z059 | Metro Core | Zepto Noida Sec 44 | 8.8 km | 9,659 | 0.83 | 90.0 | 2,653 | Noida far-east periphery |
| 8 | Z014 | Urban | Blinkit Greater Noida | 12.1 km | 8,236 | 0.90 | 88.8 | 2,262 | Greater Noida West fringe |
| 9 | Z036 | Metro Core | Blinkit Gurgaon Sec 29 | 3.1 km | 16,566 | 1.00 | 88.6 | 4,550 | Gurgaon Sector 29–40 belt |
| 10 | Z049 | Urban | Blinkit Palam Vihar | 8.3 km | 4,023 | 1.00 | 86.5 | 1,105 | South-West Gurgaon border |

*Full data with all intermediate scores: `outputs/top10_expansion_zones.csv`. Order and GMV estimates per zone: `outputs/order_demand_estimates.csv`.*

---

## Key Findings

### Finding 1 — Rank 6 (Near Connaught Place) Has the Highest Single-Zone Order Potential
Z069 has the highest population density in the entire top 10 (26,680/km²) and the highest estimated daily order volume (7,327), despite a below-average income proxy (0.62) relative to the rest of the list. Sheer density compensates for a smaller average basket size — high order *volume* rather than high order *value*.

### Finding 2 — Gurgaon and Noida Peripheries Dominate the List
7 of the top 10 zones sit in Gurgaon or Noida extended sectors rather than core Delhi. This is consistent with the seed store list being denser in established Delhi neighbourhoods (South Delhi, Central Delhi, Karol Bagh) and comparatively thinner in NCR's faster-growing outer sectors — exactly the kind of whitespace a DSOI model is built to surface.

### Finding 3 — All Top 10 Zones Have an Income Proxy Above 0.6
Every zone in this run, even the lowest-ranked, sits well above the income floor that would suggest a low-basket-size market. This is a direct consequence of the 35% weight on density and 35% on distance crowding out income as the binding constraint — in this particular run, there was no need to trade off density/distance against income, because zones scoring well on the first two also happened to skew affluent.

---

## Strategic Recommendations

### Recommendation 1 — Sequence Z034, Z058, and Z020 as the First Wave
These three combine the highest DSOI scores with real distance from existing coverage (4–9km, comfortably outside the 1.5km cannibalisation radius). Recommend opening these three in the same quarter to establish presence across three distinct geographic corridors (Gurgaon periphery, Noida, Sohna Road) before competitors respond in any one of them.

### Recommendation 2 — Validate the Seed Store List Before Committing Capital
The "nearest store" distances in this brief are only as good as the 38-location seed list in `data_loader.py`. Before using this analysis to inform real site selection, replace the seed list with Blinkit's actual internal store roster (or a verified, current third-party dataset) and re-run `src/opportunity_model.py` — the scoring logic itself does not need to change.

### Recommendation 3 — Use Z069's Result as a Sense-Check, Not a Site Pick
Z069 sits only 3.25km from an existing Connaught Place store — close enough that real-world cannibalisation risk is meaningfully higher than the model's 1.5km threshold fully captures, especially if the existing store's actual delivery radius extends past 1.5km in practice. Treat this result as a signal that the area is under-capacitated relative to demand, not as a literal "open here" instruction.

---

## Financial Impact Summary (Top 10 Zones, This Run)

| Metric | Total |
|---|---|
| Combined estimated daily orders | 36,530 |
| Combined estimated monthly GMV | ₹41.64 Cr |
| Combined estimated annual GMV | ₹506.67 Cr |

*Assumes 8 orders per 1,000 residents per day for zones with income proxy ≥ 0.6 (all 10 zones in this run cleared that threshold), and a category-standard basket size baked into `estimate_order_demand()`. See `docs/methodology.md` for the exact formula and the basket-size assumption.*

---

## Caveats and Limitations

- **Existing store locations are a hand-built seed list of ~38 real, named locations**, not a live or comprehensive feed of Blinkit/Zepto/Instamart's actual store networks. The real networks are larger; a more complete seed list would likely shrink some of the gaps identified here.
- **Demand zone density, income, and delivery-demand are synthetic**, calibrated to Delhi-NCR's real multi-center urban structure (CP, Gurgaon, Noida, Rohini) but not sourced from Census or any official dataset.
- 1.5km coverage radius is a stated industry assumption, not validated against any specific operator's actual delivery-radius policy.
- The basket-size and order-rate assumptions in `estimate_order_demand()` are reasonable estimates, not sourced from any operator's disclosed unit economics.
- Area name labels are approximate, based on matching each zone's lat/lon to known Delhi-NCR geography by eye.

---

## Next Steps

1. Replace the seed store list with a verified, current dataset of all three operators' actual store locations
2. Source real ward/sector-level population and income data for Delhi-NCR to replace the synthetic demand grid
3. Pilot Z034, Z058, and Z020 with a 90-day tracked rollout before committing to the remaining 7 zones
4. Extend the bounding box to cover Faridabad and Ghaziabad with the same methodology

---

*This brief was produced as part of an independent data analytics project, generated directly from the code in this repository. Both the existing-store seed list and the demand-zone population data are best-effort approximations, not official or live data feeds — see Caveats above before treating any specific number as a real-world recommendation.*
