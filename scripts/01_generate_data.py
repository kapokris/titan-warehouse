import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

RAW_DIR = "data/raw"

FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "David",
    "Elizabeth",
    "Sarah",
    "Daniel",
    "Karen",
    "Matthew",
    "Nancy",
    "Anthony",
    "Lisa",
    "Priya",
    "Wei",
    "Fatima",
    "Chen",
    "Amir",
    "Sofia",
    "Liam",
    "Noah",
    "Olivia",
    "Emma",
    "Ava",
]
LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Wilson",
    "Lee",
    "Patel",
    "Kim",
    "Nguyen",
    "Singh",
    "Chan",
    "Khan",
    "Tremblay",
    "Roy",
    "Gagnon",
    "Cote",
]
CITIES = [
    ("Toronto", "ON"),
    ("Mississauga", "ON"),
    ("Ottawa", "ON"),
    ("Hamilton", "ON"),
    ("Vancouver", "BC"),
    ("Surrey", "BC"),
    ("Calgary", "AB"),
    ("Edmonton", "AB"),
    ("Montreal", "QC"),
    ("Quebec City", "QC"),
    ("Winnipeg", "MB"),
    ("Halifax", "NS"),
]
SEGMENTS = ["retail", "premium", "business"]
ACCOUNT_TYPES = ["chequing", "savings", "credit"]
PRODUCTS = [
    ("PRD001", "Everyday Chequing", "deposit"),
    ("PRD002", "High-Interest Savings", "deposit"),
    ("PRD003", "Cashback Credit Card", "card"),
    ("PRD004", "Travel Rewards Credit Card", "card"),
    ("PRD005", "Personal Line of Credit", "loan"),
    ("PRD006", "Auto Loan", "loan"),
    ("PRD007", "Mortgage - Fixed", "loan"),
    ("PRD008", "Mortgage - Variable", "loan"),
]
CHANNELS = ["branch", "atm", "online", "mobile"]
TXN_TYPES = ["deposit", "withdrawal", "transfer", "payment"]

N_BRANCHES = 15
N_CUSTOMERS = 2000
N_ACCOUNTS = 3200
N_TRANSACTIONS = 60000
N_LOAN_APPS = 1500


def rand_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


START = datetime(2023, 1, 1)
END = datetime(2025, 12, 31)

branches = []
for i in range(1, N_BRANCHES + 1):
    city, prov = random.choice(CITIES)
    branches.append(
        {
            "branch_id": f"BR{i:03d}",
            "branch_name": f"{city} Branch {i}",
            "city": city,
            "province": prov,
        }
    )
df_branch = pd.DataFrame(branches)
df_branch.to_csv(f"{RAW_DIR}/branches.csv", index=False)

df_product = pd.DataFrame(
    PRODUCTS, columns=["product_id", "product_name", "product_category"]
)
df_product.to_csv(f"{RAW_DIR}/products.csv", index=False)

customer_rows = []
for i in range(1, N_CUSTOMERS + 1):
    cid = f"CUST{i:05d}"
    fname = random.choice(FIRST_NAMES)
    lname = random.choice(LAST_NAMES)
    city, prov = random.choice(CITIES)
    segment = random.choices(SEGMENTS, weights=[0.7, 0.2, 0.1])[0]
    dob = rand_date(datetime(1950, 1, 1), datetime(2004, 1, 1)).date()
    signup_date = rand_date(START, END).date()

    name_variant = (
        f"{fname} {lname}"
        if random.random() > 0.1
        else f"{fname.upper()} {lname.lower()}"
    )

    row = {
        "customer_id": cid,
        "name": name_variant,
        "dob": dob,
        "segment": segment,
        "city": city if random.random() > 0.03 else None,
        "province": prov,
        "signup_date": signup_date,
        "record_date": signup_date,
    }
    customer_rows.append(row)

    if random.random() < 0.15:
        change_date = signup_date + timedelta(days=random.randint(60, 500))
        if change_date < END.date():
            new_city, new_prov = random.choice(CITIES)
            new_segment = random.choices(SEGMENTS, weights=[0.5, 0.35, 0.15])[0]
            customer_rows.append(
                {
                    "customer_id": cid,
                    "name": name_variant,
                    "dob": dob,
                    "segment": new_segment,
                    "city": new_city,
                    "province": new_prov,
                    "signup_date": signup_date,
                    "record_date": change_date,
                }
            )

df_customers = pd.DataFrame(customer_rows)

dupes = df_customers.sample(frac=0.01, random_state=1)
df_customers = pd.concat([df_customers, dupes], ignore_index=True)
df_customers.to_csv(f"{RAW_DIR}/customers.csv", index=False)
customer_ids = df_customers["customer_id"].unique().tolist()
account_rows = []
for i in range(1, N_ACCOUNTS + 1):
    aid = f"ACC{i:06d}"
    cust = random.choice(customer_ids)
    branch = random.choice(df_branch["branch_id"].tolist())
    atype = random.choice(ACCOUNT_TYPES)
    open_date = rand_date(START, END).date()
    account_rows.append(
        {
            "account_id": aid,
            "customer_id": cust,
            "branch_id": branch,
            "account_type": atype,
            "open_date": open_date,
            "status": random.choices(
                ["active", "closed", "dormant"], weights=[0.85, 0.1, 0.05]
            )[0],
        }
    )
df_accounts = pd.DataFrame(account_rows)
df_accounts.to_csv(f"{RAW_DIR}/accounts.csv", index=False)
account_ids = df_accounts["account_id"].tolist()
txn_rows = []
for i in range(1, N_TRANSACTIONS + 1):
    tid = f"TXN{i:08d}"
    acc = random.choice(account_ids)
    if random.random() < 0.002:
        acc = f"ACC{random.randint(900000,999999)}"
    prod = random.choice(df_product["product_id"].tolist())
    branch = random.choice(df_branch["branch_id"].tolist())
    txn_date = rand_date(START, END)
    amount = round(np.random.exponential(scale=180) * random.choice([1, 1, 1, -1]), 2)
    txn_rows.append(
        {
            "transaction_id": tid,
            "account_id": acc,
            "branch_id": branch,
            "product_id": prod,
            "txn_date": txn_date.date(),
            "amount": amount,
            "transaction_type": random.choice(TXN_TYPES),
            "channel": random.choice(CHANNELS),
            "is_fraud_flag": random.random() < 0.004,
        }
    )
df_txn = pd.DataFrame(txn_rows)
df_txn.to_csv(f"{RAW_DIR}/transactions.csv", index=False)
loan_products = df_product[df_product["product_category"] == "loan"][
    "product_id"
].tolist()
loan_rows = []
for i in range(1, N_LOAN_APPS + 1):
    lid = f"LOAN{i:06d}"
    cust = random.choice(customer_ids)
    branch = random.choice(df_branch["branch_id"].tolist())
    prod = random.choice(loan_products)
    app_date = rand_date(START, END)
    approved = random.random() < 0.72
    defaulted = approved and (random.random() < 0.06)
    loan_rows.append(
        {
            "application_id": lid,
            "customer_id": cust,
            "branch_id": branch,
            "product_id": prod,
            "app_date": app_date.date(),
            "loan_amount": round(np.random.uniform(2000, 450000), 2),
            "approved": approved,
            "defaulted": defaulted,
            "interest_rate": round(np.random.uniform(3.5, 12.5), 2),
        }
    )
df_loans = pd.DataFrame(loan_rows)
df_loans.to_csv(f"{RAW_DIR}/loan_applications.csv", index=False)

print("Raw data generated successfully.")
print(f"  branches.csv           {len(df_branch):>7} rows")
print(f"  products.csv            {len(df_product):>6} rows")
print(f"  customers.csv           {len(df_customers):>6} rows")
print(f"  accounts.csv            {len(df_accounts):>6} rows")
print(f"  transactions.csv       {len(df_txn):>7} rows")
print(f"  loan_applications.csv   {len(df_loans):>6} rows")
