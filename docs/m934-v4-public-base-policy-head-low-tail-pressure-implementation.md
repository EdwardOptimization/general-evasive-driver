# M934 V4 Public Base Policy-Head Low-Tail Pressure Implementation

## Purpose

M933 designed one stronger actor_mean-only objective pass after M932 showed
weak normal-safe low-tail movement. M934 runs that objective while preserving
the P0 actor input contract and keeping the trainable surface limited to
`model.actor_mean`.

No exact compatibility, replay, PPO, private holdout, or promotion is run.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_policy_head_trust_region_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m934_v4_public_base_policy_head_low_tail_pressure \
  --device cpu \
  --epochs 80 \
  --seed 9340 \
  --lr 0.001 \
  --target-action-coef 0.10 \
  --low-tail-gap-floor-coef 10.0 \
  --low-tail-deficit-coef 6.0 \
  --normal-retention-coef 12.0 \
  --intervention-anchor-coef 0.50 \
  --parameter-anchor-coef 0.001 \
  --alphas 0.001,0.002,0.005,0.010,0.020,0.050,0.100,0.200,0.350,0.500,0.750,1.000
```

## Artifacts

- Summary: `runs/m934_v4_public_base_policy_head_low_tail_pressure/summary.json`
- Alpha metrics: `runs/m934_v4_public_base_policy_head_low_tail_pressure/alpha_metrics.csv`
- Objective rows: `runs/m934_v4_public_base_policy_head_low_tail_pressure/objective_rows.csv`
- Raw actor-mean checkpoint:
  `runs/m934_v4_public_base_policy_head_low_tail_pressure/checkpoints/raw_actor_mean_update.pt`

## Result

M934 is a clean actor_mean-only trust-region conflict.

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122
missing_target_keys: 0
training_started: true
actor_mean_changed: true
feature_backbone_changed: false
critic_changed: false
log_std_changed: false
non_actor_mean_changed: false
candidate_alpha_count: 0
strict_candidate_count: 0
low_tail_effect_candidate_count: 0
target_tolerance_candidate_count: 0
normal_safe_low_tail_trend_count: 3
result_class: public_base_policy_head_trust_region_probe_trust_region_conflict
```

No actor-input contract violation occurred. No non-head parameters changed.

## Alpha Interpretation

The stronger pressure produces useful low-tail movement only after normal
retention starts to fail.

Best normal-retaining row:

```text
alpha: 0.2
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: true
target_tolerance_pass: true
normal_safe_low_tail_trend: true
first_action_drift_from_base_mean: 0.0018456547
first_action_drift_from_base_p95:  0.0043201657
normal_intervention_gap_p10:       0.0076419356
gap_deficit_mean:                  0.0162048696
low_tail_fraction:                 0.3948886991
target_action_mse_mean:            0.0005215467
strict_target_action_mse_mean:     0.0005269441
```

Best tail-lift row:

```text
alpha: 1.0
normal_retention_pass: false
tail_lift_pass: true
target_loss_pass: false
first_action_drift_from_base_mean: 0.0092238141
first_action_drift_from_base_p95:  0.0215761632
normal_anchor_mse_mean:            0.0000415892
normal_anchor_mse_p95:             0.0001551774
normal_intervention_gap_p10:       0.0115052192
gap_deficit_mean:                  0.0132707707
low_tail_fraction:                 0.3413025439
```

This is the same structural conflict seen in earlier residual work, now on the
actor_mean surface:

```text
normal-safe alphas improve low-tail trend but do not reach tail-lift threshold;
tail-lift alphas require too much normal action drift.
```

## Decision

Do not run exact compatibility, replay, PPO, or promotion from M934.

Do not continue with another actor_mean-only coefficient variant immediately.
The branch stop condition from M933 fired: another actor_mean-only
implementation failed to produce an admissible strict or low-tail-effect
candidate.

Next blocker:

```text
m935-v4-public-base-policy-level-trust-region-branch-synthesis
```

M935 should synthesize M929-M934 and decide whether to close actor_mean-only
work and open a controlled broader-surface branch.
