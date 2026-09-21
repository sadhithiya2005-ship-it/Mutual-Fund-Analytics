from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


st.set_page_config(
    page_title="Risk Analysis",
    page_icon="⚠️",
    layout="wide",
)

st.title("⚠️ Risk Analysis")
st.caption("Leverage and interest-coverage analysis for N100 companies")


@st.cache_data
def load_data():
    df = pd.read_csv(RATIOS_FILE)

    # Keep latest available record for each company
    df = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    return df


try:
    df = load_data()

    total_companies = len(df)

    debt_free_count = int(
        df["debt_free_flag"].fillna(False).sum()
    )

    high_leverage_count = int(
        df["high_leverage_flag"].fillna(False).sum()
    )

    icr_warning_count = int(
        df["interest_coverage_warning"].fillna(False).sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Companies Analysed",
        total_companies,
    )

    col2.metric(
        "Debt-Free",
        debt_free_count,
    )

    col3.metric(
        "High Leverage",
        high_leverage_count,
    )

    col4.metric(
        "ICR Warning",
        icr_warning_count,
    )

    st.divider()

    st.subheader("Risk Indicators")

    display_columns = [
        "company_name",
        "debt_to_equity",
        "interest_coverage",
        "debt_free_flag",
        "high_leverage_flag",
        "interest_coverage_warning",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in df.columns
    ]

    risk_table = df[display_columns].copy()

    st.dataframe(
        risk_table.sort_values(
            "debt_to_equity",
            ascending=False,
        ),
        use_container_width=True,
    )

    st.divider()

    st.subheader("Select Company")

    selected_company = st.selectbox(
        "Company",
        sorted(df["company_name"].dropna().unique()),
    )

    selected = df[
        df["company_name"] == selected_company
    ].iloc[0]

    st.write(
        f"**Debt / Equity:** "
        f"{selected['debt_to_equity']:.2f}"
        if pd.notna(selected["debt_to_equity"])
        else "**Debt / Equity:** N/A"
    )

    st.write(
        f"**Interest Coverage:** "
        f"{selected['interest_coverage']:.2f}"
        if pd.notna(selected["interest_coverage"])
        else "**Interest Coverage:** N/A"
    )

    if bool(selected["debt_free_flag"]):
        st.success("Debt-Free Flag: Yes")
    else:
        st.info("Debt-Free Flag: No")

    if bool(selected["high_leverage_flag"]):
        st.warning("High Leverage Flag: Yes")
    else:
        st.success("High Leverage Flag: No")

    if bool(selected["interest_coverage_warning"]):
        st.warning("Interest Coverage Warning: Yes")
    else:
        st.success("Interest Coverage Warning: No")

except Exception as e:
    st.error(f"Unable to load risk data: {e}")