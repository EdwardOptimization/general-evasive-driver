# M2396 Paper-Route Current-Sim Dual-Axis Effective Candidate Measured Validation Design

- status: completed
- decision: `effective_candidate_measured_validation_design_admit_implementation`
- manifest: `experiments/manifests/m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design.json`
- parent audit: `docs/m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit.md`
- parent reset summary: `runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json`
- reset execution in M2396: `false`
- rollout/measured execution in M2396: `false`
- policy action executed in M2396: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2396 freezes a bounded measured-validation route for the M2394 reset-ready
effective candidate artifacts.

The goal is not to rank controller families or prove paper-level performance.
The goal is to produce the first closed-loop measured artifact over the actual
effective candidate references that survived schema repair and reset validation.

## Input Artifacts

Use these fixed inputs:

```text
effective candidate rows:
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv

effective candidate scenario rows:
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_scenario_rows.csv

effective candidate config files:
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs/*.json

reset-readiness evidence:
  runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json
  runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/candidate_scenario_reset_rows.csv
  runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_target_rows.csv
  runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_validation_rows.csv

selected checkpoint rows:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv

profile config root:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs
```

The selected-checkpoint source remains diagnostic-only:

```text
selected checkpoints: 15
profiles: 5
seeds per profile: 3
ranking_admissible: false
winner_selected: false
```

## Denominator

M2396 chooses the full candidate-scenario reference denominator:

```text
effective candidates: 54
candidate-scenario references: 2049
unique pack/scenario reset targets: 350
selected checkpoints: 15
measured episodes: 2049 * 15 = 30735
```

The measured denominator is `candidate_id + pack_id + scenario_spec_id +
selected_checkpoint`. This preserves candidate identity and source-slice
lineage. It intentionally does not collapse to the 350 reset targets because
reset targets only prove that an environment can load and reset; they do not
represent distinct candidate repair hypotheses.

Required uniqueness:

```text
unique candidate_id count: 54
unique candidate-pack-scenario rows: 2049
unique pack-scenario reset targets: 350
unique selected checkpoints: 15
unique workload ids: 30735
```

Workload id:

```text
{selected_key}::{candidate_id}::{pack_id}::{scenario_spec_id}
```

## Runner Decision

M2397 should implement:

```text
autodrift.paper_route_current_sim_dual_axis_effective_candidate_measured_validation
```

The adapter should reuse the existing rollout mechanics from:

```text
autodrift.paper_route_current_sim_scenario_task_family_measured_execution
autodrift.paper_route_current_sim_dual_axis_repaired_pack_measured_execution
```

Required reuse:

```text
load_actor_critic_checkpoint
build_env_config
ControllerProfileObservationWrapper / mask_spec_from_config
ActorPolicy
run_episode_with_policy
role success semantics
aggregate metric writers
finite metric completeness checks
claim-boundary writer
resume/run_state mechanics
```

The difference from M2362 is the workload source. M2362 used five repaired
packs with 72 scenario specs each. M2397 must flatten the M2391 effective
candidate config files and their `selected_scenario_specs`, preserving
candidate metadata on every episode row.

## Seed Rule

Use:

```text
eval_seed_base: 239700
eval_seed =
  eval_seed_base
  + selected_checkpoint_index * 100000
  + effective_candidate_scenario_index
```

`effective_candidate_scenario_index` is the stable row index in
`effective_candidate_scenario_rows.csv` after sorting by:

```text
candidate_id
pack_id
scenario_spec_id
```

This makes every selected-checkpoint/candidate-scenario cell deterministic
without depending on Python object ordering.

## Required Episode Metadata

Each episode row must preserve at least:

```text
workload_id
effective_candidate_scenario_index
candidate_id
candidate_index
effective_candidate_config_path
source_candidate_config_path
source_repair_spec_id
repair_family
priority_tier
source_slice_axis
source_slice_value
selected_scenario_count
selected_base_pack_count
pack_id
pack_index
pack_path
scenario_spec_id
scenario_family_id
role_family
sampled_obstacle_label
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
actor_contract_id
include_privileged_params
wheel_observation_mode
obstacle_relative_velocity_mode
history_length
profile_name
seed_id
matrix_id
selected_checkpoint_path
selected_checkpoint_step
selected_checkpoint_kind
eval_seed
outcome_bucket
success
collision
off_track
termination_reason
return
steps
min_clearance_margin
max_off_track_overshoot
time_to_first_off_track_s
high_sideslip_fraction
action_rate_mean
```

All rows must keep:

```text
actor_contract_id: P0_human_view_no_wheel_no_oracle
include_privileged_params: false
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
history_length: 1
```

## Required Outputs

M2397 should write:

```text
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/episode_rows.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/failure_rows.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/validation_failure_rows.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/metadata_missing_rows.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/metric_completeness_failures.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/claim_boundary.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/run_state.json
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_candidate.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_candidate_profile.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_candidate_pack.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_repair_family.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_source_slice_axis.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_source_slice_value.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_pack.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_role_family.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_scenario_family.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_profile_seed.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_profile.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_obstacle_label.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_timing_bucket.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_lateral_bucket.csv
runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_hidden_dynamics_bucket.csv
```

## Metrics

Use the existing M2362/M2293 metric semantics:

```text
success_count / success_rate
collision_count / collision_rate
offtrack_count / offtrack_rate
max_step_noncompletion_count / rate
other_failure_count / rate
mean_return
mean_steps
mean_min_clearance_margin
min_min_clearance_margin
mean_max_off_track_overshoot
mean_time_to_first_off_track_s
mean_high_sideslip_fraction
mean_action_rate_mean
termination_reason histogram
outcome_bucket histogram
```

All aggregate tables are diagnostic only. They can localize failure modes and
candidate effects, but M2397 must not rank candidates, profiles, or controller
families.

## Pass Criteria For M2397

M2397 measured validation passes only if:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_validation_pass
source_candidate_count: 54
candidate_scenario_reference_count: 2049
selected_checkpoint_count: 15
target_episode_count: 30735
episode_count: 30735
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

A high collision/offtrack rate does not fail the runner. It is measured outcome
evidence for the next audit. Runner failure is about incomplete execution,
invalid metadata, metric artifacts, lineage violations, contract violations, or
forbidden claims.

## Claim Boundary

Admissible after M2397 completion:

```text
M2397 completed a bounded closed-loop measured-validation panel over the
M2394 reset-ready effective candidate artifacts.
```

Not admissible in M2397:

```text
effective candidate ranking
controller family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
training repair success
current-sim verdict
```

Those require a separate result audit, outcome localization, and eventually a
paper-route comparison protocol.

## Failure Taxonomy

Use:

```text
scenario_sampling_failure
metric_artifact
lineage_invalid
contract_violation
behavior_regression
training_instability
```

Expected interpretation:

- `scenario_sampling_failure`: candidate scenario rows cannot be loaded, reset,
  or sampled despite M2394 evidence.
- `metric_artifact`: rows execute but required metrics are missing, non-finite,
  mislabeled, or confused with reset readiness.
- `lineage_invalid`: episode rows cannot be traced back to candidate/pack/spec
  and selected checkpoint inputs.
- `contract_violation`: actor input or env metadata violates the P0 human-view
  no-wheel/no-oracle boundary.
- `behavior_regression`: measured outcomes show a closed-loop degradation to be
  audited in the result audit, not interpreted during implementation.
- `training_instability`: reserved for checkpoint/model loading or policy
  execution instability, not training in M2397.

## Decision

Decision:

```text
effective_candidate_measured_validation_design_admit_implementation
```

Next milestone:

```text
m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation
```

M2397 should implement and run the measured-validation adapter. It should not
rank, select a winner, execute repair, train, or claim paper/self-ID/current-sim
verdicts.
