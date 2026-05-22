# M181 Low-Threshold Source-Diverse Boundary Mining

M180 showed that lateral and longitudinal obstacle offsets do not diversify the
M179 wrong-history outcome surface. M181 tests whether the duplicate domination
was caused by an overly strict base action-distance filter.

Result: negative. Lowering `min-base-action-distance` from `0.02` to `0.0`
increases the candidate set, but accepted wrong-history rows remain exactly the
same duplicate-dominated surface.

## Setup

All runs start from:

```text
runs/m178_dual_checkpoint_outcome_proof_surface_seed9510/outcome_interventions.csv
```

Checkpoints:

```text
m168_strict = runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt
m170_split  = runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt
```

The actor input contract is unchanged: P0 human-view no-wheel online GRU.

Each threshold runs wrong-history-only boundary relocation, then a robustness
gate. No PPO, corpus construction, or actor update is admitted by this
milestone.

## Threshold Ablation

| min-base-action-distance | Candidate rows | Replay rows | Accepted wrong rows | Raw source pairs | Success drops | Strict physical pairs | Left steps | Targets | Margin buckets | Max pair fraction | Decision |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.000 | 960 | 5202 | 48 | 20 | 48 | 3 | 2 | 1 | 2 | 0.333333 | reject duplicate dominated |
| 0.005 | 878 | 4736 | 48 | 20 | 48 | 3 | 2 | 1 | 2 | 0.333333 | reject duplicate dominated |
| 0.010 | 804 | 4266 | 48 | 20 | 48 | 3 | 2 | 1 | 2 | 0.333333 | reject duplicate dominated |
| 0.020 | 658 | 3376 | 48 | 20 | 48 | 3 | 2 | 1 | 2 | 0.333333 | reject duplicate dominated |

All robustness gates fail on the same conditions:

```text
accepted wrong physical pairs: 3 < 10
accepted wrong left steps:     2 < 5
max pair fraction:             0.333333 > 0.25
```

## Accepted Surface

Accepted rows remain lateral-only:

| Checkpoint | Target | Rows | Raw source pairs | Success drops | Mean margin gap | Max margin gap |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m168_strict | future_lateral_accel_response | 24 | 20 | 24 | 0.008496 | 0.010628 |
| m170_split | future_lateral_accel_response | 24 | 20 | 24 | 0.008547 | 0.010718 |

Dominating strict physical pairs:

```text
(9530, 18, 9540, 21) -> 16 accepted rows
(9530, 18, 9540, 24) -> 16 accepted rows
(9530, 21, 9540, 24) -> 16 accepted rows
```

## Commands

Representative surface command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m178_dual_checkpoint_outcome_proof_surface_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.0 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 40 \
  --report-variants wrong_matched_history \
  --device cpu \
  --run-dir runs/m181_action0_wrong_history_boundary_surface_seed9510
```

Representative robustness command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m181_action0_wrong_history_boundary_surface_seed9510/boundary_relocation_rows.csv \
  --control-checkpoint-label none \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 40 \
  --min-physical-pairs 10 \
  --min-left-steps 5 \
  --min-checkpoints 2 \
  --min-targets 1 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.25 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m181_action0_robustness_seed9510
```

Run directories:

```text
runs/m181_action0_wrong_history_boundary_surface_seed9510
runs/m181_action0_robustness_seed9510
runs/m181_action005_wrong_history_boundary_surface_seed9510
runs/m181_action005_robustness_seed9510
runs/m181_action01_wrong_history_boundary_surface_seed9510
runs/m181_action01_robustness_seed9510
runs/m181_action02_wrong_history_boundary_surface_seed9510
runs/m181_action02_robustness_seed9510
```

## Interpretation

What M181 proves:

- the M178 candidate pool is exhausted for this boundary relocation recipe;
- the duplicate domination is not caused by the `0.02` action-distance filter;
- selecting from the same M178 rows cannot produce a source-diverse outcome
  proof surface.

What M181 does not support:

- no source-diverse proof surface;
- no multi-variant replay admission;
- no boundary outcome corpus;
- no actor update or PPO.

## Decision

Complete M181 as a negative threshold-ablation result.

The next step must change the data source or mining objective, not just the
threshold. M182 should remine a source-diverse matched-current/proof surface
with diversity as a first-class selection constraint.
