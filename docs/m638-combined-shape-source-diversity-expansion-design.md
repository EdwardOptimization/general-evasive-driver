# M638 Combined Shape Source-Diversity Expansion Design

## Purpose

M638 designs the next no-training step after M637.

Question:

```text
Can the M636 combined projected-shape method generalize beyond four focused
source rows before we design any target corpus or actor update?
```

Answer:

```text
Test it on the broader M627 trust-primary non-collision near-miss source set.
Do not train yet.
```

This is design-only:

```text
no rollout
no training
no PPO
no checkpoint promotion
no optimizer admission
no trust-region relaxation
no target-threshold relaxation
```

## Parent Evidence

M636 is the strongest positive diagnostic in this sequence-target branch:

| Source | Accepted candidates | Best improvement | Grid |
| ---: | ---: | ---: | --- |
| `8` | `664` | `0.026789` | source8_recovery_grid |
| `0` | `196` | `0.022995` | source8_recovery_grid |
| `7` | `134` | `0.025043` | source7_preservation_grid |
| `30` | `430` | `0.029507` | source8_recovery_grid |

But M637 correctly blocks target-corpus admission:

```text
accepted source rows: 4
unique physical pairs: 4
unique left seeds: 3
candidate count: 1424, but not source diversity
```

M627 found a broader near-miss set:

```text
near-miss source rows: 13
trust-primary non-collision rows: 9
unique physical pairs: 12 across all M627 rows
unique left seeds: 10 across all M627 rows
surfaces: fresh and ood
targets:
  future_braking_deceleration
  future_lateral_accel_response
  future_yaw_response
```

So the next question is not whether source `8`, `0`, `7`, and `30` can be
fixed. The next question is whether the same projected-shape mechanism can
recover enough source-diverse rows to justify a corpus.

## Source Set

M639 should use:

```text
source table:
  runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv

near-miss table:
  runs/m627_near_miss_trust_geometry/near_miss_sources.csv
```

Primary implementation source filter:

```text
has_trust_near_miss == true
has_collision_near_miss == false
best_primary_failure in {mean_l2_excess, max_l2_excess}
```

Expected primary source ids from M627:

```text
13, 14, 20, 32, 5, 30, 7, 0, 8
```

These include already-accepted high-signal rows as well as rows that M636
recovered. M639 should not restrict the test to only zero-accepted rows, because
the point is source diversity under the combined projected-shape method.

Collision-primary rows should remain separate:

```text
1, 2, 15, 21
```

They may be reported as a diagnostic category, but they must not count toward
source-diversity admission. Collision-primary failure is a different blocker
than trust-primary projection failure.

## Candidate-Shape Design

M639 should implement a reusable expansion runner rather than adding another
hand-targeted four-source script.

Suggested module:

```text
src/autodrift/combined_shape_source_diversity_expansion.py
```

It should reuse existing rollout and projection helpers:

```text
autodrift.trust_projected_sequence_shape.mine_projected_sequences_for_surface
autodrift.trust_projected_sequence_shape.source_recovery_summary
autodrift.combined_projected_sequence_shape.GridSpec
```

The candidate families should preserve M636's two successful local shape ideas,
but run them over the expanded source set:

```text
source8_recovery_style:
  sequence_lengths: 5, 7, 9
  families:
    targeted_constant_delta
    targeted_decay_hold
    targeted_late_brake_hold
    targeted_steer_build_brake_hold
    targeted_smoothstep_hold
  steer_deltas: -0.02, 0.00, 0.02, 0.03, 0.04, 0.05, 0.06
  throttle_deltas: -0.08, -0.07, -0.06, -0.05
  brake_deltas: 0.02, 0.03, 0.04, 0.05, 0.06, 0.08

source7_preservation_style:
  sequence_lengths: 3, 5, 7, 9
  families:
    targeted_constant_delta
    targeted_decay_hold
    targeted_late_brake_hold
  steer_deltas: 0.06, 0.08, 0.10
  throttle_deltas: -0.02, 0.00, 0.02
  brake_deltas: 0.00, 0.02, 0.04
```

Every candidate must still be projected into the existing trust limits:

```text
sequence_mean_l2 <= 0.08
sequence_max_l2 <= 0.10
max_delta_delta_l2 <= 0.08
```

Do not create a large unconstrained global Cartesian grid. If source-specific
target categories are added later, they must be named as separate grid groups
and tracked in artifacts.

## Required Artifacts

M639 should write:

```text
runs/m639_combined_shape_source_diversity_expansion/selected_expanded_source_rows.csv
runs/m639_combined_shape_source_diversity_expansion/expanded_projected_candidates.csv
runs/m639_combined_shape_source_diversity_expansion/accepted_expanded_sequences.csv
runs/m639_combined_shape_source_diversity_expansion/source_recovery_summary.csv
runs/m639_combined_shape_source_diversity_expansion/source_diversity_summary.csv
runs/m639_combined_shape_source_diversity_expansion/summary.json
docs/m639-combined-shape-source-diversity-expansion-implementation.md
```

Required summary keys:

```text
selected_source_rows
selected_source_ids
candidate_rollouts
accepted_expanded_candidates
accepted_source_rows
accepted_unique_physical_pairs
accepted_unique_left_seeds
accepted_surfaces
accepted_targets
accepted_variants
accepted_counts_by_source
accepted_counts_by_grid
trust_limits_preserved
target_corpus_admission_candidate
diagnostic_only
optimizer_admission
```

## Admission Criteria

M639 may classify the result as a target-corpus admission candidate only if all
of these pass:

```text
accepted_source_rows >= 8
accepted_unique_physical_pairs >= 6
accepted_unique_left_seeds >= 6
accepted_surfaces >= 2
accepted_targets >= 2
trust_limits_preserved == true
```

Even if this passes, it is still not permission to train. It only admits:

```text
m640 source-diverse sequence target corpus design
```

## Failure Branches

If M639 fails narrowly:

```text
accepted_source_rows >= 6
accepted_unique_physical_pairs >= 5
accepted_unique_left_seeds < 6
```

then the next step should be another source-diversity audit or source expansion,
not training.

If M639 stays close to the M636 four-source footprint:

```text
accepted_source_rows <= 5
```

then stop pure sequence-grid mining and switch to the stronger directions
identified in the external review:

```text
local terminal-boundary QP / finite-difference correction
hidden-to-action forcing / adapter probe
BC-v2 objective with capability + contrastive + sequence terms
active diagnostic history curriculum
```

This prevents the harness from becoming an endless candidate-grid search.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
combined_shape_source_diversity_expansion_design_admit_m639
```

Next:

```text
m639-combined-shape-source-diversity-expansion-implementation
```
