# M3067 Active Safety Driver v1 Offtrack-Dominant Direct-Action Closed-Loop Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_offtrack_behavior_direct_action_closed_loop_measurement_preflight_pass`
- scheduled measurement rows: 32/32
- measurement episode rows: 32
- measurement failure rows: 0
- success count: 8
- collision count: 4
- offtrack count: 16
- raw action abs max: 2.2606801986694336
- action clip fraction mean: 0.03451952273501378
- final action abs max: 1.0
- runtime base policy required: False
- gate matrix pass: True

## Interpretation

M3067 records same-denominator current-sim measurement rows for the M3065 direct-action candidate. These rows are measurement artifacts for M3068 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-result-audit.json`
