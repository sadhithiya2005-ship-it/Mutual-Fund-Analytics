"""
Valuation analytics for the N100 Financial Intelligence Platform.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "valuation_analysis.csv"


def load_data():
    """Load the engineered financial ratio dataset."""
    return pd.read_csv(INPUT_FILE)


def build_valuation_analysis():
    """Create a latest-year valuation analysis for each company."""
    df = load_data()

    # Keep the latest available record for each company
    df["year_num"] = (
        df["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .astype(float)
    )

    latest = (
        df.sort_values(["company_id", "year_num"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    valuation = latest[
        [
            "company_id",
            "company_name",
            "year",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
            "company_roe_pct",
            "roce_pct",
        ]
    ].copy()

    # Simple data-quality flags
    valuation["pe_available"] = valuation["pe_ratio"].notna()
    valuation["pb_available"] = valuation["pb_ratio"].notna()
    valuation["ev_ebitda_available"] = valuation["ev_ebitda"].notna()

    # Relative valuation bands based on the N100 dataset itself.
    valuation["pe_percentile"] = (
        valuation["pe_ratio"]
        .rank(pct=True)
        .mul(100)
    )

    valuation["pb_percentile"] = (
        valuation["pb_ratio"]
        .rank(pct=True)
        .mul(100)
    )

    valuation["ev_ebitda_percentile"] = (
        valuation["ev_ebitda"]
        .rank(pct=True)
        .mul(100)
    )

    # Neutral descriptive labels based on dataset percentiles.
    def valuation_band(value):
        if pd.isna(value):
            return "Unavailable"
        if value <= 33.33:
            return "Lower relative valuation"
        if value <= 66.67:
            return "Middle relative valuation"
        return "Higher relative valuation"

    valuation["pe_relative_band"] = valuation["pe_percentile"].apply(
        valuation_band
    )

    valuation["pb_relative_band"] = valuation["pb_percentile"].apply(
        valuation_band
    )

    valuation["ev_ebitda_relative_band"] = (
        valuation["ev_ebitda_percentile"].apply(valuation_band)
    )

    return valuation.drop(columns=["year_num"], errors="ignore")


def main():
    """Run the valuation analytics pipeline."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = build_valuation_analysis()

    result.to_csv(OUTPUT_FILE, index=False)

    print("VALUATION ANALYSIS COMPLETED")
    print(f"Companies: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()