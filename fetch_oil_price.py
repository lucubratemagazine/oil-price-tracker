import requests
import csv
import os
from datetime import datetime
import yfinance as yf

EIA_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=1&api_key=4msf5FM2dOmGZrWg53TBPItkMuQYErjgjxwpGMCm"


def log(msg):
    print(f"[INFO] {msg}")


def fetch_eia_price():
    try:
        log("Fetching EIA price...")
        response = requests.get(EIA_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        record = data["response"]["data"][0]
        price = float(record["value"])
        date = record["period"]

        log(f"EIA OK: {date} = {price}")
        return date, price
    except Exception as e:
        log(f"EIA FAILED: {e}")
        return None, None


def fetch_yahoo_price():
    try:
        log("Fetching Yahoo Finance price...")
        ticker = yf.Ticker("BZ=F")
        hist = ticker.history(period="1d")

        price = float(hist["Close"].iloc[-1])
        date = datetime.utcnow().strftime("%Y-%m-%d")

        log(f"Yahoo OK: {date} = {price}")
        return date, price
    except Exception as e:
        log(f"Yahoo FAILED: {e}")
        return None, None


def append_to_csv(date, eia_price, yahoo_price, filename="history.csv"):
    file_exists = os.path.isfile(filename)

    if not file_exists or os.path.getsize(filename) == 0:
        log("Creating new CSV with header...")
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "eia_price", "yahoo_price"])

    last_date = None
    with open(filename, "r", newline="") as f:
        rows = list(csv.reader(f))
        if len(rows) > 1:
            last_date = rows[-1][0]

    if last_date == date:
        log(f"Skipping append: {date} already exists")
        return

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, eia_price, yahoo_price])
        log(f"Added row: {date}, {eia_price}, {yahoo_price}")


if __name__ == "__main__":
    eia_date, eia_price = fetch_eia_price()
    yahoo_date, yahoo_price = fetch_yahoo_price()

    # Fallback‑logikk
    if yahoo_date:
        final_date = yahoo_date
    elif eia_date:
        final_date = eia_date
    else:
        log("Both EIA and Yahoo failed — aborting.")
        exit(1)

    if yahoo_price is None:
        yahoo_price = "NaN"

    if eia_price is None:
        eia_price = "NaN"

    append_to_csv(final_date, eia_price, yahoo_price)

if __name__ == "__main__":
    date, price = fetch_oil_price()
    append_to_csv(date, price)
