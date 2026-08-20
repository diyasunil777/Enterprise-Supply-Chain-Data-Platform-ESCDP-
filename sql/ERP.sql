CREATE TABLE staging.enterprise_resource_planning_erp (
    order_id                    INTEGER,
    customer_id                   INTEGER,
    customer_fname                 VARCHAR(100),
    customer_lname                  VARCHAR(100),
    customer_email                   VARCHAR(255),
    customer_password                 VARCHAR(255),
    customer_segment                   VARCHAR(50),
    customer_city                      VARCHAR(100),
    customer_country                    VARCHAR(100),
    customer_state                       VARCHAR(50),
    customer_street                       VARCHAR(255),
    customer_zipcode                       VARCHAR(20),
    sales_per_customer                     NUMERIC(12,2),
    sales                                    NUMERIC(12,2),
    order_item_profit_ratio                   NUMERIC(8,4),
    order_profit_per_order                     NUMERIC(12,2),
    benefit_per_order                            NUMERIC(12,2)
);