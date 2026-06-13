# M3253 Phase-4 E3 Chrono Measurement A/C Smoke

Status: completed. This is an E3 protocol smoke only; it does not decide the full Chrono detection-latency table, the full recoverable-set budget, or Track F admission.

## Verdict

- E3 quick verdict: **protocol_smoke_passed**.
- Protocol gates passed: **true**.
- Rows: 4 / expected 4.

## Measured

| measurement | case | outcome | steps | fired/recovered |
|---|---|---|---:|---|
| A | A_long | speed_too_low | 94 | fired_step=50 |
| A | A_lat | max_steps | 160 | fired_step=125 |
| C | C_baseline_coast | recovered | 18 | recovered=True step=9 |
| C | C_v4_incumbent | recovered | 20 | recovered=True step=11 |

## Inferred

The current Chrono worker interface can execute the E3 smoke data path for obs72 detector traces and planar overshoot recovery traces. A full E3 verdict still needs a separate preregistration with frozen truth definitions, cells, seed streams, and safety-gating thresholds.

## Claim Boundary

Phase-4 E3 Chrono measurement-A/C protocol smoke only: scripted brake/steer ramps collect obs72 slip-detector traces, and injected planar overshoot states collect coast/v4 recovery traces on the default Chrono Sedan/TMeasy fixture. Quick mode is not a Chrono detection-latency verdict, not a full reflex recoverable-set budget, and makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, Track-F-admission, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_prereg.json`
- Quick JSON: `experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_quick.json`
- Episode rows: `runs/feasibility_audit/phase4_e3_chrono_measurement_ac/episode_rows_quick.csv`
- Metrics: `runs/feasibility_audit/phase4_e3_chrono_measurement_ac/metrics_quick.csv`
- Script: `scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_smoke.py`
