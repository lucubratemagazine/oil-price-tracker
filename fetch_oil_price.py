import requests
import csv
from datetime import datetime
import os

# API for Brent crude oil price (EIA)
API_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=1&api_key=DEMO_KEY"

def fetch_oil_price():
    response = requests.get(API_URL)
    data = response.json()

    # Extract price
    price = data["response"]["data"][0]["value"]
    date = data["response"]["data"][0]["period"]

    return date, price

def append_to_csv(date, price):
    file_exists = os.path.isfile("history.csv")

    # Ensure file has header
    if not file_exists or os.path.getsize("history.csv") == 0:
        with open("history.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "price"])

    # Append new row
    with open("history.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, price])

if __name__ == "__main__":
    date, price = fetch_oil_price()
    append_to_csv(date, price)
