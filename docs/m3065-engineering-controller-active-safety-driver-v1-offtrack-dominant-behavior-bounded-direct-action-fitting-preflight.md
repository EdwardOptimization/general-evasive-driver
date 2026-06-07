# M3065 Active Safety Driver v1 Offtrack-Dominant Behavior Bounded Direct-Action Fitting Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_offtrack_behavior_direct_action_fit_route_to_m3066_result_audit`
- fitting dataset rows: 24
- fit/internal rows: 18 / 6
- fitting samples: 2128
- bounded offline direct-action fitting run: True
- candidate direct-action artifact: `runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz`
- initial fit weighted MSE: 0.6617927582032398
- final fit weighted MSE: 0.00020769915329666637
- all-accounting weighted MSE: 0.0023938326408113344
- final action abs max: 1.0
- actor exclusion pass: True
- side-effect guard pass: True
- target-quality boundary pass: True
- claim boundary pass: True
- gate matrix pass: True

## Interpretation

M3065 fits one bounded offline direct-action obs72-to-action3 candidate from actor-visible observation traces and actor-invisible trainer-side target_action tensors. The candidate artifact is an engineering implementation artifact for later audit and closed-loop measurement admission. It is not target-quality validation, a validation result, ranking, promotion, repair-success claim, driver-performance verdict, paper result, high-fidelity result, finite-window-vs-GRU conclusion, or self-ID claim.

Rejected claims:

```text
target quality, closed-loop repair success, validation readiness or result, driver performance, controller/checkpoint/candidate ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Runtime Contract

```text
input: observation vector shape 72
output: direct action shape 3
components: steer; throttle; brake
action bounds: clip each output to [-1, 1]
base policy required at runtime: false
```

## Next

- next blocker: `m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-result-audit`
- selected next action: `m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-result-audit`
