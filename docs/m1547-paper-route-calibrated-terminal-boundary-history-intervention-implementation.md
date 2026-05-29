# M1547 Paper-Route Calibrated Terminal-Boundary History-Intervention Implementation

## Summary

M1547 implements the bounded calibrated terminal-boundary history-intervention
smoke designed by M1546.

Decision:

```text
calibrated_terminal_boundary_history_intervention_smoke_pair_narrow_null_route_to_synthesis
```

The implementation works mechanically: it reconstructs M1544 calibrated specs,
reruns measured traces with response/context snapshots, builds matched pairs,
and runs all intervention variants with clean replay. The result is not positive
history evidence. Pair construction is too narrow, and interventions produce no
terminal-margin or outcome difference.

No candidate materialization, training corpus export, training, PPO, promotion,
private holdout, actor-input change, or level3 self-identification claim is
admitted.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_calibrated_terminal_boundary_history_interventions.py -q
```

Result:

```text
4 passed
```

Smoke:

```text
PYTHONPATH=src python -m autodrift.calibrated_terminal_boundary_history_interventions \
  --output-dir runs/m1547_calibrated_terminal_boundary_history_intervention_smoke \
  --accepted-calibrated-rows runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv \
  --seed 1843 \
  --seed-count 2 \
  --max-base-rows 20 \
  --max-calibration-specs 160 \
  --max-pairs 12
```

## Implementation

New module:

```text
src/autodrift/calibrated_terminal_boundary_history_interventions.py
```

New tests:

```text
tests/test_calibrated_terminal_boundary_history_interventions.py
```

The module:

```text
rebuilds M1544 calibrated specs deterministically;
filters by accepted calibration_id;
reruns fixed-policy measured traces with response/context vectors;
builds matched scene/current-state pairs;
runs normal, reset, zero-current, delayed, wrong-history, donor-stream, and donor-plus-hidden variants;
writes measured trace, pair, intervention, summary, and guardrail artifacts.
```

## Smoke Artifacts

Primary artifact:

```text
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/summary.json
```

Additional artifacts:

```text
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/accepted_calibrated_source_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_trace_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_snapshot_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_trace_attempt_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/measured_pair_candidates.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/accepted_pair_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/intervention_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/pair_summary.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/variant_summary.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/guardrail_summary.csv
```

## Key Metrics

Measured trace metrics:

```text
accepted_calibrated_source_count: 8
measured_trace_count: 8
measured_snapshot_count: 10
measured_trace_family_count: 4
failure_type_counts: none=8
```

Pair metrics:

```text
accepted_pair_count: 2
accepted_source_family_edge_count: 1
max_single_pair_source_edge_share: 1.0
window_pair_kind_counts:
  decision|decision: 1
  post_decision|decision: 1
```

Intervention metrics:

```text
intervention_row_count: 40
variant_count: 10
anchor_replay_failure_count: 0
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_donor_stream_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
terminal_max_history_margin_gap: 0.0
terminal_max_control_margin_gap: 0.0
```

Gates:

```text
passes_measured_trace_gates: false
passes_pair_gates: false
passes_history_positive_gates: false
passes_control_gate: true
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

## Interpretation

Supported by M1547:

```text
calibrated spec reconstruction works;
accepted calibrated rows can be rerun into measured traces;
response/context measured snapshots are captured;
intervention replay is stable on the accepted pair subset;
guardrails remain clean.
```

Not supported by M1547:

```text
source-diverse calibrated pair construction;
history-positive terminal-boundary intervention effects;
donor-stream effects;
reset/zero-current outcome sensitivity;
candidate materialization;
training corpus export;
level3 self-identification.
```

The immediate blocker is pair diversity. The only accepted pairs are the same
edge:

```text
curved_boundary_obstacle -> t5_boundary_axis_retarget
```

Intervention effects are null on that narrow subset.

## Failure Classification

Primary failure types for the follow-up audit:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` applies because matched-pair coverage is below the
pre-registered threshold. `metric_artifact` applies because the null history
effect is only measured on two same-edge pairs and should not be interpreted as
a global falsification.

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
m1548-paper-route-fresh-ambiguity-source-mining-branch-synthesis
```
