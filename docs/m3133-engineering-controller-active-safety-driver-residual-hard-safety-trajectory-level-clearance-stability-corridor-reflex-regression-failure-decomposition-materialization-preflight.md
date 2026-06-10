# M3133 Corridor Reflex Regression Failure Decomposition Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_residual_hard_safety_corridor_reflex_regression_failure_decomposition_materialization_pass`
- source full-fresh rows: 64
- decomposition rows: 64
- exact M3105 same-row matches: 64
- success delta vs M3105: -22
- collision delta vs M3105: 2
- offtrack delta vs M3105: 12
- speed-too-low delta vs M3105: 8
- primary axis counts: {'added_collision_regression': 2, 'added_offtrack_regression': 12, 'added_speed_floor_regression': 8, 'clearance_margin_loss': 31, 'return_or_success_loss': 6, 'stability_recovery_loss': 5}
- gate matrix pass: True

## Interpretation

M3133 materializes a no-new-execution decomposition of the M3131 standalone corridor-reflex regression against M3105. It preserves the M3131 row identity and M3105 same-row alignment, and it does not run a reset, step, rollout, replay, fitting, PPO, training, repair materialization, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, feasibility proof, or self-ID test.

Regression routing pressure:

```text
success regressions: 22
success improvements: 0
added collision rows: 2
added offtrack rows: 12
added speed-too-low rows: 8
clearance-margin regressions: 44
return regressions: 60
stability regressions: 46
```

Rejected claims:

```text
new execution, repair materialization, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit`
- follow-up manifest: `experiments/manifests/m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit.json`
