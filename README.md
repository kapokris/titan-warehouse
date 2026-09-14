# Titan Warehouse

An end-to-end retail & banking analytics data warehouse — built from raw synthetic data through ETL, a star-schema warehouse, SQL analytics, a BI dashboard, containerization, CI/CD, orchestration, and a cloud data platform.

Built as a portfolio project targeting Data Engineering / Data Analytics internships at Canadian banks (RBC, CIBC, BMO, Scotiabank).

---

## What this project demonstrates

- Realistic, deliberately messy synthetic data generation
- ETL with **Slowly Changing Dimension (SCD Type 2)** logic, referential integrity checks, and a quarantine-not-drop data quality pattern
- A proper **star schema** (fact/dimension tables) loaded into a real SQL warehouse
- Advanced SQL: joins, CTEs, window functions (`LAG`), subqueries
- A **Power BI** executive dashboard with KPI cards, DAX measures, and an interactive slicer
- **Docker** containerization of the full pipeline
- **GitHub Actions** CI pipeline that re-runs the pipeline on every push
- **Apache Airflow** DAG orchestrating the pipeline as a scheduled, retry-capable workflow
- A cloud lift to **AWS S3** (data lake) and **Snowflake** (cloud data warehouse), with all 7 KPIs re-verified against the cloud copy

---

## Architecture
                 ┌─────────────────────┐
                 │   01_generate_data   │   synthetic messy data
                 │        .py           │   (customers, accounts,
                 └──────────┬───────────┘    transactions, loans...)
                            │
                            ▼
                 ┌─────────────────────┐
                 │   02_transform.py    │   clean · dedupe · SCD2
                 │   (ETL + data        │   quarantine bad FKs
                 │    quality checks)    │   11-check DQ log
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  03_load_warehouse    │   star schema warehouse
                 │        .py           │   (SQLite locally)
                 └──────────┬───────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
      SQL KPI queries   Power BI      Cloud lift:
      (joins, CTEs,     Dashboard     S3 → Snowflake
       window fns)      (4 KPI cards, (same 7 KPIs
                         3 charts,      re-verified)
                         slicer)
Orchestration: Airflow DAG runs all 3 scripts, in order, with retries
Packaging: Dockerfile containerizes the whole pipeline
CI: GitHub Actions re-runs the pipeline on every push to main


### Star schema
            dim_customer (SCD Type 2)
                   │
dim_branch ───── fact_transactions ───── dim_product
│
dim_date

dim_branch ───── fact_loan_applications ───── dim_product
│ │
dim_customer dim_date

dim_account (bridges customers to transactions via account_id)


**Grain:**
- `fact_transactions`: one row = one transaction event
- `fact_loan_applications`: one row = one loan application

---

## Tech stack

| Layer | Tools |
|---|---|
| Data generation & ETL | Python, pandas, numpy |
| Local warehouse | SQLite |
| Cloud warehouse | Snowflake |
| Cloud storage | AWS S3 |
| BI / Dashboard | Power BI, DAX |
| Orchestration | Apache Airflow |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| SQL | Joins, CTEs, window functions, subqueries |

---

## Data quality & governance

This project treats data quality as a first-class concern, not an afterthought:

- **Deduplication** — exact-duplicate customer rows (simulating source-system re-sends) are detected and dropped, with counts logged
- **SCD Type 2** — `dim_customer` tracks history: every change to a customer's segment or city creates a new row with `effective_date` / `expiry_date` / `is_current`, rather than overwriting history
- **Quarantine, not drop** — ~0.2% of transactions reference an account that doesn't exist (simulating late-arriving/bad data). These rows are routed to `quarantine_transactions.csv` for investigation, never silently discarded
- **Row-count reconciliation** — every filtering step is checked: `clean rows + quarantined rows == raw row count`, proving no data was lost or duplicated
- **Referential integrity checks** — every foreign key relationship (accounts→customers, transactions→accounts, loans→customers) is explicitly verified
- **Audit trail** — every check above is logged to `data_quality_log.csv` with a pass/fail result and a human-readable detail message

---

## Repository structure
titan-warehouse/
├── docs/
│ └── 01_design.md KPI definitions + star schema design doc
├── scripts/
│ ├── 01_generate_data.py generates realistic, messy raw data
│ ├── 02_transform.py ETL: clean, SCD2, quarantine, DQ log
│ └── 03_load_warehouse.py loads staging tables into SQLite
├── sql/
│ ├── 01_ddl.sql warehouse schema (CREATE TABLE statements)
│ └── 02_kpi_queries.sql 7 executive KPI queries
├── data/
│ ├── raw/ generated messy source data
│ ├── staging/ cleaned star-schema tables + DQ log
│ └── warehouse/ titan.db (SQLite warehouse)
├── dashboards/
│ └── titan_dashboard.pbix Power BI dashboard
├── airflow/
│ └── dags/
│ └── titan_pipeline.py Airflow DAG (generate → transform → load)
├── .github/workflows/
│ └── pipeline.yml GitHub Actions CI pipeline
├── Dockerfile
├── requirements.txt
└── README.md


---

## The 7 KPIs

1. Monthly revenue / transaction volume by branch and product
2. Customer churn rate (no transaction in 90+ days)
3. Loan default rate by product type and region
4. Fraud flag rate over time (monthly)
5. Average transaction value by customer segment
6. New account growth rate, month over month (window function)
7. Approximate customer lifetime value by segment

All 7 are implemented in `sql/02_kpi_queries.sql`, tested against the local SQLite warehouse, and re-verified with identical results against the Snowflake cloud warehouse.

---

## How to run it locally

```bash
# clone and set up
git clone https://github.com/kapokris/titan-warehouse.git
cd titan-warehouse
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# run the pipeline
python3 scripts/01_generate_data.py
python3 scripts/02_transform.py
python3 scripts/03_load_warehouse.py
```

## How to run it with Docker

```bash
docker build -t titan-warehouse .
docker run -v $(pwd)/data:/app/data titan-warehouse
```

## How to run it with Airflow

```bash
export AIRFLOW_HOME=~/path/to/titan-warehouse/airflow
airflow standalone
# open http://localhost:8080, trigger the `titan_warehouse_pipeline` DAG
```

---

## Dashboard

The Power BI dashboard (`dashboards/titan_dashboard.pbix`) includes:
- 4 KPI cards: Total Revenue, Total Transactions, Fraud Rate %, Default Rate %
- Revenue by Branch (bar chart)
- Fraud Incidents by Month (line chart)
- Loan Defaults by Product (bar chart)
- A Year slicer filtering the whole page

---

## What I'd build next

- Real-time streaming ingestion (Kafka/Kinesis) instead of batch file generation
- dbt for transformation instead of raw pandas, for better testing/lineage tooling
- Scheduled (not manually-triggered) Airflow runs with alerting on task failure
- Row-level security in Snowflake for customer PII fields

---

## Author

Krishna — Honours Bachelor of Computer Science, Data Analytics Concentration, Sheridan College. Built as a portfolio project for Canadian banking data engineering/analytics internships.
