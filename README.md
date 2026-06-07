# the_ruum_dataset

A dbt-core project using DuckDB as the warehouse, with synthetic e-commerce data generated via Faker.

## Stack

- **dbt-core** — transformation layer
- **dbt-duckdb** — local DuckDB adapter
- **DuckDB** — embedded analytical database (`dev.duckdb`)

## Project structure

```
models/
  staging/             # views cleaning raw source tables
  staging_incremental/ # incremental models for orders, order items, user events
  mart/                # dimension and fact tables (materialized as tables)
seeds/
  exchange_rates.csv   # static currency reference data
```

## Setup

```bash
pip install -r requirements.txt
```

Configure `~/.dbt/profiles.yml` with a `the_ruum` profile pointing to `dev.duckdb`:

```yaml
the_ruum:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: dev.duckdb
```

## Running the project

```bash
# Generate raw data
python generate_data.py

# Load seeds and run all models
dbt seed
dbt run

# Run tests
dbt test

# Launch docs
dbt docs generate
dbt docs serve
```

## Testing philosophy

The project has 153 tests across source, staging, incremental, and mart layers. Tests are not
a formality — they are the primary defence against silent data failures that produce no errors
but corrupt compliance logic downstream.

Full testing rationale lives in [`models/staging/docs_testing.md`](models/staging/docs_testing.md)
and is rendered inside `dbt docs serve`. Key areas covered:

- **Source layer** — guards against upstream schema changes, NULL injections, duplicate primary
  keys, and orphaned foreign keys before any transformation runs
- **Model layer** — verifies that SQL logic produced correct output, not just that data arrived
  intact (e.g. the exchange rate JOIN worked, CASE logic covered all branches)
- **Incremental layer** — catches missed rows, duplicate inserts, and schema drift specific to
  incremental materialisation
- **Quebec compliance** — a dedicated set of tests validates three regulatory obligations (see below)

## Quebec compliance

Locations where `is_quebec_compliant_required = true` are subject to three overlapping frameworks:

| Framework | Obligation | Column enforcing it |
|---|---|---|
| Bill 101 (Charter of the French Language) | All commercial communications must be available in French | `marketing_language_requirement = 'EN,FR'` |
| Quebec Consumer Protection Act | Prices must be displayed in CAD with a valid exchange rate | `currency_code = 'CAD'` and `exchange_rate_to_usd > 0` |
| PIPEDA (Privacy) | GDPR-equivalent controls; must know which events belong to QC users | `is_quebec_event = true` on all events from QC users |

Two singular tests enforce this automatically on every `dbt test` run:
`assert_quebec_transparent_pricing.sql` and `assert_quebec_language_requirements.sql`.

## Key dataset insights

Derived from the synthetic dataset (see `output/charts/` for visuals):

| Metric | Value | Relevance |
|---|---|---|
| Gross GMV | $838K | Full exposure if QC pricing compliance is broken |
| Cancelled orders | $208K (24.8%) | Refund processing requires correct user attribution via `is_quebec_event` |
| Single-purchase customers | 1,621 (83% of buyers) | Re-engagement campaigns require `marketing_language_requirement` to select French templates for QC |

A failed compliance test before shipping costs the time to fix a flag. A failed compliance test
discovered during a regulatory audit costs legal fees, remediation, and mandatory customer
notification under PIPEDA.
