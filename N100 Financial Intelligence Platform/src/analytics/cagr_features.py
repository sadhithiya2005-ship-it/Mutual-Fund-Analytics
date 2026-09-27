from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

P_AND_L_FILE = BASE_DIR / "data" / "raw" / "profitandloss.xlsx"
CASHFLOW_FILE = BASE_DIR / "data" / "raw" / "cashflow.xlsx"
COMPANIES_FILE = BASE_DIR / "data" / "raw" / "companies.xlsx"

OUTPUT_FILE = BASE_DIR / "output" / "cagr_features.csv"


def calculate_cagr(start_value, end_value, years):
    """Calculate CAGR percentage."""
    if pd.isna(start_value) or pd.isna(end_value):
        return np.nan

    if start_value <= 0 or end_value <= 0 or years <= 0:
        return np.nan

    return ((end_value / start_value) ** (1 / years) - 1) * 100


def normalize_year(value):
    """Extract calendar year from financial year text."""
    value = str(value).strip()

    match = pd.Series([value]).str.extract(r"(\d{4})")[0].iloc[0]

    if pd.isna(match):
        return np.nan

    return int(match)


def calculate_revenue_cagr(pl):
    """Calculate 5-year revenue CAGR for each company."""
    df = pl.copy()

    df["year_num"] = df["year"].apply(normalize_year)
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")

    results = []

    for company_id, group in df.groupby("company_id"):
        group = group.dropna(subset=["year_num", "sales"])
        group = group[group["sales"] > 0]
        group = group.sort_values("year_num")

        if group.empty:
            results.append(
                {
                    "company_id": company_id,
                    "revenue_cagr_5yr": np.nan,
                }
            )
            continue

        latest_year = group["year_num"].max()
        start_year = latest_year - 5

        latest_rows = group[group["year_num"] == latest_year]
        start_rows = group[group["year_num"] == start_year]

        if latest_rows.empty or start_rows.empty:
            results.append(
                {
                    "company_id": company_id,
                    "revenue_cagr_5yr": np.nan,
                }
            )
            continue

        start_sales = start_rows.iloc[-1]["sales"]
        end_sales = latest_rows.iloc[-1]["sales"]

        cagr = calculate_cagr(start_sales, end_sales, 5)

        results.append(
            {
                "company_id": company_id,
                "revenue_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(results)


def calculate_fcf_cagr(cashflow):
    """Calculate 5-year FCF CAGR using CFO minus CapEx."""
    df = cashflow.copy()

    df["year_num"] = df["year"].apply(normalize_year)

    df["operating_activity"] = pd.to_numeric(
        df["operating_activity"],
        errors="coerce",
    )

    df["investing_activity"] = pd.to_numeric(
        df["investing_activity"],
        errors="coerce",
    )

    # Project definition:
    # FCF = CFO - CapEx
    # CapEx is represented by the absolute investing activity.
    df["fcf"] = df["operating_activity"] - df["investing_activity"].abs()

    results = []

    for company_id, group in df.groupby("company_id"):
        group = group.dropna(subset=["year_num", "fcf"])
        group = group.sort_values("year_num")

        if group.empty:
            results.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": np.nan,
                }
            )
            continue

        latest_year = group["year_num"].max()
        start_year = latest_year - 5

        latest_rows = group[group["year_num"] == latest_year]
        start_rows = group[group["year_num"] == start_year]

        if latest_rows.empty or start_rows.empty:
            results.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": np.nan,
                }
            )
            continue

        start_fcf = start_rows.iloc[-1]["fcf"]
        end_fcf = latest_rows.iloc[-1]["fcf"]

        cagr = calculate_cagr(start_fcf, end_fcf, 5)

        results.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(results)


def main():
    """Generate 5-year revenue and FCF CAGR features."""

    print("Loading source files...")

    pl = pd.read_excel(P_AND_L_FILE, header=1)
    cashflow = pd.read_excel(CASHFLOW_FILE, header=1)
    companies = pd.read_excel(COMPANIES_FILE, header=1)

    n100 = companies[["id"]].copy()
    n100 = n100.rename(columns={"id": "company_id"})
    n100["company_id"] = n100["company_id"].astype(str).str.strip()

    revenue_cagr = calculate_revenue_cagr(pl)
    fcf_cagr = calculate_fcf_cagr(cashflow)

    result = n100.merge(
        revenue_cagr,
        on="company_id",
        how="left",
    )

    result = result.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nCAGR feature calculation completed.")
    print(f"Companies: {len(result)}")
    print(f"Revenue CAGR available: {result['revenue_cagr_5yr'].notna().sum()}")
    print(f"FCF CAGR available: {result['fcf_cagr_5yr'].notna().sum()}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nMissing Revenue CAGR:")
    print(
        result.loc[
            result["revenue_cagr_5yr"].isna(),
            "company_id",
        ].tolist()
    )

    print("\nMissing FCF CAGR:")
    print(
        result.loc[
            result["fcf_cagr_5yr"].isna(),
            "company_id",
        ].tolist()
    )


if __name__ == "__main__":
    main()