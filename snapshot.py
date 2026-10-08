#!/usr/bin/env python3
"""Pull the full Panta catalog + per-market detail into data/snapshot.json.

Read-only. Re-runnable; each run writes data/snapshot-<UTC>.json and updates
data/snapshot-latest.json. Every price in the snapshot traces to a Panta API
response; nothing is invented.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panta_client import categories, list_markets, market_detail, market_trades

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def main():
    os.makedirs(DATA, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    rows = list_markets()
    detail, errors = [], 0
    for m in rows:
        mid = m.get("marketId")
        try:
            d = market_detail(mid)
            t = market_trades(mid, limit=20)
            detail.append({
                "marketId": mid, "title": d.get("title"),
                "category": d.get("category"), "phase": d.get("phase"),
                "resolved": d.get("resolved"), "status": d.get("status"),
                "yesPrice": d.get("yesPrice"), "noPrice": d.get("noPrice"),
                "primaryYesPrice": d.get("primaryYesPrice"),
                "primaryNoPrice": d.get("primaryNoPrice"),
                "secondaryYesPrice": d.get("secondaryYesPrice"),
                "secondaryNoPrice": d.get("secondaryNoPrice"),
                "priceSource": d.get("priceSource"),
                "volumeUsdc": d.get("volumeUsdc"),
                "totalVolumeUsdc": d.get("totalVolumeUsdc"),
                "startTime": d.get("startTime"), "endTime": d.get("endTime"),
                "resolutionTime": d.get("resolutionTime"),
                "recentTrades": (t.get("items") or t.get("trades") or [])[:20],
            })
        except Exception as e:
            errors += 1
            print(f"  skip {mid}: {e}")
    snap = {"pulledAt": stamp, "marketCount": len(rows),
            "detailErrors": errors, "markets": detail}
    path = os.path.join(DATA, f"snapshot-{stamp}.json")
    with open(path, "w") as f:
        json.dump(snap, f, indent=1)
    latest = os.path.join(DATA, "snapshot-latest.json")
    with open(latest, "w") as f:
        json.dump(snap, f, indent=1)
    print(f"markets: {len(rows)}, detailed: {len(detail)}, errors: {errors}")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
