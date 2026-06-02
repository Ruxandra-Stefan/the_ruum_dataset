with order_totals as (
    select
        order_id,
        sum(line_total)  as total_amount,
        sum(quantity)    as total_items,
        count(*)         as num_line_items
    from {{ ref('stg_order_items') }}
    group by order_id
)

select
    o.order_id,
    o.user_id,
    o.order_date,
    o.order_status,
    o.payment_method,
    o.updated_at,
    ot.total_amount,
    ot.total_items,
    ot.num_line_items
from {{ ref('stg_orders') }} o
left join order_totals ot
    on o.order_id = ot.order_id
