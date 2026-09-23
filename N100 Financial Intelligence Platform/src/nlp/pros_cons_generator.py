from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
OUTPUT_FILE = ROOT / "output" / "pros_cons_generated.csv"


def add_signal(records, company_id, signal_type, rule_id, text, confidence):
    """Add a signal only when confidence is above 60%."""
    if confidence > 60:
        records.append(
            {
                "company_id": company_id,
                "type": signal_type,
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": round(confidence, 2),
            }
        )


def main():
    df = pd.read_csv(INPUT_FILE)

    records = []

    for company_id, group in df.groupby("company_id"):
        group = group.sort_values("year")
        latest = group.iloc[-1]

        # -------------------------
        # PRO RULE 3
        # Debt-free balance sheet
        # -------------------------
        if latest["debt_free_flag"]:
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_3",
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                95,
            )

        # -------------------------
        # PRO RULE 5
        # OPM > 25%
        # -------------------------
        opm = latest["operating_profit_margin_pct"]

        if pd.notna(opm) and opm > 25:
            confidence = min(100, 70 + (opm - 25) * 2)

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_5",
                "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                confidence,
            )

        # -------------------------
        # PRO RULE 7
        # ICR > 10 or Debt Free
        # -------------------------
        icr = latest["interest_coverage"]

        if latest["debt_free_flag"] or (
            pd.notna(icr) and icr > 10
        ):
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_7",
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                90,
            )

        # -------------------------
        # PRO RULE 8
        # Dividend yield > 2% + positive FCF
        # -------------------------
        dividend_yield = latest["dividend_yield_pct"]
        fcf = latest["free_cash_flow_cr"]

        if (
            pd.notna(dividend_yield)
            and dividend_yield > 2
            and pd.notna(fcf)
            and fcf > 0
        ):
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_8",
                "Consistent dividend yield above 2% backed by positive free cash flow",
                90,
            )

        # -------------------------
        # PRO RULE 9
        # EPS CAGR > 15%
        #
        # Uses the existing 5-year CAGR output
        # where available.
        # -------------------------
        cagr_file = ROOT / "output" / "cagr_analysis.csv"

        if cagr_file.exists():
            cagr_df = pd.read_csv(cagr_file)

            cagr_row = cagr_df[
                cagr_df["company_id"].astype(str) == str(company_id)
            ]

            if not cagr_row.empty:
                eps_cagr = cagr_row.iloc[0]["eps_cagr_5yr_pct"]

                if pd.notna(eps_cagr) and eps_cagr > 15:
                    confidence = min(
                        100,
                        70 + (eps_cagr - 15) * 2,
                    )

                    add_signal(
                        records,
                        company_id,
                        "pro",
                        "PRO_9",
                        "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                        confidence,
                    )

        # -------------------------
        # CON RULE 1
        # D/E > 2
        # -------------------------
        de = latest["debt_to_equity"]

        if pd.notna(de) and de > 2:
            confidence = min(
                100,
                70 + (de - 2) * 10,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_1",
                f"Debt-to-equity ratio of {de:.2f} is elevated and warrants monitoring",
                confidence,
            )

        # -------------------------
        # CON RULE 6
        # ICR < 1.5
        # -------------------------
        if pd.notna(icr) and icr < 1.5:
            add_signal(
                records,
                company_id,
                "con",
                "CON_6",
                "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                90,
            )

        # -------------------------
        # CON RULE 7
        # Dividend payout > 100%
        # -------------------------
        payout = latest["dividend_payout_ratio_pct"]

        if pd.notna(payout) and payout > 100:
            add_signal(
                records,
                company_id,
                "con",
                "CON_7",
                "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                90,
            )

        # -------------------------
        # CON RULE 10
        # ROCE < 10%
        # -------------------------
        roce = latest["roce_pct"]

        if pd.notna(roce) and roce < 10:
            confidence = min(
                100,
                70 + (10 - roce) * 3,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_10",
                "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                confidence,
            )

        # -------------------------
        # CON RULE 2
        # Negative FCF
        # -------------------------
        if pd.notna(fcf) and fcf < 0:
            add_signal(
                records,
                company_id,
                "con",
                "CON_2",
                "Free cash flow is negative and raises concern about cash generation quality",
                75,
            )

    # =========================================================
    # SOURCE DATA COVERAGE
    # =========================================================
    # Compare the 92 companies in companies.xlsx against the
    # companies available in financial_ratios_engineered.csv.
    #
    # ATGL and SBIN are currently missing from the financial
    # ratio source. We record them transparently instead of
    # generating unsupported pros/cons.
    # =========================================================

    companies_file = ROOT / "data" / "raw" / "companies.xlsx"

    if companies_file.exists():
        companies_df = pd.read_excel(
            companies_file,
            header=1,
        )

        source_companies = set(
            df["company_id"].astype(str)
        )

        all_companies = set(
            companies_df["id"].astype(str)
        )

        missing_companies = sorted(
            all_companies - source_companies
        )

        for missing_id in missing_companies:
            records.append(
                {
                    "company_id": missing_id,
                    "type": "data_unavailable",
                    "rule_id": "SOURCE_MISSING",
                    "text": (
                        "Financial ratio source data is unavailable; "
                        "no unsupported pros/cons were generated"
                    ),
                    "confidence_pct": None,
                }
            )

    # =========================================================
    # CREATE FINAL OUTPUT
    # =========================================================

    output_df = pd.DataFrame(
        records,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("Pros/Cons generation completed.")
    print(f"Signals generated: {len(output_df)}")
    print(f"Companies covered: {output_df['company_id'].nunique()}")
    print(f"Output: {OUTPUT_FILE}")

    # Show companies for which source data is unavailable.
    missing_rows = output_df[
        output_df["type"] == "data_unavailable"
    ]

    if not missing_rows.empty:
        print(
            "Companies without financial-ratio source data:"
        )
        print(
            missing_rows["company_id"]
            .tolist()
        )


if __name__ == "__main__":
    main()