# M2227 Paper-Route Current-Sim Matched-Budget Profile Training Config Materialization

- status: completed
- decision: `current_sim_matched_budget_profile_training_config_materialization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2227-paper-route-current-sim-matched-budget-profile-training-config-materialization.json`
- run artifact: `runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_matched_budget_profile_training_configs.py`
- focused tests: `2 passed`

## Result

M2227 materializes the M2226 matched-budget short-v0 training matrix without
starting training, reset, rollout, replay, PPO, measured execution, or policy
action execution.

Key summary fields:

- result_class: `current_sim_matched_budget_profile_training_config_materialization_pass`
- generated_config_count: `15`
- expected_config_count: `15`
- training_matrix_row_count: `15`
- trainable_profile_count: `5`
- trainable profiles: `L0_current_masked`, `L1_one_step`, `L2_window_25`, `L2_window_50`, `L3_online_gru`
- alias/control profile: `L3_reset_control`
- alias source profile: `L3_online_gru`
- seeds_per_profile: `3`
- seed_ids: `222601`, `222602`, `222603`
- budget_matched: `true`
- seed_policy_matched: `true`
- contract_violation_count: `0`
- guardrail_violation_count: `0`
- ranking_admissible_count: `0`
- winner_selected: `false`
- training_started: `false`
- environment_reset_started: `false`
- environment_rollout_started: `false`
- measured_rollout_started: `false`
- policy_action_executed: `false`
- replay_started: `false`
- ppo_started: `false`
- controller_family_ranking_claim_made: `false`
- finite_window_vs_gru_conclusion_made: `false`
- paper_level_claim_made: `false`
- level3_self_id_claim_made: `false`

Matched budget fields are identical across all generated trainable
profile/seed configs:

- total_steps: `8192`
- rollout_steps: `128`
- num_envs: `4`
- update_epochs: `2`
- minibatch_size: `256`
- learning_rate: `0.0001`
- clip_coef: `0.1`
- max_grad_norm: `0.25`
- eval_episodes: `32`
- device: `cpu`
- vector_env_mode: `sync`

Generated config directory:

```text
configs/paper_route_profiles/m2227_matched_budget_short_v0/
```

Run artifacts:

```text
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/summary.json
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/profile_plan.csv
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/claim_boundary.csv
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/run_state.json
```

The command matrix targets the future training output root:

```text
runs/m2228_paper_route_current_sim_matched_budget_profile_training_execution
```

## Interpretation

This is a config and command materialization result only. It does not provide
new policy performance evidence, controller-family ranking evidence,
finite-window-vs-GRU evidence, paper-level evidence, or level3
self-identification evidence.

The useful contribution is that the next training step now has deterministic,
contract-clean profile/seed configs and a command matrix with matched budgets.
Before running training, the artifacts should be audited to confirm the matrix
exactly preserves M2226 constraints and that the next command cannot silently
change profile-specific budgets.

## Next

Pre-register M2228 as a process audit over the M2227 result artifacts:

```text
m2228-paper-route-current-sim-matched-budget-profile-training-config-materialization-result-audit
```

M2228 should not train. It should decide whether the M2227 materialized configs
are clean enough to admit a separate training-execution command design.
