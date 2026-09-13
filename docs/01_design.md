# Titan Warehouse — Design Doc

## 1. Business Questions / KPIs
These are the questions the warehouse must be able to answer for an "executive dashboard":

1. Monthly revenue/transaction volume by branch and product
2. Customer churn rate (customers with no transaction in last 90 days)
3. Loan default rate by product type and region
4. Fraud flag rate (% of transactions flagged) over time
5. Average transaction value by customer segment
6. New account growth rate by branch, month over month
7. Customer lifetime value (approx) by segment

## 2. Star Schema

### Fact Tables
**fact_transactions** (grain: one row per transaction)
- transaction_id (PK)
- account_id (FK -> dim_account)
- customer_id (FK -> dim_customer)
- branch_id (FK -> dim_branch)
- product_id (FK -> dim_product)
- date_id (FK -> dim_date)
- amount
- transaction_type (deposit, withdrawal, transfer, payment)
- is_fraud_flag
- channel (branch, atm, online, mobile)

**fact_loan_applications** (grain: one row per loan application)
- application_id (PK)
- customer_id (FK -> dim_customer)
- branch_id (FK -> dim_branch)
- product_id (FK -> dim_product)
- date_id (FK -> dim_date)
- loan_amount
- approved (bool)
- defaulted (bool)
- interest_rate

### Dimension Tables
**dim_customer** (SCD Type 2 — tracks history of changes)
- customer_sk (surrogate PK)
- customer_id (natural/business key)
- name, dob, segment (retail/premium/business), city, province
- effective_date, expiry_date, is_current

**dim_account**
- account_sk (PK), account_id, account_type (chequing/savings/credit), open_date, status

**dim_branch**
- branch_sk (PK), branch_id, branch_name, city, province

**dim_product**
- product_sk (PK), product_id, product_name, product_category (loan/card/deposit)

**dim_date**
- date_id (PK, YYYYMMDD int), full_date, day, month, quarter, year, day_of_week, is_weekend

## 3. Grain & Reconciliation Rules
- fact_transactions: 1 row = 1 transaction event. No aggregation at load time.
- Row-count reconciliation: raw source row count must match staging row count post-cleaning within an expected delta.
- Referential integrity: every FK in fact tables must resolve to a valid dimension row (orphans get routed to a quarantine table, not silently dropped).
- dim_customer SCD2: any change to segment/city creates a new row, closes the old row's expiry_date.

## 4. Tech choices for this build (v1, local-first)
- Data generation: Python (random, numpy)
- Transform: Pandas
- Warehouse (local dev): SQLite (upgrade to PostgreSQL/Snowflake later)
- Orchestration: Airflow (added once pipeline steps are stable)
- BI: Power BI