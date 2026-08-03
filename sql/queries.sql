-- ===========================================
-- Mutual Fund Analytics - Analytical Queries
-- ===========================================

-- 1. Top 5 funds by AUM
SELECT scheme_name, aum_crore
FROM scheme_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- 2. Average NAV by Fund
SELECT amfi_code, AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY amfi_code;

-- 3. Total SIP Amount
SELECT SUM(amount_inr) AS total_sip
FROM fact_transactions
WHERE transaction_type = 'SIP';

-- 4. Transactions by State
SELECT state, COUNT(*) AS total_transactions
FROM fact_transactions
GROUP BY state
ORDER BY total_transactions DESC;

-- 5. Funds with Expense Ratio less than 1%
SELECT scheme_name, expense_ratio_pct
FROM scheme_performance
WHERE expense_ratio_pct < 1;

-- 6. Average Return (3 Years)
SELECT AVG(return_3yr_pct) AS avg_return_3yr
FROM scheme_performance;

-- 7. Number of Investors by Gender
SELECT gender, COUNT(*) AS total_investors
FROM fact_transactions
GROUP BY gender;

-- 8. Total Investment by Transaction Type
SELECT transaction_type,
       SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY transaction_type;

-- 9. Highest Rated Funds
SELECT scheme_name,
       morningstar_rating
FROM scheme_performance
ORDER BY morningstar_rating DESC;

-- 10. Investors by KYC Status
SELECT kyc_status,
       COUNT(*) AS total
FROM fact_transactions
GROUP BY kyc_status;