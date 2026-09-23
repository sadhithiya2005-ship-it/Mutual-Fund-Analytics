from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[2]

COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
CAGR_FILE = ROOT / "output" / "cagr_analysis.csv"
OUTPUT_DIR = ROOT / "output" / "reports" / "portfolio"


def safe_number(value, default=None):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value, suffix="", decimals=2):
    number = safe_number(value)

    if number is None:
        return "N/A"

    return f"{number:.{decimals}f}{suffix}"


def trend_arrow(current, previous):
    current = safe_number(current)
    previous = safe_number(previous)

    if current is None or previous is None:
        return "→"

    if current > previous:
        return "↑"

    if current < previous:
        return "↓"

    return "→"


def load_data():
    companies = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    ratios = pd.read_csv(
        RATIOS_FILE
    )

    cagr = pd.read_csv(
        CAGR_FILE
    )

    companies["id"] = (
        companies["id"]
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

    return companies, ratios, cagr


def make_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TinyText",
            parent=styles["Normal"],
            fontSize=7,
            leading=8.5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CompanyTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=21,
            spaceAfter=5,
        )
    )

    return styles


def build_company_page(
    company,
    ratios,
    cagr,
    styles,
):
    company_id = str(company["id"])

    company_ratios = ratios[
        ratios["company_id"] == company_id
    ].copy()

    company_ratios["_year"] = pd.to_numeric(
        company_ratios["year"],
        errors="coerce",
    )

    company_ratios = (
        company_ratios
        .dropna(subset=["_year"])
        .sort_values("_year")
    )

    latest = (
        company_ratios.iloc[-1]
        if not company_ratios.empty
        else None
    )

    previous = (
        company_ratios.iloc[-2]
        if len(company_ratios) >= 2
        else None
    )

    company_cagr = cagr[
        cagr["company_id"] == company_id
    ]

    cagr_row = (
        company_cagr.iloc[0]
        if not company_cagr.empty
        else None
    )

    story = []

    company_name = company.get(
        "company_name",
        company_id,
    )

    story.append(
        Paragraph(
            f"{company_name} ({company_id})",
            styles["CompanyTitle"],
        )
    )

    story.append(
        Paragraph(
            "N100 Financial Intelligence Platform — Portfolio Summary",
            styles["SmallText"],
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    if latest is None:
        story.append(
            Paragraph(
                "Financial ratio source data is unavailable for this company.",
                styles["SmallText"],
            )
        )

        return story

    latest_year = latest["_year"]

    story.append(
        Paragraph(
            f"Latest available financial year: {int(latest_year)}",
            styles["SmallText"],
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # KPI values
    opm = latest.get(
        "operating_profit_margin_pct"
    )

    roe = latest.get(
        "return_on_equity_pct"
    )

    debt_to_equity = latest.get(
        "debt_to_equity"
    )

    interest_coverage = latest.get(
        "interest_coverage"
    )

    fcf = latest.get(
        "free_cash_flow_cr"
    )

    roce = company.get(
        "roce_percentage"
    )

    eps_cagr_5yr = (
        cagr_row.get("eps_cagr_5yr_pct")
        if cagr_row is not None
        else None
    )

    kpi_data = [
        [
            "Operating Margin",
            "ROE",
            "ROCE",
            "Debt / Equity",
        ],
        [
            fmt(opm, "%"),
            fmt(roe, "%"),
            fmt(roce, "%"),
            fmt(debt_to_equity),
        ],
        [
            trend_arrow(
                opm,
                previous.get("operating_profit_margin_pct")
                if previous is not None
                else None,
            ),
            trend_arrow(
                roe,
                previous.get("return_on_equity_pct")
                if previous is not None
                else None,
            ),
            "—",
            trend_arrow(
                debt_to_equity,
                previous.get("debt_to_equity")
                if previous is not None
                else None,
            ),
        ],
    ]

    table = Table(
        kpi_data,
        colWidths=[
            43 * mm,
            43 * mm,
            43 * mm,
            43 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
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
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # Additional metrics
    additional_data = [
        ["Metric", "Latest available value"],
        [
            "Free Cash Flow",
            fmt(fcf, " Cr"),
        ],
        [
            "Interest Coverage",
            fmt(interest_coverage, "x"),
        ],
        [
            "EPS CAGR — 5 Year",
            fmt(eps_cagr_5yr, "%"),
        ],
        [
            "Book Value",
            fmt(company.get("book_value")),
        ],
        [
            "Dividend Yield",
            fmt(latest.get("dividend_yield_pct"), "%"),
        ],
    ]

    additional_table = Table(
        additional_data,
        colWidths=[
            75 * mm,
            97 * mm,
        ],
    )

    additional_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
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
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(additional_table)

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # Trend table
    trend_rows = [
        [
            "Year",
            "OPM %",
            "ROE %",
            "Debt / Equity",
            "FCF Cr",
        ]
    ]

    for _, row in company_ratios.tail(5).iterrows():
        trend_rows.append(
            [
                str(int(row["_year"])),
                fmt(
                    row.get(
                        "operating_profit_margin_pct"
                    ),
                    "%",
                ),
                fmt(
                    row.get(
                        "return_on_equity_pct"
                    ),
                    "%",
                ),
                fmt(
                    row.get(
                        "debt_to_equity"
                    )
                ),
                fmt(
                    row.get(
                        "free_cash_flow_cr"
                    )
                ),
            ]
        )

    trend_table = Table(
        trend_rows,
        colWidths=[
            30 * mm,
            35 * mm,
            35 * mm,
            38 * mm,
            34 * mm,
        ],
    )

    trend_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(
        Paragraph(
            "Recent financial trend",
            styles["Heading3"],
        )
    )

    story.append(trend_table)

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Data note: Metrics shown are limited to the available N100 source datasets. Missing source fields are reported as N/A rather than estimated.",
            styles["TinyText"],
        )
    )

    return story


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    companies, ratios, cagr = load_data()

    styles = make_styles()

    generated = 0

    for _, company in companies.iterrows():
        company_id = str(
            company["id"]
        ).strip()

        output_file = (
            OUTPUT_DIR
            / f"{company_id}_portfolio_summary.pdf"
        )

        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        story = build_company_page(
            company,
            ratios,
            cagr,
            styles,
        )

        doc.build(story)

        generated += 1

    print(
        "Portfolio summary generation completed."
    )
    print(
        f"Generated: {generated}"
    )
    print(
        f"Total companies: {len(companies)}"
    )
    print(
        f"Output directory: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()