# M3254 Phase-4 E3 Chrono Tire Telemetry Smoke

Status: completed. This is a tire-truth telemetry connector smoke only; it does not decide full E3, a detection-latency table, a recoverable-set budget, or Track F admission.

## Verdict

- Telemetry quick verdict: **tire_telemetry_smoke_passed**.
- Protocol gates passed: **true**.
- Samples: 8 / expected 8.
- Wheel rows: 32 / expected 32.
- Normal load range: 3195.13 to 4952.06 N.

## Measured

| case | sample | obs72 finite | wheels | max slip angle | max lateral force | min normal load |
|---|---:|---|---:|---:|---:|---:|
| coast_hold | 0 | True | 4 | 0.00851054 | 4931.52 | 4012.82 |
| coast_hold | 1 | True | 4 | 0.00896117 | 555.217 | 3806.51 |
| coast_hold | 6 | True | 4 | 0.0082859 | 483.825 | 4039.2 |
| coast_hold | 12 | True | 4 | 0.00775205 | 453.736 | 4043.59 |
| brake_steer | 0 | True | 4 | 0.00851054 | 4931.52 | 4012.82 |
| brake_steer | 1 | True | 4 | 0.0484554 | 2099.37 | 3556.31 |
| brake_steer | 6 | True | 4 | 0.0789064 | 1426.89 | 3195.13 |
| brake_steer | 12 | True | 4 | 0.109282 | 267.104 | 3271 |

## Inferred

The current Chrono worker diagnostics can expose 4-wheel tire slip/force truth rows through reset and step samples while preserving finite obs72. Full E3 still needs a separate preregistration that freezes how these tire-truth fields define detection latency, recovery budgets, cells, seed streams, paired readouts, and safety gates.

## Claim Boundary

Phase-4 E3 Chrono tire-truth telemetry connector smoke only: the Chrono worker diagnostics expose finite four-wheel tire slip, wheel speed, tire force, local-force projection, and normal-load rows on the default Sedan/TMeasy fixture. Quick mode is not a Chrono detection-latency verdict, not a full reflex recoverable-set budget, and makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, Track-F-admission, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e3_chrono_tire_telemetry_prereg.json`
- Quick JSON: `experiments/feasibility_audit/phase4_e3_chrono_tire_telemetry_quick.json`
- Sample rows: `runs/feasibility_audit/phase4_e3_chrono_tire_telemetry/sample_rows_quick.csv`
- Wheel rows: `runs/feasibility_audit/phase4_e3_chrono_tire_telemetry/wheel_rows_quick.csv`
- Metrics: `runs/feasibility_audit/phase4_e3_chrono_tire_telemetry/metrics_quick.csv`
- Script: `scripts/feasibility_audit/phase4_e3_chrono_tire_telemetry_smoke.py`
