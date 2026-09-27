"""
Cash-flow intelligence and capital-allocation engine
for the N100 Financial Intelligence Platform.

This module calculates cash-flow KPIs supported by the
available financial_ratios.xlsx source data.

Source limitations:
- PAT is unavailable.
- Sales is unavailable.
- CFF is unavailable.
- Historical borrowings are unavailable.
- Therefore, full distress/deleveraging rules cannot be calculated.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RATIOS_FILE = ROOT / "data" / "raw" / "financial_ratios.xlsx"
OUTPUT_DIR = ROOT / "output"

CASHFLOW_FILE = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_FILE = OUTPUT_DIR / "distress_alerts.csv"
PATTERN_FILE = OUTPUT_DIR / "pattern_changes.csv"


def load_data():
    """Load financial ratio data."""
    return pd.read_excel(RATIOS_FILE)


def build_cashflow_intelligence():
    """Calculate supported cash-flow intelligence KPIs."""

    df = load_data()

    # ---------------------------------------------------------
    # Free Cash Flow
    # ---------------------------------------------------------
    df["free_cash_flow_calculated_cr"] = (
        df["cash_from_operations_cr"]
        - df["capex_cr"]
    )

    # ---------------------------------------------------------
    # FCF conversion relative to CFO
    # ---------------------------------------------------------
    df["fcf_conversion_pct"] = (
        df["free_cash_flow_calculated_cr"]
        / df["cash_from_operations_cr"].replace(0, pd.NA)
        * 100
    )

    # ---------------------------------------------------------
    # CapEx / CFO
    #
    # Sprint specification mentions CapEx / Sales.
    # Sales is unavailable, so this supported proxy is
    # explicitly named capex_to_cfo_pct.
    # ---------------------------------------------------------
    df["capex_to_cfo_pct"] = (
        df["capex_cr"]
        / df["cash_from_operations_cr"].replace(0, pd.NA)
        * 100
    )

    # ---------------------------------------------------------
    # Data availability flags
    # ---------------------------------------------------------
    df["cfo_available_flag"] = (
        df["cash_from_operations_cr"].notna()
    )

    df["pat_available_flag"] = False
    df["cff_available_flag"] = False
    df["borrowings_available_flag"] = False

    # ---------------------------------------------------------
    # CFO quality score
    #
    # Requires PAT, which is unavailable.
    # ---------------------------------------------------------
    df["cfo_quality_score_5yr"] = pd.NA

    # ---------------------------------------------------------
    # Distress rule
    #
    # Required:
    # CFO < 0 AND CFF > 0
    #
    # CFF unavailable.
    # ---------------------------------------------------------
    df["distress_flag"] = False

    df["distress_status"] = (
        "Unavailable - CFF not in source"
    )

    # ---------------------------------------------------------
    # Deleveraging rule
    #
    # Required:
    # CFF < 0 + borrowings declining.
    #
    # Required source fields unavailable.
    # ---------------------------------------------------------
    df["deleveraging_flag"] = False

    df["deleveraging_status"] = (
        "Unavailable - CFF/borrowings not in source"
    )

    # ---------------------------------------------------------
    # Capital allocation classification
    # ---------------------------------------------------------
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


def build_pattern_changes(df):
    """
    Build year-over-year capital-allocation pattern changes.

    Only companies available in the financial-ratio source
    are included.
    """

    work = df[
        [
            "company_id",
            "year",
            "capital_allocation_pattern",
        ]
    ].copy()

    # Convert year strings such as "Mar 2024" and "Sep 2024"
    # into a sortable datetime.
    work["year_date"] = pd.to_datetime(
        work["year"],
        errors="coerce",
    )

    work = work.sort_values(
        ["company_id", "year_date"]
    )

    work["previous_pattern"] = (
        work.groupby("company_id")[
            "capital_allocation_pattern"
        ].shift(1)
    )

    work["pattern_changed"] = (
        work["previous_pattern"].notna()
        & (
            work["capital_allocation_pattern"]
            != work["previous_pattern"]
        )
    )

    pattern_changes = work[
        work["pattern_changed"]
    ].copy()

    pattern_changes = pattern_changes[
        [
            "company_id",
            "year",
            "previous_pattern",
            "capital_allocation_pattern",
            "pattern_changed",
        ]
    ]

    return pattern_changes


def build_latest_year_summary(df):
    """
    Build latest-year capital allocation distribution.

    The latest available observation for each company is used.
    """

    work = df.copy()

    work["year_date"] = pd.to_datetime(
        work["year"],
        errors="coerce",
    )

    latest = (
        work.sort_values(
            ["company_id", "year_date"]
        )
        .groupby("company_id")
        .tail(1)
    )

    summary = (
        latest[
            "capital_allocation_pattern"
        ]
        .value_counts()
        .rename_axis("capital_allocation_pattern")
        .reset_index(name="company_count")
    )

    return summary


def build_distress_alerts(df):
    """Build transparent distress-alert output."""

    return df[
        [
            "company_id",
            "year",
            "cash_from_operations_cr",
            "distress_flag",
            "distress_status",
        ]
    ].copy()


def main():
    """Run cash-flow intelligence and capital-allocation analysis."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = build_cashflow_intelligence()

    # ---------------------------------------------------------
    # Main cash-flow intelligence output
    # ---------------------------------------------------------
    output_columns = [
        "company_id",
        "year",
        "cash_from_operations_cr",
        "capex_cr",
        "free_cash_flow_calculated_cr",
        "fcf_conversion_pct",
        "capex_to_cfo_pct",
        "cfo_available_flag",
        "pat_available_flag",
        "cff_available_flag",
        "borrowings_available_flag",
        "cfo_quality_score_5yr",
        "distress_flag",
        "distress_status",
        "deleveraging_flag",
        "deleveraging_status",
        "capital_allocation_pattern",
    ]

    result = df[output_columns].copy()

    result.to_excel(
        CASHFLOW_FILE,
        index=False,
    )

    # ---------------------------------------------------------
    # Distress alerts
    # ---------------------------------------------------------
    distress_alerts = build_distress_alerts(df)

    distress_alerts.to_csv(
        DISTRESS_FILE,
        index=False,
    )

    # ---------------------------------------------------------
    # Pattern changes
    # ---------------------------------------------------------
    pattern_changes = build_pattern_changes(df)

    pattern_changes.to_csv(
        PATTERN_FILE,
        index=False,
    )

    # ---------------------------------------------------------
    # Latest-year distribution
    # ---------------------------------------------------------
    latest_summary = build_latest_year_summary(df)

    # Save the latest-year summary as another sheet
    # in cashflow_intelligence.xlsx.
    with pd.ExcelWriter(
        CASHFLOW_FILE,
        engine="openpyxl",
        mode="a",
    ) as writer:
        latest_summary.to_excel(
            writer,
            sheet_name="latest_year_summary",
            index=False,
        )

    # ---------------------------------------------------------
    # Console summary
    # ---------------------------------------------------------
    print("CASH-FLOW INTELLIGENCE ENGINE COMPLETED")
    print(f"Rows: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(f"Cash-flow output: {CASHFLOW_FILE}")
    print(f"Distress output: {DISTRESS_FILE}")
    print(f"Pattern changes: {PATTERN_FILE}")
    print()

    print("LATEST-YEAR CAPITAL ALLOCATION:")
    print(
        latest_summary.to_string(
            index=False
        )
    )

    print()
    print("PATTERN CHANGES:")
    print(f"Rows: {len(pattern_changes)}")

    print()
    print("SOURCE LIMITATIONS:")
    print("- PAT: unavailable")
    print("- Sales: unavailable")
    print("- CFF: unavailable")
    print("- Historical borrowings: unavailable")
    print("- Full CFO quality score: unavailable")
    print("- Full distress rule: unavailable")
    print("- Full deleveraging rule: unavailable")


if __name__ == "__main__":
    main()