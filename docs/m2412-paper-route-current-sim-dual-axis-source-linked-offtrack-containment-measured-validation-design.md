# M2412 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Measured Validation Design

- status: completed
- decision: `source_linked_measured_validation_design_admit_implementation`
- manifest: `experiments/manifests/m2412-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-design.json`
- parent audit: `docs/m2411-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-result-audit.md`
- parent reset summary: `runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/summary.json`
- reset execution in M2412: `false`
- rollout/measured execution in M2412: `false`
- policy action executed in M2412: `false`
- repair execution/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2412 freezes a bounded measured-validation route for the M2410 source-linked
reset panel.

The goal is to produce a closed-loop measured artifact over the concrete env
configs that are both:

```text
source-linked to M2406 offtrack containment families
reset-valid in M2410
```

The goal is not to rank candidate families, select a winner, execute repair,
or prove current-sim success. The panel is a diagnostic measured-validation
step for the offtrack-dominated blocker inherited from M2397.

## Input Artifacts

Use these fixed inputs:

```text
source-linked reset summary:
  runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/summary.json

reset targets:
  runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/reset_target_rows.csv

family coverage:
  runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/source_linked_family_rows.csv

source-linked scenario refs:
  runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/source_linked_scenario_rows.csv

unmatched-key diagnostics:
  runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/unmatched_source_key_rows.csv

effective candidate env-config source:
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs/*.json

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

M2412 chooses the unique reset-target denominator:

```text
unique reset targets: 350
selected checkpoints: 15
measured episodes: 350 * 15 = 5250
```

The measured denominator is:

```text
reset_target_key + selected_checkpoint
```

This is intentionally different from M2397. M2397 used 2049
candidate-scenario references because each reference represented a distinct
effective-candidate hypothesis. M2410 source-linked scenario refs are
overlapping evidence links into the same concrete env configs. Using all 3505
refs as rollout units would repeatedly execute the same environment and could
turn family/source overlap into an implicit ranking weight.

Required uniqueness:

```text
unique reset_target_key count: 350
unique selected checkpoints: 15
unique workload ids: 5250
```

Workload id:

```text
{selected_key}::{reset_target_key}
```

## Family Membership

Family membership is overlapping and diagnostic. It is not a mutually exclusive
assignment.

Each reset target carries:

```text
family_ids
effective_candidate_ids
scenario_reference_count
```

M2413 should write one primary episode row per workload and a separate exploded
membership table:

```text
episode_family_membership_rows.csv
```

The membership table should contain one row per:

```text
workload_id + family_id
```

Allowed family aggregates:

```text
aggregate_by_family_membership.csv
aggregate_by_family_profile.csv
aggregate_by_family_pack.csv
```

These aggregates are diagnostic only. They must not rank families, select a
winner, or imply a family-specific repair succeeded.

## Env Config Reconstruction

M2410 did not write full env configs into `reset_target_rows.csv`; it only wrote
the reset target key and env-config hash. M2413 should reconstruct env configs
from the M2391 effective-candidate config payloads:

```text
load effective_candidate_configs/*.json
iterate selected_scenario_specs
compute reset_target_key = pack_id|scenario_spec_id|hash(env_config)[:16]
keep the env_config whose reset_target_key appears in M2410 reset_target_rows
```

If a reset target maps to multiple env configs with different hashes, fail
closed as `lineage_invalid`. If a reset target has no env config, fail closed
as `scenario_sampling_failure`.

## Seed Rule

Use:

```text
eval_seed_base: 241300
eval_seed =
  eval_seed_base
  + selected_checkpoint_index * 100000
  + reset_target_index
```

`reset_target_index` is the stable row index in `reset_target_rows.csv` after
sorting by:

```text
reset_target_key
```

This makes every selected-checkpoint/reset-target cell deterministic.

## Required Episode Metadata

Each episode row must preserve at least:

```text
workload_id
reset_target_index
reset_target_key
env_config_hash
pack_id
scenario_spec_id
family_ids
family_count
effective_candidate_ids
effective_candidate_count
scenario_reference_count
selected_checkpoint_index
selected_key
profile_name
seed_id
matrix_id
selected_checkpoint_path
selected_checkpoint_step
selected_checkpoint_kind
eval_seed
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

M2413 should write:

```text
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_family_membership_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/failure_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/validation_failure_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/metadata_missing_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/metric_completeness_failures.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/claim_boundary.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/run_state.json
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_reset_target.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_pack.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_role_family.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_scenario_family.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_profile_seed.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_profile.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_obstacle_label.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_timing_bucket.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_lateral_bucket.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_hidden_dynamics_bucket.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_family_membership.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_family_profile.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_family_pack.csv
```

## Metrics

Use the existing M2397/M2362 metric semantics:

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
show family-membership outcome slices, but M2413 must not rank families,
profiles, or controller families.

## Pass Criteria For M2413

M2413 measured validation passes only if:

```text
result_class: current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass
source_reset_target_count: 350
selected_checkpoint_count: 15
target_episode_count: 5250
episode_count: 5250
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

Admissible after M2413 completion:

```text
M2413 completed a bounded closed-loop measured-validation panel over the M2410
source-linked reset panel.
```

Not admissible in M2413:

```text
candidate family ranking
controller family ranking
support-policy ranking
winner selection
repair execution
scenario redesign executed
training repair success
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

Those require separate result audit, outcome localization, and paper-route
comparison protocols.

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

- `scenario_sampling_failure`: reset targets cannot be reconstructed, loaded,
  reset, sampled, or rolled out despite M2410 evidence.
- `metric_artifact`: rows execute but required metrics are missing, non-finite,
  mislabeled, or confused with reset readiness.
- `lineage_invalid`: episode rows cannot be traced back to reset target,
  selected checkpoint, family membership, and env-config hash inputs.
- `contract_violation`: actor input or env metadata violates the P0
  human-view no-wheel/no-oracle boundary.
- `behavior_regression`: measured outcomes show a closed-loop degradation to be
  audited in the result audit, not interpreted during implementation.
- `training_instability`: reserved for checkpoint/model loading or policy
  execution instability, not training in M2413.

## Decision

Decision:

```text
source_linked_measured_validation_design_admit_implementation
```

Next milestone:

```text
m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation
```

M2413 should implement and run the measured-validation adapter. It should not
rank, select a winner, execute repair, train, or claim paper/self-ID/current-sim
verdicts.
