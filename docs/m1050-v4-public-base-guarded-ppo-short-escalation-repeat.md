# M1050 V4 Public Base Guarded PPO Short Escalation Repeat

## Purpose

M1050 runs two fresh 4096-step guarded PPO repeats from the current public-gate
base and gates each raw checkpoint without promotion.

This milestone does not promote, use private holdout, change actor inputs,
change the PPO recipe, or claim medium/long PPO stability.

## Base

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

## Commands

Seed 61050:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt \
  --config configs/ppo_m1050_guarded_short_repeat_seed61050.json \
  --run-dir runs/m1050_guarded_ppo_short_repeat_seed61050 \
  --ppo-run-dir runs/ppo_m1050_guarded_short_repeat_seed61050 \
  --device auto
```

Seed 61051:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt \
  --config configs/ppo_m1050_guarded_short_repeat_seed61051.json \
  --run-dir runs/m1050_guarded_ppo_short_repeat_seed61051 \
  --ppo-run-dir runs/ppo_m1050_guarded_short_repeat_seed61051 \
  --device auto
```

## Aggregate Result

```text
result_class: guarded_ppo_short_escalation_repeat_pass
seed_count: 2
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
runs/m1050_guarded_ppo_short_escalation_repeat_summary.json
runs/m1050_guarded_ppo_short_escalation_repeat_summary.csv
```

## Per-Seed Results

Seed 61050:

```text
raw_checkpoint: runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
result_class: combined_active_set_guarded_ppo_raw_candidate
M997 action_l2_mean: 0.008471
M997 action_l2_max: 0.055131
total_loss_improvement: 0.014407
M267/M264 success drops: 17 / 17
M183/M170 success drops: 17 / 17
row15 wrong_history_margin: -0.000847
row16 normal_margin: 0.000467
fresh margin delta mean: +0.000472
moderate-OOD margin delta: +0.000349
```

Seed 61051:

```text
raw_checkpoint: runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
result_class: combined_active_set_guarded_ppo_raw_candidate
M997 action_l2_mean: 0.008801
M997 action_l2_max: 0.055634
total_loss_improvement: 0.014658
M267/M264 success drops: 17 / 17
M183/M170 success drops: 17 / 17
row15 wrong_history_margin: -0.000847
row16 normal_margin: 0.000467
fresh margin delta mean: +0.000460
moderate-OOD margin delta: +0.000358
```

## Proof Gates

Both 4096-step repeats passed all six public replay surfaces:

```text
m183_m168
m183_m170
m193_m189
m212_m204
m223_m219
m267_m264
```

Both also passed the source-diverse protected diagnostics:

```text
current_m333_surface
m317_continuity_surface
m314_continuity_surface
```

## Hard Rollback Rows

Both repeats retained the required hard row polarity:

```text
M267/M264 row15:
  normal_success: true
  wrong_history_success: false
  wrong_history_margin: -0.000847

M183/M170 row16:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.000467
```

## Generalization And Behavior

Both repeats retained success, termination, and collision rates on:

```text
fresh_public seeds: 103900, 103901
moderate_ood seed: 103920
```

Both retained behavior ordering:

```text
normal >= reset_recurrent_state >= zero_all_response
```

for behavior seeds:

```text
9505
9506
103930
103931
```

## Interpretation

M1050 shows that the 4096-step guarded PPO recipe is not a single-seed short
escalation accident. Together with M1049, there are now three 4096-step public
gate passes from the M1045 public-gate base:

```text
61049
61050
61051
```

This supports a stronger short-PPO repeatability claim, but still not a
private-holdout, promotion, medium-PPO, long-PPO, or paper-level claim. The
next step should synthesize the short-escalation evidence before deciding
whether to run a promotion audit, refresh public surfaces, or attempt a medium
PPO design.

## Decision

```text
guarded_ppo_short_escalation_repeat_pass_route_to_synthesis
```

Next:

```text
m1051-v4-public-base-guarded-ppo-short-escalation-synthesis
```
