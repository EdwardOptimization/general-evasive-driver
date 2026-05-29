# M1606 Paper-Route Contour-Aware Bounded Replay Result Audit

## Summary

M1606 audits M1605.

Decision:

```text
contour_aware_bounded_replay_audit_admit_diagnostic_completeness_repair_design
```

M1605 is not a full pass. It is a split result: primary replay preserved the
clean contour, but the bounded diagnostic sample failed the dominated/control
count gate.

## Pair-ID Artifact

The first M1605 run found a metric artifact: directed `pair_id` values collide
across source runs. The implementation was fixed before the final run by using:

```text
source_run::pair_id
```

The final result is based on the corrected identifiers. The artifact is
recorded, but it is not the final blocker.

## Primary Result

The primary branch passed its intended contour checks:

```text
primary_replay_directed_pair_count: 144
primary_source_run_count: 2
primary_source_edge_count: 4
primary_clean_directed_pair_count: 39
primary_clean_source_edge_count: 4
max_primary_clean_source_edge_share: 0.3333333333333333
endpoint_neighbor_primary_count: 0
negative_diagnostic_primary_count: 0
mixed_diagnostic_primary_count: 0
required_variant_coverage_complete: true
anchor_replay_failure_count: 0
```

This supports the claim that the strict M1602 primary contour can be replayed
without losing the clean signal.

## Diagnostic Result

The diagnostic branch failed:

```text
diagnostic_replay_directed_pair_count: 96
diagnostic_reason_count: 3
diagnostic_dominated_or_control_count: 35
required: >= 50
diagnostic_clean_share: 0.0
```

By reason:

```text
endpoint_neighbor_exclusion:
  32 rows, 2 control-only, 30 null

mixed_dominated_edge:
  32 rows, 16 dominated, 1 control-only, 15 null

negative_diagnostic_edge:
  32 rows, 8 dominated, 8 control-only, 16 null
```

The failed claim is:

```text
a 96-row reason-capped diagnostic sample is enough to preserve negative/control evidence.
```

The failure does not invalidate the primary contour. It does block any replay
pass claim until diagnostic controls are fixed.

## Supported Claims

M1606 supports:

```text
the stable replay id fix is necessary and now applied;
primary contour replay preserved 39 clean rows;
diagnostic control evidence is insufficient under the M1605 sample;
one diagnostic-completeness repair design is justified.
```

## Unsupported Claims

M1606 does not support:

```text
M1605 public pass;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification;
level3 anticipatory self-identification.
```

## Repair Direction

The next design should be label-blind. It should not cherry-pick rows by the
M1602 labels. The clean repair is to replay the full diagnostic set by reason:

```text
primary rows: all 144 M1602 primary rows
diagnostic rows: all 232 M1602 diagnostic rows
diagnostic reasons: endpoint_neighbor_exclusion, negative_diagnostic_edge, mixed_dominated_edge
selection by labels: forbidden
```

This tests whether the diagnostic failure was caused by the `32` rows per reason
cap, not by the contour itself.

## Route Decision

Admit design-only milestone:

```text
m1607-paper-route-diagnostic-complete-bounded-replay-design
```

M1607 may design a diagnostic-complete replay. It must not run it.

## Guardrails

```text
replay_started: false in M1606
history_interventions_executed: false in M1606
candidate_materialized: false
training_started: false
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
m1607-paper-route-diagnostic-complete-bounded-replay-design
```
