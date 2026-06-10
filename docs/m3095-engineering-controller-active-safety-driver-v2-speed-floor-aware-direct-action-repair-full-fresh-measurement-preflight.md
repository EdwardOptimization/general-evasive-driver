# M3095 Active Safety Driver v2 Speed-Floor-Aware Full-Fresh Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v2_speed_floor_aware_direct_action_repair_full_fresh_measurement_preflight_pass`
- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 64
- success count: 57
- collision count: 5
- offtrack count: 2
- speed-too-low count: 0
- success count delta vs M3090: 14
- collision count delta vs M3090: 0
- offtrack count delta vs M3090: -3
- speed-too-low count delta vs M3090: -11
- clearance margin mean: 10.980184738052884
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3095 records full-fresh current-sim rows through the M3093 v2 speed-floor-aware direct-action repair function and writes same-row deltas against M3090. These are measurement and audit-input artifacts for M3096 only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3096-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3096-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-result-audit.json`
