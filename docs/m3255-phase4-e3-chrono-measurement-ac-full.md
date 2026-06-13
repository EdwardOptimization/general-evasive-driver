# M3255 Phase-4 E3 Chrono Measurement A/C Full

Status: completed. This is the full E3 Chrono safety-measurement panel; it does not admit Track F without PI CP-3.

## Verdict

- Full E3 verdict: **chrono_safety_measurement_completed**.
- Protocol gates passed: **true**.
- CP-3 evidence ready: **true**.
- Track F admitted: **false**.

## Measured

| readout | value |
|---|---:|
| Measurement A rows | 24 / 24 |
| Measurement A truth-onset rate | 1 |
| Measurement A detector miss rate | 0.166667 |
| Measurement A p90 latency | 1.346 s |
| Measurement C rows | 72 / 72 |
| Measurement C v4 recovery rate | 1 |
| Measurement C baseline recovery rate | 1 |
| Measurement C v4 minus baseline | 0 |

## Measurement A By Axis

| axis | rows | truth onset | fire rate | median latency | p90 latency |
|---|---:|---:|---:|---:|---:|
| long | 12 | 1 | 1 | -35 steps | -19.1 steps |
| lat | 12 | 1 | 0.666667 | 60 steps | 88 steps |

## Measurement C By Overshoot

| overshoot | rows | v4 recovery | baseline recovery | v4-baseline |
|---:|---:|---:|---:|---:|
| 1.05 | 24 | 1 | 1 | 0 |
| 1.15 | 24 | 1 | 1 | 0 |
| 1.3 | 24 | 1 | 1 | 0 |

## Inferred

Full E3 has now measured the Sedan/TMeasy Chrono detector-latency table and paired baseline/v4 recoverable-set budget under frozen tire-truth definitions. These data make the Track-E evidence package ready for PI CP-3 review, but they do not self-approve Track F targets or budget.

## Claim Boundary

Phase-4 E3 full Chrono measurement A/C only: measurement A compares the obs72 shortfall detector to frozen Chrono tire-truth onset definitions, and measurement C quantifies the baseline/v4 recoverable-set budget from frozen injected planar overshoot states on Sedan/TMeasy. This is zero training and makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, Track-F-admission, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_full_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_full.json`
- Latency rows: `runs/feasibility_audit/phase4_e3_chrono_measurement_ac_full/latency_rows_full.csv`
- Recovery rows: `runs/feasibility_audit/phase4_e3_chrono_measurement_ac_full/recovery_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e3_chrono_measurement_ac_full/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_full.py`
