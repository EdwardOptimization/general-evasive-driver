# M629 Trust-Projected Sequence Shape Design

## Purpose

M629 designs the next no-training sequence candidate pass after M628.

Question:

```text
Can M627 trust-primary near misses be converted into accepted source rows by
projecting or smoothing action sequences back inside the existing trust limits?
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

M627 found:

```text
near_miss_candidates: 802
near_miss_sources: 13
primary mean_l2_excess: 542
primary max_l2_excess: 185
primary candidate_collision: 75
candidate_off_road: 0
candidate_spin_out: 0
```

M628 split the source rows into:

```text
trust-primary low/zero accepted sources: 30, 7, 0, 8
collision-primary sources: 1, 2, 15, 21
high-count already accepted sources: 13, 14, 20, 32, 5
```

M629 focuses on the first group only. Collision-primary rows should remain
visible in artifacts but should not be used as trust-only evidence.

## Source Filter

The M630 implementation should read:

```text
runs/m627_near_miss_trust_geometry/near_miss_sources.csv
runs/m627_near_miss_trust_geometry/near_miss_candidates.csv
runs/m624_longer_low_amplitude_sequence_miner/sequence_candidates.csv
runs/m616_expanded_sequence_source_miner/expanded_sources.csv
```

Default focused source filter:

```text
accepted_candidate_count <= 3
best_primary_failure in {mean_l2_excess, max_l2_excess}
has_collision_near_miss == false
```

Expected focused source ids from M627:

```text
30
7
0
8
```

The implementation may also write a diagnostic comparison for all
trust-primary sources, but admission decisions must be source-level, not
candidate-count-level.

## Projection Rule

The current sequence miner builds a base action sequence and adds a
`delta_sequence`. It then rejects candidates when any of these limits fail:

```text
sequence_mean_l2 <= 0.08
sequence_max_l2 <= 0.10
max_delta_delta_l2 <= 0.08
per_step_action_l2 <= 0.10
```

M630 should add a radial projection pass over the raw `delta_sequence` before
rollout:

```text
metrics = trust_metrics(base_action_sequence + delta_sequence, base_action_sequence)

scale = min(
  1.0,
  0.10 / max(sequence_max_l2, eps),
  0.08 / max(sequence_mean_l2, eps),
  0.08 / max(max_delta_delta_l2, eps)
)

projected_delta_sequence = scale * delta_sequence
```

Then rebuild the candidate through the existing `_make_candidate` path and
assert:

```text
projected.sequence_mean_l2 <= 0.08 + tolerance
projected.sequence_max_l2 <= 0.10 + tolerance
projected.max_delta_delta_l2 <= 0.08 + tolerance
projected.trust_region_ok == true
```

This is not a trust-region relaxation. It is a deterministic projection into
the existing trust region.

## Shape Families

M630 should compare projected variants of the current families:

```text
projected_constant_delta
projected_decay_pulse
projected_steer_then_brake
projected_brake_release_then_steer
```

It should also add smoother low-amplitude scale families:

```text
projected_linear_ramp
projected_half_sine_pulse
projected_s_curve_pulse
```

All new families must still use independent steer / throttle / brake action
components and the same physical action bounds. Do not convert output into
acceleration commands or add rule-based maneuver modes.

## Candidate Grid

Use the M624 grid as the baseline:

```text
sequence_lengths: 3, 5, 7
steer_deltas: existing M624 deltas, including +/-0.06
throttle_deltas: existing M624 deltas
brake_deltas: existing M624 deltas
```

M630 may include a small projection-only expansion around the near-miss signs,
but it must report the grid explicitly and keep the raw M624 comparison
available.

## Artifacts

M630 should write:

```text
runs/m630_trust_projected_sequence_shape/projected_sequence_candidates.csv
runs/m630_trust_projected_sequence_shape/accepted_projected_sequences.csv
runs/m630_trust_projected_sequence_shape/unaccepted_projected_rows.csv
runs/m630_trust_projected_sequence_shape/source_recovery_summary.csv
runs/m630_trust_projected_sequence_shape/summary.json
docs/m630-trust-projected-sequence-shape-implementation.md
```

Required candidate columns:

```text
source_index
source_tier
surface
target
variant
family
raw_family
sequence_length
projection_scale
raw_sequence_mean_l2
raw_sequence_max_l2
raw_max_delta_delta_l2
sequence_mean_l2
sequence_max_l2
max_delta_delta_l2
candidate_margin
margin_improvement
candidate_risk_score
risk_improvement
accepted
rejection_reason
candidate_collision
candidate_off_road
candidate_spin_out
```

Required source summary columns:

```text
source_index
accepted_before_m624
accepted_after_projection
best_projected_margin_improvement
best_projected_family
best_projection_scale
trust_primary
collision_primary
recovered_by_projection
```

## Interpretation Rules

Positive diagnostic signal:

```text
projected candidates recover at least one low/zero accepted trust-primary
source while preserving all trust limits and safety checks.
```

Strong positive signal:

```text
projected candidates recover at least two of sources 30, 7, 0, 8.
```

Negative diagnostic signal:

```text
projection scales useful candidates so much that margin/risk improvement falls
below threshold on all focused sources.
```

Safety split:

```text
collision-primary rows remain collision-primary after projection
```

That would support a later safety-shaping branch rather than trust-region
relaxation.

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
trust_projected_sequence_shape_design_admit_m630
```

Next blocker:

```text
m630-trust-projected-sequence-shape-implementation
```
