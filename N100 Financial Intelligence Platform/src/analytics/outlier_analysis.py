from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

COMPANIES_FILE = BASE_DIR / "data" / "raw" / "companies.xlsx"
SECTORS_FILE = BASE_DIR / "data" / "raw" / "sectors.xlsx"
RATIOS_FILE = BASE_DIR / "output" / "financial_ratios_engineered.csv"
CAGR_FILE = BASE_DIR / "output" / "cagr_features.csv"

OUTPUT_DIR = BASE_DIR / "output"

OUTLIER_OUTPUT = OUTPUT_DIR / "outlier_report.csv"
PORTFOLIO_OUTPUT = OUTPUT_DIR / "portfolio_stats.csv"


# Sprint 6 clustering features.
# DO NOT change these because clustering.py uses them.
FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


# Sprint 6 portfolio statistics.
# Ten core KPIs with P10/P25/P50/P75/P90/Mean/Std.
PORTFOLIO_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "interest_coverage",
    "asset_turnover",
    "earnings_per_share",
    "free_cash_flow_cr",
]


def load_data():
    """Load N100, sector, financial ratio and CAGR data."""

    companies = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    sectors = pd.read_excel(
        SECTORS_FILE,
        header=0,
    )

    ratios = pd.read_csv(
        RATIOS_FILE,
    )

    cagr = pd.read_csv(
        CAGR_FILE,
    )

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
    )

    sectors["company_id"] = (
        sectors["company_id"]
        .astype(str)
        .str.strip()
    )

    ratios["company_id"] = (
        ratios["company_id"]
        .astype(str)
        .str.strip()
    )

    cagr["company_id"] = (
        cagr["company_id"]
        .astype(str)
        .str.strip()
    )

    return companies, sectors, ratios, cagr


def prepare_dataset(
    companies,
    sectors,
    ratios,
    cagr,
):
    """Create one latest-year feature row per N100 company."""

    n100 = companies[
        ["id", "company_name"]
    ].copy()

    n100 = n100.rename(
        columns={
            "id": "company_id",
        }
    )

    ratios["year_num"] = (
        ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )

    ratios["year_num"] = pd.to_numeric(
        ratios["year_num"],
        errors="coerce",
    )

    latest_ratios = (
        ratios
        .sort_values("year_num")
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    # Keep all portfolio KPI columns that are available
    # in financial_ratios_engineered.csv.
    ratio_columns = [
        "company_id",
        "return_on_equity_pct",
        "debt_to_equity",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "interest_coverage",
        "asset_turnover",
        "earnings_per_share",
        "free_cash_flow_cr",
    ]

    # Only select columns that actually exist in the source.
    available_ratio_columns = [
        column
        for column in ratio_columns
        if column in latest_ratios.columns
    ]

    ratio_features = latest_ratios[
        available_ratio_columns
    ].copy()

    result = n100.merge(
        ratio_features,
        on="company_id",
        how="left",
    )

    result = result.merge(
        cagr[
            [
                "company_id",
                "revenue_cagr_5yr",
                "fcf_cagr_5yr",
            ]
        ],
        on="company_id",
        how="left",
    )

    result = result.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
            ]
        ],
        on="company_id",
        how="left",
    )

    return result


def sector_median_imputation(df):
    """
    Fill missing clustering feature values using sector medians.

    Only the five clustering features are imputed here because
    this is the same preprocessing used by Sprint 6 clustering.
    """

    df = df.copy()

    for feature in FEATURES:

        df[feature] = pd.to_numeric(
            df[feature],
            errors="coerce",
        )

        sector_median = (
            df.groupby("broad_sector")[feature]
            .transform("median")
        )

        df[feature] = df[feature].fillna(
            sector_median
        )

        # Final overall median fallback
        df[feature] = df[feature].fillna(
            df[feature].median()
        )

    return df


def calculate_zscore(series):
    """Calculate population-style Z-scores."""

    mean = series.mean()
    std = series.std(ddof=0)

    if pd.isna(std) or std == 0:
        return pd.Series(
            0.0,
            index=series.index,
        )

    return (series - mean) / std


def detect_sector_outliers(df):
    """Detect feature outliers within each broad sector."""

    records = []

    for sector, sector_df in df.groupby(
        "broad_sector",
        dropna=False,
    ):

        sector_df = sector_df.copy()

        for feature in FEATURES:

            values = pd.to_numeric(
                sector_df[feature],
                errors="coerce",
            )

            zscores = calculate_zscore(
                values
            )

            for idx in sector_df.index:

                value = values.loc[idx]
                zscore = zscores.loc[idx]

                if pd.isna(value):
                    continue

                if abs(zscore) > 3:

                    records.append(
                        {
                            "company_id": sector_df.loc[
                                idx,
                                "company_id",
                            ],
                            "company_name": sector_df.loc[
                                idx,
                                "company_name",
                            ],
                            "broad_sector": sector,
                            "feature": feature,
                            "value": value,
                            "z_score": zscore,
                            "outlier_flag": True,
                        }
                    )

    return pd.DataFrame(
        records,
        columns=[
            "company_id",
            "company_name",
            "broad_sector",
            "feature",
            "value",
            "z_score",
            "outlier_flag",
        ],
    )


def calculate_portfolio_stats(df):
    """
    Calculate P10/P25/P50/P75/P90/Mean/Std
    for ten core portfolio KPIs.
    """

    records = []

    for feature in PORTFOLIO_FEATURES:

        # Skip a feature only if the source does not contain it.
        if feature not in df.columns:
            continue

        values = pd.to_numeric(
            df[feature],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        records.append(
            {
                "feature": feature,
                "P10": values.quantile(0.10),
                "P25": values.quantile(0.25),
                "P50": values.quantile(0.50),
                "P75": values.quantile(0.75),
                "P90": values.quantile(0.90),
                "Mean": values.mean(),
                "Std": values.std(),
            }
        )

    return pd.DataFrame(records)


def main():
    """Run Sprint 6 Day 37 outlier and portfolio analysis."""

    print("Loading data...")

    (
        companies,
        sectors,
        ratios,
        cagr,
    ) = load_data()

    print(
        "Preparing dataset..."
    )

    df = prepare_dataset(
        companies,
        sectors,
        ratios,
        cagr,
    )

    print(
        f"Companies: {len(df)}"
    )

    print(
        "Applying sector median imputation..."
    )

    df = sector_median_imputation(
        df
    )

    print(
        "Detecting sector outliers..."
    )

    outliers = detect_sector_outliers(
        df
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    outliers.to_csv(
        OUTLIER_OUTPUT,
        index=False,
    )

    print(
        f"Outlier records: {len(outliers)}"
    )

    print(
        "Calculating portfolio statistics..."
    )

    portfolio_stats = (
        calculate_portfolio_stats(df)
    )

    portfolio_stats.to_csv(
        PORTFOLIO_OUTPUT,
        index=False,
    )

    print(
        f"Portfolio KPI count: {len(portfolio_stats)}"
    )

    print(
        "\nAnalysis completed."
    )

    print(
        "\nPortfolio statistics:"
    )

    print(
        portfolio_stats.to_string(
            index=False
        )
    )

    print(
        "\nOutput files:"
    )

    print(
        OUTLIER_OUTPUT
    )

    print(
        PORTFOLIO_OUTPUT
    )


if __name__ == "__main__":
    main()