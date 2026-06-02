select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.line_total,
    o.user_id,
    o.order_date,
    o.order_status,
    o.payment_method,
    p.product_name,
    p.category
from {{ ref('stg_order_items') }} oi
left join {{ ref('stg_orders') }} o
    on oi.order_id = o.order_id
left join {{ ref('stg_products') }} p
    on oi.product_id = p.product_id
