# M3100 Active Safety Driver v3 High-Speed Obstacle/Edge Hard-Safety Full-Fresh Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_full_fresh_measurement_preflight_pass`
- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 64
- success count: 55
- collision count: 5
- offtrack count: 3
- speed-too-low count: 1
- success count delta vs M3095: -2
- collision count delta vs M3095: 0
- offtrack count delta vs M3095: 1
- speed-too-low count delta vs M3095: 1
- success count delta vs M3090: 12
- collision count delta vs M3090: 0
- offtrack count delta vs M3090: -2
- speed-too-low count delta vs M3090: -10
- clearance margin mean: 11.38396328636265
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3100 records full-fresh current-sim rows through the M3098 v3 high-speed obstacle/edge hard-safety direct-action repair function and writes same-row deltas against M3095 and M3090. These are measurement and audit-input artifacts for M3101 only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3101-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3101-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-result-audit.json`
