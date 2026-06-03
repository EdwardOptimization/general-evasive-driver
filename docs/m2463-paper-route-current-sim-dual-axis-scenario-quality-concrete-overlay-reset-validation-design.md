# M2463 Paper-Route Current-Sim Dual-Axis Scenario-Quality Concrete Overlay Reset Validation Design

- status: completed
- decision: `concrete_overlay_reset_validation_design_admit_reset_only_implementation`
- manifest: `experiments/manifests/m2463-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-design.json`
- parent synthesis: `docs/m2462-paper-route-current-sim-dual-axis-scenario-quality-discriminant-branch-synthesis.md`
- parent preflight: `runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/summary.json`
- reset/rollout/policy action in M2463: `false`
- measured execution in M2463: `false`
- repair/training/replay/PPO in M2463: `false`
- ranking/winner selection in M2463: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2463 freezes a reset-only validation route for the six M2461 concrete-overlay
stable/AES rows. It does not run reset validation. M2464 may instantiate and
reset environments only if it follows the exact scope below.

Target workload:

```text
target_reset_count: 6
source_preflight_rows: 6 static_then_reset rows
source_overlay_rows: 6
expected_observation_dim: 72
eval_seed_base: 246400
environment_step_count: 0
policy_actions: 0
```

M2464 is a scenario-spec admissibility check. Passing reset validation would
mean the six concrete overlay rows can load/reset under the current simulator
and human-view actor contract. It would not mean driver performance improved,
actual success improved, scenario redesign was executed, repair/training worked,
or current-sim/paper/self-ID verdict evidence exists.

## Source Inputs

M2464 must read:

```text
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/summary.json
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/concrete_overlay_rows.csv
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/candidate_rows_with_overlays.csv
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/adapter_preflight_work_items.csv
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/adapter_reset_check_rows.csv
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/guardrail_rows.csv
runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight/claim_boundary.csv
```

Admission requires:

```text
M2461 result_class == scenario_quality_concrete_overlay_materialization_preflight_pass
M2461 target_preflight_row_count == 6
M2461 concrete_overlay_row_count == 6
M2461 adapter_concrete_overlay_available_count == 6
M2461 adapter_static_check_fail_count == 0
M2461 adapter_reset_attempted_count == 0
M2461 guardrail_violation_count == 0
```

If any admission check fails, M2464 must stop before environment loading and
route to result/failure audit.

## Target Rows

M2464 reset targets are exactly the six adapter preflight rows with:

```text
candidate_group in {stable_feasibility_support, stable_aes_support}
preflight_lane == static_then_reset
static_check_required == True
reset_check_required == True
concrete_overlay_required == True
concrete_overlay_available == True
env_config_overlay_json nonempty
blocked_reason empty
```

Expected role split:

```text
stable_feasibility_support / R0_stable_avoidable: 3
stable_aes_support / R1_aeb_infeasible_stable_aes: 3
```

M2464 must join each target to exactly one M2461 `concrete_overlay_rows.csv`
row by:

```text
preflight_id
source_candidate_id
candidate_group
env_config_overlay_json
```

The joined overlay JSON must use only the M2460 allowed overlay keys already
recorded in `allowed_overlay_keys`. Labels such as `aeb_feasible` and
`aes_feasible` remain environment sampling metadata only; they must not enter
actor input.

## Effective Reset Config

M2461 overlays are partial environment overlays, not full scenario configs.
M2464 must build temporary effective reset configs under its output directory:

```text
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/effective_env_configs/*.json
```

Each effective config is:

```text
base_human_view_contract_env_config + env_config_overlay_json
```

Base human-view contract values:

```text
history_length: 1
action_history_mode: full
include_privileged_params: false
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
```

The implementation should construct the simulator config with
`build_env_config(merge_env_config(base_contract, overlay))`. It must not
overwrite active configs or write effective configs outside the M2464 run
directory.

Actor-contract static checks must confirm:

```text
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
history_length == 1
action_history_mode == full
obstacle.enabled == true
labels_enter_actor_input == false
actor_input_contract_changed == false
scenario_redesign_executed == false
policy_action_executed == false
repair_execution_started == false
training_started == false
ranking_admissible == false
winner_selected == false
```

## M2464 Command

M2464 should implement and run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation.py

PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation \
  --m2461-dir runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight \
  --output-dir runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation \
  --target-reset-count 6 \
  --expected-observation-dim 72 \
  --eval-seed-base 246400 \
  --next-blocker m2465-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-result-audit
```

The first command is the focused synthetic test. The second command may load
and reset environments. It must never call `env.step`, execute a policy action,
or start measured rollout.

## Expected Artifacts

M2464 must write:

```text
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/summary.json
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/static_validation_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/reset_target_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/effective_env_config_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/reset_validation_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/reset_failure_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/guardrail_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/claim_boundary.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/decision_rows.csv
runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/effective_env_configs/*.json
```

Each reset target row must include:

```text
reset_target_id
preflight_id
overlay_id
source_candidate_id
source_panel_id
candidate_group
role_scope
sampled_obstacle_label_scope
split
overlay_family
env_config_overlay_hash
effective_env_config_path
eval_seed
expected_observation_dim
```

Each reset validation row must include:

```text
reset_target_id
preflight_id
source_candidate_id
candidate_group
role_scope
environment_load_attempted
environment_reset_attempted
environment_reset_success
observation_length
expected_observation_length
observation_dimension_matches_expected
observation_finite
obstacle_initialized
obstacle_label
environment_step_count
policy_action_executed
environment_rollout_started
measured_rollout_started
repair_execution_started
training_started
replay_started
ppo_used
promoted
private_holdout_used
active_config_overwritten
actor_input_contract_changed
ranking_admissible
winner_selected
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
scenario_redesign_executed_claim_made
training_repair_success_claim_made
current_sim_verdict_claim_made
failure_type
failure_reason
```

## Pass Gates

M2464 passes only if:

```text
result_class == scenario_quality_concrete_overlay_reset_validation_pass
source_result_class == scenario_quality_concrete_overlay_materialization_preflight_pass
target_reset_count == 6
static_validation_pass_count == 6
static_validation_failure_count == 0
effective_env_config_written_count == 6
effective_env_config_outside_run_dir_count == 0
environment_load_attempt_count == 6
environment_reset_attempt_count == 6
environment_reset_success_count == 6
environment_reset_failure_count == 0
observation_finite_count == 6
observation_dimension_failure_count == 0
obstacle_initialized_count == 6
environment_step_count == 0
policy_action_executed == false
environment_rollout_started == false
measured_rollout_started == false
active_config_overwrite_count == 0
repair_execution_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed_count == 0
ranking_admissible_count == 0
winner_selected_count == 0
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
training_repair_success_claim_made == false
current_sim_verdict_claim_made == false
guardrail_violation_count == 0
```

If any reset fails, M2464 should still write all artifacts and route to the same
result audit with a failure result. It must not repair overlays and rerun inside
the same milestone.

## Failure Taxonomy

M2464 should classify failures as:

```text
lineage_invalid:
  missing or inconsistent M2461 source rows, duplicate joins, target count not
  six, or effective config path outside run dir.

contract_violation:
  actor-input guard failure, forbidden execution flag, active config overwrite,
  observation dimension failure, environment step count nonzero, policy action,
  rollout, training, ranking, or verdict claim.

scenario_sampling_failure:
  environment reset cannot sample a compatible obstacle scenario from the
  bounded overlay.

metric_artifact:
  any attempt to treat reset-only evidence, soft-boundary tolerance, or labels
  as actual success.

behavior_regression:
  reset succeeds but observation is non-finite or obstacle initialization is
  missing under the expected contract.
```

## Claim Boundary

M2464 may claim only:

```text
reset-only validation over six concrete overlay rows passed or failed.
```

Still blocked:

```text
driver performance improvement
measured actual success improvement
scenario redesign executed
repair execution or training repair success
support-policy/controller/checkpoint/scenario candidate ranking
winner selection
paper-level result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Decision

Accepted next route:

```text
m2464-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-implementation
```

M2464 should implement and run the reset-only validator above, then route to
`m2465-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-result-audit`.
