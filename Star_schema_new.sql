-- =====================================================
-- ESCDP STAR SCHEMA: DIMENSION TABLES
-- Database: PostgreSQL
-- Schema: public
-- =====================================================

-- 1. DATE DIMENSION
CREATE TABLE IF NOT EXISTS public.dim_date (
    date_key       INTEGER PRIMARY KEY, -- YYYYMMDD
    full_date      DATE UNIQUE,
    day_number     INTEGER,
    month_number   INTEGER,
    month_name     TEXT,
    quarter_number INTEGER,
    year_number    INTEGER,
    day_of_week    INTEGER,
    day_name       TEXT
);

-- 2. CUSTOMER DIMENSION
CREATE TABLE IF NOT EXISTS public.dim_customer (
    customer_key     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id      TEXT UNIQUE,
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
CREATE TABLE IF NOT EXISTS public.dim_product (
    product_key       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id        TEXT UNIQUE,
    product_name      TEXT,
    product_status    TEXT,
    product_image     TEXT,
    category_id       TEXT,
    category_name     TEXT,
    department_id     TEXT,
    department_name   TEXT,
    product_card_id   TEXT,
    product_category_id TEXT
);

-- 4. GEOGRAPHY DIMENSION
CREATE TABLE IF NOT EXISTS public.dim_geography (
    geography_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city          TEXT,
    state         TEXT,
    country       TEXT,
    region        TEXT,
    market        TEXT,
    latitude      NUMERIC(12, 8),
    longitude     NUMERIC(12, 8),
    UNIQUE NULLS NOT DISTINCT
        (city, state, country, region, market)
);

-- 5. WAREHOUSE / DISTRIBUTION CENTER DIMENSION
CREATE TABLE IF NOT EXISTS public.dim_warehouse (
    warehouse_key          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    distribution_center_id TEXT UNIQUE,
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
CREATE TABLE IF NOT EXISTS public.dim_vendor (
    vendor_key         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vendor_id          TEXT,
    vendor_name        TEXT,
    manufacturing_site TEXT,
    country            TEXT,
    managed_by         TEXT,
    fulfill_via        TEXT,
    vendor_inco_term   TEXT,
    shipment_mode      TEXT,
    UNIQUE (vendor_id, vendor_name, manufacturing_site)
);

-- 7. SHIPPING MODE DIMENSION
CREATE TABLE IF NOT EXISTS public.dim_shipping_mode (
    shipping_mode_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipping_mode     TEXT UNIQUE
);

-- 8. ORDER DIMENSION
CREATE TABLE IF NOT EXISTS public.dim_order (
    order_key    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id     TEXT UNIQUE,
    order_type   TEXT,
    order_status TEXT,
    customer_id  TEXT,
    order_date   DATE,
    geography_key BIGINT REFERENCES public.dim_geography(geography_key)
);

-- =====================================================
-- ESCDP STAR SCHEMA: FACT TABLES
-- =====================================================

-- 1. FACT ORDER SALES
-- Grain: one row per order.
CREATE TABLE IF NOT EXISTS public.fact_order_sales (
    sales_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_key      BIGINT REFERENCES public.dim_order(order_key),
    customer_key   BIGINT REFERENCES public.dim_customer(customer_key),
    order_date_key INTEGER REFERENCES public.dim_date(date_key),
    geography_key  BIGINT REFERENCES public.dim_geography(geography_key),

    source_order_id TEXT UNIQUE,

    sales_amount          NUMERIC(18, 2),
    sales_per_customer    NUMERIC(18, 2),
    order_profit          NUMERIC(18, 2),
    benefit_per_order     NUMERIC(18, 2),
    profit_ratio          NUMERIC(12, 6)
);

-- 2. FACT INVENTORY / ORDER ITEMS
-- Grain: one row per source inventory line.
CREATE TABLE IF NOT EXISTS public.fact_inventory (
    inventory_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_key      BIGINT REFERENCES public.dim_order(order_key),
    product_key    BIGINT REFERENCES public.dim_product(product_key),

    source_order_id TEXT,
    source_item_id  TEXT,

    quantity             NUMERIC(18, 3),
    product_price        NUMERIC(18, 2),
    item_product_price   NUMERIC(18, 2),
    item_total           NUMERIC(18, 2),
    discount_amount      NUMERIC(18, 2),
    discount_rate        NUMERIC(12, 6)
);

-- 3. FACT SHIPPING
-- Grain: one row per order, provided the source has
-- exactly one consolidated shipping record per order.
CREATE TABLE IF NOT EXISTS public.fact_shipping (
    shipping_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_key         BIGINT REFERENCES public.dim_order(order_key),
    shipping_mode_key BIGINT REFERENCES public.dim_shipping_mode(shipping_mode_key),
    shipping_date_key INTEGER REFERENCES public.dim_date(date_key),

    source_order_id TEXT UNIQUE,

    late_delivery_risk       INTEGER,
    actual_shipping_days     NUMERIC(10, 2),
    scheduled_shipping_days  NUMERIC(10, 2),
    delivery_status          TEXT
);

-- 4. FACT WAREHOUSE
-- Grain: one warehouse snapshot per date and product,
-- where the source data supports that level of detail.
CREATE TABLE IF NOT EXISTS public.fact_warehouse (
    warehouse_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    warehouse_key BIGINT REFERENCES public.dim_warehouse(warehouse_key),
    product_key   BIGINT REFERENCES public.dim_product(product_key),
    date_key      INTEGER REFERENCES public.dim_date(date_key),

    inventory_units        NUMERIC(18, 3),
    storage_capacity_units NUMERIC(18, 3),
    occupied_capacity_units NUMERIC(18, 3),
    utilization_pct        NUMERIC(12, 4),
    inbound_shipments      INTEGER,
    outbound_shipments     INTEGER,
    orders_processed       INTEGER,
    avg_processing_hours   NUMERIC(12, 3),
    on_time_dispatch_pct   NUMERIC(12, 4),
    damaged_units          NUMERIC(18, 3),
    stockout_flag          BOOLEAN
);

-- 5. FACT PROCUREMENT
-- Grain: one procurement line per source ID.
CREATE TABLE IF NOT EXISTS public.fact_procurement (
    procurement_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    vendor_key BIGINT REFERENCES public.dim_vendor(vendor_key),

    source_procurement_id TEXT,
    project_code           TEXT,
    purchase_order_number  TEXT,
    product_group          TEXT,
    sub_classification     TEXT,
    molecule_test_type     TEXT,
    dosage                 TEXT,
    dosage_form            TEXT,

    scheduled_date_key INTEGER REFERENCES public.dim_date(date_key),
    delivered_date_key INTEGER REFERENCES public.dim_date(date_key),

    line_item_quantity NUMERIC(18, 3),
    line_item_value    NUMERIC(18, 2),
    pack_price         NUMERIC(18, 2),
    unit_price         NUMERIC(18, 2),
    weight_kg          NUMERIC(18, 3),
    freight_cost       NUMERIC(18, 2),
    insurance_cost     NUMERIC(18, 2)
);

-- 6. FACT DELIVERY
-- Grain: one procurement/vendor delivery record.
CREATE TABLE IF NOT EXISTS public.fact_delivery (
    delivery_fact_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    vendor_key BIGINT REFERENCES public.dim_vendor(vendor_key),

    source_record_id TEXT,
    purchase_order_number TEXT,
    asn_dn_number TEXT,

    scheduled_date_key INTEGER REFERENCES public.dim_date(date_key),
    delivered_date_key INTEGER REFERENCES public.dim_date(date_key),
    recorded_date_key  INTEGER REFERENCES public.dim_date(date_key),

    delivery_days NUMERIC(10, 2),
    is_delivered  BOOLEAN
);