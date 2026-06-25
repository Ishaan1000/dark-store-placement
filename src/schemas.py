"""
schemas.py
==========
Pandera schema definitions for the Dark Store Placement Intelligence project.

Validation contract between raw data sources (OSM API / fallback seed
list / synthetic demand grid) and the modelling layer in
opportunity_model.py. Run at the end of extraction, before persistence
or modelling.

Author: Ishaan Mankotia
"""

from pandera.pandas import Column, DataFrameSchema, Check

# ─────────────────────────────────────────────
# DARK STORES SCHEMA
# ─────────────────────────────────────────────

dark_stores_schema = DataFrameSchema(
    {
        "name": Column(str, Check.str_length(min_value=1), nullable=False),
        "brand": Column(
            str,
            Check.isin(["Blinkit", "Zepto", "Instamart", "Unknown"]),
            nullable=False,
        ),
        "lat": Column(float, Check.in_range(28.0, 29.2), nullable=False),
        "lon": Column(float, Check.in_range(76.5, 77.8), nullable=False),
    },
    unique=["name", "lat", "lon"],
    strict=False,
    coerce=True,
)

# ─────────────────────────────────────────────
# DEMAND ZONES SCHEMA
# ─────────────────────────────────────────────

demand_zones_schema = DataFrameSchema(
    {
        "zone_id": Column(str, Check.str_matches(r"^Z\d{3}$"), unique=True, nullable=False),
        "lat_center": Column(float, Check.in_range(28.0, 29.2), nullable=False),
        "lon_center": Column(float, Check.in_range(76.5, 77.8), nullable=False),
        "zone_type": Column(
            str,
            Check.isin(["Metro Core", "Urban", "Suburban", "Peri-urban"]),
            nullable=False,
        ),
        "population_density": Column(
            float,
            checks=[
                Check.greater_than_or_equal_to(0),
                Check.less_than_or_equal_to(100_000),
            ],
            nullable=False,
        ),
        "income_proxy": Column(float, Check.in_range(0.0, 1.0), nullable=False),
        "delivery_demand": Column(
            float, Check.greater_than_or_equal_to(0), nullable=False
        ),
        "area_km2": Column(float, Check.greater_than(0), nullable=False),
    },
    strict=False,
    coerce=True,
)


def validate_dark_stores(df) -> bool:
    """Validates dark store locations against dark_stores_schema."""
    dark_stores_schema.validate(df, lazy=True)
    return True


def validate_demand_zones(df) -> bool:
    """Validates demand zone grid against demand_zones_schema."""
    demand_zones_schema.validate(df, lazy=True)
    return True
