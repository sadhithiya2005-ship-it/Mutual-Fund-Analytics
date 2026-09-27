from pathlib import Path
import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

COMPANIES_FILE = BASE_DIR / "data" / "raw" / "companies.xlsx"
SECTORS_FILE = BASE_DIR / "data" / "raw" / "sectors.xlsx"
RATIOS_FILE = BASE_DIR / "output" / "financial_ratios_engineered.csv"

OUTPUT_DIR = BASE_DIR / "reports" / "portfolio"
OUTPUT_FILE = OUTPUT_DIR / "portfolio_summary.pdf"


# ============================================================
# HELPERS
# ============================================================

def clean_number(value):
    """Convert a value to float when possible."""
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def format_value(value, suffix="", decimals=2):
    """Format KPI values safely."""
    value = clean_number(value)

    if pd.isna(value):
        return "N/A"

    return f"{value:.{decimals}f}{suffix}"


def trend_arrow(current, previous):
    """
    Return a simple trend arrow comparing current and previous values.

    ↑ = increased
    ↓ = decreased
    → = approximately unchanged
    — = unavailable
    """
    current = clean_number(current)
    previous = clean_number(previous)

    if pd.isna(current) or pd.isna(previous):
        return "—"

    if current > previous:
        return "↑"

    if current < previous:
        return "↓"

    return "→"


def safe_year_sort(df):
    """Create a sortable year value from mixed year strings."""
    result = df.copy()

    result["_year_num"] = (
        result["year"]
        .astype(str)
        .str.extract(r"(\d{4})", expand=False)
    )

    result["_year_num"] = pd.to_numeric(
        result["_year_num"],
        errors="coerce",
    )

    return result.sort_values(
        ["company_id", "_year_num"],
        na_position="last",
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load companies, sector mapping and engineered financial ratios."""

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

    companies.columns = [
        str(col).strip()
        for col in companies.columns
    ]

    sectors.columns = [
        str(col).strip()
        for col in sectors.columns
    ]

    ratios.columns = [
        str(col).strip()
        for col in ratios.columns
    ]

    return companies, sectors, ratios


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(companies, sectors, ratios):
    """Prepare latest and previous KPI records for all companies."""

    # --------------------------------------------------------
    # Company ID cleanup
    # --------------------------------------------------------

    companies["id"] = companies["id"].astype(str).str.strip()

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

    # --------------------------------------------------------
    # Sector mapping
    # --------------------------------------------------------

    sector_map = (
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
            ]
        ]
        .drop_duplicates("company_id")
    )

    # --------------------------------------------------------
    # Company master
    # --------------------------------------------------------

    master = companies.merge(
        sector_map,
        left_on="id",
        right_on="company_id",
        how="left",
    )

    # Keep one company record per ticker
    master = master.drop_duplicates(
        subset=["id"]
    )

    # --------------------------------------------------------
    # Ratios
    # --------------------------------------------------------

    ratios = safe_year_sort(ratios)

    # Latest and previous record per company
    latest = (
        ratios
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    previous = (
        ratios
        .groupby("company_id", as_index=False)
        .nth(-2)
        .copy()
    )

    return master, ratios, latest, previous


# ============================================================
# KPI DEFINITIONS
# ============================================================

KPI_DEFINITIONS = [
    (
        "ROE",
        "return_on_equity_pct",
        "%",
    ),
    (
        "ROCE",
        "roce_pct",
        "%",
    ),
    (
        "Operating Margin",
        "operating_profit_margin_pct",
        "%",
    ),
    (
        "Net Margin",
        "net_profit_margin_pct",
        "%",
    ),
    (
        "Debt / Equity",
        "debt_to_equity",
        "x",
    ),
    (
        "Free Cash Flow",
        "free_cash_flow_cr",
        " Cr",
    ),
]


# ============================================================
# PDF HEADER / FOOTER
# ============================================================

def add_page_number(canvas, doc):
    """Add footer page number to each PDF page."""

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.drawCentredString(
        A4[0] / 2,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# COMPANY PAGE
# ============================================================

def build_company_page(
    story,
    company,
    latest,
    previous,
):
    """Build one complete portfolio-summary page."""

    ticker = str(
        company.get("id", "")
    ).strip()

    company_name = str(
        company.get("company_name", ticker)
    ).strip()

    broad_sector = company.get(
        "broad_sector",
        "N/A",
    )

    sub_sector = company.get(
        "sub_sector",
        "",
    )

    if pd.isna(broad_sector):
        broad_sector = "N/A"

    if pd.isna(sub_sector):
        sub_sector = ""

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    story.append(
        Paragraph(
            f"<b>{company_name}</b>",
            TITLE_STYLE,
        )
    )

    story.append(
        Paragraph(
            f"<b>Ticker:</b> {ticker}",
            SUBTITLE_STYLE,
        )
    )

    sector_text = str(broad_sector)

    if sub_sector:
        sector_text += f" | {sub_sector}"

    story.append(
        Paragraph(
            f"<b>Sector:</b> {sector_text}",
            SUBTITLE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # --------------------------------------------------------
    # Latest year
    # --------------------------------------------------------

    latest_year = latest.get(
        "year",
        "N/A",
    )

    if pd.isna(latest_year):
        latest_year = "N/A"

    story.append(
        Paragraph(
            f"<b>Latest available financial period:</b> "
            f"{latest_year}",
            BODY_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # --------------------------------------------------------
    # KPI table
    # --------------------------------------------------------

    table_data = [
        [
            "KPI",
            "Value",
            "Trend",
        ]
    ]

    for label, column, suffix in KPI_DEFINITIONS:

        current = latest.get(
            column,
            np.nan,
        )

        previous_value = previous.get(
            column,
            np.nan,
        )

        if suffix == " Cr":
            value_text = format_value(
                current,
                suffix,
                0,
            )
        elif suffix == "x":
            value_text = format_value(
                current,
                suffix,
                2,
            )
        else:
            value_text = format_value(
                current,
                suffix,
                2,
            )

        arrow = trend_arrow(
            current,
            previous_value,
        )

        table_data.append(
            [
                label,
                value_text,
                arrow,
            ]
        )

    kpi_table = Table(
        table_data,
        colWidths=[
            65 * mm,
            55 * mm,
            25 * mm,
        ],
        repeatRows=1,
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f4e78"),
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
                    9,
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.whitesmoke,
                        colors.HexColor("#edf3f8"),
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(kpi_table)

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    # --------------------------------------------------------
    # Additional company information
    # --------------------------------------------------------

    additional_data = []

    book_value = company.get(
        "book_value",
        company.get(
            "company_book_value",
            np.nan,
        ),
    )

    face_value = company.get(
        "face_value",
        np.nan,
    )

    company_roe = company.get(
        "roe_percentage",
        np.nan,
    )

    company_roce = company.get(
        "roce_percentage",
        np.nan,
    )

    if not pd.isna(book_value):
        additional_data.append(
            [
                "Book Value",
                format_value(
                    book_value,
                    "",
                    2,
                ),
            ]
        )

    if not pd.isna(face_value):
        additional_data.append(
            [
                "Face Value",
                format_value(
                    face_value,
                    "",
                    2,
                ),
            ]
        )

    if not pd.isna(company_roe):
        additional_data.append(
            [
                "Company ROE",
                format_value(
                    company_roe,
                    "%",
                    2,
                ),
            ]
        )

    if not pd.isna(company_roce):
        additional_data.append(
            [
                "Company ROCE",
                format_value(
                    company_roce,
                    "%",
                    2,
                ),
            ]
        )

    if additional_data:

        story.append(
            Paragraph(
                "<b>Additional Company Metrics</b>",
                SECTION_STYLE,
            )
        )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        additional_table = Table(
            additional_data,
            colWidths=[
                65 * mm,
                55 * mm,
            ],
        )

        additional_table.setStyle(
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
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
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

        story.append(
            additional_table
        )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    # --------------------------------------------------------
    # Data availability note
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "<b>Trend legend:</b> "
            "↑ increased from previous available period, "
            "↓ decreased, "
            "→ unchanged, "
            "— unavailable.",
            SMALL_STYLE,
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
            "Values are based on the available project datasets. "
            "N/A indicates that the corresponding source value was "
            "not available for the company or period.",
            SMALL_STYLE,
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():
    """Generate the combined 92-company portfolio summary PDF."""

    print("=" * 60)
    print("SPRINT 5 COMBINED PORTFOLIO SUMMARY")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading source data...")

    companies, sectors, ratios = load_data()

    print(
        f"Companies source rows: {len(companies)}"
    )

    print(
        f"Financial ratio rows: {len(ratios)}"
    )

    master, ratios, latest_df, previous_df = prepare_data(
        companies,
        sectors,
        ratios,
    )

    # --------------------------------------------------------
    # Build lookup dictionaries
    # --------------------------------------------------------

    latest_lookup = {
        str(row["company_id"]).strip(): row
        for _, row in latest_df.iterrows()
    }

    previous_lookup = {
        str(row["company_id"]).strip(): row
        for _, row in previous_df.iterrows()
    }

    # --------------------------------------------------------
    # Sort companies alphabetically
    # --------------------------------------------------------

    master = master.sort_values(
        by="company_name",
        key=lambda s: s.astype(str).str.lower(),
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # PDF document
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="N100 Portfolio Summary",
        author="N100 Financial Intelligence Platform",
    )

    story = []

    generated = 0
    missing_latest = []

    # --------------------------------------------------------
    # One page per company
    # --------------------------------------------------------

    for index, company in master.iterrows():

        ticker = str(
            company.get("id", "")
        ).strip()

        latest = latest_lookup.get(
            ticker,
            {},
        )

        previous = previous_lookup.get(
            ticker,
            {},
        )

        if not isinstance(latest, dict) and hasattr(
            latest,
            "to_dict",
        ):
            latest = latest.to_dict()

        if not isinstance(previous, dict) and hasattr(
            previous,
            "to_dict",
        ):
            previous = previous.to_dict()

        if not latest:
            missing_latest.append(ticker)

        build_company_page(
            story,
            company.to_dict(),
            latest,
            previous,
        )

        generated += 1

        # Every company gets exactly one page
        if index < len(master) - 1:
            story.append(PageBreak())

    # --------------------------------------------------------
    # Build PDF
    # --------------------------------------------------------

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    print()
    print(
        f"Generated companies: {generated}"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print(
        f"File exists: {OUTPUT_FILE.exists()}"
    )

    if missing_latest:
        print(
            f"Companies without latest ratio row: "
            f"{len(missing_latest)}"
        )
        print(
            "Missing tickers:",
            ", ".join(missing_latest),
        )
    else:
        print(
            "All companies have a latest ratio record."
        )

    print("=" * 60)
    print("PORTFOLIO SUMMARY GENERATION COMPLETE")
    print("=" * 60)


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "PortfolioTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    alignment=TA_CENTER,
    spaceAfter=3 * mm,
)

SUBTITLE_STYLE = ParagraphStyle(
    "PortfolioSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
    spaceAfter=2 * mm,
)

SECTION_STYLE = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    alignment=TA_LEFT,
)

BODY_STYLE = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=12,
)

SMALL_STYLE = ParagraphStyle(
    "Small",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    alignment=TA_LEFT,
)


if __name__ == "__main__":
    main()