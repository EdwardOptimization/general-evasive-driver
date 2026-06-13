# M3260 Phase-4 E4 Drift Regime Pricing

Status: completed. This is pricing evidence only; it does not open Track F/F2 and does not mutate the incumbent.

## Measured

- Verdict: `drift_pricing_completed`.
- Protocol gates passed: `true`.
- Rows: 204 total, 44 selection, 160 validation.
- Track F admitted: `false`.

| cell | units | fixed* success | per-tuned success | native success | drift-specialized success | oracle-fixed | oracle-per-tuned | dominant reflex failures |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| low_mu_power_oversteer | 20 | 0.000 | 0.000 | 0.000 | 0.400 | 0.400 [0.180, 0.620] | 0.400 [0.180, 0.620] | fail_to_enter:34, fail_to_stabilize:6 |
| lift_off_recovery | 20 | 0.000 | 0.000 | 0.050 | 0.000 | 0.050 [-0.048, 0.148] | 0.050 [-0.048, 0.148] | fail_to_stabilize:40 |

## Inferred

E4 characterizes where the reflex family fails in drift-specific Chrono cells using actor-visible sideslip/yaw plus rear-tire saturation telemetry. Positive oracle gaps are only pricing signals for later PI-gated Track F/F2 planning; neutral or negative gaps remain full-fidelity negative evidence.

## Claim Boundary

Phase-4 E4 Chrono drift / beyond-saturation pricing only: fixed v4 reflex, selection-row per-cell tuned reflex, native Chrono structured+CEM oracle, and drift-specialized feedback oracle are compared on frozen low-mu circle drift cells with obs72 sideslip/yaw and Chrono rear-tire saturation telemetry. E4 does not mutate ActiveSafetyReflexDriver, does not train, does not admit Track F/F2, and makes no validation ranking, promotion, driver-performance, current-sim sufficiency, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e4_drift_regime_pricing_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e4_drift_regime_pricing.json`
- Rows: `runs/feasibility_audit/phase4_e4_drift_regime_pricing/episode_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e4_drift_regime_pricing/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e4_drift_regime_pricing.py`
