"""
pipeline.py
===========
Data engineering layer for the Dark Store Placement Intelligence project.

Wraps the existing data_loader.py functions (fetch_dark_stores,
generate_demand_grid) in an explicit Extract -> Validate -> Transform ->
Load pipeline, persisting clean, schema-validated tables to a local
SQLite database (outputs/dark_store.db) in addition to the CSV/GeoJSON
outputs the rest of the project already produces.

This module is additive: it does not change the behaviour of
opportunity_model.py or any notebook. Run it standalone with:

    python src/pipeline.py

Author: Ishaan Mankotia
"""

import os
import sqlite3
import logging
from datetime import datetime, timezone

import pandas as pd

from data_loader import fetch_dark_stores, generate_demand_grid
from schemas import validate_dark_stores, validate_demand_zones

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("dark_store_pipeline")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "outputs", "dark_store.db")


# ─────────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────────

def extract() -> dict:
    """
    EXTRACT stage: pulls raw dark store locations and demand zone grid
    using the existing data_loader functions. No transformation or
    validation here.
    """
    log.info("EXTRACT — fetching dark store locations (OSM, with fallback)")
    stores_raw = fetch_dark_stores()

    log.info("EXTRACT — generating demand zone grid")
    zones_raw = generate_demand_grid()

    log.info(f"EXTRACT complete — {len(stores_raw)} stores, {len(zones_raw)} zones")
    return {"stores": stores_raw, "zones": zones_raw}


# ─────────────────────────────────────────────
# VALIDATE
# ─────────────────────────────────────────────

def validate(raw: dict) -> dict:
    """
    VALIDATE stage: runs each table against its pandera schema.
    Fails loudly and immediately on a contract violation — intentionally
    not caught here, since a validation failure should halt the
    pipeline rather than be silently logged and ignored.
    """
    log.info("VALIDATE — checking dark stores against schema")
    stores = raw["stores"]
    if "lat" not in stores.columns:
        stores = stores.assign(lat=stores.geometry.y, lon=stores.geometry.x)
    validate_dark_stores(stores[["name", "brand", "lat", "lon"]])

    log.info("VALIDATE — checking demand zones against schema")
    validate_demand_zones(raw["zones"])

    log.info("VALIDATE complete — both tables conform to schema")
    return raw


# ─────────────────────────────────────────────
# TRANSFORM
# ─────────────────────────────────────────────

def transform(validated: dict) -> dict:
    """
    TRANSFORM stage: light cleaning/normalisation before load.
    - Drops exact-duplicate store rows (can happen with OSM tag overlap)
    - Flattens geometry to lat/lon for the SQLite table
    - Adds a load timestamp column for traceability
    """
    stores = validated["stores"].copy()
    zones = validated["zones"].copy()

    before = len(stores)
    stores = stores.drop_duplicates(subset=["name", "brand"]).reset_index(drop=True)
    if len(stores) < before:
        log.info(f"TRANSFORM — dropped {before - len(stores)} duplicate store rows")

    if "lat" not in stores.columns:
        stores["lat"] = stores.geometry.y
        stores["lon"] = stores.geometry.x

    load_ts = datetime.now(timezone.utc).isoformat()
    stores_flat = stores[["name", "brand", "lat", "lon"]].copy()
    stores_flat["loaded_at"] = load_ts

    zones_flat = zones.drop(columns=["geometry"]).copy()
    zones_flat["loaded_at"] = load_ts

    log.info(f"TRANSFORM complete — {len(stores_flat)} stores, {len(zones_flat)} zones ready to load")
    return {"stores": stores_flat, "zones": zones_flat, "stores_geo": stores, "zones_geo": zones}


# ─────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────

def load(transformed: dict, db_path: str = DB_PATH) -> None:
    """
    LOAD stage: writes clean tables to a local SQLite database.
    Uses 'replace' (not 'append') so this pipeline is idempotent —
    re-running it produces the same database state, not duplicate rows.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    log.info(f"LOAD — writing to {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        transformed["stores"].to_sql("dark_stores", conn, if_exists="replace", index=False)
        transformed["zones"].to_sql("demand_zones", conn, if_exists="replace", index=False)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT NOT NULL,
                store_row_count INTEGER NOT NULL,
                zone_row_count INTEGER NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO pipeline_runs (run_at, store_row_count, zone_row_count) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(),
             len(transformed["stores"]), len(transformed["zones"]))
        )
        conn.commit()
        log.info(f"LOAD complete — {len(transformed['stores'])} stores, "
                 f"{len(transformed['zones'])} zones committed to SQLite")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# DATA QUALITY REPORT
# ─────────────────────────────────────────────

def generate_quality_report(transformed: dict, output_path: str = None) -> str:
    """Produces a short, human-readable data quality summary."""
    stores = transformed["stores"]
    zones = transformed["zones"]

    lines = [
        "# Data Quality Report — Dark Store Placement Intelligence",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}",
        "\n## Dark Stores",
        f"- Row count: {len(stores)}",
        f"- Null values: {stores.isnull().sum().sum()}",
        f"- Unique stores (name+brand): {stores.drop_duplicates(subset=['name','brand']).shape[0]}",
        f"- Brand distribution:\n{stores['brand'].value_counts().to_string()}",
        f"- Latitude range: {stores['lat'].min():.4f} to {stores['lat'].max():.4f} "
        f"(schema bound: 28.0–29.2)",
        f"- Longitude range: {stores['lon'].min():.4f} to {stores['lon'].max():.4f} "
        f"(schema bound: 76.5–77.8)",
        "\n## Demand Zones",
        f"- Row count: {len(zones)}",
        f"- Null values: {zones.isnull().sum().sum()}",
        f"- Unique zone_id: {zones['zone_id'].nunique()} (should equal row count)",
        f"- Population density range: {zones['population_density'].min():.0f} to "
        f"{zones['population_density'].max():.0f} (schema ceiling: 100,000)",
        f"- Income proxy range: {zones['income_proxy'].min():.3f} to "
        f"{zones['income_proxy'].max():.3f} (schema bound: 0.0–1.0)",
        f"- Zone type distribution:\n{zones['zone_type'].value_counts().to_string()}",
        "\n## Schema Validation",
        "- Both tables passed `schemas.py` validation (lat/lon bounds, brand "
        "enum, income proxy range, population density ceiling, zone type "
        "enum, zone_id uniqueness and format) before being loaded to SQLite.",
        "- See `src/schemas.py` for the full pandera schema definitions.",
    ]

    report = "\n".join(lines)
    if output_path:
        with open(output_path, "w") as f:
            f.write(report)
        log.info(f"Data quality report written to {output_path}")
    return report


# ─────────────────────────────────────────────
# PIPELINE ENTRYPOINT
# ─────────────────────────────────────────────

def run_pipeline() -> dict:
    """Runs the full Extract -> Validate -> Transform -> Load pipeline."""
    log.info("=" * 60)
    log.info("Starting Dark Store Placement data pipeline")
    log.info("=" * 60)

    raw = extract()
    validated = validate(raw)
    transformed = transform(validated)
    load(transformed)

    report_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "data_quality_report.md")
    generate_quality_report(transformed, output_path=report_path)

    log.info("=" * 60)
    log.info("Pipeline complete.")
    log.info("=" * 60)
    return transformed


if __name__ == "__main__":
    run_pipeline()
