select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    discount,
    line_total
from {{ ref('order_items') }}
