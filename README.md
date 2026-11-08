# Oil Price Tracker

Tracks daily Brent crude oil prices using the [EIA API](https://www.eia.gov/opendata/) and Yahoo Finance, published to GitHub Pages.

## Setup

### Repository Secret

The EIA data fetch requires an API key stored as a GitHub Actions repository secret:

| Secret name | Description |
|-------------|-------------|
| `EIA_API_KEY` | EIA Open Data API key. Obtain one free at <https://www.eia.gov/opendata/register.php>. |

To add the secret: **Settings → Secrets and variables → Actions → New repository secret**.

If `EIA_API_KEY` is not set the workflow still runs but only Yahoo Finance prices are collected; EIA columns will be blank until the secret is configured.

## How it works

- A GitHub Actions workflow runs daily at 05:00 UTC.
- `fetch_oil_price.py` fetches the **last 120 days** of EIA Brent prices in one request, then merges them with Yahoo Finance closing prices.
- Existing rows with blank EIA values are **backfilled** automatically when EIA publishes lagged data.
- `generate_chart.py` renders light/dark Plotly charts from `history.csv`.
- `change30d.txt` stores the 30-day percentage change used by the front-end.
