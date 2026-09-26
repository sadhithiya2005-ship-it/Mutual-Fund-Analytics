import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/peers",
    tags=["Peers"],
)


ROOT = Path(__file__).resolve().parents[3]

PEER_GROUPS_FILE = ROOT / "data" / "raw" / "peer_groups.xlsx"
RATIOS_FILE = ROOT / "output" / "financial_ratios_engineered.csv"


@router.get("/{group_name}")
def get_peer_group(group_name: str):
    """Return companies in a peer group with percentile ranks."""

    try:
        peer_groups = pd.read_excel(
            PEER_GROUPS_FILE,
            header=0,
        )

        ratios = pd.read_csv(
            RATIOS_FILE,
        )

        required_peer_columns = [
            "peer_group_name",
            "company_id",
            "is_benchmark",
        ]

        missing_peer_columns = [
            column
            for column in required_peer_columns
            if column not in peer_groups.columns
        ]

        if missing_peer_columns:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Missing peer group columns: "
                    f"{missing_peer_columns}"
                ),
            )

        peer_groups["peer_group_name"] = (
            peer_groups["peer_group_name"]
            .astype(str)
            .str.strip()
        )

        peer_groups["company_id"] = (
            peer_groups["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        group_name_clean = group_name.strip()

        group_data = peer_groups[
            peer_groups["peer_group_name"]
            .str.lower()
            == group_name_clean.lower()
        ].copy()

        if group_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Peer group '{group_name}' not found",
            )

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

        metrics = [
            "return_on_equity_pct",
            "debt_to_equity",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "free_cash_flow_cr",
            "asset_turnover",
            "interest_coverage",
            "earnings_per_share",
            "pe_ratio",
            "pb_ratio",
        ]

        available_metrics = [
            metric
            for metric in metrics
            if metric in latest_ratios.columns
        ]

        peer_data = group_data.merge(
            latest_ratios,
            on="company_id",
            how="left",
        )

        for metric in available_metrics:
            peer_data[metric] = pd.to_numeric(
                peer_data[metric],
                errors="coerce",
            )

            peer_data[
                f"{metric}_percentile"
            ] = peer_data[metric].rank(
                pct=True,
                method="average",
            ) * 100

        output_columns = [
            "company_id",
            "peer_group_name",
            "is_benchmark",
        ]

        for metric in available_metrics:
            output_columns.append(metric)
            output_columns.append(
                f"{metric}_percentile"
            )

        output_columns = [
            column
            for column in output_columns
            if column in peer_data.columns
        ]

        result = peer_data[output_columns].copy()

        result = result.replace(
            {
                float("inf"): None,
                float("-inf"): None,
            }
        )

        records = json.loads(
            result
            .where(
                pd.notna(result),
                None,
            )
            .to_json(
                orient="records"
            )
        )

        benchmark_rows = group_data[
            group_data["is_benchmark"]
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

        if not benchmark_rows.empty:
            benchmark_company = (
                benchmark_rows.iloc[0]["company_id"]
            )

        return {
            "peer_group_name": group_name_clean,
            "count": len(records),
            "benchmark_company": benchmark_company,
            "metrics": available_metrics,
            "peers": records,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load peer group data: {exc}",
        )