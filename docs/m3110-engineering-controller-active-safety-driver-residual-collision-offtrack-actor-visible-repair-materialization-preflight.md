# M3110 Residual Collision/Offtrack Actor-Visible Repair Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight_pass`
- policy id: `m3110_residual_collision_offtrack_actor_visible_repair`
- source residual rows: 7
- residual collision rows: 5
- residual offtrack rows: 2
- residual speed-too-low rows: 0
- rule rows: 6
- residual repair guard rows: 7
- actor-input exclusion rows: 10
- claim-boundary rows: 21
- gate matrix pass: True
- low-speed probe throttle: -0.37863999605178833
- residual obstacle probe brake: 0.8299338221549988
- residual edge probe brake: -0.5046315789222717

## Interpretation

M3110 materializes an actor-visible residual collision/offtrack direct-action repair package. It does not run an environment reset, step, rollout, replay, fitting, PPO, training, measurement, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.

The materialized function remains:

```text
obs72 actor-visible input -> direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
```

Rejected claims:

```text
measurement result, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-result-audit.json`
