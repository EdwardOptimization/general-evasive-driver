# M2228 Paper-Route Current-Sim Matched-Budget Profile Training Config Materialization Result Audit

- status: completed
- decision: `current_sim_matched_budget_profile_training_config_audit_admit_execution_command_design`
- manifest: `experiments/manifests/m2228-paper-route-current-sim-matched-budget-profile-training-config-materialization-result-audit.json`
- parent result: `runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/summary.json`
- parent matrix: `runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv`

## Audit Checks

M2228 audits M2227 artifacts only. It does not run reset, rollout, measured
execution, replay, PPO, training, or policy actions.

Required checks:

- M2227 result_class: `current_sim_matched_budget_profile_training_config_materialization_pass`
- generated_config_count: `15`
- expected_config_count: `15`
- training_matrix_row_count: `15`
- trainable_profile_count: `5`
- trainable profiles: `L0_current_masked`, `L1_one_step`, `L2_window_25`, `L2_window_50`, `L3_online_gru`
- seed_ids: `222601`, `222602`, `222603`
- seeds_per_profile: `3`
- budget_signature_count: `1`
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
- finite_window_vs_gru_conclusion_made: `false`
- paper_level_claim_made: `false`
- level3_self_id_claim_made: `false`

The training matrix contains exactly `15` rows with profiles:

```text
L0_current_masked
L1_one_step
L2_window_25
L2_window_50
L3_online_gru
```

and seeds:

```text
222601
222602
222603
```

All matrix rows share one budget signature over:

```text
total_steps=8192
rollout_steps=128
num_envs=4
update_epochs=2
minibatch_size=256
learning_rate=0.0001
clip_coef=0.1
max_grad_norm=0.25
eval_episodes=32
```

The matrix contract modes are:

```text
input_contract=P0_human_view_no_wheel_no_oracle
wheel_observation_mode=none
obstacle_relative_velocity_mode=zero
```

## Naming Note

The M2227 command matrix freezes `training_output_root` as:

```text
runs/m2228_paper_route_current_sim_matched_budget_profile_training_execution
```

That path is a frozen command output root from the M2227 materialization step.
It is not the M2228 audit artifact. M2229 must explicitly preserve or revise
the execution-root decision before any training command is run; it must not
silently rewrite budgets, profiles, seeds, or actor inputs.

## Decision

M2227 artifacts are clean enough to admit a separate training-execution command
design milestone.

This audit does not admit immediate training. The next milestone must freeze
the exact execution policy: command source, output-root handling, run order,
failure behavior, CPU/GPU/device handling, logging, and post-training quality
floors. Ranking, finite-window-vs-GRU conclusions, paper-level claims, and
level3 self-identification claims remain blocked.

## Next

Pre-register:

```text
m2229-paper-route-current-sim-matched-budget-profile-training-execution-command-design
```

M2229 should design the execution command only. The actual training run should
remain a separate admitted milestone.
