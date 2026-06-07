# M3080 Active Safety Driver v1 Deterministic Direct-Action Safety-Reflex Closed-Loop Measurement Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_closed_loop_measurement_preflight_pass`
- scheduled measurement rows: 32/32
- measurement episode rows: 32
- measurement failure rows: 0
- success count: 19
- collision count: 3
- offtrack count: 3
- speed-too-low count: 7
- clearance margin mean: 11.22031853760992
- high sideslip fraction mean: 0.15814697934268326
- raw action abs max: 1.0
- action clip fraction mean: 0.0
- final action abs max: 1.0
- runtime base policy required: False
- gate matrix pass: True

## Interpretation

M3080 records same-denominator current-sim measurement rows for the M3078 deterministic direct-action safety-reflex candidate. These rows are measurement artifacts for M3081 audit only. They are not validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3081-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-result-audit`
- follow-up manifest: `experiments/manifests/m3081-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-result-audit.json`
