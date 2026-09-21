from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


st.set_page_config(
    page_title="N100 Overview",
    page_icon="📊",
    layout="wide",
)

st.title("📊 N100 Overview")
st.caption("N100 Financial Intelligence Platform")


@st.cache_data
def load_data():
    companies = pd.read_excel(COMPANIES_FILE, header=1)
    ratios = pd.read_csv(RATIOS_FILE)
    return companies, ratios


try:
    companies, ratios = load_data()

    total_companies = companies["id"].nunique()
    avg_roce = companies["roce_percentage"].mean()
    avg_roe = companies["roe_percentage"].mean()

    debt_free_count = (
        ratios.groupby("company_id")["debt_free_flag"]
        .max()
        .sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("N100 Companies", total_companies)
    col2.metric("Average ROCE", f"{avg_roce:.2f}%")
    col3.metric("Average ROE", f"{avg_roe:.2f}%")
    col4.metric("Debt-Free Companies", int(debt_free_count))

    st.divider()

    st.subheader("Top Companies by ROCE")

    top_roce = (
        companies[
            ["id", "company_name", "roce_percentage", "roe_percentage"]
        ]
        .sort_values("roce_percentage", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    top_roce.index = top_roce.index + 1

    st.dataframe(
        top_roce,
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Unable to load dashboard data: {e}")