from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


st.set_page_config(
    page_title="Company Screener",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Company Screener")
st.caption("Filter N100 companies using available financial metrics")


@st.cache_data
def load_data():
    df = pd.read_csv(RATIOS_FILE)

    # Keep one record per company using the latest available row
    df = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    return df


try:
    df = load_data()

    st.subheader("Screening Filters")

    col1, col2 = st.columns(2)

    with col1:
        min_roe = st.slider(
            "Minimum ROE (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
        )

        max_de = st.slider(
            "Maximum Debt / Equity",
            min_value=0.0,
            max_value=10.0,
            value=10.0,
            step=0.1,
        )

    with col2:
        min_roce = st.slider(
            "Minimum ROCE (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
        )

        max_pe = st.slider(
            "Maximum P/E",
            min_value=0.0,
            max_value=200.0,
            value=200.0,
            step=5.0,
        )

    # Apply filters
    screened = df.copy()

    screened = screened[
        (screened["company_roe_pct"].fillna(0) >= min_roe)
        & (screened["roce_pct"].fillna(0) >= min_roce)
        & (screened["debt_to_equity"].fillna(999) <= max_de)
        & (screened["pe_ratio"].fillna(999) <= max_pe)
    ]

    st.divider()

    st.subheader(f"Matching Companies: {len(screened)}")

    display_columns = [
        "company_name",
        "company_roe_pct",
        "roce_pct",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "market_cap_crore",
        "dividend_yield_pct",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in screened.columns
    ]

    result = screened[display_columns].sort_values(
        "company_roe_pct",
        ascending=False,
    )

    st.dataframe(
        result,
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Unable to load screening data: {e}")