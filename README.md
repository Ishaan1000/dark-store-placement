# 🛒 Dark Store Placement Intelligence
### *Where should Blinkit open next in Delhi-NCR?*

---

## 📌 Problem Statement

India's quick commerce sector crossed **$5 billion in GMV in 2025**, with Blinkit, Zepto, and Swiggy Instamart competing aggressively for micro-market dominance. Every new dark store represents a ₹1–3 crore infrastructure investment — and placement decisions are made on a combination of gut feel, existing delivery data, and ad hoc analysis.

This project builds a **data-driven dark store placement model** that answers a real question Blinkit's expansion team faces every quarter:

> **"Which residential clusters in Delhi-NCR are underserved by current dark store coverage, and which 10 zones should we open in next?"**

---

## 🎯 Project Objectives

1. Map all existing Blinkit / Zepto / Swiggy Instamart dark store locations in Delhi-NCR
2. Compute coverage gaps using 2km delivery radius analysis
3. Score each zone on a **Dark Store Opportunity Index (DSOI)**: population density, income proxy, delivery demand signals, and distance to nearest dark store
4. Identify top 10 expansion zones with estimated daily order potential
5. Deliver a strategy brief framed as a memo to Blinkit's Head of Expansion

---

## 📁 Repository Structure

```
dark-store-placement/
│
├── data/
│   ├── raw/                        # Source data
│   └── processed/                  # Cleaned, merged datasets
│
├── notebooks/
│   ├── 01_data_collection.ipynb    # Dark store + ward data ingestion
│   ├── 02_eda_and_cleaning.ipynb   # Coverage and demand EDA
│   ├── 03_opportunity_model.ipynb  # DSOI scoring model
│   └── 04_visualization.ipynb      # Maps and charts
│
├── src/
│   ├── data_loader.py              # Data ingestion functions
│   ├── opportunity_model.py        # DSOI scoring logic
│   └── visualizer.py               # Map and chart generation
│
├── outputs/
│   ├── dark_store_opportunity_map.html   # Interactive Folium map
│   ├── top10_expansion_zones.csv         # Final ranked zones
│   └── strategy_brief.md                 # Consulting recommendation memo
│
├── docs/
│   └── methodology.md              # Detailed methodology
│
├── requirements.txt
└── README.md
```

---

## 📊 Data Sources

| Dataset | Source | Format |
|---|---|---|
| Existing dark store locations | OpenStreetMap (supermarket/convenience tags) + manual seed | GeoJSON |
| Ward population density | Census of India 2011 via data.gov.in | CSV |
| Delhi-NCR ward boundaries | Delhi Open Govt Data | GeoJSON |
| Residential density proxy | OSM building footprint density | GeoJSON |
| Income proxy | Housing type classification (OSM + Census) | Derived |

---

## 🧮 Dark Store Opportunity Index (DSOI)

```
DSOI = (0.35 × Population Density Score)
     + (0.35 × Distance to Nearest Dark Store Score)
     + (0.20 × Income / Spending Power Score)
     + (0.10 × Delivery Demand Proxy Score)
```

- **Higher score = bigger whitespace = higher expansion priority**
- Zones within 1.5km of an existing dark store are classified as already covered
- Income proxy derived from residential housing classification

---

## 🗺️ Key Output: Interactive Opportunity Map

The interactive map shows:
- 🔴 Existing dark store locations with 2km delivery radii
- 🟠 High-opportunity zones (DSOI top quartile)
- 📍 Top 10 ranked expansion sites with order demand estimates
- 🏘️ Ward choropleth coloured by DSOI tier

---

## 💼 Strategy Brief Summary

> *Full brief in `outputs/strategy_brief.md`*

**Top Insight:** Delhi-NCR's current ~120 dark stores are heavily concentrated in South Delhi and Central NCR (Noida Sector 18–62 corridor). North-West Delhi, Outer East Delhi, and Faridabad's newer residential sectors represent 40%+ of the city's addressable population with less than 15% of current dark store coverage.

**Recommendation:** 3 zones in North-West Delhi (Rohini outer sectors, Bawana) and 2 in Outer East (Kondli, Gharoli) should be prioritised for Q3 2026 store openings, with an estimated combined addressable demand of 3,200–4,500 orders/day.

---

## 🛠️ How to Run

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/dark-store-placement
cd dark-store-placement

# Install dependencies
pip install -r requirements.txt

# Run notebooks in order (01 → 04)
jupyter notebook

# Or run the full pipeline directly
python src/opportunity_model.py
```

---

## 📦 Requirements

```
pandas>=2.0
geopandas>=0.14
folium>=0.15
scikit-learn>=1.3
matplotlib>=3.7
seaborn>=0.12
requests>=2.31
numpy>=1.24
shapely>=2.0
notebook>=7.0
```

---

## 👤 Author

**Ishaan Mankotia**  
Associate Software Engineer @ Nagarro | B.Tech AI/ML, GGSIPU '25  
[LinkedIn](https://linkedin.com/in/YOUR_PROFILE) | [GitHub](https://github.com/Ishaan1000)

---

## 📄 License

MIT License
