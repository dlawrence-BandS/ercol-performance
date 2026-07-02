# Ercol Performance Dashboard

Live dashboard tracking Ercol SEO optimisation results — engagement, revenue, YoY comparisons, brand contribution, and product catalogue growth.

**Live URL:** `https://dlawrence-bands.github.io/ercol-performance/`

---

## What it does

- **Live GA4 data** — queries BigQuery directly from the browser on every page load, so the dashboard always shows the latest data
- **Product growth chart** — tracks how many Ercol products and variants are live on the site over time, using weekly snapshots from the Feedonomics product feed
- **YoY comparisons** — Apr and May like-for-like to avoid seasonal skew from Black Friday / January peaks
- **Brand revenue comparison** — Ercol vs all other brands (B&S excluded), showing its #1 position
- **Phase analysis** — Pre-optimisation / Onsite content / Product expansion phases throughout

---

## Setup

### 1. Create the GitHub repo

1. Create a new repo called `ercol-performance` on GitHub under `dlawrence-bands`
2. Push all files from this folder
3. Go to Settings → Pages → Source: **Deploy from branch** → `main` / `/ (root)`

### 2. Get a service account key

Use the existing `bs-dashboard@commanding-air-450109-p0.iam.gserviceaccount.com` service account (same as your other dashboards).

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → IAM & Admin → Service Accounts
2. Click the service account → Keys → Add Key → JSON
3. Download the JSON file

> ⚠️ Keep this repo **private** or at minimum never commit the key file.

### 3. Open the dashboard

Open `https://dlawrence-bands.github.io/ercol-performance/` and paste in the service account JSON key when prompted. It's saved to your browser's localStorage — you only need to do this once per device.

---

## Updating data

### Product count snapshots (run manually or weekly)

Double-click `refresh_data.bat` from this folder. It will:

1. Download the latest Feedonomics product feed
2. Count Ercol products and variants
3. Append a timestamped entry to `data/ercol_product_history.json`
4. Commit and push to GitHub

The dashboard picks up the new snapshot on the next page load.

**First run:** The script records the current product count as today's snapshot. Run it regularly (weekly recommended) to build up the trend line.

### GA4 data

No action needed — the dashboard queries BigQuery live on every page load. It always shows the latest available data.

---

## GitHub Actions (automated weekly snapshot)

The `.github/workflows/weekly_snapshot.yml` workflow runs every Monday at 07:00 UTC. It doesn't need any secrets configured — it just runs `ercol_refresh.py` and commits the result.

> Note: the GitHub Action only handles the product count snapshot. GA4 data is always live via BigQuery.

---

## Files

```
ercol-performance/
├── index.html                           # Dashboard (GitHub Pages)
├── refresh_data.bat                     # Windows: double-click to snapshot product counts
├── data/
│   └── ercol_product_history.json       # Product count snapshots (appended by bat script)
├── scripts/
│   └── ercol_refresh.py                 # Python: feed download + snapshot + git push
└── .github/workflows/
    └── weekly_snapshot.yml              # GitHub Action: runs every Monday
```

---

## BigQuery query

The dashboard runs this query on load (simplified for clarity):

```sql
SELECT
  FORMAT_DATE('%Y-%m', PARSE_DATE('%Y%m%d', e.event_date)) AS ym,
  COUNT(DISTINCT session_key) AS sessions,
  COUNT(DISTINCT CASE WHEN engaged THEN session_key END) AS engaged_sessions,
  COUNTIF(event_name = 'add_to_cart' AND item_brand = 'ercol') AS add_to_carts,
  COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN transaction_id END) AS purchases,
  SUM(CASE WHEN event_name = 'purchase' THEN price * quantity ELSE 0 END) AS revenue
FROM `commanding-air-450109-p0.analytics_287404213.events_*`, UNNEST(items) i
WHERE _TABLE_SUFFIX BETWEEN '20250401' AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
  AND LOWER(i.item_brand) = 'ercol'
GROUP BY 1
ORDER BY 1
```

GCP project: `commanding-air-450109-p0` · Dataset: `analytics_287404213`
