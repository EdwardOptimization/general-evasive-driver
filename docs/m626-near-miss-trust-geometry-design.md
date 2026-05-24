# M626 Near-Miss Trust Geometry Design

## Purpose

M626 designs a no-training analyzer after M625 found that M624 has many
near-miss candidates that meet the margin-improvement target but fail safety or
trust checks.

Question:

```text
Which exact constraints block M624 near misses, and can the next candidate-shape
step stay inside the existing trust region?
```

M626 is design-only:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
no trust-region relaxation
no target-threshold relaxation
```

## Inputs

M627 should analyze:

```text
runs/m624_longer_low_amplitude_sequence_miner/sequence_candidates.csv
runs/m624_longer_low_amplitude_sequence_miner/unaccepted_rows.csv
runs/m624_longer_low_amplitude_sequence_miner/accepted_sequences.csv
runs/m624_longer_low_amplitude_sequence_miner/summary.json
```

Trust limits remain:

```text
sequence_mean_l2 <= 0.08
sequence_max_l2 <= 0.10
max_delta_delta_l2 <= 0.08
```

Utility thresholds remain:

```text
margin_improvement >= 0.02
or risk_improvement >= 0.05
```

## Candidate Near-Miss Filter

M627 should define candidate near misses as rows satisfying:

```text
accepted == false
and (
  margin_improvement >= 0.02
  or risk_improvement >= 0.05
)
```

Then classify why the candidate is not accepted.

Do not include already accepted candidates in the near-miss table; they should
only be used for comparison.

## Trust Failure Classification

For each near-miss candidate, M627 should compute:

```text
mean_l2_excess = max(0, sequence_mean_l2 - 0.08)
max_l2_excess = max(0, sequence_max_l2 - 0.10)
delta_delta_excess = max(0, max_delta_delta_l2 - 0.08)
```

It should write boolean flags:

```text
fails_mean_l2
fails_max_l2
fails_delta_delta_l2
candidate_collision
candidate_off_road
candidate_spin_out
```

Primary failure should be deterministic and ordered:

```text
candidate_collision
candidate_off_road
candidate_spin_out
mean_l2_excess
max_l2_excess
delta_delta_excess
insufficient_utility
other
```

Note: the current sequence acceptance checks trust region before collision, but
the analyzer should still report collision/off-road/spin flags so future audits
do not confuse trust and safety failures.

## Source-Level Summary

M627 should aggregate near-miss candidates by source row:

```text
source_index
source_tier
surface
target
variant
left_seed / right_seed
left_step / right_step
candidate_count
near_miss_count
best_margin_improvement
best_risk_improvement
best_primary_failure
min_mean_l2_excess
min_max_l2_excess
min_delta_delta_excess
has_collision_near_miss
has_trust_near_miss
```

This is the key artifact for deciding whether source-level diversity is blocked
by:

```text
1. a small trust-region excess that might be fixed by better candidate shapes;
2. a large trust-region excess that indicates the current trust region prevents
   the maneuver;
3. collision/safety under candidate prefixes;
4. source rows that remain below utility threshold even with K=7.
```

## Artifacts

M627 should write:

```text
runs/m627_near_miss_trust_geometry/near_miss_candidates.csv
runs/m627_near_miss_trust_geometry/near_miss_sources.csv
runs/m627_near_miss_trust_geometry/summary.json
docs/m627-near-miss-trust-geometry-analyzer.md
```

Summary should include:

```text
candidate_rows
near_miss_candidates
near_miss_sources
near_miss_sources_by_tier
primary_failure_counts
constraint_failure_counts
sources_with_margin_threshold_near_miss
sources_with_trust_near_miss
sources_with_collision_near_miss
best_margin_improvement
median_mean_l2_excess
median_max_l2_excess
median_delta_delta_excess
```

## Interpretation Rules

If most near misses fail only `mean_l2_excess` with small `max_l2_excess`, the
next design should consider lower-amplitude longer sequences or smoother
candidate shapes while preserving limits.

If most near misses fail `max_l2_excess` by a large amount, the current trust
region is the main blocker. Do not relax it automatically; record that as a
design tradeoff.

If near misses are mostly collision/off-road/spin, the next step should be
candidate safety shaping or source re-mining, not sequence length expansion.

If near misses cover many new source rows but require only small trust changes,
the next design may add a projected candidate family that normalizes candidate
deltas back into the existing trust region instead of widening the region.

## Contract Checks

```text
actor_input_changed: false
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
near_miss_trust_geometry_design_admit_m627
```

Next blocker:

```text
m627-near-miss-trust-geometry-analyzer
```
