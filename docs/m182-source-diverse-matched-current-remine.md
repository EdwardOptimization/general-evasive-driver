# M182 Source-Diverse Matched-Current Remine

M181 showed that threshold filtering on the M178 outcome rows was exhausted:
every threshold recovered the same duplicate-dominated boundary rows. M182 moves
upstream and remakes the matched-current candidate surface with source diversity
as a first-class selection constraint before any boundary relocation.

## Harness Change

Updated `autodrift.matched_current_response_ambiguity` with source-diversity
controls:

```text
--max-pairs-per-left-step
--max-pairs-per-source-obstacle-bucket
--obstacle-distance-bucket-width
--obstacle-lateral-bucket-width
```

`hidden_envelope_probe` now logs `obstacle_distance` and
`obstacle_lateral_offset` in the sample rows. These values are used only by the
miner and summaries; they are not actor inputs.

Validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_matched_current_response_ambiguity.py

python -m compileall -q src tests
```

Result:

```text
6 passed in 0.97s
compileall passed
```

## Matched-Current Remine

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 9510,9511,9512,9513 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m182_source_diverse_matched_current_zero_relvel_seed9510
```

Artifacts:

```text
runs/m182_source_diverse_matched_current_zero_relvel_seed9510/summary.json
runs/m182_source_diverse_matched_current_zero_relvel_seed9510/matched_pairs.csv
runs/m182_source_diverse_matched_current_zero_relvel_seed9510/candidate_pairs.csv
runs/m182_source_diverse_matched_current_zero_relvel_seed9510/target_summary.csv
```

Result:

| Metric | Value |
| --- | ---: |
| Candidate pairs | 185976 |
| Accepted matched pairs | 1691 |
| Accepted physical pairs | 319 |
| Accepted left steps | 26 |
| Accepted source obstacle buckets | 16 |
| Max rows per physical pair | 8 |
| Surface found | true |

By target:

| Target | Rows | Physical pairs | Left steps | Buckets |
| --- | ---: | ---: | ---: | ---: |
| future braking deceleration | 1201 | 213 | 26 | 15 |
| future lateral accel response | 267 | 54 | 14 | 11 |
| future yaw response | 223 | 53 | 12 | 9 |

## Direct Outcome Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m182_source_diverse_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m182_matched_history_outcome_zero_relvel_seed9510
```

Raw continuation remains outcome-neutral:

| Metric | Value |
| --- | ---: |
| Input pairs | 1691 |
| Wrong-history rows | 1691 |
| Wrong-history success drops | 0 |
| Wrong-history mean margin gap | -0.000015 |
| Wrong-history max margin gap | 0.011399 |

This matches M178: current matched states are action-sensitive but do not fail
without tightening the boundary.

## Boundary Relocation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m182_matched_history_outcome_zero_relvel_seed9510/outcome_interventions.csv \
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
  --run-dir runs/m182_wrong_history_boundary_surface_seed9510
```

Boundary result:

| Metric | Value |
| --- | ---: |
| Candidate rows | 1691 |
| Replay rows | 8520 |
| Accepted wrong-history rows | 78 |
| Accepted wrong-history source pairs | 60 |
| Wrong-history success drops | 78 |
| Surface found | true |

## Robustness Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m182_wrong_history_boundary_surface_seed9510/boundary_relocation_rows.csv \
  --control-checkpoint-label none \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 40 \
  --min-physical-pairs 10 \
  --min-left-steps 5 \
  --min-checkpoints 2 \
  --min-targets 2 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.25 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m182_boundary_robustness_seed9510
```

Robustness result:

| Gate metric | Value | Threshold |
| --- | ---: | ---: |
| Accepted wrong rows | 78 | >= 40 |
| Accepted physical pairs | 15 | >= 10 |
| Accepted left steps | 8 | >= 5 |
| Accepted checkpoints | 2 | >= 2 |
| Accepted targets | 3 | >= 2 |
| Accepted margin buckets | 2 | >= 2 |
| Success-drop fraction | 1.0 | >= 1.0 |
| Max rows per physical pair fraction | 0.153846 | <= 0.25 |
| Control accepted rows | 0 | <= 0 |

Decision:

```text
admit_boundary_wrong_history_objective
```

Accepted rows by checkpoint and target:

| Checkpoint | Target | Rows | Physical pairs | Left steps | Mean margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m168_strict | future braking deceleration | 28 | 10 | 6 | 0.007932 |
| m168_strict | future lateral accel response | 6 | 3 | 2 | 0.008589 |
| m168_strict | future yaw response | 4 | 1 | 1 | 0.005443 |
| m170_split | future braking deceleration | 31 | 11 | 7 | 0.007792 |
| m170_split | future lateral accel response | 5 | 3 | 2 | 0.008820 |
| m170_split | future yaw response | 4 | 1 | 1 | 0.005535 |

## Decision

M182 is a positive proof-surface result. It resolves the M179-M181 duplicate
domination blocker by remaking the upstream matched-current corpus before
boundary relocation.

This does not yet admit PPO. The next step is to convert the M182 accepted
boundary rows into a deduplicated boundary-outcome corpus/objective and prove
that the fixed objective is replay-aligned before any actor update.
