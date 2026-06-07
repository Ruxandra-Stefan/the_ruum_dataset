select
    order_item_id,
    order_id,
    product_id,
    quantity::integer as quantity,
    unit_price::double as unit_price,
    discount::double as discount,
    line_total::double as line_total
from {{ source('raw_ecommerce', 'order_items') }}
