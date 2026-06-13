# M3250 Phase-4 E1 Spread-Revival Pricing Full

Status: completed. This is the frozen full E1 Chrono pricing verdict; it is not training and does not admit Track F.

## Verdict

- E1 full verdict: **e1_spread_revival_not_supported**.
- Qualifying variants: none.
- Protocol gates passed: **true**.
- Fixed* grid selected on selection rows: `(0.6, 1.45, 1.4)`.

## Measured

- Variants: `sedan_tmeasy`, `bmw_e90_tmeasy`, `uazbus_tmeasy`.
- Validation variant/pair units: 18.
- Rows CSV: `runs/feasibility_audit/phase4_e1_spread_revival/episode_rows_full.csv`.

| variant | fixed | RLS | pertuned | native | pertuned-fixed | CI95 | pertuned-RLS | CI95 | native-pertuned |
|---|---:|---:|---:|---:|---:|---|---:|---|---:|
| `sedan_tmeasy` | 5 | 4 | 5 | 3 | 0.0000 | [0.0, 0.0] | 0.1667 | [0.0, 0.5] | -0.3333 |
| `bmw_e90_tmeasy` | 6 | 6 | 6 | 1 | 0.0000 | [0.0, 0.0] | 0.0000 | [0.0, 0.0] | -0.8333 |
| `uazbus_tmeasy` | 3 | 3 | 2 | 1 | -0.1667 | [-0.5, 0.0] | -0.1667 | [-0.5, 0.0] | -0.1667 |

Pooled readouts:

- `v4_pertuned - fixed_star`: -0.0556, CI95 [-0.1667, 0.0].
- `v4_pertuned - v4_rls`: 0.0000, CI95 [-0.1667, 0.1667].
- `native_oracle - v4_pertuned`: -0.4444, CI95 [-0.6667, -0.2222].

## Inferred

The verdict above applies only to the E0-admitted Chrono fixture envelope and this frozen grid/oracle budget. It does not cover independent payload-position, h_cg, tire-family, split-mu, or continuous lf/lr/Iz/cf/cr axes.

Track F remains blocked until Track E completes and CP-3 confirms targets and budget.

## Claim Boundary

Phase-4 E1 full Chrono spread-revival pricing only: fixed*, RLS-retuned, same-instance selection-tuned reflex, and attempt-limited native Chrono oracle arms are compared on the E0-frozen Sedan/BMW_E90/UAZBUS fixture envelope. This is zero-training pricing evidence; it makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e1_spread_revival_full_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e1_spread_revival_full.json`
- Episode rows: `runs/feasibility_audit/phase4_e1_spread_revival/episode_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e1_spread_revival/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e1_spread_revival_pricing_full.py`
