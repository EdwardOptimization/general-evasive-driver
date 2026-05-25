# M813 V4 Adaptive Boundary Bracketing Design

## Purpose

M813 designs the next no-training data route after M812 classified M811 as a
fixed-grid boundary-resolution miss.

The design question is:

```text
How should we refine M811 collision/safe edges into strict primary low-margin
rows without weakening alpha, thresholds, source diversity, or actor contract?
```

M813 is design-only:

```text
no implementation
no replay
no actor training
no residual-head training
no calibrator training
no PPO
no checkpoint promotion
```

## M812 Diagnosis

M811 generated useful collision/safe structure:

```text
boundary_search_replay_rows: 2688
collision_negative: 542
safe_or_positive: 2146
snapshot_axis_brackets: 48
bracket_axes:
  obstacle_lateral_offset: 40
  obstacle_timing: 8
```

But fixed candidate deltas skipped the strict primary band:

```text
primary_0_to_5e-5: 0
near_5e-5_to_1e-3: 0
minimum positive margin: 0.0029221692398473387
maximum negative margin: -0.0007608713848834547
minimum snapshot-axis bracket gap: 0.015385162709582234
```

The correct next step is not calibration. The correct next step is adaptive
closed-loop boundary refinement.

## Contract

The actor remains:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

M814 must not add deploy-time inputs:

```text
mu
mass / tire / brake / actuator hidden parameters
slip ratio
tire force
friction margin
oracle feasibility labels
TTC
required clearance
reference trajectory
success/collision/progress labels
```

M814 may use simulator metadata only for offline corpus generation, balancing,
and audit diagnostics.

## Core Idea

M814 should treat each source snapshot plus boundary axis as a one-dimensional
closed-loop boundary problem:

```text
same frozen actor
same frozen residual head
same snapshot hidden state
same alpha = 0.2
same max continuation
vary one offline scenario parameter
measure closed-loop min_clearance_margin
```

The target is:

```text
0.0 <= min_clearance_margin <= 0.00005
```

The active unit is:

```text
source_group_id + snapshot_uid + boundary_axis + parameter interval
```

## Bracket Sources

M814 should start from M811-style source collection, not only from persisted CSV
rows. M811 did not persist `TemporalSnapshot` objects, so the implementation
should regenerate source groups deterministically and then refine brackets in
memory.

Inputs:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
M811 source group recipe
M811 warm-up recipe
M811 alpha = 0.2
```

Candidate axes:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
fault_activation_step
fault_severity
```

Primary refinement should prioritize axes that have or can produce a bracket:

```text
1. obstacle_lateral_offset
2. obstacle_timing
3. obstacle_half_width
4. fault_activation_step / fault_severity as diagnostic axes
```

Fault-axis refinement may be discontinuous because activation step is integer
and severity can change closed-loop behavior non-smoothly. These axes can
contribute to source coverage and diagnostics, but a final pass still requires
multi-axis evidence, not a fault-axis-only corpus.

## Bracket Construction

For each snapshot and axis, M814 should first establish a valid bracket:

```text
collision side:
  reconstructed normal replay
  collision == true or min_clearance_margin < 0

safe side:
  reconstructed normal replay
  success == true
  collision == false
  min_clearance_margin > 0
```

If M811-style coarse candidates already contain both sides, use the nearest
collision and nearest safe candidates:

```text
negative endpoint = max negative margin
positive endpoint = min positive margin
```

If only one side exists, M814 may run bounded bracket expansion:

```text
obstacle_lateral_offset:
  expand along the direction that moves obstacle away from or toward ego path

obstacle_timing:
  expand body longitudinal offset in both earlier/later directions

obstacle_half_width:
  expand half-width down for safe side or up for collision side

fault_severity:
  expand severity scale within the current-model proxy range only

fault_activation_step:
  expand by integer steps within the scenario limits only
```

Expansion limits:

```text
max_expansion_attempts_per_axis: 6
max_refinement_attempts_per_bracket: 12
max_total_replays: pre-registered by implementation manifest
```

If no valid bracket is found, export the failure row and do not keep searching
unboundedly.

## Refinement Algorithm

Use deterministic bracket refinement, not random search.

For continuous axes:

```text
1. evaluate midpoint
2. if accepted primary row, record accepted and optionally continue once for
   neighboring robustness
3. if midpoint collides or margin < 0, replace collision endpoint
4. if midpoint is safe with margin > primary threshold, replace safe endpoint
5. stop when accepted, max iterations reached, parameter interval is too small,
   or repeated non-monotone behavior is detected
```

For obstacle half-width, monotonicity is expected locally:

```text
larger half-width -> lower clearance margin
```

For lateral offset and timing, monotonicity is not guaranteed globally. M814
should therefore use local bracket refinement with a non-monotone guard:

```text
if two consecutive midpoint evaluations move margin away from zero on both
endpoints, mark bracket_nonmonotone and stop that bracket
```

For integer axes such as fault activation step:

```text
use integer bisection / neighbor sweep
do not claim continuous primary resolution
classify accepted rows as diagnostic unless axis diversity also passes
```

## Acceptance

An accepted primary row must satisfy:

```text
reconstructed == true
success == true
collision == false
0.0 <= min_clearance_margin <= 0.00005
actor checksum unchanged
residual-head checksum unchanged
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Accepted rows should also replay history interventions when the primary row is
found:

```text
normal
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
delayed_history
scaled_response_history
wrong_history_from_matched_fault if available
```

M814 should not require intervention failures for data-route acceptance, but it
must export intervention diagnostics. Calibration remains blocked until a later
audit decides whether the corpus is safe to use.

## Balance Gates

M814 primary pass must keep the M811/M810 balance standard:

```text
accepted primary rows >= 80
unique seeds >= 8
unique source groups >= 16
unique source indices >= 8
unique fault-family pairs >= 4
unique warm-up modes >= 2
unique boundary axes >= 3
max seed dominance <= 0.25
max source-group dominance <= 0.15
max fault-family-pair dominance <= 0.40
max boundary-axis dominance <= 0.60
normal collision rate in accepted rows == 0.0
```

At least `10` accepted rows must come from at least `3` boundary axes.

Important classification rule:

```text
If M814 finds primary rows on only obstacle_lateral_offset and obstacle_timing,
the result may be diagnostic-positive, but it is not a source/axis-diverse pass.
```

This prevents replacing the previous half-width-only artifact with a new
two-axis artifact.

## Output Artifacts

M814 should write:

```text
src/autodrift/v4_adaptive_boundary_bracketing.py
tests/test_v4_adaptive_boundary_bracketing.py
runs/m814_v4_adaptive_boundary_bracketing/summary.json
runs/m814_v4_adaptive_boundary_bracketing/source_group_rows.csv
runs/m814_v4_adaptive_boundary_bracketing/bracket_seed_rows.csv
runs/m814_v4_adaptive_boundary_bracketing/bracket_refinement_rows.csv
runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv
runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv
runs/m814_v4_adaptive_boundary_bracketing/source_balance_summary.csv
runs/m814_v4_adaptive_boundary_bracketing/axis_balance_summary.csv
runs/m814_v4_adaptive_boundary_bracketing/bracket_failure_rows.csv
runs/m814_v4_adaptive_boundary_bracketing/fault_proxy_limitations.md
docs/m814-v4-adaptive-boundary-bracketing-implementation.md
```

Summary fields must include:

```text
accepted_primary_rows
accepted_primary_raw_rows
unique_accepted_seeds
unique_accepted_source_groups
unique_accepted_source_indices
unique_accepted_fault_family_pairs
unique_accepted_warmup_modes
unique_accepted_boundary_axes
max_accepted_seed_dominance
max_accepted_source_group_dominance
max_accepted_fault_pair_dominance
max_accepted_boundary_axis_dominance
brackets_attempted
brackets_valid
brackets_refined
bracket_nonmonotone_count
bracket_expansion_fail_count
replay_errors
warmup_artifact_rows
actor_backbone_changed
residual_head_changed
training_started
optimizer_started
ppo_used
promoted
result_class
```

## Result Classes

M814 should classify results as:

```text
v4_adaptive_boundary_bracketing_pass
v4_adaptive_boundary_bracketing_sparse
v4_adaptive_boundary_bracketing_axis_concentrated
v4_adaptive_boundary_bracketing_source_concentrated
v4_adaptive_boundary_bracketing_bracket_sparse
v4_adaptive_boundary_bracketing_nonmonotone
v4_adaptive_boundary_bracketing_replay_error
v4_adaptive_boundary_bracketing_warmup_artifact
v4_adaptive_boundary_bracketing_contract_violation
```

Only `v4_adaptive_boundary_bracketing_pass` may admit a later audit for
possible corpus use. It still must not directly admit training, PPO, or
promotion.

## Implementation Guidance

M814 should reuse M811 components where possible:

```text
build_fault_variants
build_source_groups
collect_warmup_snapshots
replay_residual_sequence_variant
relocate_temporal_snapshot
select_source_balanced_rows
```

It should add small pure functions for:

```text
axis parameter extraction
axis parameter application
bracket endpoint selection
midpoint proposal
non-monotone detection
result classification
```

These functions should be unit-tested without loading Torch checkpoints.

## Decision

Decision:

```text
adaptive_boundary_bracketing_design_admit_m814
```

Next blocker:

```text
m814-v4-adaptive-boundary-bracketing-implementation
```

M814 may implement and run the no-training adaptive bracketing route. It must
not run residual calibration, PPO, or promotion.

If M814 still finds no source/axis-diverse primary rows, the next step should be
an audit, not another immediate refinement branch.
