# M949 V4 Public Base Controlled Fusion Rejected-Branch Retention Probe

## Purpose

M949 implements the M948 no-PPO objective-only probe. It adds rejected-history
branch retention proxies to the controlled-fusion objective and then runs
M267/M264 preflight before any full replay or promotion.

M949 does not run PPO, use private holdout, or promote.

## Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python -m autodrift.public_base_controlled_fusion_rejected_branch_retention_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --m267-corpus runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --run-dir runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe \
  --device cpu \
  --epochs 80 \
  --seed 9490 \
  --lr 0.0005 \
  --train-alphas 0.125,0.150,0.175 \
  --alphas 0.005,0.010,0.020,0.035,0.050,0.0675,0.0700,0.0725,0.0750,0.1000,0.1250,0.1500,0.2000,0.2500
```

## Artifacts

- Summary: `runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/summary.json`
- Alpha metrics: `runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/alpha_metrics.csv`
- M267 preflight: `runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/m267_preflight_summary.csv`
- Training metrics: `runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/training_metrics.csv`
- Active rejected rows: `runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/active_rejected_branch_rows.csv`

## Result

M949 is valid but not a candidate:

```text
result_class: controlled_fusion_rejected_branch_retention_objective_conflict
positive_rows: 1213
reconstructed_rows: 1213
active_rejected_rows: 4 / 4
joined_target_rows: 122
missing_target_keys: 0
actor_mean_changed: true
fusion_changed: true
forbidden_parameter_changed: false
training_started: true
m267_preflight_used: true
ppo_used: false
promoted: false
```

Candidate counts:

```text
exact_candidate_alpha_count: 0
m267_preflight_pass_alpha_count: 3
candidate_alpha_count: 0
normal_safe_low_tail_trend_count: 9
boundary_near_miss_count: 0
```

## M267/M264 Preflight

The rejected-branch retention objective does recover M267/M264 preflight at
some alphas:

| alpha | M267 preflight | success_drop_count | failed active rows |
| ---: | --- | ---: | --- |
| 0.005 | pass | 17 / 17 | none |
| 0.010 | pass | 17 / 17 | none |
| 0.020 | fail | 15 / 17 | 6, 15 |
| 0.035 | fail | 14 / 17 | 6, 15, 16 |
| 0.050 | fail | 14 / 17 | 6, 15, 16 |
| 0.0675 | fail | 14 / 17 | 6, 15, 16 |
| 0.0700 | fail | 14 / 17 | 6, 15, 16 |
| 0.0725 | fail | 13 / 17 | 6, 13, 15, 16 |
| 0.0750 | fail | 13 / 17 | 6, 13, 15, 16 |
| 0.1000 | fail | 13 / 17 | 6, 13, 15, 16 |
| 0.1250 | fail | 13 / 17 | 6, 13, 15, 16 |
| 0.1500 | fail | 15 / 17 | 15, 16 |
| 0.2000 | pass | 17 / 17 | none |
| 0.2500 | fail | 16 / 17 | none active; full gate normal success regresses |

This means the rejected-branch retention terms are not dead. They can recover
the M267/M264 proof rows, but the recovery does not align with exact low-tail
candidate requirements.

## Exact Objective Metrics

The alpha band has a clear tradeoff:

```text
0.005 - 0.075:
  normal_retention_pass true
  tail_lift_pass false
  target_loss_pass true
  normal_safe_low_tail_trend true

0.100 - 0.250:
  tail_lift_pass true
  target_loss_pass true
  normal_retention_pass false
```

The boundary is narrow:

```text
alpha 0.075:
  normal_retention_pass: true
  tail_lift_pass: false
  normal_intervention_gap_p10: 0.010755
  gap_deficit_mean: 0.013556
  low_tail_fraction: 0.343776

alpha 0.100:
  normal_retention_pass: false
  tail_lift_pass: true
  normal_intervention_gap_p10: 0.012271
  gap_deficit_mean: 0.012419
  low_tail_fraction: 0.302556
```

Compared with M944, M949 shifts the problem: M267/M264 preflight can be
recovered, but exact low-tail lift and normal retention no longer overlap.

## Classification

M949 is classified as:

```text
failure_type: objective_overfit
result_class: controlled_fusion_rejected_branch_retention_objective_conflict
```

Supported claims:

- The active rejected rows reconstruct cleanly.
- The rejected-branch retention implementation preserves the P0 contract and
  only changes the allowed controlled-fusion surface.
- M267/M264 preflight is live and can pass at some alphas.
- The current objective has no alpha satisfying exact low-tail candidate
  criteria and M267 preflight together.

Unsupported claims:

- M949 produces a replay-admissible candidate.
- M949 justifies full six-surface replay.
- M949 justifies PPO or promotion.

## Decision

Do not run full replay from M949.
Do not run PPO.
Do not promote.

The next step should audit the objective conflict window:

```text
m950-v4-public-base-rejected-branch-retention-objective-conflict-audit
```

The audit should decide whether to tune the M949 objective around the
`0.075-0.100` boundary, export stronger trajectory targets, or synthesize/close
the controlled-fusion branch.
