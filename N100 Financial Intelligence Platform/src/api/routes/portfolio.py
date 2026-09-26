import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


ROOT = Path(__file__).resolve().parents[3]

CLUSTER_FILE = (
    ROOT
    / "output"
    / "cluster_labels.csv"
)

PORTFOLIO_STATS_FILE = (
    ROOT
    / "output"
    / "portfolio_stats.csv"
)


@router.get("/stats")
def get_portfolio_stats():
    """Return portfolio-level feature statistics."""

    try:
        df = pd.read_csv(
            PORTFOLIO_STATS_FILE
        )

        records = json.loads(
            df.where(
                pd.notna(df),
                None,
            ).to_json(
                orient="records"
            )
        )

        return {
            "count": len(records),
            "statistics": records,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load portfolio statistics: "
                f"{exc}"
            ),
        )


@router.get("/clusters")
def get_portfolio_clusters():
    """Return N100 companies with their cluster assignments."""

    try:
        df = pd.read_csv(
            CLUSTER_FILE
        )

        records = json.loads(
            df.where(
                pd.notna(df),
                None,
            ).to_json(
                orient="records"
            )
        )

        return {
            "count": len(records),
            "clusters": records,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load cluster data: "
                f"{exc}"
            ),
        )