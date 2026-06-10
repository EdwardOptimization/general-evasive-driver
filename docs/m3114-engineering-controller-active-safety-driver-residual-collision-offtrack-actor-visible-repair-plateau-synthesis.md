# M3114 Residual Collision/Offtrack Actor-Visible Repair Plateau Synthesis

## Decision

- synthesis decision: `pivot`
- decision: `pivot_to_m3115_residual_failure_step_action_influence_trace_materialization`
- selected next action: `m3115-engineering-controller-active-safety-driver-residual-failure-step-action-influence-trace-materialization-preflight`
- reason: M3112 proves the M3110 actor-visible overlay is complete and deployable but behavior-plateaued against M3105 and M3095. Continuing to add direct overlay gains without step/action influence evidence risks optimizing the same known rows without understanding why steering, braking, throttle, clearance, sideslip, and boundary recovery still fail.

## Evidence Summary

M3112 is complete and claim-safe as a full-fresh measurement artifact:

```text
rows: 64/64
execution failures: 0
success: 57
collision: 5
offtrack: 2
speed_too_low: 0
same-row comparison rows: 256
baselines: M3105 64, M3095 64, M3100 64, M3090 64
```

Against M3105 and M3095, M3112 is a plateau:

```text
success delta: 0
collision delta: 0
offtrack delta: 0
speed_too_low delta: 0
```

The residual rows remain the same failure family:

```text
collision_lateral_intrusion: 3 rows
offtrack_boundary_recovery: 4 rows
obstacle_collision: 5 rows
off_track: 2 rows
speed_too_low: 0 rows
```

The deployable actor contract remains intact:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

## Supported Claims

- M3112 is a complete, same-denominator, claim-safe measurement artifact.
- M3112 preserves the speed-floor improvement and does not reopen speed-too-low failures.
- M3112 does not regress aggregate hard-safety counts relative to M3105/M3095.
- M3112 does not improve residual collision/offtrack behavior.
- The next useful evidence is step/action influence trace decomposition for the seven residual failures, not another blind materialization overlay.

## Falsified Claims

- The M3110 residual actor-visible overlay is not a repair-success result.
- The M3110 overlay does not reduce residual collision/offtrack counts on the current 64-row denominator.
- M3112 is not validation, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, or self-ID evidence.
- Continuing the same overlay strategy without step-level evidence would not change the evidence axis.

## Failure Taxonomy Summary

- `contract_violation`: not observed; the direct obs72/action3 boundary is preserved.
- `lineage_invalid`: not observed; M3114 routes from M3113/M3112/M3110/M3108 evidence.
- `metric_artifact`: not observed; M3112 row counts, gate matrix, and comparison artifacts are complete.
- `scenario_sampling_failure`: not observed; all 64 rows are accounted.
- `behavior_regression`: not observed versus M3105/M3095 aggregate counts; observed versus the full goal because collisions/offtrack remain.
- `objective_overfit`: high risk if the branch keeps tuning known residual rows without action-influence traces.
- `proof_washout`: high risk if plateaued no-regression is described as repair success.
- `seed_fragility`: unresolved; no broader validation should start while current-sim residual hard-safety blockers remain.

## Public Gate Overfit Risk

Risk is high for continuing the current repair branch by direct gain edits. M3112 demonstrates that actor-visible overlay materialization can preserve the contract but does not move the residual failure outcomes. The next branch must expose step-level action influence around the seven residual failures before changing the policy again.

## Next Branch Decision

Pivot to:

```text
m3115-engineering-controller-active-safety-driver-residual-failure-step-action-influence-trace-materialization-preflight
```

M3115 should produce row-preserving residual failure traces for M3112/M3105/M3095 comparison:

- per-step steer/throttle/brake values and deltas
- obstacle urgency, edge urgency, speed, sideslip, lateral error, clearance, and action-rate traces
- final pre-failure windows for the seven residual rows
- separation of collision_lateral_intrusion and offtrack_boundary_recovery failure mechanisms
- claim-boundary gates that keep traces diagnostic and forbid repair-success interpretation

The next branch name is:

```text
active_safety_driver_residual_step_action_influence_diagnosis
```

## Boundary

M3114 is a synthesis decision only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
