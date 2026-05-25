# M863 V4 Pair-Delta Boundary Expansion Branch Synthesis

## Purpose

M863 synthesizes the M853-M862 `v4_pair_delta_boundary_expansion` branch before
any further narrow continuation.

This is synthesis-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Evidence Summary

### M853-M855: Underrepresented Boundary Expansion

M853 designed no-training boundary expansion over underrepresented M825
source/fault/seed families after M850 showed pair-delta positives were
source-concentrated.

M854 implemented the expansion:

```text
target_source_rows: 61
target_unique_seed_count: 12
target_unique_fault_family_count: 9
reconstructed_snapshot_rows: 61
accepted_boundary_rows: 32
pairability_projection_rows: 77
```

But accepted rows all came from recovered existing-boundary sources:

```text
existing_boundary_recovered accepted rows: 32
boundary_new_to_m844 accepted rows: 0
rejected_rows: 151
rejection_reason: no_collision_safe_bracket
```

M855 audited this as a clean source-limited result. The blocker was not
snapshot reconstruction or actor/residual mutation; it was that new sources did
not produce boundary brackets under the tested axis grid.

### M856-M858: Boundary-New Trace Diagnostics

M856 designed a trace-first no-bracket diagnostic for boundary-new-to-M844
sources.

M857 implemented it:

```text
target_trace_sources: 52
primary_boundary_new_to_m844_sources: 44
reconstructed_snapshot_rows: 52
bracket_trace_rows: 1924
traced_source_axis_rows: 132
accepted_boundary_found_extended_source_axes: 0
```

The primary cause was all-safe-wide:

```text
all_safe_wide: 114 / 132 = 0.863636
all_collision_or_negative: 18 / 132 = 0.136364
```

M858 audited this as valid trace evidence. It ruled out simple same-axis
widening as the best immediate continuation and justified closer
obstacle/source generation.

### M859-M861: Closer Obstacle Source Generation

M859 designed no-training closer obstacle/source generation from M857 traces.

M860 implemented it:

```text
generation_plan_rows: 660
primary_source_groups_planned: 44
primary_seed_count_planned: 8
primary_fault_family_count_planned: 9
generated_replay_rows: 660
accepted_generated_boundary_rows: 17
pairability_projection_rows: 38
```

This was an improvement over zero generated boundary rows, but still below
sparse gate:

```text
accepted_generated_boundary_rows: 17 < 32
accepted_boundary_new_to_m844_rows: 17 < 24
unique_seed_count: 4 < 5
pairability_projection_rows: 38 < 40
```

Route-specific evidence:

```text
all_safe_closer_obstacle: 570 replay rows, 17 accepted
all_collision_safer_side: 90 replay rows, 0 accepted
obstacle_lateral_offset: 14 accepted
obstacle_timing: 3 accepted
obstacle_half_width: 0 accepted
```

M861 audited M860 as source-limited but refinement-ready. The key new evidence
was:

```text
groups with accepted boundary row: 17
groups with wide/negative bracket but no accepted row: 13
groups all wide: 84
groups all negative: 18
```

So the generated grid did not simply remain all-wide. It crossed the terminal
margin boundary in a subset of source/axis groups, but often jumped over the
accepted window.

### M862: Generated Boundary Refinement Design

M862 designed the next no-training route:

```text
select M860 same-source same-step same-axis all_safe_closer_obstacle groups
find adjacent wide/negative endpoint brackets
reconstruct the original M825 temporal snapshot
run bounded normal closed-loop bisection/refinement
report refined-only and combined M860+refined coverage
```

M862 also discovered a workflow issue: the branch had reached its 10-milestone
synthesis cadence, so implementation must wait until this synthesis.

## Supported Claims

This branch supports:

1. The pair-delta data bottleneck after M850 was real source/fault/seed
   coverage, not absence of pair-delta controllability.
2. Underrepresented source targeting and snapshot reconstruction work reliably
   on M825/M568/M761 artifacts.
3. Boundary-new-to-M844 sources were mostly too safe/wide under the initial
   expansion grid.
4. Full trace diagnostics can distinguish all-safe-wide, all-collision, and
   accepted/bracket-found cases without training.
5. Closer obstacle/source generation opens real new boundary-new-to-M844 rows:
   M860 found `17` accepted rows where M857 had zero.
6. M860 generated replay contains `13` refinement-ready wide/negative bracket
   groups, making generated-boundary refinement the most targeted next route.
7. The no-training harness preserved actor and M761 residual-head checksums
   across the branch.

## Falsified Claims

This branch falsifies or strongly weakens:

1. M850 pair-delta rows are ready for objective training without broader
   boundary generation.
2. Retargeting underrepresented sources with the original boundary grid is
   enough to create broad boundary-new-to-M844 coverage.
3. Boundary-new-to-M844 failures are mainly reconstruction failures.
4. Widening the same trace grid is the obvious next move after M857.
5. M860 single-axis generated candidates are already sufficient for pair-delta
   replay or objective training.
6. Pairability projection can be treated as pair-delta outcome evidence.

The branch does not falsify:

```text
learned response-history self-ID
generated-boundary refinement
future pair-delta replay after sparse boundary coverage
the long-term driver goal
```

## Failure Taxonomy Summary

### scenario_sampling_failure

Primary recurring label.

The branch repeatedly finds useful signal but not enough source-diverse accepted
coverage:

```text
M854: 32 accepted rows, but 0 boundary-new-to-M844
M857: 0 accepted extended primary source axes
M860: 17 accepted generated boundary rows, below sparse gate
```

### metric_artifact

Secondary recurring risk.

Pairability projection is useful for deciding whether rows are likely pairable,
but it is not a closed-loop pair-delta sequence result. Generated boundary rows
are data-construction artifacts, not learned self-ID proof.

### not contract_violation

Across M853-M862:

```text
no actor input contract change
no hidden/oracle actor inputs
no actor or residual-head training
no PPO
no checkpoint promotion
```

## Public Gate Overfit Risk

The evidence remains public-corpus evidence:

```text
derived from M825/M844/M850/M857 public artifacts
no private holdout
no deployed actor behavior improvement
no wrong-history pair-delta outcome replay in this branch
no objective-trained policy
```

The main overfit risk is now:

```text
the harness may become good at creating boundary rows around known public
sources without producing a broad enough distribution for objective training.
```

The workflow guard should therefore remain:

```text
do not train PPO
do not promote a checkpoint
do not treat generated rows as self-ID proof
do not run pair-delta replay until generated-boundary sparse coverage is met or
explicitly audited
```

## Next Branch Decision

Decision:

```text
continue
```

Continue branch:

```text
v4_pair_delta_boundary_expansion
```

Next milestone:

```text
m864-v4-generated-boundary-refinement-implementation
```

Rationale:

```text
M860/M861 provide direct evidence for the next no-training implementation:
13 generated same-source same-axis wide/negative brackets with no accepted row.
M862 has already specified bracket selection, refinement, artifacts, and gates.
This is a better immediate continuation than broad scenario generation because
the branch has refinement-ready brackets; it is also safer than pair-delta
replay because sparse generated-boundary coverage has not passed.
```

M864 may only implement the no-training generated-boundary refinement runner.
It must not run PPO, train, promote, mutate actor inputs, mutate the M761
residual head, or run pair-delta sequence replay.
