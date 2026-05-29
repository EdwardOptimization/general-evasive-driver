# M1584 Paper-Route Source-Diverse Pairability History-Intervention Design

## Summary

M1584 designs the next bounded implementation after M1583.

Decision:

```text
source_diverse_pairability_history_intervention_design_admit_bounded_implementation
```

The design uses M1582 pairability rows as a public diagnostic input, but it does
not treat them as a training corpus and does not claim history necessity.

The next implementation should answer:

```text
when current response/action and context are similar but recurrent hidden states
come from source-diverse histories, does swapping or corrupting the history
state change closed-loop outcome more than current-frame controls?
```

## Inputs

Primary public input:

```text
runs/m1582_history_pairability_source_miner_smoke/pairability_pair_rows.csv
```

Required reconstruction inputs:

```text
runs/m1582_history_pairability_source_miner_smoke/source_spec_rows.csv
runs/m1582_history_pairability_source_miner_smoke/anchor_candidate_rows.csv
runs/m1582_history_pairability_source_miner_smoke/summary.json
```

The implementation may reconstruct specs by reusing the M1582 source generator
parameters:

```text
seed: 1901
seed_count: 6
max_source_specs: 480
max_anchor_candidates: 640
```

No actor input changes are admitted.

## Pair Selection

Eligible pairs:

```text
tier_a_strict == true
context_ok == true
response_action_l2 <= 0.55
hidden_l2 >= 3.0
```

Selection should be balanced, not purely rank-ordered:

```text
target_pair_count: 72
max_pairs_per_source_edge: 4
max_pairs_per_endpoint_family: 20
max_pairs_per_anchor_window: 20
preferred same_window: true
allow cross-window pairs only if needed for source-edge coverage
```

Minimum selection gates:

```text
selected_pair_count >= 64
selected_source_edge_count >= 8
selected_endpoint_source_family_count >= 6
selected_window_count >= 4
max_selected_source_edge_share <= 0.20
```

The selector should write:

```text
selected_pair_rows.csv
selected_pair_source_edge_summary.csv
selected_pair_source_family_summary.csv
selected_pair_window_summary.csv
```

Do not export selected rows as a training corpus.

## High-Speed Caveat

M1583 found:

```text
t5_high_speed_close_obstacle endpoint pairs in capped M1582 rows: 0
late_reveal_boundary endpoint pairs in capped M1582 rows: 108
```

Therefore:

```text
high_speed_endpoint_required: false
high_speed_endpoint_diagnostic_only: true
```

The implementation must report high-speed endpoint counts, but a zero count is
not a failure of M1585. It remains a source-generation caveat for later branch
synthesis or source repair.

## Directions

Each selected pair should be evaluated in both directions when possible:

```text
left as target, right as donor;
right as target, left as donor.
```

Each directed pair defines:

```text
target current observation/context;
target recurrent hidden state;
donor recurrent hidden state;
donor response/action frame;
target normal continuation baseline.
```

If an anchor cannot be replayed cleanly, record it and continue. Do not silently
drop failures from denominators.

## Intervention Variants

Pre-register these variants:

```text
normal
wrong_history_hidden
donor_response_action_plus_hidden
donor_response_action_only
reset_hidden
zero_current_response
zero_action_history
zero_all_response
```

Interpretation:

```text
wrong_history_hidden:
  replace target recurrent state with donor hidden while preserving target current frame/context.

donor_response_action_plus_hidden:
  inject both donor response/action frame and donor hidden.

donor_response_action_only:
  inject donor response/action frame without donor hidden; this is a current-frame substitution control.

reset_hidden:
  zero or reset recurrent state while preserving current target frame.

zero_current_response:
  zero the explicit current response/action stream while preserving context and hidden.

zero_action_history:
  zero previous-command/action-history channels only.

zero_all_response:
  zero explicit response/action channels and action-history channels.
```

The exact implementation can reuse the existing intervention machinery, but it
must keep these variants separate in artifacts.

## Metrics

For every directed pair and variant, report:

```text
terminal_margin
success
collision
road_departure
spin_or_instability if available
termination_reason
margin_gap_vs_normal
success_drop_vs_normal
collision_increase_vs_normal
target_source_family
donor_source_family
source_edge
anchor_window
response_action_l2
context_l2
hidden_l2
```

Primary history variants:

```text
wrong_history_hidden
donor_response_action_plus_hidden
```

Current-frame controls:

```text
donor_response_action_only
reset_hidden
zero_current_response
zero_action_history
zero_all_response
```

## Public Gates For M1585

M1585 should pass public smoke gates only if:

```text
selected_pair_count >= 64
selected_source_edge_count >= 8
selected_endpoint_source_family_count >= 6
selected_window_count >= 4
max_selected_source_edge_share <= 0.20
directed_pair_count >= 128
intervention_row_count >= 896
anchor_replay_failure_count <= 8
guardrail_violation_count == 0
history_interventions_executed == true
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
history_positive_directed_pair_count >= 8
history_positive_source_edge_count >= 3
history_positive_endpoint_source_family_count >= 4
history_success_drop_count >= 1 OR max_history_margin_gap >= 0.05
control_substitution_dominated_share <= 0.50
wrong_history_or_donor_plus_hidden_max_gap >= 0.02
max_history_gap >= 1.33 * max_current_frame_control_gap OR at least one success drop unique to history variant
```

High-speed endpoint positive count is diagnostic only:

```text
high_speed_endpoint_directed_pair_count: report
high_speed_history_positive_count: report
do not require nonzero for M1585 pass
```

## Null Classification

Use these result classes:

```text
selection_balance_failure:
  selected pairs cannot meet source-edge/window/family gates.

replay_failure:
  too many selected anchors fail replay.

history_null:
  history variants do not exceed the 0.02 margin-gap threshold and no success drop occurs.

control_dominated:
  current-frame controls match or exceed history-variant effects.

source_singleton_history:
  positives exist but concentrate in fewer than 3 source edges.

late_only_history:
  positives exist but only in late-reveal endpoint pairs.

high_speed_endpoint_absent:
  high-speed endpoint remains absent; diagnostic, not public gate failure.

public_pass_evidence_quality_fail:
  row/replay gates pass but history evidence targets fail.

public_and_evidence_pass:
  public smoke gates and evidence-quality targets pass.
```

## Required Artifacts For M1585

```text
runs/m1585_source_diverse_pairability_history_intervention_smoke/selected_pair_rows.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/selected_pair_source_edge_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/selected_pair_source_family_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/selected_pair_window_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/variant_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/source_edge_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/guardrail_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/summary.json
```

## Guardrails

```text
history_interventions_executed: false in M1584
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
m1585-paper-route-source-diverse-pairability-history-intervention-implementation
```
