# M3088 Active Safety Driver v1 Deployable Runtime-Smoke Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight_pass`
- scheduled smoke rows: 8/8
- runtime-smoke episode rows: 8
- runtime-smoke failure rows: 0
- success count: 6
- collision count: 0
- offtrack count: 1
- speed-too-low count: 1
- clearance margin mean: 10.288422972097099
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3088 records bounded runtime-smoke current-sim rows through the packaged ActiveSafetyReflexDriver API. These rows are integration smoke artifacts for M3089 audit only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-result-audit.json`
