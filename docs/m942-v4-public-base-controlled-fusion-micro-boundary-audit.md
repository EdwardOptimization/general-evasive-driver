# M942 V4 Public Base Controlled Fusion Micro Boundary Audit

## Purpose

M942 runs the one no-training micro-alpha audit allowed by M941. It evaluates
the M940 raw controlled-fusion boundary-objective direction between alpha
`0.05` and `0.075`, where M940 showed a narrow transition:

```text
0.05:  normal-retained low-tail trend, no tail lift
0.075: tail lift, just outside normal retention
```

M942 does not train, update a checkpoint, run replay, run PPO, use private
holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_controlled_fusion_raw_direction_feasibility \
  --base-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m940_v4_public_base_controlled_fusion_boundary_objective/checkpoints/raw_boundary_objective_update.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit \
  --device cpu \
  --alphas 0.040,0.045,0.0475,0.050,0.0525,0.055,0.0575,0.060,0.0625,0.065,0.0675,0.070,0.0725,0.075,0.0775,0.080,0.085,0.090,0.100
```

## Artifacts

- Summary:
  `runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/summary.json`
- Alpha metrics:
  `runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/alpha_metrics.csv`
- Objective rows:
  `runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/objective_rows.csv`

## Result

M942 finds an exact objective-level overlap.

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122
missing_target_keys: 0
actor_mean_changed_between_checkpoints: true
fusion_changed_between_checkpoints: true
forbidden_parameter_changed_between_checkpoints: false
training_started: false
optimizer_started: false
candidate_alpha_count: 3
strict_candidate_count: 3
low_tail_effect_candidate_count: 3
target_tolerance_candidate_count: 3
normal_safe_low_tail_trend_count: 13
replay_used: false
ppo_used: false
promoted: false
result_class: public_base_controlled_fusion_raw_direction_feasibility_candidate
```

Candidate alphas:

```text
0.0675
0.0700
0.0725
```

## Candidate Rows

Primary candidate, best by low-tail/deficit among normal-retaining rows:

```text
alpha: 0.0725
normal_retention_pass: true
tail_lift_pass: true
target_loss_pass: true
target_tolerance_pass: true
first_action_drift_from_base_mean: 0.0026981827
first_action_drift_from_base_p95:  0.0064748540
normal_anchor_mse_mean:            0.0000038589
normal_anchor_mse_p95:             0.0000139746
normal_intervention_gap_p10:       0.0113417562
gap_deficit_mean:                  0.0129708514
low_tail_fraction:                 0.3264633119
target_action_mse_mean:            0.0005227432
```

Most conservative candidate:

```text
alpha: 0.0675
normal_retention_pass: true
tail_lift_pass: true
target_loss_pass: true
target_tolerance_pass: true
first_action_drift_from_base_mean: 0.0025495142
normal_anchor_mse_mean:            0.0000034283
normal_intervention_gap_p10:       0.0110019054
gap_deficit_mean:                  0.0132407104
low_tail_fraction:                 0.3289365172
target_action_mse_mean:            0.0005236954
```

The rejected boundary remains clear:

```text
alpha: 0.075
normal_retention_pass: false
tail_lift_pass: true
normal_anchor_mse_mean: 0.0000040802
```

## Interpretation

M942 converts the M940 trust-region conflict into an exact objective-level
candidate. The controlled-fusion surface can satisfy the registered public
objective gates when alpha is calibrated more finely.

This is not a replay, PPO, or driver-improvement result. It only shows that the
M940 raw direction contains candidate interpolated checkpoints that should be
materialized and checked with exact no-update compatibility before any replay
or promotion path.

## Decision

Do not run replay, PPO, private holdout, or promotion from M942.

Next route:

```text
exact no-update compatibility design
```

M943 should design candidate checkpoint materialization and exact compatibility
for the three candidate alphas, with alpha `0.0725` as the primary candidate
and `0.0675` / `0.0700` as backups.

Next blocker:

```text
m943-v4-public-base-controlled-fusion-candidate-compatibility-design
```
