from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]

RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
CAGR_FILE = ROOT / "output" / "cagr_analysis.csv"
CASHFLOW_FILE = ROOT / "output" / "capital_allocation.csv"


st.set_page_config(
    page_title="Data Explorer",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Data Explorer")
st.caption("Explore the available N100 financial datasets")


@st.cache_data
def load_data():
    ratios = pd.read_csv(RATIOS_FILE)
    cagr = pd.read_csv(CAGR_FILE)
    cashflow = pd.read_csv(CASHFLOW_FILE)

    return ratios, cagr, cashflow


try:
    ratios, cagr, cashflow = load_data()

    dataset = st.selectbox(
        "Select Dataset",
        [
            "Financial Ratios",
            "EPS CAGR",
            "Cash Flow",
        ],
    )

    if dataset == "Financial Ratios":
        data = ratios.copy()

    elif dataset == "EPS CAGR":
        data = cagr.copy()

    else:
        data = cashflow.copy()

    st.subheader(f"{dataset} Dataset")

    search_text = st.text_input(
        "Search company",
        placeholder="Enter company name...",
    )

    if search_text:
        data = data[
            data["company_name"]
            .astype(str)
            .str.contains(
                search_text,
                case=False,
                na=False,
            )
        ]

    st.write(f"Rows: {len(data)}")

    st.dataframe(
        data,
        use_container_width=True,
        height=550,
    )

except Exception as e:
    st.error(f"Unable to load data: {e}")