select
    id as product_id,
    name as product_name,
    category,
    description,
    price,
    dimensions,
    material,
    stock
from {{ source('raw_ecommerce', 'products') }}
