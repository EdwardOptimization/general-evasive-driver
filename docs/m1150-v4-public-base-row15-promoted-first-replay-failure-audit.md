# M1150 V4 Public Base Row15 Promoted First Replay Failure Audit

## Purpose

M1150 audits the M1149 first-replay failure before any further update or replay
escalation.

Inputs inspected:

```text
runs/m1149_row15_promoted_actor_update_first_replay/summary.json
runs/m1149_row15_promoted_actor_update_first_replay/first_replay_summary.csv
runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv
runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.csv
runs/m1144_row15_promoted_objective_corpus/selected_boundary_rows.csv
runs/m1147_row15_promoted_actor_update_exact_eval/summary.json
runs/m1147_row15_promoted_actor_update_parameter_audit/summary.json
```

M1150 does not train actor weights, run PPO, run replay, mine new rows, promote
a checkpoint, use private holdout, or change actor inputs.

## M1149 Failure Recap

M1149 rejects `m1147_114602`:

```text
surface_count: 10
passed_surface_count: 8
failed_surface_count: 2
lost_success_drop_events: 76
normal_lost_events: 0
wrong_history_safe_events: 76
```

Failed surfaces:

```text
m267_m264:
  lost success-drop events: 1

row15_promoted_materialized:
  lost success-drop events: 75
```

The failure is proof washout through wrong-history rollouts becoming safe. It
is not normal-history collapse.

## Objective Coverage

The first question was whether the M1149 materialized failures were simply
absent from the M1144 objective corpus.

Result:

```text
materialized_lost_rows: 75
materialized_lost_unique_boundary_geometries: 49
lost_rows_boundary_geometry_selected_in_m1144_count: 75
lost_rows_boundary_geometry_selected_in_m1144_fraction: 1.0
lost_unique_geometries_selected_in_m1144_count: 49
lost_unique_geometries_selected_in_m1144_fraction: 1.0
```

All `75` row15-promoted materialized failures map to boundary geometries that
were selected into M1144. Therefore this is not a coverage-miss explanation for
the materialized surface.

The old-public `m267_m264` failure is different:

```text
m267_failure_present_in_m1144_objective: false
```

That one row remains an old-public retention requirement outside the M1144
promoted materialized corpus.

## Failure Concentration

The row15-promoted materialized failures all come from the braking target:

```text
future_braking_deceleration: 75
future_yaw_response: 0
```

They span:

```text
failed rows: 75
unique boundary geometries: 49
physical pairs: 9
source labels: 5
```

Source distribution:

```text
short61051: 23
short61050: 22
short61049: 21
row15_current: 5
previous_m1078_base: 4
```

Top physical-pair groups:

```text
113201:18:113230:45  lost rows: 12
113201:24:113230:51  lost rows: 12
113201:21:113230:48  lost rows: 12
113201:15:113230:42  lost rows: 10
113201:24:113230:48  lost rows: 10
```

This is a source-diverse and geometry-diverse failure inside the promoted
surface, not a single stale singleton.

## Margin Mechanism

The baseline wrong-history margins were already close to zero:

```text
baseline_wrong_history_margin_min: -0.000991
baseline_wrong_history_margin_max: -0.000063
```

After the M1147 actor update, all failed wrong-history branches cross positive:

```text
candidate_wrong_history_margin_min: 0.000118
candidate_wrong_history_margin_max: 0.001430
wrong_history_margin_crossing_delta_mean: 0.001142
```

Normal margins move in the opposite direction:

```text
normal_margin_delta_mean: 0.000769
normal_margin_delta_min: 0.000283
normal_margin_delta_max: 0.001057
```

So the candidate improves normal-history clearance while also making
wrong-history rollouts safe. That is exactly the self-identification proof
failure: the wrong hidden/history branch no longer produces the unsafe outcome
needed to demonstrate causal history dependence.

## Objective-Form Diagnosis

M1144 objective sanity was real:

```text
rows: 76
objective_pass: true
seed_pass_count: 3
mean_val_combined_loss_improvement: 3.211031
mean_val_pairwise_accuracy_after: 1.0
```

M1147 also improved exact M1144 loss:

```text
base exact loss: 0.417700
m1147_114602 exact loss: 0.409408
exact delta: -0.008292
```

The actor update stayed inside the allowed parameter surface:

```text
changed tensors:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
disallowed changed tensors: 0
log_std changed: false
max_abs_delta: 0.000496
```

The problem is not contract violation or optimizer instability. The problem is
that the M1144 preference objective is not a direct closed-loop terminal-margin
constraint.

The failed rows are low-weight, near-boundary braking rows:

```text
M1144 corpus rows with lost materialized failures: 49
M1144 corpus rows without lost materialized failures: 27

failed-row weight mean:    0.003962
nonfailed-row weight mean: 0.015196

failed-row wrong-history margin mean:    -0.000463
nonfailed-row wrong-history margin mean: -0.004114
```

This explains the mismatch:

```text
exact objective improvement:
  improves log-probability preference on the selected current hidden/action rows

closed-loop proof requirement:
  wrong-history rollouts must remain terminally unsafe on near-boundary rows
```

The current objective can improve the former while violating the latter.

## Artifacts

```text
runs/m1150_row15_promoted_first_replay_failure_audit/summary.json
runs/m1150_row15_promoted_first_replay_failure_audit/materialized_failed_rows_joined.csv
runs/m1150_row15_promoted_first_replay_failure_audit/materialized_failed_by_pair.csv
runs/m1150_row15_promoted_first_replay_failure_audit/materialized_failed_by_source.csv
runs/m1150_row15_promoted_first_replay_failure_audit/materialized_failed_by_geometry.csv
runs/m1150_row15_promoted_first_replay_failure_audit/m1144_corpus_failure_overlay.csv
```

## Decision

M1149 is confirmed as `proof_washout`, specifically
`wrong_history_safe_terminal_margin_crossing`.

The next repair should not be another generic actor update and should not
continue to family replay. It should design a terminal-margin-aware
wrong-history unsafe-margin projection or retention objective over the M1149
failed rows, while keeping old-public M267 retention explicit.

Because the `row15_promoted_target_materialization` branch has now reached its
synthesis cadence, the next milestone should be a branch synthesis that closes
this branch and opens a new `row15_promoted_unsafe_margin_projection` branch.

```text
decision: row15_promoted_first_replay_failure_audit_route_to_branch_synthesis
next: m1151-v4-public-base-row15-promoted-target-materialization-synthesis
```
