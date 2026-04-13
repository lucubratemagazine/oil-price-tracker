import pandas as pd

df = pd.read_csv("history.csv")

# Konverter til numerisk
df["eia_price"] = pd.to_numeric(df["eia_price"], errors="coerce")
df["yahoo_price"] = pd.to_numeric(df["yahoo_price"], errors="coerce")

# Fjern rader der både EIA og Yahoo er NaN
df = df.dropna(subset=["eia_price", "yahoo_price"], how="all")

# Sorter på dato for sikkerhets skyld
df = df.sort_values("date")

df.to_csv("history.csv", index=False)
print("Cleaned history.csv, rows left:", len(df))
