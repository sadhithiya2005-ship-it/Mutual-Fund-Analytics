"""
Load engineered financial ratios into SQLite.
"""

from pathlib import Path
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
DATABASE_DIR = ROOT / "data" / "database"
DATABASE_FILE = DATABASE_DIR / "n100_financial_intelligence.db"


def main():
    """Load financial ratio data into SQLite."""

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    connection = sqlite3.connect(DATABASE_FILE)

    df.to_sql(
        "financial_ratios",
        connection,
        if_exists="replace",
        index=False,
    )

    row_count = pd.read_sql_query(
        "SELECT COUNT(*) AS count FROM financial_ratios",
        connection,
    ).iloc[0]["count"]

    connection.close()

    print("SQLITE LOAD COMPLETED")
    print(f"Rows loaded: {row_count}")
    print(f"Database: {DATABASE_FILE}")


if __name__ == "__main__":
    main()