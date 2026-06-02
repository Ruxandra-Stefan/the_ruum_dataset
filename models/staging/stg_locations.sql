select
    location_id,
    country_code,
    country_full_name,
    city,
    address,
    zip_code::varchar as zip_code,
    state
from {{ ref('locations') }}
