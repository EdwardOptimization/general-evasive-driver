# M820 V4 Low-Margin New Data Route Branch Synthesis

## Purpose

M820 synthesizes the `v4_low_margin_new_data_route` branch from M810 through
M819 before any new implementation milestone.

This is a workflow synthesis milestone:

```text
no replay
no calibrator training
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

The synthesis decision is:

```text
continue
```

The branch should continue, but only into the exact non-PPO calibration-grid
implementation designed by M819. PPO, actor updates, residual-head updates, and
driver promotion remain blocked.

## Evidence Summary

### M810

M810 opened the `v4_low_margin_new_data_route` branch after the previous
retarget branch became geometry-only. It changed the route from post-hoc
retargeting of fixed public anchors to generating near-boundary source states
during scenario collection.

The design introduced:

```text
active diagnostic warm-up modes
joint obstacle/fault timing
boundary search during data generation
history interventions
source-balanced export
strict primary margin threshold = 0.00005
```

### M811

M811 implemented the first no-training data route:

```text
boundary candidates: 2688
source groups: 96
snapshots: 192
replay errors: 0
warm-up artifact rows: 0
primary accepted rows: 0
safe rows: 2146
collision rows: 542
```

This was a clean sparse result, not a runtime failure.

### M812

M812 audited M811 and found the key positive signal:

```text
collision/safe snapshot-axis brackets: 48
closest bracket gap: 0.015385162709582234
primary window: 0.00005
```

The failure mode was a fixed-grid boundary-resolution miss. This admitted
adaptive bracketing rather than threshold relaxation.

### M813

M813 designed deterministic adaptive bracketing over M811 collision/safe edges.
It kept:

```text
alpha = 0.2
primary margin threshold = 0.00005
no training
no PPO
unchanged checksum requirements
source/fault/warm-up/axis diversity gates
```

### M814

M814 implemented the adaptive bracketing route:

```text
attempted brackets: 576
validated/refined brackets: 193
raw primary rows: 101
balanced accepted primary rows: 85
unique seeds: 9
unique source groups: 55
unique source indices: 73
unique fault-family pairs: 8
unique warm-up modes: 4
unique axes: 3
axis counts: 48 lateral, 25 timing, 12 half-width
max seed dominance: 0.235294
max source-group dominance: 0.047059
max fault-pair dominance: 0.235294
max axis dominance: 0.564706
```

Actor and residual-head checksums stayed unchanged. No training, PPO, or
promotion occurred.

This is the central positive evidence of the branch: the new data route plus
adaptive bracketing can produce a source-axis-diverse strict primary corpus.

### M815

M815 audited M814 as a valid corpus pass, not a driver promotion.

Intervention diagnostics remained mechanism-positive:

```text
reset-hidden variants collide on 69 / 101 raw accepted rows
zero-command intervention collides on 67 / 101 raw accepted rows
```

M815 admitted only source-heldout residual calibration design.

### M816

M816 designed the first calibration route:

```text
train only a separate residual gate / calibrator
freeze M568 actor
freeze M761 residual head
split by source_group_id + seed + fault-family pair
run train and holdout exact gates
keep PPO and promotion blocked
```

### M817

M817 implemented the source-heldout calibration probe:

```text
train rows: 57
holdout rows: 28
split units: 55
snapshot lookup rows: 110
missing snapshots: 0
train normal collisions: 0
holdout normal collisions: 0
train intervention collision rate: 0.678363 -> 0.678363
holdout intervention collision rate: 0.702381 -> 0.702381
mean old-behavior action drift: 8.15e-7
max old-behavior action drift: 1.58e-6
actor checksum changed: false
M761 residual-head checksum changed: false
```

The calibrator remained near identity:

```text
scalar gate_mean: 0.998986
```

### M818

M818 audited M817 as harness-positive but not performance-improving.

The key classification:

```text
valid source-heldout retention harness
not meaningful adaptive calibration
not a PPO admission
not a promotion candidate
```

### M819

M819 designed the next follow-up:

```text
compare identity, fixed scalar gates, fixed vector gates, and then adaptive gates
select candidates on train rows only
evaluate holdout rows exactly
rank by normal-margin lift after retention gates
preserve intervention sensitivity
preserve old-behavior drift limits
route to branch synthesis before implementation
```

## Supported Claims

The branch supports these claims:

1. The earlier sparse low-margin problem was not a simulator or instrumentation
   impossibility. It was a boundary-resolution problem.
2. Adaptive bracketing can produce a strict primary low-margin corpus with
   source, fault, warm-up, and axis diversity.
3. The M814 accepted rows retain useful intervention sensitivity under
   reset-hidden and zero-command interventions.
4. The source-heldout calibration harness can evaluate train and holdout normal
   rows, intervention variants, and old-behavior drift without changing actor
   or residual-head weights.
5. M817 proves retention infrastructure, not a useful adaptive calibrator.
6. A non-PPO exact calibration-grid implementation is now justified as the next
   narrow experiment.

## Falsified Claims

The branch falsifies or fails to support these working claims:

```text
The first fixed-grid new-data route is enough to populate the strict primary
low-margin band.
```

M811 found zero primary rows despite broad candidate coverage.

```text
Adaptive bracketing is unnecessary.
```

M814 showed adaptive bracketing was the decisive step that turned M811's
collision/safe brackets into accepted primary rows.

```text
Near-identity residual calibration proves adaptive control.
```

M817/M818 explicitly reject this. Gate values stayed near `0.999`, and no
margin-lift or performance-improvement claim is supported.

```text
The branch is ready for PPO or checkpoint promotion.
```

It is not. Current evidence supports only exact non-PPO calibration-grid
implementation.

## Failure Taxonomy Summary

### scenario_sampling_failure

M811 produced zero primary rows. M812 reclassified this as a fixed-grid
boundary-resolution miss because collision/safe brackets existed. M814 resolved
this specific sampling failure through adaptive bracketing.

### metric_artifact

M817 is the main metric-artifact warning. A near-identity calibrator can pass
retention gates while adding almost no scientific evidence. Future milestones
must report margin lift and nontrivial gate movement, not just retention.

### objective_overfit

Not yet observed in this branch because M817 was near identity. The risk becomes
active in M821: train-selected scalar/vector gates may fail on holdout. M819
therefore requires train-only selection and holdout-only acceptance.

### behavior_regression

Not observed in M817. It remains an active guard because nontrivial residual
scaling could change old behavior or intervention sensitivity.

Rejected failure labels for the branch so far:

```text
contract_violation
training_instability
proof_washout
promotion_gate_failure
private_holdout_contamination
```

No milestone in this branch trained the actor, changed the residual head, ran
PPO, or promoted a checkpoint.

## Public Gate Overfit Risk

The public-gate overfit risk is moderate.

Mitigations already in place:

```text
M814 balanced source groups, seeds, fault-family pairs, warm-up modes, and axes
M817 split by source_group_id + seed + fault-family pair
M817 used holdout rows only for evaluation
M819 requires train-only candidate selection
M819 requires holdout exact acceptance
```

Remaining risks:

```text
M814/M817/M819 still reuse the same public corpus family
M817 showed retention gates can be too easy if the calibrator remains identity
M821 could overfit train rows if holdout failures are used for repair
the current proxy-fault model is not true wheel-level mechanical failure data
```

Rules for the next implementation:

```text
do not tune from holdout failures;
do not claim promotion from public corpus evidence;
do not start PPO after a fixed-grid positive without a separate audit;
rotate or expand the corpus if holdout evidence guides repair.
```

## Next Branch Decision

Decision:

```text
continue
```

The branch should continue into exactly one implementation class:

```text
M821 exact non-PPO calibration-grid implementation
```

Allowed in M821:

```text
identity baseline
fixed scalar gate grid
fixed vector/action-dimension gate grid
train-only candidate ranking
holdout exact acceptance
unchanged actor and residual-head checksums
```

Blocked in M821:

```text
actor training
M761 residual-head training
learned adaptive calibrator training unless explicitly gated after fixed-grid evidence
PPO
checkpoint promotion
holdout optimization
primary-threshold relaxation
```

If M821 finds no nontrivial gate better than identity on holdout, the branch
should not keep tuning calibrators against the same public surface. It should
either pivot back to data generation or close the branch as corpus/harness
evidence.

## Decision

Decision:

```text
v4_low_margin_new_data_route_continue_to_calibration_grid
```

Next blocker:

```text
m821-v4-adaptive-primary-calibration-grid-implementation
```
