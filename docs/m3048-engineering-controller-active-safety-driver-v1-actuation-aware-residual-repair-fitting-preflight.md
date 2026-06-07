# M3048 Active Safety Driver v1 Actuation-Aware Residual Repair Fitting Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_actuation_aware_residual_repair_fitting_preflight_pass`
- fitting dataset rows: 32
- fitting samples: 3216
- initial weighted MSE: 0.0011555318603820917
- final weighted MSE: 0.0004514343111628829
- final residual abs max: 0.07999999821186066
- action saturation guards pass: True
- success preservation guards pass: True
- gate matrix pass: True

## Interpretation

M3048 fits one offline action-headroom-constrained residual/reflex artifact. The artifact is for M3049 audit and possible later closed-loop measurement only. It is not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Candidate composition:

```text
raw_residual = obs_72 @ linear_weight + linear_bias
bounded_residual = clip(raw_residual, -residual_limit, residual_limit)
headroom_residual = clip(bounded_residual, action_low - base_action, action_high - base_action)
final_action = clip(base_action + headroom_residual, action_low, action_high)
```

Rejected claims:

```text
closed-loop repair success, driver performance, validation readiness or result, controller/checkpoint/candidate ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3049-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-result-audit`
- follow-up manifest: `experiments/manifests/m3049-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-result-audit.json`
