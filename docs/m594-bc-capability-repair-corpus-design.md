# M594 BC Capability Repair Corpus Design

## Purpose

M594 designs the real corpus and runner needed before any capability-repair
smoke training.

This milestone is design-only:

```text
no corpus export
no training
no PPO
no checkpoint promotion
```

## Core Decision

The real capability repair corpus should be collected from closed-loop BC5660
base rollouts, not by retrofitting labels onto the old L2 teacher BC corpus.

Reason:

```text
future-response labels, recurrent hidden state, observation, and action anchor
must all correspond to the same closed-loop state.
```

The old BC corpus is still useful as lineage and behavior reference, but it
does not store simulator state or future-response labels. Reconstructing labels
from only `seed` and `step` would require reproducing the exact rollout policy
and state path. A dedicated rollout corpus is cleaner and less error-prone.

## Corpus Collector

M595 should implement a collector, tentatively:

```text
python -m autodrift.bc_capability_corpus
```

Inputs:

```text
base_checkpoint = runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
env_config      = configs/ppo_m541_matched_l3_variance_4096.json
seeds           = explicit seed list or range
horizon_steps   = future response probe horizon
sample_stride   = step sampling interval
```

Per sampled step, store:

```text
student_obs_seq              (N, 72)
anchor_action_seq            (N, 3)   # BC5660 deterministic action
capability_target_seq        (N, 3)   # future response labels
episode_start_seq            (N,)
done_seq                     (N,)
seed_seq                     (N,)
episode_id_seq               (N,)
step_seq                     (N,)
```

Optional diagnostic-only arrays:

```text
base_hidden_seq              (N, H)   # for analysis, not actor input
base_feature_seq             (N, H)   # for analysis, not actor input
```

The corpus must not store or feed deployable actor inputs such as:

```text
mu
mass
tire stiffness
brake scale
actuator tau
slip
tire force
oracle feasibility
```

Future-response capability labels are allowed only as training/evaluation
targets.

## Train/Validation Split

Use explicit seed blocks:

```text
train seeds:      first non-public block
validation seeds: separate non-public block
```

The validation block is not a private paper holdout. It is a repair-development
validation set and may be used for debugging. Promotion remains blocked.

First smoke-scale recommendation:

```text
train episodes: 16-32
validation episodes: 8-16
sample_stride: 2 or 4
horizon_steps: match existing hidden-envelope probe default
```

The exact seed ranges should be registered in M595 or M596 before export.

## Pair-Ranking Rows

Matched-current ranking rows should be mined from the new capability corpus,
not imported blindly from M586.

Reason:

```text
M586 pairs refer to previous BC5660 rollout snapshots and targets. The repair
corpus needs pair indices that directly reference rows in the new corpus.
```

M595 should either:

1. implement pair mining inside the corpus tool; or
2. write a corpus CSV with row indices and reuse `matched_current_response_ambiguity`
   logic adapted to corpus rows.

Required pair fields:

```text
left_row
right_row
target
target_left
target_right
target_delta
target_std
target_z_delta
visible_distance
left_seed/right_seed
left_step/right_step
```

M596 smoke should use only pairs whose `target_z_delta >= 1.0` and whose source
diversity is summarized before training.

## Action Anchor

The first action anchor should be the BC5660 base deterministic action:

```text
anchor_action_seq = pi_bc5660(obs_t, hidden_t)
```

Reason:

```text
BC5660 is the current behavior-transfer checkpoint. M592-M593 are trying to
make hidden informative without destroying that behavior.
```

L2 teacher actions can be added later, but should not be the first anchor for
this repair because the repair corpus is collected under BC5660 closed-loop
state distribution.

## Smoke Runner

After M595 corpus implementation, M596 should run a small smoke:

```text
base checkpoint: BC5660
objective: M593 capability repair loss
epochs: small
device: cpu unless GPU is explicitly useful
outputs: checkpoint, metrics, summary
promotion: false
```

Required metrics:

```text
train_action_anchor_mse
val_action_anchor_mse
train_capability_regression_loss
val_capability_regression_loss
train_pair_rank_loss
val_pair_rank_loss
metadata.input_contract
metadata.capability_repair.labels_enter_actor_input
```

No route or M591 action-sensitivity claim should be made until the smoke proves
the objective is wired and stable.

## Smoke Pass Criteria

The first smoke should pass only if:

- capability regression loss decreases on train and validation;
- pair ranking loss decreases on train and validation;
- action anchor MSE remains below a pre-registered tolerance;
- checkpoint metadata preserves P0 L3 contract;
- checkpoint is marked unpromoted and non-PPO;
- no capability labels enter actor observation.

Suggested first action-anchor tolerance:

```text
val_action_anchor_mse <= 0.0025
```

This is intentionally conservative; the first repair should not change driving
behavior before hidden capability evidence improves.

## Outputs For M595

M595 should implement:

```text
src/autodrift/bc_capability_corpus.py
tests/test_bc_capability_corpus.py
```

Expected run artifacts for later smoke:

```text
capability_corpus.npz
pairs.csv
target_summary.csv
pair_summary.csv
summary.json
```

## Decision

```text
bc_capability_repair_corpus_design_admit_runner_implementation
```

M594 passes because it defines a closed-loop BC5660 rollout corpus, action
anchor source, future-response labels, matched-current ranking rows, and smoke
metrics without training or actor-input leakage.

## Next

```text
M595: implement the BC capability corpus and pair-ranking runner.
```
