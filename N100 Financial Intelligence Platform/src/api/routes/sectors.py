import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"],
)


ROOT = Path(__file__).resolve().parents[3]

SECTORS_FILE = ROOT / "data" / "raw" / "sectors.xlsx"
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


@router.get("/")
def get_sectors():
    """Return sector information for all N100 companies."""

    try:
        sectors = pd.read_excel(
            SECTORS_FILE,
            header=0,
        )

        ratios = pd.read_csv(
            RATIOS_FILE,
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
            .groupby("company_id", as_index=False)
            .tail(1)
        )

        df = sectors.merge(
            latest_ratios[
                [
                    "company_id",
                    "return_on_equity_pct",
                    "debt_to_equity",
                    "pe_ratio",
                ]
            ],
            on="company_id",
            how="left",
        )

        result = (
            df.groupby("broad_sector")
            .agg(
                company_count=("company_id", "nunique"),
                median_roe=(
                    "return_on_equity_pct",
                    "median",
                ),
                median_pe=(
                    "pe_ratio",
                    "median",
                ),
                median_de=(
                    "debt_to_equity",
                    "median",
                ),
            )
            .reset_index()
        )

        records = json.loads(
            result
            .where(pd.notna(result), None)
            .to_json(orient="records")
        )

        return {
            "count": len(records),
            "sectors": records,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load sector data: {exc}",
        )


@router.get("/{sector}/companies")
def get_sector_companies(sector: str):
    """Return companies belonging to a specific sector."""

    try:
        sectors = pd.read_excel(
            SECTORS_FILE,
            header=0,
        )

        ratios = pd.read_csv(
            RATIOS_FILE,
        )

        sector_name = sector.strip()

        sector_data = sectors[
            sectors["broad_sector"]
            .astype(str)
            .str.strip()
            .str.lower()
            == sector_name.lower()
        ].copy()

        if sector_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Sector '{sector}' not found",
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
            .groupby("company_id", as_index=False)
            .tail(1)
        )

        df = sector_data.merge(
            latest_ratios,
            on="company_id",
            how="left",
        )

        columns = [
            "company_id",
            "broad_sector",
            "sub_sector",
            "index_weight_pct",
            "market_cap_category",
            "return_on_equity_pct",
            "debt_to_equity",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "free_cash_flow_cr",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "market_cap_crore",
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
            "sector": sector_name,
            "count": len(records),
            "companies": records,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load companies for sector: {exc}",
        )