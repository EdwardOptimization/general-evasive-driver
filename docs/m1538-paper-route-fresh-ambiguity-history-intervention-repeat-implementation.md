# M1538 Paper-Route Fresh Ambiguity History-Intervention Repeat Implementation

## Summary

M1538 implements the source-expanded repeat admitted by M1537 synthesis.

Decision:

```text
fresh_ambiguity_history_intervention_repeat_smoke_positive_source_expanded_route_to_audit
```

The repeat is a meaningful positive result: measured mining expanded accepted
pairs from `3` to `13`, accepted source-family edges from the M1534 small set to
`11`, wrong-history and donor-response-plus-hidden margin gaps both repeated
above threshold, and reset/zero-current controls no longer dominate the maximum
gap. The result is still not materializable because history-positive T5 or
terminal-boundary target sides remain `0`.

No candidate materialization, training corpus export, training, PPO, promotion,
private holdout, actor-input change, or level3 self-identification claim is
admitted.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_fresh_ambiguity_measured_mining.py tests/test_fresh_ambiguity_history_interventions.py -q
```

Result:

```text
11 passed
```

Measured repeat:

```text
PYTHONPATH=src python -m autodrift.fresh_ambiguity_measured_mining \
  --output-dir runs/m1538_fresh_ambiguity_measured_mining_repeat \
  --seed 1631 \
  --seed-count 2 \
  --max-pair-candidates 128
```

Intervention repeat:

```text
PYTHONPATH=src python -m autodrift.fresh_ambiguity_history_interventions \
  --output-dir runs/m1538_fresh_ambiguity_history_intervention_repeat \
  --pair-candidates runs/m1538_fresh_ambiguity_measured_mining_repeat/measured_pair_candidates.csv \
  --source-seed 1631 \
  --source-seed-count 2 \
  --continuation-steps 64
```

## Measured-Mining Repeat

Artifact:

```text
runs/m1538_fresh_ambiguity_measured_mining_repeat/summary.json
```

Key metrics:

```text
source_row_count: 28
attempted_source_families: 14
reached_reveal_source_families: 14
reached_decision_source_families: 14
trace_row_count: 2497
snapshot_row_count: 135
measured_pair_candidate_count: 18
accepted_measured_pair_count: 13
target_replay_failure_count: 1
donor_replay_failure_count: 0
max_single_source_family_share: 0.07142857142857142
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

Derived source-diversity metrics:

```text
accepted_source_family_edge_count: 11
accepted_source_family_max_share: 0.11538461538461539
t5_or_terminal_boundary_accepted_pair_count: 5
```

This passes the M1536 source-diversity gates:

```text
accepted_measured_pair_count >= 6
accepted_source_family_edge_count >= 5
max_accepted_source_family_share <= 0.50
t5_or_terminal_boundary_accepted_pair_count >= 1
```

## History-Intervention Repeat

Artifact:

```text
runs/m1538_fresh_ambiguity_history_intervention_repeat/summary.json
```

Key metrics:

```text
accepted_pair_count: 13
target_side_count: 26
variant_count: 10
intervention_row_count: 260
anchor_replay_success_count: 260
anchor_replay_failure_count: 0
wrong_history_row_count: 26
donor_response_action_row_count: 52
reset_zero_control_row_count: 104
max_wrong_history_margin_gap: 0.12242202469492369
max_donor_response_action_margin_gap: 0.12600996295198996
max_reset_zero_margin_gap: 0.09327067729080696
control_to_history_gap_ratio: 0.7401849433631154
success_drop_count: 12
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

Variant summary:

```text
wrong_history_donor_hidden_at_anchor:
  positive_target_sides: 4
  positive_pairs: 4
  positive_source_edges: 3
  positive_t5_or_boundary_target_sides: 0
  max_margin_gap_from_normal: 0.12242202469492369
  success_drop_count: 0

donor_response_action_plus_hidden_from_anchor:
  positive_target_sides: 4
  positive_pairs: 4
  positive_source_edges: 3
  positive_t5_or_boundary_target_sides: 0
  max_margin_gap_from_normal: 0.12600996295198996
  success_drop_count: 1

donor_response_action_stream_from_anchor:
  positive_target_sides: 0
  max_margin_gap_from_normal: 0.019388015986013585
  success_drop_count: 0

delayed_hidden_16_at_anchor:
  positive_target_sides: 2
  positive_source_edges: 2
  max_margin_gap_from_normal: 0.038692235106069006

reset/zero-current controls:
  max_margin_gap_from_normal: 0.09327067729080696
  positive_t5_or_boundary_target_sides: 1
```

## Interpretation

Supported by M1538:

```text
source-expanded public repeat is feasible;
M1534 wrong-history and donor-plus-hidden positives were not a single-pair artifact;
history-intervention positives now cover multiple pairs and source-family edges;
control interventions no longer dominate the maximum terminal-margin gap;
the repeat remains guardrail-clean.
```

Still unsupported:

```text
T5 or terminal-boundary history-positive evidence;
direct donor response/action stream sensitivity above threshold;
paper-level evidence;
candidate materialization;
training corpus export;
level3 anticipatory self-identification;
policy superiority.
```

The next step must be an audit. The audit should decide whether to:

```text
route to terminal-boundary pair repair / task generation;
route to a candidate-materialization design with T5 explicitly excluded;
or require another source expansion before any corpus export.
```

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
m1539-paper-route-fresh-ambiguity-history-intervention-repeat-result-audit
```
