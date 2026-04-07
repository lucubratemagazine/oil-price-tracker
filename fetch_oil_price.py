import requests
import csv
import os
from datetime import datetime
import yfinance as yf

# EIA API (offisiell, men forsinket)
EIA_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=1&api_key=4msf5FM2dOmGZrWg53TBPItkMuQYErjgjxwpGMCm"


def fetch_eia_price():
    response = requests.get(EIA_URL)
    response.raise_for_status()
    data = response.json()

    record = data["response"]["data"][0]
    price = float(record["value"])
    date = record["period"]  # f.eks. "2026-03-30"

    return date, price


def fetch_yahoo_price():
    ticker = yf.Ticker("BZ=F")
    hist = ticker.history(period="1d")

    price = float(hist["Close"].iloc[-1])
    date = datetime.utcnow().strftime("%Y-%m-%d")  # dagens dato

    return date, price


def append_to_csv(date, eia_price, yahoo_price, filename="history.csv"):
    file_exists = os.path.isfile(filename)

    # Ensure header exists
    if not file_exists or os.path.getsize(filename) == 0:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "eia_price", "yahoo_price"])

    # Read last date to avoid duplicates
    last_date = None
    with open(filename, "r", newline="") as f:
        rows = list(csv.reader(f))
        if len(rows) > 1:
            last_date = rows[-1][0]

    if last_date == date:
        print(f"Date {date} already exists. Skipping.")
        return

    # Append new row
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, eia_price, yahoo_price])
        print(f"Added row: {date}, {eia_price}, {yahoo_price}")


if __name__ == "__main__":
    eia_date, eia_price = fetch_eia_price()
    yahoo_date, yahoo_price = fetch_yahoo_price()

    # Vi bruker Yahoo-datoen som "dagens dato"
    append_to_csv(yahoo_date, eia_price, yahoo_price)


if __name__ == "__main__":
    date, price = fetch_oil_price()
    append_to_csv(date, price)
