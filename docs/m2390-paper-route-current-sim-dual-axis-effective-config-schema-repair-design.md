# M2390 Paper-Route Current-Sim Dual-Axis Effective Config Schema Repair Design

- status: completed
- decision: `effective_candidate_pack_schema_repair_route_to_materialization`
- manifest: `experiments/manifests/m2390-paper-route-current-sim-dual-axis-effective-config-schema-repair-design.json`
- parent audit: `docs/m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit.md`
- reset/rollout/measured execution in M2390: `false`
- candidate effective config materialization in M2390: `false`
- active config overwrite in M2390: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Finding

M2388 failed closed for the right reason but made a too-narrow schema
assumption:

```text
incorrect assumption:
  one M2385 candidate config should already contain one reset-ready env_config

actual artifact type:
  one M2385 candidate config is an overlay candidate:
    reward_overlay
    curriculum_overlay
    guardrail_overlay
    source_slice_axis/source_slice_value
```

The candidate overlays are valid repair artifacts, not standalone scenario
environment configs. The schema repair should therefore materialize effective
candidate pack artifacts by joining:

```text
M2385 candidate overlay
  + M2356 reset-valid repaired config pack lineage
  + matching scenario_specs selected by source_slice_axis/source_slice_value
```

It should not force a single `env_config` into each overlay file.

## Base Env Config Lineage

Legitimate base env config lineage exists:

```text
base pack manifest:
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json

base pack files:
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/baseline_reference_pack.json
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/g_primary_pack.json
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/h_primary_pack.json
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/g_h_primary_pack.json
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/gh_minimal_pack.json
```

This lineage is executable enough for reset-ready schema repair:

```text
M2356:
  repaired config pack manifest exists
  config_pack_count: 5
  scenario_specs_per_pack: 72
  active_config_overwritten: false

M2359:
  result_class: current_sim_dual_axis_repaired_pack_reset_validation_pass
  reset_attempt_count: 360
  reset_success_count: 360
  contract_violation_count: 0
  guardrail_violation_count: 0
  environment_rollout_started: false

M2362:
  result_class: current_sim_dual_axis_repaired_pack_measured_execution_pass
  episode_count: 5400
  config_pack_count: 5
  scenario_specs_per_pack_count: 72
  validation_failure_count: 0
  metadata_missing_count: 0
  metric_completeness_failure_count: 0
  guardrail_violation_count: 0
```

The base specs preserve the main actor contract:

```text
actor_contract_id: P0_human_view_no_wheel_no_oracle
include_privileged_params: false
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
history_length: 1
```

## Effective Candidate Pack Schema

M2391 should materialize one run-dir-only effective candidate artifact per
M2385 candidate. The artifact is a pack-scoped scenario selection plus overlays,
not a replacement for the active scenario config.

Required top-level fields:

```text
schema_version
candidate_id
source_repair_spec_id
repair_family
priority_tier
source_slice_axis
source_slice_value
source_candidate_config_path
base_pack_manifest_path
base_reset_validation_summary_path
base_measured_execution_summary_path
matching_rule
selected_scenario_specs
selected_scenario_count
selected_scenario_count_by_pack
reward_overlay
curriculum_overlay
guardrail_overlay
mixed_guarded_requirements
claim_boundary
guardrail_flags
```

Each selected scenario entry should include:

```text
pack_id
pack_path
scenario_spec_id
scenario_family_id
role_family
source_slice_axis
source_slice_value
match_values
env_config
actor_contract_id
include_privileged_params
wheel_observation_mode
obstacle_relative_velocity_mode
history_length
```

The full `env_config` should be copied from the selected M2356 scenario spec.
M2391 must not mutate the active config and must write only inside its run
directory.

## Matching Semantics

M2391 should match source slices against scenario metadata, not actor inputs.

Simple slice:

```text
source_slice_axis: hidden_dynamics_bucket
source_slice_value: slow_steer_actuator

match if:
  scenario_spec["hidden_dynamics_bucket"] == "slow_steer_actuator"
```

Composite slice:

```text
source_slice_axis: role_family+hidden_dynamics_bucket
source_slice_value: R5_hidden_dynamics_robustness|weak_brake

match if:
  scenario_spec["role_family"] == "R5_hidden_dynamics_robustness"
  and scenario_spec["hidden_dynamics_bucket"] == "weak_brake"
```

Fail closed if:

```text
axis/value arity differs
any axis is missing from a scenario spec
no matching scenario specs exist
any selected scenario lacks env_config
any selected env_config violates the actor contract guardrails
any output path escapes the M2391 run directory
```

A schema inventory during M2390 found that the current 54 M2385 candidates all
have at least one match across the five M2356 packs:

```text
candidate_count: 54
zero_match_candidate_count: 0
min_selected_scenario_count: 6
max_selected_scenario_count: 180
total_selected_scenario_references: 2049
```

This is only design-time inventory. M2391 must recompute it and write the
result as artifacts.

## M2391 Materialization Route

M2391 should implement and run an artifact-only materializer:

```text
input:
  M2385 candidate config generation run dir
  M2356 repaired config pack manifest

output:
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs/*.json
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_scenario_rows.csv
  runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/claim_boundary.csv
```

M2391 must not:

```text
load an environment
reset an environment
step an environment
execute a policy action
apply reward/curriculum overlays to active config
execute repair levers
train/replay/PPO
rank policies or controller families
select a winner
claim repair success, paper evidence, finite-window-vs-GRU conclusion,
level3 self-ID, scenario-redesign execution, or current-sim verdict
```

## Expected M2391 Pass Gate

M2391 should pass only if:

```text
source_candidate_config_count: 54
static_validation_pass_count: 54
effective_candidate_config_written_count: 54
effective_candidate_config_outside_run_dir_count: 0
candidate_without_matching_scenarios_count: 0
candidate_without_env_config_count: 0
base_pack_count: 5
base_scenario_specs_per_pack_count: 72
active_config_overwrite_count: 0
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_step_count: 0
policy_action_executed: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

If materialization fails, it should write a failure summary and route to a
result audit or schema repair. It must not silently relax matching or guardrail
requirements.

## Claim Boundary

M2390 may claim only:

```text
Effective candidate pack schema repair has been designed.
```

Still blocked:

```text
effective config materialization in M2390
candidate config loading or reset in M2390
environment rollout or measured execution
repair execution
training/replay/PPO
support-policy or controller-family ranking
winner selection
paper-level result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
training repair success
current-sim verdict
```
