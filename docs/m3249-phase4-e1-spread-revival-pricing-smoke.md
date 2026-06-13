# M3249 Phase-4 E1 Spread-Revival Pricing Smoke

Status: completed. This is an E1 protocol smoke, not the full spread-revival pricing verdict.

## Verdict

- Quick protocol pass: **true**.
- E1 full verdict: **not run**.
- Next admitted step: register a separate full E1 pricing milestone with frozen selection/validation rows and paired CIs.
- E0 axis-table SHA256: `e5e7d2724585e4a997e079dd628d1efdf8829dfb00e4e0618a553fb30c2afe18`.

## Measured

- Quick variants: `sedan_tmeasy`, `bmw_e90_tmeasy`, `uazbus_tmeasy`.
- Quick selected row: `S1-inst03-seed7315000`.
- Fixed* quick grid: `(1.0, 1.0, 1.0)`.
- Arms exercised for every variant: fixed*, v4_rls, v4_pertuned, native_oracle.

| variant | fixed success | RLS success | pertuned success | native oracle success | structured attempts | CEM attempts |
|---|---:|---:|---:|---:|---:|---:|
| `sedan_tmeasy` | 0 | 0 | 0 | 1 | 2 | 2 |
| `bmw_e90_tmeasy` | 1 | 1 | 1 | 0 | 2 | 2 |
| `uazbus_tmeasy` | 0 | 0 | 0 | 0 | 2 | 2 |

## Inferred

The E1 four-arm Chrono protocol is runnable inside the M3248 E0 envelope. The numbers above are smoke context only: the same quick row is used to exercise arm plumbing, so no spread-revival or residual conclusion is admitted.

A full E1 milestone must separately freeze selection rows, validation rows, the global fixed* selection rule, per-instance tuning rule, native-oracle budget, paired CIs, and pass/negative decision thresholds before any pricing verdict.

## Claim Boundary

Phase-4 E1 Chrono spread-revival pricing protocol smoke only: exercises the fixed*, RLS-retuned, per-instance tuned, and native Chrono oracle arms inside the E0-frozen expressibility envelope. Quick mode is not a spread pricing verdict and makes no driver-performance, high-fidelity sufficiency, validation ranking, promotion, repair-success, feasibility-proof, paper, robustness, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e1_spread_revival_prereg.json`
- Quick JSON: `experiments/feasibility_audit/phase4_e1_spread_revival_quick.json`
- Episode rows: `runs/feasibility_audit/phase4_e1_spread_revival/episode_rows_quick.csv`
- Metrics: `runs/feasibility_audit/phase4_e1_spread_revival/metrics_quick.csv`
- Script: `scripts/feasibility_audit/phase4_e1_spread_revival_pricing.py`
