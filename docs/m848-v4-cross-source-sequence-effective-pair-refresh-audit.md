# M848 V4 Cross-Source Sequence-Effective Pair Refresh Audit

## Purpose

M848 audits M847 before objective design or another implementation.

The audit question is:

```text
Is M847's pair-delta evidence strong enough for objective design, or should the
branch first mine a more source-balanced pair-delta corpus?
```

M848 is audit-only:

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
docs/m847-v4-cross-source-sequence-effective-pair-refresh-implementation.md
runs/m847_v4_cross_source_sequence_effective_pair_refresh/summary.json
runs/m847_v4_cross_source_sequence_effective_pair_refresh/diversity_summary.json
runs/m847_v4_cross_source_sequence_effective_pair_refresh/gate_summary.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_pair_delta_rows.csv
runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_sequence_effective_rows.csv
```

M847 result class:

```text
v4_cross_source_sequence_effective_pair_refresh_sparse_pair_positive
```

## Artifact And Contract Audit

M847 produced the expected paired artifacts:

```text
pair_candidate_rows: 208
balanced_pair_rows: 76
reconstructed_pair_rows: 76
reconstructed_snapshot_rows: 18
sequence_effective_rows: 3648
pair_delta_sequence_rows: 912
accepted_sequence_effective_rows: 145
accepted_pair_delta_rows: 17
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

No actor-input contract change occurred. The use of fault/source metadata is
offline corpus construction only.

## What M847 Proved

M847 resolves the key structural gap left by M844:

```text
M844 accepted_pair_delta_rows: 0
M847 accepted_pair_delta_rows: 17
```

The branch now has evidence that real cross-source pair-delta sequence
directions can move terminal outcome. That is stronger than component-only
sequence controllability.

M847 also passes broad paired-construction gates:

```text
paired_candidate_rows: 76 >= 40
pair_delta_sequence_rows: 912 > 0
accepted_primary_sequence_effective_rows: 145 >= 120
unique_fault_family_pair_count: 17 >= 8
unique_onset_pair_count: 9 >= 5
unique_warmup_pair_count: 5 >= 3
```

## What M847 Did Not Prove

The accepted pair-delta subset is still too narrow:

```text
accepted_pair_delta_rows: 17 < 30
pair-delta unique_left_source_group_count: 3
pair-delta unique_left_seed_count: 2
pair-delta unique_left_fault_family_count: 2
pair-delta max_left_source_group_dominance: 0.7059
pair-delta max_left_seed_dominance: 0.7059
```

The overall accepted set is also dominated:

```text
unique_left_source_group_count: 9 < 10
unique_left_seed_count: 3 < 4
unique_left_fault_family_count: 4 < 5
max_left_source_group_dominance: 0.3034 > 0.30
max_left_seed_dominance: 0.5517 > 0.35
max_direction_family_dominance: 0.6690 > 0.55
```

Most accepted rows are still component-axis rows:

```text
throttle_axis: 97 / 145
steer_axis:    21 / 145
pair_delta:    17 / 145
brake_axis:    10 / 145
```

Therefore M847 is not ready for outcome-coupled objective design as-is.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. Pair-delta evidence exists, but the accepted pair-delta subset is
source/fault concentrated.

### metric_artifact

Secondary label. Direct pair-delta sequence overrides are still offline
controllability diagnostics, not learned response-history self-ID proof.

### not contract_violation

Checksums stayed fixed and no forbidden actor input was introduced.

## Supported Claims

M848 supports:

- real cross-source pair construction works;
- pair-delta sequence controllability exists on this branch;
- component sequence effects remain broader than pair-delta effects;
- the next branch should target pair-delta evidence quality, not PPO.

## Unsupported Claims

M848 does not support:

- learned self-ID proof;
- PPO admission;
- checkpoint promotion;
- objective training on the full M847 accepted corpus;
- claiming the component-heavy M847 accepted set is a strong pair-delta corpus.

## Next Control Variable

The next highest-leverage step is a pair-delta-focused source-balanced mining
design.

M849 should design a no-training runner that:

```text
1. starts from the broader M847 pair_candidate_rows, not only balanced rows;
2. scans pair_delta_positive and pair_delta_negative first;
3. expands pairing tolerance only within pre-registered bounds;
4. selects accepted pair-delta rows with source/fault/seed balance after
   observing pair-delta outcomes;
5. keeps component directions as controls, not as the main acceptance route;
6. routes to expanded boundary bracketing if pair-delta rows remain below 30.
```

This is more targeted than rerunning M847 with larger caps because the current
failure is not pair construction in general. It is accepted pair-delta
concentration.

## Decision

Decision:

```text
admit_pair_delta_focused_source_balanced_mining_design
```

Next:

```text
m849-v4-pair-delta-focused-source-balanced-mining-design
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
