from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
VALUATION_FILE = ROOT / "output" / "valuation_analysis.csv"


st.set_page_config(
    page_title="Valuation",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Valuation Analysis")
st.caption("N100 valuation metrics and relative valuation bands")


@st.cache_data
def load_data():
    return pd.read_csv(VALUATION_FILE)


try:
    df = load_data()

    companies = (
        df[["company_id", "company_name"]]
        .drop_duplicates()
        .sort_values("company_name")
    )

    selected_company = st.selectbox(
        "Select Company",
        companies["company_name"].tolist(),
    )

    selected_id = companies.loc[
        companies["company_name"] == selected_company,
        "company_id",
    ].iloc[0]

    company = df[df["company_id"] == selected_id].iloc[0]

    st.subheader(selected_company)

    col1, col2, col3 = st.columns(3)

    pe = company["pe_ratio"]
    pb = company["pb_ratio"]
    ev_ebitda = company["ev_ebitda"]

    col1.metric(
        "P/E Ratio",
        f"{pe:.2f}" if pd.notna(pe) else "N/A",
    )

    col2.metric(
        "P/B Ratio",
        f"{pb:.2f}" if pd.notna(pb) else "N/A",
    )

    col3.metric(
        "EV / EBITDA",
        f"{ev_ebitda:.2f}" if pd.notna(ev_ebitda) else "N/A",
    )

    col1, col2, col3 = st.columns(3)

    market_cap = company["market_cap_crore"]
    enterprise_value = company["enterprise_value_crore"]
    dividend_yield = company["dividend_yield_pct"]

    col1.metric(
        "Market Cap",
        f"₹{market_cap:,.2f} Cr"
        if pd.notna(market_cap)
        else "N/A",
    )

    col2.metric(
        "Enterprise Value",
        f"₹{enterprise_value:,.2f} Cr"
        if pd.notna(enterprise_value)
        else "N/A",
    )

    col3.metric(
        "Dividend Yield",
        f"{dividend_yield:.2f}%"
        if pd.notna(dividend_yield)
        else "N/A",
    )

    st.divider()

    st.subheader("Relative Valuation Bands")

    band_col1, band_col2, band_col3 = st.columns(3)

    band_col1.info(
        f"P/E: {company['pe_relative_band']}"
    )

    band_col2.info(
        f"P/B: {company['pb_relative_band']}"
    )

    band_col3.info(
        f"EV/EBITDA: {company['ev_ebitda_relative_band']}"
    )

    st.divider()

    st.subheader("Company Financial Context")

    context = pd.DataFrame(
        {
            "Metric": [
                "ROE",
                "ROCE",
                "P/E Percentile",
                "P/B Percentile",
                "EV/EBITDA Percentile",
            ],
            "Value": [
                f"{company['company_roe_pct']:.2f}%"
                if pd.notna(company["company_roe_pct"])
                else "N/A",
                f"{company['roce_pct']:.2f}%"
                if pd.notna(company["roce_pct"])
                else "N/A",
                f"{company['pe_percentile']:.2f}"
                if pd.notna(company["pe_percentile"])
                else "N/A",
                f"{company['pb_percentile']:.2f}"
                if pd.notna(company["pb_percentile"])
                else "N/A",
                f"{company['ev_ebitda_percentile']:.2f}"
                if pd.notna(company["ev_ebitda_percentile"])
                else "N/A",
            ],
        }
    )

    st.dataframe(
        context,
        use_container_width=True,
        hide_index=True,
    )

except Exception as e:
    st.error(f"Unable to load valuation analysis: {e}")