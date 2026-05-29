# M1600 Paper-Route Clean Contour Mapper Result Audit

## Summary

M1600 audits M1599.

Decision:

```text
clean_contour_mapper_audit_admit_contour_aware_source_rule_design
```

M1599 is a successful offline diagnostic. It explains the M1592/M1595 split
well enough to justify a design-only contour-aware source rule. It does not
admit replay, materialization, training, PPO, promotion, or private holdout.

## M1599 Evidence

M1599 public gates passed:

```text
input_source_run_count: 3
input_directed_pair_count: 528
enriched_directed_pair_count: 528
metadata_joined_fraction: 1.0
clean_directed_pair_count: 51
dominated_history_positive_directed_pair_count: 72
control_only_positive_directed_pair_count: 79
history_null_all_controls_null_directed_pair_count: 326
source_edge_count: 24
feature_group_count: 398
passes_public_smoke_gates: true
null_result_classification: contour_mapping_public_pass
```

## Main Finding

The clean contour is not broad pairability. It is concentrated in
`clean_edge_window` rows on a small set of source edges.

Selection-source summary:

```text
M1592 clean_edge_window:
  112 rows, 29 clean, clean share 0.2589

M1595 clean_edge_window:
  32 rows, 10 clean, clean share 0.3125

M1595 clean_endpoint_neighbor:
  120 rows, 0 clean, 19 control-only, 101 null

M1595 negative_diagnostic_edge:
  40 rows, 0 clean, 13 dominated, 13 control-only, 14 null
```

The M1595 failure is therefore not mysterious. The round-robin rule broadened
selection into endpoint-neighbor and diagnostic edges that are mostly null or
control-only.

## Source-Edge Contour

Primary clean edges:

```text
actuator_delay_step|capability_step_up:
  18 clean / 48 rows

curved_boundary_obstacle|t5_boundary_axis_retarget:
  14 clean / 48 rows

actuator_delay_step|t5_near_boundary_warmup:
  10 clean / 48 rows

capability_step_down|t5_near_boundary_warmup:
  7 clean / 48 rows
```

Mixed/diagnostic edge:

```text
capability_step_up|t5_near_boundary_warmup:
  2 clean / 48 rows
  22 dominated / 48 rows
```

This edge should not be treated as primary clean evidence despite having a small
number of clean rows.

## Supported Claims

M1600 supports:

```text
offline contour mapping is operational;
M1592 succeeded because it heavily sampled clean_edge_window rows;
M1595 failed because it over-sampled endpoint-neighbor and diagnostic edges;
a contour-aware source-rule design is justified before any replay;
dominated/control-only rows remain central to the next rule.
```

## Unsupported Claims

M1600 does not support:

```text
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification;
level3 anticipatory self-identification;
immediate replay without design.
```

## Failure Taxonomy

```text
scenario_sampling_failure
objective_overfit
```

The next design must reduce both risks: avoid broad null-heavy sampling while
also avoiding a fixed-public-row gate-passing rule.

## Route Decision

Admit a design-only milestone:

```text
m1601-paper-route-contour-aware-source-rule-design
```

The design should:

```text
use clean_edge_window as the primary source contour;
prioritize the four primary clean source edges;
keep capability_step_up|t5_near_boundary_warmup as diagnostic/mixed;
exclude broad clean_endpoint_neighbor expansion from the primary set;
keep negative_diagnostic_edge rows as diagnostics only;
pre-register diversity and source-share gates;
route to implementation only after design;
route to audit after any implementation;
block replay, materialization, training, PPO, promotion, private holdout, and threshold relaxation in the design milestone.
```

## Guardrails

```text
replay_started: false
history_interventions_executed: false in M1600
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
m1601-paper-route-contour-aware-source-rule-design
```
