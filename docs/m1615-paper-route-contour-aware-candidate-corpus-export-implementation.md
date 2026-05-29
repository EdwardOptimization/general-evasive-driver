# M1615 Paper-Route Contour-Aware Candidate Corpus Export Implementation

## Summary

M1615 exports the candidate corpus package designed in M1614.

Decision:

```text
contour_aware_candidate_corpus_export_public_pass_route_to_audit
```

The implementation writes a candidate corpus package, not a training corpus. It
does not construct a loss or objective, train, run PPO, promote, use private
holdout, change actor inputs, or claim level3 self-identification.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_contour_aware_candidate_corpus_export.py -q
```

Result:

```text
3 passed in 2.11s
```

Export:

```text
PYTHONPATH=src python -m autodrift.contour_aware_candidate_corpus_export --output-dir runs/m1615_contour_aware_candidate_corpus
```

## Result

```text
candidate_corpus_exported: true
training_corpus_exported: false
loss_constructed: false
objective_constructed: false
positive_candidate_count: 39
diagnostic_guardrail_count: 232
positive_rows_all_clean: true
diagnostic_rows_used_as_positive: false
candidate_pair_ids_unique: true
diagnostic_pair_ids_unique: true
source_edge_count: 4
max_source_edge_share: 0.3333333333333333
public_proof_metadata_complete: true
requires_export_audit: true
requires_objective_design_before_training: true
guardrail_violation_count: 0
```

Blocked operations:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

Outcome:

```text
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
null_result_classification: contour_aware_candidate_corpus_export_public_pass
```

## Package Files

```text
corpus_manifest.json
diagnostic_guardrail_rows.csv
guardrail_summary.csv
positive_candidate_rows.csv
role_summary.csv
source_edge_summary.csv
summary.json
```

No `training_corpus.csv`, loss config, objective config, checkpoint, or PPO
config was written.

## Corpus Manifest

```text
public_proof_artifact: true
private_holdout_used: false
paper_level_claim_supported: false
level3_self_id_claim_supported: false
training_ready: false
requires_export_audit: true
requires_objective_design_before_training: true
positive_candidate_default_weight: 1.0
diagnostic_guardrail_training_weight: 0.0
```

## Role Summary

```text
positive_candidate: 39 rows, role_weight 1.0, candidate_only
diagnostic_guardrail: 232 rows, role_weight 0.0, guardrail_only
```

## Source Edge Summary

```text
actuator_delay_step|capability_step_up: 13
actuator_delay_step|t5_near_boundary_warmup: 8
capability_step_down|t5_near_boundary_warmup: 6
curved_boundary_obstacle|t5_boundary_axis_retarget: 12
```

## Interpretation

M1615 makes the public proof artifacts easier to consume by later tooling while
preserving their limitations. The package is explicitly not training-ready and
requires audit plus later objective design before any actor update or PPO.

## Next

Route to result audit:

```text
m1616-paper-route-contour-aware-candidate-corpus-export-result-audit
```
