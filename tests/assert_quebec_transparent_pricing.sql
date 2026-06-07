-- Transparent pricing compliance for Quebec (Consumer Protection Act, s.224).
-- Quebec locations must show prices in CAD with a valid exchange rate on record.
-- Any row returned = a failing location that would expose the business to a compliance violation.

select
    location_id,
    country_code,
    state,
    currency_code,
    exchange_rate_to_usd
from {{ ref('stg_locations') }}
where is_quebec_compliant_required = true
  and (
      currency_code != 'CAD'
      or exchange_rate_to_usd is null
      or exchange_rate_to_usd <= 0
  )
