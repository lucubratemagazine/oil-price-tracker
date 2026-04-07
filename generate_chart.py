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
    # -----------------------------------------
    # Detect 5/10/15% changes in last 30 days
    # -----------------------------------------
    log("Calculating percentage change alerts...")

    # Use Yahoo price if available, else EIA
    df["price"] = df["yahoo_price"].fillna(df["eia_price"])

    # Filter last 30 days
    last_30 = df[df["date"] >= (df["date"].max() - pd.Timedelta(days=30))]

    if len(last_30) > 1:
        start_price = last_30["price"].iloc[0]

        # Calculate percent change
        last_30["pct_change"] = (last_30["price"] - start_price) / start_price * 100

        # Thresholds: ±5%, ±10%, ±15%, ...
        thresholds = []
        for pct in range(5, 101, 5):
            thresholds.append(pct)
            thresholds.append(-pct)

        # Find crossings
        alerts = []
        for t in thresholds:
            crossed = last_30[last_30["pct_change"] >= t] if t > 0 else last_30[last_30["pct_change"] <= t]
            if not crossed.empty:
                row = crossed.iloc[0]
                alerts.append((row["date"], row["price"], t))

        # Add markers to chart
        for date, price, pct in alerts:
            fig.add_trace(go.Scatter(
                x=[date],
                y=[price],
                mode="markers+text",
                text=[f"{pct:+.0f}%"],
                textposition="top center",
                marker=dict(size=12, color="red" if pct < 0 else "green"),
                name=f"{pct:+.0f}% alert"
            ))

        log(f"Added {len(alerts)} percentage-change alerts.")
    else:
        log("Not enough data for 30-day analysis.")
 
  #   Save as PNG

    try:
        pio.write_image(fig, output, width=1000, height=500)
        log(f"Chart saved as {output}")
    except Exception as e:
        log(f"Failed to save chart: {e}")

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
