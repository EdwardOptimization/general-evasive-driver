# M1628 Paper-Route Contour-Aware Policy Target Materialization Branch Synthesis

## Summary

M1628 synthesizes the M1619-M1627 policy-target materialization sequence before
another materialization design or implementation.

Synthesis decision:

```text
continue
```

Route decision:

```text
admit full target materialization design
```

This is process-only. It does not materialize the full target corpus, construct
a loss or objective config, update an actor, train, run PPO, promote a
checkpoint, use private holdout, change actor inputs, or claim level3
self-identification.

## Evidence Summary

M1619 made the M1615 package executable as a no-update exact evaluator:

```text
positive_candidate_count: 39
diagnostic_guardrail_count: 232
positive_rows_all_clean: true
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0.0
all_objective_metrics_finite: true
checkpoint_weights_mutated: false
passes_public_smoke_gates: true
candidate_objective_residual_mean: 0.6822030978276948
history_control_separation_margin_mean: 0.022017600571959638
hidden_specific_gap_mean: 0.021311087773094452
```

M1620 found the evaluator useful but insufficient for actor updates, because it
only had row metrics and metadata rather than policy-side tensors. It pivoted to
policy-target materialization.

M1621-M1622 specified and audited the target materialization contract:

```text
trace M1615 rows to source/replay artifacts;
materialize observation, correct/wrong hidden, and action tensors;
keep diagnostics as zero-weight guardrails;
block loss/objective construction and training until after materialization
audit.
```

M1623 proved full-package source/variant traceability:

```text
positive_candidate_count: 39
diagnostic_guardrail_count: 232
source_run_resolution_failure_count: 0
positive_replay_pair_match_count: 39
diagnostic_replay_pair_match_count: 232
positive normal/wrong-history/donor-plus-hidden matches: 39/39/39
diagnostic normal/wrong-history/donor-plus-hidden matches: 232/232/232
missing_traceability_row_count: 0
passes_public_smoke_gates: true
```

M1624-M1625 correctly limited the next step to a source-diverse tensor-capture
dry run rather than full materialization.

M1626 implemented that dry run and passed:

```text
dry_run_row_count: 4
positive_capture_count: 2
diagnostic_capture_count: 2
observation_shape: [4, 72]
correct_hidden_shape: [4, 128]
wrong_hidden_shape: [4, 128]
preferred_action_shape: [4, 3]
wrong_history_action_shape: [4, 3]
donor_plus_hidden_action_shape: [4, 3]
all_tensor_values_finite: true
source action reproduction L2 max: 0.0
missing_capture_row_count: 0
diagnostic_rows_used_as_positive: false
checkpoint_weights_mutated: false
guardrail_violation_count: 0
```

M1627 audited M1626 as a clean dry-run pass and routed here for branch
synthesis before full materialization.

## Supported Claims

The branch now supports:

```text
the 39-positive / 232-diagnostic public package has role integrity;
the package is traceable to replay pairs and required intervention variants;
the actor contract remains canonical P0 human-view 72-dim online-GRU;
the replay path can recover observation and hidden tensors at least on the
source-diverse dry-run subset;
deterministic captured actions exactly reproduce M1609 source action metadata
on that subset;
diagnostic guardrails can remain zero-weight and non-positive through capture.
```

## Falsified Or Rejected Claims

The branch rejects:

```text
row-metric residuals alone are enough for actor objective updates;
the package is training-ready without policy-side tensors;
diagnostic guardrails can be promoted to positive targets;
the dry-run subset proves full-package materialization is already complete;
any current artifact supports objective update, PPO, promotion, private holdout,
paper-level validation, or level3 anticipatory self-identification.
```

No new scientific failure is introduced in M1628. Failure taxonomy remains:

```text
none
```

## Failure Taxonomy Summary

Recent branch failure handling:

```text
M1620: not a failure; identified metadata-only evaluator limitation and pivoted.
M1623: traceability pass; no missing rows.
M1626: tensor-capture dry-run pass; no missing rows or guardrail violations.
M1627: process audit pass; routes to synthesis.
```

The dominant residual risk is not a current failure type like
`proof_washout` or `training_instability`; it is scope risk:

```text
public package is narrow;
dry-run tensor capture is not yet full-package tensor capture;
future optimizer objectives could overfit public proof rows if admitted too
early.
```

## Public-Gate Overfit Risk

Risk remains high but manageable:

```text
the package has only 39 positive candidates;
the 39 positives come from public contour filters and two source-run aliases;
diagnostics are public controls, not private holdout;
full-package materialization will still be public proof plumbing, not a
promotion or paper-level generalization result;
future objective construction must not turn this into a gate-passing optimizer.
```

Mitigation:

```text
next step is design-only full target materialization;
the design must keep training_ready=false;
diagnostics must stay role_weight=0.0 and used_as_positive=false;
full materialization implementation must route to audit before any loss or
objective config;
objective construction and PPO remain blocked until a later synthesis/audit.
```

## Next Branch Decision

Decision:

```text
continue
```

Next task:

```text
m1629-paper-route-contour-aware-full-target-materialization-design
```

M1629 should design a full 39-positive / 232-diagnostic tensor materialization
implementation using the M1626 capture path. It should not implement the full
materialization yet, and it must keep blocked:

```text
loss/objective construction;
actor update;
training;
PPO;
promotion;
private holdout;
actor input changes;
level3 self-ID claims.
```
