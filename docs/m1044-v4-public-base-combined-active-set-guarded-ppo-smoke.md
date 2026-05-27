# M1044 V4 Public Base Combined Active-Set Guarded PPO Smoke

## Purpose

M1044 runs exactly one smoke-scale guarded PPO proposal from the combined
active-set public-gate base and gates the raw checkpoint without promotion.

This milestone trains for `1024` PPO steps, but it does not promote, use private
holdout, run longer PPO, or claim paper-level/real-vehicle generalization.

## Command

```bash
rm -rf runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke \
  runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044 && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt \
  --config configs/ppo_m1044_combined_active_set_guarded_smoke.json \
  --run-dir runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke \
  --ppo-run-dir runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044 \
  --device auto
```

## Base And Raw Checkpoint

Base checkpoint:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Raw PPO checkpoint:

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

Config:

```text
configs/ppo_m1044_combined_active_set_guarded_smoke.json
```

Combined active-set anchor:

```text
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
```

## PPO Result

```text
ppo_returncode: 0
training_metrics_finite: true
training_started: true
ppo_used: true
raw_checkpoint_exists: true
actor_inputs_changed: false
private_holdout_used: false
promoted: false
```

Training smoke metrics:

```text
step: 1024
rollout_return_mean: 58.691013
reward_mean: 0.972460
episode_count: 13
termination_rate: 0.307692
response_prediction_loss_mean: 0.049737
outcome_intervention_loss_mean: 0.675752
rejected_history_preference_loss_mean: 1.015836
trajectory_action_anchor_loss_mean: 0.00000114
```

Trainer smoke eval:

```text
return_mean: 73.379598
steps_mean: 70.4
termination_rate: 0.0
```

## Gate Result

Run classification:

```text
result_class: combined_active_set_guarded_ppo_raw_candidate
failure_types: none
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
```

Summary artifact:

```text
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/summary.json
```

## Exact And Combined Active-Set Checks

```text
M997 action_l2_mean: 0.003190
M997 action_l2_max: 0.012716
M997 total_loss_improvement: 0.005033
M297 delta vs base: 0.000000
M270 delta vs base: 0.000000
combined anchor total loss: 0.000006316
combined M267 loss: 0.000028293
combined M183 row16 loss: 0.000000821
full exact contract gate: true
```

The PPO raw checkpoint changes expected PPO trainable surfaces:

```text
actor_mean.
context_encoder.
critic.
online_gru_cell.
response_context_fusion.0.
response_encoder.
response_prediction_head.
```

The deployable actor input contract remains unchanged.

## Proof Replay Gates

All six public proof replay surfaces pass:

```text
m183_m168: 16 / 16 success drops retained
m183_m170: 17 / 17 success drops retained
m193_m189: 14 / 14 success drops retained
m212_m204: 17 / 17 success drops retained
m223_m219: 17 / 17 success drops retained
m267_m264: 17 / 17 success drops retained
```

Important hard rows:

```text
M267/M264 row15:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.005731
  wrong_history_margin: -0.000847
  margin_gap: 0.006578

M183/M170 row16:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.000467
  wrong_history_margin: -0.006022
  margin_gap: 0.006489
```

This is the important difference from M1026: the PPO proposal did not lift the
row15 wrong-history branch into success, and it did not push row16 normal branch
below zero.

## Source-Diverse Diagnostics

All three source-diverse replay diagnostics pass:

```text
current_m333_surface: 17 / 17 success drops retained
m317_continuity_surface: 17 / 17 success drops retained
m314_continuity_surface: 17 / 17 success drops retained
```

The old key neighborhood remains diagnostic-only:

```text
base accepted cases: 34 / 40
raw PPO accepted cases: 35 / 40
old key policy_pass: false for both
```

## Generalization

Fresh public and moderate-OOD public checks retain success and termination
rates, with small positive margin deltas:

```text
fresh_public seed 103900:
  base success: 0.867188
  raw success: 0.867188
  margin delta: +0.000181

fresh_public seed 103901:
  base success: 0.871094
  raw success: 0.871094
  margin delta: +0.000181

moderate_ood seed 103920:
  base success: 0.640625
  raw success: 0.640625
  margin delta: +0.000218
```

## Behavior And Ablation

Behavior seeds pass and preserve:

```text
normal >= reset >= zero_all
```

Results:

```text
seed 9505: normal 0.8625, reset 0.8500, zero_all 0.8000
seed 9506: normal 0.8625, reset 0.8500, zero_all 0.8000
seed 103930: normal 0.8375, reset 0.8125, zero_all 0.8000
seed 103931: normal 0.8250, reset 0.8000, zero_all 0.7875
```

Raw PPO normal success matches the base on all behavior seeds.

## Interpretation

M1044 is the first post-promotion PPO smoke in this branch that keeps exact
retention, row15 wrong-history failure, row16 normal success, all public replay
surfaces, source-diverse diagnostics, fresh/OOD public checks, and behavior
ordering.

It supports routing to a separate promotion audit. It does not itself promote.

## Scope Limits

This result does not claim:

```text
long-run PPO stability;
multi-seed PPO repeatability;
private holdout generalization;
paper-level statistical evidence;
real-vehicle transfer;
full scenario-distribution benchmark completion.
```

## Decision

```text
combined_active_set_guarded_ppo_raw_candidate_route_to_promotion_audit
```

Next:

```text
m1045-v4-public-base-combined-active-set-guarded-ppo-promotion-audit
```
