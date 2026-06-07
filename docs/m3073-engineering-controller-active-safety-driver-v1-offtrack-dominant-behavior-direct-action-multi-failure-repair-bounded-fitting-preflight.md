# M3073 Active Safety Driver v1 Direct-Action Multi-Failure Repair Bounded Fitting Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_direct_action_multi_failure_repair_bounded_fitting_preflight_pass`
- repair fitting dataset rows: 24
- fit/internal rows: 18 / 6
- repair samples: 2128
- final repair weighted MSE: 0.00021525553328820269
- parent weighted MSE accounting: 0.0002183983045141296
- candidate artifact: `runs/m3073_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_bounded_fitting_preflight/candidate_direct_action_repair_reflex_layer.npz`
- actor/action contract: obs72 to action3 [steer throttle brake]
- runtime base policy required: False
- gate matrix pass: True

## Interpretation

M3073 writes one bounded offline direct-action repair fitting artifact under the M3071 multi-failure contract. This is not target quality, fitted policy quality, validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
target quality, fitted policy quality, closed-loop repair success, validation readiness or result, driver performance, controller/checkpoint/candidate ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3074-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-result-audit`
- follow-up manifest: `experiments/manifests/m3074-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-result-audit.json`
