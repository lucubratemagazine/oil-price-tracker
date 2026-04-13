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

    # ⭐ Fjern rader der både EIA og Yahoo mangler → ingen hull i grafen
    df = df.dropna(subset=["eia_price", "yahoo_price"], how="all")

    df = df.sort_values("date")

    log(f"Cleaned dataframe: {len(df)} valid rows.")
    return df

def compute_30d_change(df):
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

def build_figure(df, theme="plotly_white"):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["eia_price"],
        mode="lines+markers",
        name="EIA (official)",
        line=dict(color="#4da3ff", width=3),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["yahoo_price"],
        mode="lines+markers",
        name="Yahoo Finance (real-time)",
        line=dict(color="#ff9933", width=3),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title="Oil Price History",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template=theme,
        height=500,
        margin=dict(l=40, r=20, t=80, b=40),

        # ⭐ Stor og tydelig legend
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.18,
            xanchor="left",
            x=0,
            font=dict(size=22),
            itemsizing="constant"
        ),

        # ⭐ Større aksetekst + skråstilte datoer
        xaxis=dict(
            title_font=dict(size=20),
            tickfont=dict(size=14),
            tickangle=45
        ),
        yaxis=dict(
            title_font=dict(size=20),
            tickfont=dict(size=14)
        )
    )

    return fig

def generate_chart(df):
    log("Generating charts...")

    compute_30d_change(df)

    # LIGHT
    fig_light = build_figure(df, theme="plotly_white")
    pio.write_image(fig_light, "chart_light.png", width=1000, height=500)
    log("Saved chart_light.png")

    # DARK
    fig_dark = build_figure(df, theme="plotly_dark")
    pio.write_image(fig_dark, "chart_dark.png", width=1000, height=500)
    log("Saved chart_dark.png")

if __name__ == "__main__":
    df = load_csv()
    if df is None:
        exit(1)

    df = clean_dataframe(df)
    if df is None or df.empty:
        exit(1)

    generate_chart(df)
