# M1603 Paper-Route Contour-Aware Source Rule Result Audit

## Summary

M1603 audits M1602.

Decision:

```text
contour_aware_source_rule_audit_admit_bounded_replay_design
```

M1602 is a successful offline selector implementation. It supports designing a
bounded replay experiment, but it does not itself admit replay, candidate
materialization, training-corpus export, training, PPO, promotion, private
holdout, or paper-level self-identification claims.

## M1602 Evidence

M1602 public offline gates passed:

```text
input_contour_row_count: 528
primary_rule_directed_pair_count: 144
primary_source_edge_count: 4
primary_clean_directed_pair_count: 39
primary_clean_source_edge_count: 4
max_primary_clean_source_edge_share: 0.3333333333333333
endpoint_neighbor_primary_count: 0
negative_diagnostic_primary_count: 0
mixed_diagnostic_primary_count: 0
diagnostic_directed_pair_count: 232
diagnostic_dominated_or_control_count: 81
excluded_directed_pair_count: 152
guardrail_violation_count: 0
passes_public_smoke_gates: true
```

## Primary Evidence

The primary rule is clean enough to justify a replay-design milestone:

```text
selection_source == clean_edge_window
source_edge in four primary clean source edges
144 primary rows
39 clean rows
4 clean source edges
max clean source-edge share <= 0.35
```

This avoids the M1595 failure mode because endpoint-neighbor expansion is not
allowed into primary evidence.

## Diagnostic Evidence

The diagnostic set remains large:

```text
diagnostic rows: 232
dominated/control diagnostic rows: 81
endpoint-neighbor diagnostics: 120
negative-edge diagnostics: 64
mixed-edge diagnostics: 48
```

This is important. The next replay design must keep these rows as controls or
exclusion checks, not silently discard them. Otherwise the branch would regress
into fixed-public-row overfit.

## Supported Claims

M1603 supports:

```text
the offline contour-aware selector works;
the strict primary rule avoids endpoint-neighbor leakage;
the diagnostic rows preserve negative evidence;
a bounded replay-design milestone is justified.
```

## Unsupported Claims

M1603 does not support:

```text
replay has passed;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification;
level3 anticipatory self-identification.
```

## Replay-Design Requirements

The next design must pre-register:

```text
primary replay rows come only from M1602 primary_rule_rows.csv;
diagnostic controls come from M1602 diagnostic_rule_rows.csv;
endpoint-neighbor rows remain excluded from primary evidence;
negative and mixed dominated rows remain diagnostic controls;
max replayed primary source-edge share is capped;
diagnostic replay/control outcomes are reported separately;
result routes to audit before materialization or training;
no actor-input changes, private holdout, PPO, promotion, or threshold relaxation.
```

## Route Decision

Admit a design-only milestone:

```text
m1604-paper-route-contour-aware-bounded-replay-design
```

M1604 may design a bounded replay. It must not run it.

## Guardrails

```text
replay_started: false
history_interventions_executed: false in M1603
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
m1604-paper-route-contour-aware-bounded-replay-design
```
