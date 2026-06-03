# M2464 Paper-Route Current-Sim Dual-Axis Scenario-Quality Concrete Overlay Reset Validation Implementation

- status: completed
- result_class: `scenario_quality_concrete_overlay_reset_validation_fail`
- manifest: `experiments/manifests/m2464-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation.py`
- summary: `runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/summary.json`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: reset attempted only; rollout/policy action/scenario-redesign execution/repair/training/replay/PPO `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Result

M2464 implemented and ran the M2463 reset-only validator for the six M2461
concrete-overlay stable/AES rows. Static validation and effective config
materialization both passed, then the validator stopped after environment
reset attempts.

```text
result_class: scenario_quality_concrete_overlay_reset_validation_fail
source_result_class: scenario_quality_concrete_overlay_materialization_preflight_pass
target_reset_count: 6
static_validation_pass_count: 6
static_validation_failure_count: 0
effective_env_config_written_count: 6
effective_env_config_outside_run_dir_count: 0
environment_load_attempt_count: 6
environment_reset_attempt_count: 6
environment_reset_success_count: 4
environment_reset_failure_count: 2
guardrail_violation_count: 1
failure_types_observed: scenario_sampling_failure
```

Target families:

```text
R0_stable_avoidable / stable_feasibility_support: 3 reset successes out of 3
R1_aeb_infeasible_stable_aes / stable_aes_support: 1 reset success out of 3
```

The two failed reset rows are both stable-AES overlay targets:

```text
m2464_reset_target_004 / m2455_stable_aes_support_001:
  RuntimeError: failed to sample an obstacle scenario matching the configured filters

m2464_reset_target_006 / m2455_stable_aes_support_003:
  RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

## Interpretation

The result is a clean reset-sampling failure, not a driver-performance result.
M2464 proves that the six rows can be joined, statically checked, converted to
temporary effective env configs under the run dir, and loaded for reset
attempts under the P0 human-view contract. It does not prove the R1 stable-AES
overlay family is reset-compatible for all admitted seeds: two of the three R1
rows fail during obstacle scenario sampling.

No repair, overlay tuning, retry policy, or measured rollout is executed in
M2464. The next step must be a result audit that decides whether to design a
bounded R1 overlay/sampler repair, branch-synthesize, or stop.

## Boundary Checks

The execution boundary held:

```text
environment_step_count: 0
policy_action_executed: false
environment_rollout_started: false
measured_rollout_started: false
active_config_overwrite_count: 0
labels_enter_actor_input_count: 0
actor_input_contract_changed_count: 0
repair_execution_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
ranking_admissible_count: 0
winner_selected_count: 0
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
scenario_redesign_executed_claim_made: false
training_repair_success_claim_made: false
current_sim_verdict_claim_made: false
```

The successful reset rows preserved the expected observation contract:

```text
observation_finite_count: 4
observation_dimension_failure_count: 0
obstacle_initialized_count: 4
expected_observation_dim: 72
```

## Commands

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation.py
3 passed
```

Reset-only validation:

```text
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation --m2461-dir runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight --output-dir runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation --target-reset-count 6 --expected-observation-dim 72 --eval-seed-base 246400 --next-blocker m2465-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-result-audit
```

## Decision

Accepted next route:

```text
m2465-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-result-audit
```

M2465 must audit M2464 before any overlay repair, sampler repair, reset retry,
measured rollout, policy action, scenario redesign execution, repair execution,
training, ranking, winner selection, paper/FW-vs-GRU/self-ID/training-repair
verdict, or current-sim verdict route.
