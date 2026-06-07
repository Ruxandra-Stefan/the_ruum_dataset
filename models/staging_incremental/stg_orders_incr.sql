{{
    config(
        materialized='incremental',
        unique_key='order_id',
        on_schema_change='fail',
        tags=['incremental', 'fact']
    )
}}

with orders as (
    select
        order_id,
        user_id,
        order_date,
        order_status,
        payment_method,
        updated_at
    from {{ source('raw_ecommerce', 'orders') }}
),
user_locations as (
    select
        u.user_id,
        l.country_code,
        l.state,
        l.zip_code::varchar as zip_code
    from {{ source('raw_ecommerce', 'users') }} u
    left join {{ source('raw_ecommerce', 'locations') }} l
        on u.location_id = l.location_id
)
select
    o.order_id,
    o.user_id,
    o.order_date,
    o.order_status,
    o.payment_method,
    o.updated_at,
    {{ get_region_type('ul.country_code', 'ul.state', 'ul.zip_code') }} as fulfillment_region_type
from orders o
left join user_locations ul on o.user_id = ul.user_id

{% if is_incremental() %}
    where o.updated_at > (select max(updated_at) from {{ this }})
{% endif %}
