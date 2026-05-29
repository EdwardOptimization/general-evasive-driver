# M1550 Paper-Route Calibrated Pair-Expansion Planner Implementation

## Summary

M1550 implements the no-training calibrated pair-expansion planner designed by
M1549.

Decision:

```text
calibrated_pair_expansion_planner_pair_gate_pass_trace_snapshot_fail_route_to_audit
```

This is a partial positive result. The implementation repaired the M1547
pair-bottleneck substantially: accepted pairs increased from `2` to `21`, and
source-family edges increased from `1` to `5`. Pair gates passed. Trace gates
did not pass because measured snapshot count was only `13`, below the
pre-registered `24` threshold. No history interventions were run.

No candidate materialization, training corpus export, history intervention,
training, PPO, promotion, private holdout, actor-input change, or level3
self-identification claim is admitted.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_calibrated_pair_expansion_planner.py -q
```

Result:

```text
5 passed
```

Smoke:

```text
PYTHONPATH=src python -m autodrift.calibrated_pair_expansion_planner \
  --output-dir runs/m1550_calibrated_pair_expansion_planner_smoke \
  --accepted-calibrated-rows runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv \
  --seed 1843 \
  --seed-count 3 \
  --max-base-rows 24 \
  --max-calibration-specs 240 \
  --max-pair-candidates 256
```

## Implementation

New module:

```text
src/autodrift/calibrated_pair_expansion_planner.py
```

New tests:

```text
tests/test_calibrated_pair_expansion_planner.py
```

The planner:

```text
over-samples terminal source rows before applying the max-base-row cap;
builds calibrated task specs;
reruns measured traces and snapshots;
scores pair candidates with scene/current distance, action divergence, terminal
  margin gap, anchor-window distance, source-edge diversity, and window-bucket
  diversity;
selects accepted pairs with source-edge round-robin;
writes source specs, measured traces, snapshots, pair candidates, accepted
  pairs, family summaries, guardrails, and summary;
does not run history interventions.
```

## Smoke Artifacts

Primary artifact:

```text
runs/m1550_calibrated_pair_expansion_planner_smoke/summary.json
```

Additional artifacts:

```text
runs/m1550_calibrated_pair_expansion_planner_smoke/admitted_calibrated_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/source_spec_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/measured_trace_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/measured_snapshot_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/measured_trace_attempt_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/pair_candidate_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/accepted_pair_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/pair_family_summary.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/guardrail_summary.csv
```

## Key Metrics

Trace/source metrics:

```text
terminal_base_source_rows: 20
calibration_spec_count: 200
measured_trace_count: 200
measured_snapshot_count: 13
measured_trace_family_count: 5
rollout_failure_count: 95
failure_type_counts:
  did_not_reach_decision_step: 93
  none: 105
  reset_failure: 2
```

Pair metrics:

```text
pair_candidate_count: 21
accepted_pair_count: 21
accepted_source_family_edge_count: 5
max_single_pair_source_edge_share: 0.38095238095238093
accepted_terminal_family_count: 4
accepted_window_bucket_count: 3
```

Accepted source-family edges:

```text
curved_boundary_obstacle|t5_boundary_axis_retarget: 5
curved_boundary_obstacle|t5_high_speed_close_obstacle: 5
curved_boundary_obstacle|t5_near_boundary_warmup: 8
t5_boundary_axis_retarget|t5_high_speed_close_obstacle: 1
t5_boundary_axis_retarget|t5_near_boundary_warmup: 2
```

Gates:

```text
passes_trace_gates: false
passes_pair_gates: true
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
guardrail_violation_count: 0
history_interventions_executed: false
```

## Interpretation

Supported by M1550:

```text
M1547 pair bottleneck can be relaxed substantially;
pairability-first source expansion produced 21 accepted pairs;
source-family edge diversity reached 5 edges;
window-bucket diversity reached 3 buckets;
round-robin pair selection prevents a single edge from fully dominating;
all no-training/no-materialization guardrails remain clean.
```

Not supported by M1550:

```text
full public smoke gate pass;
enough measured snapshot coverage under the pre-registered trace gate;
history intervention effects;
candidate materialization;
training corpus export;
level3 self-identification.
```

The main blocker is now trace/snapshot coverage, not pair diversity. M1551 must
audit whether `measured_snapshot_count: 13` is a hard blocker before designing
pair-expanded interventions, or whether the pair-gate pass is sufficient to
admit a bounded intervention design with explicit caveats.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

The planner found enough pair-diverse accepted pairs, but it did not meet the
pre-registered measured snapshot count. This should be audited before any
intervention replay.

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
history_interventions_executed: false
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
m1551-paper-route-calibrated-pair-expansion-planner-result-audit
```
