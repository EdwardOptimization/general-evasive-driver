# M940 V4 Public Base Controlled Fusion Boundary Objective Implementation

## Purpose

M940 implements the M939 boundary-aware controlled-fusion objective. It trains
only the registered controlled surface:

```text
actor_mean
response_context_fusion.0
```

The response encoder, context encoder, online GRU, critic, `log_std`, actor
inputs, replay, PPO, exact compatibility, private holdout, and promotion remain
blocked.

The key implementation difference from M937 is that the training loss is
computed through differentiable interpolation at the boundary alphas:

```text
train_alphas: 0.125, 0.150, 0.175
theta_eff = theta_base + alpha * (theta_raw - theta_base)
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_controlled_fusion_boundary_objective_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m940_v4_public_base_controlled_fusion_boundary_objective \
  --device cpu \
  --epochs 80 \
  --seed 9400 \
  --lr 0.0005 \
  --train-alphas 0.125,0.150,0.175 \
  --alphas 0.050,0.075,0.100,0.125,0.150,0.175,0.200,0.225,0.250,0.275,0.300,0.325,0.350,0.500,0.750,1.000
```

## Artifacts

- Summary:
  `runs/m940_v4_public_base_controlled_fusion_boundary_objective/summary.json`
- Alpha metrics:
  `runs/m940_v4_public_base_controlled_fusion_boundary_objective/alpha_metrics.csv`
- Training metrics:
  `runs/m940_v4_public_base_controlled_fusion_boundary_objective/training_metrics.csv`
- Objective rows:
  `runs/m940_v4_public_base_controlled_fusion_boundary_objective/objective_rows.csv`
- Raw checkpoint:
  `runs/m940_v4_public_base_controlled_fusion_boundary_objective/checkpoints/raw_boundary_objective_update.pt`

## Result

M940 is a clean objective-only implementation, but not an admissible candidate.

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122
missing_target_keys: 0
training_started: true
boundary_interpolation_used: true
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
normal_safe_low_tail_trend_count: 1
boundary_near_miss_count: 0
result_class: public_base_controlled_fusion_boundary_objective_trust_region_conflict
```

No exact compatibility, replay, PPO, private holdout, or promotion was run.

## Alpha Findings

Best normal-retaining row:

```text
alpha: 0.05
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: true
target_tolerance_pass: true
normal_safe_low_tail_trend: true
first_action_drift_from_base_mean: 0.0019947257
first_action_drift_from_base_p95:  0.0049017474
normal_anchor_mse_mean:            0.0000020586
normal_anchor_mse_p95:             0.0000080092
normal_intervention_gap_p10:       0.0098703578
gap_deficit_mean:                  0.0141870732
low_tail_fraction:                 0.3594394028
target_action_mse_mean:            0.0005265849
```

First registered tail-lift row:

```text
alpha: 0.075
normal_retention_pass: false
tail_lift_pass: true
target_loss_pass: true
target_tolerance_pass: true
first_action_drift_from_base_mean: 0.0027712190
first_action_drift_from_base_p95:  0.0066053644
normal_anchor_mse_mean:            0.0000040802
normal_anchor_mse_p95:             0.0000145436
normal_intervention_gap_p10:       0.0114989556
gap_deficit_mean:                  0.0128357342
low_tail_fraction:                 0.3066776693
target_action_mse_mean:            0.0005222433
```

The `0.075` row misses normal retention only on mean normal-anchor MSE:

```text
threshold: 0.0000040000
observed:  0.0000040802
```

So M940 did not eliminate the trust-region conflict. It shifted the useful
boundary into a narrower alpha interval between `0.05` and `0.075`.

## Interpretation

The boundary-aware objective is not a no-effect result:

- It keeps the actor-input and trainable-surface contract clean.
- It improves low-tail metrics and target-action MSE at the normal-retained
  `0.05` point.
- It reaches tail lift by `0.075`.

But the update is too sharp. The training alphas `0.125`, `0.150`, and `0.175`
produce a raw direction whose admissible normal-retained scale is much smaller
than the intended training boundary. This is a trust-region shaping problem, not
evidence that the encoders or GRU should be unfrozen.

## Decision

Do not run exact compatibility, replay, PPO, or promotion from M940.

Because M940 has a near-boundary transition between `0.05` and `0.075`, the next
step should synthesize the controlled-fusion branch and decide whether a
no-training micro-alpha audit is justified before any broader actor update.

Next blocker:

```text
m941-v4-public-base-controlled-fusion-branch-synthesis
```
