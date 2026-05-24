# M660 Action-Divergent Wrong-History Corpus Design

## Purpose

M660 designs a stronger wrong-history corpus after M658 showed that changing
feature views is not enough. The current blocker is likely the corpus/target
definition: M641 rows are hidden-different, but not action-divergent enough to
create a strong rejected-history branch.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Evidence From M659

M659 classified M658 as:

```text
partial_relative_signal_but_absolute_wrong_history_gap_negative
```

The important numbers:

```text
fused wrong_validation_prediction_gap_l2 mean:       0.000471
next_hidden wrong_validation_prediction_gap_l2 mean: 0.001732
next_hidden / fused ratio:                           3.714
next_hidden wrong_validation_gap_mse mean:          -0.0000030
```

So `next_hidden` carries more wrong-history signal than fused features, but the
absolute wrong-history gap remains too weak and gap MSE does not become
positive.

## Design Principle

M661 should not accept a row just because recurrent hidden states differ.

It should accept rows only when the wrong-history branch is action-divergent
and short-horizon relevant:

```text
same/similar current observation
different recurrent history
normal-history branch has a grounded preferred action sequence
wrong-history branch produces a distinct rejected action sequence
wrong-history branch has lower margin / higher risk / worse short-horizon behavior
```

The key change from M641 is the explicit rejected-history target:

```text
preferred_action_sequence
rejected_action_sequence
preferred_margin / risk
rejected_margin / risk
preferred_vs_rejected_action_l2
```

This supports a later preference objective. It is not just a normal target with
an implicit "make wrong hidden different" margin.

## Candidate Inputs

M661 should start from existing BC5660 artifacts:

```text
checkpoint:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

matched-current surfaces:
  runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv
  runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv

surface configs:
  fresh=configs/ppo_m541_matched_l3_variance_4096.json
  ood=configs/eval_m574_moderate_ood_l3.json

normal preferred sequence candidates:
  runs/m636_combined_source7_preserving_shape/accepted_combined_sequences.csv
  runs/m633_targeted_source8_projected_shape/accepted_targeted_sequences.csv
```

M661 may also use M641 rows as diagnostics, but it must not rebuild the next
corpus by blindly copying M641 wrong-history rows.

## Scoring Protocol

For each matched-current pair and candidate decision step:

1. Reconstruct normal and wrong-history snapshots.
2. Roll out normal history for `K` steps.
3. Roll out wrong matched history for the same `K` steps.
4. If a preferred projected sequence is available for the normal branch, roll
   it out as the preferred target.
5. Store the wrong-history base action sequence as the rejected target if it is
   action-divergent and worse than the preferred branch.

Minimum metrics:

```text
wrong_first_action_l2
wrong_action_sequence_mean_l2
wrong_action_sequence_max_l2
normal_vs_wrong_trajectory_l2
preferred_vs_rejected_action_mean_l2
normal_margin
wrong_margin
preferred_margin
rejected_margin
margin_gap = preferred_margin - rejected_margin
risk_gap = rejected_risk - preferred_risk
```

## Acceptance Thresholds

Initial M661 thresholds:

```text
wrong_first_action_l2 >= 0.002
wrong_action_sequence_mean_l2 >= 0.006
preferred_vs_rejected_action_mean_l2 >= 0.010
margin_gap >= 0.010
preferred_margin >= 0.000
rejected_margin <= preferred_margin - 0.010
sequence_length in {5, 7, 9}
```

These thresholds are intentionally above the weak M641/M658 wrong-history
scale, but below the older `0.02` action-screen threshold that BC5660 could not
meet on M586. If M661 finds too few accepted rows, the negative result is useful
and should trigger broader candidate mining rather than threshold weakening
inside the same milestone.

## Diversity Rules

M661 should enforce:

```text
min accepted rows: 80 preferred, 40 required
min physical pairs: 8
min left seeds: 6
min targets: 2
min surfaces: 2 preferred, 1 required
max rows per physical pair fraction: 0.20
max rows per source_index fraction: 0.25
source-heldout split: at least one full source or target held out
```

If source diversity fails, do not train. Audit whether the corpus is too
concentrated or whether a broader miner is needed.

## Required Corpus Fields

M661 should write an NPZ/CSV pair with at least:

```text
observation
normal_hidden
variant_hidden
preferred_action_sequence
rejected_action_sequence
sequence_mask
normal_base_action_sequence
variant_base_action_sequence
preferred_margin
rejected_margin
preferred_risk_score
rejected_risk_score
wrong_first_action_l2
wrong_action_sequence_mean_l2
preferred_vs_rejected_action_mean_l2
source_index
surface
target
variant
split
weight
```

The future objective should be able to compute:

```text
logp(preferred | normal_hidden)
logp(preferred | wrong_hidden)
logp(rejected  | wrong_hidden)
```

without re-running the simulator.

## Required Artifacts

M661 should write:

```text
runs/m661_action_divergent_wrong_history_corpus/summary.json
runs/m661_action_divergent_wrong_history_corpus/action_divergent_corpus.npz
runs/m661_action_divergent_wrong_history_corpus/action_divergent_rows.csv
runs/m661_action_divergent_wrong_history_corpus/candidate_scores.csv
runs/m661_action_divergent_wrong_history_corpus/source_summary.csv
runs/m661_action_divergent_wrong_history_corpus/split_summary.csv
runs/m661_action_divergent_wrong_history_corpus/target_summary.csv
docs/m661-action-divergent-wrong-history-corpus-implementation.md
```

## Pass Criteria

M661 passes as corpus construction if:

```text
accepted rows >= 40
accepted physical pairs >= 8
accepted left seeds >= 6
targets >= 2
source-heldout split is nonempty
mean preferred_vs_rejected_action_mean_l2 >= 0.010
mean margin_gap >= 0.010
actor checksum unchanged
no actor checkpoint written
no PPO used
```

M661 should be classified as negative if it cannot find enough rows under these
thresholds. That would mean BC5660 currently does not contain enough
action-divergent wrong-history behavior on the existing matched-current
surfaces.

## Forbidden Shortcuts

Do not:

- train a head or actor;
- run PPO;
- promote a checkpoint;
- use metadata as actor input;
- use hidden-distance-only acceptance;
- accept rows without explicit rejected-history target/action data;
- tune thresholds after seeing a weak corpus and still call it the original
  gate.

## Decision

`action_divergent_wrong_history_corpus_design_admit_m661`

## Next

`m661-action-divergent-wrong-history-corpus-implementation`
