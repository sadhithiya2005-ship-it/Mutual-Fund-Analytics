import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/valuation",
    tags=["Valuation"],
)


ROOT = Path(__file__).resolve().parents[3]
VALUATION_FILE = ROOT / "output" / "valuation_analysis.csv"


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