-- ============================================================
-- Supply Chain / Order Data Platform
-- PostgreSQL Database Setup
-- Restructured to follow the universal schema pattern
-- (schemas added; table contents/columns left unchanged)
-- ============================================================


-- ============================================================
-- 1. CREATE SCHEMAS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS source_sql;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE SCHEMA IF NOT EXISTS audit;


-- ============================================================
-- 2. STAGING
-- Source: Order Fulfillment
-- ============================================================

DROP TABLE IF EXISTS staging.order_fulfillment;
CREATE TABLE staging.order_fulfillment (
    "Order Id"                 INTEGER,
    "Type"                     VARCHAR(20),
    "order date (DateOrders)"  VARCHAR(50),
    "Order Status"             VARCHAR(50),
    "Order Customer Id"        INTEGER,
    "Order City"               VARCHAR(100),
    "Order Country"            VARCHAR(100),
    "Order State"              VARCHAR(100),
    "Order Zipcode"            VARCHAR(20)
);


-- ============================================================
-- 3. STAGING
-- Source: Warehouse Management (WMS)
-- ============================================================

DROP TABLE IF EXISTS staging.warehouse_management_wms;
CREATE TABLE staging.warehouse_management_wms (
    "Order Id"                 INTEGER,
    "Category Id"              INTEGER,
    "Category Name"            VARCHAR(255),
    "Department Id"            INTEGER,
    "Department Name"          VARCHAR(255),
    "Order Item Cardprod Id"   INTEGER,
    "Order Item Id"            INTEGER,
    "Product Card Id"          INTEGER,
    "Product Category Id"      INTEGER,
    "Product Description"      VARCHAR(1000),
    "Product Image"            VARCHAR(500),
    "Product Name"             VARCHAR(255),
    "Product Status"           INTEGER
);


-- ============================================================
-- 4. STAGING
-- Source: Transportation Management (TMS)
-- ============================================================

DROP TABLE IF EXISTS staging.transportation_management_tms;
CREATE TABLE staging.transportation_management_tms (
    order_id                       INTEGER,
    shipping_mode                  VARCHAR(50),
    days_for_shipping_real         INTEGER,
    days_for_shipment_scheduled    INTEGER,
    shipping_date_dateorders       VARCHAR(50)
);


-- ============================================================
-- 5. STAGING
-- Source: Inventory Management
-- ============================================================

DROP TABLE IF EXISTS staging.inventory_management;
CREATE TABLE staging.inventory_management (
    "Order Id"                     INTEGER,
    "Order Item Quantity"          INTEGER,
    "Product Price"                NUMERIC(12,2),
    "Order Item Product Price"     NUMERIC(12,2),
    "Order Item Total"             NUMERIC(12,2),
    "Order Item Discount"          NUMERIC(12,2),
    "Order Item Discount Rate"     NUMERIC(6,4)
);


-- ============================================================
-- 6. STAGING
-- Source: Enterprise Resource Planning (ERP)
-- ============================================================

DROP TABLE IF EXISTS staging.enterprise_resource_planning_erp;
CREATE TABLE staging.enterprise_resource_planning_erp (
    "Order Id"                     INTEGER,
    "Customer Id"                  INTEGER,
    "Customer Fname"                VARCHAR(100),
    "Customer Lname"                 VARCHAR(100),
    "Customer Email"                  VARCHAR(255),
    "Customer Password"                VARCHAR(255),
    "Customer Segment"                  VARCHAR(50),
    "Customer City"                      VARCHAR(100),
    "Customer Country"                    VARCHAR(100),
    "Customer State"                       VARCHAR(50),
    "Customer Street"                       VARCHAR(255),
    "Customer Zipcode"                       VARCHAR(20),  
    "Sales per customer"                      NUMERIC(12,2),
    "Sales"                                    NUMERIC(12,2),
    "Order Item Profit Ratio"                   NUMERIC(8,4),
    "Order Profit Per Order"                     NUMERIC(12,2),
    "Benefit per order"                           NUMERIC(12,2)
);


-- ============================================================
-- 7. STAGING
-- Source: Procurement
-- ============================================================

DROP TABLE IF EXISTS staging.procurement;
CREATE TABLE staging.procurement (
    "ID"                                INTEGER,
    "Project Code"                       VARCHAR(50),
    "PQ #"                                VARCHAR(100),
    "PO / SO #"                            VARCHAR(100),
    "ASN/DN #"                              VARCHAR(100),
    "Country"                                 VARCHAR(100),
    "Managed By"                               VARCHAR(100),
    "Fulfill Via"                                VARCHAR(100),
    "Vendor INCO Term"                            VARCHAR(20),
    "Shipment Mode"                                VARCHAR(50),
    "PQ First Sent to Client Date"                  VARCHAR(50),
    "PO Sent to Vendor Date"                          VARCHAR(50),
    "Scheduled Delivery Date"                          VARCHAR(50),
    "Delivered to Client Date"                           VARCHAR(50),
    "Delivery Recorded Date"                              VARCHAR(50),
    "Product Group"                                        VARCHAR(50),
    "Sub Classification"                                     VARCHAR(100),
    "Item Description"                                        VARCHAR(1000),
    "Molecule/Test Type"                                        VARCHAR(255),
    "Dosage"                                                     VARCHAR(100),
    "Dosage Form"                                                 VARCHAR(100),
    "Unit of Measure (Per Pack)"                                   INTEGER,
    "Line Item Quantity"                                             INTEGER,
    "Line Item Value"                                                 NUMERIC(14,2),
    "Pack Price"                                                       NUMERIC(12,2),
    "Unit Price"                                                        NUMERIC(12,2),
    "First Line Designation"                                             VARCHAR(10),
    "Weight (Kilograms)"                                                  NUMERIC(12,2),
    "Freight Cost (USD)"                                                   VARCHAR(50),  
    "Line Item Insurance (USD)"                                             NUMERIC(12,2)
);


-- ============================================================
-- 8. STAGING
-- Source: Vendor Management
-- ============================================================

DROP TABLE IF EXISTS staging.vendor_management;
CREATE TABLE staging.vendor_management (
    "ID"                            INTEGER,
    "Vendor"                         VARCHAR(255),
    "Manufacturing Site"              VARCHAR(255),
    "Vendor INCO Term"                 VARCHAR(20),
    "Managed By"                        VARCHAR(100),
    "Fulfill Via"                        VARCHAR(100),
    "Shipment Mode"                       VARCHAR(50),
    "Country"                              VARCHAR(100),
    "Product Group"                         VARCHAR(50),
    "Sub Classification"                     VARCHAR(100),
    "PO / SO #"                               VARCHAR(100),
    "ASN/DN #"                                 VARCHAR(100),
    "Scheduled Delivery Date"                   VARCHAR(50),
    "Delivered to Client Date"                    VARCHAR(50),
    "Delivery Recorded Date"                        VARCHAR(50)
);


-- ============================================================
-- 9. STAGING
-- Source: Supply Chain Management (SCM)
-- ============================================================

DROP TABLE IF EXISTS staging.supply_chain_management_scm;
CREATE TABLE staging.supply_chain_management_scm (
    "Order Id"          INTEGER,
    "Market"            VARCHAR(50),
    "Order Region"      VARCHAR(50),
    "Latitude"          NUMERIC(12,8),
    "Longitude"         NUMERIC(12,8)
);


-- ============================================================
-- 10. STAGING
-- Source: Logistics Tracking
-- ============================================================

DROP TABLE IF EXISTS staging.logistics_tracking;
CREATE TABLE staging.logistics_tracking (
    order_id                   INTEGER,
    delivery_status            VARCHAR(50),
    late_delivery_risk         INTEGER
);


-- ============================================================
-- 11. STAGING
-- Source: Distribution Center Database
-- ============================================================

DROP TABLE IF EXISTS staging.distribution_center_database;
CREATE TABLE staging.distribution_center_database (
    distribution_center_id     VARCHAR(50),
    distribution_center_name   VARCHAR(255),
    warehouse_type              VARCHAR(100),
    region                       VARCHAR(100),
    city                         VARCHAR(100),
    country                      VARCHAR(100),
    manager_id                   VARCHAR(50),
    product_id                   VARCHAR(50),
    storage_type                 VARCHAR(50),
    inventory_units               INTEGER,
    storage_capacity_units        INTEGER,
    occupied_capacity_units       INTEGER,
    utilization_pct               NUMERIC(5,2),
    inbound_shipments             INTEGER,
    outbound_shipments            INTEGER,
    orders_processed               INTEGER,
    avg_processing_time_hours      NUMERIC(5,2),
    dock_doors                     INTEGER,
    employees                       INTEGER,
    operating_shift                 VARCHAR(20),
    status                           VARCHAR(50),
    record_date                      DATE,
    on_time_dispatch_pct             NUMERIC(5,2),
    damaged_units                     INTEGER,
    stockout_flag                      VARCHAR(10),
    last_inventory_audit_date          DATE
);


-- ============================================================
-- 12. AUDIT / ETL LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS audit.etl_log (
    log_id BIGSERIAL PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    source_name TEXT,
    source_format TEXT,
    target_table TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    rows_read INTEGER,
    rows_loaded INTEGER,
    status TEXT,
    error_message TEXT
);


-- ============================================================
-- 13. BASIC STAGING INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_order_fulfillment_order_id
ON staging.order_fulfillment("Order Id");

CREATE INDEX IF NOT EXISTS idx_warehouse_management_wms_order_id
ON staging.warehouse_management_wms("Order Id");

CREATE INDEX IF NOT EXISTS idx_transportation_management_tms_order_id
ON staging.transportation_management_tms(order_id);

CREATE INDEX IF NOT EXISTS idx_inventory_management_order_id
ON staging.inventory_management("Order Id");

CREATE INDEX IF NOT EXISTS idx_erp_order_id
ON staging.enterprise_resource_planning_erp("Order Id");

CREATE INDEX IF NOT EXISTS idx_erp_customer_id
ON staging.enterprise_resource_planning_erp("Customer Id");

CREATE INDEX IF NOT EXISTS idx_procurement_po_so
ON staging.procurement("PO / SO #");

CREATE INDEX IF NOT EXISTS idx_vendor_management_po_so
ON staging.vendor_management("PO / SO #");

CREATE INDEX IF NOT EXISTS idx_scm_order_id
ON staging.supply_chain_management_scm("Order Id");

CREATE INDEX IF NOT EXISTS idx_logistics_tracking_order_id
ON staging.logistics_tracking(order_id);

CREATE INDEX IF NOT EXISTS idx_distribution_center_product_id
ON staging.distribution_center_database(product_id);


-- ============================================================
-- 14. VERIFY SCHEMAS
-- ============================================================

SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN (
    'source_sql',
    'staging',
    'warehouse',
    'audit'
)
ORDER BY schema_name;


-- ============================================================
-- 15. VERIFY ALL PROJECT TABLES
-- ============================================================

SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema IN (
    'source_sql',
    'staging',
    'warehouse',
    'audit'
)
ORDER BY
    table_schema,
    table_name;
