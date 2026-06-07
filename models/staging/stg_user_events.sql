with raw_events as (
    select
        event_id,
        user_id,
        event_type,
        event_timestamp::timestamp as event_timestamp,
        page_url,
        product_id,
        additional_details
    from {{ source('raw_ecommerce', 'user_events') }}
),
user_locations as (
    select
        su.user_id,
        sl.is_quebec_compliant_required
    from {{ ref('stg_users') }} su
    left join {{ ref('stg_locations') }} sl
        on su.location_id = sl.location_id
)
select
    e.event_id,
    e.user_id,
    e.event_type,
    e.event_timestamp,
    e.page_url,
    e.product_id,
    e.additional_details,
    coalesce(ul.is_quebec_compliant_required, false) as is_quebec_event
from raw_events e
left join user_locations ul on e.user_id = ul.user_id
