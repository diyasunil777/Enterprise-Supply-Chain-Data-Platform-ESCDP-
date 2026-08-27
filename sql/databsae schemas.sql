
DROP TABLE IF EXISTS order_fulfillment;
CREATE TABLE order_fulfillment (
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



DROP TABLE IF EXISTS warehouse_management_wms;
CREATE TABLE warehouse_management_wms (
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


DROP TABLE IF EXISTS transportation_management_tms;
CREATE TABLE transportation_management_tms (
    order_id                       INTEGER,
    shipping_mode                  VARCHAR(50),
    days_for_shipping_real         INTEGER,
    days_for_shipment_scheduled    INTEGER,
    shipping_date_dateorders       VARCHAR(50)
);


DROP TABLE IF EXISTS inventory_management;
CREATE TABLE inventory_management (
    "Order Id"                     INTEGER,
    "Order Item Quantity"          INTEGER,
    "Product Price"                NUMERIC(12,2),
    "Order Item Product Price"     NUMERIC(12,2),
    "Order Item Total"             NUMERIC(12,2),
    "Order Item Discount"          NUMERIC(12,2),
    "Order Item Discount Rate"     NUMERIC(6,4)
);


DROP TABLE IF EXISTS enterprise_resource_planning_erp;
CREATE TABLE enterprise_resource_planning_erp (
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


DROP TABLE IF EXISTS procurement;
CREATE TABLE procurement (
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



DROP TABLE IF EXISTS vendor_management;
CREATE TABLE vendor_management (
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



DROP TABLE IF EXISTS supply_chain_management_scm;
CREATE TABLE supply_chain_management_scm (
    "Order Id"          INTEGER,
    "Market"            VARCHAR(50),
    "Order Region"      VARCHAR(50),
    "Latitude"          NUMERIC(12,8),
    "Longitude"         NUMERIC(12,8)
);



DROP TABLE IF EXISTS logistics_tracking;
CREATE TABLE logistics_tracking (
    order_id                   INTEGER,
    delivery_status            VARCHAR(50),
    late_delivery_risk         INTEGER
);



DROP TABLE IF EXISTS distribution_center_database;
CREATE TABLE distribution_center_database (
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
