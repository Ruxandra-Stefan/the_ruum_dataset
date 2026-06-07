-- SOURCE LAYER — Referential integrity test (order_items → orders).
--
-- Why this matters: dbt's generic relationships test covers this at the
-- model layer, but running it at the source catches upstream breaks before
-- any transformation runs. An order_item with no parent order cannot be
-- attributed to a user, region, or compliance context — including Quebec
-- PIPEDA audits that require knowing which user's data is being processed.
--
-- Risk if ignored: orphan line items inflate GMV but cannot be linked to
-- a user for refund processing, tax reporting, or compliance auditing.
-- In a Quebec PIPEDA audit, unattributable order items mean the business
-- cannot demonstrate lawful data processing for those transactions.
--
-- Any row returned = an orphaned line item with no parent order.

select
    oi.order_item_id,
    oi.order_id
from {{ source('raw_ecommerce', 'order_items') }} oi
where not exists (
    select 1
    from {{ source('raw_ecommerce', 'orders') }} o
    where o.order_id = oi.order_id
)
