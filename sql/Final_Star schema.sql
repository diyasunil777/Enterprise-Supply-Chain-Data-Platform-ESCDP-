/*
ESCDP STAR SCHEMA - PostgreSQL
Target schema: warehouse
Source schema: public

IMPORTANT:
1. Back up the database before running this script.
2. The DROP statements below remove ONLY the warehouse star-schema tables,
   not the raw source tables in public.
3. Recreate the warehouse tables before rerunning Pentaho loads, otherwise
   CREATE TABLE IF NOT EXISTS will not repair an existing incorrect structure.
4. Product-to-inventory and procurement-to-vendor mappings must be validated
   against real source data before filling those foreign keys.
5. PostgreSQL 15+ is required for UNIQUE NULLS NOT DISTINCT.
*/

CREATE SCHEMA IF NOT EXISTS warehouse;

BEGIN;

DROP TABLE IF EXISTS warehouse.fact_delivery CASCADE;
DROP TABLE IF EXISTS warehouse.fact_procurement CASCADE;
DROP TABLE IF EXISTS warehouse.fact_warehouse CASCADE;
DROP TABLE IF EXISTS warehouse.fact_shipping CASCADE;
DROP TABLE IF EXISTS warehouse.fact_inventory CASCADE;
DROP TABLE IF EXISTS warehouse.fact_order_sales CASCADE;

DROP TABLE IF EXISTS warehouse.dim_order CASCADE;
DROP TABLE IF EXISTS warehouse.dim_shipping_mode CASCADE;
DROP TABLE IF EXISTS warehouse.dim_vendor CASCADE;
DROP TABLE IF EXISTS warehouse.dim_warehouse CASCADE;
DROP TABLE IF EXISTS warehouse.dim_geography CASCADE;
DROP TABLE IF EXISTS warehouse.dim_product CASCADE;
DROP TABLE IF EXISTS warehouse.dim_customer CASCADE;
DROP TABLE IF EXISTS warehouse.dim_date CASCADE;

-- 1. DATE DIMENSION
CREATE TABLE warehouse.dim_date (
    date_key       INTEGER PRIMARY KEY, -- YYYYMMDD
    full_date      DATE NOT NULL UNIQUE,
    day_number     SMALLINT NOT NULL,
    month_number   SMALLINT NOT NULL,
    month_name     TEXT NOT NULL,
    quarter_number SMALLINT NOT NULL,
    year_number    INTEGER NOT NULL,
    day_of_week    SMALLINT NOT NULL,
    day_name       TEXT NOT NULL
);

-- 2. CUSTOMER DIMENSION
CREATE TABLE warehouse.dim_customer (
    customer_key     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id      TEXT NOT NULL UNIQUE,
    first_name       TEXT,
    last_name        TEXT,
    email            TEXT,
    customer_segment TEXT,
    city             TEXT,
    state            TEXT,
    country          TEXT,
    zipcode          TEXT,
    street           TEXT
);

-- 3. PRODUCT DIMENSION
-- product_id is sourced from WMS Product Card Id.
-- Do not substitute Order Item Cardprod Id unless validated as the same key.
CREATE TABLE warehouse.dim_product (
    product_key         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id          TEXT UNIQUE,
    product_name        TEXT,
    product_status      TEXT,
    product_image       TEXT,
    category_id         TEXT,
    category_name       TEXT,
    department_id       TEXT,
    department_name     TEXT,
    product_card_id     TEXT,
    product_category_id TEXT
);

-- 4. GEOGRAPHY DIMENSION
CREATE TABLE warehouse.dim_geography (
    geography_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city          TEXT,
    state         TEXT,
    country       TEXT,
    region         TEXT,
    market         TEXT,
    latitude       NUMERIC(12,8),
    longitude      NUMERIC(12,8),
    CONSTRAINT dim_geography_location_uk
      UNIQUE NULLS NOT DISTINCT (city, state, country, region, market)
);

-- 5. WAREHOUSE DIMENSION
CREATE TABLE warehouse.dim_warehouse (
    warehouse_key          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    distribution_center_id TEXT NOT NULL UNIQUE,
    warehouse_name         TEXT,
    warehouse_type         TEXT,
    region                 TEXT,
    city                   TEXT,
    country                TEXT,
    manager_id             TEXT,
    storage_type           TEXT,
    dock_doors             INTEGER,
    employees              INTEGER,
    operating_shift        TEXT,
    status                 TEXT
);

-- 6. VENDOR DIMENSION
-- Current vendor_management_2000 source only has ID and Vendor.
-- Additional columns remain nullable until a verified source mapping exists.
CREATE TABLE warehouse.dim_vendor (
    vendor_key         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vendor_id          TEXT,
    vendor_name        TEXT,
    manufacturing_site TEXT,
    country            TEXT,
    managed_by         TEXT,
    fulfill_via        TEXT,
    vendor_inco_term   TEXT,
    shipment_mode      TEXT,
    CONSTRAINT dim_vendor_business_key_uk
      UNIQUE NULLS NOT DISTINCT (vendor_id, vendor_name, manufacturing_site)
);

-- 7. SHIPPING MODE DIMENSION
CREATE TABLE warehouse.dim_shipping_mode (
    shipping_mode_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipping_mode     TEXT NOT NULL UNIQUE
);

-- 8. ORDER DIMENSION
CREATE TABLE warehouse.dim_order (
    order_key      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id       TEXT NOT NULL UNIQUE,
    order_type     TEXT,
    order_status   TEXT,
    customer_id    TEXT,
    order_date     DATE,
    geography_key  BIGINT REFERENCES warehouse.dim_geography(geography_key)
);

-- FACT 1: ORDER SALES
-- One row per order. Aggregate source ERP lines carefully before loading.
CREATE TABLE warehouse.fact_order_sales (
    sales_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_key      BIGINT REFERENCES warehouse.dim_order(order_key),
    customer_key   BIGINT REFERENCES warehouse.dim_customer(customer_key),
    order_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    geography_key  BIGINT REFERENCES warehouse.dim_geography(geography_key),
    source_order_id TEXT NOT NULL UNIQUE,
    sales_amount       NUMERIC(18,2),
    sales_per_customer NUMERIC(18,2),
    order_profit       NUMERIC(18,2),
    benefit_per_order  NUMERIC(18,2),
    profit_ratio       NUMERIC(12,6)
);

-- FACT 2: INVENTORY / ORDER ITEMS
-- product_key is nullable until a trustworthy item-to-product mapping is available.
-- The current inventory source has no item identifier, so do not join product by order ID alone.
CREATE TABLE warehouse.fact_inventory (
    inventory_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_key      BIGINT REFERENCES warehouse.dim_order(order_key),
    product_key    BIGINT REFERENCES warehouse.dim_product(product_key),
    source_order_id TEXT,
    source_item_id  TEXT,
    source_record_hash TEXT NOT NULL UNIQUE,
    quantity             NUMERIC(18,3),
    product_price        NUMERIC(18,2),
    item_product_price   NUMERIC(18,2),
    item_total           NUMERIC(18,2),
    discount_amount      NUMERIC(18,2),
    discount_rate        NUMERIC(12,6)
);

-- FACT 3: SHIPPING
CREATE TABLE warehouse.fact_shipping (
    shipping_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_key         BIGINT REFERENCES warehouse.dim_order(order_key),
    shipping_mode_key BIGINT REFERENCES warehouse.dim_shipping_mode(shipping_mode_key),
    shipping_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    source_order_id   TEXT NOT NULL UNIQUE,
    late_delivery_risk INTEGER,
    actual_shipping_days NUMERIC(10,2),
    scheduled_shipping_days NUMERIC(10,2),
    delivery_status TEXT
);

-- FACT 4: WAREHOUSE SNAPSHOTS
-- One row per source warehouse/product/date combination where the source supports it.
CREATE TABLE warehouse.fact_warehouse (
    warehouse_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_key BIGINT REFERENCES warehouse.dim_warehouse(warehouse_key),
    product_key   BIGINT REFERENCES warehouse.dim_product(product_key),
    date_key      INTEGER REFERENCES warehouse.dim_date(date_key),
    source_snapshot_hash TEXT NOT NULL UNIQUE,
    inventory_units         NUMERIC(18,3),
    storage_capacity_units  NUMERIC(18,3),
    occupied_capacity_units NUMERIC(18,3),
    utilization_pct         NUMERIC(12,4),
    inbound_shipments       INTEGER,
    outbound_shipments      INTEGER,
    orders_processed        INTEGER,
    avg_processing_hours    NUMERIC(12,3),
    on_time_dispatch_pct    NUMERIC(12,4),
    damaged_units           NUMERIC(18,3),
    stockout_flag           BOOLEAN
);

-- FACT 5: PROCUREMENT
CREATE TABLE warehouse.fact_procurement (
    procurement_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vendor_key BIGINT REFERENCES warehouse.dim_vendor(vendor_key),
    source_procurement_id TEXT NOT NULL UNIQUE,
    project_code           TEXT,
    purchase_order_number  TEXT,
    product_group          TEXT,
    sub_classification     TEXT,
    molecule_test_type     TEXT,
    dosage                 TEXT,
    dosage_form            TEXT,
    scheduled_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    delivered_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    line_item_quantity NUMERIC(18,3),
    line_item_value    NUMERIC(18,2),
    pack_price         NUMERIC(18,2),
    unit_price         NUMERIC(18,2),
    weight_kg          NUMERIC(18,3),
    freight_cost       NUMERIC(18,2),
    insurance_cost     NUMERIC(18,2)
);

-- FACT 6: DELIVERY
-- This is sourced from procurement_2001 date/order records unless a separate
-- delivery source with matching business keys becomes available.
CREATE TABLE warehouse.fact_delivery (
    delivery_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vendor_key BIGINT REFERENCES warehouse.dim_vendor(vendor_key),
    source_record_id TEXT NOT NULL UNIQUE,
    purchase_order_number TEXT,
    asn_dn_number TEXT,
    scheduled_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    delivered_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    recorded_date_key  INTEGER REFERENCES warehouse.dim_date(date_key),
    delivery_days NUMERIC(10,2),
    is_delivered BOOLEAN
);

-- Date dimension covers the source data range commonly used in the project.
-- Extend the range if source dates fall outside 2000-2035.
INSERT INTO warehouse.dim_date
(date_key, full_date, day_number, month_number, month_name,
 quarter_number, year_number, day_of_week, day_name)
SELECT
    TO_CHAR(d::date, 'YYYYMMDD')::INTEGER,
    d::date,
    EXTRACT(DAY FROM d)::SMALLINT,
    EXTRACT(MONTH FROM d)::SMALLINT,
    TO_CHAR(d::date, 'FMMonth'),
    EXTRACT(QUARTER FROM d)::SMALLINT,
    EXTRACT(YEAR FROM d)::INTEGER,
    EXTRACT(ISODOW FROM d)::SMALLINT,
    TO_CHAR(d::date, 'FMDay')
FROM generate_series(DATE '2000-01-01', DATE '2035-12-31', INTERVAL '1 day') AS g(d)
ON CONFLICT (date_key) DO NOTHING;

COMMIT;

-- Verify the warehouse tables 
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'warehouse'
ORDER BY table_name;
