# M645 BC-v2 Head-Only Smoke Design

## Purpose

M645 designs a frozen-actor smoke test for the M641/M644 BC-v2 sequence-delta
objective. The goal is to test whether BC5660's frozen recurrent policy
features contain enough information to predict the local correction sequences
from M641 before any actor-coupling update is considered.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Frozen Scope

The later M646 implementation must freeze:

- response encoder;
- context encoder;
- online GRU cell;
- response/context fusion;
- actor mean;
- critic;
- log standard deviation;
- every parameter from `runs/m568_scaled_l3_bc_seed5660/checkpoint.pt`.

The only trainable module in M646 may be an auxiliary sequence-delta head:

```text
SequenceDeltaHead(features) -> delta_action_sequence[K, 3]
```

This head is not the deployed actor. It is a diagnostic/auxiliary head to test
feature learnability and source-heldout behavior.

## Features

Use frozen BC5660 features from the normal recurrent hidden branch:

```text
features_normal = frozen_actor.recurrent_features_tensor(observation, normal_hidden)
```

Also evaluate the same head on variant hidden features:

```text
features_variant = frozen_actor.recurrent_features_tensor(observation, variant_hidden)
```

The variant branch is diagnostic only. It is not a training label and must not
be used to mutate the actor.

## Target

Train the auxiliary head to predict sequence deltas:

```text
delta_star = target_action_sequence - normal_base_action_sequence
```

Then reconstruct:

```text
u_pred = normal_base_action_sequence + delta_pred
```

Use `sequence_mask` for all losses. Padding must not contribute.

## Loss

Primary source-balanced masked delta MSE:

```text
L_delta =
  sum_i w_i * mean_ta(mask_it * (delta_pred_ita - delta_star_ita)^2)
```

Report action reconstruction MSE as a derived metric:

```text
L_action =
  sum_i w_i * mean_ta(mask_it * (u_pred_ita - target_action_ita)^2)
```

Because this is head-only, no policy-gradient, log-prob, entropy, critic, or
PPO term is allowed.

## Splits

Use the M641 split:

```text
train:
  sources 13, 14, 5, 30, 0, 8

source_holdout_validation:
  sources 20, 32, 7
```

The source-heldout split is not private promotion evidence. It is a branch-level
sanity check. If a later update is tuned using source-heldout failures, that
split must be treated as contaminated for promotion.

## M646 Command

M646 should implement a runner like:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_v2_head_only_smoke \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --epochs 300 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --seed 6460 \
  --device cpu \
  --run-dir runs/m646_bc_v2_head_only_smoke
```

Required artifacts:

```text
summary.json
train_metrics.csv
validation_metrics.csv
row_predictions.csv
source_head_summary.csv
split_head_summary.csv
sequence_delta_head.pt
```

Do not write an actor checkpoint.

## Metrics

M646 must report:

```text
train_initial_delta_mse
train_final_delta_mse
train_delta_mse_improvement
validation_initial_delta_mse
validation_final_delta_mse
validation_delta_mse_improvement
normal_head_loss
variant_head_loss
normal_variant_prediction_gap_l2
actor_checksum_before
actor_checksum_after
actor_parameters_changed
```

It must also report source-level metrics so a high-count source cannot dominate
the conclusion.

## M646 Pass Criteria

M646 passes as a head-only smoke if:

```text
actor_parameters_changed == false
checkpoint_written == false
head_checkpoint_written == true
train_delta_mse_improvement >= 0.30
validation_delta_mse does not increase
all metrics finite
source-balanced weights preserved
train and source-heldout summaries written
```

If validation improves by at least `0.05`, the head-only result is stronger and
can admit an adapter/actor-coupling design. If validation does not improve but
also does not regress, M646 is still allowed to pass as a learnability smoke,
but M647 must audit before any actor-coupling design.

## Non-Goals

M645/M646 do not claim:

- closed-loop driving improvement;
- recurrent self-identification proof;
- wrong-history outcome sensitivity;
- actor behavior change;
- promotion eligibility.

They only test whether frozen BC5660 features can support the M641 local
sequence corrections through an auxiliary head.

## Failure Classification

| Result | Classification |
| --- | --- |
| actor checksum changes | `contract_violation` |
| train improves and validation regresses | `objective_overfit` |
| metrics are non-finite | `metric_artifact` |
| head cannot improve train loss | `training_instability` |
| implementation writes actor checkpoint | `contract_violation` |

## Decision

`bc_v2_head_only_smoke_design_admit_m646`

## Next

`m646-bc-v2-head-only-smoke-implementation`
