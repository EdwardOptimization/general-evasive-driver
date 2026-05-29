# M1589 Paper-Route History-vs-Control Selector Result Audit

## Summary

M1589 audits M1588.

Decision:

```text
history_vs_control_selector_audit_admit_clean_source_generation_repair_design
```

M1588 is a clean selector-only implementation. It passes public diagnostic
gates, but the clean history-vs-control surface remains just below the
evidence-quality count target.

This should not be handled by relaxing the threshold. The next route should
design source-generation repair that uses the clean-label criteria directly.

## M1588 Evidence

Public selector gates passed:

```text
input_directed_pair_count: 144
classified_directed_pair_count: 144
required_variant_coverage_complete: true
clean_directed_pair_count: 7
clean_source_edge_count: 4
dominated_history_positive_directed_pair_count: 16
null_or_control_only_directed_pair_count: 121
guardrail_violation_count: 0
passes_public_smoke_gates: true
```

Evidence-quality failed:

```text
passes_evidence_quality_targets: false
null_result_classification: selector_public_pass_clean_shortfall
clean_directed_pair_count: 7
target clean_directed_pair_count: 8
```

Clean diversity is acceptable but small:

```text
clean_source_edge_count: 4
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.2857142857142857
```

Label counts:

```text
history_control_separated: 7
history_positive_control_dominated: 16
control_only_positive: 28
history_null_all_controls_null: 93
```

## Interpretation

M1588 supports a narrow but real clean surface:

```text
history gap >= 0.02;
control gap < 0.75 * history gap;
hidden-specific gap or wrong-history gap present;
source spread across 4 edges.
```

It does not support history necessity or materialization. The clean count is too
small and comes from fixed public rows.

## Route Decision

Do not route to:

```text
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout;
another broad pairability intervention;
post-hoc clean threshold relaxation.
```

Admit a design-only milestone:

```text
m1590-paper-route-clean-history-control-source-generation-repair-design
```

The next design should use the clean selector as the source-generation target:

```text
positive seeds:
  M1588 clean rows and their source edges.

negative diagnostics:
  M1588 dominated rows and control-only rows.

repair objective:
  generate more matched-current hidden-divergent pairs whose interventions are likely history-control separated,
  not merely pairable.
```

## Suggested Repair Targets

Clean source edges from M1588:

```text
actuator_delay_step|t5_near_boundary_warmup
actuator_delay_step|capability_step_up
curved_boundary_obstacle|t5_boundary_axis_retarget
capability_step_down|t5_near_boundary_warmup
```

Dominated edges to treat as negative diagnostics:

```text
capability_step_up|t5_near_boundary_warmup
capability_step_up|curved_boundary_obstacle
capability_step_up|t5_boundary_axis_retarget
capability_step_down|drive_loss_proxy
```

The design must also keep high-speed endpoint absence as a caveat. Do not claim
high-speed history sensitivity from this branch.

## Failure Taxonomy

```text
scenario_sampling_failure
```

The selector works; the sampled clean surface is too small.

## Guardrails

```text
history_interventions_executed: false in M1589
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
m1590-paper-route-clean-history-control-source-generation-repair-design
```
