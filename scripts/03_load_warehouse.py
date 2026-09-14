import sqlite3
import pandas as pd

STAGE = "data/staging"
DB_PATH = "data/warehouse/titan.db"
DDL_PATH = "sql/01_ddl.sql"

conn = sqlite3.connect(DB_PATH)

with open(DDL_PATH) as f:
    conn.executescript(f.read())

print(f"Database created/connected at: {DB_PATH}")
print("Schema (tables) created from DDL.")
tables = [
    "dim_customer",
    "dim_branch",
    "dim_product",
    "dim_account",
    "dim_date",
    "fact_transactions",
    "fact_loan_applications",
]

print("=== Loading staging tables into warehouse ===")
for t in tables:
    df = pd.read_csv(f"{STAGE}/{t}.csv")
    df.to_sql(t, conn, if_exists="replace", index=False)
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:<26} {n:>7} rows loaded")

conn.commit()
conn.close()
print(f"\nWarehouse ready at: {DB_PATH}")
