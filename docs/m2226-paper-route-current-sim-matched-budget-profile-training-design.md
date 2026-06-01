# M2226 Paper-Route Current-Sim Matched-Budget Profile Training Design

- status: completed
- decision: `current_sim_matched_budget_profile_training_design_admit_config_materialization`
- manifest: `experiments/manifests/m2226-paper-route-current-sim-matched-budget-profile-training-design.json`
- parent audit: `docs/m2225-paper-route-current-sim-recurrent-profile-checkpoint-quality-result-audit.md`
- reset in M2226: `false`
- measured execution in M2226: `false`
- policy action executed in M2226: `false`
- training started in M2226: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2226 freezes a fair training route to replace the weak M2171 smoke checkpoints
before any controller-family comparison. The core rule is:

```text
Do not repair only L3; train the primary deployable profile matrix under the
same budget and admission rules.
```

This keeps the project aligned with the paper-route plans: finite-window may be
the better engineering answer, and GRU/self-ID claims require matched evidence
rather than assumptions.

## Primary Profile Matrix

Primary trained profiles:

```text
L0_current_masked
L1_one_step
L2_window_25
L2_window_50
L3_online_gru
```

Control/alias profile:

```text
L3_reset_control
```

`L3_reset_control` is not trained separately. It aliases the admitted
`L3_online_gru` checkpoint and resets hidden state every control step.

Deferred diagnostic side profiles:

```text
L2_window_13
L2_window_100
```

These are useful later, but M2227 should first materialize the primary matrix.
The reason is pragmatic: M2224 already shows `L2_window_25`, `L2_window_50`,
and `L3_online_gru` are the profiles needed to remove the immediate weak-L3
blocker. Extra windows should not delay the first fair checkpoint-quality
repair.

## Budget And Seed Policy

First matched-budget stage:

```text
stage_name: matched_budget_short_v0
trainable_profile_count: 5
seeds_per_profile: 3
seed_ids: 222601, 222602, 222603
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
learning_rate: 0.0001
clip_coef: 0.1
max_grad_norm: 0.25
eval_episodes: 32
```

Budget fairness means each trained profile receives the same number of
environment steps per seed. Device choice is not a scientific variable; local
execution may use CUDA if available, but the budget is counted in environment
steps and the configs must remain CPU-compatible.

If this stage fails the quality floors for more than one primary profile, the
next route should be a matched-budget escalation design, not profile-specific
tuning. A likely escalation is:

```text
total_steps_per_seed: 32768
seeds_per_profile: 3
same profile matrix and same config generator
```

## Shared Environment And Reward Contract

All profiles must keep the current P0 deployable input boundary:

```text
include_privileged_params: false
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
action_history_mode: full
actor output: [steer, throttle, brake]
```

The train/eval scenario distribution should start from the same paper-route
profile config family as M1190/M2171, with only matched-budget training fields
changed. Profile-specific differences are limited to representation mechanics:

```text
L0_current_masked:
  zero previous-command fields.

L1_one_step:
  current human-view frame with previous command/actuator state.

L2_window_25:
  explicit 25-frame command-response window.

L2_window_50:
  explicit 50-frame command-response window.

L3_online_gru:
  current frame plus episode-persistent recurrent hidden state.
```

No profile may receive hidden dynamics parameters, wheel/slip inputs, feasibility
labels, TTC, path/reference errors, success/progress labels, or controller-mode
answers.

## Selection Rule

M2227/M2228 should produce all seed checkpoints. Selecting an admitted seed for
later measured execution must use only the pre-registered train/eval metrics:

```text
1. lower eval_termination_rate wins;
2. tie-break by higher eval_return_mean;
3. tie-break by lower eval_lateral_rmse_mean;
4. tie-break by lower seed id.
```

Measured-execution results must not influence checkpoint selection. If all
seeds of a profile fail quality floors, that profile is not admitted and the
route moves to audit/escalation instead of comparison.

## Quality Floors

Per-profile admission requires:

```text
checkpoint exists;
training returncode is 0;
training metrics are present;
eval_summary is present;
eval_termination_rate <= 0.4 for at least 2/3 seeds;
eval_return_mean >= 50.0 for at least 2/3 seeds;
no hidden/oracle/wheel/reference input contract violation;
no profile-specific tuning flag;
```

For `L3_online_gru`, also require:

```text
checkpoint actor_encoder == human_view_online_gru;
checkpoint obs_dim == 72;
checkpoint is_online_recurrent == true;
recurrent_sequence_training == true;
```

For `L3_reset_control`, require:

```text
aliases admitted L3_online_gru checkpoint;
reset_hidden_policy == every_step_control;
runtime reset-routing smoke or static-equivalent artifact exists before measured execution.
```

## Post-Training Admission Route

The route after M2226 is:

```text
M2227:
  materialize matched-budget profile training configs and command matrix.
  no training.

M2228:
  execute the matched-budget training matrix.
  no measured execution or ranking.

M2229:
  audit training completeness, checkpoint existence, quality floors, and seed
  stability.

M2230:
  materialize admitted profile checkpoints and L3 reset-control alias.
  no rollout.

M2231:
  no-rollout contract/readiness check.

M2232:
  reset/runtime smoke validation.

Only after those gates:
  design measured execution rerun.
```

The exact milestone numbers may change, but the order must not.

## Claim Boundary

Allowed after this design:

```text
The project has a matched-budget training route to remove the weak-smoke
checkpoint blocker.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU conclusion;
paper-level benchmark result;
level3 self-identification;
new rollout or measured execution;
training before config materialization and review.
```

## Next Step

M2227 should implement no-training config materialization for
`matched_budget_short_v0`, producing:

```text
configs/paper_route_profiles/m2227_matched_budget_short_v0/*.json
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/summary.json
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/claim_boundary.csv
```

M2227 must not train or rank profiles.
