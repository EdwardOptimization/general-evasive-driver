# M2393 Paper-Route Current-Sim Dual-Axis Effective Candidate Reset Validation Adapter Design

- status: completed
- decision: `effective_candidate_reset_validation_adapter_design_admit_implementation`
- manifest: `experiments/manifests/m2393-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-design.json`
- parent synthesis: `docs/m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis.md`
- source summary: `runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json`
- environment load/reset/step in M2393: `0/0/0`
- policy action in M2393: `false`
- active config overwrite in M2393: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2393 designs a bounded reset-only validation adapter for the M2391 effective
candidate pack artifacts. It does not load or reset environments in M2393.

The key design rule is two-layer validation:

```text
candidate-scenario reference layer:
  validate all 2049 M2391 selected candidate-scenario references statically

unique reset target layer:
  reset each unique (pack_id, scenario_spec_id) env_config once
  current target unique reset count: 350
```

This avoids treating duplicate references as independent reset evidence while
still preserving candidate-level coverage.

## Source Inventory

M2394 should read:

```text
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/summary.json
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_materialization_manifest.json
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_scenario_rows.csv
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/claim_boundary.csv
runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs/*.json
```

Expected source counts:

```text
source_candidate_config_count: 54
effective_candidate_config_written_count: 54
effective_candidate_config_outside_run_dir_count: 0
candidate_without_matching_scenarios_count: 0
candidate_without_env_config_count: 0
actor_contract_violation_count: 0
selected_scenario_reference_count: 2049
unique_reset_target_count: 350
base_pack_count: 5
base_scenario_specs_per_pack_count: 72
```

## Static Adapter Checks

Before any environment construction, M2394 must verify:

```text
M2391 summary result_class is pass;
effective_candidate_config_rows.csv has 54 candidate rows;
effective_candidate_scenario_rows.csv has 2049 scenario-reference rows;
all effective_candidate_config_path values exist;
all effective_candidate_config_path values resolve under the M2391 run dir;
all candidate payload candidate_id values match rows;
each candidate payload selected_scenario_count matches scenario rows;
each selected scenario has env_config;
each selected scenario passes actor contract guardrails:
  actor_contract_id == P0_human_view_no_wheel_no_oracle
  include_privileged_params == false
  wheel_observation_mode == none
  obstacle_relative_velocity_mode == zero
  history_length == 1
all claim boundaries block environment step, policy action, repair execution,
training, ranking, winner selection, paper claims, self-ID claims, and
current-sim verdict claims.
```

If any static check fails, M2394 must stop before environment loading and write
a failure summary with:

```text
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_step_count: 0
policy_action_executed: false
```

## Reset Target Policy

M2394 should construct reset targets by deduplicating scenario references on:

```text
pack_id
scenario_spec_id
```

The reset target row should also include:

```text
candidate_ids_referencing_target
reference_count
env_config_hash
pack_path
scenario_family_id
role_family
source_slice_axes_referencing_target
```

Current expected reset target count:

```text
unique_reset_target_count: 350
```

This is the reset attempt budget. M2394 should not reset all 2049 references
independently unless the synthesis explicitly changes the duplicate policy.

## Future Reset-Only Scope

M2394 may instantiate environments only far enough to test config load and
reset compatibility for each unique reset target:

```text
target_reset_attempt_count: 350
environment_step_count: 0
policy_action_executed: false
```

Allowed future M2394 outputs:

```text
static_validation_rows.csv
reset_target_rows.csv
reset_validation_rows.csv
candidate_scenario_reset_rows.csv
effective_candidate_reset_summary_rows.csv
reset_failure_rows.csv
claim_boundary.csv
summary.json
```

Candidate-level status should be derived after unique reset targets are tested:

```text
candidate_reset_pass:
  all reset targets referenced by that candidate reset successfully

candidate_reset_fail:
  any reset target referenced by that candidate fails to load or reset
```

## Pass Gate For Future M2394

M2394 should pass only if:

```text
source_candidate_config_count: 54
effective_candidate_config_written_count: 54
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
static_validation_pass_count: 2049
static_validation_failure_count: 0
environment_load_attempt_count: 350
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
candidate_reset_pass_count: 54
candidate_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
active_config_overwrite_count: 0
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

M2394 must fail closed if:

```text
selected scenario metadata is inconsistent with effective candidate payloads;
unique reset target count differs from expected count without being reported;
any selected scenario lacks env_config;
any actor-contract guardrail fails;
any output path escapes the M2394 run dir;
any forbidden execution or claim flag is set.
```

## Claim Boundary

M2393 may claim only:

```text
A bounded reset-validation adapter has been designed for M2391 effective
candidate pack artifacts.
```

Still blocked:

```text
environment load/reset in M2393
environment rollout or measured execution
policy action
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

## Decision

Decision:

```text
effective_candidate_reset_validation_adapter_design_admit_implementation
```

Next milestone:

```text
m2394-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-implementation
```

M2394 may implement and run the reset-only adapter described above. It must not
step environments, execute policy actions, repair, train, rank, select a winner,
or make paper/self-ID/current-sim claims.
