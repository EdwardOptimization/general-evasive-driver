# M1588 Paper-Route History-vs-Control Active-Set Selector Implementation

## Summary

M1588 implements the selector-only classifier designed in M1587.

Decision:

```text
history_vs_control_active_set_selector_public_pass_clean_shortfall_route_to_audit
```

The selector reproduces the M1586 diagnosis:

```text
clean history-vs-control rows exist;
the clean surface is below evidence-quality count target;
source-generation repair is likely needed, but audit must come first.
```

No simulator, history intervention, training, PPO, materialization, or corpus
export was run.

## Implementation

New module:

```text
src/autodrift/history_vs_control_active_set_selector.py
```

Focused tests:

```text
tests/test_history_vs_control_active_set_selector.py
```

Focused test result:

```text
PYTHONPATH=src python -m pytest tests/test_history_vs_control_active_set_selector.py -q
3 passed
```

## Command

```bash
PYTHONPATH=src python -m autodrift.history_vs_control_active_set_selector --input-rows runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv --output-dir runs/m1588_history_vs_control_active_set_selector
```

## Result

Artifact:

```text
runs/m1588_history_vs_control_active_set_selector/summary.json
```

Key metrics:

```text
input_directed_pair_count: 144
classified_directed_pair_count: 144
required_variant_coverage_complete: true
clean_directed_pair_count: 7
clean_source_edge_count: 4
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.2857142857142857
dominated_history_positive_directed_pair_count: 16
control_only_positive_directed_pair_count: 28
history_null_all_controls_null_directed_pair_count: 93
invalid_directed_pair_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
null_result_classification: selector_public_pass_clean_shortfall
```

Label counts:

```text
history_control_separated: 7
history_positive_control_dominated: 16
control_only_positive: 28
history_null_all_controls_null: 93
```

Clean source edges:

```text
actuator_delay_step|t5_near_boundary_warmup
actuator_delay_step|capability_step_up
curved_boundary_obstacle|t5_boundary_axis_retarget
capability_step_down|t5_near_boundary_warmup
```

## Interpretation

M1588 is a clean selector implementation. It does not strengthen the self-ID
claim. It confirms:

```text
the clean active-set exists;
the clean count is one below the pre-registered evidence-quality target;
the broad pairability route should not proceed directly to materialization or training;
the next route should audit whether to design source-generation repair using clean-label criteria.
```

## Supported Claims

M1588 supports:

```text
M1585 rows can be reproducibly classified into clean, dominated, null, and control-only labels;
the clean history-vs-control sub-surface spans 4 source edges and 6 endpoint families;
the selector public diagnostic gates pass.
```

## Unsupported Claims

M1588 does not support:

```text
history necessity;
source-diverse self-identification;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level result;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

The selector itself worked. The clean surface is still too small for
evidence-quality targets.

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
guardrail_violation_count: 0
```

## Next

```text
m1589-paper-route-history-vs-control-selector-result-audit
```
