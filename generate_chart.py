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

    df["eia_price"] = pd.to_numeric(df["eia_price"], errors="coerce")
    df["yahoo_price"] = pd.to_numeric(df["yahoo_price"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.dropna(subset=["date"])
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

    # Legend at top (Option A)
    fig.update_layout(
        title="Oil Price History",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        height=500,
        margin=dict(l=40, r=20, t=80, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="left",
            x=0
        )
    )

    # -----------------------------------------
    # 30-day change
    # -----------------------------------------
    log("Calculating 30-day change...")

    df["price"] = df["yahoo_price"].fillna(df["eia_price"])
    last_30 = df[df["date"] >= (df["date"].max() - pd.Timedelta(days=30))]

    if len(last_30) > 1:
        start_price = last_30["price"].iloc[0]
        end_price = last_30["price"].iloc[-1]
        pct_change_30d = round((end_price - start_price) / start_price * 100, 2)

        log(f"30-day change: {pct_change_30d}%")

        with open("change30d.txt", "w") as f:
            f.write(str(pct_change_30d))
    else:
        log("Not enough data for 30-day change.")
        with open("change30d.txt", "w") as f:
            f.write("NaN")

    # -----------------------------------------
    # Detect 5/10/15% changes in last 30 days
    # -----------------------------------------
    log("Calculating percentage change alerts...")

    if len(last_30) > 1:
        last_30["pct_change"] = (last_30["price"] - start_price) / start_price * 100

        thresholds = []
        for pct in range(5, 101, 5):
            thresholds.append(pct)
            thresholds.append(-pct)

        alerts = []
        for t in thresholds:
            crossed = last_30[last_30["pct_change"] >= t] if t > 0 else last_30[last_30["pct_change"] <= t]
            if not crossed.empty:
                row = crossed.iloc[0]
                alerts.append((row["date"], row["price"], t))

        for date, price, pct in alerts:
            fig.add_trace(go.Scatter(
                x=[date],
