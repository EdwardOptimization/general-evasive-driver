# M3252 Phase-4 E2 Chrono Two-Regime Full

Status: completed. This is the frozen full E2 Chrono Sedan/TMeasy verdict; it is zero-training pricing and does not admit Track F.

## Verdict

- E2 full verdict: **chrono_clean_belief_value_positive**.
- Qualifying clean reveals: [9.5, 12.0].
- Protocol gates passed: **true**.

## Measured

- Selection rows: 280 / expected 280.
- Validation rows: 192 / expected 192.
- Rows CSV: `runs/feasibility_audit/phase4_e2_chrono_two_regime/episode_rows_full.csv`.

| clean reveal m | oracle - floor | CI95 | n | qualifies | oracle - seeker | seeker - fixed |
|---:|---:|---|---:|---|---:|---:|
| 9.5 | 0.75 | [0.375, 1.0] | 8 | True | 1.0 | -0.25 |
| 12 | 0.625 | [0.25, 0.875] | 8 | True | 0.625 | -0.125 |
| 16 | 0.25 | [0.0, 0.625] | 8 | False | 0.25 | 0.0 |
| 22 | 0.25 | [0.0, 0.625] | 8 | False | 0.625 | -0.375 |
| 30 | 0.125 | [0.0, 0.375] | 8 | False | 0.75 | -0.625 |

Secondary degraded spot:

| cell | reveal m | oracle - floor | CI95 | n |
|---|---:|---:|---|---:|
| delay25_tight | 9.5 | 0.125 | [0.0, 0.375] | 8 |

## Inferred

The verdict is scoped to the frozen default Chrono Sedan/TMeasy fixture and this controller grid. It does not cover BMW_E90/UAZBUS E2, independent payload-position/h_cg, tire-family, split-mu, or learned-policy performance.

Track F remains blocked until E3 completes and CP-3 confirms targets and budget.

## Claim Boundary

Phase-4 E2 full Chrono two-regime-law pricing only: scripted oracle, threshold-seeker, and fixed belief-free controller families are compared on the default Chrono Sedan/TMeasy fixture over frozen clean reveal tiers plus one delay25 tight degraded spot. This is zero-training pricing evidence; it makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e2_chrono_two_regime_full_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e2_chrono_two_regime_full.json`
- Episode rows: `runs/feasibility_audit/phase4_e2_chrono_two_regime/episode_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e2_chrono_two_regime/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e2_chrono_two_regime_full.py`
