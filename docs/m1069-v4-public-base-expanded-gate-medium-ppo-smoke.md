# M1069 V4 Public Base Expanded-Gate Medium PPO Smoke

## Purpose

M1069 ran the first conservative 8192-step medium-ramp PPO proposal from the
current M1049 public-gate base, using the expanded gate stack introduced by the
M1061 family-intersection surface and propagated by M1067.

This milestone did not promote a checkpoint and did not use private holdout.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --config configs/ppo_m1069_expanded_gate_medium_seed61069.json \
  --run-dir runs/m1069_expanded_gate_medium_ppo_seed61069 \
  --ppo-run-dir runs/ppo_m1069_expanded_gate_medium_seed61069 \
  --device auto
```

## Summary

```text
result_class: combined_active_set_guarded_ppo_exact_retention_regression
ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
exact_pass: false
proof_pass: false
public_replay_pass: false
family_intersection_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
promoted: false
private_holdout_used: false
summary: runs/m1069_expanded_gate_medium_ppo_seed61069/summary.json
raw_checkpoint: runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
```

The PPO run completed and wrote a checkpoint. The candidate is rejected because
it washed out exact/proof evidence even though fresh/OOD and behavior gates did
not regress.

## Training Metrics

The 8192-step run stayed numerically finite:

```text
final_step: 8192
rollout_return_mean: 85.974659
reward_mean: 1.141391
episode_count: 13
episode_length_mean: 75.615385
termination_rate: 0.0
response_prediction_loss_mean: 0.055148
outcome_intervention_loss_mean: 0.675767
rejected_history_preference_loss_mean: 1.127319
baseline_action_anchor_loss_mean: 0.000111696
snippet_action_anchor_loss_mean: 0.000000868
trajectory_action_anchor_loss_mean: 0.000003526
```

This is not a training-instability failure.

## Exact Contract

The exact contract failed:

```text
full_exact_contract_gate_pass: false
m297_m270_exact_pass: true
exact_m297_delta_vs_base: 0.0
exact_m270_delta_vs_base: 0.0
combined_anchor_total_loss: 0.0000188576
combined_anchor_m267_loss: 0.0000558008
combined_anchor_m183_row16_loss: 0.0000096218
```

Interpretation: the explicit M297/M270 exact losses did not regress, but the
combined active-set / action-distance exact contract failed. The raw PPO
movement is therefore outside the accepted proof trust region before replay
gates are considered.

## Old Public Replay Gates

Three of six old public proof replay surfaces failed:

```text
m183_m168: 14 / 16 success drops retained, failed
m183_m170: 16 / 17 success drops retained, failed
m193_m189: 14 / 14 success drops retained, passed
m212_m204: 17 / 17 success drops retained, passed
m223_m219: 17 / 17 success drops retained, passed
m267_m264: 16 / 17 success drops retained, failed
```

Failed rows:

```text
m183_m168 rows 9,10:
  wrong_history_success became true with margins +0.000154 and +0.001163

m183_m170 row 10:
  wrong_history_success became true with margin +0.000701

m267_m264 row 15:
  wrong_history_success became true with margin +0.000660
```

The failures preserve normal-history success but make wrong-history rollouts too
safe. This is the same proof-washout class the gates are intended to catch.

## Family-Intersection Gate

The M1061 family-intersection gate failed all three source-to-candidate replay
checks:

```text
short61049 -> candidate: 21 / 25 success drops retained, failed
short61050 -> candidate: 21 / 27 success drops retained, failed
short61051 -> candidate: 21 / 27 success drops retained, failed
```

Representative failed rows:

```text
short61049 rows 16,22,23,24:
  wrong_history_success became true, margins +0.000371 to +0.001075

short61050 rows 16,17,23,24,25,26:
  wrong_history_success became true, margins +0.000029 to +0.000789

short61051 rows 16,17,23,24,25,26:
  wrong_history_success became true, margins +0.000050 to +0.000788
```

This is a current-family proof washout, not just an old single-key artifact.

## Source-Diverse Gate

The source-diverse protected gate failed two of three replay surfaces:

```text
current_m333_surface: 17 / 17 success drops retained, passed
m317_continuity_surface: 16 / 17 success drops retained, failed
m314_continuity_surface: 16 / 17 success drops retained, failed
```

Both failed continuity surfaces lose row 15:

```text
normal_success: true
normal_margin: about +0.00823
wrong_history_success: true
wrong_history_margin: about +0.00017
```

Again, the failure is that the wrong-history branch became marginally safe.

## Generalization And Behavior

Fresh/OOD gates passed:

```text
fresh_public seed 103900: success delta 0.0, margin delta +0.000860
fresh_public seed 103901: success delta 0.0, margin delta +0.000863
moderate_ood seed 103920: success delta 0.0, margin delta +0.000473
```

Behavior gates also passed.

This matters because the candidate would look acceptable under broad aggregate
metrics. The expanded proof gates correctly rejected it because it no longer
preserves causal wrong-history sensitivity.

## Decision

```text
expanded_gate_medium_ppo_reject_proof_washout_route_to_audit
```

M1069 is a negative result. The raw checkpoint is not promotable, should not be
used as a base, and should not be repeated at new seeds before the failure is
localized.

Next:

```text
m1070-v4-public-base-medium-ppo-proof-washout-audit
```
