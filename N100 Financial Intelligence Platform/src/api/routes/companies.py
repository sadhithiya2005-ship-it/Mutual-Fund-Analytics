import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.schemas.common import CompaniesResponse


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


ROOT = Path(__file__).resolve().parents[3]

COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
SECTORS_FILE = ROOT / "data" / "raw" / "sectors.xlsx"
PL_FILE = ROOT / "data" / "raw" / "profitandloss.xlsx"
BS_FILE = ROOT / "data" / "raw" / "balancesheet.xlsx"
CASHFLOW_FILE = ROOT / "data" / "raw" / "cashflow.xlsx"
TEARSHEET_DIR = ROOT / "output" / "reports" / "tearsheets"
PEER_GROUPS_FILE = ROOT / "data" / "raw" / "peer_groups.xlsx"


@router.get("/", response_model=CompaniesResponse)
def get_companies(
    sector: str | None = Query(default=None),
    market_cap_category: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    """Return the N100 company list with optional filters."""

    try:
        companies = pd.read_excel(
            COMPANIES_FILE,
            header=1,
        )

        sectors = pd.read_excel(
            SECTORS_FILE,
            header=0,
        )

        df = companies.merge(
            sectors[
                [
                    "company_id",
                    "broad_sector",
                    "sub_sector",
                    "market_cap_category",
                ]
            ],
            left_on="id",
            right_on="company_id",
            how="left",
        )

        if sector:
            df = df[
                df["broad_sector"]
                .astype(str)
                .str.contains(
                    sector,
                    case=False,
                    na=False,
                )
            ]

        if market_cap_category:
            df = df[
                df["market_cap_category"]
                .astype(str)
                .str.contains(
                    market_cap_category,
                    case=False,
                    na=False,
                )
            ]

        if search:
            search_text = search.lower()

            df = df[
                df["id"]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_text,
                    na=False,
                )
                |
                df["company_name"]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_text,
                    na=False,
                )
            ]

        columns = [
            "id",
            "company_name",
            "broad_sector",
            "sub_sector",
            "website",
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage",
            "market_cap_category",
        ]

        columns = [
            column
            for column in columns
            if column in df.columns
        ]

        records = json.loads(
            df[columns]
            .where(
                pd.notna(df[columns]),
                None,
            )
            .to_json(
                orient="records"
            )
        )

        return {
            "count": len(records),
            "companies": records,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load companies: {exc}",
        )


@router.get("/{ticker}/documents")
def get_company_documents(ticker: str):
    """
    Return company document/profile links.

    URL validity checks whether the stored value has
    a valid HTTP or HTTPS URL format.
    """

    try:
        companies = pd.read_excel(
            COMPANIES_FILE,
            header=1,
        )

        ticker = ticker.upper()

        company = companies[
            companies["id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        record = company.iloc[0]

        documents = []

        document_fields = [
            ("website", record.get("website")),
            ("nse_profile", record.get("nse_profile")),
            ("bse_profile", record.get("bse_profile")),
        ]

        for document_type, url in document_fields:

            if pd.isna(url) or not str(url).strip():
                continue

            url = str(url).strip()

            is_url_valid = (
                url.startswith("http://")
                or url.startswith("https://")
            )

            documents.append(
                {
                    "document_type": document_type,
                    "url": url,
                    "is_url_valid": is_url_valid,
                }
            )

        return {
            "company_id": ticker,
            "company_name": record.get("company_name"),
            "count": len(documents),
            "documents": documents,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load company documents: "
                f"{exc}"
            ),
        )


@router.get("/{ticker}/ratios")
def get_company_ratios(ticker: str):
    """Return all financial ratio records for a company."""

    try:
        df = pd.read_csv(
            RATIOS_FILE,
        )

        ticker = ticker.upper()

        company_data = df[
            df["company_id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        records = json.loads(
            company_data
            .where(
                pd.notna(company_data),
                None,
            )
            .to_json(
                orient="records",
                date_format="iso",
            )
        )

        return {
            "company_id": ticker,
            "company_name": records[0].get(
                "company_name"
            ),
            "count": len(records),
            "ratios": records,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load ratio data: {exc}",
        )


@router.get("/{ticker}")
def get_company_profile(ticker: str):
    """Return full company profile with latest KPIs and sector data."""

    try:
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

        ticker = ticker.upper()

        company = companies[
            companies["id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        company_record = json.loads(
            company
            .where(
                pd.notna(company),
                None,
            )
            .to_json(
                orient="records"
            )
        )[0]

        sector_data = sectors[
            sectors["company_id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if not sector_data.empty:
            sector_record = json.loads(
                sector_data
                .where(
                    pd.notna(sector_data),
                    None,
                )
                .to_json(
                    orient="records"
                )
            )[0]
        else:
            sector_record = {}

        company_ratios = ratios[
            ratios["company_id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company_ratios.empty:
            latest_kpis = {}

        else:
            company_ratios["year_num"] = pd.to_numeric(
                company_ratios["year"]
                .astype(str)
                .str.extract(r"(\d{4})")[0],
                errors="coerce",
            )

            latest = (
                company_ratios
                .sort_values("year_num")
                .tail(1)
            )

            latest_kpis = json.loads(
                latest
                .where(
                    pd.notna(latest),
                    None,
                )
                .to_json(
                    orient="records"
                )
            )[0]

            latest_kpis.pop(
                "year_num",
                None,
            )

        return {
            "company_id": ticker,
            "company": company_record,
            "sector": sector_record,
            "latest_kpis": latest_kpis,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load company profile: {exc}",
        )


@router.get("/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return P&L history for a company."""

    try:
        df = pd.read_excel(
            PL_FILE,
            header=1,
        )

        ticker = ticker.upper()

        company_data = df[
            df["company_id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        company_data["year_num"] = pd.to_numeric(
            company_data["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce",
        )

        if from_year:
            company_data = company_data[
                company_data["year_num"]
                >= int(from_year[:4])
            ]

        if to_year:
            company_data = company_data[
                company_data["year_num"]
                <= int(to_year[:4])
            ]

        company_data = company_data.drop(
            columns=["year_num"],
            errors="ignore",
        )

        records = json.loads(
            company_data
            .where(
                pd.notna(company_data),
                None,
            )
            .to_json(
                orient="records"
            )
        )

        return {
            "company_id": ticker,
            "count": len(records),
            "from_year": from_year,
            "to_year": to_year,
            "pl_history": records,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load P&L data: {exc}",
        )


@router.get("/{ticker}/bs")
def get_company_balance_sheet(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return balance sheet history for a company."""

    try:
        df = pd.read_excel(
            BS_FILE,
            header=1,
        )

        ticker = ticker.upper()

        company_data = df[
            df["company_id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        company_data["year_num"] = pd.to_numeric(
            company_data["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce",
        )

        if from_year:
            company_data = company_data[
                company_data["year_num"]
                >= int(from_year[:4])
            ]

        if to_year:
            company_data = company_data[
                company_data["year_num"]
                <= int(to_year[:4])
            ]

        company_data = company_data.drop(
            columns=["year_num"],
            errors="ignore",
        )

        records = json.loads(
            company_data
            .where(
                pd.notna(company_data),
                None,
            )
            .to_json(
                orient="records"
            )
        )

        return {
            "company_id": ticker,
            "count": len(records),
            "from_year": from_year,
            "to_year": to_year,
            "balance_sheet_history": records,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load balance sheet data: {exc}",
        )


@router.get("/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return cash flow history for a company."""

    try:
        df = pd.read_excel(
            CASHFLOW_FILE,
            header=1,
        )

        ticker = ticker.upper()

        company_data = df[
            df["company_id"]
            .astype(str)
            .str.upper()
            == ticker
        ].copy()

        if company_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        company_data["year_num"] = pd.to_numeric(
            company_data["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce",
        )

        if from_year:
            company_data = company_data[
                company_data["year_num"]
                >= int(from_year[:4])
            ]

        if to_year:
            company_data = company_data[
                company_data["year_num"]
                <= int(to_year[:4])
            ]

        company_data = company_data.drop(
            columns=["year_num"],
            errors="ignore",
        )

        records = json.loads(
            company_data
            .where(
                pd.notna(company_data),
                None,
            )
            .to_json(
                orient="records"
            )
        )

        return {
            "company_id": ticker,
            "count": len(records),
            "from_year": from_year,
            "to_year": to_year,
            "cashflow_history": records,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load cash flow data: {exc}",
        )


@router.get("/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):
    """Return the pre-generated tearsheet PDF for a company."""

    ticker = ticker.upper()

    tearsheet_file = (
        TEARSHEET_DIR
        / f"{ticker}_tearsheet.pdf"
    )

    if not tearsheet_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet not found for company '{ticker}'",
        )

    return FileResponse(
        path=tearsheet_file,
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )


@router.get("/{ticker}/peers/compare")
def compare_company_with_peers(ticker: str):
    """Return radar-style comparison data for a company and its peer group."""

    try:
        ticker = ticker.upper()

        peer_groups = pd.read_excel(
            PEER_GROUPS_FILE,
            header=0,
        )

        ratios = pd.read_csv(
            RATIOS_FILE,
        )

        peer_groups["company_id"] = (
            peer_groups["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        peer_groups["peer_group_name"] = (
            peer_groups["peer_group_name"]
            .astype(str)
            .str.strip()
        )

        company_group = peer_groups[
            peer_groups["company_id"] == ticker
        ].copy()

        if company_group.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found in peer groups",
            )

        peer_group_name = company_group.iloc[0][
            "peer_group_name"
        ]

        peer_data = peer_groups[
            peer_groups["peer_group_name"].str.lower()
            == str(peer_group_name).lower()
        ].copy()

        ratios["company_id"] = (
            ratios["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        ratios["year_num"] = pd.to_numeric(
            ratios["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
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

        metric_map = {
            "ROE": "return_on_equity_pct",
            "Debt to Equity": "debt_to_equity",
            "Net Profit Margin": "net_profit_margin_pct",
            "Operating Profit Margin": (
                "operating_profit_margin_pct"
            ),
            "Free Cash Flow": "free_cash_flow_cr",
            "Asset Turnover": "asset_turnover",
            "Interest Coverage": "interest_coverage",
            "EPS": "earnings_per_share",
        }

        available_axes = []

        for axis_name, column_name in metric_map.items():
            if column_name in latest_ratios.columns:
                available_axes.append(
                    (axis_name, column_name)
                )

        merged = peer_data.merge(
            latest_ratios,
            on="company_id",
            how="left",
        )

        company_row = merged[
            merged["company_id"] == ticker
        ]

        if company_row.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No KPI data found for '{ticker}'",
            )

        company_values = {}
        peer_averages = {}

        for axis_name, column_name in available_axes:
            values = pd.to_numeric(
                merged[column_name],
                errors="coerce",
            )

            company_value = pd.to_numeric(
                company_row.iloc[0][column_name],
                errors="coerce",
            )

            peer_average = values.mean()

            company_values[axis_name] = (
                None
                if pd.isna(company_value)
                else float(company_value)
            )

            peer_averages[axis_name] = (
                None
                if pd.isna(peer_average)
                else float(peer_average)
            )

        benchmark_rows = merged[
            merged["is_benchmark"]
            .astype(str)
            .str.lower()
            .isin(
                [
                    "true",
                    "1",
                    "yes",
                ]
            )
        ]

        benchmark_company = None
        benchmark_values = {}

        if not benchmark_rows.empty:
            benchmark_company = benchmark_rows.iloc[0][
                "company_id"
            ]

            for axis_name, column_name in available_axes:
                value = pd.to_numeric(
                    benchmark_rows.iloc[0][column_name],
                    errors="coerce",
                )

                benchmark_values[axis_name] = (
                    None
                    if pd.isna(value)
                    else float(value)
                )

        axes = list(company_values.keys())

        return {
            "company_id": ticker,
            "peer_group_name": peer_group_name,
            "benchmark_company": benchmark_company,
            "axes": axes,
            "company": company_values,
            "peer_group_average": peer_averages,
            "benchmark": benchmark_values,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to compare company with peers: {exc}",
        )