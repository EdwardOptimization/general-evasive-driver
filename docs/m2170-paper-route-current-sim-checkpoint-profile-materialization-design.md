# M2170 Paper-Route Current-Sim Checkpoint/Profile Materialization Design

- status: completed
- decision: `current_sim_checkpoint_profile_materialization_design_admit_implementation`
- real M2151 measured execution in M2170: `false`
- policy actions executed in M2170: `false`
- checkpoint training in M2170: `false`
- replay/PPO in M2170: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2169 closed the measured-runner schema blocker and left one active readiness
blocker:

```text
checkpoint_path_missing_count == 320
profile_ready_count == 0
```

M2170 converts that blocker into a fair checkpoint/profile materialization
route. This milestone does not train or run measured execution.

## Profile Matrix

The current-sim comparison uses the exact 8-profile matrix from M2151:

| Profile | Level | Encoder | Env history | Actor history | Observation dim | Training role | Checkpoint source |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `L0_current_masked` | `L0_current_observation` | `mlp` | 1 | 1 | 72 | train | own checkpoint |
| `L1_one_step` | `L1_one_step_feedback` | `mlp` | 1 | 1 | 72 | train | own checkpoint |
| `L2_window_13` | `L2_finite_window` | `temporal_gru` | 13 | 13 | 936 | train | own checkpoint |
| `L2_window_25` | `L2_finite_window` | `temporal_gru` | 25 | 25 | 1800 | train | own checkpoint |
| `L2_window_50` | `L2_finite_window` | `temporal_gru` | 50 | 50 | 3600 | train | own checkpoint |
| `L2_window_100` | `L2_finite_window` | `temporal_gru` | 100 | 100 | 7200 | train | own checkpoint |
| `L3_online_gru` | `L3_online_gru` | `human_view_online_gru` | 1 | 1 | 72 | train | own checkpoint |
| `L3_reset_control` | `L3_online_gru_reset_control` | `human_view_online_gru` | 1 | 1 | 72 | no separate training | alias to `L3_online_gru` |

`L3_reset_control` must reuse the `L3_online_gru` weights. Its only intended
difference is evaluation-time hidden-state reset, so training a separate
checkpoint would confound the reset-control comparison.

## Frozen Training Commands

M2171 may run only the following 7 trainable profile commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l0_current_masked_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L0_current_masked \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L0_current_masked/checkpoint.pt \
  --device cpu

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l1_one_step_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L1_one_step \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L1_one_step/checkpoint.pt \
  --device cpu

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l2_window_13_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L2_window_13 \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_13/checkpoint.pt \
  --device cpu

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l2_window_25_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L2_window_25 \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_25/checkpoint.pt \
  --device cpu

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l2_window_50_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L2_window_50 \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_50/checkpoint.pt \
  --device cpu

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l2_window_100_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L2_window_100 \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_100/checkpoint.pt \
  --device cpu

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/paper_route_profiles/m1190_l3_online_gru_smoke.json \
  --run-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profiles/L3_online_gru \
  --save runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L3_online_gru/checkpoint.pt \
  --device cpu
```

All commands must use each profile config's frozen PPO budget:

```text
total_steps: 1024
rollout_steps: 64
num_envs: 2
update_epochs: 1
minibatch_size: 128
learning_rate: 0.0001
eval_episodes: 5
device: cpu
```

No profile-specific budget, seed, reward, environment, observation, or actor
input tuning is allowed.

## Materialization Output Policy

M2171 must write:

```text
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/claim_boundary.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/run_state.json
```

For the 7 trainable profiles, `checkpoint_path` must be the saved checkpoint
path from the corresponding frozen command.

For `L3_reset_control`, `checkpoint_path` must equal the resolved
`L3_online_gru` checkpoint path, and the profile row must record:

```text
checkpoint_source_profile_name = L3_online_gru
checkpoint_materialization_mode = alias_same_weights_reset_hidden_control
training_started_for_profile = false
```

The materialized workload must preserve all original M2151 workload fields and
replace only the empty `checkpoint_path` cells.

## Pass Criteria

M2171 passes only if:

```text
profile_count == 8
trainable_profile_count == 7
alias_profile_count == 1
training_command_count == 7
successful_training_command_count == 7
checkpoint_path_present_count == 320
checkpoint_path_missing_count == 0
checkpoint_path_exists_count == 320
materialized_workload_count == 320
profile_specific_tuning == false
controller_family_ranking_claim_made == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
environment_rollout_started_for_measured_execution == false
policy_action_executed_for_measured_execution == false
guardrail_violation_count == 0
```

Training rollouts are allowed in M2171 only for checkpoint creation. Measured
execution over the M2151 workload is still forbidden.

## Failure Criteria

M2171 must fail closed if:

```text
any trainable profile checkpoint is missing;
any trainable profile command fails;
the reset-control profile trains its own weights;
any workload row still has an empty checkpoint_path;
any checkpoint_path points to a nonexistent file;
any actor input contract changes;
any profile-specific tuning appears;
any measured execution starts;
any ranking, winner, paper-level, finite-window-vs-GRU, or self-ID claim is made.
```

## Claim Boundary

Allowed claim after M2171:

```text
The current-sim comparison panel has materialized checkpoints for all 8 profile
rows and a workload with non-empty existing checkpoint paths.
```

Still not allowed:

```text
driver performance;
controller-family ranking;
which history representation is best;
paper-level benchmark result;
finite-window vs GRU verdict;
level3 self-identification.
```

## Next Step

M2171 should implement the checkpoint/profile materialization runner and run the
frozen materialization procedure. If it passes, M2172 must audit the result
before any real measured execution command is designed.
