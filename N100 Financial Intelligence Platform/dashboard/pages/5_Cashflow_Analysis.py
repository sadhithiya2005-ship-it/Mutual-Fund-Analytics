from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
CASHFLOW_FILE = ROOT / "output" / "capital_allocation.csv"


st.set_page_config(
    page_title="Cash Flow Analysis",
    page_icon="💵",
    layout="wide",
)

st.title("💵 Cash Flow & Capital Allocation")
st.caption("N100 company cash-flow analysis")


@st.cache_data
def load_data():
    return pd.read_csv(CASHFLOW_FILE)


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

    col1, col2, col3, col4 = st.columns(4)

    fcf = latest.get("free_cash_flow_cr")
    cfo = latest.get("cash_from_operations_cr")
    fcf_conversion = latest.get("fcf_conversion_pct")
    capex_cfo = latest.get("capex_to_cfo_pct")

    col1.metric(
        "Free Cash Flow",
        f"₹{fcf:,.2f} Cr" if pd.notna(fcf) else "N/A",
    )

    col2.metric(
        "Cash From Operations",
        f"₹{cfo:,.2f} Cr" if pd.notna(cfo) else "N/A",
    )

    col3.metric(
        "FCF Conversion",
        f"{fcf_conversion:.2f}%"
        if pd.notna(fcf_conversion)
        else "N/A",
    )

    col4.metric(
        "CapEx / CFO",
        f"{capex_cfo:.2f}%"
        if pd.notna(capex_cfo)
        else "N/A",
    )

    st.divider()

    st.subheader("Capital Allocation Pattern")

    pattern = latest.get("capital_allocation_pattern")

    if pd.notna(pattern):
        st.info(f"Latest pattern: {pattern}")
    else:
        st.warning("Capital allocation pattern unavailable.")

    st.subheader("Cash Flow History")

    display_columns = [
        "year",
        "free_cash_flow_cr",
        "cash_from_operations_cr",
        "capex_cr",
        "fcf_conversion_pct",
        "capex_to_cfo_pct",
        "capital_allocation_pattern",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in company_data.columns
    ]

    st.dataframe(
        company_data[display_columns],
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Unable to load cash-flow data: {e}")