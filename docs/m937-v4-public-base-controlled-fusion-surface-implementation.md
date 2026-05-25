# M937 V4 Public Base Controlled Fusion Surface Implementation

## Purpose

M936 designed the narrowest broader surface after actor_mean-only synthesis:

```text
trainable:
  actor_mean
  response_context_fusion.0

frozen:
  response_encoder
  context_encoder
  online_gru_cell
  critic
  log_std
  actor inputs
```

M937 implements this objective-only probe. It does not run exact compatibility,
replay, PPO, private holdout, or promotion.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_controlled_fusion_surface_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m937_v4_public_base_controlled_fusion_surface \
  --device cpu \
  --epochs 80 \
  --seed 9370 \
  --lr 0.0005 \
  --alphas 0.001,0.002,0.005,0.010,0.020,0.050,0.100,0.200,0.350,0.500,0.750,1.000
```

## Artifacts

- Summary: `runs/m937_v4_public_base_controlled_fusion_surface/summary.json`
- Alpha metrics: `runs/m937_v4_public_base_controlled_fusion_surface/alpha_metrics.csv`
- Objective rows: `runs/m937_v4_public_base_controlled_fusion_surface/objective_rows.csv`
- Raw checkpoint:
  `runs/m937_v4_public_base_controlled_fusion_surface/checkpoints/raw_controlled_fusion_update.pt`

## Result

M937 is a clean controlled-surface trust-region conflict.

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122
missing_target_keys: 0
training_started: true
actor_mean_changed: true
fusion_changed: true
response_encoder_changed: false
context_encoder_changed: false
online_gru_changed: false
critic_changed: false
log_std_changed: false
forbidden_parameter_changed: false
candidate_alpha_count: 0
strict_candidate_count: 0
low_tail_effect_candidate_count: 0
target_tolerance_candidate_count: 0
normal_safe_low_tail_trend_count: 4
result_class: public_base_controlled_fusion_surface_probe_trust_region_conflict
```

The implementation satisfies the M936 trainable-surface contract. Only
`actor_mean` and `response_context_fusion.0` changed.

## Alpha Findings

Best normal-retaining row:

```text
alpha: 0.1
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: false
target_tolerance_pass: true
normal_safe_low_tail_trend: true
first_action_drift_from_base_mean: 0.0016333646
first_action_drift_from_base_p95:  0.0042932509
normal_anchor_mse_mean:            0.0000014965
normal_anchor_mse_p95:             0.0000061440
normal_intervention_gap_p10:       0.0083945366
gap_deficit_mean:                  0.0157023912
low_tail_fraction:                 0.3907666802
```

Tail-lift row at the high end:

```text
alpha: 1.0
normal_retention_pass: false
tail_lift_pass: true
target_loss_pass: true
target_tolerance_pass: true
first_action_drift_from_base_mean: 0.0043332486
first_action_drift_from_base_p95:  0.0097801145
normal_anchor_mse_mean:            0.0000095142
normal_anchor_mse_p95:             0.0000318835
normal_intervention_gap_p10:       0.0303132460
gap_deficit_mean:                  0.0040869862
low_tail_fraction:                 0.0453421287
```

This is much stronger than M934:

```text
M934 alpha 1.0 low_tail_fraction: 0.34130
M937 alpha 1.0 low_tail_fraction: 0.04534
```

But it still fails admission because the tail-lift alphas are outside normal
retention.

## Interpretation

The controlled fusion surface has real low-tail leverage. It is not a no-effect
surface.

The current alpha grid is too coarse around the boundary:

```text
alpha 0.1: normal_retained, no tail_lift
alpha 0.2: normal_retention fails, no tail_lift
alpha 0.35: normal_retention fails, tail_lift starts
```

Before changing the objective or widening the trainable surface again, the next
step should map the raw M937 direction with a finer no-training alpha sweep.

## Decision

Do not run exact compatibility, replay, PPO, or promotion from M937.

Next blocker:

```text
m938-v4-public-base-controlled-fusion-alpha-boundary-audit
```

M938 should evaluate the saved M937 raw controlled-fusion direction with a finer
alpha grid around `0.10` to `0.35`, plus the original high-alpha reference
points. The goal is to determine whether an overlap exists between normal
retention and tail lift, or whether this is a hard trust-region conflict.
