# M597 BC Capability Repair Objective Smoke Design

## Purpose

M597 designs the first objective smoke after M596 exported train and validation
capability corpora.

This milestone is design-only:

```text
no smoke training
no PPO
no route evaluation
no checkpoint promotion
```

## Scope Decision

The first smoke should freeze the entire actor and train only a capability head
on the recorded BC5660 hidden state:

```text
input = base_next_hidden_seq
target = capability_target_seq
trainable = CapabilityHead only
frozen = ActorCritic / response encoder / GRU / fusion / action head
```

Reason:

```text
before changing the driver, verify that M596 capability labels and pair rows
contain learnable signal on the existing hidden manifold.
```

This is not yet a repaired driver. It is a data/objective wiring smoke.

## Objective

Use the M593 losses, but with actor frozen:

```text
L = 1.0 * L_capability_regression
  + 0.25 * L_capability_rank
```

Action anchor is still measured:

```text
action_anchor_mse = ||base_action_from_checkpoint - anchor_action_seq||^2
```

But actor parameters are frozen, so no action-anchor optimization is needed in
this smoke. The expected value should be near zero, allowing only numerical
tolerance.

## Inputs

Train:

```text
runs/m596_bc_capability_corpus_train_smoke/capability_corpus.npz
runs/m596_bc_capability_corpus_train_smoke/pairs.csv
```

Validation:

```text
runs/m596_bc_capability_corpus_validation_smoke/capability_corpus.npz
runs/m596_bc_capability_corpus_validation_smoke/pairs.csv
```

Base checkpoint:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

## M598 Implementation

M598 should implement a small head-only smoke runner:

```text
python -m autodrift.bc_capability_repair_smoke
```

Minimum outputs:

```text
capability_head.pt
train_metrics.csv
validation_metrics.csv
summary.json
docs/m598-bc-capability-repair-objective-smoke-implementation.md
```

The runner should:

1. load train/validation capability corpora;
2. load train/validation pair CSVs;
3. train `CapabilityHead(hidden_size=64, output_dim=3)` on
   `base_next_hidden_seq`;
4. compute regression and ranking losses on both splits;
5. compute action-anchor MSE from stored `anchor_action_seq`;
6. write summary and metrics;
7. not save or promote a modified actor checkpoint.

## First Smoke Hyperparameters

Use conservative CPU-scale settings:

```text
epochs = 200
learning_rate = 0.003
rank_loss_weight = 0.25
batch_size = full-batch or all rows
seed = 5980
device = cpu
```

The corpora are tiny enough for deterministic full-batch training.

## Metrics

Required summary metrics:

```text
train_initial_regression_loss
train_final_regression_loss
validation_initial_regression_loss
validation_final_regression_loss
train_initial_rank_loss
train_final_rank_loss
validation_initial_rank_loss
validation_final_rank_loss
train_action_anchor_mse
validation_action_anchor_mse
actor_parameters_changed
labels_enter_actor_input
promoted
ppo_used
```

## Pass Criteria

M598 should pass only if:

- train regression loss decreases by at least `30%`;
- validation regression loss decreases by at least `10%`;
- train ranking loss decreases by at least `10%`;
- validation ranking loss does not increase by more than `10%`;
- train and validation action-anchor MSE are `<= 1e-8`;
- actor parameters are unchanged;
- output is explicitly unpromoted and non-PPO;
- capability labels remain training targets only.

If regression improves but rank does not, the next step should redesign pair
sampling before any actor fine-tune.

If neither improves, the next step should audit corpus target variance or
hidden-predictability before adding model capacity.

## Explicit Non-Claims

M598 must not claim:

```text
driver improvement
hidden self-ID proof
wrong-history action sensitivity
route/OOD performance
promotion readiness
```

Those require later milestones after a successful head-only smoke.

## Decision

```text
bc_capability_repair_smoke_design_admit_head_only_implementation
```

M597 passes because it registers a narrow, head-only objective smoke that tests
whether the M596 capability corpus has learnable signal without modifying the
driver.

## Next

```text
M598: implement and run the head-only capability repair objective smoke.
```
