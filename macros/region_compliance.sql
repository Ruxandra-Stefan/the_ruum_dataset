-- Macro: get_region_type
-- Purpose: Classify location into region type for compliance/fulfillment
-- Usage: {{ get_region_type('country_code', 'state', 'zip_code') }}

{% macro get_region_type(country_code, state, zip_code) %}
    case
        when {{ country_code }} = 'CA' and {{ state }} = 'QC' then 'QC'
        when {{ country_code }} = 'US' and {{ state }} in ('AK', 'HI') then 'EXCLUDED'
        when {{ country_code }} = 'US' and {{ zip_code }}::varchar like '009%' then 'EXCLUDED'
        when {{ country_code }} in ('US', 'CA') then 'STANDARD'
        else 'STANDARD'
    end
{% endmacro %}

-- Macro: requires_french_support
-- Purpose: Check if region requires French language support
-- Usage: {{ requires_french_support('country_code', 'state') }}

{% macro requires_french_support(country_code, state) %}
    case 
        when {{ country_code }} = 'CA' and {{ state }} = 'QC' then true
        when {{ country_code }} = 'CA' then false  -- English OK for rest of Canada (but French preferred)
        else false
    end
{% endmacro %}

-- Macro: requires_compliance_flag
-- Purpose: Check if location requires special compliance handling
-- Usage: {{ requires_compliance_flag('country_code', 'state') }}

{% macro requires_compliance_flag(country_code, state) %}
    case 
        when {{ country_code }} = 'CA' and {{ state }} = 'QC' then true  -- PIPEDA + Bill 101 + Quebec Privacy Law
        else false
    end
{% endmacro %}

-- Macro: is_fulfillable
-- Purpose: Check if location is eligible for fulfillment
-- Usage: {{ is_fulfillable('country_code', 'state', 'zip_code') }}

{% macro is_fulfillable(country_code, state, zip_code) %}
    ({{ country_code }} != 'US' or ({{ state }} not in ('AK', 'HI') and {{ zip_code }}::varchar not like '009%'))
{% endmacro %}
