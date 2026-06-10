# M3132 Residual Hard-Safety Trajectory-Level Clearance/Stability Corridor Reflex Full-Fresh Measurement Result Audit

## Decision

- decision: `accept_m3131_artifacts_reject_behavior_regression_route_to_m3133_regression_failure_decomposition`
- selected next action: `m3133-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-regression-failure-decomposition-materialization-preflight`
- result class: `accept_m3131_complete_claim_safe_behavior_negative_measurement`

## Evidence Summary

M3131 is complete and claim-safe as a full-fresh current-sim measurement artifact:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
scheduled rows: 64/64
measurement episode rows: 64
measurement failure rows: 0
same-row comparison rows: 256
same-row exact seed matches: 64 per baseline
actor observation contract: obs72_actor_visible_current_frame_only
candidate output semantics: direct_action_clipped
candidate output components: [steer, throttle, brake]
runtime_base_policy_required: False
checkpoint_model_required: False
recurrent_hidden_state_required: False
hidden_oracle_actor_input_required: False
ttc_actor_input_required: False
validation_run: False
repair_success_claim_made: False
driver_performance_claim_made: False
```

Behavior evidence is negative versus the current M3105/M3095 plateau baselines:

```text
M3131 success/collision/offtrack/speed_too_low: 35/7/14/8
M3131 success rate: 0.546875
M3131 clearance margin mean: 8.551778383515293
delta vs M3105 success/collision/offtrack/speed_too_low: -22/+2/+12/+8
delta vs M3095 success/collision/offtrack/speed_too_low: -22/+2/+12/+8
delta vs M3100 success/collision/offtrack/speed_too_low: -20/+2/+11/+7
delta vs M3090 success/collision/offtrack/speed_too_low: -8/+2/+9/-3
clearance margin delta mean vs M3105: -2.429528843793889
return delta mean vs M3105: -70.2271982962308
speed mean delta mean vs M3105: -1.837472878134811
```

## Accepted Claims

- M3131 artifacts are complete and claim-safe.
- M3131 executed the complete 64-row M3084 fresh denominator with zero execution failures.
- M3131 preserves the deployable actor contract: actor-visible obs72 input to direct `[steer, throttle, brake]` output.
- M3131 same-row comparisons against M3105, M3095, M3100, and M3090 are available and exact-seed aligned.
- M3131 is behavior-negative relative to M3105/M3095 on collision, offtrack, speed-too-low, success count, clearance margin, and return.

## Rejected Claims

- M3131 is not repair-success evidence.
- M3131 is not validation, ranking, promotion, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.
- M3131 does not prove feasibility or infeasibility of residual rows.
- M3131 does not justify promotion of the standalone M3129 corridor reflex as the active driver.
- M3131 does not justify another blind direct gain edit without decomposing the regression axes.

## Failure Taxonomy

- `contract_violation`: not observed.
- `lineage_invalid`: not observed.
- `metric_artifact`: not observed.
- `scenario_sampling_failure`: not observed.
- `behavior_regression`: observed; success drops by 22 rows versus M3105/M3095 and hard-safety failures increase.
- `objective_overfit`: observed risk; the materialized corridor reflex worsens broad fresh-denominator behavior.
- `proof_washout`: high risk if M3131 is described as a repair result instead of a failed measurement route.
- `seed_fragility`: unresolved; no validation or robustness claim is allowed.

## Next

Route to M3133 regression failure decomposition. M3133 should not execute new environment rows. It should transform M3131 measurement rows and same-row comparisons into failure-axis rows that identify where the standalone corridor reflex regresses: extra offtrack, extra speed-too-low, added collision, clearance-margin loss, return loss, and stability/recovery degradation. M3133 should preserve the current deployable actor contract and decide whether the next implementation should be artifact repair, guarded fallback/hybridization, synthesis, or stop. It must not claim repair success, validation, ranking, promotion, driver performance, robustness result, current-sim verdict, high-fidelity result, feasibility proof, or self-ID evidence.
