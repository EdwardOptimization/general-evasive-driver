# M2288 Paper-Route Current-Sim Scenario Task-Family Reset-Sampling And Lateral-Sign Repair Result Audit

- status: completed
- decision: `current_sim_scenario_task_family_reset_repair_audit_route_to_filter_edge_repair_design`
- manifest: `experiments/manifests/m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit.json`
- parent result: `runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/reset_validation/summary.json`
- reset rerun in M2288: `false`
- rollout/measured execution in M2288: `false`
- policy actions executed in M2288: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2287 materially repaired the v0 scenario pack but did not fully pass reset
validation:

```text
materialization result_class: current_sim_scenario_task_family_config_materialization_pass
scenario_spec_count: 72
unsupported_execution_blocker_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0

reset result_class: current_sim_scenario_task_family_reset_validation_fail
reset_success_count: 71 / 72
reset_failure_count: 1
lateral_bucket_mismatch_count: 1
label_not_allowed_count: 1
guardrail_violation_count: 0
```

This remains scenario/config evidence only. It is not a controller-performance
result.

## Remaining Failure

The only failed row is:

```text
scenario_spec_id: m2277_r4_02
scenario_family_id: R4
role_family: R4_unavoidable_mitigation
hidden_dynamics_bucket: low_mu
timing_bucket: late_close
lateral_bucket: centerline
expected_label: unavoidable
error: RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

Static classifier precheck for the materialized center says the row is correctly
classified:

```text
speed: 17.2 m/s
mu: 0.45
distance: 11.0 m
obstacle_half_width: 7.0 m
label: unavoidable
aeb_stop_distance: 37.23 m
distance_minus_safety_margin: 10.70 m
conventional_lateral_capacity: 0.38 m
drift_lateral_capacity: 0.77 m
required_lateral_offset: 8.20 m
```

Therefore the failure is not explained by the four-way obstacle label
classifier alone.

## Root Cause

The materializer's sampler-aware helper checked:

```text
classify_obstacle_scenario(speed, mu, distance, half_width)
```

but it did not also check the environment sampler's friction-step timing filter:

```text
has_time_after_step =
  obstacle_time_after_friction_step(scenario) >= min_time_after_friction_step
```

For this row:

```text
time_to_obstacle = 11.0 / 17.2 = 0.6395 s
dt = 0.02 s
latest nonnegative friction step ~= floor(0.6395 / 0.02) = 31
configured friction_step.step_range = 24..42
```

If the reset seed samples `friction_step_at > 31`, every exact obstacle sample is
rejected even though the label is `unavoidable`. The M2287 eval seed for this
row hit that edge, producing one reset failure.

This localizes the blocker to:

```text
scenario_sampling_failure / friction_step_timing_filter_not_in_materializer_precheck
```

## Lateral Sign Outcome

The M2284 left/right sign reversal is fixed. In M2287 there are no successful
left/right rows with signed-bucket mismatch.

The remaining summary-level lateral mismatch is a reset-unavailable artifact:
the failed row has no actual lateral offset, so the validator records one
numeric and bucket mismatch for that row.

## Contract And Guardrails

Clean:

```text
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
```

No policy action, rollout, measured execution, training, replay, PPO, private
holdout, controller-family ranking, paper-level claim, finite-window-vs-GRU
verdict, or level3 self-ID claim was made.

## Decision

Route to a focused filter-edge repair design:

```text
m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design
```

The design should decide how to make materialization precheck the same sampler
filters used by reset. Acceptable design options include:

```text
1. make low_mu friction_step.step_range compatible with the selected
   time_to_obstacle;
2. disable friction_step in this reset-valid scenario pack when exact initial
   mu already encodes the low_mu hidden bucket;
3. add an explicit materializer helper that rejects candidate targets whose
   obstacle time is incompatible with configured friction-step filters.
```

M2289 should not rerun reset. The next implementation can rerun materialization
and reset validation after the filter repair is frozen.

## Blocked Routes

Blocked:

```text
direct measured rollout from the 71/72-valid pack
policy action execution
training or PPO
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
```

## Next

Pre-register:

```text
m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design
```
