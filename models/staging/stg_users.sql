with raw_users as (
    select
        user_id,
        first_name,
        last_name,
        email,
        created_at::timestamp as created_at,
        location_id,
        row_number() over (partition by email order by created_at) as rn
    from {{ source('raw_ecommerce', 'users') }}
)
select
    user_id,
    first_name,
    last_name,
    email,
    created_at,
    location_id,
    case when rn > 1 then true else false end as is_duplicate_email
from raw_users
