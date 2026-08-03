-- ===========================================
-- Mutual Fund Analytics - Star Schema
-- ===========================================

-- =========================
-- Dimension Table: Fund
-- =========================
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    plan TEXT,
    risk_grade TEXT,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER
);

-- =========================
-- Dimension Table: Date
-- =========================
CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE,
    day INTEGER,
    month INTEGER,
    month_name TEXT,
    quarter INTEGER,
    year INTEGER
);

-- =========================
-- Fact Table: NAV
-- =========================
CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date_id INTEGER,
    nav REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- =========================
-- Fact Table: Transactions
-- =========================
CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT,
    amfi_code INTEGER,
    date_id INTEGER,
    transaction_type TEXT,
    amount_inr REAL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- =========================
-- Fact Table: Performance
-- =========================
CREATE TABLE fact_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- =========================
-- Fact Table: AUM
-- =========================
CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    aum_crore REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);