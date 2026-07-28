import requests
import pandas as pd
import os

# Folder to save NAV files
SAVE_FOLDER = "data/raw"

# AMFI Scheme Codes
schemes = {
    "HDFC_Top_100_Direct": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841
}

# Create folder if it doesn't exist
os.makedirs(SAVE_FOLDER, exist_ok=True)

for scheme_name, scheme_code in schemes.items():
    url = f"https://api.mfapi.in/mf/{scheme_code}"

    print(f"\nFetching {scheme_name}...")

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        nav_data = pd.DataFrame(data["data"])

        file_name = f"{scheme_name}.csv"
        file_path = os.path.join(SAVE_FOLDER, file_name)

        nav_data.to_csv(file_path, index=False)

        print(f"Saved: {file_name}")

    else:
        print(f"Failed to fetch {scheme_name}")