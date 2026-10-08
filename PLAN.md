# XR-008 — Panta pivot build plan (from XR-007)

## Trigger state (per Osiris 2026-10-06 ~10:18 CDT)

- Condensed Solami support comment POSTED to Earn listing ~10:21 CDT,
  verified public as XGEN Research.
- 12-hour clock expires **~22:21 CDT Oct 6**.
- Actionable = working activation method, actual trial/account activation, or
  usable $0 data access. Acknowledgment / "looking into it" / generic
  troubleshooting does NOT stop the clock.
- If no actionable resolution by ~22:21 CDT: XR-007 → Blocked — Sponsor Data
  Access Failure, pivot immediately to Panta as **XR-008**.

## Target

Crypto World's Fair — Panta API Sidetrack
(https://superteam.fun/earn/listing/panta-api-side-track)
$5,000 USDG pool: 2000 / 1000 / 1000 / 1000.
Requires BOTH the official Colosseum Crypto World's Fair submission AND the
Earn sidetrack submission. "Powered by Panta" attribution required.

## Hard deadlines

- Colosseum submission close: **Oct 12, 2026 23:59 PT** (= Oct 13 01:59 CDT)
- Earn sidetrack submission close: **Oct 13, 2026 06:59 UTC** (= Oct 13 01:59 CDT)
- Both close at the same wall-clock moment. Work backwards from Oct 12 evening.

## Product angle: Market Integrity Lens

The read-only lane is crowded (panta-copilot, pantadesk, sonar-panta,
OddsMind — all verified on GitHub as of Oct 6). Another terminal clone loses.
The XGEN-brandable differentiation: **an evidence-graded market-integrity
dashboard** — the same discipline as Token Intel and mermail-opportunity-radar
(transparent scoring, math shown, read-only by design):

- **Mispricing flags**: markets where implied YES+NO deviates from 100, or
  where the last-tape price moved materially vs quoted price (stale quotes).
- **Liquidity health**: volume concentration, tape velocity, spread proxy from
  tape — markets that are effectively untradable get flagged, not hidden.
- **Staleness / resolution drift**: markets past resolutionTime still quoted;
  countdowns to close with phase badges.
- **Category pulse**: which categories carry the volume and the anomalies —
  a daily-brief style digest ("one honest observation") generated from real
  pulls, every number traced to the API.
- All scoring rules published in-app with the inputs shown. No black box.

Judging map: Panta API integration (meaningful — catalog + detail + tape
composed into a product), technical execution, product/UX, originality
(integrity lens is novel in this lane), impact potential, traction
(honest: none — say so, don't fake it).

## Build sequence (autonomous unless noted)

1. DONE (2026-10-06): read-only client + snapshot pipeline verified live
   (91 markets, 12 categories, all currently secondary phase).
2. Data layer: hourly `snapshot.py` cron → `data/snapshot-latest.json`
   (evidence discipline: every number traced).
3. Integrity scoring engine: misprice / staleness / liquidity-health rules
   with unit tests (RED/GREEN/unknown style, like Rug Radar's risk.py).
4. Static dashboard: single-page, renders from snapshot JSON, "Powered by
   Panta" attribution, rules published inline. (Static site = deployable to
   GitHub Pages with zero infra spend.)
5. Public repo + runnable README (listing requires public repo + demo).
6. Demo video 2–3 min: screen-record the dashboard against live data,
   narrate the integrity angle. Recording is a human gate (needs review).

## Human gates (Osiris)

- Colosseum Crypto World's Fair registration (free; Google/GitHub/email).
- Colosseum submission + Earn sidetrack submission (both due ~Oct 12 23:59 PT).
- Demo video review/approval before publishing.
- No wallet, no keys, no spend anywhere in this build. Panta writes
  (market creation / trading) are NOT used; the product is strictly read-only.

## Budget

~$0. API free tier is read-only-friendly; snapshot cadence ~hourly keeps
usage trivial. No signup beyond the existing Panta account.
