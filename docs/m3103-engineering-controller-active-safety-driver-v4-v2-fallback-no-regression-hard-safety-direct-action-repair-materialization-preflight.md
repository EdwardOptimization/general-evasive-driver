# M3103 Active Safety Driver v4 v2-Fallback No-Regression Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_materialization_preflight_pass`
- policy id: `m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair`
- rule rows: 5
- no-regression guard rows: 4
- actor-input exclusion rows: 10
- claim-boundary rows: 21
- gate matrix pass: True
- low-speed probe throttle: 0.3700000047683716
- local obstacle probe brake: 0.5479999780654907
- local edge probe brake: -0.46895238757133484

## Interpretation

M3103 materializes a v4 v2-fallback no-regression direct-action repair package. It does not run an environment reset, step, rollout, replay, fitting, PPO, training, measurement, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.

Rejected claims:

```text
measurement result, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-result-audit.json`
