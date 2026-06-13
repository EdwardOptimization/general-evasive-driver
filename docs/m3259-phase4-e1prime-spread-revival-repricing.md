# M3259 Phase-4 E1' Oracle-Adequate Spread-Revival Repricing

Status: completed. This is the frozen E1' Chrono repricing verdict with a selection-row oracle-adequacy gate; it is not training and does not admit Track F.

## Verdict

- E1' full verdict: **e1prime_spread_revival_not_supported**.
- Qualifying variants: none.
- Protocol gates passed: **true**.
- Oracle adequacy gate passed: **true**.
- Fixed* grid selected on selection rows: `(0.6, 1.45, 1.4)`.

## Measured

- Variants: `sedan_tmeasy`, `bmw_e90_tmeasy`, `uazbus_tmeasy`.
- Validation units per variant: 24.
- Rows CSV: `runs/feasibility_audit/phase4_e1prime_spread_revival_repricing/episode_rows_full.csv`.

Selection-row oracle adequacy:

| variant | native - pertuned | CI95 | n | floor candidates | structured | CEM | gate |
|---|---:|---|---:|---:|---:|---:|---|
| `sedan_tmeasy` | 0.0417 | [0.0, 0.125] | 24 | 24 | 8 | 0 | True |
| `bmw_e90_tmeasy` | 0.0000 | [0.0, 0.0] | 24 | 24 | 0 | 0 | True |
| `uazbus_tmeasy` | 0.1250 | [0.0, 0.25] | 24 | 24 | 24 | 0 | True |

Validation spread readouts:

| variant | fixed | RLS | pertuned | native | pertuned-fixed | CI95 | pertuned-RLS | CI95 | native-pertuned |
|---|---:|---:|---:|---:|---:|---|---:|---|---:|
| `sedan_tmeasy` | 22 | 20 | 21 | 24 | -0.0417 | [-0.125, 0.0] | 0.0417 | [-0.0833, 0.1667] | 0.1250 |
| `bmw_e90_tmeasy` | 24 | 21 | 21 | 21 | -0.1250 | [-0.2917, 0.0] | 0.0000 | [-0.1667, 0.1667] | 0.0000 |
| `uazbus_tmeasy` | 19 | 20 | 13 | 23 | -0.2500 | [-0.4583, -0.0417] | -0.2917 | [-0.5, -0.125] | 0.4167 |

Pooled readouts:

- `v4_pertuned - fixed_star`: -0.1389, CI95 [-0.2222, -0.0556].
- `v4_pertuned - v4_rls`: -0.0833, CI95 [-0.1806, 0.0139].
- `native_oracle - v4_pertuned`: 0.1806, CI95 [0.0972, 0.2778].

## Inferred

The verdict above applies only to the E0-admitted Chrono fixture envelope and this frozen grid/oracle budget. It does not cover independent payload-position, h_cg, tire-family, split-mu, or continuous lf/lr/Iz/cf/cr axes.

Track F remains blocked until the later PI GPU-days checkpoint.

## Claim Boundary

Phase-4 E1' oracle-adequate Chrono spread-revival repricing only: fixed*, RLS-retuned, same-instance selection-tuned reflex, and native Chrono oracle arms are compared on the E0-frozen Sedan/BMW_E90/UAZBUS fixture envelope after an oracle-adequacy gate verifies that the native oracle anchor no longer underperforms v4_pertuned on selection rows. This is zero-training pricing evidence; it makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e1prime_spread_revival_repricing_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e1prime_spread_revival_repricing.json`
- Episode rows: `runs/feasibility_audit/phase4_e1prime_spread_revival_repricing/episode_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e1prime_spread_revival_repricing/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e1prime_spread_revival_repricing.py`
