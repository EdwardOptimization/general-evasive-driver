# M3105 Active Safety Driver v4 V2-Fallback No-Regression Hard-Safety Full-Fresh Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight_pass`
- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 192
- success count: 57
- collision count: 5
- offtrack count: 2
- speed-too-low count: 0
- success count delta vs M3095: 0
- collision count delta vs M3095: 0
- offtrack count delta vs M3095: 0
- speed-too-low count delta vs M3095: 0
- success count delta vs M3100: 2
- collision count delta vs M3100: 0
- offtrack count delta vs M3100: -1
- speed-too-low count delta vs M3100: -1
- success count delta vs M3090: 14
- collision count delta vs M3090: 0
- offtrack count delta vs M3090: -3
- speed-too-low count delta vs M3090: -11
- clearance margin mean: 10.981307227309182
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3105 records full-fresh current-sim rows through the M3103 v4 v2-fallback no-regression hard-safety direct-action repair function and writes same-row deltas against M3095, M3100, and M3090. These are measurement and audit-input artifacts for M3106 only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.json`
