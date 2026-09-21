# N100 Financial Intelligence Platform — KPI Mapping

## Source Files

| Source | Records | Purpose |
|---|---:|---|
| companies.xlsx | 92 companies | Company master data and ROCE/ROE |
| market_cap.xlsx | 552 records | Market valuation KPIs |
| financial_ratios.xlsx | 1,184 records | Historical financial KPIs |

## Available KPIs

### From financial_ratios.xlsx
- Net Profit Margin (NPM)
- Operating Profit Margin (OPM)
- Return on Equity (ROE)
- Debt to Equity (D/E)
- Interest Coverage Ratio (ICR)
- Asset Turnover
- Free Cash Flow (FCF)
- CapEx
- Earnings Per Share (EPS)
- Book Value Per Share
- Dividend Payout Ratio
- Total Debt
- Cash from Operations (CFO)

### From companies.xlsx
- ROCE
- ROE
- Book Value
- Face Value

### From market_cap.xlsx
- Market Capitalization
- Enterprise Value
- P/E Ratio
- P/B Ratio
- EV/EBITDA
- Dividend Yield

## KPIs Requiring Additional Financial Statement Data

The current source files do not directly provide the underlying values required to calculate:

- Revenue
- Operating Profit
- Profit After Tax (PAT)
- Total Assets
- Total Equity
- Current Assets
- Current Liabilities
- Revenue CAGR
- PAT CAGR
- EPS CAGR
- CFO / Revenue
- CapEx / Revenue

These KPIs must not be fabricated. They require an additional source dataset or documented calculation source.

## Data Quality Notes

- companies.xlsx contains 92 companies.
- financial_ratios.xlsx contains 1,184 records.
- financial_ratios.xlsx contains 119 duplicate company-year observations.
- These observations must not be deleted without understanding their source structure.
- Missing values must be handled according to documented business rules.