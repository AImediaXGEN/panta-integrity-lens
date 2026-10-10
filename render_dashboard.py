#!/usr/bin/env python3
"""Render a static, self-contained dashboard.html from the latest snapshot.

No build step, no JS framework: open dashboard.html in any browser.
Attribution "Powered by Panta" is in the footer, per Panta terms.
"""
import html
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from signals import analyze

DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "dashboard.html")

BADGE_CSS = {
    "live": "b-live", "new_listing": "b-new", "resolving_soon": "b-soon",
    "heavy_favorite": "b-fav", "long_shot": "b-long",
    "lean_yes": "b-yes", "lean_no": "b-no",
    "venue_mismatch": "b-warn", "hot_volume": "b-hot",
    "fresh_flow": "b-flow", "one_sided_flow": "b-flow",
    "thin": "b-thin", "placeholder": "b-ph",
}


def esc(x):
    return html.escape(str(x) if x is not None else "")


def price_bar(yes):
    try:
        p = float(yes)
    except (TypeError, ValueError):
        return "<span class=na>n/a</span>"
    pct = max(0.0, min(100.0, p * 100))
    return ("<div class=pbar><div class=pfill style='width:%.1f%%'></div></div>"
            "<span class=pnum>%.1f&cent;</span>" % (pct, pct))


def badges(sigs):
    return " ".join(
        '<span class="badge %s" title="%s">%s</span>' % (
            BADGE_CSS.get(c, "b-ph"), esc(d), esc(lbl))
        for c, lbl, d in sigs if c not in ("live", "placeholder"))


def row(m):
    title = esc(m.get("title") or "(untitled)")
    cat = esc(m.get("category") or "?")
    phase = esc(m.get("phase") or "?")
    vol = m.get("volumeUsdc") or "0.00"
    src = esc(m.get("priceSource") or "")
    return ("<tr><td class=t>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            "<td class=vol>$%s</td><td class=src>%s</td><td>%s</td></tr>" % (
                title, cat, phase, price_bar(m.get("yesPrice")), vol, src,
                badges(m.get("signals", []))))


def main():
    snap_path = os.path.join(DATA, "snapshot-latest.json")
    snap = json.load(open(snap_path))
    markets = snap["markets"]
    summary = analyze(markets)
    pulled = esc(snap.get("pulledAt", "?"))
    when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    live_titled = sorted(
        [m for m in markets if not m.get("resolved")
         and m.get("phase") in ("primary", "secondary") and (m.get("title") or "").strip()],
        key=lambda m: -float(m.get("volumeUsdc") or 0))
    res_titled = sorted(
        [m for m in markets if (m.get("resolved") or m.get("phase") == "resolved")
         and (m.get("title") or "").strip()],
        key=lambda m: -float(m.get("volumeUsdc") or 0))
    mism = [m for m in markets if any(c == "venue_mismatch" for c, _, _ in m.get("signals", []))]

    def cnt(c):
        return summary["signalCounts"].get(c, 0)

    rows_live = "\n".join(row(m) for m in live_titled) or \
        '<tr><td colspan=7 class=empty>No live titled markets in this snapshot.</td></tr>'
    rows_res = "\n".join(row(m) for m in res_titled[:25]) or \
        '<tr><td colspan=7 class=empty>None.</td></tr>'

    html_doc = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panta Market Intelligence — snapshot {pulled}</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#0e1116;color:#dfe5ee}}
header{{padding:22px 28px;border-bottom:1px solid #232a35}}
h1{{margin:0 0 6px;font-size:22px}} h2{{margin:26px 28px 8px;font-size:16px}}
.sub{{color:#8b94a3;font-size:13px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 28px 0}}
.stat{{background:#161c25;border:1px solid #232a35;border-radius:8px;padding:10px 14px;min-width:120px}}
.stat .n{{font-size:20px;font-weight:700}} .stat .l{{font-size:11px;color:#8b94a3}}
table{{width:100%;margin:0;border-collapse:collapse;font-size:13px;min-width:640px}}
.tbl{{overflow-x:auto;margin:8px 28px 20px}}
@media (max-width:700px){{header{{padding:18px 16px}}h1{{font-size:20px}}h2{{margin:22px 16px 8px}}.stats{{margin:12px 16px 0;gap:8px}}.note{{margin:0 16px}}footer{{margin:10px 16px 24px}}.tbl{{margin:8px 0 16px 16px}}}}
th{{text-align:left;color:#8b94a3;font-weight:600;padding:8px;border-bottom:1px solid #232a35}}
td{{padding:8px;border-bottom:1px solid #1a2029;vertical-align:top}}
tr:hover td{{background:#131922}}
td.t{{max-width:340px}} td.vol{{text-align:right;white-space:nowrap}} td.src{{color:#8b94a3;font-size:11px}}
.pbar{{display:inline-block;width:90px;height:8px;background:#232a35;border-radius:4px;overflow:hidden;vertical-align:middle}}
.pfill{{height:100%;background:#3fb950}} .pnum{{margin-left:6px;color:#8b94a3}} .na{{color:#555}}
.badge{{display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;margin:1px 2px;white-space:nowrap}}
.b-new{{background:#1f3b63;color:#9ecbff}} .b-soon{{background:#5a3413;color:#ffce7a}}
.b-fav{{background:#123f22;color:#7ee2a0}} .b-long{{background:#4a1f24;color:#ff9aa5}}
.b-yes{{background:#123f22;color:#7ee2a0}} .b-no{{background:#4a1f24;color:#ff9aa5}}
.b-warn{{background:#5a3413;color:#ffce7a}} .b-hot{{background:#3d2a5c;color:#d3b8ff}}
.b-flow{{background:#123f45;color:#7adbe2}} .b-thin{{background:#2a2f38;color:#9aa4b2}}
.empty{{color:#8b94a3;text-align:center;padding:20px}}
footer{{margin:10px 28px 30px;color:#8b94a3;font-size:12px;border-top:1px solid #232a35;padding-top:14px}}
footer a{{color:#8b94a3}}
.note{{margin:0 28px;color:#8b94a3;font-size:12px;max-width:900px}}
</style></head><body>
<header><h1>Panta Market Intelligence</h1>
<div class=sub>Read-only dashboard over the Panta prediction-market catalog &middot;
point-in-time snapshot {pulled} UTC (not a live feed) &middot; rendered {when}</div></header>
<div class=stats>
<div class=stat><div class=n>{live}</div><div class=l>live markets</div></div>
<div class=stat><div class=n>{titled}</div><div class=l>titled (intel-grade)</div></div>
<div class=stat><div class=n>{ph}</div><div class=l>untitled shells excluded</div></div>
<div class=stat><div class=n>${tvol}</div><div class=l>catalog volume</div></div>
<div class=stat><div class=n>{new}</div><div class=l>new listings (72h)</div></div>
<div class=stat><div class=n>{soon}</div><div class=l>resolving &le;7d</div></div>
<div class=stat><div class=n>{mis}</div><div class=l>venue mismatches</div></div>
</div>
<h2>Live markets</h2>
<div class=tbl><table><tr><th>Market</th><th>Category</th><th>Phase</th><th>YES price</th>
<th style="text-align:right">Volume</th><th>Price src</th><th>Signals</th></tr>
{rows_live}</table></div>
<h2>Recently resolved (top 25 by volume)</h2>
<div class=tbl><table><tr><th>Market</th><th>Category</th><th>Phase</th><th>YES price</th>
<th style="text-align:right">Volume</th><th>Price src</th><th>Signals</th></tr>
{rows_res}</table></div>
<p class=note>Data-quality note: {ph} of {total} catalog rows are untitled
placeholder shells and are excluded from the intelligence tables above. Prices are
spot prices from the Panta API (priceSource shown per market); resolved markets show
final outcome (1 = YES won, 0 = NO won). Signals compare live prices against the
uninformed 50/50 prior and against primary-curve vs secondary-market venues — all
derived from this snapshot, nothing external.</p>
<footer>Powered by Panta &middot; read-only: this dashboard never creates markets,
trades, or touches a wallet &middot; not financial advice.<br>
<a href="https://github.com/AImediaXGEN/panta-integrity-lens">GitHub repo</a> &middot;
<a href="https://github.com/AImediaXGEN/panta-integrity-lens/blob/main/METHODOLOGY.md">Methodology (7 signals)</a> &middot;
<a href="https://www.youtube.com/watch?v=ZlIi8W_Elyk">Pitch video</a> &middot;
<a href="https://www.youtube.com/watch?v=e4TmhvFEms8">Demo video</a> &middot;
<a href="https://docs.panta.market/">Panta API docs</a></footer>
<p class=note>How to read this: <b>observed</b> = values taken directly from the Panta API
(title, prices, volume, phase); <b>derived</b> = integrity signals computed from this
snapshot only (see METHODOLOGY.md) — no external data, no outcome predictions.</p>
</body></html>""".format(
        pulled=pulled, when=when,
        live=summary["live"], titled=summary["titled"],
        ph=summary["placeholder"], tvol=summary["totalVolumeUsdc"],
        new=cnt("new_listing"), soon=cnt("resolving_soon"),
        mis=cnt("venue_mismatch"), total=summary["markets"],
        rows_live=rows_live, rows_res=rows_res)

    with open(OUT, "w") as f:
        f.write(html_doc)
    print("wrote %s (%d bytes), snapshot %s" % (OUT, len(html_doc), pulled))
    print("summary:", {k: v for k, v in summary.items() if k != "signalCounts"})
    print("signalCounts:", summary["signalCounts"])


if __name__ == "__main__":
    main()
