select
    product_id,
    product_name,
    category,
    description,
    price,
    dimensions,
    material,
    stock
from {{ ref('stg_products') }}
