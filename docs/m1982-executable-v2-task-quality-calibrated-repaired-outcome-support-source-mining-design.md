# M1982 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Source-Mining Design

- status: completed
- decision: `task_quality_calibrated_outcome_support_source_mining_design_admit_implementation`
- parent audit: `docs/m1981-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-result-audit.md`
- template artifact: `configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json`
- source-mining execution in M1982: `false`
- reset/rollout/measured execution in M1982: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1980/M1981 produced and audited a clean `192`-candidate no-rollout repair
template artifact. M1982 designs the bounded source-mining adapter that should
map those templates into accepted candidate cells before any materialization,
reset validation, measured execution, or controller-family ranking.

The blocker remains task quality:

```text
outcome_support_low_offtrack_and_collision_dominated
```

The design goal is not to make a ranking claim. It is to ask whether the new
repair templates have enough no-rollout source support to justify a later
materialization subset.

## Implementation Target

M1983 should add a focused adapter:

```text
src/autodrift/executable_v2_task_quality_calibrated_outcome_support_source_mining.py
tests/test_executable_v2_task_quality_calibrated_outcome_support_source_mining.py
```

It should reuse the existing no-reset source-mining semantics from:

```text
src/autodrift/executable_v2_support_first_source_mining.py
src/autodrift/executable_v2_task_quality_offtrack_support_repair_source_mining.py
```

but must treat `repair_axis` as first-class, because M1980 splits
`mitigation_isolation_check` into two different axes:

```text
collision_mitigation_relief: 32
mitigation_metric_isolation: 16
```

## Inputs

Required inputs:

```text
--repair-templates
  configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json

--executable-task-specs
  runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json

--output-dir
  runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining

--next-blocker
  m1984-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-result-audit
```

Optional artifact input:

```text
--anchor-fallback-geometry
  runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json
```

This optional input may be used only as artifact-provenanced fallback geometry
for offtrack-anchor stable-AEB rows when exact repaired executable specs cannot
resolve the parent geometry. Do not copy selected geometry constants into the
adapter as untracked magic constants.

## Template Normalization

Each M1980 template should be normalized into a source candidate by mapping:

```text
source_role_semantics        <- target_source_role_semantics
feasibility_tier_id          <- target_feasibility_tier_id
surface_variant              <- target_surface_variant
normalized_surface_variant   <- target_normalized_surface_variant
sampled_obstacle_label       <- target_sampled_obstacle_label
candidate_source_id          <- repair_candidate_id
source_v1_bounded_panel_spec_id <- repair_candidate_id
source_scenario_spec_id      <- repair_candidate_id + "_scenario"
```

All parent fields must be preserved, including:

```text
repair_axis
repair_source_kind
repair_source_family
parent_candidate_source_id
parent_task_source_id
parent_profile_name
parent_repair_source_kind
parent_feasibility_tier_id
parent_source_role_semantics
parent_normalized_surface_variant
parent_sampled_obstacle_label
parent_base_geometry_source
parent_outcome_bucket
parent_termination_reason
source_split
```

## Geometry Resolution

The adapter should try geometry in this order:

1. exact repaired executable spec match by `parent_task_source_id`;
2. exact repaired executable spec match by `parent_candidate_source_id`;
3. artifact-provenanced anchor fallback for stable-AEB offtrack anchors;
4. deterministic tier/role/surface fallback for remaining unresolved rows.

M1983 must report geometry provenance with `base_geometry_source` so the audit
can identify which support came from exact repaired specs versus fallback.

Expected exact-resolution pattern from the M1980 artifact:

```text
success_support_expansion: 48 / 48 exact repaired spec matches
offtrack_anchor_relief: 0 / 64 exact matches, requires fallback
offtrack_boundary_relief_extension: 0 / 32 exact matches, requires fallback
collision_mitigation_relief: 0 / 32 exact matches, requires fallback
mitigation_metric_isolation: 0 / 16 exact matches, requires fallback
```

## Axis Scan Windows

M1983 should define axis-level scan windows rather than only
`repair_source_kind` windows:

```text
offtrack_anchor_relief:
  center = resolved obstacle distance/half-width plus template deltas
  distance radius/count = 4.0 / 9
  half-width radius/count = 0.15 / 7
  min accepted cells = 3

offtrack_boundary_relief_extension:
  distance radius/count = 5.0 / 11
  half-width radius/count = 0.20 / 7
  min accepted cells = 3

success_support_expansion:
  distance radius/count = 2.0 / 7
  half-width radius/count = 0.10 / 5
  min accepted cells = 2

collision_mitigation_relief:
  distance radius/count = 2.0 / 5
  half-width radius/count = 0.15 / 5
  min accepted cells = 1

mitigation_metric_isolation:
  distance radius/count = 1.0 / 3
  half-width radius/count = 0.05 / 3
  min accepted cells = 1
```

`mitigation_metric_isolation` is diagnostic support, not obstacle-pass ranking
support. It should be carried to later metrics as mitigation diagnostics, not
promoted as a controller-family ranking row.

## Outputs

M1983 should write:

```text
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/summary.json
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_blocked_rows.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/resolution_failure_rows.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/repair_axis_aggregate.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/split_aggregate.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/role_surface_aggregate.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/claim_boundary.csv
```

The accepted-cell output must preserve:

```text
repair_candidate_id
repair_axis
repair_source_kind
repair_source_family
source_split
source_role_semantics
feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
base_geometry_source
post_obstacle_track_width
obstacle_distance
obstacle_half_width
label
threshold_score
time_to_obstacle
time_after_friction_step
accepted
reject_reason
```

## Pass Gates

M1983 should pass only if:

```text
result_class == task_quality_calibrated_outcome_support_source_mining_pass
input_template_count == 192
source_candidate_count == 192
resolution_failure_count == 0
accepted_cell_count_total > 0
supported_source_count >= 96
public_gate_supported_source_count >= 32

offtrack_anchor_relief_supported_source_count >= 32
offtrack_boundary_relief_extension_supported_source_count >= 8
success_support_expansion_supported_source_count >= 24
collision_mitigation_relief_supported_source_count >= 8
mitigation_metric_isolation_source_count == 16

labels_enter_actor_input_count == 0
v2_ranking_admissible_by_default_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0

environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If M1983 fails, M1984 must audit the failure. Do not immediately lower support
floors or proceed to materialization.

## Command

M1983 should run:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_outcome_support_source_mining \
  --repair-templates configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json \
  --executable-task-specs runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json \
  --anchor-fallback-geometry runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json \
  --output-dir runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining \
  --next-blocker m1984-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-result-audit
```

This command is no-rollout source mining only. It must not reset environments,
execute policy actions, run measured rollouts, train, replay, PPO, rank
controllers, or use private holdout.

## Supported Claims

M1982 supports:

- the M1980 template artifact can move to a bounded no-rollout source-mining
  implementation;
- the required input schema, geometry resolution order, scan windows, output
  schema, and pass gates are explicit;
- ranking, paper-level evidence, reset validity, and self-ID claims remain
  blocked.

M1982 does not support:

- source-mining success;
- executable scenario validity;
- reset validity;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1983-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-implementation
```

M1983 should implement the adapter, run the no-rollout source-mining command,
and route the result to M1984 audit.
