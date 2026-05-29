# M1581 Paper-Route History Pairability Source-Generation Design

## Summary

M1581 starts the new branch:

```text
paper_route_history_pairability_source_generation
```

Decision:

```text
history_pairability_source_generation_design_admit_bounded_implementation
```

The branch changes the order of evidence:

```text
first prove pairability;
then run history interventions.
```

M1579 failed before interventions because no target-donor pair satisfied the
matched-current / hidden-divergent screen. M1582 should therefore mine and
characterize pairability directly. It should not run history interventions,
export a corpus, materialize candidates, train, run PPO, use private holdout, or
claim self-identification.

## Pairability Definition

A pairability candidate is two public P0 replays at anchor time with:

```text
same or similar current response/action frame;
source-diverse histories;
hidden-state separation;
same or nearby temporal window;
same deployable actor observation contract.
```

Pairability is not self-ID evidence. It is only the prerequisite for a later
wrong-history intervention to be meaningful.

## Source Scope

M1582 should mine across broad public P0 source families, not only high-speed
and late-reveal:

```text
t5_near_boundary_warmup
t5_boundary_axis_retarget
t5_high_speed_close_obstacle
late_reveal_boundary
curved_boundary_obstacle
grip_loss_proxy
brake_fade_or_loss_proxy
drive_loss_proxy
actuator_delay_step
capability_step_down
capability_step_up
```

These source-family labels are artifact metadata only. They must not enter actor
input.

Do not add four-wheel physical faults such as single-wheel blowout or half-shaft
breakage in this branch. Those require simulator-fidelity work.

## Anchor Windows

M1582 should screen pairability over windows where history can plausibly matter:

```text
reveal
reveal_plus_4
reveal_plus_8
decision_minus_32
decision_minus_24
decision_minus_16
decision_minus_8
decision
```

De-duplicate by:

```text
calibration_id@anchor_step
```

## Measurements

For each replay-ok anchor, capture:

```text
anchor_id
calibration_id
source_family
task_family
mode_name
anchor_window
anchor_step
normal_terminal_margin
normal_success
normal_collision
response_action_frame[0:12]
context_frame[12:72]
hidden_norm
hidden_checksum
hidden_vector for distance computation only
```

For each cross-source pair, compute:

```text
response_action_l2
context_l2
hidden_l2
anchor_step_distance
same_window
same_task_family
same_outcome
source_edge
```

Hidden vectors are for offline artifact diagnostics only. They must not enter
actor input or any deployable policy.

## Pairability Tiers

M1582 should report threshold sweeps instead of choosing one post-hoc threshold.

Pre-registered tiers:

```text
tier_a_strict:
  response_action_l2 <= 0.55
  hidden_l2 >= 3.0

tier_b_moderate:
  response_action_l2 <= 0.75
  hidden_l2 >= 2.0

tier_c_diagnostic:
  response_action_l2 <= 1.00
  hidden_l2 >= 2.5
```

Context guard:

```text
context_l2 <= 4.0
```

If context L2 is unavailable or too noisy, it must be reported separately and
not silently ignored.

## Public Gates For M1582

M1582 should pass public pairability smoke gates only if:

```text
source_spec_count >= 360
anchor_candidate_count >= 512
replay_ok_anchor_count >= 256
pair_screen_candidate_count >= 10000
tier_b_pair_count >= 64
tier_a_pair_count >= 8
pairable_source_edge_count >= 4
pairable_target_source_family_count >= 3
pairable_window_count >= 3
high_speed_or_late_pair_count >= 8
guardrail_violation_count == 0
history_interventions_executed == false
candidate_materialized == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
training_corpus_exported == false
```

Evidence-quality targets:

```text
tier_b_pair_count >= 160
tier_a_pair_count >= 24
pairable_source_edge_count >= 8
pairable_target_source_family_count >= 4
pairable_window_count >= 4
max_single_pairable_source_edge_share <= 0.35
high_speed_or_late_pair_count >= 24
```

If public gates pass, M1583 must audit before any history intervention design.

## Required Artifacts

M1582 should write:

```text
runs/m1582_history_pairability_source_miner_smoke/source_spec_rows.csv
runs/m1582_history_pairability_source_miner_smoke/anchor_candidate_rows.csv
runs/m1582_history_pairability_source_miner_smoke/pairability_pair_rows.csv
runs/m1582_history_pairability_source_miner_smoke/pairability_source_edge_summary.csv
runs/m1582_history_pairability_source_miner_smoke/pairability_source_family_summary.csv
runs/m1582_history_pairability_source_miner_smoke/pairability_window_summary.csv
runs/m1582_history_pairability_source_miner_smoke/threshold_sweep_summary.csv
runs/m1582_history_pairability_source_miner_smoke/guardrail_summary.csv
runs/m1582_history_pairability_source_miner_smoke/summary.json
```

Do not write:

```text
history_intervention_rows;
training corpus;
checkpoint;
promotion artifact;
private-holdout result.
```

## Null Classification

M1582 should classify failures as:

```text
pairability_absent:
  no tier_b pairs.

strict_pairability_absent:
  tier_b pairs exist but tier_a is zero.

source_singleton_pairability:
  pairs exist but one source edge dominates.

high_speed_late_pairability_absent:
  pairs exist elsewhere but not in high-speed/late targets.

context_mismatch_dominated:
  response/action match exists only when context is very different.

replay_or_contract_failure:
  replay, nonfinite state, or actor contract guardrails fail.

pairability_public_pass:
  public gates pass.
```

## Follow-Up Logic

If M1582 passes public pairability gates:

```text
M1583 audits whether to design a source-diverse wrong-history intervention over
the pairable set.
```

If M1582 fails because pairability is absent:

```text
M1583 audits whether the current P0 simulator/source family set can support the
paper-route self-ID evidence at all.
```

If M1582 passes only relaxed tiers:

```text
M1583 audits threshold sensitivity. Do not silently weaken pairability gates.
```

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
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
m1582-paper-route-history-pairability-source-miner-implementation
```
