-- Language compliance for Quebec (Bill 101 — Charter of the French Language).
-- All Quebec locations must have compliance notes that reference both French language
-- support and Bill 101. Missing or incomplete notes = undocumented compliance gap.
-- Any row returned = a failing location.

select
    location_id,
    country_code,
    state,
    quebec_compliance_notes
from {{ ref('stg_locations') }}
where is_quebec_compliant_required = true
  and (
      quebec_compliance_notes is null
      or lower(quebec_compliance_notes) not like '%french%'
      or lower(quebec_compliance_notes) not like '%bill 101%'
  )
