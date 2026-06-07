-- SOURCE LAYER — Financial formula integrity test.
--
-- Why this matters: line_total is pre-computed upstream. If the source system
-- applies a rounding rule, promotion logic, or data entry error that breaks
-- the formula, every revenue figure derived from this dataset is wrong —
-- including GMV, refund calculations, and Quebec transparent-pricing displays.
-- Catching this at the source prevents corrupt data from flowing through all
-- downstream models and charts.
--
-- Risk if ignored: silent revenue misreporting. A $0.01 rounding error at
-- scale (2,092 line items, $838K GMV) compounds into material discrepancies
-- that only surface during financial audits — not in routine dbt runs.
--
-- Tolerance: 1 cent (0.01). Any row returned = a failing record.

select
    order_item_id,
    order_id,
    quantity,
    unit_price,
    discount,
    line_total,
    round(quantity * unit_price * (1.0 - discount), 2) as expected_line_total,
    abs(line_total - round(quantity * unit_price * (1.0 - discount), 2)) as variance
from {{ source('raw_ecommerce', 'order_items') }}
where abs(line_total - round(quantity * unit_price * (1.0 - discount), 2)) > 0.01
