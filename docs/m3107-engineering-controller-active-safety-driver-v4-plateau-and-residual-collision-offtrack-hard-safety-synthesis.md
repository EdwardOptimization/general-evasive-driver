# M3107 Active Safety Driver v4 Plateau and Residual Hard-Safety Synthesis

## Decision

- synthesis decision: `pivot`
- decision: `pivot_to_m3108_residual_collision_offtrack_failure_decomposition`
- selected next action: `m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-materialization-preflight`
- reason: M3105 removes the M3100 regression but does not improve over M3095; continuing v4 no-regression local rules would preserve the same plateau without improving the residual hard-safety evidence.

## Evidence Summary

M3105 is complete and claim-safe as a full-fresh measurement artifact:

```text
rows: 64/64
execution failures: 0
success: 57
collision: 5
offtrack: 2
speed_too_low: 0
same-row comparison rows: 192
baselines: M3095 64, M3100 64, M3090 64
```

Against M3095, M3105 is a plateau:

```text
success delta: 0
collision delta: 0
offtrack delta: 0
speed_too_low delta: 0
mean clearance delta: 0.0011224892562964814
mean return delta: -0.009582429768155099
mean speed delta: -0.004289535331364308
```

Against M3100, M3105 removes the known regression:

```text
success delta: +2
collision delta: 0
offtrack delta: -1
speed_too_low delta: -1
```

The residual 7 failures are concentrated:

```text
collision_lateral_intrusion: 3 rows
offtrack_boundary_recovery: 4 rows
obstacle_collision: 5 rows
off_track: 2 rows
candidate rows: 4
parent rows: 3
```

The measured deployable actor contract remains intact:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

## Supported Claims

- M3105 is a complete, same-denominator, claim-safe measurement artifact.
- M3105 recovers from the M3100 offtrack and speed-floor regressions.
- M3105 does not regress aggregate hard-safety counts relative to M3095.
- The remaining hard-safety blocker is no longer speed-floor dominated; it is residual collision/offtrack behavior concentrated in two axes.
- The next useful evidence is row-preserving residual failure decomposition, not another process-only audit or narrow v4 no-regression edit.

## Falsified Claims

- The v4 no-regression route is not a repair-success result: it leaves 5 collisions and 2 offtrack failures.
- M3105 is not a driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, or self-ID result.
- The M3100 regression recovery does not prove active-safety improvement over the best measured M3095/M3105 baseline.
- Continuing the same v4 branch without new residual failure decomposition would not change the evidence axis.

## Failure Taxonomy Summary

- `contract_violation`: not observed; the direct obs72/action3 boundary is preserved.
- `lineage_invalid`: not observed; M3107 routes from M3106/M3105/M3103/M3095 evidence.
- `metric_artifact`: not observed; M3105 row counts, gate matrix, and comparison artifacts are complete.
- `scenario_sampling_failure`: not observed; all 64 rows are accounted.
- `behavior_regression`: not observed versus M3095 on aggregate counts; observed versus the full goal because collisions/offtrack remain.
- `objective_overfit`: high risk if the branch continues to tune local v4 guards on the same known rows.
- `proof_washout`: high risk if no-regression versus M3095 is described as repair success.
- `seed_fragility`: unresolved; no broader validation should start while residual current-sim hard-safety blockers remain.

## Public Gate Overfit Risk

Risk is high for continuing the current branch. The same 64-row denominator has now shown that v4 no-regression can recover from M3100, but it cannot move past M3095. A new edit on the same branch would likely optimize around known failure rows without improving the evidence structure.

The next branch must preserve the deployment boundary but change the evidence axis from local rule repair to residual failure understanding.

## Next Branch Decision

Pivot to:

```text
m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-failure-decomposition-materialization-preflight
```

M3108 should perform no new environment execution. It should materialize row-preserving residual failure artifacts from M3105/M3095/M3100:

- residual failure rows for the 7 non-success M3105 rows
- axis and termination summaries
- same-row residual baseline comparison against M3095, M3100, and M3090
- repair requirements that preserve speed-floor gains while targeting collision/offtrack
- claim-boundary and actor-contract gates

The next branch name is:

```text
active_safety_driver_residual_collision_offtrack_decomposition
```

## Boundary

M3107 is a synthesis decision only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
