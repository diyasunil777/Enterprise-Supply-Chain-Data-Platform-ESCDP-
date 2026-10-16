-- =====================================================
-- ESCDP: RAW TABLES IN THE PUBLIC SCHEMA
-- All column names match the uploaded CSV files exactly.
-- No separate staging schema is created; everything lives in public.
-- =====================================================


-- 1. DISTRIBUTION CENTER

CREATE TABLE IF NOT EXISTS public."distribution_center_database_2000" (
    "distribution_center_id" TEXT,
    "distribution_center_name" TEXT,
    "warehouse_type" TEXT,
    "region" TEXT,
    "city" TEXT,
    "country" TEXT,
    "manager_id" TEXT,
    "product_id" TEXT,
    "storage_type" TEXT,
    "inventory_units" TEXT,
    "storage_capacity_units" TEXT,
    "occupied_capacity_units" TEXT,
    "utilization_pct" TEXT,
    "inbound_shipments" TEXT,
    "outbound_shipments" TEXT,
    "orders_processed" TEXT,
    "avg_processing_time_hours" TEXT,
    "dock_doors" TEXT,
    "employees" TEXT,
    "operating_shift" TEXT,
    "status" TEXT,
    "record_date" TEXT,
    "on_time_dispatch_pct" TEXT,
    "damaged_units" TEXT,
    "stockout_flag" TEXT,
    "last_inventory_audit_date" TEXT
);


-- 2. ENTERPRISE RESOURCE PLANNING (ERP)

DROP TABLE IF EXISTS public."enterprise_resource_planning_erp_2000_source_erp";
CREATE TABLE public."enterprise_resource_planning_erp_2000_source_erp" (
    "Order Id" TEXT,
    "Customer Id" TEXT,
    "Customer Fname" TEXT,
    "Customer Lname" TEXT,
    "Customer Email" TEXT,
    "Customer Password" TEXT,
    "Customer Segment" TEXT,
    "Customer City" TEXT,
    "Customer Country" TEXT,
    "Customer State" TEXT,
    "Customer Street" TEXT,
    "Customer Zipcode" TEXT,
    "Sales per customer" TEXT,
    "sales" TEXT,
    "Order Item Profit Ratio" TEXT,
    "Order Profit Per Order" TEXT,
    "Benefit per order" TEXT
);


-- 3. INVENTORY MANAGEMENT

CREATE TABLE IF NOT EXISTS public."inventory_management_2000" (
    "Order Id" TEXT,
    "Order Item Quantity" TEXT,
    "Product Price" TEXT,
    "Order Item Product Price" TEXT,
    "Order Item Total" TEXT,
    "Order Item Discount" TEXT,
    "Order Item Discount Rate" TEXT
);


-- 4. LOGISTICS TRACKING

CREATE TABLE IF NOT EXISTS public."logistics_tracking_2000" (
    "late_delivery_risk" TEXT,
    "order_id" TEXT,
    "delivery_status" TEXT
);


-- 5. ORDER FULFILLMENT

CREATE TABLE IF NOT EXISTS public."order_fulfillment_2000" (
    "Order Id" TEXT,
    "Type" TEXT,
    "order date (DateOrders)" TEXT,
    "Order Status" TEXT,
    "Order Customer Id" TEXT,
    "Order City" TEXT,
    "Order Country" TEXT,
    "Order State" TEXT,
    "Order Zipcode" TEXT
);


-- 6. PROCUREMENT
DROP TABLE IF EXISTS public."procurement_2001";
CREATE TABLE public."procurement_2001" (
    "ID" TEXT,
    "Project Code" TEXT,
    "PQ #" TEXT,
    "PO / SO #" TEXT,
    "ASN/DN #" TEXT,
    Country TEXT,
    "Managed By" TEXT,
    "Fulfill Via" TEXT,
    "Vendor INCO Term" TEXT,
    "Shipment Mode" TEXT,
    "PQ First Sent to Client Date" TEXT,
    "PO Sent to Vendor Date" TEXT,
    "Scheduled Delivery Date" TEXT,
    "Delivered to Client Date" TEXT,
    "Delivery Recorded Date" TEXT,
    "Product Group" TEXT,
    "Sub Classification" TEXT,
    "Item Description" TEXT,
    "Molecule/Test Type" TEXT,
    Dosage TEXT,
    "Dosage Form" TEXT,
    "Unit of Measure (Per Pack)" TEXT,
    "Line Item Quantity" TEXT,
    "Line Item Value" TEXT,
    "Pack Price" TEXT,
    "Unit Price" TEXT,
    "First Line Designation" TEXT,
    "Weight (Kilograms)" TEXT,
    "Freight Cost (USD)" TEXT,
    "Line Item Insurance (USD)" TEXT
);

-- 7. SUPPLY CHAIN MANAGEMENT (SCM)

DROP TABLE IF EXISTS public."supply_chain_management_scm_2000";
CREATE TABLE public."supply_chain_management_scm_2000" (
    "Order Id" TEXT,
    Market TEXT,
    "Order Region" TEXT,
    Latitude TEXT,
    Longitude TEXT
);


-- 8. TRANSPORTATION MANAGEMENT (TMS)

CREATE TABLE IF NOT EXISTS public."transportation_management_tms_2000" (
    order_id TEXT,
    shipping_mode TEXT,
    days_for_shipping_real TEXT,
    days_for_shipment_scheduled TEXT,
    shipping_date_dateorders TEXT
);


-- 9. VENDOR MANAGEMENT

DROP TABLE IF EXISTS public."vendor_management_2000";
CREATE TABLE public."vendor_management_2000" (
    ID INTEGER,
    Vendor VARCHAR(100)
);


-- 10. WAREHOUSE MANAGEMENT SYSTEM (WMS)

CREATE TABLE IF NOT EXISTS public."wms_excel_3_sheet1" (
    "Order Id" TEXT,
    "Category Id" TEXT,
    "Category Name" TEXT,
    "Department Id" TEXT,
    "Department Name" TEXT,
    "Order Item Cardprod Id" TEXT,
    "Order Item Id" TEXT,
    "Product Card Id" TEXT,
    "Product Category Id" TEXT,
    "Product Image" TEXT,
    "Product Name" TEXT,
    "Product Status" TEXT
);