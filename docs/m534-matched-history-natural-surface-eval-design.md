# M534 Matched History Natural Surface Eval Design

## Purpose

M534 designs the next evidence layer after M533. The matched short-train route
is stable, but route metrics do not prove recurrent history value. The next
step must evaluate the trained L0/L2/L3 checkpoints on the public natural
history-value surfaces from M497/M487/M524/M526.

No training is run in M534. No checkpoint is promoted.

## Why A New Evaluator Is Needed

The existing `tail_aligned_wrong_history_gate` is not directly suitable for
matched L0/L2/L3 evaluation:

```text
1. It requires an online recurrent checkpoint.
2. It reconstructs tail snapshots by rolling the evaluated checkpoint itself.
3. If L0, L2, and L3 each reconstruct their own trajectories, the current
   state is no longer matched across baselines.
```

For this milestone family, the evaluation must compare policies on the same
natural source states. Therefore M535 should implement a frozen source-surface
evaluator instead of reusing the recurrent-only gate.

## Public Diagnostic Surfaces

Use the natural surfaces that produced M524/M526 history-value diagnostics:

```text
m497_natural_belief:
  env configs:
    configs/m494_natural_belief_short_reveal_zero_relvel.json
    configs/m494_natural_belief_warmup_capability_zero_relvel.json
  pair CSVs:
    runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv
    runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv

m487_critical_window:
  use the combined natural tail outcome surface already summarized by M524.
  This surface is public diagnostic evidence, not a private holdout.
```

Projected surfaces such as M520 must remain separate and must not be mixed into
the natural-surface claim.

## Frozen Source-Surface Semantics

M535 should use M399 as the source policy for reconstructing source states:

```text
source checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

For each source surface row and each tail offset:

```text
1. Roll the source policy on the source env config and seed.
2. Deep-copy the source env at left_tail_step.
3. Store the source observation at that tail step.
4. For L0 and L2 baselines, evaluate from that frozen source observation.
5. For L3 baselines, build the target actor hidden by feeding the same source
   observation sequence through the target actor up to the frozen tail step,
   then continue closed-loop from the frozen source env copy.
```

This is an off-policy frozen-surface evaluation. It asks:

```text
Given the same natural state and command-response history observed on the
source trajectory, which baseline chooses better continuation actions?
```

It is not a replacement for later fully closed-loop scenario-distribution eval.

## Checkpoint Mapping

Evaluate all nine short-train checkpoints from M532/M533:

```text
seed 3530:
  L0 runs/m532_matched_l0_short_train_seed3530/checkpoint.pt
  L2 runs/m532_matched_l2_short_train_seed3530/checkpoint.pt
  L3 runs/m532_matched_l3_short_train_seed3530/checkpoint.pt

seed 3531:
  L0 runs/m533_matched_l0_short_train_seed3531/checkpoint.pt
  L2 runs/m533_matched_l2_short_train_seed3531/checkpoint.pt
  L3 runs/m533_matched_l3_short_train_seed3531/checkpoint.pt

seed 3532:
  L0 runs/m533_matched_l0_short_train_seed3532/checkpoint.pt
  L2 runs/m533_matched_l2_short_train_seed3532/checkpoint.pt
  L3 runs/m533_matched_l3_short_train_seed3532/checkpoint.pt
```

Each checkpoint must pass metadata validation:

```text
checkpoint.config.history_baseline_level == declared level
checkpoint.metadata.history_baseline.input_contract == P0_human_view_no_wheel_no_oracle
```

## Metrics

For each baseline, surface, target, seed, and tail offset, report:

```text
success rate
obstacle completion rate
collision rate
terminal reason histogram
return mean
steps mean
min_clearance_margin mean/p10/p90
first action mean and std
```

For matched baseline comparisons, report:

```text
L3 - L0 margin gap
L3 - L2 margin gap
L2 - L0 margin gap
L3 obstacle-completion advantage
L2 obstacle-completion advantage
event-subset advantage on M526 event rows
source diversity: surfaces, probe seeds, targets, tail offsets
```

M526 event rows should be reported as an overlay:

```text
all natural rows
M526 event subset
non-event diagnostic rows
```

The event subset is public diagnostic data, not a private holdout.

## Acceptance For M535

M535 should implement the frozen source-surface evaluator with focused tests.
It does not need to run the full natural eval yet.

Minimum M535 requirements:

```text
can load L0, L2, and L3 checkpoints;
rejects checkpoint metadata/declared-level mismatches;
can roll source M399 and replay a frozen source snapshot;
uses feedforward action path for L0/L2;
uses off-policy source observation sequence to construct L3 hidden;
writes row CSV, summary CSV, and summary JSON;
does not promote a checkpoint.
```

## Later Evidence Rule

Only after M535 implementation passes should M536 run the natural eval. If M536
finds L3 better on M526 event subset but not on broader rows, that is useful
diagnostic evidence, not final proof. Paper-level claims still require fresh
holdout surfaces and broader scenario-distribution evaluation.

## Decision

```text
admit_m535_frozen_source_surface_eval_implementation
```
