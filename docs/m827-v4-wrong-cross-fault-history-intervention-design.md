# M827 V4 Wrong-Cross-Fault History Intervention Design

## Purpose

M827 designs the missing intervention identified by M826:

```text
current emergency geometry + current observation
but recurrent hidden/history from a matched different hidden-dynamics source
```

The design question is:

```text
Can we turn M825 matched action-divergent proxy pairs into a real closed-loop
wrong-history intervention that tests response-history self-identification,
rather than only zero-command or reset-hidden sensitivity?
```

M827 is design-only:

```text
no implementation
no replay
no actor update
no M761 residual-head update
no PPO
no checkpoint promotion
```

## Motivation

M825 found some history-sensitive rows, but M826 audited the signal as sparse
and dominated by `zero_command_obs`:

```text
accepted_self_id_rows: 18 / required 120
accepted seeds: 2
accepted source groups: 3
accepted warm-up modes: 1
zero_command_obs max margin gap: 0.028255885109984114
response_delay_obs max margin gap: 0.00006529045199066275
wrong_cross_fault_history: unsupported
```

M825 also found a useful diagnostic artifact:

```text
matched_pair_rows: 256
unique_fault_family_pair_count: 16
unique_fidelity_pair_count: 3
unique_left_fault_family_count: 7
unique_right_fault_family_count: 5
unique_left_warmup_mode_count: 3
unique_right_warmup_mode_count: 3
unique_onset_pair_count: 6
```

These pairs are not proof yet. They are candidate pairs where apparent geometry
and current ego response are close enough, but fault family and first action are
different. M828 should use them to run real wrong-history replay.

## Claim Boundary

Allowed claim after implementation:

```text
Under current single-track/proxy hidden dynamics, injecting recurrent history
from a matched different-fault source degrades action or margin.
```

Forbidden claim:

```text
The actor sees or uses fault labels.
```

Forbidden claim:

```text
The current model physically represents true single-wheel, split-mu,
stuck-caliper, halfshaft, suspension, or wheel-speed sensor faults.
```

The actor input remains P0 human-view no-wheel/no-oracle:

```text
ego response
actuator state
previous physical commands
road/free-space/obstacle geometry
recurrent hidden state from past command-response history
```

Fault names, fidelity classes, and pair IDs are logging and source-selection
metadata only.

## Source Inputs

M828 should use M825 artifacts:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/normal_replay_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

`matched_pair_rows.csv` provides left/right candidate IDs. The implementation
should join each ID back to `candidate_plan_rows.csv` and reject pairs whose
plan rows are missing or no longer reconstruct.

## Reconstruction

For each accepted pair:

```text
left = current target source
right = wrong-history source
```

M828 should reconstruct both temporal snapshots by re-running the same source
collection path used by M825:

```text
source row -> fault spec + seed + warm-up mode
collect_warmup_snapshots(...)
match snapshot_uid
```

The left snapshot is then relocated to the left target geometry:

```text
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
```

The right snapshot is not used as the environment. It supplies only the wrong
history hidden state and optional wrong-history diagnostics.

## Replay Semantics

M828 should replay the left relocated environment under these variants:

```text
normal
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
command_shift_obs
response_delay_obs
wrong_cross_fault_hidden
```

The decisive new variant is:

```text
wrong_cross_fault_hidden:
  env = copy(left relocated env)
  obs_t = left current observation
  hidden_t = right.hidden
  action_t = policy(obs_t, hidden_t)
  rollout continues in left env after the first action
```

This tests whether the actor's recurrent belief from a different vehicle/fault
history causes an incorrect maneuver in the same current scene.

Optional diagnostic variants:

```text
wrong_cross_fault_hidden_then_normal:
  use right.hidden at step 0 only, then normal recurrent update in left env

wrong_cross_fault_history_recomputed:
  recompute right hidden from right.history_start_hidden and right.history_observations,
  then inject it into left env
```

The first implementation may start with `wrong_cross_fault_hidden` and log the
optional variants as unsupported if not implemented.

## Pair Rejection Rules

Reject a matched pair if any condition holds:

```text
left or right candidate_id missing from candidate_plan_rows
left or right snapshot_uid cannot be reconstructed
left relocation fails
left/right fault family is equal
left/right ego_response_distance > 0.08
left/right obstacle_geometry_distance > 0.08
left/right first_action_l2 < 0.02
left normal replay is not finite
left normal margin is non-finite
pair uses future_only fidelity class
```

Source balancing should limit dominance by:

```text
left seed
right seed
left source group
right source group
fault-family pair
warm-up mode pair
onset-bucket pair
fidelity pair
```

## Metrics

For every replay row:

```text
normal_success
normal_collision
normal_margin
variant_success
variant_collision
variant_margin
margin_gap_from_normal = normal_margin - variant_margin
prefix_l2_mean_vs_normal
first_action_l2_vs_normal
variant_to_right_action_distance
wrong_history_closer_to_right_action
```

For wrong-history rows, also log:

```text
left_fault_family
right_fault_family
left_fidelity_class
right_fidelity_class
left_warmup_mode
right_warmup_mode
left_onset_bucket
right_onset_bucket
ego_response_distance
obstacle_geometry_distance
first_action_l2_between_normal_left_and_normal_right
```

## Accepted Row Classes

### Primary Wrong-History Rows

Required:

```text
left normal replay succeeds or has finite non-collision margin
wrong_cross_fault_hidden margin_gap_from_normal >= 0.01
wrong_cross_fault_hidden first_action_l2_vs_normal >= 0.014
wrong_history_closer_to_right_action == true when right action is available
```

The `closer_to_right_action` criterion is important. It checks that the wrong
history is not merely random perturbation; it moves the action toward the
different-fault source.

### Outcome Wrong-History Rows

Required:

```text
left normal replay succeeds
wrong_cross_fault_hidden collides or terminates
normal - wrong margin gap >= 0.01
```

### Mitigation Wrong-History Rows

Required:

```text
normal and wrong-history may both fail
normal margin exceeds wrong-history margin by >= 0.02
```

## Pass/Fail Gates

M828 should classify results with these outcome classes:

```text
v4_wrong_cross_fault_history_intervention_pass
v4_wrong_cross_fault_history_intervention_sparse
v4_wrong_cross_fault_history_intervention_zero_command_dominated
v4_wrong_cross_fault_history_intervention_history_insensitive
v4_wrong_cross_fault_history_intervention_reconstruction_failure
v4_wrong_cross_fault_history_intervention_contract_violation
```

Pass gate:

```text
primary_wrong_history_rows >= 80
unique_left_seed_count >= 8
unique_right_seed_count >= 8
unique_fault_family_pair_count >= 8
unique_warmup_pair_count >= 3
unique_onset_pair_count >= 4
max_left_seed_dominance <= 0.25
max_right_seed_dominance <= 0.25
max_fault_family_pair_dominance <= 0.30
actor_backbone_changed == false
residual_head_changed == false
ppo_used == false
promoted == false
```

Zero-command dominance guard:

```text
wrong_history accepted rows must be counted separately from zero_command rows
zero_command-only rows cannot satisfy the pass gate
report wrong_history_gap / zero_command_gap ratios when both are available
```

If wrong-history rows are sparse but matched pairs reconstruct correctly, M828
should not relax the gate. It should classify sparse and audit whether stricter
pair mining or broader source collection is needed.

## Required Implementation Artifacts

M828 should add:

```text
src/autodrift/v4_wrong_cross_fault_history_intervention.py
tests/test_v4_wrong_cross_fault_history_intervention.py
runs/m828_v4_wrong_cross_fault_history_intervention/summary.json
docs/m828-v4-wrong-cross-fault-history-intervention-implementation.md
```

Run artifacts:

```text
pair_source_rows.csv
reconstructed_snapshot_rows.csv
wrong_history_replay_rows.csv
accepted_wrong_history_rows.csv
accepted_mitigation_rows.csv
rejected_pair_rows.csv
diversity_summary.json
gate_summary.csv
fault_proxy_limitations.md
progress.jsonl
```

## Decision

Decision:

```text
wrong_cross_fault_history_intervention_design_admit_m828
```

M828 should implement the wrong-cross-fault intervention route. It must remain
no-training and no-promotion. PPO remains blocked until wrong-history evidence
passes source-diverse gates.
