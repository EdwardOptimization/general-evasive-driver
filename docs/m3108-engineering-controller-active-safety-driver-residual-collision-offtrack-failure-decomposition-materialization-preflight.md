# M3108 Residual Collision/Offtrack Failure Decomposition Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight_pass`
- source denominator rows: 64
- residual failure rows: 7
- residual collision rows: 5
- residual offtrack rows: 2
- residual speed-too-low rows: 0
- residual axes: collision_lateral_intrusion, offtrack_boundary_recovery
- residual comparison rows: 21
- repair requirement rows: 7
- gate matrix pass: True

## Interpretation

M3108 materializes row-preserving residual failure decomposition artifacts from M3105. It does not run a reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.

Residual hard-safety pressure:

```text
collision_lateral_intrusion rows: 3
offtrack_boundary_recovery rows: 4
obstacle_collision rows: 5
off_track rows: 2
speed_too_low rows: 0
```

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3109-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-result-audit`
- follow-up manifest: `experiments/manifests/m3109-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-result-audit.json`
