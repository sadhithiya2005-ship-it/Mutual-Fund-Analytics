"""
CAGR analytics for the N100 Financial Intelligence Platform.

Calculates EPS CAGR where sufficient historical EPS data is available.
Revenue and PAT CAGR are not calculated because those source fields
are not available in the current financial_ratios dataset.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RATIOS_FILE = ROOT / "data" / "raw" / "financial_ratios.xlsx"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "cagr_analysis.csv"


def load_data():
    """Load financial ratio data."""
    return pd.read_excel(RATIOS_FILE)


def extract_year(value):
    """Extract four-digit year from the source year field."""
    return int(str(value)[-4:])


def calculate_eps_cagr(df, years):
    """Calculate EPS CAGR for a given number of years."""

    results = []

    for company_id, group in df.groupby("company_id"):

        group = group.copy()

        group["year_num"] = group["year"].apply(extract_year)

        # Remove duplicate company-year observations.
        group = group.drop_duplicates(
            subset=["company_id", "year_num"],
            keep="first",
        )

        group = group.dropna(subset=["earnings_per_share"])

        if group.empty:
            continue

        latest_year = group["year_num"].max()
        target_year = latest_year - years

        start_rows = group[group["year_num"] <= target_year]

        if start_rows.empty:
            continue

        start_row = start_rows.sort_values("year_num").iloc[-1]
        end_row = group[group["year_num"] == latest_year].iloc[0]

        start_eps = start_row["earnings_per_share"]
        end_eps = end_row["earnings_per_share"]

        if start_eps <= 0 or end_eps <= 0:
            continue

        actual_years = latest_year - start_row["year_num"]

        if actual_years <= 0:
            continue

        cagr = (
            (end_eps / start_eps) ** (1 / actual_years) - 1
        ) * 100

        results.append(
            {
                "company_id": company_id,
                "latest_year": latest_year,
                "start_year": start_row["year_num"],
                "start_eps": start_eps,
                "end_eps": end_eps,
                "actual_years": actual_years,
                f"eps_cagr_{years}yr_pct": cagr,
            }
        )

    return pd.DataFrame(results)


def main():
    """Run CAGR analysis and save results."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    cagr_3 = calculate_eps_cagr(df, 3)
    cagr_5 = calculate_eps_cagr(df, 5)
    cagr_10 = calculate_eps_cagr(df, 10)

    result = cagr_3.merge(
        cagr_5[
            [
                "company_id",
                "eps_cagr_5yr_pct",
            ]
        ],
        on="company_id",
        how="outer",
    )

    result = result.merge(
        cagr_10[
            [
                "company_id",
                "eps_cagr_10yr_pct",
            ]
        ],
        on="company_id",
        how="outer",
    )

    result.to_csv(OUTPUT_FILE, index=False)

    print("CAGR ANALYSIS COMPLETED")
    print(f"Companies with CAGR data: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()