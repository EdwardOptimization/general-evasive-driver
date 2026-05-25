# M855 V4 Pair-Delta Boundary Expansion Audit

## Purpose

M855 audits M854 before another boundary implementation or any pair-delta
replay.

The audit question is:

```text
Did M854 broaden low-margin boundary coverage enough for pair-delta mining, or
did it expose a more specific boundary-new-to-M844 bracket failure?
```

M855 is audit-only:

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
docs/m854-v4-pair-delta-boundary-expansion-implementation.md
runs/m854_v4_pair_delta_boundary_expansion/summary.json
runs/m854_v4_pair_delta_boundary_expansion/boundary_diversity_summary.json
runs/m854_v4_pair_delta_boundary_expansion/target_source_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/accepted_boundary_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/rejected_rows.csv
runs/m854_v4_pair_delta_boundary_expansion/pairability_projection_rows.csv
```

M854 result class:

```text
v4_pair_delta_boundary_expansion_source_limited
```

## Artifact And Contract Audit

M854 produced the required artifacts and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
checkpoint_promoted: false
```

This is not a contract violation.

## Positive Evidence

Target selection worked:

```text
target_source_rows: 61
target_unique_source_group_count: 61
target_unique_seed_count: 12
target_unique_fault_family_count: 9
reconstructed_snapshot_rows: 61
snapshot_rejection_rows: 0
```

M854 also produced some usable boundary and pairability evidence:

```text
accepted_boundary_rows: 32
unique_source_group_count: 17
unique_fault_family_count: 7
unique_boundary_axis_count: 3
pairability_projection_rows: 77
diagnostic_pairability_projection_rows: 125
projected_pairable_source_groups: 13
```

Compared with M850 balanced pair-delta rows, these accepted boundary rows are
not limited to the active M850 source groups `35`, `41`, and `47`. So M854 did
expand beyond the M850 active pair-delta set.

## Limitation

The strong and sparse expansion gates did not pass:

```text
accepted_boundary_rows: 32 < sparse 50 < strong 80
unique_source_group_count: 17 < sparse 20 < strong 32
unique_seed_count: 4 < sparse 6 < strong 8
pairability_projection_rows: 77 < sparse 80 < strong 160
```

The main limitation is more specific than generic source concentration:

```text
target boundary_new_to_m844 rows: 44
target existing_boundary_recovered rows: 17

accepted existing_boundary_recovered rows: 32
accepted boundary_new_to_m844 rows: 0

rejected_rows: 151
rejection_reason: no_collision_safe_bracket
```

M854 therefore recovered and densified already-known M844 boundary source
families, but it did not open genuinely new boundary sources from M825.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. Broad source selection and snapshot reconstruction work, but the
current bracketing grid does not find collision/success brackets for
boundary-new-to-M844 sources.

### metric_artifact

Secondary risk. Pairability projection is only a geometric and first-action
diagnostic. It must not be reported as pair-delta sequence outcome evidence.

### not contract_violation

Checksums stayed fixed, no optimizer started, no PPO ran, and actor inputs were
not changed.

## Interpretation

M854 should not be followed immediately by objective design or PPO.

It also should not be followed by pair-delta mining as a broad source-diverse
claim, because the accepted boundary set is still below sparse gates and is
entirely recovered from sources already represented in M844 boundary rows.

The next useful question is:

```text
Why do boundary-new-to-M844 sources fail to bracket?
```

The current M854 artifacts do not preserve every initial and expansion
evaluation for rejected axes, so they cannot tell whether each no-bracket source
is:

```text
all-safe wide-margin
all-collision
non-monotone / ambiguous
axis-range too narrow
source-step mismatch
geometry outside useful window
```

## Decision

Decision:

```text
admit_boundary_new_to_m844_bracket_trace_design
```

Next:

```text
m856-v4-boundary-new-to-m844-bracket-trace-design
```

M856 should design a no-training bracket-trace diagnostic that logs all
initial/expansion evaluations for boundary-new-to-M844 rejected source axes
before changing thresholds, running pair-delta replay, or generating new source
families.

PPO, checkpoint promotion, actor training, residual-head training, objective
training, and pair-delta sequence replay remain blocked.
