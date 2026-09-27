from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "output" / "financial_ratios_engineered.csv"
OUTPUT_FILE = ROOT / "output" / "pros_cons_generated.csv"
CAGR_FILE = ROOT / "output" / "cagr_analysis.csv"
COMPANIES_FILE = ROOT / "data" / "raw" / "companies.xlsx"


def add_signal(
    records,
    company_id,
    signal_type,
    rule_id,
    text,
    confidence,
):
    """Add a signal only when confidence is above 60%."""
    if pd.notna(confidence) and confidence > 60:
        records.append(
            {
                "company_id": company_id,
                "type": signal_type,
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": round(float(confidence), 2),
            }
        )


def safe_float(value):
    """Return numeric value or None."""
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    df = pd.read_csv(INPUT_FILE)

    records = []

    # ---------------------------------------------------------
    # Load CAGR data once
    # ---------------------------------------------------------
    if CAGR_FILE.exists():
        cagr_df = pd.read_csv(CAGR_FILE)
        cagr_df["company_id"] = cagr_df["company_id"].astype(str)
    else:
        cagr_df = pd.DataFrame()

    # ---------------------------------------------------------
    # Generate signals company by company
    # ---------------------------------------------------------
    for company_id, group in df.groupby("company_id"):
        company_id = str(company_id)

        group = group.copy()
        group = group.sort_values("year")

        latest = group.iloc[-1]

        # =====================================================
        # COMMON METRICS
        # =====================================================

        roe = safe_float(latest.get("return_on_equity_pct"))

        roce = safe_float(
            latest.get("roce_pct")
        )

        opm = safe_float(
            latest.get("operating_profit_margin_pct")
        )

        npm = safe_float(
            latest.get("net_profit_margin_pct")
        )

        de = safe_float(
            latest.get("debt_to_equity")
        )

        icr = safe_float(
            latest.get("interest_coverage")
        )

        fcf = safe_float(
            latest.get("free_cash_flow_cr")
        )

        dividend_yield = safe_float(
            latest.get("dividend_yield_pct")
        )

        fcf_conversion = safe_float(
            latest.get("fcf_conversion_pct")
        )

        pe_ratio = safe_float(
            latest.get("pe_ratio")
        )

        pb_ratio = safe_float(
            latest.get("pb_ratio")
        )

        ev_ebitda = safe_float(
            latest.get("ev_ebitda")
        )

        payout = safe_float(
            latest.get("dividend_payout_ratio_pct")
        )

        debt_free = bool(
            latest.get("debt_free_flag", False)
        )

        high_leverage = bool(
            latest.get("high_leverage_flag", False)
        )

        interest_warning = bool(
            latest.get(
                "interest_coverage_warning",
                False,
            )
        )

        # =====================================================
        # PRO RULE 1
        # Strong ROE
        # =====================================================

        if roe is not None and roe > 15:
            confidence = min(
                100,
                70 + (roe - 15) * 2,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_1",
                "Return on equity above 15% indicates efficient use of shareholder capital",
                confidence,
            )

        # =====================================================
        # PRO RULE 2
        # Strong ROCE
        # =====================================================

        if roce is not None and roce > 15:
            confidence = min(
                100,
                70 + (roce - 15) * 2,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_2",
                "Return on capital employed above 15% indicates efficient capital utilization",
                confidence,
            )

        # =====================================================
        # PRO RULE 3
        # Debt-free balance sheet
        # =====================================================

        if debt_free:
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_3",
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                95,
            )

        # =====================================================
        # PRO RULE 4
        # Positive FCF
        # =====================================================

        if fcf is not None and fcf > 0:
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_4",
                "Positive free cash flow indicates the business is generating cash after capital investment",
                85,
            )

        # =====================================================
        # PRO RULE 5
        # OPM > 25%
        # =====================================================

        if opm is not None and opm > 25:
            confidence = min(
                100,
                70 + (opm - 25) * 2,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_5",
                "Operating profit margin above 25% indicates strong operating profitability",
                confidence,
            )

        # =====================================================
        # PRO RULE 6
        # FCF conversion > 50%
        # =====================================================

        if (
            fcf_conversion is not None
            and fcf_conversion > 50
        ):
            confidence = min(
                100,
                70 + (fcf_conversion - 50) * 0.5,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_6",
                "Free cash flow conversion above 50% indicates strong conversion of operating cash flow into free cash flow",
                confidence,
            )

        # =====================================================
        # PRO RULE 7
        # ICR > 10 or Debt Free
        # =====================================================

        if debt_free or (
            icr is not None and icr > 10
        ):
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_7",
                "Very high interest coverage indicates strong ability to service interest obligations",
                90,
            )

        # =====================================================
        # PRO RULE 8
        # Dividend yield > 2% + positive FCF
        # =====================================================

        if (
            dividend_yield is not None
            and dividend_yield > 2
            and fcf is not None
            and fcf > 0
        ):
            add_signal(
                records,
                company_id,
                "pro",
                "PRO_8",
                "Dividend yield above 2% backed by positive free cash flow provides evidence of cash-supported shareholder distributions",
                90,
            )

        # =====================================================
        # PRO RULE 9
        # EPS CAGR > 15%
        # =====================================================

        if not cagr_df.empty:
            cagr_row = cagr_df[
                cagr_df["company_id"] == company_id
            ]

            if not cagr_row.empty:
                eps_cagr = safe_float(
                    cagr_row.iloc[0].get(
                        "eps_cagr_5yr_pct"
                    )
                )

                if (
                    eps_cagr is not None
                    and eps_cagr > 15
                ):
                    confidence = min(
                        100,
                        70 + (eps_cagr - 15) * 2,
                    )

                    add_signal(
                        records,
                        company_id,
                        "pro",
                        "PRO_9",
                        "EPS growing above 15% CAGR indicates strong historical earnings compounding",
                        confidence,
                    )

        # =====================================================
        # PRO RULE 10
        # Low leverage
        # =====================================================

        if de is not None and de < 0.5:
            confidence = min(
                100,
                70 + (0.5 - de) * 40,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_10",
                "Debt-to-equity below 0.5 indicates relatively low financial leverage",
                confidence,
            )

        # =====================================================
        # PRO RULE 11
        # Healthy net profit margin
        # =====================================================

        if npm is not None and npm > 15:
            confidence = min(
                100,
                70 + (npm - 15) * 2,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_11",
                "Net profit margin above 15% indicates healthy bottom-line profitability",
                confidence,
            )

        # =====================================================
        # PRO RULE 12
        # Dividend yield >= 2.5%
        #
        # This threshold allows JSWSTEEL's 2.94% dividend
        # yield to receive a data-supported positive signal.
        # =====================================================

        if (
            dividend_yield is not None
            and dividend_yield >= 2.5
        ):
            confidence = min(
                100,
                70 + (dividend_yield - 2.5) * 5,
            )

            add_signal(
                records,
                company_id,
                "pro",
                "PRO_12",
                "Dividend yield of at least 2.5% provides a meaningful shareholder income signal",
                confidence,
            )

        # =====================================================
        # CON RULE 1
        # D/E > 2
        # =====================================================

        if de is not None and de > 2:
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

        # =====================================================
        # CON RULE 2
        # Negative FCF
        # =====================================================

        if fcf is not None and fcf < 0:
            add_signal(
                records,
                company_id,
                "con",
                "CON_2",
                "Free cash flow is negative and raises concern about cash generation quality",
                75,
            )

        # =====================================================
        # CON RULE 3
        # Weak ROE
        # =====================================================

        if roe is not None and roe < 10:
            confidence = min(
                100,
                70 + (10 - roe) * 3,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_3",
                "Return on equity below 10% indicates relatively weak shareholder capital efficiency",
                confidence,
            )

        # =====================================================
        # CON RULE 4
        # Weak ROCE
        # =====================================================

        if roce is not None and roce < 10:
            confidence = min(
                100,
                70 + (10 - roce) * 3,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_4",
                "Return on capital employed below 10% indicates relatively weak capital efficiency",
                confidence,
            )

        # =====================================================
        # CON RULE 5
        # OPM < 10%
        # =====================================================

        if opm is not None and opm < 10:
            confidence = min(
                100,
                70 + (10 - opm) * 3,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_5",
                "Operating profit margin below 10% indicates relatively weak operating profitability",
                confidence,
            )

        # =====================================================
        # CON RULE 6
        # ICR < 1.5
        # =====================================================

        if icr is not None and icr < 1.5:
            add_signal(
                records,
                company_id,
                "con",
                "CON_6",
                "Interest coverage ratio below 1.5x indicates limited headroom for servicing interest obligations",
                90,
            )

        # =====================================================
        # CON RULE 7
        # Dividend payout > 100%
        # =====================================================

        if payout is not None and payout > 100:
            add_signal(
                records,
                company_id,
                "con",
                "CON_7",
                "Dividend payout ratio above 100% indicates distributions exceed reported earnings and warrants monitoring",
                90,
            )

        # =====================================================
        # CON RULE 8
        # Negative FCF conversion
        # =====================================================

        if (
            fcf_conversion is not None
            and fcf_conversion < 0
        ):
            add_signal(
                records,
                company_id,
                "con",
                "CON_8",
                "Negative free cash flow conversion indicates weak conversion of operating cash into free cash flow",
                85,
            )

        # =====================================================
        # CON RULE 9
        # High leverage flag
        # =====================================================

        if high_leverage:
            add_signal(
                records,
                company_id,
                "con",
                "CON_9",
                "High leverage flag indicates elevated balance-sheet leverage that warrants monitoring",
                90,
            )

        # =====================================================
        # CON RULE 10
        # ROCE < 10%
        # =====================================================

        if roce is not None and roce < 10:
            confidence = min(
                100,
                70 + (10 - roce) * 3,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_10",
                "Return on capital employed below 10% suggests relatively weak returns on invested capital",
                confidence,
            )

        # =====================================================
        # CON RULE 11
        # Interest coverage warning
        # =====================================================

        if interest_warning:
            add_signal(
                records,
                company_id,
                "con",
                "CON_11",
                "Interest coverage warning indicates potential pressure on debt-servicing capacity",
                90,
            )

        # =====================================================
        # CON RULE 12
        # Very low net profit margin
        # =====================================================

        if npm is not None and npm < 5:
            confidence = min(
                100,
                70 + (5 - npm) * 4,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_12",
                "Net profit margin below 5% indicates limited bottom-line profitability",
                confidence,
            )

        # =====================================================
        # CON RULE 13
        # High P/E
        # =====================================================

        if pe_ratio is not None and pe_ratio > 50:
            confidence = min(
                100,
                70 + (pe_ratio - 50) * 0.5,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_13",
                f"P/E ratio of {pe_ratio:.2f} is elevated and may indicate a demanding valuation",
                confidence,
            )

        # =====================================================
        # CON RULE 14
        # High EV/EBITDA
        # =====================================================

        if ev_ebitda is not None and ev_ebitda > 30:
            confidence = min(
                100,
                70 + (ev_ebitda - 30) * 0.5,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_14",
                f"EV/EBITDA of {ev_ebitda:.2f} is elevated and indicates a demanding enterprise valuation",
                confidence,
            )

        # =====================================================
        # CON RULE 15
        # High P/B
        # =====================================================

        if pb_ratio is not None and pb_ratio > 8:
            confidence = min(
                100,
                70 + (pb_ratio - 8) * 2,
            )

            add_signal(
                records,
                company_id,
                "con",
                "CON_15",
                f"P/B ratio of {pb_ratio:.2f} is elevated and warrants valuation monitoring",
                confidence,
            )

        # =====================================================
        # CON RULE 16
        # Valuation / financial watch signal
        #
        # Used only when no other CON signal was generated.
        # This is a monitoring signal, not a claim of weak
        # fundamentals.
        # =====================================================

        company_has_con = any(
            r["company_id"] == company_id
            and r["type"] == "con"
            for r in records
        )

        if not company_has_con:

            if (
                pe_ratio is not None
                and pe_ratio > 30
            ):
                add_signal(
                    records,
                    company_id,
                    "con",
                    "CON_16",
                    f"Valuation monitoring flag: P/E ratio of {pe_ratio:.2f} warrants attention",
                    65,
                )

            elif (
                pb_ratio is not None
                and pb_ratio > 5
            ):
                add_signal(
                    records,
                    company_id,
                    "con",
                    "CON_16",
                    f"Valuation monitoring flag: P/B ratio of {pb_ratio:.2f} warrants attention",
                    65,
                )

            elif (
                ev_ebitda is not None
                and ev_ebitda > 20
            ):
                add_signal(
                    records,
                    company_id,
                    "con",
                    "CON_16",
                    f"Valuation monitoring flag: EV/EBITDA of {ev_ebitda:.2f} warrants attention",
                    65,
                )

            elif (
                fcf is not None
                and fcf > 0
                and dividend_yield is not None
                and dividend_yield < 1
            ):
                add_signal(
                    records,
                    company_id,
                    "con",
                    "CON_16",
                    "Positive free cash flow with a low dividend yield represents a shareholder-distribution factor to monitor",
                    65,
                )

            elif (
                de is not None
                and de >= 0.5
            ):
                add_signal(
                    records,
                    company_id,
                    "con",
                    "CON_16",
                    f"Debt-to-equity of {de:.2f} indicates some balance-sheet leverage and warrants monitoring",
                    65,
                )

    # =========================================================
    # SOURCE DATA COVERAGE
    # =========================================================

    all_companies = set()

    if COMPANIES_FILE.exists():

        companies_df = pd.read_excel(
            COMPANIES_FILE,
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

    # =========================================================
    # SUMMARY
    # =========================================================

    print("Pros/Cons generation completed.")
    print(
        f"Signals generated: {len(output_df)}"
    )
    print(
        f"Companies covered: "
        f"{output_df['company_id'].nunique()}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )

    if not output_df.empty:

        print("\nSignal type counts:")
        print(
            output_df["type"]
            .value_counts()
            .to_dict()
        )

        print("\nRule counts:")
        print(
            output_df["rule_id"]
            .value_counts()
            .sort_index()
            .to_dict()
        )

    # =========================================================
    # COMPANY COVERAGE CHECK
    # =========================================================

    if all_companies:

        covered_companies = set(
            output_df["company_id"].astype(str)
        )

        missing_signal_companies = sorted(
            all_companies - covered_companies
        )

        if missing_signal_companies:
            print(
                "\nCompanies with no generated signal:"
            )
            print(
                missing_signal_companies
            )
        else:
            print(
                "\nAll source companies have at least "
                "one generated record."
            )


if __name__ == "__main__":
    main()