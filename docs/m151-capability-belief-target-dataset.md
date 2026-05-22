# M151 Capability-Belief Target Dataset

Date: 2026-05-22

## Question

M150 showed that P0-close target-divergent pairs are best treated as a
capability-belief problem, not as direct friction prediction or passive input
expansion. M151 builds the training-time dataset for that next objective.

The actor input contract does not change.

## Dataset Contract

Student input arrays:

```text
student_p0_i
student_p0_j
```

These contain only deployable P0 history features:

```text
vx, vy, yaw_rate, ax, ay
steering actuator state, steer-rate proxy
throttle/brake actuator states
previous steering/throttle/brake commands
road/obstacle geometry
```

Teacher / training-time arrays:

```text
teacher_capability_i
teacher_capability_j
teacher_capability_delta
teacher_capability_abs_delta_z
pair_weight
dominant_target_index
dominant_hidden_group_index
hidden_group_distances
```

Teacher targets are:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

Hidden group diagnostics are stored only as training-time metadata for target
weighting, analysis, and teacher design. They are not actor inputs.

## Implementation

New module:

```text
src/autodrift/capability_belief_target_dataset.py
```

New tests:

```text
tests/test_capability_belief_target_dataset.py
```

## Commands

Seed datasets:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_target_dataset \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9480/accepted_pairs.csv \
  --hidden-metrics-csv runs/m150_p0_close_hidden_cause_seed9480/hidden_pair_metrics.csv \
  --episodes 40 --seed 9480 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 \
  --run-dir runs/m151_capability_belief_dataset_seed9480

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_target_dataset \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9481/accepted_pairs.csv \
  --hidden-metrics-csv runs/m150_p0_close_hidden_cause_seed9481/hidden_pair_metrics.csv \
  --episodes 40 --seed 9481 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 \
  --run-dir runs/m151_capability_belief_dataset_seed9481

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_target_dataset \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9482/accepted_pairs.csv \
  --hidden-metrics-csv runs/m150_p0_close_hidden_cause_seed9482/hidden_pair_metrics.csv \
  --episodes 40 --seed 9482 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 \
  --run-dir runs/m151_capability_belief_dataset_seed9482
```

Combine:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_target_dataset \
  --mode combine \
  --dataset-npzs runs/m151_capability_belief_dataset_seed9480/capability_belief_dataset.npz,runs/m151_capability_belief_dataset_seed9481/capability_belief_dataset.npz,runs/m151_capability_belief_dataset_seed9482/capability_belief_dataset.npz \
  --summary-jsons runs/m151_capability_belief_dataset_seed9480/summary.json,runs/m151_capability_belief_dataset_seed9481/summary.json,runs/m151_capability_belief_dataset_seed9482/summary.json \
  --run-dir runs/m151_capability_belief_dataset_multiseed
```

## Artifacts

```text
runs/m151_capability_belief_dataset_seed9480/capability_belief_dataset.npz
runs/m151_capability_belief_dataset_seed9481/capability_belief_dataset.npz
runs/m151_capability_belief_dataset_seed9482/capability_belief_dataset.npz
runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz
runs/m151_capability_belief_dataset_multiseed/summary.json
runs/m151_capability_belief_dataset_multiseed/coverage_summary.csv
```

## Dataset Shape

Combined dataset:

| Array | Shape | Meaning |
| --- | ---: | --- |
| student_p0_i | 240 x 1800 | deployable P0 history for left sample |
| student_p0_j | 240 x 1800 | deployable P0 history for right sample |
| teacher_capability_i | 240 x 3 | future capability target for left sample |
| teacher_capability_j | 240 x 3 | future capability target for right sample |
| teacher_capability_delta | 240 x 3 | signed target delta |
| teacher_capability_abs_delta_z | 240 x 3 | normalized absolute target delta |
| pair_weight | 240 | max normalized target delta |
| hidden_group_distances | 240 x 6 | diagnostic hidden group distances |

## Coverage

Dominant target coverage:

| Target | Count | Fraction |
| --- | ---: | ---: |
| future braking deceleration | 73 | 0.304167 |
| future yaw response | 114 | 0.475000 |
| future lateral accel response | 53 | 0.220833 |

Dominant hidden group coverage:

| Hidden group | Count | Fraction |
| --- | ---: | ---: |
| friction | 82 | 0.341667 |
| braking authority | 10 | 0.041667 |
| drive authority | 38 | 0.158333 |
| tire lateral authority | 15 | 0.062500 |
| mass geometry | 72 | 0.300000 |
| actuator delay | 23 | 0.095833 |

Mean pair weight:

```text
3.481229
```

## Decision

Complete M151 as capability-belief infrastructure:

- the dataset is P0-close and target-divergent;
- student input is deployable P0 history only;
- teacher targets are capability-envelope deltas, not direct `mu` labels;
- hidden diagnostics are stored for training-time weighting and analysis only;
- next step is objective-only sanity on this dataset before any PPO or actor
  input change.
