# M1595 Paper-Route Selector-Balanced Clean-Source Repair Implementation

## Summary

M1595 implemented the selector-balanced cap repair designed by M1594.

Decision:

```text
selector_balanced_clean_source_repair_overbalanced_clean_shortfall_route_to_audit
```

This is a negative result. The stricter source-edge round-robin cap fixed the
selection-side diversity objective, but it diluted the clean signal too much:

```text
selected_source_edge_count: 24
clean_directed_pair_count: 10
clean_source_edge_count: 4
null_result_classification: clean_count_shortfall
```

M1595 does not pass, does not admit materialization, and does not justify a
third immediate implementation. It routes to audit.

## Commands

Focused tests:

```bash
PYTHONPATH=src python -m pytest tests/test_clean_history_control_source_generation_repair.py -q
```

Result:

```text
4 passed
```

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.clean_history_control_source_generation_repair \
  --output-dir runs/m1595_selector_balanced_clean_source_repair_smoke \
  --seed 1901 \
  --max-source-specs 480 \
  --max-selected-pairs 96 \
  --max-pairs-per-source-edge 12 \
  --min-selected-source-edges 8 \
  --device cpu
```

## Artifacts

```text
runs/m1595_selector_balanced_clean_source_repair_smoke/summary.json
runs/m1595_selector_balanced_clean_source_repair_smoke/source_spec_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/selected_pair_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/intervention_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/classified_directed_pair_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/clean_directed_pair_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/source_edge_summary.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/label_summary.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/variant_summary.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/guardrail_summary.csv
```

## Result

```text
source_spec_count: 480
selected_pair_count: 96
selected_source_edge_count: 24
selected_endpoint_source_family_count: 8
selected_window_count: 6
directed_pair_count: 192
intervention_row_count: 1536
classified_directed_pair_count: 192
required_variant_coverage_complete: true
invalid_directed_pair_count: 0
clean_directed_pair_count: 10
clean_source_edge_count: 4
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.4
dominated_history_positive_directed_pair_count: 17
control_only_positive_directed_pair_count: 33
history_null_all_controls_null_directed_pair_count: 132
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
null_result_classification: clean_count_shortfall
guardrail_violation_count: 0
```

Label counts:

```text
history_control_separated: 10
history_positive_control_dominated: 17
control_only_positive: 33
history_null_all_controls_null: 132
```

## Comparison With M1592

```text
M1592 selected_source_edge_count: 7
M1592 clean_directed_pair_count: 34
M1592 clean_source_edge_count: 5
M1592 max_clean_source_edge_share: 0.35294117647058826

M1595 selected_source_edge_count: 24
M1595 clean_directed_pair_count: 10
M1595 clean_source_edge_count: 4
M1595 max_clean_source_edge_share: 0.4
```

M1595 shows that broad source-edge round-robin is too blunt. It improves
selection diversity but pulls too many rows from edges that are pairable yet
history-null or control-only.

## Interpretation

M1595 falsifies the assumption that stronger source-edge balancing alone will
preserve the clean signal. The repair needs a more selective active-set rule if
the branch continues:

```text
not broad round-robin over all pairable source edges;
not post-hoc threshold relaxation;
not another immediate cap tweak;
audit first.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

The sampled balanced surface is too broad and clean-count poor.

## Guardrails

```text
history_interventions_executed: true
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

Route to audit:

```text
m1596-paper-route-selector-balanced-repair-result-audit
```

The audit should decide whether to stop, synthesize, or design a more selective
active-set contour. It must not run another repair directly.
