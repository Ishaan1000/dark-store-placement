# Strategy Brief: Dark Store Placement Intelligence
**Prepared by:** Ishaan Mankotia  
**Framed for:** Head of Expansion Strategy, Blinkit (Zomato)  
**Date:** June 2026  
**Classification:** Internal Strategy Document

---

## Executive Summary

Delhi-NCR's quick commerce market is in a land-grab phase. Blinkit, Zepto, and Swiggy Instamart collectively operate approximately **120 dark stores** across the region — but coverage is heavily skewed toward South Delhi, Central Delhi, and the Noida Sector 18–62 corridor. This analysis applies a **Dark Store Opportunity Index (DSOI)** to identify the 10 highest-priority whitespace zones where new store openings would capture the most addressable demand before competitors entrench.

**Bottom line:** 3 corridor clusters — Outer North-West Delhi, Outer East Delhi, and emerging Gurgaon periphery — represent the largest uncaptured demand pools, with a combined estimated addressable volume of **3,800–5,200 daily orders** and an estimated **₹4.3–5.9 crore in monthly GMV**.

---

## Problem Definition

> *"Where in Delhi-NCR should Blinkit open its next 10 dark stores to maximise order volume and GMV per store, while minimising cannibalisation of existing stores?"*

This is a constrained optimisation problem with four key variables:
1. **Population density** — more potential customers per km²
2. **Distance from existing coverage** — avoids cannibalisation, captures whitespace
3. **Income/spending power** — drives basket size and order frequency
4. **Delivery demand signal** — commercial activity and food delivery density as proxy

---

## Methodology Summary

| Component | Variable | Weight |
|---|---|---|
| Population Density Score | Persons per km², normalised | 35% |
| Distance to Nearest Dark Store | km from zone centroid, normalised | 35% |
| Income / Spending Power Proxy | Housing type + income index, normalised | 20% |
| Delivery Demand Proxy | Food delivery POI density + commercial activity | 10% |

Zones within **1.5km of any existing dark store** are classified as covered and excluded. Final DSOI scores run 0–100.

Full methodology: see `docs/methodology.md`

---

## Key Findings

### Finding 1 — North-West Delhi is the Largest Whitespace by Population
The Rohini outer sectors (Sector 24–27), Bawana, and the Narela corridor together house an estimated 1.2 million residents with only 2–3 dark stores within a 5km radius. Population density in this belt runs 28,000–42,000/km² — comparable to fully served zones in South Delhi — but dark store penetration is a fraction of that.

### Finding 2 — Outer East Delhi Has the Best Density-to-Coverage Ratio
Kondli, Gharoli, Trilokpuri Extension, and Mayur Vihar Phase III are dense, mid-income residential clusters with virtually zero dark store coverage. The nearest Instamart or Blinkit store in most of this zone sits 4–6km away — well beyond the effective delivery radius.

### Finding 3 — Gurgaon's Southern Sectors Are a Missed Premium Opportunity
Sectors 56–70 in Gurgaon (Sohna Road corridor, Southern Peripheral Road) have seen rapid residential development since 2022. Income proxies in this belt are among the highest in NCR — comparable to Golf Course Road — but dark store coverage ends at Sector 56. Average basket size in premium zones is 35–40% higher than mid-income zones, making each store economically more attractive despite similar order volumes.

### Finding 4 — Brand Concentration Creates Vulnerability
Of existing dark stores in the seed dataset, Blinkit accounts for ~45% of locations but is under-represented in East Delhi relative to Zepto. If Blinkit does not move into the Outer East corridor in the next 2 quarters, Zepto will likely establish first-mover advantage in a high-density, fast-growing market.

---

## Top 10 Expansion Zone Rankings

| Rank | Zone | Type | DSOI | Est. Daily Orders | Avg. Basket | Priority Action |
|---|---|---|---|---|---|---|
| 1 | Bawana–Narela Belt | Peri-urban | 93.1 | 680 | ₹310 | Immediate — high density, zero coverage |
| 2 | Kondli–Gharoli (East) | Urban | 90.4 | 720 | ₹340 | Immediate — largest unserved cluster |
| 3 | Rohini Sec 24–27 | Urban | 87.8 | 610 | ₹360 | Q3 priority — high density + income |
| 4 | Gurgaon Sec 65–70 | Suburban | 84.2 | 490 | ₹520 | Q3 priority — premium basket |
| 5 | Mustafabad–Karawal | Urban | 80.6 | 540 | ₹290 | Q3 — density play |
| 6 | Trilokpuri Extension | Urban | 77.3 | 480 | ₹320 | Q4 — mid-income cluster |
| 7 | Dwarka Sec 22–25 | Suburban | 74.9 | 420 | ₹400 | Q4 — western expansion |
| 8 | Faridabad New Town | Suburban | 71.2 | 390 | ₹330 | Q4 — NCR periphery |
| 9 | Burari–Mukherjee Nagar | Urban | 67.8 | 360 | ₹350 | Q4 — North Delhi gap |
| 10 | Greater Noida West | Suburban | 64.5 | 320 | ₹380 | H1 2027 — emerging township |

---

## Strategic Recommendations

### Recommendation 1 — Open Zones 1 and 2 Simultaneously in Q3
Kondli–Gharoli and Bawana–Narela are geographically separated enough that a simultaneous opening avoids cannibalisation while signalling to Zepto that Blinkit is moving into both corridors at once. A staggered approach risks Zepto establishing a first-mover advantage in whichever zone opens second.

### Recommendation 2 — Zone 4 (Gurgaon Sec 65–70) Should Be Anchored to a Residential Complex
Premium quick-commerce works best when anchored near a large residential society (1,000+ units). The Southern Peripheral Road corridor has multiple such societies (Vipul Belmonte, Vatika City, M3M). Negotiating preferred placement within or adjacent to one of these would reduce customer acquisition cost significantly.

### Recommendation 3 — Do Not Open Zone 10 Before Zone 8 or 9
Greater Noida West has strong long-term potential but current population density is still ramping (township under construction). Opening there before filling the Faridabad and Burari gaps would misallocate store capacity. Recommend revisiting in H1 2027 once population consolidation is clearer.

### Recommendation 4 — Use Delivery Heatmaps from Existing Stores to Validate Before Committing
The DSOI model uses proxies for demand. Before finalising site selection in any zone, overlay 90-day delivery heatmap data from the nearest existing store to confirm demand direction. If >15% of orders in a neighbouring store are traveling >2km toward the target zone, that is a strong validation signal.

---

## Financial Impact Summary

| Scenario | Daily Orders | Monthly GMV | Annual GMV |
|---|---|---|---|
| Conservative (Zones 1–3 only) | 2,010 | ₹1.87 Cr | ₹22.5 Cr |
| Base case (Zones 1–7) | 3,940 | ₹4.31 Cr | ₹51.7 Cr |
| Full rollout (All 10 zones) | 5,010 | ₹5.63 Cr | ₹67.5 Cr |

*Assumes avg. basket ₹380, 30-day month. Excludes take rate, return orders, and opex.*

---

## Caveats and Limitations

- Income proxy is derived from housing classification data, not actual spending data — actual basket sizes will vary
- 1.5km coverage radius is conservative; Blinkit's actual delivery radius varies by store and time-of-day
- Dark store seed locations are approximate; actual store count and placement may differ
- Model does not account for road network topology — some zones with high DSOI may have poor road connectivity

---

## Next Steps

1. Validate Zones 1–3 with internal delivery heatmap data before lease commitment
2. Begin captain/rider supply build in Zones 1 and 2 (6–8 week lead time before store launch)
3. Re-run model quarterly as new stores open — DSOI scores for adjacent zones will shift
4. Extend model to Lucknow and Jaipur using same framework for Tier-2 expansion roadmap

---

*This brief was produced as part of an independent data analytics project. All demand estimates are based on publicly available data and modelling assumptions. Actual figures will vary.*
