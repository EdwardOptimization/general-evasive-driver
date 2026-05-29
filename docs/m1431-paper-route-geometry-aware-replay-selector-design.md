# M1431 Paper-Route Geometry-Aware Replay Selector Design

## Summary

M1431 designs the geometry-aware selector admitted by M1430.

Decision:

```text
geometry_aware_replay_selector_design_admit_implementation
```

M1431 does not run replay, train, run PPO, promote, use private holdout, export
a training corpus, or change actor inputs.

## Problem

M1429 proved that the bounded relocation replay tool works, but the selected
source rows were geometry-poor:

```text
selected_candidate_rows: 128
actual_replay_rows: 384
history_positive_rows: 0
control_positive_rows: 0
selected_unique_source_seeds: 3
selected_unique_variants: 1
selected_max_single_seed_share: 0.75
source_body_x_median: -1.678050
relocated_body_x_clipped_groups: 126 / 128
```

The replay negative is therefore not a valid no-history result. Most selected
snapshots had the obstacle behind the vehicle, and relocation clipped them to
the minimum forward body distance.

## Design Goal

Build a preflight selector that answers before replay:

```text
Does the candidate set contain enough forward, unclipped, source-diverse
obstacle geometries to justify a bounded relocation replay run?
```

This selector is a gate in front of replay. It is not an actor input and is not
used during deployment.

## Inputs

The first implementation should consume the same public source rows and config
used by M1429:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

config:
  configs/m1419_warmup_gate_invasiveness_retune_source_wave.json

candidate rows:
  runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv
```

## Preflight Mechanics

For each candidate row:

```text
1. Prepare the row with the existing bounded replay candidate schema.
2. Reconstruct the preferred trace up to the candidate reveal step.
3. Convert the preferred current TracePoint to an OutcomeSnapshot.
4. Compute obstacle body geometry:
     source_body_x
     source_body_y
     source_half_width
5. Compute the requested relocation geometry without replay:
     relocated_body_x = max(min_body_x, source_body_x + body_longitudinal_offset)
     relocated_body_y = source_body_y + body_lateral_offset
     relocated_half_width = max(min_half_width, source_half_width + half_width_inflation)
6. Mark whether the row was clipped by min_body_x or min_half_width.
7. Apply geometry, diversity, and variant filters before selecting rows.
```

The selector should reuse the existing helpers where possible:

```text
prepare_candidate_frame
collect_fault_trace_window
_trace_to_outcome_snapshot
obstacle_body_geometry
bounded_relocation_geometry
source_diversity
```

## Geometry Gates

The first implementation should reject rows when any of these are true:

```text
source_body_x < 4.0
relocated_body_x <= min_body_x + 1e-6
relocation_body_x_clipped == true
source_half_width < 0.05
relocated_half_width <= min_half_width + 1e-6
obstacle geometry is non-finite
```

Rationale:

```text
source_body_x < 4.0:
  the obstacle is too close or already behind, so replay tests emergency clipping
  rather than a meaningful forward obstacle.

relocated_body_x clipped:
  the candidate's requested pressure did not produce a natural forward
  relocation; it hit the artificial min_body_x bound.
```

## Selection Policy

After preflight, rank candidates by:

```text
1. geometry_pass == true
2. history_variant == true
3. sequence_action_l2_mean descending
4. nonnegative original margin_gap
5. source diversity across seed / capability pair / reveal bucket / variant
```

Then enforce caps:

```text
max_candidate_rows: 128
per_seed_cap: 24
per_capability_pair_cap: 12
per_reveal_bucket_cap: 12
per_variant_cap: 48
```

The selector should prefer multiple history variants. It must not select only
`warmup_removed` if other history variants pass the geometry preflight.

## Pre-Registered Public Gates

A future replay run is admissible only if the preflight summary satisfies:

```text
forward_geometry_rows >= 64
selected_candidate_rows >= 64
unique_source_seeds >= 6
unique_capability_pairs >= 8
unique_reveal_buckets >= 6
unique_history_variants >= 2
max_single_seed_share <= 0.35
relocation_clipped_share <= 0.10
source_body_x_p50 >= 4.0
source_body_x_min >= 4.0
```

If those gates fail, do not run replay with the selected rows. Route to branch
synthesis or source mining.

## Required Outputs

The implementation should write:

```text
geometry_preflight_rows.csv
selected_candidate_rows.csv
rejected_rows.csv
source_diversity_summary.csv
geometry_summary.json
summary.json
```

The summary must include:

```text
input rows
history candidate rows
geometry-pass rows
selected candidate rows
rejected reason counts
source_body_x min / p50 / p95
relocation clipped share
source diversity
history variant diversity
guardrail flags
```

## Guardrails

M1431 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

The geometry selector is a research harness filter. It must not become actor
input, reward shaping, an oracle deployment feature, or a training corpus by
itself.

## Next Route

Admit:

```text
m1432-paper-route-geometry-aware-selector-implementation
```

M1432 should implement the preflight selector and focused tests only. It should
not run bounded replay. Because this branch is approaching the synthesis
cadence, the next replay run after implementation should be preceded by a
branch synthesis or explicit cadence decision.
