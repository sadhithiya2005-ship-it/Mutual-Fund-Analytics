import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/valuation",
    tags=["Valuation"],
)

market_cap_router = APIRouter(
    prefix="/market-cap",
    tags=["Market Cap"],
)


ROOT = Path(__file__).resolve().parents[3]

VALUATION_FILE = ROOT / "output" / "valuation_analysis.csv"
MARKET_CAP_FILE = ROOT / "data" / "raw" / "market_cap.xlsx"


@router.get("/{company_id}")
def get_company_valuation(company_id: str):
    """Return valuation metrics for a company."""

    try:
        df = pd.read_csv(VALUATION_FILE)

        company_data = df[
            df["company_id"].astype(str).str.upper()
            == company_id.upper()
        ].copy()

        if company_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found",
            )

        record = json.loads(
            company_data.head(1).to_json(
                orient="records"
            )
        )[0]

        return {
            "company_id": company_id.upper(),
            "company_name": record.get("company_name"),
            "valuation": record,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load valuation data: {exc}",
        )


def load_market_cap_history(ticker: str):
    """Load historical market-cap data for a company."""

    df = pd.read_excel(MARKET_CAP_FILE)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.upper()
    )

    ticker = ticker.upper()

    company_data = df[
        (df["company_id"] == ticker)
        & (df["year"].between(2019, 2024))
    ].copy()

    if company_data.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No market-cap history found for "
                f"'{ticker}' between 2019 and 2024"
            ),
        )

    company_data = company_data.sort_values("year")

    records = json.loads(
        company_data.to_json(
            orient="records"
        )
    )

    return {
        "company_id": ticker,
        "year_range": "2019-2024",
        "count": len(records),
        "history": records,
    }


@router.get("/market-cap/{ticker}")
def get_market_cap_history(ticker: str):
    """Return historical market-cap valuation multiples."""

    try:
        return load_market_cap_history(ticker)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load market-cap data: {exc}",
        )


@market_cap_router.get("/{ticker}")
def get_market_cap_exact(ticker: str):
    """
    Sprint 6 exact endpoint.

    GET /api/v1/market-cap/{ticker}
    """

    try:
        return load_market_cap_history(ticker)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load market-cap data: {exc}",
        )