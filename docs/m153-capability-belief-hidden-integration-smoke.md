# M153 Capability-Belief Hidden Integration Smoke

Date: 2026-05-22

## Question

M152 showed that a flat deployable-history MLP can learn the M151
capability-belief target. M153 asks whether the same target can be attached to
the current recurrent driver architecture without changing actor inputs or
starting broad PPO.

This is still a smoke test. It does not prove closed-loop driver behavior and it
does not promote a policy.

## Contract

Input:

```text
student_p0_i
student_p0_j
```

Each sample is reshaped into:

```text
25 x 72 canonical P0 human-view frames
```

Driver structure:

```text
ActorCritic(
  obs_dim=72,
  act_dim=3,
  actor_encoder="human_view_online_gru",
)
```

Feature source:

```text
response_hidden
```

The capability head reads the final recurrent response hidden state. It does
not read hidden simulator parameters, hidden diagnostics, `mu`, feasibility
labels, controller mode, path errors, TTC, or tire diagnostics.

Training-time target:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

Training-time metadata not used as actor input:

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

## Implementation

New module:

```text
src/autodrift/capability_belief_hidden_integration.py
```

New tests:

```text
tests/test_capability_belief_hidden_integration.py
```

The harness trains:

```text
response_encoder
online_gru_cell
capability_belief_head
```

Loss:

```text
target MSE for left and right samples
pairwise delta MSE for predicted capability difference
```

The actor head is not used for behavior claims in this smoke.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_hidden_integration \
  --dataset-npz runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz \
  --optimization-seeds 9610,9611,9612 \
  --train-fraction 0.70 \
  --steps 300 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-size 128 \
  --history-window 25 \
  --feature-source response_hidden \
  --delta-loss-coef 0.5 \
  --device cpu \
  --run-dir runs/m153_capability_belief_hidden_integration_smoke
```

## Artifacts

```text
runs/m153_capability_belief_hidden_integration_smoke/summary.json
runs/m153_capability_belief_hidden_integration_smoke/seed_summary.csv
runs/m153_capability_belief_hidden_integration_smoke/loss_summary.csv
```

## Results

Validation improvements, before minus after:

| Optimization seed | Combined | Target | Delta | Pass |
| ---: | ---: | ---: | ---: | --- |
| 9610 | 1.674818 | 0.612447 | 2.124743 | true |
| 9611 | 1.877988 | 0.721843 | 2.312291 | true |
| 9612 | 1.700866 | 0.632542 | 2.136648 | true |

Mean validation improvements:

| Metric | Improvement |
| --- | ---: |
| combined loss | 1.751224 |
| target loss | 0.655611 |
| pairwise delta loss | 2.191227 |

Mean validation target-loss improvements:

| Target | Improvement |
| --- | ---: |
| future braking deceleration | 0.423007 |
| future yaw response | 0.757553 |
| future lateral accel response | 0.786272 |

Mean validation pairwise-delta improvements:

| Target | Improvement |
| --- | ---: |
| future braking deceleration | 2.124797 |
| future yaw response | 2.877059 |
| future lateral accel response | 1.571825 |

M153 pass summary:

```text
integration_smoke_pass: true
seed_pass_count: 3 / 3
pairs: 240
train_pairs: 168
val_pairs: 72
actor_encoder: human_view_online_gru
feature_source: response_hidden
```

## Interpretation

M153 is a positive recurrent-integration smoke. The M152 capability-belief
target can be optimized through the same response encoder and online GRU family
used by the current human-view driver, using only canonical P0 observation
history.

This result is weaker than a closed-loop driver result. The actor head was not
used to make an avoidance-behavior claim, and no behavior retention,
wrong-history, reset-hidden, or rollout-margin gate has run.

## Decision

Admit guarded behavior and wrong-history gate design:

```text
admit_guarded_behavior_and_wrong_history_gate_design
```

The next step should define or implement a guard that connects capability-belief
training to driver behavior without allowing PPO or driver promotion to proceed
unless behavior retention and intervention degradation are preserved.
