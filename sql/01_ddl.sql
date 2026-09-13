CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk     INTEGER PRIMARY KEY,
    customer_id     TEXT NOT NULL,
    name            TEXT,
    dob             DATE,
    segment         TEXT,
    city            TEXT,
    province        TEXT,
    effective_date  DATE,
    expiry_date     DATE,
    is_current      BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_branch (
    branch_sk    INTEGER PRIMARY KEY,
    branch_id    TEXT NOT NULL,
    branch_name  TEXT,
    city         TEXT,
    province     TEXT
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_sk        INTEGER PRIMARY KEY,
    product_id        TEXT NOT NULL,
    product_name      TEXT,
    product_category  TEXT
);

CREATE TABLE IF NOT EXISTS dim_account (
    account_sk    INTEGER PRIMARY KEY,
    account_id    TEXT NOT NULL,
    customer_id   TEXT,
    branch_id     TEXT,
    account_type  TEXT,
    open_date     DATE,
    status        TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id      INTEGER PRIMARY KEY,
    full_date    DATE,
    day          INTEGER,
    month        INTEGER,
    quarter      INTEGER,
    year         INTEGER,
    day_of_week  TEXT,
    is_weekend   BOOLEAN
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id   TEXT PRIMARY KEY,
    account_sk       INTEGER REFERENCES dim_account(account_sk),
    customer_sk      INTEGER REFERENCES dim_customer(customer_sk),
    branch_sk        INTEGER REFERENCES dim_branch(branch_sk),
    product_sk       INTEGER REFERENCES dim_product(product_sk),
    date_id          INTEGER REFERENCES dim_date(date_id),
    amount           REAL,
    transaction_type TEXT,
    channel          TEXT,
    is_fraud_flag    BOOLEAN
);

CREATE TABLE IF NOT EXISTS fact_loan_applications (
    application_id TEXT PRIMARY KEY,
    customer_sk    INTEGER REFERENCES dim_customer(customer_sk),
    branch_sk      INTEGER REFERENCES dim_branch(branch_sk),
    product_sk     INTEGER REFERENCES dim_product(product_sk),
    date_id        INTEGER REFERENCES dim_date(date_id),
    loan_amount    REAL,
    approved       BOOLEAN,
    defaulted      BOOLEAN,
    interest_rate  REAL
);

CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_branch ON fact_transactions(branch_sk);
CREATE INDEX IF NOT EXISTS idx_fact_loan_date ON fact_loan_applications(date_id);