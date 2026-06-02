select
    user_id,
    first_name,
    last_name,
    email,
    created_at::timestamp as created_at,
    location_id
from {{ ref('users') }}
