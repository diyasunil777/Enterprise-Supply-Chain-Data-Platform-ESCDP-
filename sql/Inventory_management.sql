CREATE TABLE staging.inventory_management (
    order_id                     INTEGER,
    order_item_quantity            INTEGER,
    product_price                  NUMERIC(12,2),
    order_item_product_price        NUMERIC(12,2),
    order_item_total                NUMERIC(12,2),
    order_item_discount              NUMERIC(12,2),
    order_item_discount_rate          NUMERIC(6,4)
);