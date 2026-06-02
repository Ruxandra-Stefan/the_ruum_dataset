# The Ruum Dataset — Setup Instructions

## Prerequisites

- Python 3.9 or higher
- Git

---

## 1. Clone the repository

```bash
git clone https://github.com/Ruxandra-Stefan/the_ruum_dataset.git
cd the_ruum_dataset
```

---

## 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Activate:

| OS | Command |
|----|---------|
| Windows | `.venv\Scripts\activate` |
| Mac / Linux | `source .venv/bin/activate` |

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
pip install duckdb dbt-duckdb
```

---

## 4. Configure the dbt profile

Create `~/.dbt/profiles.yml` if it does not exist, and add the following block.

- **Windows path:** `C:\Users\<your-username>\.dbt\profiles.yml`
- **Mac/Linux path:** `~/.dbt/profiles.yml`

```yaml
the_ruum:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "/absolute/path/to/the_ruum_dataset/dev.duckdb"
      schema: main
      threads: 4
```

Replace the `path` value with the full absolute path to the cloned folder, for example:

- Windows: `C:/Users/yourname/the_ruum_dataset/dev.duckdb`
- Mac/Linux: `/home/yourname/the_ruum_dataset/dev.duckdb`

---

## 5. (Optional) Regenerate the dataset

The `output/` folder already contains pre-generated CSV files — skip this step unless you want fresh data.

```bash
python generate_data.py
```

---

## 6. Load data and build dbt models

```bash
dbt seed   # loads all CSVs from output/ into dev.duckdb
dbt run    # builds staging views and mart tables
```

Verify everything works:

```bash
dbt test --select staging
```

---

## 7. (Optional) View dbt documentation

```bash
dbt docs generate
dbt docs serve --port 8888
```

Opens at `http://localhost:8888` — lineage DAG, model and column descriptions.

---

## Project structure

```
the_ruum_dataset/
├── input/
│   └── products.csv              # source product catalogue
├── output/                       # CSV files loaded as dbt seeds
│   ├── users.csv
│   ├── locations.csv
│   ├── orders.csv
│   ├── order_items.csv
│   ├── products.csv
│   └── user_events.csv
├── models/
│   ├── staging/                  # views — light cleaning on top of seeds
│   │   ├── _schema.yml           # column descriptions and tests
│   │   ├── stg_users.sql
│   │   ├── stg_locations.sql
│   │   ├── stg_orders.sql
│   │   ├── stg_order_items.sql
│   │   ├── stg_products.sql
│   │   └── stg_user_events.sql
│   └── mart/                     # tables — final analytics-ready models
│       ├── dim_users.sql
│       ├── dim_products.sql
│       ├── fct_orders.sql
│       ├── fct_order_items.sql
│       └── fct_user_events.sql
├── generate_data.py              # generates synthetic dataset
├── create_database.py            # alternative loader (pulls from GitHub)
├── dbt_project.yml
├── requirements.txt
└── schema.dbml                   # entity-relationship diagram
```

---

## Quick reference

```bash
# One-time setup
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
pip install duckdb dbt-duckdb

# Configure ~/.dbt/profiles.yml  (see step 4)

# Build
dbt seed && dbt run

# Test
dbt test --select staging
```
