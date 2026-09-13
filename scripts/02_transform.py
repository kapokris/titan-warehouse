import pandas as pd
import numpy as np
from datetime import date

RAW = "data/raw"
STAGE = "data/staging"

dq_log = []

def log_check(name, table, passed, detail):
    dq_log.append({"check_name": name, "table": table, "passed": passed, "detail": detail})
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name} ({table}): {detail}")

print("=== Loading raw data ===")
customers = pd.read_csv(f"{RAW}/customers.csv", parse_dates=["dob", "signup_date", "record_date"])
branches = pd.read_csv(f"{RAW}/branches.csv")
products = pd.read_csv(f"{RAW}/products.csv")
accounts = pd.read_csv(f"{RAW}/accounts.csv", parse_dates=["open_date"])
transactions = pd.read_csv(f"{RAW}/transactions.csv", parse_dates=["txn_date"])
loans = pd.read_csv(f"{RAW}/loan_applications.csv", parse_dates=["app_date"])

raw_counts = {
    "customers": len(customers), "branches": len(branches), "products": len(products),
    "accounts": len(accounts), "transactions": len(transactions), "loans": len(loans),
}

print("\n=== Cleaning customers -> dim_customer (SCD2) ===")

before = len(customers)
customers = customers.drop_duplicates()
log_check("dedup_exact_rows", "customers", True, f"dropped {before - len(customers)} exact duplicate rows")

customers["name"] = customers["name"].str.strip().str.title()

n_missing_city = customers["city"].isna().sum()
customers["city"] = customers["city"].fillna("Unknown")
log_check("null_city_handling", "customers", True, f"{n_missing_city} missing cities set to 'Unknown' (row kept, not dropped)")

customers = customers.sort_values(["customer_id", "record_date"]).reset_index(drop=True)
scd_rows = []
for cust_id, grp in customers.groupby("customer_id"):
    grp = grp.sort_values("record_date").reset_index(drop=True)
    for i, row in grp.iterrows():
        effective_date = row["record_date"]
        expiry_date = grp.loc[i + 1, "record_date"] if i + 1 < len(grp) else pd.NaT
        is_current = pd.isna(expiry_date)
        scd_rows.append({
            "customer_id": row["customer_id"],
            "name": row["name"],
            "dob": row["dob"],
            "segment": row["segment"],
            "city": row["city"],
            "province": row["province"],
            "effective_date": effective_date,
            "expiry_date": expiry_date,
            "is_current": is_current,
        })

dim_customer = pd.DataFrame(scd_rows).reset_index(drop=True)
dim_customer.insert(0, "customer_sk", range(1, len(dim_customer) + 1))

log_check("scd2_build", "dim_customer", True,
          f"built {len(dim_customer)} SCD2 rows for {dim_customer['customer_id'].nunique()} unique customers")

n_current = dim_customer["is_current"].sum()
log_check("scd2_one_current_per_customer", "dim_customer",
          n_current == dim_customer["customer_id"].nunique(),
          f"{n_current} current rows vs {dim_customer['customer_id'].nunique()} unique customers")


dim_branch = branches.drop_duplicates().reset_index(drop=True)
dim_branch.insert(0, "branch_sk", range(1, len(dim_branch) + 1))

dim_product = products.drop_duplicates().reset_index(drop=True)
dim_product.insert(0, "product_sk", range(1, len(dim_product) + 1))
dim_account = accounts.drop_duplicates(subset=["account_id"]).reset_index(drop=True)
dim_account.insert(0, "account_sk", range(1, len(dim_account) + 1))

valid_cust_ids = set(dim_customer["customer_id"])
orphan_accounts = ~dim_account["customer_id"].isin(valid_cust_ids)
log_check("fk_integrity_account_customer", "dim_account",
          orphan_accounts.sum() == 0,
          f"{orphan_accounts.sum()} accounts reference a customer_id not in dim_customer")
all_dates = pd.concat([transactions["txn_date"], loans["app_date"]])
d_min, d_max = all_dates.min(), all_dates.max()
date_range = pd.date_range(d_min, d_max, freq="D")

dim_date = pd.DataFrame({"full_date": date_range})
dim_date["date_id"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
dim_date["day"] = dim_date["full_date"].dt.day
dim_date["month"] = dim_date["full_date"].dt.month
dim_date["quarter"] = dim_date["full_date"].dt.quarter
dim_date["year"] = dim_date["full_date"].dt.year
dim_date["day_of_week"] = dim_date["full_date"].dt.day_name()
dim_date["is_weekend"] = dim_date["full_date"].dt.dayofweek >= 5
dim_date = dim_date[["date_id","full_date","day","month","quarter","year","day_of_week","is_weekend"]]

log_check("dim_date_build", "dim_date", True, f"built {len(dim_date)} calendar day rows from {d_min.date()} to {d_max.date()}")
print("\n=== Cleaning transactions -> fact_transactions ===")

valid_account_ids = set(dim_account["account_id"])
orphan_mask = ~transactions["account_id"].isin(valid_account_ids)
quarantine_txn = transactions[orphan_mask].copy()
clean_txn = transactions[~orphan_mask].copy()

log_check("fk_integrity_txn_account", "fact_transactions", True,
          f"{orphan_mask.sum()} rows ({orphan_mask.mean()*100:.3f}%) had orphan account_id -> routed to quarantine, not dropped")

recon_ok = len(clean_txn) + len(quarantine_txn) == raw_counts["transactions"]
log_check("row_count_reconciliation", "fact_transactions", recon_ok,
          f"raw={raw_counts['transactions']}, clean={len(clean_txn)}, quarantined={len(quarantine_txn)}")
fact_transactions = clean_txn.merge(dim_account[["account_id","account_sk"]], on="account_id", how="left")
fact_transactions = fact_transactions.merge(dim_branch[["branch_id","branch_sk"]], on="branch_id", how="left")
fact_transactions = fact_transactions.merge(dim_product[["product_id","product_sk"]], on="product_id", how="left")
fact_transactions["date_id"] = fact_transactions["txn_date"].dt.strftime("%Y%m%d").astype(int)

acct_to_cust = dim_account[["account_id","customer_id"]]
fact_transactions = fact_transactions.merge(acct_to_cust, on="account_id", how="left")
current_cust = dim_customer[dim_customer["is_current"]][["customer_id","customer_sk"]]
fact_transactions = fact_transactions.merge(current_cust, on="customer_id", how="left")

fact_transactions = fact_transactions[[
    "transaction_id","account_sk","customer_sk","branch_sk","product_sk","date_id",
    "amount","transaction_type","channel","is_fraud_flag"
]]

log_check("fact_transactions_build", "fact_transactions", True,
          f"built {len(fact_transactions)} fact rows with surrogate keys joined in")
print("\n=== Cleaning loan_applications -> fact_loan_applications ===")

valid_cust_ids_set = set(dim_customer["customer_id"])
orphan_loan_cust = ~loans["customer_id"].isin(valid_cust_ids_set)
log_check("fk_integrity_loan_customer", "fact_loan_applications",
          orphan_loan_cust.sum() == 0,
          f"{orphan_loan_cust.sum()} loan applications reference unknown customer_id")

fact_loans = loans.merge(current_cust, on="customer_id", how="left")
fact_loans = fact_loans.merge(dim_branch[["branch_id","branch_sk"]], on="branch_id", how="left")
fact_loans = fact_loans.merge(dim_product[["product_id","product_sk"]], on="product_id", how="left")
fact_loans["date_id"] = fact_loans["app_date"].dt.strftime("%Y%m%d").astype(int)

fact_loans = fact_loans[[
    "application_id","customer_sk","branch_sk","product_sk","date_id",
    "loan_amount","approved","defaulted","interest_rate"
]]

log_check("fact_loans_build", "fact_loan_applications", True,
          f"built {len(fact_loans)} fact rows with surrogate keys joined in")
dim_customer.to_csv(f"{STAGE}/dim_customer.csv", index=False)
dim_branch.to_csv(f"{STAGE}/dim_branch.csv", index=False)
dim_product.to_csv(f"{STAGE}/dim_product.csv", index=False)
dim_account.to_csv(f"{STAGE}/dim_account.csv", index=False)
dim_date.to_csv(f"{STAGE}/dim_date.csv", index=False)
fact_transactions.to_csv(f"{STAGE}/fact_transactions.csv", index=False)
fact_loans.to_csv(f"{STAGE}/fact_loan_applications.csv", index=False)
quarantine_txn.to_csv(f"{STAGE}/quarantine_transactions.csv", index=False)
pd.DataFrame(dq_log).to_csv(f"{STAGE}/data_quality_log.csv", index=False)

print("\n=== Staging tables written ===")
for name, df in [("dim_customer", dim_customer), ("dim_branch", dim_branch),
                  ("dim_product", dim_product), ("dim_account", dim_account),
                  ("dim_date", dim_date), ("fact_transactions", fact_transactions),
                  ("fact_loan_applications", fact_loans)]:
    print(f"  {name:<26} {len(df):>7} rows")
print(f"\n  data_quality_log.csv has {len(dq_log)} checks logged.")