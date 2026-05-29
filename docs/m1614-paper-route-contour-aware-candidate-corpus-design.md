# M1614 Paper-Route Contour-Aware Candidate Corpus Design

## Summary

M1614 designs a candidate corpus package from M1612 artifacts.

Decision:

```text
contour_aware_candidate_corpus_design_admit_offline_export
```

This is not a training corpus design. The next implementation may export a
candidate corpus package with roles and metadata, but it must not build a loss,
train, run PPO, promote, use private holdout, or make paper-level/self-ID
claims.

## Inputs

Use only:

```text
runs/m1612_contour_aware_candidate_materialization/candidate_rows.csv
runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_rows.csv
runs/m1612_contour_aware_candidate_materialization/summary.json
```

## Corpus Roles

The package should have two separate row roles:

```text
positive_candidate:
  source: candidate_rows.csv
  count: 39
  use: public proof candidate rows only
  allowed labels: history_control_separated

diagnostic_guardrail:
  source: diagnostic_guardrail_rows.csv
  count: 232
  use: guardrail and audit only
  allowed as positive candidate: false
```

Diagnostics must never be mixed into positive candidate rows.

## Metadata

The package must write explicit metadata:

```text
public_proof_artifact: true
private_holdout_used: false
paper_level_claim_supported: false
level3_self_id_claim_supported: false
training_ready: false
requires_export_audit: true
requires_objective_design_before_training: true
```

The corpus can include role weights as metadata only:

```text
positive_candidate_default_weight: 1.0
diagnostic_guardrail_training_weight: 0.0
```

These weights must not be treated as a loss/objective. Any objective or training
use requires a later design and audit.

## Required M1615 Artifacts

M1615 should write:

```text
runs/m1615_contour_aware_candidate_corpus/summary.json
runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv
runs/m1615_contour_aware_candidate_corpus/diagnostic_guardrail_rows.csv
runs/m1615_contour_aware_candidate_corpus/corpus_manifest.json
runs/m1615_contour_aware_candidate_corpus/role_summary.csv
runs/m1615_contour_aware_candidate_corpus/source_edge_summary.csv
runs/m1615_contour_aware_candidate_corpus/guardrail_summary.csv
docs/m1615-paper-route-contour-aware-candidate-corpus-export-implementation.md
```

Do not write:

```text
training_corpus.csv
loss_config.json
objective_config.json
*.pt
checkpoint files
PPO configs
promotion metadata
```

## Public Gates

M1615 should pass only if:

```text
candidate_corpus_exported == true
training_corpus_exported == false
loss_constructed == false
objective_constructed == false
positive_candidate_count == 39
diagnostic_guardrail_count == 232
positive_rows_all_clean == true
diagnostic_rows_used_as_positive == false
candidate_pair_ids_unique == true
diagnostic_pair_ids_unique == true
source_edge_count == 4
max_source_edge_share <= 0.35
public_proof_metadata_complete == true
requires_export_audit == true
requires_objective_design_before_training == true
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
guardrail_violation_count == 0
```

## Audit Requirement

Any export must route to audit before:

```text
loss/objective design
actor update
PPO
promotion
private holdout
paper-level claim
```

## Guardrails

```text
candidate_corpus_exported: false in M1614
training_corpus_exported: false
loss_constructed: false
objective_constructed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

Admit one offline export implementation:

```text
m1615-paper-route-contour-aware-candidate-corpus-export-implementation
```
