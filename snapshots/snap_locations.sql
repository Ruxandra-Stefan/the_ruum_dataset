{% snapshot snap_locations %}
    {{
        config(
            target_schema='snapshots',
            unique_key='location_id',
            strategy='timestamp',
            updated_at='snapshot_timestamp',
        )
    }}

    with locations as (
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
    )
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
        case
            when l.country_code = 'US' and l.state in ('AK', 'HI') then true
            when l.country_code = 'US' and l.zip_code like '009%' then true
            else false
        end as is_excluded_supply_chain,
        case
            when l.country_code = 'CA' and l.state = 'QC' then true
            else false
        end as is_quebec_compliant_required,
        now() as snapshot_timestamp
    from locations l
    left join exchange_rates er on l.currency_code = er.currency_code

{% endsnapshot %}
