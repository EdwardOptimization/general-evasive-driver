# M1552 Paper-Route Calibrated Pair-Expanded History-Intervention Design

## Summary

M1552 designs the bounded pair-expanded calibrated history-intervention smoke
admitted by M1551.

Decision:

```text
pair_expanded_history_intervention_design_admit_bounded_implementation
```

The design uses the `21` accepted M1550 pairs. It does not relax the self-ID
standard: pair expansion only says the source set is now broad enough to test
history interventions. It is not itself history evidence.

No implementation smoke, candidate materialization, training corpus export,
training, PPO, promotion, private holdout, actor-input change, or level3
self-identification claim is admitted by M1552.

## Inputs

Use:

```text
runs/m1550_calibrated_pair_expansion_planner_smoke/accepted_pair_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/source_spec_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/summary.json
docs/m1551-paper-route-calibrated-pair-expansion-planner-result-audit.md
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Reconstruct specs deterministically with:

```text
seed: 1843
seed_count: 3
max_base_rows: 24
max_calibration_specs: 240
```

The implementation must verify that every accepted pair id can be mapped back
to a reconstructed calibration spec before replay.

## Pair Set

M1550 accepted pair metrics:

```text
accepted_pair_count: 21
accepted_source_family_edge_count: 5
max_single_pair_source_edge_share: 0.38095238095238093
accepted_terminal_family_count: 4
accepted_window_bucket_count: 3
max_endpoint_share: 0.14285714285714285
```

M1553 should run all 21 pairs, both target sides:

```text
target_side_count: 42
variant_count: 10
planned_intervention_row_count: 420
```

If runtime forces a cap, the cap must be source-edge round-robin and must be
recorded. Do not silently take the first rows.

## Variants

Use the same core variants as M1547:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
donor_response_action_plus_hidden_from_anchor
```

Interpretation rules:

```text
wrong_history_donor_hidden_at_anchor and donor_response_action_plus_hidden_from_anchor
  are the main history-sensitive channels;
donor_response_action_stream_from_anchor tests whether current response/action
  stream substitution matters without only swapping hidden state;
reset/zero-current/zero-action are controls and cannot be counted as self-ID
  positives;
delayed hidden variants are temporal robustness diagnostics.
```

## Required Artifacts

M1553 should write:

```text
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/accepted_pair_rows.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/intervention_rows.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/pair_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/variant_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/source_edge_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/endpoint_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/window_bucket_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/guardrail_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/summary.json
```

Do not write a training corpus.

## Public Gates

Input gates:

```text
accepted_pair_count >= 16
accepted_source_family_edge_count >= 5
max_single_pair_source_edge_share <= 0.4
max_endpoint_share <= 0.2
accepted_window_bucket_count >= 3
```

Replay gates:

```text
expected_intervention_row_count >= 400
anchor_replay_failure_rate <= 0.05
nonfinite_action_count == 0
guardrail_violation_count == 0
```

History-positive gates:

```text
terminal_wrong_history_positive_target_sides
  + terminal_donor_plus_hidden_positive_target_sides >= 4
or
terminal_wrong_or_donor_success_drop_count >= 2
```

Control-dominance gates:

```text
terminal_control_to_history_gap_ratio <= 4.0
```

If history max gap is zero and controls are also zero, classify as null rather
than control dominated.

Concentration gates:

```text
positive_max_single_source_edge_share <= 0.5
positive_max_single_endpoint_share <= 0.25
```

The implementation may pass public smoke gates without passing evidence-quality
targets. It must still route to audit before any materialization.

## Expected Outcomes

Positive route:

```text
pair-expanded wrong-history or donor-plus-hidden variants create terminal margin
gaps or success drops;
controls do not dominate;
positives are not concentrated on one edge or endpoint.
```

Negative route:

```text
all history variants are null;
only reset/zero-current controls are positive;
anchor replay failures dominate;
positives concentrate on one edge or endpoint.
```

Either result must route to audit.

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
m1553-paper-route-pair-expanded-calibrated-history-intervention-implementation
```
