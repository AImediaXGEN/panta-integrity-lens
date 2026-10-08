#!/usr/bin/env python3
"""Market-intelligence signals over a Panta snapshot — pure functions, no I/O.

Every signal is derived only from fields present in the snapshot produced by
snapshot.py (catalog rows + market detail + trade tape). No external data,
no invented numbers.

Signals per market (code -> (label, explainer)):
  placeholder      untitled catalog shell — data-quality flag, not tradable intel
  live             open market with a live yes price
  new_listing      listed within the last 72h (discovery)
  resolving_soon   closes within the next 7 days
  heavy_favorite   live yes price >= 0.95
  long_shot        live yes price <= 0.05
  lean_yes / lean_no  live price deviates >= 15pp from the uninformed 50/50 prior
  venue_mismatch   primary-curve price and secondary-market price disagree > 10pp
                   (secondary prices arrive in 1e9-scaled integer strings; normalized)
  hot_volume       volume in the top quartile of live markets
  fresh_flow       >= 1 tape trade in the last 24h
  one_sided_flow   last-24h tape net buy pressure >= 80% on one side
  thin             live but zero volume and zero tape trades (illiquid)
"""

import time

NEW_LISTING_H = 72
RESOLVING_SOON_D = 7
LEAN_PP = 0.15
MISMATCH_PP = 0.10
FAVORITE = 0.95
LONGSHOT = 0.05


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _norm_secondary(x):
    """Secondary prices arrive as 1e9-scaled integer strings; list rows as decimals."""
    v = _f(x)
    if v is None:
        return None
    return v / 1e9 if v > 10 else v


def _vol(x):
    v = _f(x)
    return v if v is not None else 0.0


def analyze(markets, now=None):
    """Annotate each market dict in-place with a 'signals' list of
    [code, label, detail] triples. Returns a summary dict."""
    now = now or time.time()
    live = [m for m in markets
            if not m.get("resolved") and m.get("phase") in ("primary", "secondary")]
    live_vols = sorted(_vol(m.get("volumeUsdc")) for m in live)
    hot_cut = live_vols[int(0.75 * len(live_vols))] if live_vols else 0.0

    summary = {
        "markets": len(markets),
        "live": len(live),
        "placeholder": 0,
        "titled": 0,
        "totalVolumeUsdc": 0.0,
        "signalCounts": {},
    }

    for m in markets:
        sigs = []
        title = (m.get("title") or "").strip()
        if not title:
            sigs.append(("placeholder", "Untitled shell",
                          "Catalog row with no title/description yet — excluded from intel."))
            summary["placeholder"] += 1
        else:
            summary["titled"] += 1
        summary["totalVolumeUsdc"] += _vol(m.get("volumeUsdc"))

        is_live = (not m.get("resolved")) and m.get("phase") in ("primary", "secondary")
        yes = _f(m.get("yesPrice"))
        if is_live and yes is not None:
            sigs.append(("live", "Live", "Open market, yes=%.3f" % yes))
            st = m.get("startTime") or 0
            if st and now - st <= NEW_LISTING_H * 3600:
                sigs.append(("new_listing", "New listing",
                              "Listed %.1fh ago" % ((now - st) / 3600)))
            et = m.get("endTime") or 0
            if et and 0 < et - now <= RESOLVING_SOON_D * 86400:
                sigs.append(("resolving_soon", "Resolving soon",
                              "Closes in %.1f days" % ((et - now) / 86400)))
            if yes >= FAVORITE:
                sigs.append(("heavy_favorite", "Heavy favorite", "yes=%.2f" % yes))
            elif yes <= LONGSHOT:
                sigs.append(("long_shot", "Long shot", "yes=%.2f" % yes))
            elif yes - 0.5 >= LEAN_PP:
                sigs.append(("lean_yes", "Leans YES",
                              "+%.0fpp vs the uninformed 50/50 prior" % ((yes - 0.5) * 100)))
            elif 0.5 - yes >= LEAN_PP:
                sigs.append(("lean_no", "Leans NO",
                              "+%.0fpp vs the uninformed 50/50 prior" % ((0.5 - yes) * 100)))

            py, sy = _f(m.get("primaryYesPrice")), _norm_secondary(m.get("secondaryYesPrice"))
            if py is not None and sy is not None and abs(py - sy) >= MISMATCH_PP:
                sigs.append(("venue_mismatch", "Venue mismatch",
                              "primary %.2f vs secondary %.2f (%.0fpp apart)" %
                              (py, sy, abs(py - sy) * 100)))

            if _vol(m.get("volumeUsdc")) >= hot_cut > 0:
                sigs.append(("hot_volume", "Hot volume",
                              "Top-quartile live volume ($%.2f)" % _vol(m.get("volumeUsdc"))))

            tape = m.get("recentTrades") or []
            day_ago = now - 86400
            recent = [t for t in tape if (t.get("blockTime") or 0) >= day_ago]
            if recent:
                sigs.append(("fresh_flow", "Fresh flow",
                              "%d tape trade(s) in last 24h" % len(recent)))
                net = sum((_vol(t.get("amountUsdc")) if str(t.get("side")).lower().startswith("y")
                           else -_vol(t.get("amountUsdc"))) for t in recent)
                gross = sum(_vol(t.get("amountUsdc")) for t in recent)
                if gross > 0 and abs(net) / gross >= 0.8:
                    sigs.append(("one_sided_flow", "One-sided flow",
                                  "24h net %s $%.2f" % ("YES" if net > 0 else "NO", abs(net))))
            elif _vol(m.get("volumeUsdc")) == 0:
                sigs.append(("thin", "Thin", "Live but zero volume and no tape trades."))

        m["signals"] = sigs
        for code, _, _ in sigs:
            summary["signalCounts"][code] = summary["signalCounts"].get(code, 0) + 1

    summary["totalVolumeUsdc"] = round(summary["totalVolumeUsdc"], 2)
    return summary
