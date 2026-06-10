# M3102 Active Safety Driver v3 Regression and v2-Fallback Hard-Safety Repair Synthesis

## Synthesis Decision

- decision: `route_to_m3103_v4_v2_fallback_no_regression_hard_safety_repair_materialization`
- synthesis status: `completed_with_v3_behavior_regression`
- source measurement: `m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-full-fresh-measurement-preflight`
- fallback measurement base: `m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight`
- M3100 residual failures: `9/64`
- M3095 residual failures on same denominator: `7/64`
- selected next action: `m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight`

## Evidence Summary

M3100 preserved the deployable actor contract and produced complete artifacts, but it regressed against M3095 on the same 64-row denominator:

```text
M3100 success count: 55
M3095 success count: 57
success delta vs M3095: -2
collision delta vs M3095: 0
offtrack delta vs M3095: +1
speed-too-low delta vs M3095: +1
mean clearance-margin delta vs M3095: +0.40377854830976434
mean return delta vs M3095: -27.1564682847606
mean speed delta vs M3095: -1.3373704390077648
```

There are no same-row success improvements over M3095. The two regressions are:

```text
m3100-same-row-comparison-0014 | collision_lateral_intrusion | parent | seed 401561 | M3100 off_track | M3095 success | clearance_delta -0.7644581428376727 | speed_delta -0.9372365428961427 | return_delta -24.364740711205027
m3100-same-row-comparison-0048 | speed_floor_stress | parent | seed 401771 | M3100 speed_too_low | M3095 success | clearance_delta +0.6348293222918002 | speed_delta -4.001847922421284 | return_delta -120.24726658972227
```

M3100 residual failures are:

```text
collision_lateral_intrusion: 2 obstacle_collision, 2 off_track
offtrack_boundary_recovery: 3 obstacle_collision, 1 off_track
speed_floor_stress: 1 speed_too_low
```

The original M3095 residual failures were:

```text
collision_lateral_intrusion: 2 obstacle_collision, 1 off_track
offtrack_boundary_recovery: 3 obstacle_collision, 1 off_track
speed_floor_stress: 0 failures
stability_action_pressure: 0 failures
```

The v3 high-speed obstacle/edge overlay increased clearance margin on average, but it did not reduce the 5 collision failures, added one offtrack failure, reopened one speed-floor failure, lowered mean return, and lowered mean speed. The likely failure mode is over-broad high-speed braking/throttle suppression: it improves some clearance margins while degrading completion and speed-floor recovery.

## Supported Claims

- M3100 is complete and claim-safe as a full-fresh measurement artifact set.
- M3100 does not provide evidence to continue the v3 overlay as-is because it has no success improvements over M3095 and adds 2 failures.
- M3095 should be retained as the measured fallback base for the next repair route, without treating that as promotion, ranking, or a driver-performance verdict.
- The next repair should be narrower than M3098/M3100: it must preserve the M3095 speed-floor success surface and target only actor-visible residual collision/offtrack signatures.
- M3103 may materialize a v4 direct-action repair package based on the M3095/v2 behavior with explicit no-regression guards before any new measurement.

## Rejected Claims

- M3100 does not prove repair success.
- M3095 is not promoted or declared the driver-performance winner by M3102.
- M3102 does not justify validation, ranking, promotion, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, finite-window-vs-GRU, or self-ID claims.
- The average clearance-margin gain in M3100 is not sufficient to keep the v3 overlay because success count, speed-floor behavior, and return regress against M3095.
- The next route must not tune on hidden labels, use outcome labels as actor input, add a runtime base policy, or select only easy rows.

## Failure Taxonomy

- `contract_violation`: not observed in M3100; actor-visible obs72/action3 direct-action contract remains intact.
- `lineage_invalid`: not observed; M3102 uses M3101/M3100/M3098/M3095 artifacts.
- `metric_artifact`: not observed; M3100 comparison rows, summary, gate, contract, and claim artifacts exist.
- `scenario_sampling_failure`: not observed; all 64 rows are accounted.
- `behavior_regression`: observed; M3100 has 2 fewer successes than M3095, no collision reduction, 1 additional offtrack, and 1 speed-too-low recurrence.
- `objective_overfit`: active risk; clearance margin improved while completion, speed-floor, and return regressed.
- `proof_washout`: active risk if improvement over M3090 hides regression against the stronger M3095 repair.
- `seed_fragility`: unresolved; no broader validation should run before a no-regression materialization and full-fresh remeasurement.

## Public Gate Overfit Risk

Risk is medium-high. The synthesis is still based on the same 64-row current-sim denominator. It is sufficient to reject the v3 overlay as the next unmodified repair route and choose one bounded materialization route, but not sufficient for validation or promotion. The selected route must be measured and audited on the same denominator before any broader claim.

## Selected Repair Route

Route exactly one follow-up to:

```text
m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-materialization-preflight
```

M3103 should materialize a v4 direct-action repair package with these constraints:

- preserve input `obs72` only and output direct action3 `[steer, throttle, brake]`;
- preserve `runtime_base_policy_required=false`, `checkpoint_model_required=false`, and `recurrent_hidden_state_required=false`;
- use the M3095/v2 speed-floor-aware behavior as the measured fallback base;
- do not keep the M3100 global high-speed throttle suppression pattern as-is;
- add only local actor-visible hard-safety arbitration for residual collision/offtrack signatures;
- include explicit no-regression guard rows for speed-floor stress and M3100 regression rows 0014 and 0048;
- write rule/config/exclusion/claim/gate/doc artifacts only, with no rollout, validation, ranking, promotion, repair-success, or performance claim.

## Boundary

M3102 is synthesis only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
