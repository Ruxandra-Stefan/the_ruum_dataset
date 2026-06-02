select
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    u.created_at,
    l.location_id,
    l.city,
    l.state,
    l.country_code,
    l.country_full_name,
    l.address,
    l.zip_code
from {{ ref('stg_users') }} u
left join {{ ref('stg_locations') }} l
    on u.location_id = l.location_id
