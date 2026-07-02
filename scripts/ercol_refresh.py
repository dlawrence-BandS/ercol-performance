"""
ercol_refresh.py
================
1. Downloads the latest B&S Feedonomics product feed
2. Counts Ercol products and variants
3. Appends a timestamped snapshot to data/ercol_product_history.json
4. Commits and pushes to GitHub so the live dashboard picks it up

Run via refresh_data.bat — no arguments needed.
"""

import gzip, io, csv, json, os, sys, subprocess
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────────────────────
FEED_URL     = "https://sftpgo.feedonomics.com/ftp/fdx_fc2e94f866798/barker_and_stonehouse_facebook_v2.csv.gz"
REPO_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(REPO_ROOT, "data", "ercol_product_history.json")
ERCOL_BRAND  = "ercol"   # case-insensitive match against 'brand' or 'google_product_category'

# ── HELPERS ───────────────────────────────────────────────────────────────
def log(msg): print(f"  {msg}")

def download_feed():
    log("Downloading Feedonomics feed...")
    import urllib.request
    with urllib.request.urlopen(FEED_URL, timeout=60) as resp:
        compressed = resp.read()
    log(f"Downloaded {len(compressed)/1024:.0f}KB compressed")
    raw = gzip.decompress(compressed)
    log(f"Decompressed: {len(raw)/1024/1024:.1f}MB")
    return raw

def detect_delimiter(header_line):
    """Score tab vs comma — same logic as refresh_attributes.py"""
    KNOWN_FIELDS = {'id','title','description','link','image_link','brand','price',
                    'availability','condition','google_product_category','item_group_id','mpn'}
    tab_score  = sum(1 for f in header_line.split('\t') if f.strip().lower() in KNOWN_FIELDS)
    comma_score = sum(1 for f in header_line.split(',')  if f.strip().lower() in KNOWN_FIELDS)
    return '\t' if tab_score >= comma_score else ','

def count_ercol(raw_bytes):
    """Count unique parent products and total variants for Ercol in the feed."""
    text = raw_bytes.decode('utf-8', errors='replace')
    lines = text.splitlines()
    if not lines:
        raise ValueError("Feed is empty")

    # Skip comment/metadata lines at the top (lines starting with # or blank)
    # Find the actual header row — the first line containing known feed field names
    KNOWN_FIELDS = {'id','title','description','link','image_link','brand','price',
                    'availability','condition','google_product_category','item_group_id','mpn'}
    header_idx = 0
    for i, line in enumerate(lines):
        fields_tab   = [f.strip().lower() for f in line.split('\t')]
        fields_comma = [f.strip().lower() for f in line.split(',')]
        if len([f for f in fields_tab   if f in KNOWN_FIELDS]) >= 3:
            header_idx = i
            break
        if len([f for f in fields_comma if f in KNOWN_FIELDS]) >= 3:
            header_idx = i
            break

    log(f"Header row found at line {header_idx}: {lines[header_idx][:80]}")

    # Parse from the header row onwards
    clean_text = '\n'.join(lines[header_idx:])
    delim = detect_delimiter(lines[header_idx])
    reader = csv.DictReader(io.StringIO(clean_text), delimiter=delim)

    # Normalise field names
    rows = []
    for row in reader:
        normed = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        rows.append(normed)

    log(f"Feed rows: {len(rows):,}")

    if rows:
        log(f"Feed fields: {list(rows[0].keys())[:10]}")
        sample = rows[0]
        log(f"Sample title: {sample.get('title','')[:60]}")
        log(f"Sample brand: {sample.get('brand','(no brand field)')}")
        log(f"Sample link:  {sample.get('link','')[:60]}")

    # Find the brand field
    brand_field = 'brand' if rows and 'brand' in rows[0] else None
    item_group_field = next((f for f in (rows[0] if rows else {}) if 'item_group' in f), None)
    id_field = 'id' if rows and 'id' in rows[0] else 'link'

    ercol_rows = []
    for row in rows:
        brand_val = row.get(brand_field or '', '').lower()
        title_val = row.get('title', '').lower()
        link_val  = row.get('link', '').lower()
        if (ERCOL_BRAND in brand_val or
            title_val.startswith('ercol') or
            'ercol' in link_val):
            ercol_rows.append(row)

    log(f"Ercol rows in feed: {len(ercol_rows):,}")

    # Unique parent products (by item_group_id if present, else unique IDs)
    if item_group_field:
        parent_ids = {row[item_group_field] for row in ercol_rows if row.get(item_group_field)}
    else:
        parent_ids = {row[id_field] for row in ercol_rows if row.get(id_field)}

    products = len(parent_ids)
    variants = len(ercol_rows)
    log(f"Unique Ercol products: {products}")
    log(f"Total Ercol variants:  {variants}")
    return products, variants

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"description": "Ercol product count snapshots", "snapshots": []}

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    log(f"Saved to {HISTORY_FILE}")

def already_snapped_today(history):
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return any(s['date'] == today for s in history.get('snapshots', []))

def git_push(products, variants):
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    msg = f"data: Ercol snapshot {today} — {products} products, {variants} variants"
    try:
        subprocess.run(['git', '-C', REPO_ROOT, 'add', 'data/ercol_product_history.json'],
                       check=True, capture_output=True)
        subprocess.run(['git', '-C', REPO_ROOT, 'commit', '-m', msg],
                       check=True, capture_output=True)
        subprocess.run(['git', '-C', REPO_ROOT, 'push'],
                       check=True, capture_output=True)
        log("✓ Pushed to GitHub")
    except subprocess.CalledProcessError as e:
        log(f"Git push failed (you may need to push manually): {e}")

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print("\n========================================")
    print("  Ercol Performance Dashboard — Refresh")
    print("========================================\n")

    # 1. Load existing history
    history = load_history()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    if already_snapped_today(history) and any(s['date']==today and s.get('products',0)>0 for s in history.get('snapshots',[])):
        log(f"Already have a valid snapshot for {today} — skipping feed download.")
        log("To force a re-snap, delete today's entry from data/ercol_product_history.json")
    else:
        # Remove any zero-count snapshot for today before re-running
        history['snapshots'] = [s for s in history.get('snapshots',[]) if s['date'] != today]

        # 2. Download feed + count
        raw = download_feed()
        products, variants = count_ercol(raw)

        # 3. Append snapshot
        snapshot = {
            "date": today,
            "products": products,
            "variants": variants,
        }
        history.setdefault('snapshots', []).append(snapshot)
        history['snapshots'].sort(key=lambda s: s['date'])
        save_history(history)
        log(f"✓ Snapshot recorded: {products} products / {variants} variants on {today}")

        # 4. Push to GitHub
        print()
        log("Pushing to GitHub...")
        git_push(products, variants)

    print("\n✓ Done. Dashboard will update on next page load.\n")

if __name__ == '__main__':
    main()
