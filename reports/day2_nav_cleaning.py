import pandas as pd

# Read dataset
df = pd.read_csv(
    "C:/Users/ACER/OneDrive/Desktop/mutual_fund_analytics/data/raw/02_nav_history.csv"
)

# Convert date column
df["date"] = pd.to_datetime(df["date"])

# Sort values
df = df.sort_values(["amfi_code", "date"])

# Forward fill missing NAV
df["nav"] = df.groupby("amfi_code")["nav"].ffill()

# Check invalid NAV
invalid_nav = df[df["nav"] <= 0]
print("Invalid NAV Records:", len(invalid_nav))

# Check duplicates
print("Duplicate Rows Before:", df.duplicated().sum())

# Remove duplicates
df = df.drop_duplicates()

print("Duplicate Rows After:", df.duplicated().sum())

# Dataset overview
print(df.head())
print(df.tail())
print(df.shape)
print(df.info())
print(df.dtypes)
print(df.isnull().sum())

# Save cleaned dataset
df.to_csv(
    "C:/Users/ACER/OneDrive/Desktop/mutual_fund_analytics/data/processed/nav_history_cleaned.csv",
    index=False
)

print("✅ Cleaned dataset saved successfully!")