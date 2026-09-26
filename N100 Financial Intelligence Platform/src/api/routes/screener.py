import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/screener",
    tags=["Screener"],
)


ROOT = Path(__file__).resolve().parents[3]

RATIOS_FILE = (
    ROOT
    / "output"
    / "financial_ratios_engineered.csv"
)

SCREENER_OUTPUT_FILE = (
    ROOT
    / "output"
    / "screener_output.csv"
)


@router.get("/")
def screen_companies(
    min_roe: float | None = Query(
        default=None,
        description="Minimum ROE percentage",
    ),
    max_debt_to_equity: float | None = Query(
        default=None,
        description="Maximum debt-to-equity ratio",
    ),
    min_opm: float | None = Query(
        default=None,
        description="Minimum operating profit margin percentage",
    ),
    min_pe: float | None = Query(
        default=None,
        description="Minimum PE ratio",
    ),
    max_pe: float | None = Query(
        default=None,
        description="Maximum PE ratio",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    """Screen companies using financial metrics."""

    try:
        df = pd.read_csv(
            RATIOS_FILE
        )

        df["year_num"] = pd.to_numeric(
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce",
        )

        # Use latest available record for each company.
        df = (
            df.sort_values("year_num")
            .groupby(
                "company_id",
                as_index=False,
            )
            .tail(1)
        )

        if min_roe is not None:
            df = df[
                df["return_on_equity_pct"]
                >= min_roe
            ]

        if max_debt_to_equity is not None:
            df = df[
                df["debt_to_equity"]
                <= max_debt_to_equity
            ]

        if min_opm is not None:
            df = df[
                df["operating_profit_margin_pct"]
                >= min_opm
            ]

        if min_pe is not None:
            df = df[
                df["pe_ratio"]
                >= min_pe
            ]

        if max_pe is not None:
            df = df[
                df["pe_ratio"]
                <= max_pe
            ]

        # Apply requested result limit.
        df = df.head(limit).copy()

        # Remove helper column before export.
        export_df = df.drop(
            columns=["year_num"],
            errors="ignore",
        )

        # Save screener output for Sprint 6 acceptance testing.
        export_df.to_csv(
            SCREENER_OUTPUT_FILE,
            index=False,
        )

        records = json.loads(
            export_df
            .where(pd.notna(export_df), None)
            .to_json(
                orient="records"
            )
        )

        return {
            "count": len(records),
            "filters": {
                "min_roe": min_roe,
                "max_debt_to_equity": max_debt_to_equity,
                "min_opm": min_opm,
                "min_pe": min_pe,
                "max_pe": max_pe,
            },
            "results": records,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to run screener: "
                f"{exc}"
            ),
        )