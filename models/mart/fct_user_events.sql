select
    e.event_id,
    e.user_id,
    e.event_type,
    e.event_timestamp,
    e.page_url,
    e.product_id,
    p.product_name,
    p.category,
    e.additional_details
from {{ ref('stg_user_events') }} e
left join {{ ref('stg_products') }} p
    on e.product_id = p.product_id
