import pandas as pd

df = pd.read_csv("C:/Users/ACER/OneDrive/Desktop/mutual_fund_analytics/data/processed/scheme_performance_cleaned.csv")

print(df.columns.tolist())
print(df.shape)