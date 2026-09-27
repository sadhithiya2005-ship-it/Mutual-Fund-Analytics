"""
Company tearsheet generator for the N100 Financial Intelligence Platform.

Generates a two-page PDF company tearsheet using the financial data
available in the current project sources.

The report uses only source data available in the project.
Missing financial values are never fabricated.
"""

from pathlib import Path
import re
import tempfile

import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
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


# ============================================================
# SAFE FORMATTERS
# ============================================================

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


# ============================================================
# SOURCE LOADING
# ============================================================

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

    pros_cons = None

    if PROS_CONS_FILE.exists():
        pros_cons = pd.read_csv(
            PROS_CONS_FILE,
        )

    cagr = None

    if CAGR_FILE.exists():
        cagr = pd.read_csv(
            CAGR_FILE,
        )

    cashflow = None

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


# ============================================================
# COMPANY DATA
# ============================================================

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
        companies["id"].astype(str) == str(company_id)
    ]

    ratio_rows = ratios[
        ratios["company_id"].astype(str) == str(company_id)
    ].copy()

    market_rows = market_cap[
        market_cap["company_id"].astype(str) == str(company_id)
    ].copy()

    if pros_cons is not None:
        signal_rows = pros_cons[
            pros_cons["company_id"].astype(str)
            == str(company_id)
        ].copy()
    else:
        signal_rows = pd.DataFrame()

    if cagr is not None:
        cagr_rows = cagr[
            cagr["company_id"].astype(str)
            == str(company_id)
        ].copy()
    else:
        cagr_rows = pd.DataFrame()

    if cashflow is not None:
        cashflow_rows = cashflow[
            cashflow["company_id"].astype(str)
            == str(company_id)
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
    """Return latest row based on year field."""

    if df.empty:
        return None

    work = df.copy()

    if "year" not in work.columns:
        return work.iloc[-1]

    work["_year_date"] = pd.to_datetime(
        work["year"],
        errors="coerce",
    )

    work = work.sort_values(
        "_year_date",
        na_position="last",
    )

    return work.iloc[-1]


# ============================================================
# PDF STYLES
# ============================================================

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


# ============================================================
# CHART HELPERS
# ============================================================

def _save_chart(fig, prefix):
    """
    Save a matplotlib figure as a high-resolution PNG.

    A temporary file is used so generated chart files do not
    remain in the project output folder.
    """

    temp_file = tempfile.NamedTemporaryFile(
        prefix=f"{prefix}_",
        suffix=".png",
        delete=False,
    )

    chart_path = Path(temp_file.name)
    temp_file.close()

    fig.savefig(
        chart_path,
        dpi=220,
        bbox_inches="tight",
        format="png",
    )

    plt.close(fig)

    return chart_path


def create_trend_chart(ratios, company_id):
    """
    Create a historical OPM / ROE / ROCE trend chart.

    Only source values are plotted.
    Missing values are left as missing.
    """

    if ratios.empty:
        return None

    work = ratios.copy()

    if "year" not in work.columns:
        return None

    work["_year_date"] = pd.to_datetime(
        work["year"],
        errors="coerce",
    )

    work = work.sort_values(
        "_year_date",
        na_position="last",
    ).tail(10)

    if work.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(10, 4.8),
    )

    plotted = False

    if "operating_profit_margin_pct" in work.columns:
        values = pd.to_numeric(
            work["operating_profit_margin_pct"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="o",
                linewidth=2,
                label="Operating Profit Margin",
            )
            plotted = True

    if "return_on_equity_pct" in work.columns:
        values = pd.to_numeric(
            work["return_on_equity_pct"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="s",
                linewidth=2,
                label="ROE",
            )
            plotted = True

    if "roce_percentage" in work.columns:
        values = pd.to_numeric(
            work["roce_percentage"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="^",
                linewidth=2,
                label="ROCE",
            )
            plotted = True

    if not plotted:
        plt.close(fig)
        return None

    ax.set_title(
        f"{company_id} - Historical Profitability & Return Trend",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("Percentage")
    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        loc="best",
        fontsize=8,
    )

    fig.tight_layout()

    return _save_chart(
        fig,
        f"{company_id}_trend",
    )


def create_fcf_chart(cashflow, company_id):
    """
    Create a historical CFO / CapEx / FCF chart.

    Only available cash-flow source values are plotted.
    """

    if cashflow.empty:
        return None

    work = cashflow.copy()

    if "year" not in work.columns:
        return None

    work["_year_date"] = pd.to_datetime(
        work["year"],
        errors="coerce",
    )

    work = work.sort_values(
        "_year_date",
        na_position="last",
    ).tail(10)

    if work.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(10, 4.8),
    )

    plotted = False

    if "cash_from_operations_cr" in work.columns:
        values = pd.to_numeric(
            work["cash_from_operations_cr"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="o",
                linewidth=2,
                label="CFO",
            )
            plotted = True

    if "capex_cr" in work.columns:
        values = pd.to_numeric(
            work["capex_cr"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="s",
                linewidth=2,
                label="CapEx",
            )
            plotted = True

    if "free_cash_flow_calculated_cr" in work.columns:
        values = pd.to_numeric(
            work["free_cash_flow_calculated_cr"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="^",
                linewidth=2,
                label="Free Cash Flow",
            )
            plotted = True

    if not plotted:
        plt.close(fig)
        return None

    ax.set_title(
        f"{company_id} - Cash Flow Trend",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("₹ Crore")
    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        loc="best",
        fontsize=8,
    )

    fig.tight_layout()

    return _save_chart(
        fig,
        f"{company_id}_cashflow",
    )


def create_market_chart(market, company_id):
    """
    Create a valuation-history chart using available market-cap
    source records.
    """

    if market.empty:
        return None

    work = market.copy()

    if "year" not in work.columns:
        return None

    work["year_numeric"] = pd.to_numeric(
        work["year"],
        errors="coerce",
    )

    work = work.sort_values(
        "year_numeric",
    ).tail(10)

    if work.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(10, 4.8),
    )

    plotted = False

    if "pe_ratio" in work.columns:
        values = pd.to_numeric(
            work["pe_ratio"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="o",
                linewidth=2,
                label="P/E",
            )
            plotted = True

    if "pb_ratio" in work.columns:
        values = pd.to_numeric(
            work["pb_ratio"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="s",
                linewidth=2,
                label="P/B",
            )
            plotted = True

    if "ev_ebitda" in work.columns:
        values = pd.to_numeric(
            work["ev_ebitda"],
            errors="coerce",
        )

        if values.notna().any():
            ax.plot(
                work["year"].astype(str),
                values,
                marker="^",
                linewidth=2,
                label="EV/EBITDA",
            )
            plotted = True

    if not plotted:
        plt.close(fig)
        return None

    ax.set_title(
        f"{company_id} - Historical Valuation Multiples",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("Multiple")
    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        loc="best",
        fontsize=8,
    )

    fig.tight_layout()

    return _save_chart(
        fig,
        f"{company_id}_valuation",
    )


def create_data_availability_chart(
    company_id,
    market,
    cagr,
    cashflow,
):
    """
    Create a source-availability chart for companies where
    financial-ratio records are unavailable.

    Values are binary source-presence indicators and do not
    represent financial performance.
    """

    labels = [
        "Company Master",
        "Market Cap",
        "CAGR",
        "Cash Flow",
    ]

    values = [
        1,
        int(not market.empty),
        int(not cagr.empty),
        int(not cashflow.empty),
    ]

    fig, ax = plt.subplots(
        figsize=(10, 4.8),
    )

    ax.bar(
        labels,
        values,
    )

    ax.set_ylim(
        0,
        1.2,
    )

    ax.set_yticks(
        [0, 1],
    )

    ax.set_yticklabels(
        ["Unavailable", "Available"],
    )

    ax.set_title(
        f"{company_id} - Source Data Availability",
        fontsize=13,
        fontweight="bold",
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    return _save_chart(
        fig,
        f"{company_id}_availability",
    )


# ============================================================
# TABLES
# ============================================================

def make_unavailable_table(message):
    """Create a table explaining unavailable financial data."""

    data = [
        [
            Paragraph(
                "<b>Data Status</b>",
                ParagraphStyle(
                    "UnavailableHeader",
                    fontSize=8,
                ),
            ),
            Paragraph(
                "<b>Details</b>",
                ParagraphStyle(
                    "UnavailableHeader2",
                    fontSize=8,
                ),
            ),
        ],
        [
            "Financial ratios",
            message,
        ],
        [
            "Data handling",
            "Missing values are not estimated or fabricated.",
        ],
        [
            "Report status",
            "Partial source-data tearsheet",
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
                    0.5,
                    colors.lightgrey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
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
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    return table


def make_kpi_table(latest, market_latest, cagr_latest):
    """Create KPI tile-style table."""

    kpis = [
        (
            "ROCE",
            safe_percent(
                latest.get("roce_pct")
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
                latest.get(
                    "free_cash_flow_cr"
                )
            )
            + " Cr",
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
                cagr_latest.get(
                    "eps_cagr_5yr_pct"
                )
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
                    "KPI",
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


def make_trend_table(ratios):
    """Create a compact historical trend table."""

    if ratios.empty:
        return Table(
            [
                [
                    Paragraph(
                        "<b>Financial trend unavailable</b>",
                        ParagraphStyle(
                            "TrendUnavailable",
                            fontSize=8,
                        ),
                    )
                ]
            ],
            colWidths=[170 * mm],
        )

    work = ratios.copy()

    work["_year_date"] = pd.to_datetime(
        work["year"],
        errors="coerce",
    )

    work = work.sort_values(
        "_year_date",
        na_position="last",
    ).tail(10)

    data = [
        [
            Paragraph(
                "<b>Year</b>",
                ParagraphStyle(
                    "h1",
                    fontSize=7,
                ),
            ),
            Paragraph(
                "<b>OPM</b>",
                ParagraphStyle(
                    "h2",
                    fontSize=7,
                ),
            ),
            Paragraph(
                "<b>ROE</b>",
                ParagraphStyle(
                    "h3",
                    fontSize=7,
                ),
            ),
            Paragraph(
                "<b>ROCE</b>",
                ParagraphStyle(
                    "h4",
                    fontSize=7,
                ),
            ),
            Paragraph(
                "<b>FCF (Cr)</b>",
                ParagraphStyle(
                    "h5",
                    fontSize=7,
                ),
            ),
        ]
    ]

    for _, row in work.iterrows():
        data.append(
            [
                clean_text(row["year"]),
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
                    row.get(
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
                row["confidence_pct"]
            )

            pro_data.append(
                [
                    Paragraph(
                        f"<b>{clean_text(row['rule_id'])}</b>",
                        styles["signal"],
                    ),
                    Paragraph(
                        clean_text(row["text"]),
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
                row["confidence_pct"]
            )

            con_data.append(
                [
                    Paragraph(
                        f"<b>{clean_text(row['rule_id'])}</b>",
                        styles["signal"],
                    ),
                    Paragraph(
                        clean_text(row["text"]),
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

    fcf = safe_number(
        latest.get(
            "free_cash_flow_calculated_cr"
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


# ============================================================
# FALLBACK TEARSHEET
# ============================================================

def generate_unavailable_tearsheet(
    company_id,
    company,
    market,
    signals,
    cagr,
    cashflow,
    output_file,
):
    """Generate a two-page tearsheet when ratio data is unavailable."""

    styles = make_styles()

    company_name = clean_text(
        company.get("company_name")
    )

    market_latest = latest_row(market)

    cagr_latest = None

    if not cagr.empty:
        cagr_latest = cagr.iloc[-1]

    availability_chart = create_data_availability_chart(
        company_id,
        market,
        cagr,
        cashflow,
    )

    valuation_chart = create_market_chart(
        market,
        company_id,
    )

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    story = []

    # ---------------------------------------------------------
    # PAGE 1
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            company_name,
            styles["title"],
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
            "Financial Data Availability",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            "This company is included in the N100 company master "
            "dataset, but the supplied source package does not "
            "contain the financial-ratio records required for a "
            "standard KPI tearsheet.",
            styles["body"],
        )
    )

    story.append(
        make_unavailable_table(
            "Financial ratio source records are unavailable "
            "for this company."
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    if availability_chart is not None:
        story.append(
            Image(
                str(availability_chart),
                width=170 * mm,
                height=70 * mm,
            )
        )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    supporting_data = [
        [
            "Company master",
            "Available",
        ],
        [
            "Market-cap history",
            "Available"
            if not market.empty
            else "Unavailable",
        ],
        [
            "CAGR analysis",
            "Available"
            if not cagr.empty
            else "Unavailable",
        ],
        [
            "Cash-flow intelligence",
            "Available"
            if not cashflow.empty
            else "Unavailable",
        ],
    ]

    supporting_table = Table(
        supporting_data,
        colWidths=[
            70 * mm,
            100 * mm,
        ],
    )

    supporting_table.setStyle(
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
        Paragraph(
            "Available Supporting Data",
            styles["section"],
        )
    )

    story.append(
        supporting_table
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    valuation_data = [
        [
            "P/E",
            safe_number(
                market_latest.get("pe_ratio")
                if market_latest is not None
                else pd.NA
            ),
        ],
        [
            "P/B",
            safe_number(
                market_latest.get("pb_ratio")
                if market_latest is not None
                else pd.NA
            ),
        ],
        [
            "EV / EBITDA",
            safe_number(
                market_latest.get("ev_ebitda")
                if market_latest is not None
                else pd.NA
            ),
        ],
        [
            "Dividend Yield",
            safe_percent(
                market_latest.get("dividend_yield_pct")
                if market_latest is not None
                else pd.NA
            ),
        ],
        [
            "EPS CAGR 5Y",
            safe_percent(
                cagr_latest.get(
                    "eps_cagr_5yr_pct"
                )
                if cagr_latest is not None
                else pd.NA
            ),
        ],
    ]

    valuation_table = Table(
        valuation_data,
        colWidths=[
            70 * mm,
            100 * mm,
        ],
    )

    valuation_table.setStyle(
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
            ]
        )
    )

    story.append(
        Paragraph(
            "Available Valuation Information",
            styles["section"],
        )
    )

    story.append(
        valuation_table
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            "Important: missing financial fields are explicitly "
            "shown as unavailable. No financial values are "
            "estimated or fabricated.",
            styles["body"],
        )
    )

    story.append(
        PageBreak()
    )

    # ---------------------------------------------------------
    # PAGE 2
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Pros, Cons & Cash-Flow Availability",
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
            4 * mm,
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
            4 * mm,
        )
    )

    if valuation_chart is not None:
        story.append(
            Paragraph(
                "Available Valuation Trend",
                styles["section"],
            )
        )

        story.append(
            Image(
                str(valuation_chart),
                width=170 * mm,
                height=68 * mm,
            )
        )

    story.append(
        Spacer(
            1,
            4 * mm,
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
                "Cash-flow intelligence unavailable in the "
                "current source package.",
                styles["body"],
            )
        )
    else:
        cash_latest = latest_row(
            cashflow
        )

        cash_data = [
            [
                "CFO",
                (
                    f"{safe_number(cash_latest.get('cash_from_operations_cr'))} "
                    "Cr"
                ),
            ],
            [
                "CapEx",
                (
                    f"{safe_number(cash_latest.get('capex_cr'))} "
                    "Cr"
                ),
            ],
            [
                "FCF",
                (
                    f"{safe_number(cash_latest.get('free_cash_flow_calculated_cr'))} "
                    "Cr"
                ),
            ],
            [
                "Distress Rule",
                clean_text(
                    cash_latest.get(
                        "distress_status"
                    )
                ),
            ],
            [
                "Deleveraging Rule",
                clean_text(
                    cash_latest.get(
                        "deleveraging_status"
                    )
                ),
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
            4 * mm,
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
            "This fallback tearsheet exists to maintain complete "
            "company-level report coverage while preserving data "
            "integrity. It does not imply that unavailable "
            "financial records exist. Analysts should obtain the "
            "missing source records before performing a complete "
            "financial assessment.",
            styles["body"],
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            "Generated by N100 Financial Intelligence Platform",
            styles["small"],
        )
    )

    doc.build(
        story
    )

    if availability_chart is not None:
        availability_chart.unlink(
            missing_ok=True
        )

    if valuation_chart is not None:
        valuation_chart.unlink(
            missing_ok=True
        )

    return True


# ============================================================
# NORMAL TEARSHEET
# ============================================================

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

    # ---------------------------------------------------------
    # FALLBACK FOR COMPANIES WITHOUT RATIO DATA
    # ---------------------------------------------------------

    if ratios.empty:
        print(
            f"Generating data-unavailable tearsheet for {company_id}: "
            "ratio data not found"
        )

        return generate_unavailable_tearsheet(
            company_id,
            company,
            market,
            signals,
            cagr,
            cashflow,
            output_file,
        )

    latest = latest_row(ratios)
    market_latest = latest_row(market)

    cagr_latest = None

    if not cagr.empty:
        cagr = cagr.copy()

        cagr["_latest_year_date"] = cagr[
            "latest_year"
        ].apply(
            lambda value: pd.to_datetime(
                value,
                errors="coerce",
            )
        )

        cagr = cagr.sort_values(
            "_latest_year_date",
            na_position="last",
        )

        cagr_latest = cagr.iloc[-1]

    trend_chart = create_trend_chart(
        ratios,
        company_id,
    )

    fcf_chart = create_fcf_chart(
        cashflow,
        company_id,
    )

    valuation_chart = create_market_chart(
        market,
        company_id,
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

    # =========================================================
    # PAGE 1
    # =========================================================

    story.append(
        Paragraph(
            company_name,
            styles["title"],
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
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Paragraph(
            "Historical Profitability & Return Trend",
            styles["section"],
        )
    )

    if trend_chart is not None:
        story.append(
            Image(
                str(trend_chart),
                width=170 * mm,
                height=68 * mm,
            )
        )
    else:
        story.append(
            make_trend_table(
                ratios
            )
        )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            "Historical Data Table",
            styles["section"],
        )
    )

    story.append(
        make_trend_table(
            ratios
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
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

    story.append(
        PageBreak()
    )

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
            4 * mm,
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
            4 * mm,
        )
    )

    if fcf_chart is not None:
        story.append(
            Paragraph(
                "Cash-Flow Trend",
                styles["section"],
            )
        )

        story.append(
            Image(
                str(fcf_chart),
                width=170 * mm,
                height=65 * mm,
            )
        )

    elif valuation_chart is not None:
        story.append(
            Paragraph(
                "Historical Valuation Trend",
                styles["section"],
            )
        )

        story.append(
            Image(
                str(valuation_chart),
                width=170 * mm,
                height=65 * mm,
            )
        )

    story.append(
        Spacer(
            1,
            3 * mm,
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

        cash_data = [
            [
                "CFO",
                (
                    f"{safe_number(cash_latest.get('cash_from_operations_cr'))} "
                    "Cr"
                ),
            ],
            [
                "CapEx",
                (
                    f"{safe_number(cash_latest.get('capex_cr'))} "
                    "Cr"
                ),
            ],
            [
                "FCF",
                (
                    f"{safe_number(cash_latest.get('free_cash_flow_calculated_cr'))} "
                    "Cr"
                ),
            ],
            [
                "Distress Rule",
                clean_text(
                    cash_latest.get(
                        "distress_status"
                    )
                ),
            ],
            [
                "Deleveraging Rule",
                clean_text(
                    cash_latest.get(
                        "deleveraging_status"
                    )
                ),
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
            4 * mm,
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
            2 * mm,
        )
    )

    story.append(
        Paragraph(
            "Generated by N100 Financial Intelligence Platform",
            styles["small"],
        )
    )

    doc.build(
        story
    )

    # ---------------------------------------------------------
    # Remove temporary chart files
    # ---------------------------------------------------------

    for chart_file in [
        trend_chart,
        fcf_chart,
        valuation_chart,
    ]:
        if chart_file is not None:
            chart_file.unlink(
                missing_ok=True
            )

    return True


# ============================================================
# BATCH GENERATION
# ============================================================

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