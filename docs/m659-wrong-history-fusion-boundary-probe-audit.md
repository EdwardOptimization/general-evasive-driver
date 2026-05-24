# M659 Wrong-History Fusion-Boundary Probe Audit

## Purpose

M659 audits the negative M658 frozen feature-view comparison probe and chooses
the next branch.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M658 Classification

M658 is classified as:

```text
partial_relative_signal_but_absolute_wrong_history_gap_negative
```

The result is not a pure failure of normal learning. Normal validation remained
good for every view. It is specifically a failure to produce a strong
source-heldout rejected-history branch.

## Key Evidence

M658 summary:

```text
diagnostic_passed: false
passed_views: []
fused_weak_seed_count: 3
actor_parameters_changed: false
actor_checkpoint_written: false
ppo_used: false
promoted: false
```

Mean by view:

| View | Normal Val MSE | Wrong Val Gap MSE | Wrong Val Gap L2 | Gap L2 / Fused |
| --- | ---: | ---: | ---: | ---: |
| fused | 0.000486 | -0.0000005 | 0.000471 | 1.000 |
| next_hidden | 0.000491 | -0.0000030 | 0.001732 | 3.714 |
| fused_plus_next_hidden | 0.000483 | -0.0000027 | 0.001374 | 2.890 |

The important nuance:

```text
next_hidden gives a relative signal increase,
but absolute wrong-history gap is still too small.
```

It never reaches:

```text
wrong_validation_prediction_gap_l2 >= 0.005
wrong_validation_gap_mse >= 0.00010
```

## What M658 Proved

M658 supports:

```text
pre-fusion recurrent state carries more wrong-history signal than fused actor features
```

because `next_hidden` improves wrong-history prediction L2 by about `3.7x` over
the same-run fused baseline.

## What M658 Did Not Prove

M658 does not prove:

```text
the current M641 wrong-history rows are enough for self-ID training;
the M652 objective is correct;
the fusion boundary is the only blocker;
auxiliary head success would transfer to closed-loop behavior;
any checkpoint should be promoted.
```

The source-heldout branch remains weak, and gap MSE is negative on average.
That means the diagnostic head is not reliably making wrong-history prediction
worse with respect to the normal corrective target.

## Rejected Next Steps

Do not:

- continue tuning the same fused-only M652 contrast coefficient;
- couple the M658 `next_hidden` head into the actor;
- run PPO;
- treat relative L2 improvement as closed-loop self-ID evidence.

## Decision

The next blocker should be the corpus and target definition:

```text
M660 action-divergent wrong-history corpus design
```

The current M641 BC-v2 corpus has only `103` wrong-history rows, concentrated
in source `30` and source `32`, and supplies a normal target sequence but no
explicit rejected-history target sequence. M658 suggests that even a better
feature view cannot rescue weak/ambiguous wrong-history supervision.

M660 should design a corpus refresh that selects rows where wrong history is
not merely different in hidden space, but action-divergent and outcome-relevant:

```text
same current observation / similar visible state
different recurrent history
normal-history action sequence has a grounded target
wrong-history action sequence has a distinct rejected target or bad rollout
source-heldout wrong-history branch remains visibly different
```

Useful starting artifacts include:

```text
runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv
runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
runs/m633_targeted_source8_projected_shape/accepted_targeted_sequences.csv
runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv
```

The design should learn from the M498 result: wrong-history first-action
differences can exist while closed-loop trajectory differences quickly vanish.
So M660 must score both first-action divergence and short-horizon trajectory or
margin divergence.

## Next Branch Requirements

M660 should pre-register:

```text
candidate pool and source-diversity limits
wrong-history first-action distance threshold
short-horizon trajectory/action distance threshold
normal near-boundary or target-quality threshold
explicit rejected-history target/action fields
source-heldout split
no actor update / no PPO / no promotion
```

## Decision Label

`wrong_history_fusion_boundary_probe_audit_admit_action_divergent_corpus_design`

## Next

`m660-action-divergent-wrong-history-corpus-design`
