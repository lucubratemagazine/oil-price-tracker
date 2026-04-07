import requests
import csv
import os

API_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=daily&data[0]=value&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=1&api_key=4msf5FM2dOmGZrWg53TBPItkMuQYErjgjxwpGMCm"


def fetch_oil_price():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    # Extract latest record
    record = data["response"]["data"][0]
    price = record["value"]
    date = record["period"]  # f.eks. "2026-03-30"

    return date, price


def append_to_csv(date, price, filename="history.csv"):
    file_exists = os.path.isfile(filename)

    # Ensure file has header
    if not file_exists or os.path.getsize(filename) == 0:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "price"])

    # Les siste linje (for å unngå duplikatdato)
    last_date = None
    with open(filename, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        if len(rows) > 1:
            last_date = rows[-1][0]

    # Hvis samme dato allerede er siste rad → ikke legg til på nytt
    if last_date == date:
        print(f"Ingen ny dato. Siste dato i {filename} er allerede {date}. Hopper over append.")
        return

    # Append ny rad
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, price])
        print(f"La til rad: {date}, {price}")


if __name__ == "__main__":
    date, price = fetch_oil_price()
    append_to_csv(date, price)
