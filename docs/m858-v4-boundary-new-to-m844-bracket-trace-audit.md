# M858 V4 Boundary-New-To-M844 Bracket Trace Audit

## Purpose

M858 audits M857 before choosing the next data route.

The audit question is:

```text
Does M857's all-safe-wide trace result justify closer obstacle/source
generation rather than wider same-axis replay or pair-delta mining?
```

M858 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Evidence Inspected

Primary artifacts:

```text
docs/m857-v4-boundary-new-to-m844-bracket-trace-implementation.md
runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/cause_summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/gate_summary.csv
```

M857 result class:

```text
v4_boundary_new_to_m844_bracket_trace_all_safe_wide
```

## Artifact And Contract Audit

M857 produced complete trace artifacts:

```text
target_boundary_new_to_m844_sources: 44
control_existing_boundary_sources: 8
reconstructed_snapshot_rows: 52
snapshot_rejection_rows: 0
traced_source_axis_rows: 132
all_traced_source_axis_rows: 156
bracket_trace_rows: 1924
cause_classified_source_axis_share: 1.0
```

Frozen parameters stayed frozen:

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

## Primary Evidence

For primary boundary-new-to-M844 rows:

```text
all_safe_wide: 114 / 132 = 0.863636
all_collision_or_negative: 18 / 132 = 0.136364
accepted_boundary_found_extended: 0
bracket_found_extended: 0
ambiguous_or_nonfinite: 0
mixed_no_adjacent_bracket: 0
```

The trace completeness gates passed, but the actionable extended-boundary gate
did not:

```text
accepted_boundary_found_extended_source_axes: 0 < 12
accepted_boundary_found_extended_source_groups: 0 < 6
accepted_boundary_found_extended_fault_families: 0 < 4
```

This means the primary M854 new sources are mostly too safe/wide under the
tested obstacle retarget grids. Widening the same grid again is unlikely to be
the highest-leverage next step.

## Control Evidence

The recovered existing-boundary controls produced bracket/accept signals:

```text
control cause rows include:
accepted_boundary_found_initial
accepted_boundary_found_extended
bracket_found_initial
bracket_found_extended
```

This is useful as a sanity check: the trace runner can detect boundary behavior
when boundary behavior exists.

But those controls must not be counted as boundary-new-to-M844 evidence. They
are already known/recovered sources and cannot justify a broad pair-delta
mining claim.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. The boundary-new-to-M844 source pool is mostly not near the
low-margin boundary. The issue is not snapshot reconstruction or checksum
mutation. The branch needs source/obstacle generation that deliberately moves
these sources closer to the collision/success boundary.

### metric_artifact

Secondary risk. Trace rows and controls are diagnostics only. They do not prove
learned self-ID or pair-delta outcome behavior.

### not contract_violation

All frozen checksums and no-training flags are intact.

## Supported Claims

M858 supports:

- M857 is a valid trace diagnostic;
- boundary-new-to-M844 primary traces are mostly all-safe-wide;
- recovered controls validate that the trace runner can detect boundary rows;
- simple wider same-axis replay is not the best next route;
- pair-delta replay remains premature on the new-source branch.

## Unsupported Claims

M858 does not support:

- learned self-ID proof;
- pair-delta outcome evidence;
- objective-ready boundary corpus;
- PPO admission;
- checkpoint promotion;
- treating recovered controls as new-source evidence.

## Decision

Decision:

```text
admit_closer_obstacle_source_generation_design
```

Next:

```text
m859-v4-closer-obstacle-source-generation-design
```

M859 should design a no-training source/obstacle generation route that uses
M857 traces to deliberately create boundary-new-to-M844 low-margin candidates.
The design should prioritize moving all-safe-wide sources closer to the
obstacle boundary and handle the smaller all-collision subset with safer-side
source-step shifts.

Pair-delta replay, objective training, PPO, promotion, actor mutation, and
residual-head mutation remain blocked.
