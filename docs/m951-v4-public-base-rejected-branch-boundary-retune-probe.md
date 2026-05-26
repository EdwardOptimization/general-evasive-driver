# M951 V4 Public Base Rejected-Branch Boundary Retune Probe

## Purpose

M951 runs the one bounded lower-boundary retune admitted by M950. It keeps the
same P0 input contract and controlled-fusion trainable surface, but moves the
training alphas down to the observed conflict window and exposes loss
coefficients through the M949 probe CLI.

M951 does not run PPO, full replay, private holdout, or promotion.

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
  --run-dir runs/m951_v4_public_base_rejected_branch_boundary_retune_probe \
  --device cpu \
  --epochs 80 \
  --seed 9510 \
  --lr 0.0005 \
  --train-alphas 0.0675,0.0750,0.0900,0.1000 \
  --alphas 0.005,0.010,0.020,0.035,0.050,0.0675,0.0700,0.0725,0.0750,0.0900,0.1000,0.1250,0.1500,0.2000 \
  --boundary-deficit-coef 16.0 \
  --boundary-gap-floor-coef 12.0 \
  --normal-retention-coef 18.0 \
  --normal-anchor-coef 4.0 \
  --intervention-anchor-coef 0.5 \
  --target-action-coef 0.05 \
  --rejected-wrong-action-anchor-coef 12.0 \
  --rejected-wrong-separation-coef 8.0 \
  --rejected-wrong-direction-coef 8.0 \
  --parameter-anchor-coef 0.001
```

## Result

M951 is valid but still not a candidate:

```text
result_class: controlled_fusion_rejected_branch_retention_objective_conflict
reconstructed_rows: 1213 / 1213
active_rejected_rows: 4 / 4
joined_target_rows: 122
missing_target_keys: 0
actor_mean_changed: true
fusion_changed: true
forbidden_parameter_changed: false
ppo_used: false
promoted: false
```

Candidate counts:

```text
exact_candidate_alpha_count: 0
m267_preflight_pass_alpha_count: 13
candidate_alpha_count: 0
normal_safe_low_tail_trend_count: 5
boundary_near_miss_count: 0
```

## What Improved

M267/M264 preflight improved strongly. All alphas from `0.005` through `0.150`
pass M267/M264 with `17/17` success drops:

```text
m267_preflight_pass_alphas:
0.005, 0.010, 0.020, 0.035, 0.050,
0.0675, 0.0700, 0.0725, 0.0750,
0.0900, 0.1000, 0.1250, 0.1500
```

This confirms the rejected-branch retention side of the objective can protect
the M267 proof rows.

## What Still Fails

The retune removes the M267 problem but leaves the original trust-region
conflict:

```text
0.005 - 0.050:
  normal_retention_pass: true
  tail_lift_pass: false
  M267 preflight: pass

0.0675 - 0.150:
  normal_retention_pass: false
  tail_lift_pass: true
  M267 preflight: pass

0.200:
  normal_retention_pass: false
  tail_lift_pass: true
  M267 preflight: fail
```

The best boundary remains just outside overlap:

```text
alpha 0.050:
  normal_retention_pass: true
  tail_lift_pass: false
  M267 preflight: pass
  normal_intervention_gap_p10: 0.010551
  gap_deficit_mean: 0.013409
  low_tail_fraction: 0.330585

alpha 0.0675:
  normal_retention_pass: false
  tail_lift_pass: true
  M267 preflight: pass
  normal_intervention_gap_p10: 0.012146
  gap_deficit_mean: 0.012207
  low_tail_fraction: 0.301731
```

This is not a rejected-branch retention failure anymore. It is a
controlled-fusion surface trust-region conflict: the allowed surface can either
stay close enough to M399 or create enough low-tail lift, but not both at the
registered thresholds.

## Decision

Do not run full replay.
Do not run PPO.
Do not promote.
Do not run another local coefficient tweak.

M950 allowed exactly one bounded retune. M951 used it and still produced no
candidate. The next milestone must synthesize the branch before any further
objective or trainable-surface changes:

```text
m952-v4-public-base-controlled-fusion-branch-synthesis-2
```
