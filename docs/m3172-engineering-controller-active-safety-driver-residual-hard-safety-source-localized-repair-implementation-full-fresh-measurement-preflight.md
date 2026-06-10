# M3172 Residual Hard-Safety Source-Localized Repair Implementation Full-Fresh Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_residual_hard_safety_source_localized_repair_implementation_full_fresh_measurement_preflight_pass`
- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 256
- success count: 56
- collision count: 6
- offtrack count: 2
- speed-too-low count: 0
- success count delta vs M3105: -1
- collision count delta vs M3105: 1
- offtrack count delta vs M3105: 0
- speed-too-low count delta vs M3105: 0
- clearance margin mean: 11.002313807121931
- action clip fraction mean: 0.0
- gate matrix pass: True

## Interpretation

M3172 records full-fresh current-sim rows through the M3170 residual hard-safety source-localized repair implementation direct-action candidate and writes same-row deltas against M3105, M3095, M3100, and M3090. These are measurement and audit-input artifacts for M3173 only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3173-engineering-controller-active-safety-driver-residual-hard-safety-source-localized-repair-implementation-full-fresh-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3173-engineering-controller-active-safety-driver-residual-hard-safety-source-localized-repair-implementation-full-fresh-measurement-result-audit.json`
