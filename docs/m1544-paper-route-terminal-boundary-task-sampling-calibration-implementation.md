# M1544 Paper-Route Terminal-Boundary Task-Sampling Calibration Implementation

## Summary

M1544 implements the bounded task-sampling calibration route designed by M1543
and runs the public smoke.

Decision:

```text
terminal_boundary_task_sampling_calibration_smoke_pass_route_to_audit
```

This is a positive calibration result. Unlike M1541, the task sampling now
produces actual fixed-policy terminal target rows in decision/post-decision
near-boundary windows. It does not run history interventions and does not
materialize candidates or training data.

No candidate materialization, training corpus export, training, intervention
replay, PPO, promotion, private holdout, actor-input change, or level3
self-identification claim is admitted.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_terminal_boundary_task_sampling_calibration.py -q
```

Result:

```text
4 passed
```

Smoke:

```text
PYTHONPATH=src python -m autodrift.terminal_boundary_task_sampling_calibration \
  --output-dir runs/m1544_terminal_boundary_task_sampling_calibration_smoke \
  --seed 1843 \
  --seed-count 2 \
  --max-base-rows 20 \
  --max-calibration-specs 160
```

## Implementation

New module:

```text
src/autodrift/terminal_boundary_task_sampling_calibration.py
```

New tests:

```text
tests/test_terminal_boundary_task_sampling_calibration.py
```

The implementation starts from terminal target source rows, builds retargeted
P0-compatible env hook specs, runs the fixed public actor, measures actual
decision/post-decision/terminal margins, and writes calibrated audit artifacts.

It changes simulator task sampling only. Actor observations and the deployed
policy contract are unchanged.

## Smoke Artifacts

Primary artifact:

```text
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/summary.json
```

Additional artifacts:

```text
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/source_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/calibration_specs.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/trace_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/snapshot_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/family_summary.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/guardrail_summary.csv
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/source_attempt_rows.csv
```

## Key Metrics

Calibration source metrics:

```text
terminal_base_source_rows: 10
terminal_family_count: 5
calibration_spec_count: 100
terminal_target_trace_count: 57
trace_row_count: 5060
snapshot_row_count: 305
finite_margin_row_count: 305
rollout_failure_count: 43
```

Accepted calibrated rows:

```text
accepted_calibrated_row_count: 8
accepted_terminal_family_count: 4
decision_window_hit_count: 4
post_decision_window_hit_count: 5
preferred_decision_window_hit_count: 0
terminal_window_hit_count: 5
max_single_terminal_family_share: 0.25
```

Accepted family counts:

```text
curved_boundary_obstacle: 2
t5_boundary_axis_retarget: 2
t5_high_speed_close_obstacle: 2
t5_near_boundary_warmup: 2
```

Gates:

```text
passes_calibration_source_gates: true
passes_near_boundary_gates: true
passes_quality_gates: true
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

## Interpretation

Supported by M1544:

```text
actual fixed-policy near-boundary terminal rows can be generated;
near-boundary rows are not single-family dominated;
decision-window and post-decision-window hits are both present;
the calibration harness preserves the P0 actor-input contract;
all no-training/no-materialization guardrails remain false.
```

Still unsupported:

```text
history necessity on calibrated terminal rows;
wrong-history or donor-plus-hidden outcome sensitivity;
candidate materialization;
training corpus export;
level3 anticipatory self-identification;
policy improvement or deployment claims.
```

M1544 repairs the source-window blocker from M1541. The next step must still be
an audit before using these calibrated rows in a history-intervention design.

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
m1545-paper-route-terminal-boundary-task-sampling-calibration-result-audit
```
