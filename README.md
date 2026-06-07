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
