# M1541 Paper-Route Terminal-Boundary History-Positive Source Repair Implementation

## Summary

M1541 implements the bounded terminal-boundary source repair planner designed by
M1540 and runs the public smoke.

Decision:

```text
terminal_boundary_source_repair_smoke_complete_null_control_dominated_route_to_audit
```

The implementation is useful, but the result is not a positive
terminal-boundary history-necessity result. The smoke produced accepted
terminal pairs and clean intervention replay, but the terminal target rows did
not land in the intended near-boundary decision window, wrong-history and
donor-plus-hidden gaps stayed far below the `0.02` threshold, and reset/zero
controls dominated the maximum margin effect.

No candidate materialization, training corpus export, training, replay/PPO,
promotion, private holdout, actor-input change, or level3 self-identification
claim is admitted.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_fresh_ambiguity_measured_mining.py tests/test_fresh_ambiguity_history_interventions.py tests/test_terminal_boundary_source_repair.py -q
```

Result:

```text
17 passed
```

Smoke:

```text
PYTHONPATH=src python -m autodrift.terminal_boundary_source_repair \
  --output-dir runs/m1541_terminal_boundary_source_repair_smoke \
  --seed 1731 \
  --seed-count 3 \
  --max-repair-source-specs 72 \
  --max-pair-candidates 128 \
  --max-intervention-pairs 24
```

## Implementation

New module:

```text
src/autodrift/terminal_boundary_source_repair.py
```

New tests:

```text
tests/test_terminal_boundary_source_repair.py
```

The implementation reuses the M1531 measured-mining trace builder and the M1534
history-intervention variants, then adds terminal-boundary source selection,
target-side accounting, a four-anchor sweep, and terminal-specific summary
gates.

It also extends the shared history-intervention helper with:

```text
decision_minus_16 anchor support;
robust finalize_rows handling for replay rows with missing action fields.
```

These changes preserve the P0 actor-input contract and do not alter the
deployed policy.

## Smoke Artifacts

Primary artifact:

```text
runs/m1541_terminal_boundary_source_repair_smoke/summary.json
```

Additional artifacts:

```text
runs/m1541_terminal_boundary_source_repair_smoke/terminal_source_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_trace_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_snapshot_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_source_attempt_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_pair_candidates.csv
runs/m1541_terminal_boundary_source_repair_smoke/accepted_terminal_pair_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_intervention_rows.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_pair_summary.csv
runs/m1541_terminal_boundary_source_repair_smoke/terminal_variant_summary.csv
runs/m1541_terminal_boundary_source_repair_smoke/guardrail_summary.csv
```

## Key Metrics

Source and pair metrics:

```text
terminal_source_spec_count: 35
terminal_target_source_spec_count: 20
terminal_target_trace_count: 20
terminal_target_near_boundary_count: 0
accepted_terminal_pair_count: 11
accepted_terminal_source_edge_count: 8
```

Intervention metrics:

```text
intervention_row_count: 880
target_side_count: 88
variant_count: 10
anchor_count: 4
anchor_replay_failure_count: 0
```

History and control metrics:

```text
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_donor_stream_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
terminal_max_history_margin_gap: 0.0040251709543639436
terminal_max_control_margin_gap: 0.14847354874699903
terminal_control_to_history_gap_ratio: 36.88627152246277
```

Gates:

```text
passes_terminal_source_gates: false
passes_terminal_history_gates: false
passes_control_gate: false
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

## Interpretation

Supported by M1541:

```text
terminal-boundary source repair plumbing is implemented;
source generation reaches 20 terminal target traces;
accepted terminal pairs are available;
intervention replay is stable across 880 rows;
all no-training/no-materialization guardrails remain false.
```

Not supported by M1541:

```text
terminal target rows near the pre-registered decision-boundary margin window;
terminal-boundary wrong-history positive target sides;
terminal-boundary donor-plus-hidden positive target sides;
terminal-boundary donor stream positive target sides;
success drops from wrong-history or donor-plus-hidden interventions;
control-separated terminal-boundary history necessity;
candidate materialization;
training corpus export;
level3 anticipatory self-identification.
```

The most important negative result is:

```text
terminal_target_near_boundary_count: 0
```

The target traces are too far from the intended decision boundary at the
decision anchor, so the terminal-boundary history intervention is not testing
the tight failure surface M1540 wanted. The largest effect also comes from
`zero_action_history_from_anchor`, not wrong-history or donor-plus-hidden
channels, so the result is control-dominated.

## Failure Classification

Primary failure types for the follow-up audit:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` applies because terminal target traces did not
enter the near-boundary decision window. `metric_artifact` applies because
reset/zero controls are much larger than history interventions, so a naive
margin-gap reading would overstate self-ID evidence.

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
m1542-paper-route-terminal-boundary-source-repair-result-audit
```

M1542 must decide whether to:

```text
repair the terminal-boundary task sampling itself;
retarget the decision anchor/window definition;
pivot back to non-terminal source-expanded positives only as diagnostic
evidence;
or synthesize/stop this branch before another narrow implementation.
```
