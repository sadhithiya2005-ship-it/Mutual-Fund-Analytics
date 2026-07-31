import pandas as pd
df=pd.read_csv("C:/Users/ACER/OneDrive/Desktop/mutual_fund_analytics/data/raw/07_scheme_performance.csv")
# Find invalid expense ratios

print(df.head())
print(df.shape)
print(df.info())
print(df.dtypes)
print(df.isnull().sum())
invalid_expense = df[
    (df["expense_ratio_pct"] < 0.1) |
    (df["expense_ratio_pct"] > 2.5)
]

print("Invalid Expense Ratio Records:", len(invalid_expense))
print(df.columns)
print("Duplicate Rows:", df.duplicated().sum())
# Save cleaned dataset
df.to_csv(
    "C:/Users/ACER/OneDrive/Desktop/mutual_fund_analytics/data/processed/scheme_performance_cleaned.csv",
    index=False
)

print("✅ Cleaned scheme_performance dataset saved successfully!")