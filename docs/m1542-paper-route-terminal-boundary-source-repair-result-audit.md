# M1542 Paper-Route Terminal-Boundary Source Repair Result Audit

## Summary

M1542 audits the M1541 terminal-boundary source repair smoke.

Decision:

```text
terminal_boundary_source_repair_audit_source_window_miss_route_to_task_sampling_calibration_design
```

M1541 is a clean implementation/plumbing result but not usable
terminal-boundary history-necessity evidence. It reached terminal target traces
and accepted terminal pairs, but the target traces did not enter the
pre-registered near-boundary margin window at the decision anchor. The
wrong-history and donor-plus-hidden interventions stayed near-null, while
reset/zero-current controls produced the dominant margin effect.

Therefore candidate materialization, training, PPO, promotion, private holdout,
actor-input changes, and level3 self-identification claims remain blocked.

## Audited Evidence

Artifacts:

```text
runs/m1541_terminal_boundary_source_repair_smoke/summary.json
docs/m1541-paper-route-terminal-boundary-history-positive-source-repair-implementation.md
```

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
anchor_replay_failure_count: 0
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_donor_stream_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
```

History/control metrics:

```text
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

## Verdicts

### Implementation Plumbing

Verdict:

```text
pass
```

M1541 added the terminal-boundary repair module, exercised the fixed public
actor, wrote the expected source/pair/intervention summaries, and kept all
no-training/no-materialization guardrails false. Replay was stable:

```text
anchor_replay_failure_count: 0 / 880
```

### Source Window

Verdict:

```text
scenario_sampling_failure
```

The source planner reached the required number of terminal target traces, but
none of them were in the intended decision-boundary window:

```text
terminal_target_trace_count: 20
terminal_target_near_boundary_count: 0
```

This means M1541 did not actually test the tight terminal-boundary active set
that M1540 wanted. The failure is primarily in task/source calibration, not in
the recurrent-policy evidence standard.

### History Sensitivity

Verdict:

```text
history_effect_null_on_terminal_boundary_sources
```

Evidence:

```text
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_donor_stream_positive_target_sides: 0
terminal_max_history_margin_gap: 0.0040251709543639436
```

This is far below the pre-registered `0.02` positive threshold. Because the
target rows missed the near-boundary window, this should not be interpreted as a
global falsification of history-dependent terminal-boundary behavior.

### Control Dominance

Verdict:

```text
metric_artifact
```

Evidence:

```text
terminal_max_control_margin_gap: 0.14847354874699903
terminal_control_to_history_gap_ratio: 36.88627152246277
```

The largest effect came from reset/zero-current controls, especially
zero-action-history. A naive margin-gap reading would therefore overstate the
self-identification evidence. The result is control-dominated and must not be
used for materialization.

### Materialization

Verdict:

```text
blocked
```

Reasons:

```text
near-boundary terminal target rows are absent;
terminal history-positive target sides are absent;
wrong/donor interventions do not produce success drops;
control interventions dominate the margin effect;
the result is public development evidence only.
```

## Root Cause

M1541 mostly wrapped the existing fresh-ambiguity source families and selected
terminal families from them. That was enough to create accepted pairs, but it
was not enough to calibrate actual simulator rollouts into the intended
near-boundary active set.

The next useful question is not:

```text
Can we train from M1541?
```

It is:

```text
Can we generate T5 terminal-boundary source rows whose fixed-policy decision or
post-decision margin is actually within the target window before running
history interventions?
```

## Next Route

Admit a task-sampling calibration design:

```text
m1543-paper-route-terminal-boundary-task-sampling-calibration-design
```

The design should target actual simulator margin, not metadata `normal_margin`.
It should tune obstacle distance, obstacle width, obstacle lateral offset, road
boundary geometry, reveal/decision timing, and speed/hidden capability pairs
until target-side rollouts enter a bounded margin window.

Minimum design requirements:

```text
calibrate before interventions;
separate decision-window and post-decision-window margins;
report terminal family and geometry coverage;
require no actor-input change;
keep labels and hidden params out of actor input;
do not materialize candidates or export a training corpus;
route to a calibration implementation before any history-intervention rerun.
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
m1543-paper-route-terminal-boundary-task-sampling-calibration-design
```
