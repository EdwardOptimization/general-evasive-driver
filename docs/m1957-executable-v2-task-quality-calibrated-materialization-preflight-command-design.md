# M1957 Executable V2 Task-Quality Calibrated Materialization Preflight Command Design

- status: completed
- decision: `task_quality_calibrated_materialization_preflight_design_admit_focused_implementation`
- branch: `paper_route_task_quality_calibrated_materialization`
- parent selector: `docs/m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation.md`
- subset config: `configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json`
- accepted cells: `runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv`
- reset/rollout/measured execution in M1957: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M1957 designs the no-reset materialization/preflight command that should turn
the M1956 source-only subset into executable task specs and a 12-profile planned
workload. It does not run reset, rollout, measured execution, policy actions,
training, replay, PPO, or ranking.

The exact target remains:

```text
selected sources: 80
representative executable task specs: 80
controller profiles: 12
planned workload cells: 960
```

## Schema Decision

Do not reuse the M1928 materialization preflight directly.

The M1928 preflight is tied to the older M1925/M1926 scenario-redesign schema:

- it expects selected source rows from
  `configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json`;
- it joins against `configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json`;
- it consumes M1923 source-mining accepted cells;
- it expects old fields such as `feasibility_tier_id` and `surface_variant`.

The M1956 subset is a calibrated repair-wave schema:

- selected rows carry `repair_source_kind`, `selection_quota_name`,
  `parent_feasibility_tier_id`, `parent_surface_variant`, and
  `normalized_surface_variant`;
- source rows are already materialized from M1952 repair-source rows;
- accepted cells must come from the M1952 calibrated source-mining artifact;
- offtrack-relief rows use `relief_surface_unspecified` as a normalized
  materialization surface.

Therefore M1958 should implement a focused preflight adapter rather than bending
the M1928 preflight around a non-matching schema.

## M1958 Command

M1958 should implement:

```text
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_materialization_preflight \
  --subset-config configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json \
  --repair-accepted-cells runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight
```

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_calibrated_materialization_preflight.py
```

## Representative Cell Rule

M1958 should select one representative accepted cell for each selected source.
The selector must only use M1952 accepted-cell rows for the same
`candidate_source_id`.

Recommended deterministic rule:

```text
stable_aeb:
  prefer largest threshold_score, then larger obstacle_distance, then smaller half_width

stable_aes_only:
  prefer smallest positive threshold_score, then smaller obstacle_distance, then larger half_width

drift_required_recovery:
  prefer smallest positive threshold_score, then smaller obstacle_distance, then larger half_width

unavoidable_mitigation:
  prefer smaller obstacle_distance, then larger half_width, then threshold_score
```

The exact ordering may be implemented as a small helper, but the output must
record `representative_cell_rule` for every executable task spec.

## Output Artifact Contract

M1958 should write:

```text
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/summary.json
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/materialization_failures.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/source_kind_aggregate.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/role_surface_aggregate.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/claim_boundary.csv
```

Each executable task spec should preserve:

```text
task_source_id
candidate_source_id
repair_candidate_id
repair_source_kind
selection_quota_name
source_role_semantics
parent_feasibility_tier_id
parent_surface_variant
normalized_surface_variant
source_split
speed_ref
mu
friction_step_enabled
friction_step_at
obstacle_distance
obstacle_half_width
sampled_obstacle_label
threshold_score
time_to_obstacle
time_after_friction_step
base_geometry_source
post_obstacle_track_width
representative_cell_rule
env_config
contract_checks
diagnostic_only_no_ranking_claim
```

Each workload row should cross one task spec with one controller profile and
preserve both source metadata and profile metadata. The workload must be a
planned workload only, not measured execution.

## M1958 Pass Gates

M1958 should pass only if:

```text
result_class == task_quality_calibrated_materialization_preflight_pass
selected_source_count == 80
executable_task_spec_count == 80
controller_profile_count == 12
planned_workload_cell_count == 960
missing_accepted_cell_count == 0
duplicate_task_source_id_count == 0
duplicate_workload_key_count == 0
forbidden_key_violation_count == 0
contract_violation_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
calibrated_anchor_selected_count == 32
calibrated_anchor_post_friction_step_selected_count == 16
calibrated_anchor_steady_surface_selected_count == 16
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Interpretation Boundary

Supported by M1957:

- a focused M1958 materialization/preflight adapter is required;
- target counts and pass gates are explicit;
- accepted-cell provenance and selected-source metadata must be preserved.

Unsupported by M1957:

- environment reset validity;
- measured rollout success;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation
```

M1958 should implement and run only the no-reset preflight adapter over the real
M1956/M1952 artifacts.
