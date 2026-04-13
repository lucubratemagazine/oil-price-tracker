import requests
import csv
import os
from datetime import datetime, timedelta
import yfinance as yf

# EIA API (official, daily, sometimes delayed)
EIA_URL = (
    "https://api.eia.gov/v2/petroleum/pri/spt/data/"
    "?frequency=daily&data[0]=value&facets[series][]=RBRTE"
    "&sort[0][column]=period&sort[0][direction]=desc"
    "&offset=0&length=1"
    "&api_key=4msf5FM2dOmGZrWg53TBPItkMuQYErjgjxwpGMCm"
)

def log(msg):
    print(f"[INFO] {msg}")

# ---------------------------------------------------
# Load existing CSV and find last date
# ---------------------------------------------------
def load_existing_dates(filename="history.csv"):
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        log("No CSV found — starting fresh.")
        return None

    with open(filename, "r") as f:
        rows = [row for row in csv.reader(f) if row]

    if len(rows) <= 1:
        log("CSV only contains header — no previous data.")
        return None

    last_date = rows[-1][0]
    try:
        return datetime.strptime(last_date, "%Y-%m-%d").date()
    except:
        log("Last date in CSV is invalid — ignoring.")
        return None

# ---------------------------------------------------
# Fetch historical Yahoo Finance data
# ---------------------------------------------------
def fetch_yahoo_history(start_date, end_date):
    log(f"Fetching Yahoo Finance history {start_date} → {end_date}...")

    ticker = yf.Ticker("BZ=F")
    hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))

    if hist.empty:
        log("Yahoo returned empty dataset.")
        return {}

    result = {}
    for idx, row in hist.iterrows():
        date = idx.date()
        price = float(row["Close"])
        result[date] = price

    log(f"Yahoo returned {len(result)} days of data.")
    return result

# ---------------------------------------------------
# Fetch today's EIA price (fallback)
# ---------------------------------------------------
def fetch_eia_price():
    try:
        log("Fetching EIA price...")
        response = requests.get(EIA_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        record = data["response"]["data"][0]
        price = float(record["value"])
        date = datetime.strptime(record["period"], "%Y-%m-%d").date()

        log(f"EIA OK: {date} = {price}")
        return date, price

    except Exception as e:
        log(f"EIA FAILED: {e}")
        return None, None

# ---------------------------------------------------
# Append rows to CSV
# ---------------------------------------------------
def append_rows(rows, filename="history.csv"):
    file_exists = os.path.isfile(filename)

    if not file_exists or os.path.getsize(filename) == 0:
        log("Creating new CSV with header...")
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "eia_price", "yahoo_price"])

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
            log(f"Added row: {row}")

# ---------------------------------------------------
# Main logic
# ---------------------------------------------------
if __name__ == "__main__":
    today = datetime.utcnow().date()
    last_date = load_existing_dates()

    if last_date is None:
        start_date = today - timedelta(days=30)
    else:
        start_date = last_date + timedelta(days=1)

    if start_date > today:
        log("No missing days — CSV is up to date.")
        exit(0)

    # Fetch missing days from Yahoo
    yahoo_data = fetch_yahoo_history(start_date, today)

    rows_to_add = []

    current = start_date
    while current <= today:
        yahoo_price = yahoo_data.get(current, None)

        # EIA kun for dagens dato
        eia_price = None
        if current == today:
            eia_date, eia_val = fetch_eia_price()
            if eia_date == today:
                eia_price = eia_val

        # Hvis vi ikke har noen pris i det hele tatt → hopp over datoen
        if yahoo_price is None and eia_price is None:
            log(f"No price for {current}, skipping row.")
        else:
            rows_to_add.append([
                current.isoformat(),
                eia_price if eia_price is not None else "NaN",
                yahoo_price if yahoo_price is not None else "NaN"
            ])

        current += timedelta(days=1)

    if rows_to_add:
        append_rows(rows_to_add)
    else:
        log("No new rows to add.")
