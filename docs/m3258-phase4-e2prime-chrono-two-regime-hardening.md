# M3258 Phase-4 E2' Chrono Two-Regime Hardening

Status: completed. This is the frozen full E2' Chrono hardening verdict; it is zero-training pricing and does not admit Track F.

## Verdict

- E2' full verdict: **e2prime_flip_confirmed**.
- Flip confirmed: **true**.
- Variants confirming flip: ['sedan_tmeasy', 'uazbus_tmeasy'].
- Qualifying clean reveals by variant: {'sedan_tmeasy': [9.5, 12.0, 16.0, 22.0, 30.0], 'uazbus_tmeasy': [9.5, 12.0, 16.0, 22.0, 30.0]}.
- Protocol gates passed: **true**.

## Measured

- Vehicle variants: 2 (`sedan_tmeasy, uazbus_tmeasy`).
- Validation seeds per cell: 30.
- Selection rows: 560 / expected 560.
- Validation rows: 5760 / expected 5760.
- Rows CSV: `runs/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened/episode_rows_full.csv`.

| variant | clean reveal m | oracle - floor | CI95 | n | flip cell | oracle - seeker | seeker - fixed |
|---|---:|---:|---|---:|---|---:|---:|
| sedan_tmeasy | 9.5 | 0.7667 | [0.6833, 0.8417] | 120 | True | 0.95 | -0.1833 |
| sedan_tmeasy | 12 | 0.3333 | [0.25, 0.4167] | 120 | True | 0.4833 | -0.15 |
| sedan_tmeasy | 16 | 0.1583 | [0.1, 0.225] | 120 | True | 0.2667 | -0.1083 |
| sedan_tmeasy | 22 | 0.075 | [0.0333, 0.125] | 120 | True | 0.3583 | -0.2833 |
| sedan_tmeasy | 30 | 0.1083 | [0.0583, 0.1667] | 120 | True | 0.75 | -0.6417 |
| uazbus_tmeasy | 9.5 | 0.3583 | [0.2167, 0.5] | 120 | True | 0.6583 | -0.3 |
| uazbus_tmeasy | 12 | 0.2417 | [0.1667, 0.3167] | 120 | True | 0.45 | -0.2083 |
| uazbus_tmeasy | 16 | 0.0583 | [0.0167, 0.1] | 120 | True | 0.0583 | 0.0833 |
| uazbus_tmeasy | 22 | 0.075 | [0.0333, 0.125] | 120 | True | 0.075 | 0.45 |
| uazbus_tmeasy | 30 | 0.2 | [0.1333, 0.275] | 120 | True | 0.4 | -0.2 |

Secondary degraded spot:

| variant | cell | reveal m | oracle - floor | CI95 | n |
|---|---|---:|---:|---|---:|
| sedan_tmeasy | delay25_tight | 9.5 | 0.2 | [0.1333, 0.275] | 120 |
| uazbus_tmeasy | delay25_tight | 9.5 | -0.2167 | [-0.3333, -0.1081] | 120 |

## Inferred

The verdict is scoped to the frozen Sedan/TMeasy and UAZBUS/TMeasy fixtures and this scripted controller grid. It does not cover BMW_E90 E2, independent payload-position/h_cg, tire-family, split-mu, or learned-policy performance.

Track F remains blocked here; a confirmed flip only routes to a later GPU-days checkpoint.

## Claim Boundary

Phase-4 E2' hardened Chrono two-regime-law confirmation only: scripted oracle, threshold-seeker, and fixed belief-free controller families are compared on Sedan/TMeasy and UAZBUS/TMeasy over frozen clean reveal tiers plus one delay25 tight degraded spot, after M3257 froze the reconciled detector-onset definition. This is zero-training pricing evidence; it makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, Track-F-admission, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.json`
- Episode rows: `runs/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened/episode_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.py`
