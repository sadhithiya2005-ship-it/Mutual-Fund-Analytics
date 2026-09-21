import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


ROOT = Path(__file__).resolve().parents[3]
COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"


@router.get("/")
def get_companies():
    """Return the N100 company list."""

    try:
        df = pd.read_excel(
            COMPANIES_FILE,
            header=1,
        )

        columns = [
            "id",
            "company_name",
            "website",
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage",
        ]

        columns = [
            column
            for column in columns
            if column in df.columns
        ]

        records = json.loads(
            df[columns]
            .where(pd.notna(df[columns]), None)
            .to_json(orient="records")
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