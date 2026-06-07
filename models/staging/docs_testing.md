{% docs testing_philosophy %}
## Why We Test

Tests in this project are not a formality — they are the primary defence against
silent data failures that do not throw errors, do not break pipelines, and are
only discovered weeks later during a financial audit, a regulatory review, or a
customer complaint.

This project operates across US and Canadian markets. Quebec, as a French-language
civil-law jurisdiction, sits under three overlapping regulatory frameworks that
impose **specific, auditable data obligations**:

| Framework | Obligation | Data consequence |
|---|---|---|
| Bill 101 (Charter of the French Language) | All commercial communications must be available in French | `marketing_language_requirement = 'EN,FR'` must be set for every QC location |
| Quebec Consumer Protection Act | Prices must be displayed in the local currency with full transparency | `currency_code = 'CAD'` and a valid `exchange_rate_to_usd > 0` for every QC location |
| PIPEDA (Privacy) | GDPR-equivalent controls; must know which events are tied to QC users | `is_quebec_event = true` must propagate to every event from a QC user |

A failed test means one of these obligations **may not be met** for a subset of
users. The consequence is not a broken dashboard — it is a regulatory violation,
a potential fine, and reputational damage.

**Tests are the automated proof that compliance logic ran correctly.**
{% enddocs %}


{% docs testing_source_layer %}
## Source Layer Tests — What They Guard

Source tests run against the raw data before any transformation. Their job is to
catch upstream breaks: ingestion errors, schema changes from the source system,
or data quality issues that would silently corrupt every model downstream.

### Generic tests (in `_schema.yml` under `sources:`)

| Test | Columns covered | What it catches |
|---|---|---|
| `not_null` | All key identifiers and required fields | Missing rows, partial loads, NULL injections |
| `unique` | Primary keys on all 6 tables | Duplicate records that cause fan-out in joins |
| `relationships` | All foreign keys | Orphaned records that break referential integrity |
| `accepted_values` | `order_status`, `payment_method`, `event_type`, `country_code`, `category` | New upstream values that our CASE logic has no branch for |

### Singular tests (in `tests/`)

| Test file | Layer | What it catches |
|---|---|---|
| `assert_source_line_total_integrity.sql` | Source | `line_total ≠ quantity × unit_price × (1 - discount)` — revenue formula broken at origin |
| `assert_source_no_negative_financials.sql` | Source | Impossible financial values (negative price, discount ≥ 1) — compliance and revenue risk |
| `assert_source_no_orphan_order_items.sql` | Source | Line items with no parent order — breaks PIPEDA attribution chain |

### Why source tests matter for Quebec

If `country_code` or `state` arrives corrupted from the source (e.g., a new
province code we haven't seen before), the `accepted_values` test fails
immediately. Without it, the CASE logic in `stg_locations` falls through to the
`else` branch, `is_quebec_compliant_required` is silently set to `false`, and
Quebec users lose all their compliance protections — with no error anywhere in
the pipeline.
{% enddocs %}


{% docs testing_model_layer %}
## Model Layer Tests — What They Guard

Model tests run after transformations. Their job is to verify that our SQL logic
produced the correct output — not just that the data arrived intact.

### Generic tests (in `_schema.yml` under `models:`)

| Test | What it catches |
|---|---|
| `not_null` on derived flags | Window functions and CASE statements that produced NULL unexpectedly |
| `unique` on primary keys | Fan-out from a JOIN that turned one row into many |
| `relationships` across staging models | Cross-model FK integrity after our rename/cast transformations |
| `accepted_values` on `currency_code ['USD', 'CAD']` | CASE logic gap — an unknown `country_code` producing 'UNKNOWN' instead of a valid currency |
| `accepted_values` on `marketing_language_requirement ['EN', 'EN,FR']` | Bill 101 flag logic failure — a QC location missing bilingual flag |
| `accepted_values` on `order_status` (5 values incl. `pending_refund`) | Status normalisation gap across staging and incremental layers |

### Singular tests (in `tests/`)

| Test file | Layer | What it catches |
|---|---|---|
| `assert_quebec_transparent_pricing.sql` | Model (`stg_locations`) | QC location without `currency_code = 'CAD'` or with `exchange_rate_to_usd ≤ 0` |
| `assert_quebec_language_requirements.sql` | Model (`stg_locations`) | QC location without French-language documentation in `quebec_compliance_notes` |

### Why model tests catch what source tests cannot

Source tests prove the raw data arrived correctly. Model tests prove our logic
transformed it correctly. Example: `exchange_rate_to_usd` does not exist in the
source — it is derived by joining the `exchange_rates` seed. A source test cannot
check it. The `not_null` model test on that column is the only automated check
that the JOIN worked and the seed has a row for every currency we serve.
{% enddocs %}


{% docs testing_quebec_compliance %}
## Quebec Compliance — The Cost of Ignoring These Tests

### What is at stake

Quebec operates under a stricter regulatory environment than the rest of Canada
or the United States. Three frameworks create specific data obligations:

**1. Bill 101 — Charter of the French Language**
All commercial communications to Quebec consumers must be available in French.
This includes product names, invoices, marketing emails, push notifications, and
any customer-facing copy generated from our data.

- The column that enforces this: `stg_locations.marketing_language_requirement`
- Must be `'EN,FR'` for every row where `state = 'QC'`
- Test that validates it: `accepted_values: ['EN', 'EN,FR']` on `stg_locations`

**2. Quebec Consumer Protection Act — Transparent Pricing**
Prices must be displayed in the consumer's local currency. For Quebec, that means
CAD. Using USD pricing without conversion, or displaying a stale/invalid exchange
rate, is a consumer protection violation.

- Columns that enforce this: `currency_code = 'CAD'` and `exchange_rate_to_usd > 0`
- Test that validates it: `assert_quebec_transparent_pricing.sql`

**3. PIPEDA — Privacy**
Quebec's privacy law requires the business to know exactly which data belongs to
Quebec users, to honour data subject requests, and to apply appropriate consent
controls. If `is_quebec_event` is wrong, the business cannot produce a compliant
data subject access report.

- Column that enforces this: `is_quebec_event` on `stg_user_events`
- Test: `not_null` on `stg_user_events.is_quebec_event`

### The financial argument

From the project's own data (see `output/charts/`):

| Metric | Value | Why it matters for compliance |
|---|---|---|
| Gross GMV | $838K | Full exposure if pricing is non-compliant for QC share |
| Cancelled orders | $208K (24.8%) | Refund processing requires correct user attribution — broken by missing `is_quebec_event` |
| Single-purchase customers | 1,621 (83% of buyers) | Re-engagement campaigns require `marketing_language_requirement` to select French templates |

A CRTC or OPC (Office of the Privacy Commissioner) investigation triggered by a
consumer complaint carries potential fines and mandatory remediation. The cost of
fixing a broken compliance flag before shipping is the time to run `dbt test`.
The cost after is legal fees, remediation, and customer notification obligations.

### What "ignoring a failed test" actually means

If `assert_quebec_transparent_pricing` fails and is suppressed:
- Quebec users may see USD prices
- A consumer complains to the OPC
- The business must demonstrate it had controls in place
- A suppressed test is evidence that it did not

These tests are the documented proof that compliance logic ran.
{% enddocs %}


{% docs testing_incremental_layer %}
## Incremental Model Tests — Special Considerations

Incremental models introduce risks that batch models do not have. Tests on the
incremental layer guard against these specific failure modes.

### Why incremental models need their own tests

| Risk | How it manifests | Test that catches it |
|---|---|---|
| Missed rows | Boundary condition in `updated_at > max(updated_at)` skips simultaneous updates | `unique` + `not_null` on PK after incremental run |
| Duplicate rows | `NOT IN` NULL-unsafe logic inserts already-present rows | `unique` on `order_item_id` in `stg_order_items_incr` |
| Schema drift | `on_schema_change: fail` stops the run if upstream adds a column | Controlled by dbt config, not a test |
| Compliance gap | `fulfillment_region_type = 'STANDARD'` hardcoded, hiding QC orders | `accepted_values: ['QC', 'EXCLUDED', 'STANDARD']` + the macro producing real values |
| Status gap | `pending_refund` missing from accepted_values | `accepted_values` on `stg_orders_incr.order_status` (5 values) |

### The `loaded_at` vs business timestamp distinction

`stg_order_items_incr.loaded_at` records **when the row entered the incremental
table**, not when the order item was created. Do not use this column for
business-time analysis. Use `stg_orders.order_date` joined on `order_id` instead.
This column exists only for infrastructure diagnostics.
{% enddocs %}
