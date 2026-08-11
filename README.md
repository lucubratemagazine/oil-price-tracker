# Oil Price Tracker

A simple static web page that displays the latest crude oil price, a 30-day percentage change, a historical chart, and a full price history table.

## How It Works

`index.html` reads two plain-text data files at runtime:

| File | Purpose |
|------|---------|
| `history.csv` | Daily EIA and Yahoo Finance crude oil prices |
| `change30d.txt` | 30-day percentage price change (single number) |

Both files are updated **manually** and served directly by GitHub Pages alongside `index.html`.

---

## Manual Data Update Instructions

### `history.csv`

The file must be a UTF-8, comma-separated values (CSV) file with the following header on the first row:

```
date,eia_price,yahoo_price
```

| Column | Format | Description |
|--------|--------|-------------|
| `date` | `YYYY-MM-DD` | Date of the price record |
| `eia_price` | Numeric (e.g. `80.22`) or empty | EIA crude oil closing price in USD |
| `yahoo_price` | Numeric (e.g. `79.88`) or empty | Yahoo Finance crude oil closing price in USD |

- At least one of `eia_price` or `yahoo_price` should be present per row.
- Rows where both columns are non-numeric will show **"Data unavailable"** in the UI.
- Sort rows by date ascending (oldest first).

**Minimal example:**

```csv
date,eia_price,yahoo_price
2024-04-01,80.22,79.88
2024-04-02,,80.40
2024-04-03,81.10,
```

To add a new day, append a row to the bottom of the file, then save and push.

---

### `change30d.txt`

The file must contain a **single number** representing the 30-day percentage change (positive or negative). Do **not** include a `%` sign or any other text.

**Examples:**

```
-2.58
```

```
+4.12
```

If the file is missing, empty, or contains a non-numeric value (such as `NaN`), the UI will display **"30-day change: Data unavailable"** instead of crashing.

---

## UI Behaviour

| Situation | What the UI shows |
|-----------|-------------------|
| Page just loaded | "Loading latest price…" / "Loading 30-day change…" |
| Data loaded successfully | Price and change displayed normally |
| File missing or HTTP error | "Data unavailable" / error message in table |
| File present but value unparseable | "Data unavailable" — never raw "NaN" |

---

## Deployment

1. Edit `history.csv` and/or `change30d.txt` locally.
2. Commit and push to the `main` branch.
3. GitHub Pages will serve the updated files automatically within a few minutes.
