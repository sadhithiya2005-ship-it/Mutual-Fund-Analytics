import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/ratios",
    tags=["Financial Ratios"],
)


ROOT = Path(__file__).resolve().parents[3]
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


@router.get("/{company_id}")
def get_company_ratios(company_id: str):
    """Return financial ratio records for a company."""

    try:
        df = pd.read_csv(RATIOS_FILE)

        company_data = df[
            df["company_id"].astype(str).str.upper()
            == company_id.upper()
        ].copy()

        if company_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found",
            )

        # Convert pandas/numpy values into JSON-safe Python values
        records = json.loads(
            company_data.to_json(
                orient="records",
                date_format="iso",
            )
        )

        return {
            "company_id": company_id.upper(),
            "company_name": records[0].get("company_name"),
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