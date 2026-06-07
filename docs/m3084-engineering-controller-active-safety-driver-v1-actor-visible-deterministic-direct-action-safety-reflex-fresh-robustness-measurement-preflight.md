# M3084 Active Safety Driver v1 Deterministic Safety-Reflex Fresh Robustness Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight_pass`
- scheduled measurement rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- M3080 seed overlap count: 0
- robustness axis count: 4
- success count: 43
- collision count: 5
- offtrack count: 5
- speed-too-low count: 11
- clearance margin mean: 11.341408769853288
- high sideslip fraction mean: 0.1453887937478719
- raw action abs max: 1.0
- action clip fraction mean: 0.0
- final action abs max: 1.0
- runtime base policy required: False
- gate matrix pass: True

## Interpretation

M3084 records fresh-panel current-sim measurement rows for the M3078 deterministic direct-action safety-reflex candidate. These rows are measurement artifacts for M3085 audit only. They are not validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-result-audit.json`
