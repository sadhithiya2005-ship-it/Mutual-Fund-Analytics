"""
Cash-flow KPI engine for the N100 Financial Intelligence Platform.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RATIOS_FILE = ROOT / "data" / "raw" / "financial_ratios.xlsx"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "capital_allocation.csv"


def load_data():
    """Load financial ratio data."""
    return pd.read_excel(RATIOS_FILE)


def build_cashflow_kpis():
    """Calculate available cash-flow KPIs."""

    df = load_data()

    # Free Cash Flow
    df["free_cash_flow_calculated_cr"] = (
        df["cash_from_operations_cr"] - df["capex_cr"]
    )

    # FCF conversion relative to CFO
    df["fcf_conversion_pct"] = (
        df["free_cash_flow_calculated_cr"]
        / df["cash_from_operations_cr"].replace(0, pd.NA)
        * 100
    )

    # CapEx intensity relative to CFO
    df["capex_to_cfo_pct"] = (
        df["capex_cr"]
        / df["cash_from_operations_cr"].replace(0, pd.NA)
        * 100
    )

    # CFO quality: CFO relative to reported net profit.
    # Only calculated when net profit margin is available;
    # this source does not contain absolute PAT.
    df["cfo_available_flag"] = (
        df["cash_from_operations_cr"].notna()
    )

    # Capital allocation classification
    def classify(row):
        fcf = row["free_cash_flow_calculated_cr"]
        capex = row["capex_cr"]

        if pd.isna(fcf) or pd.isna(capex):
            return "Insufficient Data"

        if fcf > 0 and capex > 0:
            return "Positive FCF + CapEx"

        if fcf > 0 and capex <= 0:
            return "Positive FCF"

        if fcf <= 0 and capex > 0:
            return "Negative FCF + CapEx"

        return "Negative FCF"

    df["capital_allocation_pattern"] = df.apply(
        classify,
        axis=1,
    )

    return df


def main():
    """Run cash-flow KPI analysis."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = build_cashflow_kpis()

    output_columns = [
        "company_id",
        "year",
        "cash_from_operations_cr",
        "capex_cr",
        "free_cash_flow_calculated_cr",
        "fcf_conversion_pct",
        "capex_to_cfo_pct",
        "cfo_available_flag",
        "capital_allocation_pattern",
    ]

    result = df[output_columns].copy()

    result.to_csv(OUTPUT_FILE, index=False)

    print("CASH-FLOW KPI ENGINE COMPLETED")
    print(f"Rows: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()