"""
Sprint 5 - Sector / Peer Group PDF Report Generator

Generates one PDF report for each of the 11 peer groups defined in
data/raw/peer_groups.xlsx.

Each report contains:
1. Peer-group summary
2. Median KPI values
3. Company-level table with 8 financial metrics
4. Benchmark company identification

Data sources:
- peer_groups.xlsx
- companies.xlsx
- financial_ratios_engineered.csv
"""

from pathlib import Path
import re

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

PEER_GROUPS_FILE = ROOT / "data" / "raw" / "peer_groups.xlsx"
COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"

OUTPUT_DIR = ROOT / "reports" / "sector"


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

METRICS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "roce_pct",
    "OPM": "operating_profit_margin_pct",
    "NPM": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
    "EPS": "earnings_per_share",
    "FCF": "free_cash_flow_cr",
}

METRIC_FORMATS = {
    "ROE": "{:.2f}%",
    "ROCE": "{:.2f}%",
    "OPM": "{:.2f}%",
    "NPM": "{:.2f}%",
    "D/E": "{:.2f}",
    "Interest Coverage": "{:.2f}x",
    "EPS": "{:.2f}",
    "FCF": "{:.0f}",
}


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------


def safe_filename(name: str) -> str:
    """Convert a peer-group name into a safe filename."""
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name


def format_metric(metric_name: str, value) -> str:
    """Format a metric value for PDF display."""
    if pd.isna(value):
        return "N/A"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"

    return METRIC_FORMATS[metric_name].format(value)


def latest_ratio_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the latest available ratio row for each company.

    Handles year values such as:
    - Mar 2024
    - Dec 2023
    - TTM
    """

    work = df.copy()

    def year_sort(value):
        text = str(value).strip()

        if text.upper() == "TTM":
            return 999999

        match = re.search(r"(\d{4})", text)

        if match:
            return int(match.group(1))

        return -1

    work["_year_sort"] = work["year"].apply(year_sort)

    work = work.sort_values(
        ["company_id", "_year_sort"],
        ascending=[True, True],
    )

    latest = work.groupby("company_id", as_index=False).tail(1).copy()

    latest = latest.drop(columns=["_year_sort"], errors="ignore")

    return latest


def load_data():
    """Load peer groups, company information and engineered ratios."""

    print("Loading Sprint 5 sector-report data...")

    # Peer groups
    peer_groups = pd.read_excel(PEER_GROUPS_FILE)

    # Companies
    companies = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    # Financial ratios
    ratios = pd.read_csv(RATIOS_FILE)

    print(f"Peer-group rows: {len(peer_groups)}")
    print(f"Companies: {companies['id'].nunique()}")
    print(f"Ratio rows: {len(ratios)}")

    return peer_groups, companies, ratios


def prepare_data(peer_groups, companies, ratios):
    """Prepare the latest financial metrics for all companies."""

    latest = latest_ratio_rows(ratios)

    company_columns = [
        "id",
        "company_name",
        "roce_percentage",
        "roe_percentage",
    ]

    available_company_columns = [
        column
        for column in company_columns
        if column in companies.columns
    ]

    company_info = companies[available_company_columns].copy()

    company_info = company_info.rename(
        columns={
            "id": "company_id",
            "roce_percentage": "company_roce",
            "roe_percentage": "company_roe",
        }
    )

    merged = peer_groups.merge(
        company_info,
        on="company_id",
        how="left",
    )

    merged = merged.merge(
        latest,
        on="company_id",
        how="left",
        suffixes=("", "_ratio"),
    )

    return merged


# ---------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------


def build_styles():
    """Create ReportLab styles."""

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitleCustom",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubtitleCustom",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeadingCustom",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=8,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallCustom",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
        )
    )

    return styles


def create_summary_table(group_df: pd.DataFrame):
    """Create median KPI summary table."""

    rows = [["Metric", "Median"]]

    for metric_name, column_name in METRICS.items():
        if column_name not in group_df.columns:
            value = None
        else:
            numeric = pd.to_numeric(
                group_df[column_name],
                errors="coerce",
            )

            value = numeric.median()

        rows.append(
            [
                metric_name,
                format_metric(metric_name, value),
            ]
        )

    table = Table(
        rows,
        colWidths=[65 * mm, 45 * mm],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17365D"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F2F2F2")],
                ),
            ]
        )
    )

    return table


def create_company_table(group_df: pd.DataFrame):
    """Create company-level table containing the required 8 metrics."""

    headers = [
        "Ticker",
        "Company",
        "Benchmark",
        "ROE",
        "ROCE",
        "OPM",
        "NPM",
        "D/E",
        "ICR",
        "EPS",
        "FCF",
    ]

    rows = [headers]

    for _, row in group_df.sort_values("company_id").iterrows():

        company_id = str(row.get("company_id", ""))

        company_name = str(
            row.get("company_name", "N/A")
        )

        benchmark = (
            "Yes"
            if bool(row.get("is_benchmark", False))
            else "No"
        )

        metric_values = []

        for metric_name, column_name in METRICS.items():

            value = row.get(column_name)

            metric_values.append(
                format_metric(
                    metric_name,
                    value,
                )
            )

        rows.append(
            [
                company_id,
                Paragraph(
                    company_name,
                    ParagraphStyle(
                        "CompanyCell",
                        fontSize=6.5,
                        leading=8,
                    ),
                ),
                benchmark,
                *metric_values,
            ]
        )

    column_widths = [
        18 * mm,
        48 * mm,
        17 * mm,
        16 * mm,
        16 * mm,
        16 * mm,
        16 * mm,
        14 * mm,
        18 * mm,
        16 * mm,
        20 * mm,
    ]

    table = Table(
        rows,
        colWidths=column_widths,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17365D"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    6.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (3, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (2, -1),
                    "CENTER",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7F7F7")],
                ),
            ]
        )
    )

    return table


def create_sector_report(
    peer_group_name: str,
    group_df: pd.DataFrame,
    styles,
):
    """Generate one PDF report for a peer group."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        safe_filename(peer_group_name)
        + "_report.pdf"
    )

    output_path = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{peer_group_name} Report",
        author="N100 Financial Intelligence Platform",
    )

    story = []

    # -------------------------------------------------------------
    # Title
    # -------------------------------------------------------------

    story.append(
        Paragraph(
            f"{peer_group_name} — Sector / Peer Group Report",
            styles["ReportTitleCustom"],
        )
    )

    story.append(
        Paragraph(
            (
                "N100 Financial Intelligence Platform | "
                f"Companies: {len(group_df)}"
            ),
            styles["SubtitleCustom"],
        )
    )

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    story.append(
        Paragraph(
            "Peer Group Summary",
            styles["SectionHeadingCustom"],
        )
    )

    benchmark_companies = group_df[
        group_df["is_benchmark"] == True
    ]["company_id"].dropna().astype(str).tolist()

    if benchmark_companies:
        benchmark_text = ", ".join(
            benchmark_companies
        )
    else:
        benchmark_text = "None identified"

    story.append(
        Paragraph(
            (
                f"<b>Company count:</b> {len(group_df)}<br/>"
                f"<b>Benchmark company:</b> {benchmark_text}"
            ),
            styles["SmallCustom"],
        )
    )

    story.append(Spacer(1, 6))

    story.append(
        create_summary_table(group_df)
    )

    story.append(PageBreak())

    # -------------------------------------------------------------
    # Company details
    # -------------------------------------------------------------

    story.append(
        Paragraph(
            "Company-Level Financial Metrics",
            styles["SectionHeadingCustom"],
        )
    )

    story.append(
        Paragraph(
            (
                "The table below contains the eight required financial "
                "metrics using the latest available engineered ratio "
                "record for each company."
            ),
            styles["SmallCustom"],
        )
    )

    story.append(Spacer(1, 6))

    story.append(
        create_company_table(group_df)
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            (
                "<b>Metric definitions:</b> "
                "ROE = Return on Equity; "
                "ROCE = Return on Capital Employed; "
                "OPM = Operating Profit Margin; "
                "NPM = Net Profit Margin; "
                "D/E = Debt-to-Equity; "
                "ICR = Interest Coverage Ratio; "
                "EPS = Earnings Per Share; "
                "FCF = Free Cash Flow."
            ),
            styles["SmallCustom"],
        )
    )

    doc.build(story)

    return output_path


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main():
    """Generate all 11 peer-group PDF reports."""

    peer_groups, companies, ratios = load_data()

    data = prepare_data(
        peer_groups,
        companies,
        ratios,
    )

    styles = build_styles()

    peer_group_names = (
        peer_groups["peer_group_name"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    print(
        f"Peer groups to generate: {len(peer_group_names)}"
    )

    generated = 0

    for peer_group_name in peer_group_names:

        group_df = data[
            data["peer_group_name"]
            == peer_group_name
        ].copy()

        if group_df.empty:
            print(
                f"SKIPPED: {peer_group_name} "
                "(no companies found)"
            )
            continue

        output_path = create_sector_report(
            peer_group_name,
            group_df,
            styles,
        )

        generated += 1

        print(
            f"Generated: {output_path.name} "
            f"({len(group_df)} companies)"
        )

    print()
    print("========================================")
    print("SPRINT 5 SECTOR REPORT GENERATION")
    print("========================================")
    print(f"Peer groups: {len(peer_group_names)}")
    print(f"Generated:   {generated}")
    print(f"Output:      {OUTPUT_DIR}")
    print("========================================")


if __name__ == "__main__":
    main()