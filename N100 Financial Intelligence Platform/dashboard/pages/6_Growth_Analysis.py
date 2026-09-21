from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
CAGR_FILE = ROOT / "output" / "cagr_analysis.csv"


st.set_page_config(
    page_title="Growth Analysis",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Growth Analysis")
st.caption("Historical EPS CAGR analysis for N100 companies")


@st.cache_data
def load_data():
    return pd.read_csv(CAGR_FILE)


try:
    df = load_data()

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

    company_data = df[
        df["company_id"] == selected_id
    ].copy()

    latest = company_data.iloc[-1]

    st.subheader(selected_company)

    col1, col2, col3 = st.columns(3)

    eps_3yr = latest.get("eps_cagr_3yr_pct")
    eps_5yr = latest.get("eps_cagr_5yr_pct")
    eps_10yr = latest.get("eps_cagr_10yr_pct")

    col1.metric(
        "3-Year EPS CAGR",
        f"{eps_3yr:.2f}%"
        if pd.notna(eps_3yr)
        else "N/A",
    )

    col2.metric(
        "5-Year EPS CAGR",
        f"{eps_5yr:.2f}%"
        if pd.notna(eps_5yr)
        else "N/A",
    )

    col3.metric(
        "10-Year EPS CAGR",
        f"{eps_10yr:.2f}%"
        if pd.notna(eps_10yr)
        else "N/A",
    )

    st.divider()

    st.subheader("EPS CAGR Comparison")

    growth_columns = [
        "company_name",
        "eps_cagr_3yr_pct",
        "eps_cagr_5yr_pct",
        "eps_cagr_10yr_pct",
    ]

    growth_columns = [
        column
        for column in growth_columns
        if column in df.columns
    ]

    comparison = df[growth_columns].drop_duplicates()

    st.dataframe(
        comparison.sort_values(
            "eps_cagr_3yr_pct",
            ascending=False,
        ),
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Unable to load growth data: {e}")