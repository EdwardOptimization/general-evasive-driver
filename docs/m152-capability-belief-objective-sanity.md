# M152 Capability-Belief Objective Sanity

Date: 2026-05-22

## Question

M151 produced a P0-close capability-belief dataset. M152 asks whether a
training-time objective can learn the braking/yaw/lateral future-envelope
targets from deployable P0 history before any actor integration or PPO.

This is objective-only. It does not change the actor observation contract and it
does not prove closed-loop self-identification behavior.

## Contract

Student inputs used:

```text
student_p0_i
student_p0_j
```

Those arrays are deployable P0 history only:

```text
25 frames x 72 P0 human-view features = 1800 dims
```

Teacher targets used:

```text
teacher_capability_i
teacher_capability_j
```

The targets are:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

Training metadata not used as actor inputs:

```text
teacher_capability_delta
teacher_capability_abs_delta_z
pair_weight
dominant_target_index
dominant_hidden_group_index
hidden_group_distances
sample_i
sample_j
```

Hidden diagnostics remain training-time metadata only.

## Implementation

New module:

```text
src/autodrift/capability_belief_objective_sanity.py
```

New tests:

```text
tests/test_capability_belief_objective_sanity.py
```

The objective trains a small MLP on normalized P0 history. The loss contains:

```text
target MSE for left and right samples
pairwise delta MSE for predicted capability difference
```

Losses are reported separately for braking, yaw, lateral, and their pairwise
delta targets.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_objective_sanity \
  --dataset-npz runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz \
  --optimization-seeds 9600,9601,9602 \
  --train-fraction 0.70 \
  --steps 300 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --delta-loss-coef 0.5 \
  --device cpu \
  --run-dir runs/m152_capability_belief_objective_sanity
```

## Artifacts

```text
runs/m152_capability_belief_objective_sanity/summary.json
runs/m152_capability_belief_objective_sanity/seed_summary.csv
runs/m152_capability_belief_objective_sanity/loss_summary.csv
```

## Results

Validation improvements, before minus after:

| Optimization seed | Combined | Target | Delta | Pass |
| ---: | ---: | ---: | ---: | --- |
| 9600 | 2.607162 | 1.012032 | 3.190260 | true |
| 9601 | 2.294578 | 0.932582 | 2.723993 | true |
| 9602 | 2.741131 | 1.146059 | 3.190145 | true |

Mean validation improvements:

| Metric | Improvement |
| --- | ---: |
| combined loss | 2.547624 |
| target loss | 1.030224 |
| pairwise delta loss | 3.034799 |

Mean validation target-loss improvements:

| Target | Improvement |
| --- | ---: |
| future braking deceleration | 0.737355 |
| future yaw response | 1.154201 |
| future lateral accel response | 1.199116 |

Mean validation pairwise-delta improvements:

| Target | Improvement |
| --- | ---: |
| future braking deceleration | 2.243411 |
| future yaw response | 3.999414 |
| future lateral accel response | 2.861573 |

M152 pass summary:

```text
objective_pass: true
seed_pass_count: 3 / 3
pairs: 240
train_pairs: 168
val_pairs: 72
student_feature_dim: 1800
target_dim: 3
```

## Interpretation

M152 is a positive objective-only sanity result. A deployable-history student
can reduce held-out capability target loss and pairwise capability-delta loss
on the M151 P0-close surface across three optimization seeds.

This supports using capability belief as the next training-time objective.
It does not yet prove that a recurrent actor will use the belief in closed-loop
driving, nor that behavior retention or wrong-history degradation will pass.

## Decision

Admit a guarded actor/hidden-state integration test:

```text
admit_for_guarded_actor_hidden_state_integration_test
```

The next step should wire the capability-belief objective into the recurrent
driver training path or an actor-hidden objective harness while preserving the
current P0 human-view actor input contract. It must remain guarded by behavior
retention and intervention gates before PPO or driver promotion.
