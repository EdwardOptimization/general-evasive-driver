# M1027 V4 Public Base Candidate B Guarded PPO Proof Washout Audit

## Purpose

M1027 audits the M1026 guarded PPO smoke result before any longer PPO,
coefficient tuning, promotion, or private holdout.

M1027 does not train, run PPO, mutate a checkpoint, use private holdout, or
change actor inputs.

## Parent Result

M1026 raw PPO checkpoint:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

M1026 classification:

```text
candidate_b_guarded_ppo_proof_washout
```

The corrected result is not training instability:

```text
ppo_returncode: 0
training_metrics_finite: true
exact_retention_pass: true
proof_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
```

The wrapper artifact was limited to the metrics path. The PPO trainer writes
`train_metrics.csv`; M1026 now prefers that file and only falls back to legacy
`metrics.csv`.

## Surface-Level Diagnosis

M1026 proof replay:

```text
M183/M168: pass, 16/16 success drops retained
M183/M170: pass, 17/17 success drops retained
M193/M189: pass, 14/14 success drops retained
M212/M204: pass, 17/17 success drops retained
M223/M219: pass, 17/17 success drops retained
M267/M264: fail, 16/17 success drops retained
```

The failing surface is current-family M267/M264.

M267/M264 aggregate:

```text
baseline_normal_success_rate: 1.0
candidate_normal_success_rate: 1.0
normal_success_delta: 0.0
baseline_wrong_history_success_rate: 0.0
candidate_wrong_history_success_rate: 0.058823529411764705
baseline_success_drop_count: 17
candidate_success_drop_count: 16
normal_margin_mean_delta: +0.000386112488785186
margin_gap_mean_delta: +0.00012055396862334193
```

This rules out broad normal-branch regression. The raw PPO proposal improves
normal margin on average and keeps all normal rollouts successful, but it also
makes one rejected-history rollout successful.

## Row-Level Diagnosis

The failed row is:

```text
row_id: 15
target: future_braking_deceleration
physical_pair_key: 9530:21:9550:21
left_seed: 9530
right_seed: 9550
left_step: 21
right_step: 21
relocated_obstacle_body_x: 9.638111
relocated_obstacle_body_y: -0.970263
relocated_obstacle_half_width: 0.723743
```

Baseline Candidate B:

```text
normal_success: true
wrong_history_success: false
normal_margin: 0.006339
wrong_history_margin: -0.000112
margin_gap: 0.006451
wrong_history_terminal_reason: collision
wrong_history_steps: 34
```

M1026 raw PPO:

```text
normal_success: true
wrong_history_success: true
normal_margin: 0.006871
wrong_history_margin: 0.000311
margin_gap: 0.006561
wrong_history_terminal_reason: obstacle_completed
wrong_history_steps: 42
```

Delta:

```text
normal_margin_delta: +0.000533
wrong_history_margin_delta: +0.000423
margin_gap_delta: +0.000110
```

First wrong-history action changed only slightly:

```text
steer: +0.000636
throttle: -0.000474
brake: -0.000285
wrong_first_action_distance: 0.088449 -> 0.089573
wrong_trajectory_distance_mean: 0.040910 -> 0.035430
```

The proof loss is therefore a near-boundary rejected-branch lift: a tiny
trajectory change makes the wrong-history branch safe. It is not a loss of
normal capability and not a large first-action jump.

## What This Means

M1026 gives a useful PPO proposal:

```text
training runs
exact temporal retention passes
fresh public and moderate-OOD behavior does not regress
behavior/ablation ordering is retained
```

But it is not acceptable as a new base:

```text
one current-family wrong-history proof row becomes safe
```

This is the same structural risk seen earlier in the project: scalar PPO
auxiliary losses and broad replay anchors can retain aggregate behavior while
still lifting a near-zero rejected-history branch across the terminal margin
boundary.

## Route Decision

Do not run longer PPO from the same recipe yet.

Do not promote the M1026 raw checkpoint.

Do not treat M1026 as a recipe crash.

The next milestone should design an exact post-PPO repair/projection step:

```text
given:
  theta_base = Candidate B public-gate base
  theta_raw = M1026 raw PPO checkpoint

find:
  theta_repaired

lexicographic constraints:
  retain M997 exact temporal objective
  retain all six public proof replay surfaces
  especially M267/M264 row 15 rejected-history failure
  retain fresh public / moderate-OOD / behavior gates

objective:
  stay as close as possible to theta_raw while satisfying proof constraints
```

This preserves the useful idea that PPO is a proposal generator, while exact
repair/projection is responsible for proof feasibility.

## Decision

```text
candidate_b_guarded_ppo_washout_localized_route_to_exact_repair_design
```

Next milestone:

```text
m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design
```
