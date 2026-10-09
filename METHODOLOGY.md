# METHODOLOGY — Panta Integrity Lens
**Status:** Published 2026-10-08. Matches `signals.py` and `tests/test_signals.py` (27/27 passing).
**Scope:** documents the seven integrity signals exactly as implemented in `signals.py`
and pinned by `tests/test_signals.py` (27/27 passing). Nothing here describes
planned, hypothetical, or removed functionality.

## How to read this document
- **OBSERVED** — measured from a real Panta API snapshot (Oct 8, 2026 pull: 95 markets).
- **DETERMINISTIC** — a pure calculation over snapshot fields; same input, same output, no randomness, no external calls.
- **ASSUMPTION** — a judgment call baked into a threshold or rule. Named explicitly.
- **LIMITATION** — what the signal cannot tell you. No signal here predicts outcomes or profitability.

The pipeline is: Panta API (catalog + per-market detail + trade tape) → `snapshot.py`
→ `signals.py` (pure functions, no I/O) → `render_dashboard.py` → static HTML.
Signals never see anything outside the snapshot file.

## The seven integrity signals

### 1. venue_mismatch — cross-venue price disagreement
- **Purpose:** flag markets where the primary-curve price and the secondary-market price disagree enough to suggest mispricing or stale quoting on one venue.
- **Rule (DETERMINISTIC):** `|primaryYesPrice − norm(secondaryYesPrice)| ≥ 0.10` (10 percentage points).
- **Threshold:** `MISMATCH_PP = 0.10`, pinned by `TestVenueMismatch`.
- **Normalization (ASSUMPTION):** secondary prices arrive as 1e9-scaled integer strings (observed Panta API quirk); values `> 10` are divided by 1e9, values `≤ 10` pass through as decimals. If either price is missing or unparseable, the signal is **absent** — never assumed to match.
- **Output:** badge "Venue mismatch" with detail `"primary 0.49 vs secondary 0.62 (13pp apart)"`.
- **Example (OBSERVED, Oct 8 snapshot):** "Saka 7+ points, GW6" and "Manchester Vs Tottenham: will both team score a goal" — 2 mismatches in the snapshot.
- **LIMITATION:** disagreement is not direction; the signal does not say which venue is right.

### 2. one_sided_flow — concentrated tape pressure
- **Purpose:** flag markets where recent trading is overwhelmingly one-directional, a classic thin-book / informed-flow warning.
- **Rule (DETERMINISTIC):** over tape trades with `blockTime` in the last 24h, `|net| / gross ≥ 0.80`, where YES-side volume counts positive and NO-side negative. Requires `gross > 0`.
- **Threshold:** 80% net concentration, pinned by `TestVolumeAndFlow.test_one_sided_flow` / `test_balanced_flow_not_one_sided`.
- **Output:** badge "One-sided flow" with detail `"24h net YES $90.00"`.
- **Example (OBSERVED, Oct 8 snapshot):** "Will niharika cross 5k followers on x by friday 10pm SGT?" carried Fresh flow + One-sided flow.
- **LIMITATION:** 24h window and 80% cutoff are fixed heuristics (ASSUMPTION), not calibrated to any outcome data.

### 3. fresh_flow — recent tape activity (staleness detector by absence)
- **Purpose:** distinguish quoted prices backed by recent trading from quotes with no tape behind them.
- **Rule (DETERMINISTIC):** ≥ 1 trade with `blockTime` within the last 24h → "Fresh flow".
- **Output:** badge "Fresh flow" with detail `"3 tape trade(s) in last 24h"`.
- **Missing-data handling:** an empty or absent tape yields **no** fresh_flow badge. Absence of tape is not treated as evidence of no trading — the Panta trades endpoint is known to return empty for some markets (also documented by independent builders). The dashboard reports what the API returned.
- **LIMITATION:** staleness is inferred from the tape the API exposes, not from ground-truth order flow.

### 4. thin — illiquid live market
- **Purpose:** flag live markets with neither volume nor tape activity.
- **Rule (DETERMINISTIC):** live AND `volumeUsdc == 0` AND zero tape trades in the window → "Thin".
- **Output:** badge "Thin" with detail `"Live but zero volume and no tape trades."`
- **Missing-data handling:** a market with nonzero volume but an empty tape is **not** flagged thin (pinned by `test_no_fresh_flow_when_tape_stale`) — volume and tape are treated as independent evidence.
- **Example (OBSERVED, Oct 8 snapshot):** "Will bitcoin hit $100,000 by 31 Dec 2026" and "Will GTA 6 release on November 19th, 2026" (both $0.00 volume).
- **LIMITATION:** "thin" is relative to reported volume; unreported off-API activity is invisible.

### 5. hot_volume — unusual activity vs peers
- **Purpose:** surface markets attracting outsized volume relative to the current live set.
- **Rule (DETERMINISTIC):** `volumeUsdc ≥ 75th percentile` of live-market volumes in the same snapshot, with the additional guard that the cutoff itself must be `> 0`.
- **Threshold:** top quartile — a relative, not absolute, bar (ASSUMPTION).
- **Output:** badge "Hot volume" with detail `"Top-quartile live volume ($318.04)"`.
- **Example (OBSERVED, Oct 8 snapshot):** "Will Arsenal beat Leeds United on October 10, 2026?" ($318.04 catalog volume leader).
- **LIMITATION:** relative to the snapshot's live set; in a quiet snapshot the bar is low. It measures attention, not quality.

### 6. new_listing — freshly listed market
- **Purpose:** discovery — newly listed markets have the least price history and the most mispricing risk.
- **Rule (DETERMINISTIC):** `now − startTime ≤ 72h`.
- **Threshold:** `NEW_LISTING_H = 72`, pinned by `TestTimeBadges` (48h in / 100h out).
- **Missing-data handling:** absent `startTime` → no badge, never assumed new.
- **Example (OBSERVED, Oct 8 snapshot):** 4 new listings in the 72h window.

### 7. resolving_soon — approaching resolution
- **Purpose:** flag markets closing within 7 days, where resolution mechanics and timing risk dominate.
- **Rule (DETERMINISTIC):** `0 < endTime − now ≤ 7 days`. Past end times are explicitly excluded (pinned by `test_resolving_soon_past_end_time_excluded`).
- **Threshold:** `RESOLVING_SOON_D = 7`, pinned by `TestTimeBadges`.
- **Missing-data handling:** absent `endTime` → no badge.
- **Example (OBSERVED, Oct 8 snapshot):** 5 markets resolving within 7 days.

## Supporting badges (classification, not integrity signals)
- **live** — unresolved and phase in (`primary`, `secondary`).
- **placeholder** — untitled catalog shell; a data-quality flag, excluded from intel. Orthogonal to `live` (a placeholder can be in a live phase; pinned by `test_placeholder_can_be_live_phase`). 37 of 95 rows in the Oct 8 snapshot.
- **heavy_favorite** (`yes ≥ 0.95`), **long_shot** (`yes ≤ 0.05`), **lean_yes / lean_no** (`|yes − 0.5| ≥ 0.15`). The 50/50 prior is an explicitly uninformed baseline (ASSUMPTION), not a model — it marks deviation from flat, nothing more.

## How missing, stale, or incomplete data is handled
1. **Unparseable numbers** (`_f`): return `None`; the dependent signal is skipped. Never coerced to zero, never imputed.
2. **Volume** (`_vol`): unparseable → `0.0` (conservative for the thin check; documented).
3. **Timestamps**: missing `startTime`/`endTime` → time badges absent.
4. **Secondary price scaling**: the `> 10 → ÷1e9` rule is an observed-format heuristic (ASSUMPTION); decimals pass through (pinned by `test_secondary_scaling_decimal_passthrough`).
5. **Empty tape**: yields no flow badges; thin requires the independent confirmation of zero volume.
6. **Untitled rows**: flagged as placeholders and excluded from intel rather than scored.

## What this methodology does NOT claim
- No signal predicts market outcomes, price direction, or profitability. There is no backtest, no win rate, and no training data.
- Thresholds (10pp, 15pp, 80%, 72h, 7d, top quartile) are fixed, documented heuristics — not fitted parameters.
- The dashboard renders a **point-in-time snapshot**, not a live feed. Signals are recomputed per snapshot pull.
- Read-only by design: the system cannot trade, quote, or act on its own flags.

## Reproducibility
`python3 -m unittest discover -s tests` — 27 tests, synthetic fixtures, fixed clock (`NOW = 1_790_000_000.0`), no network. Every rule above has a named test class: `TestLiveFamily`, `TestTimeBadges`, `TestLeanSignals`, `TestVenueMismatch`, `TestVolumeAndFlow`, `TestSummary`. Implementation: `signals.py` (`analyze()`); constants at the top of the file.
