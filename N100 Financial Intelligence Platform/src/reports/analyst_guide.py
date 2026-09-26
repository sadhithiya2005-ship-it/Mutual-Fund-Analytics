from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "docs"
OUTPUT_FILE = OUTPUT_DIR / "analyst_guide.pdf"


def build_styles():
    """Create PDF paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="GuideTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=24,
            leading=30,
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="GuideSubtitle",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=12,
            leading=18,
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="GuideHeading",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            spaceBefore=8,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="GuideSubheading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            spaceBefore=8,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="GuideBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=15,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="GuideSmall",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=12,
            spaceAfter=5,
        )
    )

    return styles


def footer(canvas, doc):
    """Draw page number footer."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        A4[0] / 2,
        0.4 * inch,
        f"N100 Financial Intelligence Platform | Page {doc.page}",
    )
    canvas.restoreState()


def bullet(text, styles):
    """Create a bullet paragraph."""
    return Paragraph(
        f"• {text}",
        styles["GuideBody"],
    )


def build_story(styles):
    """Build the analyst guide content."""
    story = []

    # Page 1
    story.extend(
        [
            Spacer(1, 1.2 * inch),
            Paragraph(
                "N100 Financial Intelligence Platform",
                styles["GuideTitle"],
            ),
            Paragraph(
                "Analyst Guide",
                styles["GuideTitle"],
            ),
            Spacer(1, 0.3 * inch),
            Paragraph(
                "Sprint 6 — API Server, Clustering & Final QA",
                styles["GuideSubtitle"],
            ),
            Paragraph(
                "Version 1.0",
                styles["GuideSubtitle"],
            ),
            Spacer(1, 0.5 * inch),
            Paragraph(
                "This guide explains how to use the N100 Financial "
                "Intelligence Platform, including the Streamlit dashboard, "
                "screener, company analysis, PDF tearsheets, REST API, "
                "clustering outputs, and troubleshooting procedures.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 2
    story.extend(
        [
            Paragraph(
                "1. Platform Overview",
                styles["GuideHeading"],
            ),
            Paragraph(
                "The N100 Financial Intelligence Platform combines "
                "financial data engineering, financial ratio analysis, "
                "CAGR analysis, cash-flow analysis, clustering, "
                "visual dashboards, PDF reports, and a FastAPI service.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Primary data sources",
                styles["GuideSubheading"],
            ),
            bullet(
                "companies.xlsx — company master information, ROCE and ROE.",
                styles,
            ),
            bullet(
                "market_cap.xlsx — market capitalisation and valuation history.",
                styles,
            ),
            bullet(
                "financial_ratios.xlsx — historical financial ratios.",
                styles,
            ),
            bullet(
                "profitandloss.xlsx — historical P&L information.",
                styles,
            ),
            bullet(
                "balancesheet.xlsx — historical balance-sheet information.",
                styles,
            ),
            bullet(
                "cashflow.xlsx — operating, investing and financing cash flows.",
                styles,
            ),
            bullet(
                "sectors.xlsx — broad sector, sub-sector and index information.",
                styles,
            ),
            bullet(
                "peer_groups.xlsx — peer-group membership and benchmarks.",
                styles,
            ),
            Paragraph(
                "The platform currently covers 92 companies in the company "
                "master dataset.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 3
    story.extend(
        [
            Paragraph(
                "2. Running the Streamlit Dashboard",
                styles["GuideHeading"],
            ),
            Paragraph(
                "Start the dashboard from the project root using:",
                styles["GuideBody"],
            ),
            Paragraph(
                "streamlit run dashboard/app.py",
                styles["GuideSmall"],
            ),
            Paragraph(
                "The dashboard is designed as an analyst-facing interface "
                "for exploring company information, financial metrics, "
                "valuation data, peer information, and analytical outputs.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Typical workflow",
                styles["GuideSubheading"],
            ),
            bullet(
                "Open the Streamlit application in the browser.",
                styles,
            ),
            bullet(
                "Select the required dashboard page.",
                styles,
            ),
            bullet(
                "Choose a company or apply available filters.",
                styles,
            ),
            bullet(
                "Review the displayed financial metrics and analytical results.",
                styles,
            ),
            bullet(
                "Use the screener to narrow the company universe.",
                styles,
            ),
            bullet(
                "Use company-level analysis for detailed investigation.",
                styles,
            ),
            Paragraph(
                "The dashboard should be started from the project environment "
                "so that relative paths to data and output files resolve correctly.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 4
    story.extend(
        [
            Paragraph(
                "3. Using the Financial Screener",
                styles["GuideHeading"],
            ),
            Paragraph(
                "The screener filters companies using financial metrics "
                "from the engineered financial-ratio dataset.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Available filters",
                styles["GuideSubheading"],
            ),
            bullet(
                "Minimum ROE — filters companies at or above the selected ROE.",
                styles,
            ),
            bullet(
                "Maximum Debt-to-Equity — filters companies at or below the selected leverage.",
                styles,
            ),
            bullet(
                "Minimum Operating Profit Margin — filters companies above the selected OPM.",
                styles,
            ),
            bullet(
                "Minimum PE — filters companies at or above the selected PE.",
                styles,
            ),
            bullet(
                "Maximum PE — filters companies at or below the selected PE.",
                styles,
            ),
            bullet(
                "Result limit — controls the maximum number of returned records.",
                styles,
            ),
            Paragraph(
                "Example API screener request:",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/screener/?min_roe=40",
                styles["GuideSmall"],
            ),
            Paragraph(
                "The screener output is also written to "
                "output/screener_output.csv when the API endpoint is called.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 5
    story.extend(
        [
            Paragraph(
                "4. Company Profile Analysis",
                styles["GuideHeading"],
            ),
            Paragraph(
                "The company profile endpoint provides company-level "
                "information together with the latest available analytical "
                "metrics.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Example:",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/companies/TCS",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Related company endpoints",
                styles["GuideSubheading"],
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/pl — P&L history.",
                styles,
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/bs — balance-sheet history.",
                styles,
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/cashflow — cash-flow history.",
                styles,
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/ratios — computed financial ratios.",
                styles,
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/documents — company document links.",
                styles,
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/tearsheet — company PDF tearsheet.",
                styles,
            ),
            bullet(
                "GET /api/v1/companies/{ticker}/peers/compare — peer comparison data.",
                styles,
            ),
            PageBreak(),
        ]
    )

    # Page 6
    story.extend(
        [
            Paragraph(
                "5. Valuation and Market-Cap Analysis",
                styles["GuideHeading"],
            ),
            Paragraph(
                "The valuation module provides company-level valuation "
                "information and historical market-cap multiples.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Valuation endpoint",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/valuation/{ticker}",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Historical market-cap endpoint",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/market-cap/{ticker}",
                styles["GuideSmall"],
            ),
            Paragraph(
                "The historical market-cap data covers the available "
                "2019–2024 valuation history in the source dataset.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Typical valuation fields include P/E, P/B, EV/EBITDA, "
                "dividend yield, market capitalisation and enterprise value.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Analysts should interpret valuation metrics together with "
                "profitability, leverage, growth and cash-flow information "
                "rather than relying on one metric alone.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 7
    story.extend(
        [
            Paragraph(
                "6. Peer and Sector Analysis",
                styles["GuideHeading"],
            ),
            Paragraph(
                "Peer groups are defined in peer_groups.xlsx. The platform "
                "contains 11 peer groups.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Peer groups",
                styles["GuideSubheading"],
            ),
            bullet("Private Banks", styles),
            bullet("Public Sector Banks", styles),
            bullet("IT Services", styles),
            bullet("Pharmaceuticals", styles),
            bullet("Automobiles", styles),
            bullet("Life Insurance", styles),
            bullet("Oil & Gas", styles),
            bullet("Power & Utilities", styles),
            bullet("Steel", styles),
            bullet("FMCG", styles),
            bullet("Consumer Finance", styles),
            Paragraph(
                "Example endpoint:",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/peers/Private%20Banks",
                styles["GuideSmall"],
            ),
            PageBreak(),
        ]
    )

    # Page 8
    story.extend(
        [
            Paragraph(
                "7. Clustering and Portfolio Analytics",
                styles["GuideHeading"],
            ),
            Paragraph(
                "The clustering module assigns the 92 companies to five "
                "KMeans clusters.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Clustering features",
                styles["GuideSubheading"],
            ),
            bullet("Return on equity percentage.", styles),
            bullet("Debt-to-equity ratio.", styles),
            bullet("Five-year revenue CAGR.", styles),
            bullet("Five-year free-cash-flow CAGR.", styles),
            bullet("Operating profit margin percentage.", styles),
            Paragraph(
                "The clustering workflow uses sector-median imputation "
                "for missing feature values, StandardScaler and KMeans "
                "with five clusters and random_state=42.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Key outputs",
                styles["GuideSubheading"],
            ),
            bullet("output/cluster_labels.csv", styles),
            bullet("output/cluster_profiles.csv", styles),
            bullet("reports/elbow_plot.png", styles),
            bullet("output/portfolio_stats.csv", styles),
            PageBreak(),
        ]
    )

    # Page 9
    story.extend(
        [
            Paragraph(
                "8. Generating and Using PDF Tearsheets",
                styles["GuideHeading"],
            ),
            Paragraph(
                "Company tearsheets are generated as PDF reports and "
                "stored under output/reports/tearsheets/.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Typical generation workflow",
                styles["GuideSubheading"],
            ),
            bullet(
                "Run the tearsheet generation module from the project environment.",
                styles,
            ),
            bullet(
                "Verify that PDF files are created under output/reports/tearsheets/.",
                styles,
            ),
            bullet(
                "Check PDF page counts and file sizes.",
                styles,
            ),
            bullet(
                "Open representative PDFs to review layout and readability.",
                styles,
            ),
            Paragraph(
                "The API also exposes a company tearsheet endpoint:",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/companies/{ticker}/tearsheet",
                styles["GuideSmall"],
            ),
            Paragraph(
                "When reviewing reports, check for missing companies, "
                "unexpected blank pages, clipped text and chart overflow.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 10
    story.extend(
        [
            Paragraph(
                "9. REST API Quick Reference",
                styles["GuideHeading"],
            ),
            Paragraph(
                "Start the API with:",
                styles["GuideBody"],
            ),
            Paragraph(
                "uvicorn src.api.main:app --reload",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Health check",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/health/",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Company list",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/companies/",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Screener",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/screener/?min_roe=40",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Portfolio statistics",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/portfolio/stats",
                styles["GuideSmall"],
            ),
            Paragraph(
                "Portfolio clusters",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "GET /api/v1/portfolio/clusters",
                styles["GuideSmall"],
            ),
            Paragraph(
                "The interactive Swagger documentation is available at:",
                styles["GuideBody"],
            ),
            Paragraph(
                "http://127.0.0.1:8000/docs",
                styles["GuideSmall"],
            ),
            PageBreak(),
        ]
    )

    # Page 11
    story.extend(
        [
            Paragraph(
                "10. Troubleshooting",
                styles["GuideHeading"],
            ),
            Paragraph(
                "API connection refused",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "If requests return WinError 10061, confirm that Uvicorn "
                "is running on port 8000 and keep its terminal open.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Missing output file",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "Check that the required source data and output directories "
                "exist. Run the relevant analytics module before calling "
                "the dependent API endpoint.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Import or module error",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "Run commands from the N100 Financial Intelligence Platform "
                "project root and confirm the Python environment contains "
                "the required packages.",
                styles["GuideBody"],
            ),
            Paragraph(
                "PDF generation issue",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "Check that ReportLab is installed and that the output "
                "directory is writable.",
                styles["GuideBody"],
            ),
            Paragraph(
                "Pytest failure",
                styles["GuideSubheading"],
            ),
            Paragraph(
                "Run pytest from the project root and inspect the failing "
                "test before changing application code.",
                styles["GuideBody"],
            ),
            PageBreak(),
        ]
    )

    # Page 12
    story.extend(
        [
            Paragraph(
                "11. Quality Assurance Checklist",
                styles["GuideHeading"],
            ),
            Paragraph(
                "Before final delivery, verify the following:",
                styles["GuideBody"],
            ),
            bullet("92 companies are present in the company master data.", styles),
            bullet("At least 90% of companies have the required historical records.", styles),
            bullet("SQLite foreign-key validation returns zero violations.", styles),
            bullet("Financial-ratio row count meets the Sprint 6 threshold.", styles),
            bullet("Revenue CAGR spot-check is within the specified tolerance.", styles),
            bullet("ROE validation has five companies within the required tolerance.", styles),
            bullet("The quality screener returns the required range.", styles),
            bullet("Company profile response time is below the specified limit.", styles),
            bullet("Screener CSV is generated and valid.", styles),
            bullet("Tearsheet layout has been reviewed.", styles),
            bullet("Health endpoint returns HTTP 200.", styles),
            bullet("TCS ratio history contains at least ten years.", styles),
            bullet("Peer-group coverage is verified.", styles),
            bullet("All companies have cluster assignments.", styles),
            bullet("Pros/cons coverage is reviewed for all companies.", styles),
            bullet("Tearsheet count and file sizes are checked.", styles),
            bullet("Pytest has at least 60 tests with zero failures.", styles),
            bullet("Validation failures are documented.", styles),
            bullet("Analyst guide exists and contains at least ten pages.", styles),
            Paragraph(
                "End of Analyst Guide",
                styles["GuideSubtitle"],
            ),
        ]
    )

    return story


def main():
    """Generate the analyst guide PDF."""
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = build_styles()

    document = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="N100 Financial Intelligence Platform - Analyst Guide",
        author="N100 Financial Intelligence Platform",
    )

    story = build_story(styles)

    document.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    print("ANALYST GUIDE GENERATED")
    print(f"File: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()