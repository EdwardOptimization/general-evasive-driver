# M1540 Paper-Route Terminal-Boundary History-Positive Source Repair Design

## Summary

M1540 designs the terminal-boundary source repair route admitted by M1539.

Decision:

```text
terminal_boundary_history_positive_source_repair_design_admit_bounded_planner
```

M1538 proved that fresh ambiguity history interventions can produce
source-expanded wrong-history and donor-plus-hidden terminal-margin gaps. It did
not prove the paper-relevant terminal-boundary case: T5/terminal-boundary
accepted pairs existed, but history-positive target sides stayed at `0`.

M1540 therefore designs a bounded public repair planner for T5/terminal-boundary
sources. It does not run the planner, train, materialize candidates, export a
training corpus, use private holdout, promote, alter actor inputs, or claim
level3 self-identification.

## Problem Statement

Current evidence:

```text
accepted_measured_pair_count: 13
accepted_source_family_edge_count: 11
t5_or_terminal_boundary_accepted_pair_count: 5
wrong_history_positive_target_sides: 4
donor_plus_hidden_positive_target_sides: 4
t5_or_terminal_boundary_history_positive_target_sides: 0
donor_response_action_stream_positive_target_sides: 0
```

The missing evidence link is:

```text
terminal-boundary accepted pair
  -> wrong-history or donor-plus-hidden terminal-margin gap >= 0.02
  -> preferably success drop or collision/clearance outcome change
```

M1540 targets that link directly.

## Repair Sources

The implementation should focus on terminal-boundary families:

```text
t5_near_boundary_warmup
t5_high_speed_close_obstacle
t5_boundary_axis_retarget
late_reveal_boundary
curved_boundary_obstacle
```

Support families may be paired against them only if the target side remains
terminal-boundary:

```text
brake_fade_or_loss_proxy
grip_loss_proxy
actuator_delay_step
capability_step_down
capability_step_up
```

The result must report target-side and donor-side families separately. A
terminal-boundary claim requires the target rollout to be terminal-boundary, not
only the donor.

## Repair Knobs

The repair planner should generate a bounded grid of public source variants.

### Margin Compression

Make normal terminal margins closer to the decision boundary:

```text
increase initial speed or obstacle urgency;
shift obstacle distance closer;
increase obstacle half width within existing task semantics;
reduce available road/free-space width for boundary-axis variants;
lower mu / brake_scale / tire_stiffness only as diagnostic source metadata;
keep actor observation unchanged.
```

Target normal terminal-margin window:

```text
near_boundary_margin_min: -0.03
near_boundary_margin_max: 0.12
preferred_margin_abs_max: 0.06
```

### Reveal / Anchor Timing

M1538 used the decision anchor. Repair should sweep earlier anchors:

```text
decision
decision_minus_8
decision_minus_16
reveal_plus_4
```

This tests whether terminal-boundary history sensitivity exists before the
decision step becomes too late.

### Capability Contrast

For the same or near-same terminal-boundary scene, pair hidden dynamics that
should change the safe maneuver:

```text
low vs higher brake authority;
fast vs slow actuator response;
low lateral authority vs recoverable lateral authority;
capability step-down vs capability step-up near the same boundary geometry.
```

The pair acceptance should still require matched current scene and current ego
state. Hidden parameters remain logging/filtering metadata only.

### Boundary Geometry Retarget

Retarget geometry toward cases where yaw/brake choice matters:

```text
boundary_left / boundary_right / boundary_curve;
late_boundary_left / late_boundary_right / late_boundary_curve;
curved_obstacle_left / curved_obstacle_right / curved_obstacle_s.
```

The repair planner should avoid reusing only the exact public rows that already
failed. It should vary seed, reveal step, and geometry key.

## Implementation Shape

M1541 should implement a bounded planner module:

```text
src/autodrift/terminal_boundary_source_repair.py
tests/test_terminal_boundary_source_repair.py
```

The planner should:

```text
1. Build terminal-boundary repair source specs from existing P0-compatible hook
   families.
2. Run fixed-policy traces with the M1362 alpha 0.1 checkpoint.
3. Filter target-side terminal-boundary snapshots near the margin window.
4. Build matched scene/current-state pairs with hidden capability contrast.
5. Run the same ten M1538 intervention variants at selected anchors.
6. Write source, pair, intervention, variant, and guardrail summaries.
7. Route to audit before any candidate materialization.
```

Reuse existing measured-mining and intervention helpers where possible. Add a
new wrapper only where terminal-boundary repair needs explicit source selection,
anchor sweep, or target-side T5 accounting.

## Bounded Scope

Use public development seeds only:

```text
source_seed: 1731
source_seed_count: 3
max_repair_source_specs: 72
max_pair_candidates: 128
max_intervention_pairs: 24
continuation_steps: 64
device: cpu
checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

No GPU training or PPO is admitted.

## Pass / Fail Gates

Source and replay gates:

```text
terminal_source_spec_count >= 30
terminal_target_trace_count >= 20
terminal_target_near_boundary_count >= 8
accepted_terminal_pair_count >= 4
accepted_terminal_source_edge_count >= 3
anchor_replay_failure_rate <= 0.05
guardrail_violation_count == 0
```

History-positive gates:

```text
terminal_wrong_history_positive_target_sides >= 2
or
terminal_donor_plus_hidden_positive_target_sides >= 2
or
terminal_wrong_or_donor_success_drop_count >= 1
```

Positive threshold:

```text
terminal_margin_gap_from_normal >= 0.02
```

Control check:

```text
terminal_control_to_history_gap_ratio <= 4.0
```

If accepted terminal pairs exist but history-positive rows remain zero, classify
as:

```text
history_effect_null
```

If terminal pairs cannot be accepted, classify as:

```text
scenario_sampling_failure
```

If only reset/zero-current controls fire, classify as:

```text
metric_artifact
```

## Required Artifacts

M1541 should write:

```text
runs/m1541_terminal_boundary_source_repair_smoke/summary.json
runs/m1541_terminal_boundary_source_repair_smoke/terminal_source_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_pair_candidates.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_intervention_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_pair_summary.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_variant_summary.csv
runs/m1541_terminal_boundary_source_repair_smoke/guardrail_summary.csv
```

The summary must report:

```text
terminal_source_spec_count
terminal_target_trace_count
terminal_target_near_boundary_count
accepted_terminal_pair_count
accepted_terminal_source_edge_count
terminal_wrong_history_positive_target_sides
terminal_donor_plus_hidden_positive_target_sides
terminal_donor_stream_positive_target_sides
terminal_wrong_or_donor_success_drop_count
terminal_control_to_history_gap_ratio
candidate_materialized
training_started
ppo_used
private_holdout_used
actor_input_contract_changed
training_corpus_exported
level3_self_id_claim_made
```

## Materialization Rule

M1541 cannot materialize candidates. Any positive or negative result must route
to:

```text
m1542-paper-route-terminal-boundary-history-positive-source-repair-result-audit
```

Materialization remains blocked until an audit explicitly decides whether a
training corpus design is justified.

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1541-paper-route-terminal-boundary-history-positive-source-repair-implementation
```
