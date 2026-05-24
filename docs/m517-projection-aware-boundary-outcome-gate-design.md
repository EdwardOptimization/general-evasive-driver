# M517 Projection-Aware Boundary Outcome Gate Design

## Purpose

M517 designs the next proof gate after M516 admits a terminal-boundary
mechanism projection surface.

No outcome gate is run in M517. No training, PPO, actor-input change,
checkpoint update, or checkpoint promotion is performed.

## Motivation

M516 selected `292` terminal-boundary projected rows across `6` probe seeds,
`3` targets, `2` configs, `12` projected obstacle buckets, and `46` projection
buckets. The mechanism gate passed and admitted downstream outcome testing.

The existing `tail_aligned_wrong_history_gate` cannot be used unchanged for this
surface because it reconstructs snapshots from the original environment
geometry. M516 proof rows are obstacle-boundary projections: the ego state,
hidden state, and history are natural, but the obstacle geometry is relocated in
body coordinates. A valid outcome gate must preserve that relocated obstacle
geometry during replay.

## Required Gate Semantics

M518 should implement a projection-aware boundary outcome gate with this
semantics:

```text
input:
  runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv

for each selected row and offset:
  reconstruct natural left and right snapshots at left_step + offset
  relocate the left snapshot obstacle to projected_obstacle_body_x/y
  apply projected_obstacle_half_width when available
  replay variants from the relocated left snapshot
  use the right snapshot hidden for wrong_matched_history
```

Variants:

```text
normal_projected
wrong_projected_once
reset_projected
zero_current_projected
zero_action_history_projected
```

Offsets:

```text
0, 2, 4, 8
```

The gate should report both near-term action/trajectory changes and continuation
outcomes. A wrong-history no-effect result is not automatically a controller
failure: fast correction of wrong belief can be desirable. The gate should
separate:

```text
controller behavior:
  wrong belief is corrected quickly by current feedback

proof limitation:
  wrong belief does not affect outcome before correction
```

## Metrics

For each variant and offset:

```text
valid_pair_count
invalid_pair_count
proof_candidate_count
event_row_count
success_drop_count
collision_gap_count
obstacle_completion_drop_count
margin_gap_mean / p90 / max
first_action_distance_mean / p90
trajectory_distance_mean / p90
normal_success_rate
variant_success_rate
normal_margin_mean
variant_margin_mean
```

For wrong-history proof:

```text
wrong_projected_once proof rows
wrong_projected_once event rows
probe_seed_count
target_count
config_count
projected_obstacle_bucket_count
projection_bucket_count
single_seed_share
single_target_share
single_config_share
single_obstacle_bucket_share
single_projection_bucket_share
```

Controls:

```text
reset_projected proof/event rows
zero_current_projected proof/event rows
zero_action_history_projected proof/event rows
```

## Decision Rules

M518 should classify the result into one of:

```text
positive_projected_wrong_history_outcome_proof:
  wrong_projected_once has source/geometry-diverse proof rows and event rows.

margin_only_projected_history_signal:
  wrong_projected_once changes margins but has no event rows.

control_only_projected_sensitivity:
  reset/zero controls degrade but wrong_projected_once does not.

fast_correction_no_effect:
  wrong_projected_once changes first action but closed-loop feedback quickly
  removes outcome difference.

invalid_projection_replay:
  too many projected snapshots fail reconstruction or relocation.
```

## Success Criteria

```text
projection-aware gate runs on M516 targeted pairs
relocated obstacle geometry is preserved during replay
summary separates wrong-history from reset/zero controls
summary reports source/target/config/geometry diversity
result classification is explicit
actor inputs remain unchanged
no checkpoint is promoted
```

## Failure Criteria

```text
gate replays original obstacle geometry instead of projected geometry
gate treats scenario labels as actor inputs
gate conflates wrong-history rows with reset/zero controls
gate treats fast correction as policy failure without evidence
actor contract changes
training or checkpoint promotion is performed
```

## Relation To L3 Belief Policy

This gate still tests mechanism proof, not final driver performance. The recent
review discussion clarified that the main target is L3: a GRU recurrent belief
policy, not merely one-step augmented observation feedback.

If M518 shows only fast correction or margin-only signal, the next research line
should not force more artificial wrong-history outcome rows. It should add a
separate L0/L1/L2/L3 history-value ablation:

```text
L0: current observation only
L1: one-step command-response feedback
L2: finite command-response window
L3: online GRU recurrent belief
```

That ablation should measure whether multi-step recurrent belief improves
capability-envelope prediction and near-boundary control beyond one-frame
feedback.

## Decision

```text
admit_m518_projection_aware_boundary_outcome_gate
```

Next blocker:

```text
m518-projection-aware-boundary-outcome-gate
```
