# N100 Financial Intelligence Platform

A financial intelligence platform for analysing 92 Nifty 100 companies using financial ratios, valuation metrics, cash-flow analytics, clustering, screening, peer comparison, and API-based access.

## Project Overview

The N100 Financial Intelligence Platform combines financial data engineering, analytics, NLP-based insights, machine learning, reporting, and API services into a single platform.

The project covers:

- Financial ratio analysis
- Revenue and FCF CAGR analysis
- Cash-flow intelligence
- Valuation analysis
- Company screening
- Sector analysis
- Peer comparison
- KMeans company clustering
- Outlier detection
- Portfolio statistics
- Automated company tearsheets
- FastAPI services
- Streamlit dashboard
- Automated testing

## Dataset Coverage

The platform covers:

- 92 N100 companies
- 11 peer groups
- Historical financial statements
- Financial ratios
- Market-cap and valuation data
- Sector and sub-sector information
- Peer-group classifications
- Cash-flow information

### Source Data

Main source files are stored under:

`data/raw/`

Important datasets include:

- `companies.xlsx`
- `market_cap.xlsx`
- `financial_ratios.xlsx`
- `analysis.xlsx`
- `balancesheet.xlsx`
- `cashflow.xlsx`
- `sectors.xlsx`
- `peer_groups.xlsx`
- `profitandloss.xlsx`
- `stock_prices.xlsx`

## Project Structure

```text
N100 Financial Intelligence Platform/
│
├── dashboard/
│   └── Streamlit dashboard pages
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── database/
│
├── docs/
│   ├── analyst_guide.pdf
│   └── openapi.json
│
├── output/
│   ├── financial_ratios_engineered.csv
│   ├── cagr_analysis.csv
│   ├── cagr_features.csv
│   ├── cluster_labels.csv
│   ├── cluster_profiles.csv
│   ├── outlier_report.csv
│   ├── portfolio_stats.csv
│   ├── screener_output.csv
│   ├── screener_output.xlsx
│   └── reports/
│
├── reports/
│   └── generated analytical reports
│
├── src/
│   ├── analytics/
│   ├── api/
│   ├── nlp/
│   └── reports/
│
├── tests/
│   ├── api/
│   └── kpi/
│
└── n100_financial_intelligence.db