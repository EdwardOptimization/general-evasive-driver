# M1437 Paper-Route Forward Geometry Source Mining Design

## Summary

M1437 designs a new source-mining route after M1435/M1436 showed the M1425
pressure-row pool is too late or too close for forward unclipped replay.

Decision:

```text
forward_geometry_source_mining_design_admit_implementation
```

M1437 does not run source mining, source preflight, bounded replay, outcome
interventions, training, PPO, promotion, private holdout, corpus export, or
actor-input changes.

## Problem

M1435 exhausted all `846` M1425 pressure rows under the forward geometry gate:

```text
geometry_pass_rows: 0
selected_candidate_rows: 0
source_body_x_max: 3.908281
raw_relocated_body_x_max: 3.495281
```

This means the next source miner must not start from M1425 pressure rows. It
must mine earlier or different snapshots where the obstacle is naturally ahead
of the ego vehicle before any action-divergence or replay scoring.

## Design Goal

Build a no-training source miner that prioritizes source geometry first:

```text
1. reconstruct traces at candidate source steps;
2. measure source obstacle geometry;
3. reject too-close, behind, or clipped relocation rows;
4. only then compute action divergence and matched-current metadata;
5. export a source-smoke candidate pool for a later preflight run.
```

The key change is ordering:

```text
old route:
  action divergence -> proxy pressure -> replay/preflight discovers geometry is invalid

new route:
  forward geometry -> action divergence -> preflight smoke -> replay design
```

## Source Timing

The miner should sample earlier source steps relative to the existing reveal
step:

```text
source_step_offsets_from_reveal:
  -32
  -24
  -16
  -8
  0
```

Rows should preserve both:

```text
source_step
reveal_step
source_to_reveal_steps
```

The first smoke can still use the M1419/M1421 scenario family and M1362 base
checkpoint, but it must not reuse M1425 pressure rows as the source pool.

## Geometry Gates

Apply before action-divergence scoring:

```text
source_body_x >= 4.0 required
source_body_x >= 6.0 preferred
raw_relocated_body_x >= 4.0 required
relocation_body_x_clipped == false
source_half_width >= 0.05
relocation_half_width_clipped == false
finite obstacle geometry only
```

The relocation grid should favor forward geometry:

```text
body_longitudinal_offset:
  0.0
  1.0
  2.0
  4.0

body_lateral_offset:
  -0.4
   0.0
   0.4

half_width_inflation:
  0.0
  0.2
  0.4
```

Do not use negative longitudinal offsets in the first source-mining pass. The
previous branch already showed negative offsets convert late rows into clipped
near-body placements.

## Candidate Scoring

After geometry passes, compute public diagnostic fields:

```text
sequence_action_l2_mean
first_action_l2
matched_current_pass
bucketed_current_pass
capability_pair
preferred_reveal_bucket
history_variant
source_body_x
raw_relocated_body_x
relocation_body_x_clipped
```

Selection should rank:

```text
geometry_pass first
source_body_x larger
raw_relocated_body_x larger
sequence_action_l2_mean larger
matched_current or bucketed-current rows first
source diversity before repeat rows
```

## Source Smoke Gates

The first implementation/run should target:

```text
source_rows >= 512
geometry_pass_rows >= 128
selected_candidate_rows >= 128
unique_source_seeds >= 12
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
unique_history_variants >= 2
max_single_seed_share <= 0.25
relocation_clipped_share <= 0.05
source_body_x_min >= 4.0
source_body_x_p50 >= 6.0
raw_relocated_body_x_min >= 4.0
```

These are source viability gates only. Passing them does not prove history
necessity and does not admit training.

## Required Outputs

Implementation should write:

```text
forward_geometry_source_rows.csv
selected_candidate_rows.csv
rejected_rows.csv
source_diversity_summary.csv
geometry_summary.json
summary.json
```

Summary fields:

```text
source_rows
geometry_pass_rows
selected_candidate_rows
source_step_offsets
source_body_x min / p50 / p95
raw_relocated_body_x min / p50 / p95
relocation_clipped_share
selected diversity
guardrail flags
```

## Guardrails

M1437 guardrail status:

```text
source_mining_started: false
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1438-paper-route-forward-geometry-source-miner-implementation
```

M1438 should implement the source miner and focused tests only. It should not
run the source smoke. A later run milestone can evaluate whether the source
miner actually produces forward geometry.
