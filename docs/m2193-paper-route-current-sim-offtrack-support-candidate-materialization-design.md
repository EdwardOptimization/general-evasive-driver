# M2193 Paper-Route Current-Sim Offtrack-Support Candidate Materialization Design

- status: completed
- decision: `current_sim_offtrack_support_candidate_materialization_design_admit_implementation`
- manifest: `experiments/manifests/m2193-paper-route-current-sim-offtrack-support-candidate-materialization-design.json`
- parent candidate config: `configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json`
- parent executable specs: `runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json`
- next manifest: `experiments/manifests/m2194-paper-route-current-sim-offtrack-support-candidate-materialization-implementation-and-run.json`
- implementation in M2193: `false`
- reset in M2193: `false`
- measured execution in M2193: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2193 freezes how the audited M2190 support-repair candidates become executable
task specs. It does not implement or run materialization.

The design goal is a no-rollout transformation:

```text
M2190 candidate config
  + M2151 executable task specs
  -> repaired executable task specs
  -> planned workload rows
  -> materialization audit artifacts
```

## Inputs

Required inputs:

```text
configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json
```

The implementation must fail closed if:

```text
candidate_count != 288
repair_candidate_id has duplicates
any parent_task_source_id is missing from M2151 specs
axis/split quotas differ from M2192 audit
any candidate guardrail flag is true
any candidate is profile-specific
any actor-input-contract-changing candidate appears
```

## Materialization Rule

Each candidate creates exactly one repaired executable spec.

```text
new_task_source_id = repair_candidate_id
parent_task_source_id = candidate.parent_task_source_id
```

The implementation must deep-copy the parent executable spec and add metadata:

```text
repair_branch_id
repair_candidate_id
repair_axis
repair_variant_id
repair_split
parent_task_source_id
parent_task_family
parent_source_family_template
parent_capability_pair
parent_claim_level_target
parent_support_class
materialization_semantics = current_sim_offtrack_support_repair_materialization_v0
scenario_source = current_sim_offtrack_support_repair_candidate_v0
paper_validity_status = current_sim_offtrack_support_candidate_not_reset_validated
```

The materialized spec must preserve:

```text
actor_input_contract = P0_human_view_no_wheel_no_oracle
include_privileged_params = false
wheel_observation_mode = none
obstacle_relative_velocity_mode = zero
action_history_mode = full
history_length > 0
profile_specific_tuning = false
controller_family_ranking_claim_made = false
finite_window_vs_gru_conclusion_made = false
paper_level_claim_made = false
level3_self_id_claim_made = false
```

## Delta Rules

Apply candidate deltas only to task/environment difficulty, not to actor inputs
or controller profile definitions.

### Road

```text
track_width = clamp(parent.track_width + delta_track_width, 4.0, 14.0)
track_radius = max(8.0, parent.track_radius + delta_track_radius)
```

The implementation must record original and repaired values.

### Obstacle Distance

```text
distance_low  = parent.obstacle.distance_range[0] + delta_obstacle_distance_min
distance_high = parent.obstacle.distance_range[1] + delta_obstacle_distance_max
```

Validation:

```text
distance_low >= 4.0
distance_high >= distance_low
distance_high <= max(120.0, parent_distance_high + 16.0)
```

### Obstacle Half Width

```text
half_width_low  = parent.obstacle.half_width_range[0] + delta_obstacle_half_width_min
half_width_high = parent.obstacle.half_width_range[1] + delta_obstacle_half_width_max
```

Validation:

```text
half_width_low >= 0.25
half_width_high >= half_width_low
half_width_high <= 2.5
```

### Reveal Step

Use `obstacle.perception_reveal_step` as the executable source of truth. If the
parent spec also has top-level `reveal_step`, both must be updated consistently.

```text
reveal_step = max(0, parent_reveal_step + delta_reveal_step)
```

The implementation must not use reveal changes to create hidden planner labels
or TTC-like actor inputs.

### Speed

```text
speed_low  = parent.speed_range[0] + delta_speed_min
speed_high = parent.speed_range[1] + delta_speed_max
```

Validation:

```text
speed_low >= 4.0
speed_high >= speed_low
speed_high <= 35.0
```

## Output Artifacts

M2194 should write:

```text
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/summary.json
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/planned_workload.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/materialization_rows.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/materialization_failures.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/claim_boundary.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/run_state.json
```

Expected counts:

```text
repaired_executable_spec_count: 288
planned_workload_row_count: 2304
profile_count: 8
candidate_split_counts:
  public_debug: 176
  public_gate: 112
```

Workload materialization crosses each repaired candidate spec with the existing
8-profile matrix:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

Checkpoint paths may remain unresolved at materialization time if the immediate
next gate is reset validation. Measured execution compatibility must be audited
later before policy actions run.

## Summary Gate

The M2194 summary must include:

```text
result_class
candidate_count
repaired_executable_spec_count
expected_repaired_executable_spec_count
planned_workload_row_count
expected_planned_workload_row_count
materialization_failure_count
contract_violation_count
forbidden_key_violation_count
guardrail_violation_count
profile_specific_tuning_count
actor_input_contract_change_count
candidate_axis_counts
candidate_split_counts
task_family_counts
environment_reset_started
environment_rollout_started
policy_action_executed
measured_execution_started
training_started
controller_family_ranking_claim_made
winner_selected
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
next_blocker
```

Pass condition:

```text
result_class = current_sim_offtrack_support_candidate_materialization_pass
repaired_executable_spec_count = 288
planned_workload_row_count = 2304
materialization_failure_count = 0
contract_violation_count = 0
forbidden_key_violation_count = 0
guardrail_violation_count = 0
```

Any failed candidate must make the whole milestone fail closed. Partial
materialization is diagnostic only and must not admit reset validation.

## Next Step

M2194 may implement and run this no-rollout materialization. If M2194 passes,
the next route is a materialization result audit before reset-validation command
design.

Still blocked:

```text
environment reset
measured execution
controller-family ranking
winner selection
finite-window vs GRU verdict
paper-level benchmark evidence
level3 self-identification claim
```
