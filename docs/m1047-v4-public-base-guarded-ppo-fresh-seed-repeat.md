# M1047 V4 Public Base Guarded PPO Fresh-Seed Repeat

## Purpose

M1047 runs two fresh-seed 1024-step guarded PPO smoke repeats from the current
public-gate base and gates each raw checkpoint without promotion.

This milestone does not promote, use private holdout, run longer PPO, or claim
long-run PPO stability.

## Base

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

## Commands

Seed 61045:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt \
  --config configs/ppo_m1047_guarded_repeat_seed61045.json \
  --run-dir runs/m1047_guarded_ppo_repeat_seed61045 \
  --ppo-run-dir runs/ppo_m1047_guarded_repeat_seed61045 \
  --device auto
```

Seed 61046:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt \
  --config configs/ppo_m1047_guarded_repeat_seed61046.json \
  --run-dir runs/m1047_guarded_ppo_repeat_seed61046 \
  --ppo-run-dir runs/ppo_m1047_guarded_repeat_seed61046 \
  --device auto
```

## Aggregate Result

```text
result_class: guarded_ppo_fresh_seed_repeat_pass
raw_candidate_pass_count: 2 / 2
ppo_returncode_zero_count: 2 / 2
training_metrics_finite_count: 2 / 2
exact_pass_count: 2 / 2
proof_pass_count: 2 / 2
source_diverse_pass_count: 2 / 2
generalization_pass_count: 2 / 2
behavior_pass_count: 2 / 2
actor_inputs_changed_count: 0 / 2
promoted: false
private_holdout_used: false
```

Aggregate artifacts:

```text
runs/m1047_guarded_ppo_fresh_seed_repeat_summary.csv
runs/m1047_guarded_ppo_fresh_seed_repeat_summary.json
```

## Per-Seed Results

Seed 61045:

```text
raw_checkpoint: runs/ppo_m1047_guarded_repeat_seed61045/checkpoint.pt
result_class: combined_active_set_guarded_ppo_raw_candidate
M997 action_l2_mean: 0.004510
M997 action_l2_max: 0.024346
total_loss_improvement: 0.007704
M267/M264 success drops: 17 / 17
M183/M170 success drops: 17 / 17
row15 wrong_history_margin: -0.000793
row16 normal_margin: 0.000520
fresh margin delta mean: +0.000091
moderate-OOD margin delta: +0.000015
```

Seed 61046:

```text
raw_checkpoint: runs/ppo_m1047_guarded_repeat_seed61046/checkpoint.pt
result_class: combined_active_set_guarded_ppo_raw_candidate
M997 action_l2_mean: 0.004617
M997 action_l2_max: 0.024435
total_loss_improvement: 0.007912
M267/M264 success drops: 17 / 17
M183/M170 success drops: 17 / 17
row15 wrong_history_margin: -0.000632
row16 normal_margin: 0.000645
fresh margin delta mean: +0.000116
moderate-OOD margin delta: +0.000127
```

## Proof Gates

Both seeds pass all six public replay surfaces:

```text
m183_m168
m183_m170
m193_m189
m212_m204
m223_m219
m267_m264
```

Both seeds also pass the three source-diverse protected diagnostics:

```text
current_m333_surface
m317_continuity_surface
m314_continuity_surface
```

## Generalization And Behavior

Both seeds retain success and termination rates on:

```text
fresh_public seeds: 103900, 103901
moderate_ood seed: 103920
behavior seeds: 9505, 9506, 103930, 103931
```

Both preserve behavior ordering:

```text
normal >= reset >= zero_all
```

## Interpretation

M1047 provides fresh-seed smoke evidence that the M1044 guarded PPO recipe is
not a single-seed accident at the 1024-step scale. It does not yet prove
long-run PPO stability, because both repeats are still smoke-scale and use
public gates.

## Decision

```text
guarded_ppo_fresh_seed_repeat_pass_route_to_short_escalation_design
```

Next:

```text
m1048-v4-public-base-guarded-ppo-short-escalation-design
```
