from pathlib import Path

import pandas as pd
import streamlit as st


# Project root
ROOT = Path(__file__).resolve().parents[2]

RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


st.set_page_config(
    page_title="Financial Ratios",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Financial Ratios")
st.caption("N100 company financial ratio analysis")


@st.cache_data
def load_ratios():
    return pd.read_csv(RATIOS_FILE)


try:
    df = load_ratios()

    # Company selection
    companies = (
        df[["company_id", "company_name"]]
        .drop_duplicates()
        .sort_values("company_name")
    )

    selected_company = st.selectbox(
        "Select a company",
        companies["company_name"].tolist(),
    )

    selected_id = companies.loc[
        companies["company_name"] == selected_company,
        "company_id",
    ].iloc[0]

    company_data = df[df["company_id"] == selected_id].copy()

    st.subheader(selected_company)

    # Latest available record
    latest = company_data.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "ROE",
        f"{latest['company_roe_pct']:.2f}%"
        if pd.notna(latest["company_roe_pct"])
        else "N/A",
    )

    col2.metric(
        "ROCE",
        f"{latest['roce_pct']:.2f}%"
        if pd.notna(latest["roce_pct"])
        else "N/A",
    )

    col3.metric(
        "Debt / Equity",
        f"{latest['debt_to_equity']:.2f}"
        if pd.notna(latest["debt_to_equity"])
        else "N/A",
    )

    col4.metric(
        "Asset Turnover",
        f"{latest['asset_turnover']:.2f}"
        if pd.notna(latest["asset_turnover"])
        else "N/A",
    )

    st.divider()

    st.subheader("Available Financial Ratios")

    display_columns = [
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
    ]

    display_columns = [
        column for column in display_columns
        if column in company_data.columns
    ]

    st.dataframe(
        company_data[display_columns],
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Unable to load financial ratio data: {e}")