# M3090 Active Safety Driver v1 Deployable Full-Fresh Runtime Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight_pass`
- scheduled full-fresh rows: 64/64
- runtime measurement episode rows: 64
- runtime measurement failure rows: 0
- parity rows: 64
- parity outcome matches: 64/64
- success count: 43
- collision count: 5
- offtrack count: 5
- speed-too-low count: 11
- clearance margin mean: 11.341408769853288
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3090 records full-fresh current-sim rows through the packaged ActiveSafetyReflexDriver API and same-row parity against M3084 helper-path rows. These are runtime integration and parity artifacts for M3091 audit only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-result-audit.json`
