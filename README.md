# Panta Dashboard — XR-008 (Panta pivot)

Read-only market-intelligence dashboard on live Panta prediction markets.
Pivot from the blocked Solami build (XR-007 = Blocked — Sponsor Data Access
Failure, 2026-10-06 ~22:27 CDT).

**Links:** [Live dashboard](https://aimediaxgen.github.io/panta-integrity-lens/) ·
[Pitch video](https://www.youtube.com/watch?v=ZlIi8W_Elyk) ·
[Demo video](https://www.youtube.com/watch?v=e4TmhvFEms8) ·
[METHODOLOGY.md](METHODOLOGY.md) (7 signals, 27 tests)

## Verified state (2026-10-06 ~22:35 CDT)

- **Panta API $0-clean**: free email registration, no card, no wallet. Account
  active (canCreateMarkets=true). Live catalog reachable again via a
  `pk_live_` X-Api-Key (HTTP 200, real titled markets, pagination works).
  The `pk_test_` X-Api-Key hits the sandbox fixture only — not mainnet data.
  Browser-like User-Agent required (Cloudflare 1010 blocks default UAs).
- **Auth (updated 2026-10-06 ~22:30 CDT)**: Panta stopped accepting Bearer JWT
  on product routes (`/markets/`, `/categories/` → 401) while `/account/*`
  still 200s with the same JWT — a Panta-side inconsistency, not our creds.
  Recovery: `POST /account/keys/` with Bearer minted a `pk_live_` key
  (free, reversible, chmod-600 at `~/.panta_apikey_live`). `panta_client.py`
  now prefers `X-Api-Key` from `~/.panta_apikey_live`, falls back to the JWT
  from `~/.panta_auth.json`. Password at `~/.panta_pw` (chmod 600).
  Tokens/secrets are never printed, logged, committed, or written to repo
  files.
- **Sidetrack listing**: https://superteam.fun/earn/listing/panta-api-side-track
  — $5,000 USDG pool (2000/1000/1000/1000). Dual submission required:
  Colosseum Crypto World's Fair hackathon AND this Earn sidetrack.
- **Deadlines**: Colosseum submissions close Oct 12, 2026 23:59 PT;
  Earn sidetrack submissions close Oct 13, 2026 06:59 UTC (= Oct 13 01:59 CDT).
- **Attribution**: "Powered by Panta" required wherever Panta functionality
  appears — in the dashboard footer.
- **Judging**: Panta API integration, technical execution, product/UX,
  originality, impact potential, **traction** (weaker fit for read-only —
  disclose honestly, don't fake it).

## What is here

- `panta_client.py` — read-only client (catalog w/ pagination, detail,
  trade tape, categories). No write path exists anywhere in this project:
  no market creation, no quoting, no order building, no signing, no wallet.
- `snapshot.py` — pulls the full catalog + per-market detail + trade tape into
  `data/snapshot-<UTC>.json` and updates `data/snapshot-latest.json`.
  Re-runnable; every number traces to a Panta API response.
- `signals.py` — pure analytics over a snapshot: live/new-listing/resolving-soon/
  heavy-favorite/long-shot/lean-vs-50-50/venue-mismatch(primary vs secondary)/
  hot-volume/fresh-flow/one-sided-flow/thin-market signals, plus summary stats.
  No I/O, unit-testable. (Quirk handled: secondary prices arrive as 1e9-scaled
  integer strings; normalized before comparison.)
- `tests/test_signals.py` — 27 unit tests pinning every signal rule and its
  threshold (pure synthetic fixtures, fixed clock; run with
  `python3 -m unittest discover -s tests`).
- `METHODOLOGY.md` — the seven integrity signals documented for independent
  review: purpose, exact rule, threshold, and test reference per signal.
- `render_dashboard.py` — renders `dashboard.html` from the latest snapshot.
  Fully static, self-contained HTML: no build step, no framework — just open it
  in a browser.
- `dashboard.html` — generated output (regenerate after each snapshot pull).

## Run

```bash
cd panta-integrity-lens
python3 snapshot.py          # pull live catalog -> data/snapshot-<UTC>.json (read-only)
python3 render_dashboard.py  # -> dashboard.html
```

Open `dashboard.html` in a browser. Requirements: Python 3 stdlib only, `curl`
binary. Network: read-only GETs to `live-api.panta.market` (plus login on 401).

## Delivered (2026-10-09)

- Demo video (1:01) and pitch video (1:53) recorded and uploaded (links above)
- Public GitHub repo (this repo, MIT)
- Colosseum Crypto World's Fair submission: Panta Integrity Lens (Oct 9)
- Panta Earn sidetrack submission (Oct 9)

## Reproducing the grades

`data/snapshot-latest.json` is the exact Panta API snapshot behind the
deployed dashboard (pulled 20261010-041303 UTC, 97 markets, 0 detail errors).
Grades are deterministic from snapshot + `signals.py`:

```bash
python3 -m unittest discover -s tests  # 27 signal unit tests (stdlib only, no dependencies)
python3 render_dashboard.py # rebuild dashboard.html from data/snapshot-latest.json
```

## Competition note

The read-only lane is crowded: panta-copilot (agent desk + NL copilot),
pantadesk (institutional terminal, live on Vercel), sonar-panta (cross-venue
pricing signals + autonomous agent), OddsMind (research desk, tape-derived
price history). The winning angle has to be a sharp one — current proposal:
an evidence-graded market-integrity lens (venue mismatch + flow concentration +
placeholder-shell data-quality callouts) rather than another terminal clone.
