#!/usr/bin/env python3
"""Unit tests for signals.py — the XR-008 integrity-scoring engine.

Every rule gets a RED/GREEN/unknown-style fixture: a synthetic market dict
with a fixed `now` (no network, no clock dependence). The tests pin the
documented thresholds (0.95/0.05 favorite, 15pp lean, 10pp venue mismatch,
80% one-sided flow, 72h new-listing, 7d resolving-soon) so a later regression
fails loudly instead of silently degrading the dashboard's scoring.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import signals

NOW = 1_790_000_000.0  # fixed epoch for all fixtures


def market(**kw):
    base = {
        "marketId": "m1",
        "title": "Will it rain in Austin tomorrow?",
        "phase": "primary",
        "resolved": False,
        "yesPrice": 0.60,
        "primaryYesPrice": 0.60,
        "secondaryYesPrice": "600000000",
        "volumeUsdc": "100.0",
        "startTime": NOW - 10 * 86400,
        "endTime": NOW + 30 * 86400,
        "recentTrades": [
            {"blockTime": NOW - 3600, "side": "yes", "amountUsdc": "10.0"},
            {"blockTime": NOW - 7200, "side": "no", "amountUsdc": "10.0"},
        ],
    }
    base.update(kw)
    return base


def codes(m):
    return [c for c, _, _ in m["signals"]]


class TestLiveFamily(unittest.TestCase):
    def test_plain_live_market(self):
        m = market()
        s = signals.analyze([m], now=NOW)
        self.assertIn("live", codes(m))
        # placeholder-free market counts as titled
        self.assertEqual(s["titled"], 1)

    def test_placeholder_flagged_not_live_family(self):
        m = market(title="   ", yesPrice=None, phase="secondary")
        signals.analyze([m])
        c = codes(m)
        self.assertIn("placeholder", c)
        self.assertNotIn("live", c)

    def test_resolved_market_gets_no_live_signals(self):
        m = market(resolved=True)
        signals.analyze([m])
        self.assertNotIn("live", codes(m))

    def test_non_tradable_phase_gets_no_live_signals(self):
        m = market(phase="upcoming")
        signals.analyze([m])
        self.assertNotIn("live", codes(m))


class TestTimeBadges(unittest.TestCase):
    def test_new_listing_within_72h(self):
        m = market(startTime=NOW - 48 * 3600)
        signals.analyze([m], now=NOW)
        self.assertIn("new_listing", codes(m))

    def test_new_listing_outside_72h(self):
        m = market(startTime=NOW - 100 * 3600)
        signals.analyze([m], now=NOW)
        self.assertNotIn("new_listing", codes(m))

    def test_resolving_soon_within_7d(self):
        m = market(endTime=NOW + 3 * 86400)
        signals.analyze([m], now=NOW)
        self.assertIn("resolving_soon", codes(m))

    def test_resolving_soon_outside_7d(self):
        m = market(endTime=NOW + 30 * 86400)
        signals.analyze([m], now=NOW)
        self.assertNotIn("resolving_soon", codes(m))

    def test_resolving_soon_past_end_time_excluded(self):
        m = market(endTime=NOW - 100)
        signals.analyze([m], now=NOW)
        self.assertNotIn("resolving_soon", codes(m))


class TestLeanSignals(unittest.TestCase):
    def test_heavy_favorite(self):
        m = market(yesPrice=0.96)
        signals.analyze([m], now=NOW)
        self.assertIn("heavy_favorite", codes(m))

    def test_long_shot(self):
        m = market(yesPrice=0.04)
        signals.analyze([m], now=NOW)
        self.assertIn("long_shot", codes(m))

    def test_lean_yes_boundary(self):
        m = market(yesPrice=0.65)  # +15pp exactly
        signals.analyze([m], now=NOW)
        self.assertIn("lean_yes", codes(m))

    def test_lean_no_boundary(self):
        m = market(yesPrice=0.35)  # -15pp exactly
        signals.analyze([m], now=NOW)
        self.assertIn("lean_no", codes(m))

    def test_near_5050_gets_no_lean(self):
        m = market(yesPrice=0.55)
        signals.analyze([m], now=NOW)
        c = codes(m)
        self.assertNotIn("lean_yes", c)
        self.assertNotIn("lean_no", c)
        self.assertNotIn("heavy_favorite", c)
        self.assertNotIn("long_shot", c)


class TestVenueMismatch(unittest.TestCase):
    def test_mismatch_when_apart_10pp(self):
        m = market(primaryYesPrice=0.60, secondaryYesPrice="450000000")  # 0.45
        signals.analyze([m], now=NOW)
        self.assertIn("venue_mismatch", codes(m))

    def test_no_mismatch_when_close(self):
        m = market(primaryYesPrice=0.60, secondaryYesPrice="550000000")  # 0.55
        signals.analyze([m], now=NOW)
        self.assertNotIn("venue_mismatch", codes(m))

    def test_secondary_scaling_decimal_passthrough(self):
        # a secondary price already expressed as a decimal (< 10) is used as-is
        m = market(primaryYesPrice=0.60, secondaryYesPrice=0.59)
        signals.analyze([m], now=NOW)
        self.assertNotIn("venue_mismatch", codes(m))

    def test_mismatch_absent_without_secondary_price(self):
        m = market(primaryYesPrice=0.60, secondaryYesPrice=None)
        signals.analyze([m], now=NOW)
        self.assertNotIn("venue_mismatch", codes(m))


class TestVolumeAndFlow(unittest.TestCase):
    def test_hot_volume_top_quartile(self):
        ms = [market(marketId=str(i), volumeUsdc=str(10 * i)) for i in range(1, 9)]
        # 8 live markets; quartile cut index int(0.75*8)=6 of sorted vols
        signals.analyze(ms, now=NOW)
        hot = [codes(m) for m in ms]
        # top two volumes (70, 80) should be hot; bottom ones should not
        self.assertIn("hot_volume", hot[-1])
        self.assertIn("hot_volume", hot[-2])
        self.assertNotIn("hot_volume", hot[0])

    def test_fresh_flow_with_recent_trades(self):
        m = market()
        signals.analyze([m], now=NOW)
        self.assertIn("fresh_flow", codes(m))

    def test_no_fresh_flow_when_tape_stale(self):
        m = market(recentTrades=[
            {"blockTime": NOW - 2 * 86400, "side": "yes", "amountUsdc": "10.0"},
        ], volumeUsdc="50.0")
        signals.analyze([m], now=NOW)
        c = codes(m)
        self.assertNotIn("fresh_flow", c)
        self.assertNotIn("thin", c)  # volume nonzero, so not thin either

    def test_one_sided_flow(self):
        m = market(recentTrades=[
            {"blockTime": NOW - 3600, "side": "yes", "amountUsdc": "90.0"},
            {"blockTime": NOW - 7200, "side": "no", "amountUsdc": "10.0"},
        ])
        signals.analyze([m], now=NOW)
        self.assertIn("one_sided_flow", codes(m))

    def test_balanced_flow_not_one_sided(self):
        m = market()
        signals.analyze([m], now=NOW)
        self.assertNotIn("one_sided_flow", codes(m))

    def test_thin_flag(self):
        m = market(volumeUsdc="0", recentTrades=[])
        signals.analyze([m], now=NOW)
        self.assertIn("thin", codes(m))


class TestSummary(unittest.TestCase):
    def test_summary_counts(self):
        # untitled shell is flagged but, being in 'primary' phase, still
        # counts as live — placeholder is a data-quality flag, not a
        # tradability filter. Make it non-live to pin both counts.
        ms = [market(), market(title="", phase="upcoming"), market(resolved=True)]
        s = signals.analyze(ms, now=NOW)
        self.assertEqual(s["markets"], 3)
        self.assertEqual(s["live"], 1)
        self.assertEqual(s["placeholder"], 1)
        self.assertEqual(s["titled"], 2)
        self.assertEqual(s["signalCounts"].get("live"), 1)
        self.assertEqual(s["signalCounts"].get("placeholder"), 1)

    def test_placeholder_can_be_live_phase(self):
        # documented behavior: placeholder and live are orthogonal
        m = market(title="")  # phase='primary', resolved=False
        signals.analyze([m], now=NOW)
        self.assertIn("placeholder", codes(m))
        self.assertIn("live", codes(m))

    def test_total_volume(self):
        ms = [market(volumeUsdc="100.0"), market(volumeUsdc="25.5")]
        s = signals.analyze(ms, now=NOW)
        self.assertEqual(s["totalVolumeUsdc"], 125.5)


if __name__ == "__main__":
    unittest.main()
