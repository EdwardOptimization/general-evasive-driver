# M1927 Executable V2 Task-Quality Scenario Redesign Materialization Command Design

- status: completed
- decision: `task_quality_scenario_materialization_command_design_route_to_focused_materializer`
- branch: `paper_route_task_quality_scenario_redesign`
- subset config: `configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json`
- template source: `configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json`
- accepted cells: `runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution/support_first_accepted_cells.csv`
- reset/rollout/measured execution in M1927: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Compatibility Decision

M1927 does not execute materialization. It audits the command route.

Existing materializers are not exact fits:

```text
src/autodrift/controller_family_executable_workload_materialization_preflight.py
  expects historical M1680 task_source_specs with task_family/source_family
  endpoint metadata. M1926 selected_sources are scenario-quality source rows and
  do not carry that schema.

src/autodrift/executable_v2_support_first_task_quality_repair_axis_materialization.py
  expects measured episode rows and repair-axis variants. M1926 is source-only
  and must not depend on prior measured outcome rows.

src/autodrift/metric_specific_bounded_panel_materialization_preflight.py
  expects metric-specific bounded-panel artifacts, not the task-quality
  scenario-redesign template.
```

Therefore M1928 should implement a focused no-rollout materializer for the
M1926 subset. This is better than forcing old tools through ad hoc field
translation because the subset needs to join three explicit artifacts:

```text
1. selected source IDs from M1926 subset config;
2. full scenario-template metadata from M1921 640-row template;
3. representative accepted obstacle cells from M1923 source mining.
```

## M1928 Command

M1928 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_scenario_redesign_materialization_preflight \
  --subset-config configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json \
  --template configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json \
  --accepted-cells runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution/support_first_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight \
  --next-blocker m1929-executable-v2-task-quality-scenario-redesign-materialization-result-audit
```

This command is no-rollout materialization only. It must not run environment
reset, environment rollout, policy action, measured execution, training, replay,
PPO, promotion, controller-family ranking, paper-level claims, or level3
self-ID claims.

## Representative Accepted Cell Rule

For each selected source, M1928 should choose exactly one representative
accepted cell from M1923 accepted cells.

Join keys:

```text
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
```

Selection rule:

```text
filter accepted == true
filter selected candidate_source_id
sort deterministically by:
  tier_a_positive_support_sanity / tier_b_feasible_emergency:
    threshold_score descending, obstacle_distance descending,
    obstacle_half_width ascending, candidate_source_id
  tier_c_boundary_near_miss / tier_d_handling_limit_drift_required:
    threshold_score ascending, obstacle_distance ascending,
    obstacle_half_width descending, candidate_source_id
  tier_e_mitigation_only:
    obstacle_distance ascending, obstacle_half_width descending,
    threshold_score ascending, candidate_source_id
take first row
```

Rationale:

- Tier A/B should remain positive-support sanity and feasible-emergency rows,
  so the representative cell should not be the most fragile boundary cell.
- Tier C/D should stay near boundary/handling-limit, so the representative
  cell should be as close as possible to the feasibility threshold.
- Tier E remains mitigation-only and must be reported separately, not ranked as
  success/failure against avoidable tiers.

If any selected source has no accepted cell, M1928 must fail closed and write
the missing source to `unmappable_sources.csv`.

## Target Artifacts

M1928 should write:

```text
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/summary.json
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.csv
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/profile_artifacts.csv
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/selected_accepted_cells.csv
runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/unmappable_sources.csv
```

## Target Counts

M1928 pass gates:

```text
selected_source_count == 80
executable_spec_count == 80
selected_accepted_cell_count == 80
workload_cell_count == 960
profile_count == 12
expected_profile_count == 12
unmappable_source_count == 0
missing_profile_artifact_count == 0
contract_violation_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
paper_holdout_used == false
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

## Executable Spec Contract

Each executable spec should include:

```text
task_source_id
candidate_source_id
source_v1_bounded_panel_spec_id
source_scenario_spec_id
feasibility_tier_id
source_role_semantics
source_split
surface_variant
speed_ref
mu
obstacle_distance
obstacle_half_width
label
threshold_score
target_support_mode
target_boundary_mode
selected_accepted_cell_rule
env_config
contract_checks
```

The `env_config` must satisfy the existing human-view deployment contract:

```text
history_length == 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
```

No hidden dynamics parameter, oracle feasibility label, controller mode, TTC,
path/reference field, wheel/slip field, success/collision/progress label, or
precomputed answer may enter actor input. Labels and tiers remain artifact
metadata only.

## Workload Matrix Contract

The workload matrix should cross every executable source with the existing
12-profile public controller-family pilot:

```text
runs/m1674_controller_family_one_seed_public_pilot
```

Expected profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

This is still workload materialization, not ranking. The rows may include
profile names and checkpoint paths, but no metric comparison or promotion
decision.

## Next

Next milestone:

```text
m1928-executable-v2-task-quality-scenario-redesign-materialization-preflight-implementation
```

M1928 should implement the focused materializer, tests, and no-rollout
preflight output. It should not execute reset, rollout, measured policy actions,
training, replay, PPO, ranking, paper-level claims, or level3 self-ID claims.
