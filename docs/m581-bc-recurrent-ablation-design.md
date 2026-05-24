# M581 BC Recurrent Ablation Design

## Purpose

M581 designs the first recurrent-dependence diagnostic for the scaled BC branch.

The route/OOD family evidence is now strong, but it does not prove that the
deployed L3 online-GRU actor uses recurrent command-response history. M581
therefore pre-registers ablation benchmarks before any ablation result is
observed.

This milestone is design-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Candidate

First diagnostic checkpoint:

```text
bc5660 = runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

BC5660 is selected because it was the route-screen-selected member of the
scaled BC family and stayed strong through M570/M572/M575/M578/M579.

## Existing Tooling

`autodrift.benchmark` already supports checkpoint ablations:

```text
checkpoint.pt@reset_recurrent_state
checkpoint.pt@zero_current_response
checkpoint.pt@zero_action_history
checkpoint.pt@zero_all_response
```

For L3 with `history_length = 1`:

- `reset_recurrent_state` clears the online hidden state at every action.
- `zero_current_response` zeros current ego/IMU-like response, actuator state,
  and previous-command response slots while preserving hidden state.
- `zero_action_history` zeros previous physical command slots only.
- `zero_all_response` is included as a severe control; with one-frame L3 input
  it is expected to behave similarly to `zero_current_response`.

## M582 Fresh-Route Ablation

M582 should run a same-distribution fresh-route ablation benchmark:

```text
env_config = configs/ppo_m541_matched_l3_variance_4096.json
episodes = 256
seed_start = 23560
seed_list = 23560..23815
run_dir = runs/m582_bc5660_recurrent_ablation_fresh_route_eval
```

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --policies checkpoint \
  --checkpoint-policy bc5660_normal=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy bc5660_reset=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy bc5660_zero_current=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_current_response \
  --checkpoint-policy bc5660_zero_action=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_action_history \
  --checkpoint-policy bc5660_zero_all=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_all_response \
  --episodes 256 \
  --seed 23560 \
  --device cpu \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --run-dir runs/m582_bc5660_recurrent_ablation_fresh_route_eval
```

## M583 Moderate-OOD Ablation

M583 should run only after M582 is documented. It should use the M574 OOD L3
config:

```text
env_config = configs/eval_m574_moderate_ood_l3.json
episodes = 256
seed_start = 24560
seed_list = 24560..24815
run_dir = runs/m583_bc5660_recurrent_ablation_moderate_ood_eval
```

Use the same policy set and ablations as M582.

## Diagnostic Thresholds

Compare every ablation against `bc5660_normal` on the same seed block:

```text
success_drop = normal_success - ablated_success
margin_drop = normal_margin_mean - ablated_margin_mean
collision_increase = ablated_collision - normal_collision
```

Diagnostic labels:

```text
meaningful degradation:
  success_drop >= 0.02
  OR margin_drop >= 0.05
  OR collision_increase >= 0.02

strong degradation:
  success_drop >= 0.05
  OR margin_drop >= 0.10
  OR collision_increase >= 0.05
```

Interpretation:

- If `reset_recurrent_state` degrades behavior, accumulated online hidden state
  is behaviorally relevant.
- If `zero_current_response` degrades behavior but reset does not, the current
  response frame matters more than accumulated hidden state on this route block.
- If `zero_action_history` degrades behavior, previous command information is
  behaviorally relevant.
- If no ablation degrades behavior, this is a negative self-ID diagnostic: the
  BC policy may be mostly memoryless on this distribution.

## Promotion Boundary

These ablations are diagnostic proof gates, not promotion gates. Even a strong
degradation result should not promote a checkpoint by itself. Promotion remains
blocked until generalization, recurrent-dependence evidence, and later
wrong-history or delayed-history tests are all considered together.

## Decision

```text
bc_recurrent_ablation_design_admit_m582_fresh_route_eval
```

M581 passes because it pre-registers the checkpoint, ablations, seed blocks,
commands, thresholds, and interpretation rules before running ablation
benchmarks.

## Next

```text
M582: run BC5660 recurrent-ablation fresh-route benchmark.
```
