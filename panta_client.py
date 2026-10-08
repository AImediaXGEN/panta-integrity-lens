#!/usr/bin/env python3
"""Read-only Panta API v1 client for the XR-007 pivot dashboard.

Strictly read-only: catalog, detail, trade tape, categories. No code path here
creates markets, quotes, builds, signs, submits, or claims anything.
Auth: Bearer JWT from ~/.panta_auth.json (chmod 600, never in repo/chat).
Quirk: Panta Cloudflare blocks non-browser User-Agents; UA is set below.
Verified live 2026-10-06 ~10:25 CDT: 50 markets via Bearer JWT (200).
X-Api-Key (pk_test_...) hits the sandbox fixture only — not mainnet data.
"""

import json
import os
import urllib.request

BASE = "https://live-api.panta.market/api/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

AUTH_PATH = os.path.expanduser("~/.panta_auth.json")
LIVE_KEY_PATH = os.path.expanduser("~/.panta_apikey_live")


def _auth_headers():
    # 2026-10-06 ~22:30 CDT: Panta stopped accepting Bearer JWT on product
    # routes (401, while /account/* still 200s with the same JWT — Panta-side
    # inconsistency). Prefer a pk_live_ X-Api-Key minted on our own free
    # account (POST /account/keys/ with Bearer); fall back to JWT.
    if os.path.exists(LIVE_KEY_PATH):
        with open(LIVE_KEY_PATH) as f:
            return {"X-Api-Key": f.read().strip()}
    with open(AUTH_PATH) as f:
        return {"Authorization": "Bearer " + json.load(f)["access"]}


def _token():
    with open(AUTH_PATH) as f:
        return json.load(f)["access"]


def _get(path, params=None):
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, **_auth_headers()})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GET {path} -> {e.code}: {e.read()[:200]!r}")


def categories():
    """Return list of category slugs."""
    return _get("/categories/")["categories"]


def list_markets(status=None, category=None, limit=50):
    """Full paginated catalog. Returns list of market rows (no live prices on list)."""
    params = {"limit": limit}
    if status:
        params["status"] = status
    if category:
        params["category"] = category
    out, cursor, seen = [], None, 0
    while True:
        if cursor:
            params["cursor"] = cursor
        page = _get("/markets/", params)
        out.extend(page.get("items", []))
        cursor = page.get("nextCursor")
        seen += 1
        if not cursor or seen > 40:
            break
    return out


def market_detail(market_id):
    """Single market incl. live price fields (yesPrice/noPrice filled on detail)."""
    return _get(f"/markets/{market_id}/")


def market_trades(market_id, limit=50):
    """Trade tape for a market."""
    return _get(f"/markets/{market_id}/trades/", {"limit": limit})


if __name__ == "__main__":
    cats = categories()
    mkts = list_markets()
    print(f"categories: {cats}")
    print(f"markets: {len(mkts)}")
    from collections import Counter
    print("by phase:", dict(Counter(m.get("phase") for m in mkts)))
    print("by category:", dict(Counter(m.get("category") for m in mkts)))
    if mkts:
        d = market_detail(mkts[0]["marketId"])
        print("sample:", d.get("title"), "| yes:", d.get("yesPrice"),
              "no:", d.get("noPrice"), "| vol:", d.get("volumeUsdc"))
