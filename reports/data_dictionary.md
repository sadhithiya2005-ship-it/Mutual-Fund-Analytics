# Mutual Fund Analytics - Data Dictionary

## Dataset 1: nav_history

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| amfi_code | INTEGER | Unique AMFI code for each mutual fund scheme | nav_history.csv |
| date | DATE | NAV recorded date | nav_history.csv |
| nav | REAL | Net Asset Value of the scheme | nav_history.csv |

---

## Dataset 2: investor_transactions

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| investor_id | TEXT | Unique investor ID | investor_transactions.csv |
| transaction_date | DATE | Date of transaction | investor_transactions.csv |
| amfi_code | INTEGER | Mutual fund scheme code | investor_transactions.csv |
| transaction_type | TEXT | SIP / Lumpsum / Redemption | investor_transactions.csv |
| amount_inr | REAL | Transaction amount in INR | investor_transactions.csv |
| state | TEXT | Investor state | investor_transactions.csv |
| city | TEXT | Investor city | investor_transactions.csv |
| city_tier | TEXT | T30 / B30 city classification | investor_transactions.csv |
| age_group | TEXT | Investor age category | investor_transactions.csv |
| gender | TEXT | Male / Female | investor_transactions.csv |
| annual_income_lakh | REAL | Annual income in lakhs | investor_transactions.csv |
| payment_mode | TEXT | UPI / Net Banking / Cheque / Card | investor_transactions.csv |
| kyc_status | TEXT | Verified / Pending | investor_transactions.csv |

---

## Dataset 3: scheme_performance

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| amfi_code | INTEGER | Mutual fund scheme code | scheme_performance.csv |
| scheme_name | TEXT | Name of the mutual fund scheme | scheme_performance.csv |
| fund_house | TEXT | AMC/Fund house | scheme_performance.csv |
| category | TEXT | Fund category | scheme_performance.csv |
| plan | TEXT | Direct / Regular | scheme_performance.csv |
| return_1yr_pct | REAL | 1-Year return (%) | scheme_performance.csv |
| return_3yr_pct | REAL | 3-Year return (%) | scheme_performance.csv |
| return_5yr_pct | REAL | 5-Year return (%) | scheme_performance.csv |
| benchmark_3yr_pct | REAL | 3-Year benchmark return (%) | scheme_performance.csv |
| alpha | REAL | Alpha performance metric | scheme_performance.csv |
| beta | REAL | Beta risk metric | scheme_performance.csv |
| sharpe_ratio | REAL | Sharpe Ratio | scheme_performance.csv |
| sortino_ratio | REAL | Sortino Ratio | scheme_performance.csv |
| std_dev_ann_pct | REAL | Annualized standard deviation | scheme_performance.csv |
| max_drawdown_pct | REAL | Maximum drawdown (%) | scheme_performance.csv |
| aum_crore | INTEGER | Assets Under Management (₹ Crore) | scheme_performance.csv |
| expense_ratio_pct | REAL | Expense ratio (%) | scheme_performance.csv |
| morningstar_rating | INTEGER | Morningstar rating (1–5) | scheme_performance.csv |
| risk_grade | TEXT | Risk category | scheme_performance.csv |