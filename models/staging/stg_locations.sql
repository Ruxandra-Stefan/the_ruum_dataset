with raw_locations as (
    select
        location_id,
        country_code,
        country_full_name,
        city,
        address,
        zip_code::varchar as zip_code,
        state,
        case
            when country_code = 'US' then 'USD'
            when country_code = 'CA' then 'CAD'
            else 'UNKNOWN'
        end as currency_code
    from {{ source('raw_ecommerce', 'locations') }}
),
exchange_rates as (
    select
        currency_code,
        exchange_rate_to_usd::double as exchange_rate_to_usd
    from {{ ref('exchange_rates') }}
),
enhanced_locations as (
    select
        l.location_id,
        l.country_code,
        l.country_full_name,
        l.city,
        l.address,
        l.zip_code,
        l.state,
        l.currency_code,
        coalesce(er.exchange_rate_to_usd, 1.0::double) as exchange_rate_to_usd,
        -- Supply Chain Exclusions: Alaska, Hawaii, Puerto Rico
        case
            when l.country_code = 'US' and l.state = 'AK' then true
            when l.country_code = 'US' and l.state = 'HI' then true
            when l.country_code = 'US' and l.zip_code like '009%' then true  -- Puerto Rico
            else false
        end as is_excluded_supply_chain,
        case
            when l.country_code = 'US' and l.state = 'AK' then 'Alaska - Excluded due to supply chain complexity'
            when l.country_code = 'US' and l.state = 'HI' then 'Hawaii - Excluded due to supply chain complexity'
            when l.country_code = 'US' and l.zip_code like '009%' then 'Puerto Rico - Excluded due to supply chain complexity'
            else null
        end as supply_chain_exclusion_reason,
        -- Quebec Compliance Flag and Documentation
        case
            when l.country_code = 'CA' and l.state = 'QC' then true
            else false
        end as is_quebec_compliant_required,
        case
            when l.country_code = 'CA' and l.state = 'QC' then 'Quebec (QC) - Requires adherence to Bill 101 (Language Charter) and PIPEDA privacy regulations. All communications must support French. Ensure GDPR-like privacy controls.'
            else null
        end as quebec_compliance_notes,
        -- Marketing Language Requirement (Bill 101 — Charter of the French Language)
        case
            when l.country_code = 'CA' and l.state = 'QC' then 'EN,FR'
            else 'EN'
        end as marketing_language_requirement
    from raw_locations l
    left join exchange_rates er on l.currency_code = er.currency_code
)
select *
from enhanced_locations
