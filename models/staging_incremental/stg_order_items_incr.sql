{{
    config(
        materialized='incremental',
        unique_key='order_item_id',
        on_schema_change='fail',
        tags=['incremental', 'fact']
    )
}}

select
    order_item_id,
    order_id,
    product_id,
    quantity::integer as quantity,
    unit_price::double as unit_price,
    discount::double as discount,
    line_total::double as line_total,
    current_timestamp as loaded_at
from {{ source('raw_ecommerce', 'order_items') }}

{% if is_incremental() %}
    where not exists (
        select 1 from {{ this }} t
        where t.order_item_id = order_items.order_item_id
    )
{% endif %}
