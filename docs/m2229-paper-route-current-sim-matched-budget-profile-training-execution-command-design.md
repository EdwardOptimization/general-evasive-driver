# M2229 Paper-Route Current-Sim Matched-Budget Profile Training Execution Command Design

- status: completed
- decision: `current_sim_matched_budget_profile_training_execution_command_design_admit_implementation_and_run`
- manifest: `experiments/manifests/m2229-paper-route-current-sim-matched-budget-profile-training-execution-command-design.json`
- parent audit: `docs/m2228-paper-route-current-sim-matched-budget-profile-training-config-materialization-result-audit.md`
- parent matrix: `runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv`

## Design Decision

M2229 freezes the execution policy for the matched-budget profile training
panel. It does not run reset, rollout, replay, PPO, training, measured
execution, or policy actions.

The M2227 command matrix contains a frozen `training_output_root` path named:

```text
runs/m2228_paper_route_current_sim_matched_budget_profile_training_execution
```

M2229 chooses not to execute that path directly because M2228 is now the audit
milestone. The execution runner should instead treat the M2227 matrix as the
authoritative source for:

- `matrix_id`
- `profile_name`
- `seed_id`
- `generated_config_path`
- budget fields
- actor contract fields

and should remap only output paths to:

```text
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution
```

This is an output-root remap only. It must not change profiles, seeds, budgets,
actor inputs, environment configs, or PPO hyperparameters.

## Frozen Panel

Trainable profiles:

```text
L0_current_masked
L1_one_step
L2_window_25
L2_window_50
L3_online_gru
```

Seeds:

```text
222601
222602
222603
```

Expected runs:

```text
5 profiles x 3 seeds = 15 train_ppo runs
```

Matched budget per run:

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
device=cpu
vector_env_mode=sync
```

Contract gates before each run:

```text
input_contract=P0_human_view_no_wheel_no_oracle
include_privileged_params=false
wheel_observation_mode=none
obstacle_relative_velocity_mode=zero
uses_hidden_oracle_actor_inputs=false
uses_wheel_or_slip_inputs=false
uses_reference_or_ttc_inputs=false
```

## Execution Policy

M2230 should implement and run a focused execution adapter:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.paper_route_current_sim_matched_budget_profile_training_execution \
  --training-matrix runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv \
  --output-dir runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution \
  --execution-root runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution \
  --device cpu \
  --fail-fast
```

The adapter should run the 15 matrix rows in deterministic order:

```text
profile_name asc, seed_id asc
```

For each row it should run:

```text
python -m autodrift.train_ppo \
  --config <generated_config_path> \
  --run-dir <execution_root>/profiles/<profile_name>/seed_<seed_id> \
  --save <execution_root>/checkpoints/<profile_name>/seed_<seed_id>/checkpoint.pt \
  --seed <seed_id> \
  --device cpu \
  --vector-env-mode sync
```

The runner must write:

```text
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/summary.json
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/run_rows.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/profile_aggregate.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/command_matrix.csv
runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution/run_state.json
```

Each profile/seed run directory should retain `config.json`, `train_metrics.csv`,
`eval_summary.json`, `manifest.json`, `train.log`, and the checkpoint path.

## Failure Behavior

M2230 should fail closed if:

- the matrix does not contain exactly `15` rows;
- profiles or seeds differ from the M2226/M2227 frozen set;
- budget signatures differ across rows;
- any actor contract check fails;
- any generated config path is missing;
- any `train_ppo` subprocess returns nonzero;
- any expected checkpoint or eval summary is missing;
- any eval summary has non-finite selected metrics.

With `--fail-fast`, the runner should stop on the first failed profile/seed
run, but still write the partial `run_rows.csv`, `summary.json`, and
`run_state.json` with failure details.

## Post-Training Quality Floors

M2230 should not rank profiles or select a winner. It may only report whether
each profile meets the pre-registered readiness floor:

```text
at least 2/3 seeds have eval_termination_rate <= 0.4
and eval_return_mean >= 50.0
```

That floor is an admission check for result audit and downstream measured
execution. It is not a finite-window-vs-GRU conclusion, architecture ranking,
paper-level result, or self-identification claim.

## Next

Pre-register:

```text
m2230-paper-route-current-sim-matched-budget-profile-training-execution-implementation-and-run
```

M2230 may implement the focused adapter and run the 15 fixed-budget train_ppo
jobs. Interpretation remains blocked until a separate result audit.
