import requests
import csv
import os
from datetime import datetime, timedelta
import yfinance as yf

# EIA API base URL (Brent crude daily spot price)
EIA_BASE_URL = (
    "https://api.eia.gov/v2/petroleum/pri/spt/data/"
    "?frequency=daily&data[0]=value&facets[series][]=RBRTE"
    "&sort[0][column]=period&sort[0][direction]=desc"
    "&offset=0"
)

# Number of recent EIA days to fetch (covers new rows + backfills lagged values)
EIA_FETCH_DAYS = 120

# Column indices within each records dict value [eia_str, yahoo_str]
_EIA_IDX = 0
_YAHOO_IDX = 1


def log(text):
    print(f"[INFO] {text}")


# ---------------------------------------------------
# Load existing CSV into memory as {date: [eia, yahoo]}
# ---------------------------------------------------
def load_existing_csv(filename="history.csv"):
    """Return (last_date, records_dict).

    records_dict maps date strings (YYYY-MM-DD) to [eia_str, yahoo_str].
    Returns (None, {}) when the file is absent or contains only a header.
    """
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        log("No CSV found — starting fresh.")
        return None, {}

    records = {}
    last_date = None

    with open(filename, "r") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return None, {}
        for row in reader:
            if not row:
                continue
            date_str = row[0]
            eia_str = row[1] if len(row) > 1 else ""
            yahoo_str = row[2] if len(row) > 2 else ""
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                log(f"Skipping invalid date row: {row}")
                continue
            records[date_str] = [eia_str, yahoo_str]
            # Track the chronologically latest date (not just file order)
            if last_date is None or date_str > last_date:
                last_date = date_str

    if last_date is None:
        log("CSV only contains header — no previous data.")
        return None, {}

    try:
        last = datetime.strptime(last_date, "%Y-%m-%d").date()
    except ValueError:
        log("Last date in CSV is invalid — ignoring.")
        return None, {}

    log(f"Loaded {len(records)} existing rows (last: {last_date}).")
    return last, records


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
# Fetch a range of EIA daily prices
# ---------------------------------------------------
def fetch_eia_range(days=EIA_FETCH_DAYS):
    """Return a dict mapping date → price for the most recent *days* EIA records.

    Returns an empty dict when the API key is absent or the request fails.
    """
    api_key = os.environ.get("EIA_API_KEY", "").strip()
    if not api_key:
        log("EIA_API_KEY not set — skipping EIA fetch.")
        return {}

    url = f"{EIA_BASE_URL}&length={days}&api_key={api_key}"
    log(f"Fetching EIA price range (last {days} days)...")

    try:
        response = requests.get(url, timeout=15)
    except requests.RequestException as e:
        log(f"EIA request failed: {e}")
        return {}

    if response.status_code != 200:
        log(f"EIA non-200 response: HTTP {response.status_code} — {response.text[:200]}")
        return {}

    try:
        payload = response.json()
    except ValueError as e:
        log(f"EIA response is not valid JSON: {e}")
        return {}

    response_body = payload.get("response")
    if response_body is None:
        log(f"EIA JSON missing 'response' key. Keys present: {list(payload.keys())}")
        return {}

    data = response_body.get("data")
    if not data:
        log("EIA 'response.data' is empty or missing.")
        return {}

    result = {}
    for record in data:
        try:
            date = datetime.strptime(record["period"], "%Y-%m-%d").date()
            price = float(record["value"])
            result[date] = price
        except (KeyError, ValueError, TypeError) as e:
            log(f"Skipping malformed EIA record {record}: {e}")

    log(f"EIA returned {len(result)} price records.")
    return result


# ---------------------------------------------------
# Write full sorted CSV
# ---------------------------------------------------
def write_csv(records, filename="history.csv"):
    """Write all records (dict of date_str → [eia_str, yahoo_str]) sorted by date."""
    sorted_dates = sorted(records.keys())
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "eia_price", "yahoo_price"])
        for date_str in sorted_dates:
            vals = records[date_str]
            writer.writerow([date_str, vals[_EIA_IDX], vals[_YAHOO_IDX]])
    log(f"Wrote {len(sorted_dates)} rows to {filename}.")


# ---------------------------------------------------
# Main logic
# ---------------------------------------------------
if __name__ == "__main__":
    today = datetime.utcnow().date()

    last_date_obj, existing_records = load_existing_csv()

    if last_date_obj is None:
        start_date = today - timedelta(days=30)
    else:
        start_date = last_date_obj + timedelta(days=1)

    # Fetch EIA for the last EIA_FETCH_DAYS days (covers new rows + backfills blanks)
    eia_data = fetch_eia_range(EIA_FETCH_DAYS)

    # Fetch Yahoo for the new date range (start_date..today)
    if start_date <= today:
        yahoo_data = fetch_yahoo_history(start_date, today)
    else:
        log("No missing days — Yahoo fetch skipped.")
        yahoo_data = {}

    # Backfill EIA into existing rows that currently have a blank EIA value
    backfilled = 0
    for date_str, vals in existing_records.items():
        if vals[_EIA_IDX] == "":
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj in eia_data:
                vals[_EIA_IDX] = str(eia_data[date_obj])
                backfilled += 1
    if backfilled:
        log(f"Backfilled EIA values for {backfilled} existing row(s).")

    # Add new rows for dates after last known date
    new_rows = 0
    current = start_date
    while current <= today:
        yahoo_price = yahoo_data.get(current)
        eia_price = eia_data.get(current)

        if yahoo_price is None and eia_price is None:
            log(f"No price for {current}, skipping row.")
        else:
            date_str = current.isoformat()
            existing_records[date_str] = ["", ""]
            existing_records[date_str][_EIA_IDX] = str(eia_price) if eia_price is not None else ""
            existing_records[date_str][_YAHOO_IDX] = str(yahoo_price) if yahoo_price is not None else ""
            new_rows += 1

        current += timedelta(days=1)

    if new_rows == 0 and backfilled == 0:
        log("No changes to write.")
    else:
        write_csv(existing_records)
