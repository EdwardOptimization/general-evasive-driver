# M1553 Paper-Route Pair-Expanded Calibrated History-Intervention Implementation

## Summary

M1553 implements and runs the bounded pair-expanded calibrated history
intervention smoke designed by M1552.

Decision:

```text
pair_expanded_intervention_smoke_public_pass_history_null_route_to_audit
```

This is a clean negative mechanism result. The implementation reconstructed all
M1550 accepted pairs and specs, ran all `420` planned intervention rows, and
passed public smoke gates with zero anchor replay failures. However, history
effects were essentially null: the largest history margin gap was only
`0.00025038157254009263`, and there were zero wrong-history/donor-positive
target sides and zero success drops.

No candidate materialization, training corpus export, training, PPO, promotion,
private holdout, actor-input change, or level3 self-identification claim is
admitted.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_pair_expanded_calibrated_history_interventions.py -q
```

Result:

```text
4 passed
```

Smoke:

```text
PYTHONPATH=src python -m autodrift.pair_expanded_calibrated_history_interventions \
  --output-dir runs/m1553_pair_expanded_calibrated_history_intervention_smoke \
  --accepted-pair-rows runs/m1550_calibrated_pair_expansion_planner_smoke/accepted_pair_rows.csv \
  --seed 1843 \
  --seed-count 3 \
  --max-base-rows 24 \
  --max-calibration-specs 240 \
  --max-pairs 21
```

## Implementation

New module:

```text
src/autodrift/pair_expanded_calibrated_history_interventions.py
```

New tests:

```text
tests/test_pair_expanded_calibrated_history_interventions.py
```

The module:

```text
loads M1550 accepted pairs;
reconstructs M1550 calibration specs deterministically;
reuses the calibrated anchor replay/intervention runner;
runs the same ten variants as M1547 on both target sides;
writes intervention, pair, variant, source-edge, endpoint, window-bucket,
  guardrail, and summary artifacts;
does not export a training corpus.
```

## Smoke Artifacts

Primary artifact:

```text
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/summary.json
```

Additional artifacts:

```text
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/accepted_pair_rows.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/missing_spec_rows.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/intervention_rows.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/pair_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/variant_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/source_edge_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/endpoint_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/window_bucket_summary.csv
runs/m1553_pair_expanded_calibrated_history_intervention_smoke/guardrail_summary.csv
```

## Key Metrics

Input and replay:

```text
accepted_pair_count: 21
accepted_source_family_edge_count: 5
max_single_pair_source_edge_share: 0.38095238095238093
max_endpoint_share: 0.14285714285714285
accepted_window_bucket_count: 3
target_side_count: 42
variant_count: 10
expected_intervention_row_count: 420
intervention_row_count: 420
anchor_replay_failure_count: 0
anchor_replay_failure_rate: 0.0
nonfinite_action_count: 0
missing_spec_count: 0
```

History/control:

```text
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_donor_stream_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
terminal_max_history_margin_gap: 0.00025038157254009263
terminal_max_control_margin_gap: 0.00003099723002852883
terminal_control_to_history_gap_ratio: 0.12379996544500241
positive_history_count: 0
positive_control_count: 0
```

Gates:

```text
passes_spec_reconstruction_gate: true
passes_input_pair_gates: true
passes_replay_gates: true
passes_history_positive_gates: false
passes_control_gate: true
passes_concentration_gates: false
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

## Variant Summary

Largest margin gaps:

```text
wrong_history_donor_hidden_at_anchor: 0.000241753384175869
donor_response_action_plus_hidden_from_anchor: 0.00025038157254009263
donor_response_action_stream_from_anchor: 0.00006257579068158492
zero_current_response_from_anchor: 0.00003099723002852883
```

All variants had zero success drops.

## Interpretation

Supported by M1553:

```text
pair-expanded calibrated intervention replay is mechanically reliable;
the M1550 pair set reconstructs and replays cleanly;
public smoke gates pass with zero anchor replay failures;
endpoint/source-edge/window diagnostics are available for audit.
```

Not supported by M1553:

```text
history necessity;
terminal-boundary wrong-history success drops;
donor-response/action stream sensitivity;
candidate materialization;
training corpus export;
level3 self-identification.
```

This result strongly suggests that the current pair-expanded terminal-boundary
rows are not causally sensitive to the tested history interventions at the
chosen anchors. The next step must be an audit, not another immediate repair.

## Failure Classification

Primary failure type:

```text
metric_artifact
```

The source/pair/replay metrics look healthy, but the metric that matters for
history necessity is null. Public smoke pass must not be mistaken for self-ID
evidence.

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
m1554-paper-route-pair-expanded-intervention-result-audit
```
