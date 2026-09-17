-- ============================================================
-- UC18 - ENTERPRISE SUPPLY CHAIN DATA PLATFORM
-- SPRINT 2 - STAR SCHEMA
-- PostgreSQL DATA WAREHOUSE
-- ============================================================


-- ============================================================
-- 1. CREATE WAREHOUSE SCHEMA
-- ============================================================

CREATE SCHEMA IF NOT EXISTS warehouse;


-- ============================================================
-- 2. DROP EXISTING STAR SCHEMA TABLES
-- ============================================================

DROP TABLE IF EXISTS warehouse.fact_warehouse CASCADE;
DROP TABLE IF EXISTS warehouse.fact_shipment CASCADE;
DROP TABLE IF EXISTS warehouse.fact_procurement CASCADE;
DROP TABLE IF EXISTS warehouse.fact_order CASCADE;

DROP TABLE IF EXISTS warehouse.dim_order_status CASCADE;
DROP TABLE IF EXISTS warehouse.dim_distribution_center CASCADE;
DROP TABLE IF EXISTS warehouse.dim_shipping CASCADE;
DROP TABLE IF EXISTS warehouse.dim_location CASCADE;
DROP TABLE IF EXISTS warehouse.dim_supplier CASCADE;
DROP TABLE IF EXISTS warehouse.dim_product CASCADE;
DROP TABLE IF EXISTS warehouse.dim_customer CASCADE;
DROP TABLE IF EXISTS warehouse.dim_date CASCADE;


-- ============================================================
-- 3. DATE DIMENSION
-- ============================================================

CREATE TABLE warehouse.dim_date (

    date_key                INTEGER PRIMARY KEY,

    full_date               DATE,

    day                     INTEGER,

    month                   INTEGER,

    month_name              VARCHAR(20),

    quarter                 INTEGER,

    year                    INTEGER,

    week_of_year            INTEGER,

    day_of_week             INTEGER,

    day_name                VARCHAR(20)

);


-- ============================================================
-- 4. CUSTOMER DIMENSION
-- Source:
-- ERP + Order Fulfillment
-- ============================================================

CREATE TABLE warehouse.dim_customer (

    customer_key            SERIAL PRIMARY KEY,

    customer_id             INTEGER UNIQUE,

    customer_fname          VARCHAR(100),

    customer_lname          VARCHAR(100),

    customer_email          VARCHAR(255),

    customer_segment        VARCHAR(50),

    customer_city           VARCHAR(100),

    customer_state          VARCHAR(50),

    customer_country        VARCHAR(100),

    customer_street         VARCHAR(255),

    customer_zipcode        VARCHAR(20)

);


-- ============================================================
-- 5. PRODUCT DIMENSION
-- Source:
-- Warehouse Management System + Procurement
-- ============================================================

CREATE TABLE warehouse.dim_product (

    product_key             SERIAL PRIMARY KEY,

    product_id              INTEGER UNIQUE,

    product_name            VARCHAR(255),

    product_description     VARCHAR(1000),

    product_category_id     INTEGER,

    product_category_name   VARCHAR(255),

    department_id           INTEGER,

    department_name         VARCHAR(255),

    product_status          INTEGER,

    product_group           VARCHAR(50),

    sub_classification      VARCHAR(100),

    molecule_test_type      VARCHAR(255),

    dosage                   VARCHAR(100),

    dosage_form              VARCHAR(100)

);


-- ============================================================
-- 6. SUPPLIER DIMENSION
-- Source:
-- Vendor Management
-- ============================================================

CREATE TABLE warehouse.dim_supplier (

    supplier_key            SERIAL PRIMARY KEY,

    supplier_id             INTEGER UNIQUE,

    vendor_name             VARCHAR(255),

    manufacturing_site      VARCHAR(255),

    vendor_inco_term        VARCHAR(20),

    managed_by              VARCHAR(100),

    fulfill_via              VARCHAR(100),

    country                 VARCHAR(100)

);


-- ============================================================
-- 7. LOCATION DIMENSION
-- Source:
-- Supply Chain Management
-- ============================================================

CREATE TABLE warehouse.dim_location (

    location_key            SERIAL PRIMARY KEY,

    market                  VARCHAR(50),

    order_region            VARCHAR(50),

    latitude                NUMERIC(12,8),

    longitude               NUMERIC(12,8),

    UNIQUE (
        market,
        order_region,
        latitude,
        longitude
    )

);


-- ============================================================
-- 8. SHIPPING DIMENSION
-- Source:
-- TMS + Procurement + Vendor Management
-- ============================================================

CREATE TABLE warehouse.dim_shipping (

    shipping_key            SERIAL PRIMARY KEY,

    shipping_mode           VARCHAR(50),

    vendor_inco_term        VARCHAR(20),

    fulfill_via              VARCHAR(100)

);


-- ============================================================
-- 9. DISTRIBUTION CENTER DIMENSION
-- Source:
-- Distribution Center Database
-- ============================================================

CREATE TABLE warehouse.dim_distribution_center (

    distribution_center_key    SERIAL PRIMARY KEY,

    distribution_center_id     VARCHAR(50) UNIQUE,

    distribution_center_name   VARCHAR(255),

    warehouse_type             VARCHAR(100),

    region                     VARCHAR(100),

    city                       VARCHAR(100),

    country                    VARCHAR(100),

    manager_id                 VARCHAR(50),

    storage_type               VARCHAR(50),

    dock_doors                 INTEGER,

    employees                  INTEGER,

    operating_shift            VARCHAR(20),

    status                     VARCHAR(50)

);


-- ============================================================
-- 10. ORDER STATUS DIMENSION
-- Source:
-- Order Fulfillment + Logistics Tracking
-- ============================================================

CREATE TABLE warehouse.dim_order_status (

    status_key              SERIAL PRIMARY KEY,

    order_status            VARCHAR(50),

    delivery_status         VARCHAR(50),

    late_delivery_risk     INTEGER

);


-- ============================================================
-- 11. FACT ORDER
--
-- Grain:
-- One row = one order
--
-- Source:
-- Order Fulfillment + ERP + Inventory Management
-- ============================================================

CREATE TABLE warehouse.fact_order (

    order_fact_key              SERIAL PRIMARY KEY,

    order_id                    INTEGER,

    customer_key                INTEGER,

    product_key                 INTEGER,

    location_key                INTEGER,

    status_key                  INTEGER,

    order_date_key              INTEGER,

    order_status                VARCHAR(50),

    order_type                  VARCHAR(20),

    order_city                  VARCHAR(100),

    order_country               VARCHAR(100),

    order_state                 VARCHAR(100),

    order_zipcode               VARCHAR(20),

    order_item_quantity         INTEGER,

    product_price               NUMERIC(12,2),

    order_item_product_price    NUMERIC(12,2),

    order_item_total            NUMERIC(12,2),

    order_item_discount         NUMERIC(12,2),

    order_item_discount_rate    NUMERIC(6,4),

    sales_per_customer          NUMERIC(12,2),

    sales                       NUMERIC(12,2),

    order_item_profit_ratio     NUMERIC(8,4),

    order_profit_per_order      NUMERIC(12,2),

    benefit_per_order           NUMERIC(12,2),


    FOREIGN KEY (customer_key)
        REFERENCES warehouse.dim_customer(customer_key),

    FOREIGN KEY (product_key)
        REFERENCES warehouse.dim_product(product_key),

    FOREIGN KEY (location_key)
        REFERENCES warehouse.dim_location(location_key),

    FOREIGN KEY (status_key)
        REFERENCES warehouse.dim_order_status(status_key),

    FOREIGN KEY (order_date_key)
        REFERENCES warehouse.dim_date(date_key)

);


-- ============================================================
-- 12. FACT PROCUREMENT
--
-- Grain:
-- One row = one procurement line item
--
-- Source:
-- Procurement
-- ============================================================

CREATE TABLE warehouse.fact_procurement (

    procurement_fact_key        SERIAL PRIMARY KEY,

    procurement_id              INTEGER,

    product_key                 INTEGER,

    supplier_key                INTEGER,

    location_key                INTEGER,

    shipping_key                INTEGER,

    pq_number                   VARCHAR(100),

    po_so_number                VARCHAR(100),

    asn_dn_number               VARCHAR(100),

    pq_first_sent_date_key      INTEGER,

    po_sent_date_key            INTEGER,

    scheduled_delivery_date_key INTEGER,

    delivered_date_key          INTEGER,

    delivery_recorded_date_key  INTEGER,

    line_item_quantity          INTEGER,

    unit_of_measure_per_pack    INTEGER,

    line_item_value             NUMERIC(14,2),

    pack_price                  NUMERIC(12,2),

    unit_price                  NUMERIC(12,2),

    weight_kg                   NUMERIC(12,2),

    freight_cost_usd            NUMERIC(12,2),

    line_item_insurance_usd     NUMERIC(12,2),

    first_line_designation      VARCHAR(10),


    FOREIGN KEY (product_key)
        REFERENCES warehouse.dim_product(product_key),

    FOREIGN KEY (supplier_key)
        REFERENCES warehouse.dim_supplier(supplier_key),

    FOREIGN KEY (location_key)
        REFERENCES warehouse.dim_location(location_key),

    FOREIGN KEY (shipping_key)
        REFERENCES warehouse.dim_shipping(shipping_key),

    FOREIGN KEY (pq_first_sent_date_key)
        REFERENCES warehouse.dim_date(date_key),

    FOREIGN KEY (po_sent_date_key)
        REFERENCES warehouse.dim_date(date_key),

    FOREIGN KEY (scheduled_delivery_date_key)
        REFERENCES warehouse.dim_date(date_key),

    FOREIGN KEY (delivered_date_key)
        REFERENCES warehouse.dim_date(date_key),

    FOREIGN KEY (delivery_recorded_date_key)
        REFERENCES warehouse.dim_date(date_key)

);


-- ============================================================
-- 13. FACT SHIPMENT
--
-- Grain:
-- One row = one order/shipment
--
-- Source:
-- TMS + Logistics Tracking
-- ============================================================

CREATE TABLE warehouse.fact_shipment (

    shipment_fact_key            SERIAL PRIMARY KEY,

    order_id                     INTEGER,

    shipping_key                 INTEGER,

    location_key                 INTEGER,

    status_key                   INTEGER,

    shipping_date_key            INTEGER,

    days_for_shipping_real       INTEGER,

    days_for_shipment_scheduled  INTEGER,

    shipping_delay_days          INTEGER,

    late_delivery_risk           INTEGER,


    FOREIGN KEY (shipping_key)
        REFERENCES warehouse.dim_shipping(shipping_key),

    FOREIGN KEY (location_key)
        REFERENCES warehouse.dim_location(location_key),

    FOREIGN KEY (status_key)
        REFERENCES warehouse.dim_order_status(status_key),

    FOREIGN KEY (shipping_date_key)
        REFERENCES warehouse.dim_date(date_key)

);


-- ============================================================
-- 14. FACT WAREHOUSE
--
-- Grain:
-- One row = one product at one distribution center
-- on one record date
--
-- Source:
-- Distribution Center Database
-- ============================================================

CREATE TABLE warehouse.fact_warehouse (

    warehouse_fact_key            SERIAL PRIMARY KEY,

    distribution_center_key       INTEGER,

    product_id                    VARCHAR(50),

    record_date_key               INTEGER,

    last_inventory_audit_date_key INTEGER,

    inventory_units               INTEGER,

    storage_capacity_units        INTEGER,

    occupied_capacity_units       INTEGER,

    utilization_pct               NUMERIC(5,2),

    inbound_shipments             INTEGER,

    outbound_shipments            INTEGER,

    orders_processed              INTEGER,

    avg_processing_time_hours     NUMERIC(5,2),

    on_time_dispatch_pct          NUMERIC(5,2),

    damaged_units                 INTEGER,

    stockout_flag                 VARCHAR(10),


    FOREIGN KEY (distribution_center_key)
        REFERENCES warehouse.dim_distribution_center(
            distribution_center_key
        ),

    FOREIGN KEY (record_date_key)
        REFERENCES warehouse.dim_date(date_key),

    FOREIGN KEY (last_inventory_audit_date_key)
        REFERENCES warehouse.dim_date(date_key)

);