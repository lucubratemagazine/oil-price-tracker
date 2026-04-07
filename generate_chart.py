import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import os

def log(msg):
    print(f"[INFO] {msg}")

def load_csv(filename="history.csv"):
    if not os.path.isfile(filename):
        log("CSV file not found — cannot generate chart.")
        return None

    try:
        df = pd.read_csv(filename)
        log(f"Loaded CSV with {len(df)} rows.")
        return df
    except Exception as e:
        log(f"Failed to read CSV: {e}")
        return None

def clean_dataframe(df):
    required_cols = {"date", "eia_price", "yahoo_price"}

    if not required_cols.issubset(df.columns):
        log("CSV missing required columns — cannot generate chart.")
        return None

    # Convert numeric columns
    df["eia_price"] = pd.to_numeric(df["eia_price"], errors="coerce")
    df["yahoo_price"] = pd.to_numeric(df["yahoo_price"], errors="coerce")

    # Convert date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["date"])

    # Sort by date
    df = df.sort_values("date")

    log(f"Cleaned dataframe: {len(df)} valid rows.")
    return df

def generate_chart(df, output="chart.png"):
    log("Generating Plotly chart...")

    fig = go.Figure()

    # EIA line
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["eia_price"],
        mode="lines+markers",
        name="EIA (official)",
        line=dict(color="#4da3ff", width=3)
    ))

    # Yahoo line
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["yahoo_price"],
        mode="lines+markers",
        name="Yahoo Finance (real-time)",
        line=dict(color="#ff9933", width=3)
    ))

    fig.update_layout(
        title="Oil Price History",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        height=500,
        margin=dict(l=40, r=20, t=40, b=40)
    )

    # Save as PNG
    try:
        pio.write_image(fig, output, width=1000, height=500)
        log(f"Chart saved as {output}")
    except Exception as e:
        log(f"Failed to save chart: {e}")

if __name__ == "__main__":
    df = load_csv()

    if df is None:
        log("Aborting chart generation.")
        exit(1)

    df = clean_dataframe(df)

    if df is None or df.empty:
        log("No valid data — chart not generated.")
        exit(1)

    generate_chart(df)
