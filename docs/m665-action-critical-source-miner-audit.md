# M665 Action-Critical Source Miner Audit

## Purpose

M665 audits the negative M664 result before designing another miner. The core
question is whether M664 failed because no wrong-history action signal exists,
or because the action signal appears in source windows that are already failed
under the normal-history branch.

## M664 Evidence

M664 was implementation-clean:

```text
snapshot_count:          473
candidate_pairs:        2400
candidate_rows:         7200
accepted_rows:             0
actor_checksum_changed: false
actor_checkpoint_written: false
ppo_used: false
```

The snapshot bank covered both surfaces:

```text
fresh: 240 snapshots, 60 seeds, 3 targets
ood:   233 snapshots, 60 seeds, 3 targets
```

The compatibility filters were active:

```text
context_distance mean:   0.066210
response_distance mean:  0.090098
hidden_distance mean:    0.023924
```

## What Improved Over M661

M664 did find stronger action divergence than M661:

```text
wrong_first_action_l2 >= 0.002 rows:       5352
wrong_action_sequence_mean_l2 >= 0.006:      60
preferred/rejected mean_l2 >= 0.010:          3
all action thresholds:                       3
max wrong_first_action_l2:                 0.013062
max wrong_action_sequence_mean_l2:         0.010464
max preferred_vs_rejected_action_mean_l2:  0.010464
```

So the broader source miner did not merely reproduce the M661 failure. It found
wrong-history hidden sources that can change the actor output.

## Why It Still Failed

M664 found no outcome-critical evidence:

```text
margin_gap >= 0.010 rows: 0
success_drop_rate:        0.000
max margin_gap:           0.000039
normal_success_rate:      0.610
wrong_success_rate:       0.610
```

The all-action-threshold rows were not usable self-ID supervision because they
were already failed in the normal branch:

```text
normal_margin < 0
normal_success = false
wrong_success = false
success_drop = false
wrong_margin approximately unchanged
```

This means the action gap exists, but it is not yet tied to the desired
counterfactual:

```text
correct history succeeds or has margin;
wrong history changes action;
wrong history loses margin or success.
```

## Failure Classification

M664 is best classified as:

```text
action_gap_positive_outcome_gap_negative
```

Within the existing process taxonomy this is an evidence-bearing negative
result, not a process failure. It is not:

- `contract_violation`: actor inputs were unchanged and metadata stayed outside
  actor observations.
- `training_instability`: no training happened.
- `proof_washout`: no checkpoint was updated.
- `metric_artifact`: the summary reports both action and outcome gates; action
  gap alone was not treated as success.

## Root Cause

The likely root cause is source-window quality.

M664 selected close obstacle-visible snapshots:

```text
fresh obstacle_distance_mean: 2.319 m
ood obstacle_distance_mean:   2.549 m
```

That is useful for finding large action sensitivity, but too late for usable
wrong-history supervision when the normal branch has already failed. The next
source miner should make normal-history outcome a first-class source filter
before pairing wrong histories.

## Rejected Shortcuts

Do not:

- train from the empty M664 corpus;
- accept the three all-action-threshold rows despite negative normal margins;
- weaken the margin/success-drop gate;
- claim self-ID evidence from action divergence alone;
- widen compatibility limits until outcome gaps appear without preserving scene
  validity.

## Decision

```text
action_critical_source_miner_audit_admit_normal_success_boundary_design
```

## Next Branch

M666 should design a normal-success boundary source miner:

```text
1. build a broader snapshot bank across obstacle decision windows;
2. replay normal-history first;
3. keep left snapshots only if normal branch succeeds and has finite positive
   margin within a near-boundary band;
4. then pair wrong histories and require action/outcome divergence;
5. report separate diagnostics for early-safe, near-boundary, and already-failed
   windows.
```

This changes the source filter, not the actor contract or the acceptance
thresholds.

## Next

```text
m666-normal-success-boundary-source-mining-design
```
