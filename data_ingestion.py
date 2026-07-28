import pandas as pd
import os

# Folder containing the CSV files
DATA_FOLDER = "data/raw"

# Get all CSV files
csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

print("=" * 60)
print("Mutual Fund Analytics - Data Ingestion")
print("=" * 60)

for file in csv_files:
    print(f"\nReading: {file}")

    path = os.path.join(DATA_FOLDER, file)

    df = pd.read_csv(path)

    print("\nShape:")
    print(df.shape)

    print("\nData Types:")
    print(df.dtypes)

    print("\nFirst 5 Rows:")
    print(df.head())

    print("\nMissing Values:")
    print(df.isnull().sum())

    print("\nDuplicate Rows:")
    print(df.duplicated().sum())

    print("-" * 60)

print("\nAll datasets loaded successfully.")