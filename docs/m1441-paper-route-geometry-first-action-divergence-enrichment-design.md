# M1441 Paper-Route Geometry-First Action-Divergence Enrichment Design

## Summary

M1441 designs the source-step action-divergence enrichment layer that must sit
between M1440 trace-backed source geometry materialization and the M1438
row-level forward-geometry source miner.

Decision:

```text
geometry_first_action_divergence_enrichment_design_admit_implementation
```

M1441 does not run source materialization, source mining, source preflight,
bounded replay, outcome interventions, training, PPO, promotion, private
holdout, corpus export, or actor-input changes.

## Problem

M1440 materializes valid source geometry:

```text
source_body_x
source_body_y
source_half_width
source_step
reveal_step
```

M1438 selection also needs action-divergence and history-variant fields:

```text
variant
first_action_l2
sequence_action_l2_mean
sequence_action_l2_max
matched_current_pass
bucketed_current_pass
capability_pair
preferred_reveal_bucket
```

Those fields must be computed at the source step after geometry filtering. The
branch must not reuse M1425 reveal-step `outcome_pressure_rows.csv` metrics as
source-step evidence.

## Ordering

The ordering must remain:

```text
trace-backed source geometry
  -> geometry-pass filtering
  -> source-step history-variant action enrichment
  -> M1438 row-level forward-geometry miner
  -> source preflight smoke
  -> bounded replay
```

Do not score action divergence before source geometry passes. That was the
failure pattern from M1425/M1435: action-divergent rows were selected first, and
only later did replay discover that the obstacle geometry was too late or
clipped.

## Inputs

The implementation should consume M1440 rows:

```text
source_geometry_rows.csv
```

Required columns:

```text
source_geometry_index
upstream_source_index
seed
reveal_step
source_step
preferred_fault
wrong_fault
capability_pair
preferred_reveal_bucket
wrong_reveal_bucket
matched_current_pass
bucketed_current_pass
source_body_x
source_body_y
source_half_width
```

The implementation may reconstruct traces again from:

```text
checkpoint
scenario config
seed
preferred_fault
wrong_fault
reveal_step
source_step
```

The implementation should not rely on saved hidden tensors in CSV files.

## Source-Step Variant Semantics

Use the existing warmup-history variant names for compatibility, but interpret
them at the source step:

```text
normal:
  preferred hidden and preferred current observation at source_step

reset_hidden:
  model.initial_hidden at source_step

zero_current_response:
  preferred hidden, but zero explicit current response features in the source observation

warmup_removed:
  model.initial_hidden at source_step

warmup_shortened_8:
  roll model hidden over the last 8 preferred observations before source_step

delayed_warmup_history_8:
  preferred trace hidden 8 steps before source_step

delayed_warmup_history_16:
  preferred trace hidden 16 steps before source_step

wrong_warmup_history_same_reveal:
  wrong-fault hidden at the same source_step

same_recent_wrong_warmup_history:
  wrong-fault hidden before a recent window, then roll preferred recent observations into it
```

The names remain unchanged because downstream selectors already recognize
`WARMUP_HISTORY_VARIANTS`. The metadata should add:

```text
variant_time_anchor: source_step
```

to avoid confusing this with reveal-step metrics.

## Action Metrics

Compute action divergence against the normal source-step policy action.

First-action metrics:

```text
normal_action = pi(source_observation, preferred_source_hidden)
variant_action = pi(source_observation_or_variant_observation, variant_hidden)
first_action_l2 = ||variant_action - normal_action||_2
first_steer_delta
first_throttle_delta
first_brake_delta
```

Short-sequence metrics:

```text
sequence horizon: 8 to 16 steps
normal_actions = closed-loop deterministic rollout from the source snapshot
variant_actions = same source snapshot, variant hidden or observation transform
sequence_action_l2_mean
sequence_action_l2_max
sequence_action_l2_rms
sequence_steps
```

This sequence rollout is an action-distance diagnostic only. It must not classify
success, collision, clearance margin, obstacle completion, or terminal outcome.
Outcome-sensitive replay remains a later bounded replay milestone.

Default admission thresholds for enriched candidates:

```text
min_sequence_action_l2: 0.025
min_first_action_l2: 0.014
```

The implementation should emit:

```text
action_divergent = sequence_action_l2_mean >= 0.025 or first_action_l2 >= 0.014
```

## Output Schema

Write:

```text
enriched_source_geometry_rows.csv
selected_enriched_rows.csv
rejected_rows.csv
variant_summary.csv
source_diversity_summary.csv
summary.json
```

Each enriched row should include all M1440 geometry fields plus:

```text
variant
variant_time_anchor
first_action_l2
first_steer_delta
first_throttle_delta
first_brake_delta
sequence_action_l2_mean
sequence_action_l2_max
sequence_action_l2_rms
sequence_steps
action_divergent
history_variant
control_variant
enrichment_rejection_reason
```

`selected_enriched_rows.csv` should only include rows satisfying:

```text
geometry fields finite
history_variant == true
action_divergent == true
source_body_x >= 4.0
```

The final selected rows must be compatible with the M1438 row-level miner input
schema.

## Selection And Diversity

Selection should rank:

```text
source_body_x larger
sequence_action_l2_mean larger
first_action_l2 larger
matched_current_pass or bucketed_current_pass first
source-step diversity before repeats
```

Caps:

```text
per seed
per capability pair
per reveal bucket
per source step
per variant
```

The first implementation should only implement this enrichment and tests. A
later run milestone can set source-smoke gates. Do not run a public enrichment
smoke in M1442.

## Guardrails

M1441 guardrail status:

```text
source_materialization_run_started: false
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
m1442-paper-route-geometry-first-action-divergence-enrichment-implementation
```

M1442 should implement source-step action-divergence enrichment and focused
tests only. It must not run public source materialization, source preflight,
bounded replay, training, PPO, promotion, private holdout, corpus export, or
actor-input changes.
