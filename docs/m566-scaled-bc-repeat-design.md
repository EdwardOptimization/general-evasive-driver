# M566 Scaled BC Repeat Design

## Purpose

M566 designs the next L2-to-L3 distillation step after the positive M563-M565
smoke path.

The M563 checkpoint was trained from a tiny non-public corpus but matched L2 on
M564 route-screen and M565 public natural surfaces. That is a strong signal, but
not enough for promotion or PPO continuation.

M566 is design-only. It does not train or promote a checkpoint.

## Objective

Test whether L2-to-L3 behavior cloning remains stable when scaled by:

```text
larger non-public train corpus
larger non-public validation corpus
multiple BC optimizer seeds
fresh route-screen selection seed
no public frozen-source tuning
```

If the effect survives this repeat, the project can then decide whether to run
public diagnostics again or move to fresh generalization gates.

## Fixed Boundaries

Allowed:

```text
teacher = L2 finite-window P0 policy for action target generation
student = L3 online-GRU P0 current-frame policy
student input = student_obs_seq with shape (N, 72)
target = teacher_action_seq with shape (N, 3)
hidden reset = episode_start_seq
```

Forbidden:

```text
do not feed L2 4-frame stack into the L3 student
do not add hidden params / oracle labels / public source rows
do not tune from M565 public frozen-source residuals
do not reuse route-screen seed 17560 for new selection
do not start PPO until scaled BC evidence is stable
do not promote from public diagnostics alone
```

## Seed Plan

Previously used route-screen seeds:

```text
M556 selection: 15560
M560 selection: 16560
M564 selection: 17560
```

Previously used smoke corpus seeds:

```text
M562 train smoke: 18000-18001
M563 validation smoke: 18128-18129
```

M567 should use fresh non-public corpus seeds:

```text
scaled train seeds:      18200-18327  (128 episodes)
scaled validation seeds: 18328-18391  (64 episodes)
```

M569 route-screen selection should use:

```text
route-screen v2 seed: 18560
```

The old route-screen seeds can be reported later as diagnostics, but they must
not choose the next checkpoint.

## Scaled Corpus Export

M567 should run the existing exporter twice:

```text
train:
  teacher checkpoint = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
  teacher env config = configs/ppo_m541_matched_l2_variance_4096.json
  seeds = 18200:18327
  output = runs/m567_scaled_l2_teacher_corpus_train

validation:
  teacher checkpoint = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
  teacher env config = configs/ppo_m541_matched_l2_variance_4096.json
  seeds = 18328:18391
  output = runs/m567_scaled_l2_teacher_corpus_validation
```

Pass criteria:

```text
student_obs_dim = 72
teacher_obs_dim = 288
teacher_stack_stored = false
uses_public_frozen_source_rows = false
transition_count > M562/M563 smoke transition_count
train and validation terminal diagnostics written
```

## BC Repeat

M568 should train a small optimizer-seed family from the scaled corpus:

```text
bc seeds: 5660, 5661, 5662
student env config: configs/ppo_m541_matched_l3_variance_4096.json
hidden_size: 64
learning_rate: 0.001
epochs: 25
```

Each run must write:

```text
checkpoint.pt
train_metrics.csv
summary.json
```

Pass criteria for each candidate:

```text
train_action_mse improves
validation_action_mse improves
checkpoint obs_dim = 72
history_baseline.level = L3_online_gru
ppo_used = false
promoted = false
```

Do not select solely by train MSE. Prefer validation MSE and route-screen.

## Route-Screen Selection

M569 should evaluate all M568 BC checkpoints against L0 and L2 with
route-screen v2:

```text
episodes = 64
seed = 18560
L0 = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
L2 = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
candidates = M568 BC seed checkpoints
```

Selection rule:

```text
candidate must pass L0 success
candidate must pass L0 margin
candidate must pass L0 collision tolerance
candidate should be L2-competitive on success and margin
tie-breakers:
  1. success rate
  2. collision rate
  3. clearance margin
  4. validation action MSE
  5. return
```

If no candidate clears L0, classify the failure before changing BC settings.

## After M569

If the scaled BC repeat passes route-screen:

```text
M570: public diagnostic repeat on M543/M550 surfaces, no promotion
M571: fresh non-public/generalization route distribution
M572: decide whether guarded PPO is justified
```

If it fails route-screen:

```text
audit exposure bias and corpus coverage
consider DAgger-style student-rollout teacher queries
keep PPO blocked
```

## Decision

```text
scaled_bc_repeat_design_admit_m567_scaled_teacher_corpus_export
```

M566 passes because it defines the scaled non-public BC repeat protocol, seed
splits, optimizer-repeat rule, route-screen rule, and no-public-row/no-PPO
boundaries.
