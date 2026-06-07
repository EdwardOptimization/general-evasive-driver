# M3050 Active Safety Driver v1 Actuation-Aware Residual Repair Closed-Loop Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_actuation_aware_closed_loop_measurement_preflight_pass`
- scheduled measurement rows: 32/32
- measurement episode rows: 32
- measurement failure rows: 0
- success count: 4
- collision count: 4
- offtrack count: 24
- residual abs max: 0.07999999821186066
- headroom clip fraction mean: 0.19604308837476644
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3050 records same-denominator current-sim measurement rows for the M3048 action-headroom-constrained residual/reflex candidate. These rows are measurement artifacts for M3051 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3051-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-closed-loop-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3051-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-closed-loop-measurement-result-audit.json`
