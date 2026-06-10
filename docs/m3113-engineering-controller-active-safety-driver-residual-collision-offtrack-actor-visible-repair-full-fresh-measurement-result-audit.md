# M3113 Residual Collision/Offtrack Actor-Visible Full-Fresh Measurement Result Audit

## Audit Decision

- decision: `accept_m3112_artifacts_with_plateau_route_to_m3114_residual_repair_plateau_synthesis`
- audit status: `accepted_with_behavior_plateau`
- M3112 status_pass: `True`
- M3112 gate_matrix_pass: `True`
- required artifacts present: `True`
- measurement rows: `64/64`
- measurement failures: `0`
- success: `57`
- collision: `5`
- offtrack: `2`
- speed_too_low: `0`
- same-row comparison rows: `256`
- selected next action: `m3114-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-plateau-synthesis`

## Evidence Summary

M3112 executed the M3110 residual collision/offtrack actor-visible repair as the full obs72-to-action3 action source on the complete M3084 fresh denominator. The artifact set is complete and claim-safe, but it does not improve the residual hard-safety counts.

Against M3105 on the same 64 rows and seeds:

```text
success delta: 0
collision delta: 0
offtrack delta: 0
speed_too_low delta: 0
```

Against M3095 on the same 64 rows and seeds:

```text
success delta: 0
collision delta: 0
offtrack delta: 0
speed_too_low delta: 0
```

Against M3100:

```text
success delta: +2
collision delta: 0
offtrack delta: -1
speed_too_low delta: -1
```

Against M3090:

```text
success delta: +14
collision delta: 0
offtrack delta: -3
speed_too_low delta: -11
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

- M3112 is complete and claim-safe as a full-fresh measurement artifact set.
- The M3110 action function can run the full 64-row denominator without execution failures.
- The actor contract remains deployable: obs72 to direct action3 `[steer, throttle, brake]`.
- M3112 preserves the zero speed-too-low guard.
- M3112 remains better than M3100 and M3090 on aggregate success and offtrack/speed-too-low counts.

## Rejected Claims

- M3112 is not a validation result.
- M3112 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3112 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- M3112 does not improve over M3105 or M3095.
- M3112 does not solve the residual hard-safety blocker because 5 collisions and 2 offtrack failures remain.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3 direct-action and hidden-input gates pass.
- `lineage_invalid`: not observed; M3112 routes from M3111/M3110/M3108/M3105 baselines.
- `metric_artifact`: not observed; summary, measurement, comparison, metric, contract, claim, gate, doc, and M3113 manifest artifacts are present.
- `scenario_sampling_failure`: not observed; all 64 full-fresh rows are accounted.
- `behavior_regression`: not observed versus M3105 aggregate counts, but no residual hard-safety improvement is observed.
- `objective_overfit`: high risk if the branch keeps adding actor-visible overlay rules without step-level action influence evidence.
- `proof_washout`: high risk if M3110 materialization probes or M3112 completeness are described as repair success.
- `seed_fragility`: unresolved; broader validation is not justified while current-sim residual blockers remain unchanged.

## Public Gate Overfit Risk

Risk is high for continuing blind actor-visible overlay edits. M3112 changed the action rule and produced closed-loop measurement, but the same seven residual hard-safety failures remain. The next route should synthesize the plateau and instrument the residual failures at step/action level before another repair materialization.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3114-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-plateau-synthesis
```

M3114 should classify why the M3110 overlay did not move the residual counts and decide one next route. It must not validate, rank, promote, tune on hidden labels, claim repair success, or return self-ID/GRU to the mainline objective.

## Boundary

M3113 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
