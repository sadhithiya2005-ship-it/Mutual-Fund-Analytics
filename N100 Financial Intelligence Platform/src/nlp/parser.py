import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

ANALYSIS_FILE = ROOT / "data" / "raw" / "analysis.xlsx"
OUTPUT_DIR = ROOT / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_FILE = OUTPUT_DIR / "parse_failures.csv"


PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%"
)


TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


def parse_metric(value):
    """Extract period and percentage from analysis text."""
    if pd.isna(value):
        return None

    match = PATTERN.search(str(value))

    if not match:
        return None

    return int(match.group(1)), float(match.group(2))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(ANALYSIS_FILE, header=1)
    

    parsed_records = []
    failures = []

    for _, row in df.iterrows():
        company_id = row.get("company_id")

        for metric in TARGET_FIELDS:
            value = row.get(metric)

            if pd.isna(value):
                continue

            parsed = parse_metric(value)

            if parsed:
                period_years, value_pct = parsed

                parsed_records.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "period_years": period_years,
                        "value_pct": value_pct,
                    }
                )
            else:
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "raw_value": value,
                    }
                )

    parsed_df = pd.DataFrame(
        parsed_records,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failures,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
        ],
    )

    parsed_df.to_csv(PARSED_FILE, index=False)
    failures_df.to_csv(FAILURES_FILE, index=False)

    print("Analysis parsing completed.")
    print(f"Parsed records: {len(parsed_df)}")
    print(f"Parse failures: {len(failures_df)}")
    print(f"Output: {PARSED_FILE}")
    print(f"Failures: {FAILURES_FILE}")


if __name__ == "__main__":
    main()
