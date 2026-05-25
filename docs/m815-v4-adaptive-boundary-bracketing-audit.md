# M815 V4 Adaptive Boundary Bracketing Audit

## Purpose

M815 audits M814 before any residual calibration, PPO, or checkpoint promotion.

The audit question is:

```text
Does M814 produce a valid source/axis-diverse primary low-margin corpus, and if
so, what is the next safe research step?
```

M815 is audit-only:

```text
no training
no residual calibration
no PPO
no checkpoint promotion
no threshold weakening
```

## M814 Result Recap

M814 produced:

```text
result_class: v4_adaptive_boundary_bracketing_pass
brackets_attempted: 576
brackets_valid: 193
brackets_refined: 193
accepted_primary_raw_rows: 101
accepted_primary_rows: 85
replay_errors: 0
warmup_artifact_rows: 0
bracket_nonmonotone_count: 0
```

The frozen-model invariants passed:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

This rules out instrumentation failure, model mutation, and hidden promotion.

## Diversity Gate

M814 balanced accepted rows:

```text
accepted_primary_rows: 85
unique_accepted_seeds: 9
unique_accepted_source_groups: 55
unique_accepted_source_indices: 73
unique_accepted_fault_family_pairs: 8
unique_accepted_warmup_modes: 4
unique_accepted_boundary_axes: 3
```

Dominance metrics:

```text
max_accepted_seed_dominance: 0.23529411764705882
max_accepted_source_group_dominance: 0.047058823529411764
max_accepted_fault_pair_dominance: 0.23529411764705882
max_accepted_boundary_axis_dominance: 0.5647058823529412
```

Accepted axes:

```text
obstacle_lateral_offset: 48
obstacle_timing: 25
obstacle_half_width: 12
```

This satisfies the M813/M814 source and axis gates:

```text
rows >= 80
seeds >= 8
source groups >= 16
source indices >= 8
fault-family pairs >= 4
warm-up modes >= 2
boundary axes >= 3
max seed dominance <= 0.25
max source-group dominance <= 0.15
max fault-pair dominance <= 0.40
max boundary-axis dominance <= 0.60
at least 10 rows from at least 3 axes
```

## Intervention Diagnostics

M814 replayed interventions for `101` raw accepted rows:

```text
reset_hidden_each_step collisions: 69 / 101
reset_hidden_then_normal collisions: 69 / 101
zero_command_obs collisions: 67 / 101
```

This is useful mechanism evidence. It shows many primary rows remain sensitive
to command-response/history disruption. However, it is not by itself a driver
performance claim and not a checkpoint promotion gate.

## Audit Classification

M815 classifies M814 as:

```text
valid_source_axis_diverse_primary_corpus
```

Failure taxonomy status:

```text
scenario_sampling_failure: resolved for this branch's primary data-route gate
metric_artifact: still a risk for training unless holdout/retention gates are used
objective_overfit: still a risk for any calibration trained directly on M814 rows
```

The important distinction:

```text
M814 proves adaptive bracketing can generate the required corpus.
M814 does not prove a residual calibrator will improve held-out behavior.
```

## Supported Claims

M815 supports:

- adaptive bracketing resolves the fixed-grid miss from M811;
- the strict primary low-margin window is reachable without changing actor inputs or thresholds;
- the new primary corpus is source-diverse and axis-diverse under current gates;
- the corpus is a valid candidate input for a later residual calibration design;
- residual calibration, if attempted, must be guarded by source-heldout and old-gate retention checks.

## Falsified Claims

M815 rejects:

- treating M814 as driver promotion;
- starting PPO directly from M814;
- weakening the primary threshold;
- training a calibrator without source-heldout split and retention gates;
- claiming current-model proxy faults are faithful wheel-level failures.

## Decision

Decision:

```text
admit_adaptive_primary_residual_calibration_design_with_holdout_guard
```

M815 admits a design milestone only. The next design must specify:

- train/holdout split by source group, seed, and fault-family pair;
- normal primary-margin retention objective;
- intervention-sensitivity retention objective;
- old public replay / behavior retention checks from the residual branch;
- no actor weight update;
- no PPO;
- no checkpoint promotion;
- exact post-training gates before any corpus-use claim.

Next blocker:

```text
m816-v4-adaptive-primary-residual-calibration-design
```

M816 should design the calibration problem. It must not implement or run the
calibrator yet.
