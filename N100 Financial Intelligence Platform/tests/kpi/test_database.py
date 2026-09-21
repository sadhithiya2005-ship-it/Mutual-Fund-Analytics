import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DATABASE_FILE = (
    ROOT
    / "data"
    / "database"
    / "n100_financial_intelligence.db"
)


def test_financial_ratios_table_exists():
    con = sqlite3.connect(DATABASE_FILE)

    result = con.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'financial_ratios'
        """
    ).fetchone()

    con.close()

    assert result is not None


def test_financial_ratios_row_count():
    con = sqlite3.connect(DATABASE_FILE)

    count = con.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    con.close()

    assert count >= 1100


def test_financial_ratios_company_count():
    con = sqlite3.connect(DATABASE_FILE)

    count = con.execute(
        "SELECT COUNT(DISTINCT company_id) FROM financial_ratios"
    ).fetchone()[0]

    con.close()

    assert count == 92