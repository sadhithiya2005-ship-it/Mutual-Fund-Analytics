"""
Company tearsheet generator for the N100 Financial Intelligence Platform.

Generates a two-page PDF company tearsheet using the financial data
available in the current project sources.

Source limitations:
- Revenue is unavailable.
- Absolute net profit/PAT is unavailable.
- Balance-sheet history is unavailable.
- Complete CFI/CFF history is unavailable.
"""

from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]

COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"
RATIOS_FILE = ROOT / "data" / "raw" / "financial_ratios.xlsx"
MARKET_CAP_FILE = ROOT / "data" / "raw" / "market_cap.xlsx"

PROS_CONS_FILE = ROOT / "output" / "pros_cons_generated.csv"
CAGR_FILE = ROOT / "output" / "cagr_analysis.csv"
CASHFLOW_FILE = ROOT / "output" / "cashflow_intelligence.xlsx"

OUTPUT_DIR = ROOT / "output" / "reports" / "tearsheets"


def safe_number(value, decimals=2):
    """Format numeric values safely."""
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def safe_percent(value):
    """Format percentage values safely."""
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def clean_text(value):
    """Convert a value to safe display text."""
    if pd.isna(value):
        return "N/A"

    return str(value)


def parse_year_value(value):
    """Convert different year formats into a sortable datetime."""
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    parsed = pd.to_datetime(
        text,
        errors="coerce",
    )

    if pd.notna(parsed):
        return parsed

    match = re.search(r"(20\d{2}|19\d{2})", text)

    if match:
        return pd.to_datetime(
            match.group(1),
            format="%Y",
            errors="coerce",
        )

    return pd.NaT


def load_sources():
    """Load all available source datasets."""

    companies = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    ratios = pd.read_excel(
        RATIOS_FILE,
        header=0,
    )

    market_cap = pd.read_excel(
        MARKET_CAP_FILE,
        header=0,
    )

    pros_cons = pd.DataFrame()

    if PROS_CONS_FILE.exists():
        pros_cons = pd.read_csv(
            PROS_CONS_FILE,
        )

    cagr = pd.DataFrame()

    if CAGR_FILE.exists():
        cagr = pd.read_csv(
            CAGR_FILE,
        )

    cashflow = pd.DataFrame()

    if CASHFLOW_FILE.exists():
        cashflow = pd.read_excel(
            CASHFLOW_FILE,
        )

    return (
        companies,
        ratios,
        market_cap,
        pros_cons,
        cagr,
        cashflow,
    )


def get_company_data(company_id, sources):
    """Collect available data for one company."""

    (
        companies,
        ratios,
        market_cap,
        pros_cons,
        cagr,
        cashflow,
    ) = sources

    company_rows = companies[
        companies["id"].astype(str).str.strip()
        == str(company_id).strip()
    ].copy()

    ratio_rows = ratios[
        ratios["company_id"].astype(str).str.strip()
        == str(company_id).strip()
    ].copy()

    market_rows = market_cap[
        market_cap["company_id"].astype(str).str.strip()
        == str(company_id).strip()
    ].copy()

    if not pros_cons.empty:
        signal_rows = pros_cons[
            pros_cons["company_id"].astype(str).str.strip()
            == str(company_id).strip()
        ].copy()
    else:
        signal_rows = pd.DataFrame()

    if not cagr.empty:
        cagr_rows = cagr[
            cagr["company_id"].astype(str).str.strip()
            == str(company_id).strip()
        ].copy()
    else:
        cagr_rows = pd.DataFrame()

    if not cashflow.empty:
        cashflow_rows = cashflow[
            cashflow["company_id"].astype(str).str.strip()
            == str(company_id).strip()
        ].copy()
    else:
        cashflow_rows = pd.DataFrame()

    return {
        "company": company_rows,
        "ratios": ratio_rows,
        "market": market_rows,
        "signals": signal_rows,
        "cagr": cagr_rows,
        "cashflow": cashflow_rows,
    }


def latest_row(df):
    """Return latest row based on the year field."""

    if df.empty:
        return None

    work = df.copy()

    if "year" not in work.columns:
        return work.iloc[-1]

    work["_year_date"] = work["year"].apply(
        parse_year_value
    )

    work = work.sort_values(
        "_year_date",
        na_position="last",
    )

    return work.iloc[-1]


def make_styles():
    """Create PDF paragraph styles."""

    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.grey,
            spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "SectionCustom",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=12,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "SmallCustom",
            parent=styles["BodyText"],
            fontSize=7,
            leading=9,
            textColor=colors.grey,
        ),
        "signal": ParagraphStyle(
            "SignalCustom",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
        ),
        "center": ParagraphStyle(
            "CenterCustom",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
        ),
    }


def make_kpi_table(
    latest,
    market_latest,
    cagr_latest,
    company,
):
    """Create KPI tile-style table."""

    kpis = [
        (
            "ROCE",
            safe_percent(
                company.get("roce_percentage")
            ),
        ),
        (
            "ROE",
            safe_percent(
                latest.get("return_on_equity_pct")
            ),
        ),
        (
            "Debt / Equity",
            safe_number(
                latest.get("debt_to_equity")
            ),
        ),
        (
            "Interest Coverage",
            safe_number(
                latest.get("interest_coverage")
            ),
        ),
        (
            "Free Cash Flow",
            safe_number(
                latest.get("free_cash_flow_cr")
            ) + " Cr",
        ),
        (
            "P/E",
            safe_number(
                market_latest.get("pe_ratio")
                if market_latest is not None
                else pd.NA
            ),
        ),
        (
            "P/B",
            safe_number(
                market_latest.get("pb_ratio")
                if market_latest is not None
                else pd.NA
            ),
        ),
        (
            "EPS CAGR 5Y",
            safe_percent(
                cagr_latest.get("eps_cagr_5yr_pct")
                if cagr_latest is not None
                else pd.NA
            ),
        ),
    ]

    cells = []

    for label, value in kpis:
        cells.append(
            Paragraph(
                f"<b>{label}</b><br/>{value}",
                ParagraphStyle(
                    f"KPI_{label}",
                    fontSize=8,
                    leading=12,
                    alignment=TA_CENTER,
                ),
            )
        )

    table = Table(
        [
            cells[:4],
            cells[4:8],
        ],
        colWidths=[
            43 * mm,
            43 * mm,
            43 * mm,
            43 * mm,
        ],
        rowHeights=[
            17 * mm,
            17 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
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
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.whitesmoke,
                ),
            ]
        )
    )

    return table
def create_trend_chart(ratios, company_id):
    """Create a financial trend chart and return its file path."""

    work = ratios.copy()

    work["_year_date"] = work["year"].apply(
        parse_year_value
    )

    work = work.dropna(
        subset=["_year_date"]
    ).sort_values(
        "_year_date"
    ).tail(10)

    if work.empty:
        return None

    chart_dir = (
        ROOT
        / "output"
        / "reports"
        / "charts"
    )

    chart_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    chart_file = (
        chart_dir
        / f"{company_id}_trend.png"
    )

    years = [
        str(value.year)
        for value in work["_year_date"]
    ]

    opm = pd.to_numeric(
        work["operating_profit_margin_pct"],
        errors="coerce",
    )

    roe = pd.to_numeric(
        work["return_on_equity_pct"],
        errors="coerce",
    )

    plt.figure(
        figsize=(8, 3.2)
    )

    plt.plot(
        years,
        opm,
        marker="o",
        label="Operating Profit Margin",
    )

    plt.plot(
        years,
        roe,
        marker="o",
        label="Return on Equity",
    )

    plt.title(
        f"{company_id} - 10-Year Available Trend"
    )

    plt.xlabel("Year")
    plt.ylabel("Percentage")

    plt.xticks(
        rotation=45,
        ha="right",
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.legend(
        fontsize=7,
    )

    plt.tight_layout()

    plt.savefig(
        chart_file,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    return chart_file

def make_trend_table(ratios, company):
    """Create a compact historical trend table."""

    work = ratios.copy()

    work["_year_date"] = work["year"].apply(
        parse_year_value
    )

    work = work.sort_values(
        "_year_date",
        na_position="last",
    ).tail(10)

    header_style = ParagraphStyle(
        "TrendHeader",
        fontSize=7,
        leading=9,
    )

    data = [
        [
            Paragraph(
                "<b>Year</b>",
                header_style,
            ),
            Paragraph(
                "<b>OPM</b>",
                header_style,
            ),
            Paragraph(
                "<b>ROE</b>",
                header_style,
            ),
            Paragraph(
                "<b>ROCE</b>",
                header_style,
            ),
            Paragraph(
                "<b>FCF (Cr)</b>",
                header_style,
            ),
        ]
    ]

    for _, row in work.iterrows():
        data.append(
            [
                clean_text(
                    row.get("year")
                ),
                safe_percent(
                    row.get(
                        "operating_profit_margin_pct"
                    )
                ),
                safe_percent(
                    row.get(
                        "return_on_equity_pct"
                    )
                ),
                safe_percent(
                    company.get(
                        "roce_percentage"
                    )
                ),
                safe_number(
                    row.get(
                        "free_cash_flow_cr"
                    )
                ),
            ]
        )

    return Table(
        data,
        colWidths=[
            34 * mm,
            34 * mm,
            34 * mm,
            34 * mm,
            34 * mm,
        ],
        repeatRows=1,
        style=TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.lightgrey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        ),
    )


def make_pros_cons(signals, styles):
    """Create pros and cons tables."""

    if signals.empty:
        return [
            Paragraph(
                "No generated signals available.",
                styles["body"],
            )
        ]

    pros = signals[
        signals["type"] == "pro"
    ].copy()

    cons = signals[
        signals["type"] == "con"
    ].copy()

    elements = []

    elements.append(
        Paragraph(
            "Pros",
            styles["section"],
        )
    )

    if pros.empty:
        elements.append(
            Paragraph(
                "No supported pro signals available.",
                styles["body"],
            )
        )
    else:
        pro_data = []

        for _, row in pros.iterrows():
            confidence = safe_percent(
                row.get("confidence_pct")
            )

            pro_data.append(
                [
                    Paragraph(
                        f"<b>{clean_text(row.get('rule_id'))}</b>",
                        styles["signal"],
                    ),
                    Paragraph(
                        clean_text(row.get("text")),
                        styles["signal"],
                    ),
                    Paragraph(
                        confidence,
                        styles["center"],
                    ),
                ]
            )

        pro_table = Table(
            pro_data,
            colWidths=[
                20 * mm,
                120 * mm,
                30 * mm,
            ],
        )

        pro_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        elements.append(pro_table)

    elements.append(
        Paragraph(
            "Cons",
            styles["section"],
        )
    )

    if cons.empty:
        elements.append(
            Paragraph(
                "No supported con signals available.",
                styles["body"],
            )
        )
    else:
        con_data = []

        for _, row in cons.iterrows():
            confidence = safe_percent(
                row.get("confidence_pct")
            )

            con_data.append(
                [
                    Paragraph(
                        f"<b>{clean_text(row.get('rule_id'))}</b>",
                        styles["signal"],
                    ),
                    Paragraph(
                        clean_text(row.get("text")),
                        styles["signal"],
                    ),
                    Paragraph(
                        confidence,
                        styles["center"],
                    ),
                ]
            )

        con_table = Table(
            con_data,
            colWidths=[
                20 * mm,
                120 * mm,
                30 * mm,
            ],
        )

        con_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        elements.append(con_table)

    return elements


def make_capital_allocation_section(
    cashflow_rows,
    styles,
):
    """Create capital allocation section."""

    elements = [
        Paragraph(
            "Capital Allocation",
            styles["section"],
        )
    ]

    if cashflow_rows.empty:
        elements.append(
            Paragraph(
                "Capital allocation data unavailable.",
                styles["body"],
            )
        )
        return elements

    latest = latest_row(cashflow_rows)

    pattern = clean_text(
        latest.get(
            "capital_allocation_pattern"
        )
    )

    if pattern == "N/A":
        pattern = clean_text(
            latest.get(
                "capital_allocation_label"
            )
        )

    fcf = safe_number(
        latest.get(
            "free_cash_flow_calculated_cr"
        )
    )

    if fcf == "N/A":
        fcf = safe_number(
            latest.get(
                "free_cash_flow_cr"
            )
        )

    capex = safe_number(
        latest.get("capex_cr")
    )

    data = [
        [
            "Latest Pattern",
            pattern,
        ],
        [
            "Free Cash Flow",
            f"{fcf} Cr",
        ],
        [
            "CapEx",
            f"{capex} Cr",
        ],
    ]

    table = Table(
        data,
        colWidths=[
            50 * mm,
            120 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    elements.append(table)

    return elements


def generate_tearsheet(
    company_id,
    sources,
):
    """Generate a two-page company tearsheet."""

    data = get_company_data(
        company_id,
        sources,
    )

    company_rows = data["company"]
    ratios = data["ratios"]
    market = data["market"]
    signals = data["signals"]
    cagr = data["cagr"]
    cashflow = data["cashflow"]

    if company_rows.empty:
        print(
            f"Skipping {company_id}: company data not found"
        )
        return False

    if ratios.empty:
        print(
            f"Skipping {company_id}: ratio data not found"
        )
        return False

    latest = latest_row(ratios)
    market_latest = latest_row(market)

    cagr_latest = None

    if not cagr.empty:
        cagr["_latest_year_date"] = cagr[
            "latest_year"
        ].apply(parse_year_value)

        cagr = cagr.sort_values(
            "_latest_year_date",
            na_position="last",
        )

        cagr_latest = cagr.iloc[-1]

    company = company_rows.iloc[0]

    company_name = clean_text(
        company.get("company_name")
    )

    safe_company_id = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        str(company_id),
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        OUTPUT_DIR
        / f"{safe_company_id}_tearsheet.pdf"
    )

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    styles = make_styles()

    story = []
    chart_file = create_trend_chart(
    ratios,
    company_id,
)

    # =========================================================
    # PAGE 1
    # =========================================================

    story.append(
        Paragraph(
            company_name,
            styles["title"],
        )
    )
    if chart_file is not None:
        from reportlab.platypus import Image

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Image(
            str(chart_file),
            width=170 * mm,
            height=68 * mm,
        )
    )

    story.append(
        Paragraph(
            f"{company_id} | N100 Financial Intelligence Platform",
            styles["subtitle"],
        )
    )

    story.append(
        Paragraph(
            "Key Financial Indicators",
            styles["section"],
        )
    )

    story.append(
        make_kpi_table(
            latest,
            market_latest,
            cagr_latest,
            company,
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        Paragraph(
            "10-Year Available Financial Trend",
            styles["section"],
        )
    )

    story.append(
        make_trend_table(
            ratios,
            company,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Data Availability Note",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            "Revenue, absolute net profit/PAT, balance-sheet "
            "history, and complete investing/financing "
            "cash-flow data are not available in the supplied "
            "source files. These metrics are therefore not "
            "estimated or fabricated.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # =========================================================
    # PAGE 2
    # =========================================================

    story.append(
        Paragraph(
            "Pros, Cons & Capital Allocation",
            styles["title"],
        )
    )

    story.extend(
        make_pros_cons(
            signals,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.extend(
        make_capital_allocation_section(
            cashflow,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Cash-Flow Intelligence",
            styles["section"],
        )
    )

    if cashflow.empty:
        story.append(
            Paragraph(
                "Cash-flow intelligence unavailable.",
                styles["body"],
            )
        )
    else:
        cash_latest = latest_row(
            cashflow
        )

        cfo_value = cash_latest.get(
            "cash_from_operations_cr"
        )

        capex_value = cash_latest.get(
            "capex_cr"
        )

        fcf_value = cash_latest.get(
            "free_cash_flow_calculated_cr"
        )

        if pd.isna(fcf_value):
            fcf_value = cash_latest.get(
                "free_cash_flow_cr"
            )

        distress_status = cash_latest.get(
            "distress_status"
        )

        if pd.isna(distress_status):
            distress_status = cash_latest.get(
                "distress_flag"
            )

        deleveraging_status = cash_latest.get(
            "deleveraging_status"
        )

        if pd.isna(deleveraging_status):
            deleveraging_status = cash_latest.get(
                "deleveraging_flag"
            )

        cash_data = [
            [
                "CFO",
                f"{safe_number(cfo_value)} Cr",
            ],
            [
                "CapEx",
                f"{safe_number(capex_value)} Cr",
            ],
            [
                "FCF",
                f"{safe_number(fcf_value)} Cr",
            ],
            [
                "Distress Rule",
                clean_text(distress_status),
            ],
            [
                "Deleveraging Rule",
                clean_text(deleveraging_status),
            ],
        ]

        cash_table = Table(
            cash_data,
            colWidths=[
                50 * mm,
                120 * mm,
            ],
        )

        cash_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.lightgrey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(
            cash_table
        )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Report Limitation",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            "This tearsheet reflects only the financial fields "
            "available in the current N100 source package. "
            "Missing source fields are explicitly shown as "
            "unavailable rather than inferred.",
            styles["body"],
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Generated by N100 Financial Intelligence Platform",
            styles["small"],
        )
    )

    doc.build(story)

    return True


def main():
    """Generate tearsheets for all companies."""

    sources = load_sources()

    companies = sources[0]

    generated = 0
    skipped = 0
    skipped_companies = []

    company_ids = (
        companies["id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    for company_id in company_ids:

        success = generate_tearsheet(
            company_id,
            sources,
        )

        if success:
            generated += 1
        else:
            skipped += 1
            skipped_companies.append(
                company_id
            )

    skipped_file = (
        ROOT
        / "output"
        / "skipped_tearsheets.csv"
    )

    if skipped_companies:
        pd.DataFrame(
            {
                "company_id": skipped_companies
            }
        ).to_csv(
            skipped_file,
            index=False,
        )
    else:
        if skipped_file.exists():
            skipped_file.unlink()

    print()
    print(
        "=========================================="
    )
    print(
        "BATCH TEARSHEET GENERATION COMPLETED"
    )
    print(
        "=========================================="
    )
    print(
        f"Generated: {generated}"
    )
    print(
        f"Skipped: {skipped}"
    )
    print(
        f"Total companies: {len(company_ids)}"
    )
    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    if skipped_companies:
        print()
        print(
            "Skipped companies:"
        )
        print(
            skipped_companies
        )
        print(
            f"Skipped log: {skipped_file}"
        )


if __name__ == "__main__":
    main()