# M3041 Active Safety Driver v1 Bounded Residual Fitting Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_bounded_residual_fit_route_to_m3042_result_audit`
- fitting dataset rows: 29
- fitting samples: 2981
- bounded offline fitting run: True
- candidate residual artifact: `runs/m3041_engineering_controller_active_safety_driver_v1_bounded_residual_fitting_preflight/candidate_residual_reflex_layer.npz`
- initial weighted MSE: 0.0011917449554767385
- final weighted MSE: 0.00047156475673466034
- final residual abs max: 0.07999999821186066
- success guard pass: True
- actor exclusion pass: True
- side-effect guard pass: True
- claim boundary pass: True
- gate matrix pass: True

## Interpretation

M3041 fits one bounded offline 72-to-3 residual/reflex candidate from actor-visible observation traces and actor-invisible trainer-side target deltas. The candidate artifact is an engineering implementation artifact for later audit and closed-loop measurement. It is not a validation result, ranking, promotion, repair-success claim, driver-performance verdict, paper result, high-fidelity result, finite-window-vs-GRU conclusion, or self-ID claim.

Rejected claims:

```text
closed-loop repair success, driver performance, validation readiness or result, controller/checkpoint/candidate ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Runtime Contract

```text
input: observation vector shape 72
output: action residual shape 3
composition: base [steer, throttle, brake] + bounded residual, clipped by downstream action bounds
```

## Next

- next blocker: `m3042-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-result-audit`
- selected next action: `m3042-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-result-audit`
