CREATE TABLE staging.vendor_management (
    id                          INTEGER,
    vendor                        VARCHAR(255),
    manufacturing_site             VARCHAR(255),
    vendor_inco_term                 VARCHAR(20),
    managed_by                        VARCHAR(100),
    fulfill_via                        VARCHAR(100),
    shipment_mode                       VARCHAR(50),
    country                               VARCHAR(100),
    product_group                          VARCHAR(50),
    sub_classification                      VARCHAR(100),
    po_so_number                             VARCHAR(100),
    asn_dn_number                             VARCHAR(100),
    scheduled_delivery_date                    VARCHAR(50),
    delivered_to_client_date                    VARCHAR(50),
    delivery_recorded_date                       VARCHAR(50)
);