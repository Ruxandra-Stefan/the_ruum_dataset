select
    event_id,
    user_id,
    event_type,
    event_timestamp::timestamp as event_timestamp,
    page_url,
    product_id,
    additional_details
from {{ ref('user_events') }}
