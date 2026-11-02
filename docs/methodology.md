# Methodology: Dark Store Opportunity Index (DSOI)

## Overview

The Dark Store Opportunity Index (DSOI) is a composite scoring model that identifies residential zones in Delhi-NCR where quick-commerce dark store expansion would generate the highest return, while minimising cannibalisation of existing stores.

---

## Data Pipeline

```
OpenStreetMap (Overpass API)         Census of India / data.gov.in
        │                                        │
        ▼                                        ▼
Existing Dark Store Locations        Demand Zone Grid (150 cells)
(Blinkit, Zepto, Instamart)         (population density, income proxy)
        │                                        │
        └──────────────┬─────────────────────────┘
                       ▼
         Distance Computation (UTM Zone 43N)
         + Coverage Flagging (1.5km radius)
                       ▼
              DSOI Scoring (4-variable composite)
                       ▼
         Top-N Expansion Zone Recommendations
                       ▼
      Interactive Map + Strategy Brief + Charts
```

---

## Variable Definitions

### 1. Population Density Score (weight: 35%)
- **Source:** Census of India ward-level data + parametric model
- **Unit:** Persons per km²
- **Rationale:** More residents = more potential customers = higher addressable order volume

### 2. Distance to Nearest Dark Store Score (weight: 35%)
- **Source:** Computed from existing store coordinates
- **Projection:** EPSG:32643 (UTM Zone 43N) for metric accuracy
- **Unit:** km, **capped at 6km** before normalisation
- **Coverage threshold:** Zones within 1.5km of any existing store are classified as covered (DSOI = 0)
- **Rationale:** Captures true whitespace; avoids recommending zones that would cannibalise existing stores. The 6km cap prevents a single sparsely populated cell at the edge of the NCR bounding box from dominating the score purely because it happens to be far from any store — beyond that radius a location is well outside any single new store's realistic catchment anyway.

### Density floor
Zones with population density below 3,000 persons/km² are excluded from ranking entirely (DSOI forced to 0). In the synthetic grid these are open land or undeveloped periphery, not real residential catchments an expansion team would ever shortlist. Without this floor, the distance term combined with a high income proxy could push a nearly empty cell into the top-10 ahead of genuinely dense, underserved metro-core zones.

### 3. Income / Spending Power Score (weight: 20%)
- **Source:** Housing type classification (OSM) + Census income decile
- **Range:** 0–1 (1 = highest income)
- **Rationale:** Higher income zones have larger basket sizes and higher order frequency. Even with lower density, a premium zone may generate more GMV per store.

### 4. Delivery Demand Proxy Score (weight: 10%)
- **Source:** Commercial POI density (restaurants, offices, markets) from OSM
- **Rationale:** Commercial activity signals trip-generating demand beyond pure residential use. Zones near office parks or markets see higher daytime order volumes.

---

## Composite Formula

```
DSOI_raw = (0.35 × density_norm)
         + (0.35 × distance_norm)
         + (0.20 × income_norm)
         + (0.10 × delivery_demand_norm)

DSOI_score = (DSOI_raw / max(DSOI_raw)) × 100
```

All sub-scores normalised to [0, 1] using MinMaxScaler before weighting.

---

## Tier Classification

| Tier | Rule | Interpretation |
|---|---|---|
| Covered | within 1.5 km of an existing store | Already served, DSOI forced to 0 |
| Excluded (Low Density) | density < 3,000 / km² | Open land or periphery, DSOI forced to 0 |
| Low Opportunity | DSOI 0–35 | Limited whitespace or low density |
| Medium Opportunity | DSOI 35–60 | Meaningful gap |
| High Opportunity | DSOI 60–100 | Large unserved population with spending power |

*(An earlier version labelled every zero-score zone "Covered", which inflated the covered count from 6 to 86.)*

---

## Order Demand Estimation

Each top-10 zone is sized as **one new store** serving its delivery radius. A single store can't serve a whole ~34 km² grid cell, so the cell-level figure is kept only as a ceiling.

```
Catchment area   = pi x r²  (r = 1.5 km -> 7.07 km², capped at the zone area)
Catchment pop.   = Population Density x Catchment area

Daily Order Rate:
  High income zones (income_proxy >= 0.6): 8 orders / 1,000 residents / day
  Mid income zones  (income_proxy <  0.6): 4 orders / 1,000 residents / day

Daily Orders     = Catchment pop. x Daily Order Rate / 1,000
Daily GMV (Rs)   = Daily Orders x Rs 380 (avg. basket size)
Monthly GMV (Rs) = Daily GMV x 30

Zone ceiling     = Population Density x Zone area x Rate / 1,000   (reported separately)
```

**Basket size assumption (₹380):** based on reported Blinkit average order values for 2024–25 across Delhi-NCR mid-income zones. Premium zones (income_proxy ≥ 0.75) may run ₹480–520. Every assumption is an editable input in `outputs/excel/Dark_Store_Expansion_Model.xlsx`.

---

## Sensitivity Analysis (`src/analysis.py`)

| Test | Method | Result (this run) |
|---|---|---|
| Weight uncertainty | 1,000 Dirichlet draws centred on 35/35/20/10 (concentration 50, so each weight moves about ±20%) | Median draw keeps 9/10; 7 zones are in the top 10 in ≥90% of draws |
| Named scenarios | Distance-, income-, density-heavy and equal weights | 8–9 of 10 retained |
| Coverage radius | 1.0 to 3.0 km for existing stores | Top 10 unchanged |
| Density floor | 0 to 5,000 / km² | Unchanged up to 4,000; 9/10 at 5,000 |

---

## Why 1.5km Coverage Radius?

Quick-commerce platforms promise 10–15 minute delivery. At an average delivery speed of 15 km/h (accounting for traffic), 1.5km is the maximum comfortable radius for consistent sub-15-minute performance. Some operators use 2km in off-peak hours, but 1.5km is the conservative threshold for full-day consistency.

---

## Limitations

| Assumption | Potential Bias |
|---|---|
| Straight-line distance (not road network) | Underestimates true delivery complexity in dense areas |
| 2011 Census base population | Peri-urban zones 20–35% denser in reality by 2026 |
| Uniform delivery radius (1.5km) | Actual radius varies by time of day and road quality |
| Income proxy from housing type | Informal settlements may have higher spending than proxy suggests |
| Fixed basket size (₹380) | Varies significantly by zone type and category mix |

---

## Reproducibility

- **Dark store locations:** real data — OpenStreetMap via Overpass API, with a hand-built fallback seed list of ~38 real, named Blinkit/Zepto/Instamart locations if the API returns too little
- **Demand zone population density, income proxy, delivery-demand signal:** synthetic — `data_loader.generate_demand_grid()` produces a fully reproducible parametric multi-center density model calibrated to known Delhi-NCR geography (4 real urban centers: CP, Gurgaon, Noida, Rohini), **not** sourced from Census or any official dataset

See the README's "Data Status" section for the full real-vs-synthetic breakdown and the reasoning behind it.

---

## Data Engineering Layer

This methodology document covers the *modelling* logic (`opportunity_model.py`). A separate, additive data engineering layer (`schemas.py` + `pipeline.py`) wraps the same data sources in explicit Extract → Validate → Transform → Load stages, with Pandera schema validation and idempotent SQLite persistence. See the README's "Data Engineering Layer" section for details, or run `python src/pipeline.py` directly.
