-- KPI 1: Monthly revenue/transaction volume by branch and product
SELECT
    b.branch_name,
    p.product_name,
    d.year,
    d.month,
    COUNT(*) AS txn_count,
    ROUND(SUM(f.amount), 2) AS total_amount
FROM fact_transactions f
JOIN dim_branch b  ON f.branch_sk = b.branch_sk
JOIN dim_product p ON f.product_sk = p.product_sk
JOIN dim_date d    ON f.date_id = d.date_id
GROUP BY b.branch_name, p.product_name, d.year, d.month
ORDER BY d.year, d.month, total_amount DESC;
-- KPI 2: Customer churn rate (no transaction in last 90 days vs. warehouse max date)
WITH last_txn AS (
    SELECT
        c.customer_id,
        MAX(d.full_date) AS last_txn_date
    FROM fact_transactions f
    JOIN dim_customer c ON f.customer_sk = c.customer_sk
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE c.is_current = 1
    GROUP BY c.customer_id
),
ref AS (
    SELECT MAX(full_date) AS max_date FROM dim_date d
    JOIN fact_transactions f ON f.date_id = d.date_id
)
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN julianday(ref.max_date) - julianday(lt.last_txn_date) > 90 THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS churn_rate_pct
FROM last_txn lt, ref;
-- KPI 3: Loan default rate by product type and region
SELECT
    p.product_name,
    b.province,
    COUNT(*) AS total_approved_loans,
    SUM(CASE WHEN l.defaulted THEN 1 ELSE 0 END) AS defaults,
    ROUND(100.0 * SUM(CASE WHEN l.defaulted THEN 1 ELSE 0 END) / COUNT(*), 2) AS default_rate_pct
FROM fact_loan_applications l
JOIN dim_product p ON l.product_sk = p.product_sk
JOIN dim_branch b  ON l.branch_sk = b.branch_sk
WHERE l.approved = 1
GROUP BY p.product_name, b.province
ORDER BY default_rate_pct DESC;
-- KPI 4: Fraud flag rate over time (monthly)
SELECT
    d.year,
    d.month,
    COUNT(*) AS total_txns,
    SUM(CASE WHEN f.is_fraud_flag THEN 1 ELSE 0 END) AS flagged_txns,
    ROUND(100.0 * SUM(CASE WHEN f.is_fraud_flag THEN 1 ELSE 0 END) / COUNT(*), 3) AS fraud_rate_pct
FROM fact_transactions f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
-- KPI 5: Average transaction value by customer segment
SELECT
    c.segment,
    COUNT(*) AS txn_count,
    ROUND(AVG(f.amount), 2) AS avg_txn_value
FROM fact_transactions f
JOIN dim_customer c ON f.customer_sk = c.customer_sk
WHERE c.is_current = 1
GROUP BY c.segment
ORDER BY avg_txn_value DESC;

-- KPI 6: New account growth rate, month over month (window function)
WITH monthly_new_accounts AS (
    SELECT
        strftime('%Y', a.open_date) AS yr,
        strftime('%m', a.open_date) AS mo,
        COUNT(*) AS new_accounts
    FROM dim_account a
    GROUP BY yr, mo
)
SELECT
    yr, mo, new_accounts,
    LAG(new_accounts) OVER (ORDER BY yr, mo) AS prev_month_accounts,
    ROUND(
        100.0 * (new_accounts - LAG(new_accounts) OVER (ORDER BY yr, mo))
        / NULLIF(LAG(new_accounts) OVER (ORDER BY yr, mo), 0), 2
    ) AS mom_growth_pct
FROM monthly_new_accounts
ORDER BY yr, mo;
-- KPI 7: Approx customer lifetime value by segment (total txn volume per customer)
SELECT
    c.segment,
    ROUND(AVG(cust_total.total_amount), 2) AS avg_customer_lifetime_value
FROM (
    SELECT c.customer_id, SUM(f.amount) AS total_amount
    FROM fact_transactions f
    JOIN dim_customer c ON f.customer_sk = c.customer_sk
    WHERE c.is_current = 1
    GROUP BY c.customer_id
) cust_total
JOIN dim_customer c ON cust_total.customer_id = c.customer_id
WHERE c.is_current = 1
GROUP BY c.segment
ORDER BY avg_customer_lifetime_value DESC;