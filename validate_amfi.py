import pandas as pd

# Load datasets
fund_master = pd.read_csv("data/raw/01_fund_master.csv")
nav_history = pd.read_csv("data/raw/02_nav_history.csv")

print("=" * 60)
print("AMFI CODE VALIDATION")
print("=" * 60)

print("\nColumns in NAV History:")
print(nav_history.columns.tolist())

# Check if amfi_code exists
if "amfi_code" in nav_history.columns:
    fund_codes = set(fund_master["amfi_code"])
    nav_codes = set(nav_history["amfi_code"])

    missing_codes = fund_codes - nav_codes

    print("\nTotal AMFI Codes in Fund Master:", len(fund_codes))
    print("Total AMFI Codes in NAV History:", len(nav_codes))

    if len(missing_codes) == 0:
        print("\n✅ All AMFI codes are present in NAV History.")
    else:
        print("\n❌ Missing AMFI Codes:")
        print(sorted(missing_codes))

else:
    print("\n❌ 'amfi_code' column not found in NAV History.")