import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
df = pd.read_csv("history.csv")

# Convert date column to datetime
df["date"] = pd.to_datetime(df["date"])

# Create the plot
plt.figure(figsize=(10, 5))
plt.plot(df["date"], df["price"], marker="o", linestyle="-", color="blue")
plt.title("Oil Price Over Time")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.grid(True)

# Save the chart
plt.tight_layout()
plt.savefig("chart.png")
