# M1049 V4 Public Base Guarded PPO Short Escalation Smoke

## Purpose

M1049 runs one 4096-step guarded PPO proposal from the current public-gate base
and gates the raw checkpoint without promotion.

This milestone does not promote, use private holdout, change actor inputs,
change the loss recipe, or claim repeatability.

## Base

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt \
  --config configs/ppo_m1049_guarded_short_escalation_seed61049.json \
  --run-dir runs/m1049_guarded_ppo_short_escalation_seed61049 \
  --ppo-run-dir runs/ppo_m1049_guarded_short_escalation_seed61049 \
  --device auto
```

## PPO Scope

```text
total_steps: 4096
seed: 61049
rollout_steps: 128
num_envs: 8
learning_rate: 5e-7
freeze_log_std: true
promoted: false
private_holdout_used: false
```

## Result

```text
result_class: combined_active_set_guarded_ppo_raw_candidate
ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
raw_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
summary: runs/m1049_guarded_ppo_short_escalation_seed61049/summary.json
```

## Exact Contract

The raw checkpoint passed the exact M997/M297/M270/combined-active-set checks:

```text
weighted_total_loss: -0.8960123215
total_loss_improvement: 0.0145994730
candidate_action_l2_mean: 0.0089374460
candidate_action_l2_max: 0.0561829656
exact_m297_delta_vs_base: 0.0
exact_m270_delta_vs_base: 0.0
combined_anchor_total_loss: 0.0000097900
```

Allowed changed parameter prefixes remain the PPO guarded surface:

```text
actor_mean.
context_encoder.
critic.
online_gru_cell.
response_context_fusion.0.
response_encoder.
response_prediction_head.
```

Actor inputs did not change.

## Proof Replay Gates

All six public proof replay surfaces passed:

```text
m183_m168: 16 / 16 success drops
m183_m170: 17 / 17 success drops
m193_m189: 14 / 14 success drops
m212_m204: 17 / 17 success drops
m223_m219: 17 / 17 success drops
m267_m264: 17 / 17 success drops
```

Hard rollback rows:

```text
M267/M264 row15:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.0064635657
  wrong_history_margin: -0.0005672970
  margin_gap: 0.0070308627

M183/M170 row16:
  normal_success: true
  wrong_history_success: false
  normal_margin: 0.0006210534
  wrong_history_margin: -0.0061888496
  margin_gap: 0.0068099031
```

The row15 wrong-history branch remains failing, and the row16 normal-history
branch remains successful.

## Generalization And Behavior

Fresh public and moderate-OOD checks passed:

```text
fresh_public seed 103900:
  success_delta: 0.0
  margin_mean_delta: +0.0001977440

fresh_public seed 103901:
  success_delta: 0.0
  margin_mean_delta: +0.0001991423

moderate_ood seed 103920:
  success_delta: 0.0
  margin_mean_delta: +0.0016244702
```

Behavior seeds passed and retained ordering:

```text
9505: normal 0.8625, reset 0.8500, zero_all 0.8000
9506: normal 0.8625, reset 0.8500, zero_all 0.8000
103930: normal 0.8375, reset 0.8125, zero_all 0.8000
103931: normal 0.8250, reset 0.8000, zero_all 0.7875
```

## Interpretation

M1049 is the first successful escalation beyond the 1024-step smoke scale in
this guarded PPO lineage. It shows that a single 4096-step proposal can remain
within the exact/proof/source-diverse/fresh/OOD/behavior gate stack while
retaining both historical hard active sets.

It still does not prove repeatability or long-run PPO stability because it is a
single public-gate seed. The correct next step is a fresh-seed repeat at the
same 4096-step scale, not promotion or medium PPO.

## Decision

```text
guarded_ppo_short_escalation_raw_candidate_route_to_fresh_seed_repeat
```

Next:

```text
m1050-v4-public-base-guarded-ppo-short-escalation-repeat
```
