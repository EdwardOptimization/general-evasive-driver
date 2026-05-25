# M852 V4 Source-Diverse Sequence-Effective Corpus Branch Synthesis

## Purpose

M852 synthesizes the M843-M851 source-diverse sequence-effective corpus branch
before any further narrow continuation.

This is synthesis-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Summary

### M843-M845: Source-Diverse Self-Pair Refresh

M843 designed a source-diverse sequence-effective corpus refresh after M841
showed sparse sequence controllability.

M844 implemented the first refresh by reusing M832 accepted boundary rows as
self-pairs:

```text
accepted_primary_sequence_effective_rows: 57
unique_left_source_group_count: 10
max_left_source_group_dominance: 0.2807
```

This improved source coverage over M841:

```text
M841 unique_left_source_group_count: 4
M844 unique_left_source_group_count: 10
```

But M844 was not a strong corpus:

```text
accepted rows: 57 < 120
unique_left_seed_count: 3 < 4
unique_left_fault_family_count: 4 < 5
unique_fault_family_pair_count: 4 < 8
pair_delta rows: 0
```

M845 audited it as useful but source/fault limited and routed to real
cross-source pairing.

### M846-M848: Real Cross-Source Pair Refresh

M846 designed real cross-source sequence-effective pair refresh with mandatory
pair-delta directions.

M847 implemented it:

```text
pair_candidate_rows: 208
paired_candidate_rows: 76
sequence_effective_rows: 3648
pair_delta_sequence_rows: 912
accepted_primary_sequence_effective_rows: 145
accepted_pair_delta_sequence_effective_rows: 17
```

This fixed the structural M844 gap:

```text
M844 accepted_pair_delta_rows: 0
M847 accepted_pair_delta_rows: 17
```

But M847 remained source-concentrated:

```text
accepted_pair_delta unique_left_source_group_count: 3
accepted_pair_delta unique_left_seed_count: 2
accepted_pair_delta max_left_source_group_dominance: 0.7059
```

M848 audited it as real pair-delta positive but not objective-ready.

### M849-M851: Pair-Delta-First Mining

M849 designed a pair-delta-focused miner so component-axis rows could no longer
satisfy pair-delta gates.

M850 implemented it:

```text
pair_delta_sequence_rows: 1920
accepted_pair_delta_rows: 50
balanced_pair_delta_rows: 24
```

M850 improved raw pair-delta yield:

```text
M847 accepted_pair_delta_rows: 17
M850 accepted_pair_delta_rows: 50
```

But the balanced corpus was still source-limited:

```text
balanced_pair_delta_rows: 24 < 30
balanced_unique_left_source_group_count: 3 < 8
balanced_unique_left_seed_count: 2 < 4
balanced_unique_left_fault_family_count: 3 < 5
source_holdout_public_rows: 0
```

M851 audited this as a data coverage blocker, not an objective-design pass.

## Supported Claims

This branch supports:

1. Sequence-level controllability is real on the low-margin v4 surfaces.
2. Real cross-source pair construction works.
3. Pair-delta sequence directions can change terminal outcome.
4. Pair-delta-first mining improves raw pair-delta yield.
5. The current blocker is source/fault/seed coverage, not absence of
   pair-delta signal.
6. The no-training harness preserved actor and residual-head checksums across
   the branch.

## Falsified Claims

This branch falsifies or strongly weakens:

1. Self-pair component sequence rows are enough for objective design.
2. M841/M844 component sequence positives can be treated as pair-delta evidence.
3. The M847 balanced pair surface is already objective-ready.
4. Pair-delta-first mining alone solves source diversity.
5. PPO or checkpoint promotion is justified by direct sequence override rows.

The branch does not falsify:

```text
learned response-history self-ID
outcome-coupled pair-delta objectives
expanded boundary bracketing over underrepresented sources
the long-term driver goal
```

## Failure Taxonomy Summary

### scenario_sampling_failure

Primary recurring label.

The branch repeatedly finds signal but not enough balanced coverage:

```text
M844: 57 accepted rows, no pair-delta
M847: 17 accepted pair-delta rows, source concentrated
M850: 50 raw accepted pair-delta rows, only 24 balanced rows
```

### metric_artifact

Secondary label.

Direct sequence overrides are controllability diagnostics. They are useful for
constructing future objectives, but they are not learned self-ID proof.

### not contract_violation

Across M843-M851:

```text
no actor input contract change
no hidden/oracle actor inputs
no actor or residual-head training in data-mining milestones
no PPO
no checkpoint promotion
```

## Public Gate Overfit Risk

The evidence is still public-corpus evidence:

```text
derived from M832/M844/M847 public surfaces
direct intervention rows, not deployed actor behavior
no private holdout
no objective-trained policy
no source-holdout split in M850 balanced rows
```

The main overfit risk is now clear:

```text
the harness can find pair-delta positives in a small active set of source groups
but not yet a broad enough distribution for objective training.
```

Therefore:

```text
do not train PPO
do not promote a checkpoint
do not start an outcome objective on M850 as-is
do not continue another narrow candidate replay without expanding boundary data
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Next branch:

```text
v4_pair_delta_boundary_expansion
```

Next milestone:

```text
m853-v4-pair-delta-boundary-expansion-design
```

Rationale:

```text
M850 shows the pair-delta signal exists and can be mined, but the current
boundary/candidate surface does not expose enough source-diverse positives.
The next highest-leverage work is expanded boundary bracketing over
underrepresented source/fault/seed families before another pair-delta mining
pass.
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
