-- SOURCE LAYER — Financial bounds test.
--
-- Why this matters: negative quantities, zero prices, discounts outside
-- 0–1, or negative totals indicate corrupt ingestion or upstream bugs.
-- These values pass all not_null tests but produce nonsensical revenue
-- figures. For Quebec transparent-pricing compliance, a negative displayed
-- price or an impossible discount would constitute a consumer protection
-- violation under the Quebec Consumer Protection Act.
--
-- Risk if ignored: compliance exposure in Quebec (incorrect pricing display),
-- incorrect CAD/USD conversion results, and downstream aggregations that
-- undercount or negate revenue. The $208K cancellation figure from the
-- analytics layer would be understated if cancelled items carry negative totals.
--
-- Any row returned = a failing record.

select
    order_item_id,
    order_id,
    quantity,
    unit_price,
    discount,
    line_total
from {{ source('raw_ecommerce', 'order_items') }}
where quantity    <= 0
   or unit_price  <= 0
   or discount    <  0
   or discount    >= 1
   or line_total  <  0
