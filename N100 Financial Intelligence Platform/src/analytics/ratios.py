"""
Financial ratio engine for the N100 Financial Intelligence Platform.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"
RATIOS_FILE = ROOT / "data" / "raw" / "financial_ratios.xlsx"
MARKET_CAP_FILE = ROOT / "data" / "raw" / "market_cap.xlsx"

OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "financial_ratios_engineered.csv"


def load_data():
    """Load the three available N100 source files."""
    companies = pd.read_excel(COMPANIES_FILE, header=1)
    ratios = pd.read_excel(RATIOS_FILE)
    market_cap = pd.read_excel(MARKET_CAP_FILE)

    return companies, ratios, market_cap


def build_ratio_engine():
    """Build the available financial KPI dataset."""
    companies, ratios, market_cap = load_data()

    company_kpis = companies[
        [
            "id",
            "company_name",
            "book_value",
            "roce_percentage",
            "roe_percentage",
        ]
    ].copy()

    company_kpis = company_kpis.rename(
        columns={
            "id": "company_id",
            "book_value": "company_book_value",
            "roce_percentage": "roce_pct",
            "roe_percentage": "company_roe_pct",
        }
    )

    ratio_kpis = ratios.copy()
    market_kpis = market_cap.copy()

    # Convert both year fields to a common year key.
    ratio_kpis["year_key"] = (
        ratio_kpis["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )

    market_kpis["year_key"] = (
        market_kpis["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )

    # Merge historical ratios with company information.
    result = ratio_kpis.merge(
        company_kpis,
        on="company_id",
        how="left",
    )

    # Merge market valuation information.
    result = result.merge(
        market_kpis[
            [
                "company_id",
                "year_key",
                "market_cap_crore",
                "enterprise_value_crore",
                "pe_ratio",
                "pb_ratio",
                "ev_ebitda",
                "dividend_yield_pct",
            ]
        ],
        on=["company_id", "year_key"],
        how="left",
    )

    result = result.drop(columns=["year_key"])

    # FCF conversion.
    result["fcf_conversion_pct"] = (
        result["free_cash_flow_cr"]
        / result["cash_from_operations_cr"].replace(0, pd.NA)
        * 100
    )

    # CapEx intensity relative to CFO.
    result["capex_to_cfo_pct"] = (
        result["capex_cr"]
        / result["cash_from_operations_cr"].replace(0, pd.NA)
        * 100
    )

    # Debt-free flag.
    result["debt_free_flag"] = result["debt_to_equity"].eq(0)

    # Interest coverage warning.
    result["interest_coverage_warning"] = (
        result["interest_coverage"].notna()
        & (result["interest_coverage"] < 2)
    )

    # High leverage flag.
    result["high_leverage_flag"] = result["debt_to_equity"] > 2

    return result


def main():
    """Run the ratio engine and save the output."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = build_ratio_engine()

    result.to_csv(OUTPUT_FILE, index=False)

    print("RATIO ENGINE COMPLETED")
    print(f"Rows: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()