# M1545 Paper-Route Terminal-Boundary Task-Sampling Calibration Result Audit

## Summary

M1545 audits the M1544 terminal-boundary task-sampling calibration smoke.

Decision:

```text
terminal_boundary_calibration_audit_pass_admit_calibrated_intervention_design
```

M1544 repairs the M1541 source-window blocker. It generated actual fixed-policy
near-boundary terminal rows with source-family diversity, decision-window hits,
post-decision-window hits, and clean guardrails. This is enough to admit a
calibrated terminal-boundary history-intervention design.

It is not enough to admit candidate materialization, training, PPO, promotion,
private holdout, actor-input changes, or level3 self-identification claims.

## Audited Evidence

Artifacts:

```text
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/summary.json
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv
docs/m1544-paper-route-terminal-boundary-task-sampling-calibration-implementation.md
```

Calibration metrics:

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

Accepted rows:

```text
accepted_calibrated_row_count: 8
accepted_terminal_family_count: 4
decision_window_hit_count: 4
post_decision_window_hit_count: 5
preferred_decision_window_hit_count: 0
terminal_window_hit_count: 5
max_single_terminal_family_share: 0.25
```

Accepted source-family counts:

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

## Verdicts

### Source Window

Verdict:

```text
pass
```

M1544 corrected the M1541 source-window miss:

```text
M1541 terminal_target_near_boundary_count: 0
M1544 accepted_calibrated_row_count: 8
```

The accepted set includes both decision-window and post-decision-window hits.

### Source Diversity

Verdict:

```text
bounded_public_pass
```

The accepted rows cover four terminal families with max family share `0.25`.
This is sufficient for a bounded calibrated intervention design.

Caveat:

```text
late_reveal_boundary accepted rows: 0
accepted_calibrated_row_count equals the minimum threshold
```

The next step should keep family-level accounting and should not treat the
accepted set as final paper evidence.

### Near-Boundary Quality

Verdict:

```text
pass_with_caveats
```

The result contains the required decision/post-decision hits:

```text
decision_window_hit_count: 4
post_decision_window_hit_count: 5
```

Caveats:

```text
preferred_decision_window_hit_count: 0
some accepted rows are post-decision-only;
some accepted rows terminate in collision after entering the window.
```

These rows are suitable for a calibrated intervention probe because the question
is whether history interventions change terminal-boundary outcome/margin. They
are not suitable for direct candidate materialization.

### Data Sufficiency For Interventions

Verdict:

```text
admit_design_only
```

M1544's source snapshots are enough to audit calibration, but not enough to
build high-quality matched-pair interventions because the saved bounded-runner
snapshots do not include full response/context vectors. The next design must
therefore reconstruct calibrated hook specs, rerun measured traces that capture
response/context snapshots, build matched current-state/scene pairs, and then
run interventions.

### Materialization

Verdict:

```text
blocked
```

Reasons:

```text
history interventions have not been run on calibrated rows;
matched current-state/scene pairs have not been built;
accepted set is small and public;
preferred decision-window hits are zero;
some rows are collision/terminal-boundary cases;
no audit has defined a training-corpus export rule.
```

## Next Route

Admit a calibrated terminal-boundary history-intervention design:

```text
m1546-paper-route-calibrated-terminal-boundary-history-intervention-design
```

The design should require:

```text
reconstruct M1544 calibrated hook specs from deterministic grid;
rerun calibrated measured traces with response/context vectors;
build matched scene/current-state pairs from accepted calibrated rows;
run wrong-history, donor-plus-hidden, donor-stream, delayed, reset, and zero-current controls;
report terminal-history-positive target sides separately from controls;
route to audit before any materialization or training.
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
m1546-paper-route-calibrated-terminal-boundary-history-intervention-design
```
