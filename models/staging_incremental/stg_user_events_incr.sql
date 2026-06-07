{{
    config(
        materialized='incremental',
        unique_key='event_id',
        on_schema_change='fail',
        tags=['incremental', 'fact', 'high-volume']
    )
}}

with user_locations as (
    select 
        su.user_id,
        ul.is_quebec_compliant_required
    from {{ ref('stg_users') }} su
    left join {{ ref('stg_locations') }} ul
        on su.location_id = ul.location_id
)
select
    ue.event_id,
    ue.user_id,
    ue.event_type,
    ue.event_timestamp,
    ue.page_url,
    ue.product_id,
    ue.additional_details,
    coalesce(ul.is_quebec_compliant_required, false) as is_quebec_event
from {{ source('raw_ecommerce', 'user_events') }} ue
left join user_locations ul
    on ue.user_id = ul.user_id

{% if is_incremental() %}
    where ue.event_timestamp > (select max(event_timestamp) from {{ this }})
{% endif %}
