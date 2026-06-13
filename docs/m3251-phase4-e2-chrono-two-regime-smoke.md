# M3251 Phase-4 E2 Chrono Two-Regime Smoke

Status: completed. This is a protocol smoke only; it is not the Chrono two-regime-law verdict and does not admit Track F.

## Verdict

- E2 quick verdict: **protocol_smoke_passed**.
- Protocol gates passed: **true**.
- Two-regime-law verdict: **not decided by quick mode**.

## Measured

- Rows: 18 / expected 18.
- Rows CSV: `runs/feasibility_audit/phase4_e2_chrono_two_regime/episode_rows_quick.csv`.
- Metrics CSV: `runs/feasibility_audit/phase4_e2_chrono_two_regime/metrics_quick.csv`.

| cell | reveal m | oracle | seeker | fixed | indicative oracle-seeker | indicative seeker-fixed | rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| clean | 9.5 | 0.5000 | 0.5000 | 0.0000 | 0.0 | 0.5 | 6 |
| clean | 30 | 1.0000 | 0.5000 | 0.5000 | 0.5 | 0.0 | 6 |
| delay25_tight | 9.5 | 0.0000 | 0.0000 | 0.0000 | 0.0 | 0.0 | 6 |

Calibration:

- `sedan_tmeasy`: tau=0.44844, max_shortfall=0.3737, outcome=timeout_other, reset_finite=True, variant_match=True.

## Inferred

The quick panel proves only that the E2 controller family and degraded observation filter execute through the Chrono worker. Indicative success-rate differences are not effect-size claims and must not be used as the full E2 verdict.

Track F remains blocked until Track E completes and CP-3 confirms targets and budget.

## Claim Boundary

Phase-4 E2 Chrono two-regime-law protocol smoke only: the current-sim threshold-seeker / shortfall-detector controller family is ported to the Chrono worker interface and exercised on a tiny clean plus degraded spot panel. Quick mode is not a clean VoI(belief) or degraded revival verdict; it makes no training, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e2_chrono_two_regime_prereg.json`
- Quick JSON: `experiments/feasibility_audit/phase4_e2_chrono_two_regime_quick.json`
- Episode rows: `runs/feasibility_audit/phase4_e2_chrono_two_regime/episode_rows_quick.csv`
- Metrics: `runs/feasibility_audit/phase4_e2_chrono_two_regime/metrics_quick.csv`
- Script: `scripts/feasibility_audit/phase4_e2_chrono_two_regime_smoke.py`
