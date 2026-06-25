# Data Quality Report — Dark Store Placement Intelligence

Generated: 2026-06-25T10:38:56.778913+00:00

## Dark Stores
- Row count: 38
- Null values: 0
- Unique stores (name+brand): 38
- Brand distribution:
brand
Blinkit      18
Zepto        13
Instamart     7
- Latitude range: 28.4198 to 28.7025 (schema bound: 28.0–29.2)
- Longitude range: 77.0315 to 77.5040 (schema bound: 76.5–77.8)

## Demand Zones
- Row count: 150
- Null values: 0
- Unique zone_id: 150 (should equal row count)
- Population density range: 300 to 26680 (schema ceiling: 100,000)
- Income proxy range: 0.351 to 1.000 (schema bound: 0.0–1.0)
- Zone type distribution:
zone_type
Urban         83
Suburban      37
Metro Core    27
Peri-urban     3

## Schema Validation
- Both tables passed `schemas.py` validation (lat/lon bounds, brand enum, income proxy range, population density ceiling, zone type enum, zone_id uniqueness and format) before being loaded to SQLite.
- See `src/schemas.py` for the full pandera schema definitions.