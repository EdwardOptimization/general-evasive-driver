# M851 V4 Pair-Delta-Focused Source-Balanced Mining Audit

## Purpose

M851 audits M850 before any further data implementation.

The audit question is:

```text
Did M850 produce an objective-ready pair-delta corpus, or is the branch now at
a synthesis point before boundary expansion?
```

M851 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
docs/m850-v4-pair-delta-focused-source-balanced-mining-implementation.md
runs/m850_v4_pair_delta_focused_source_balanced_mining/summary.json
runs/m850_v4_pair_delta_focused_source_balanced_mining/diversity_summary.json
runs/m850_v4_pair_delta_focused_source_balanced_mining/gate_summary.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/accepted_pair_delta_rows.csv
runs/m850_v4_pair_delta_focused_source_balanced_mining/balanced_pair_delta_rows.csv
```

M850 result class:

```text
v4_pair_delta_focused_source_balanced_mining_source_limited
```

## Artifact And Contract Audit

M850 produced the expected no-training artifacts:

```text
pair_delta_sequence_rows: 1920
accepted_pair_delta_rows: 50
balanced_pair_delta_rows: 24
component_control_rows: 396
train_public_rows: 16
eval_public_rows: 8
source_holdout_public_rows: 0
```

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

No actor input contract change occurred.

## Positive Evidence

M850 improves raw pair-delta yield:

```text
M847 accepted_pair_delta_rows: 17
M850 accepted_pair_delta_rows: 50
```

This means the pair-delta signal is not a one-off artifact from the first M847
balanced subset. Pair-delta outcomes are discoverable when the broader M847
candidate surface is replayed directly.

The accepted pair-delta rows include both directions and hold steps:

```text
pair_delta_negative: 31
pair_delta_positive: 19
hold_steps=6: 28
hold_steps=4: 22
```

## Remaining Limitation

The balanced corpus remains too small and too concentrated:

```text
balanced_pair_delta_rows: 24 < 30
balanced_unique_left_source_group_count: 3 < 8
balanced_unique_left_seed_count: 2 < 4
balanced_unique_left_fault_family_count: 3 < 5
balanced_unique_fault_family_pair_count: 6 < 10
balanced_max_left_source_group_dominance: 0.3333 > 0.30
balanced_max_left_seed_dominance: 0.6667 > 0.35
balanced_max_direction_dominance: 0.6667 > 0.60
source_holdout_public_rows: 0
```

The raw accepted rows are concentrated in four left source groups:

```text
41: 18
47: 16
35: 13
59: 3
```

This is a data coverage limit, not an objective-design signal.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. Pair-delta positives exist, but the current candidate surface
does not provide enough balanced source/fault/seed coverage.

### metric_artifact

Secondary label. Direct pair-delta sequence overrides are still offline
controllability diagnostics. They do not prove learned self-ID.

### not contract_violation

Checksums stayed fixed, no training started, and no forbidden actor input was
introduced.

## Workflow Cadence Audit

This branch has run a full data-mining window after M842:

```text
M843 design source-diverse sequence-effective corpus
M844 implement source-diverse self-pair corpus
M845 audit self-pair source-limited result
M846 design real cross-source pair refresh
M847 implement real cross-source pair refresh
M848 audit sparse pair-positive result
M849 design pair-delta-focused mining
M850 implement pair-delta-focused mining
M851 audit source-limited pair-delta result
```

The next scientific move is probably expanded boundary bracketing over
underrepresented source/fault families. But this branch is now close enough to
the synthesis cadence that another narrow design should not be started directly.

## Supported Claims

M851 supports:

- pair-delta sequence controllability is real;
- pair-delta-first mining improves raw yield;
- current positives remain source-limited;
- objective training and PPO remain premature;
- branch synthesis should precede any new boundary-expansion implementation.

## Unsupported Claims

M851 does not support:

- learned self-ID proof;
- objective-ready pair-delta corpus;
- PPO admission;
- checkpoint promotion;
- continuing into another narrow implementation without synthesis.

## Decision

Decision:

```text
route_to_branch_synthesis_before_boundary_expansion
```

Next:

```text
m852-v4-source-diverse-sequence-effective-corpus-branch-synthesis
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
