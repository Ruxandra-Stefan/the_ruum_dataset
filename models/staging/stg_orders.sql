select
    order_id,
    user_id,
    order_date::timestamp as order_date,
    order_status,
    payment_method,
    updated_at::timestamp as updated_at
from {{ ref('orders') }}
