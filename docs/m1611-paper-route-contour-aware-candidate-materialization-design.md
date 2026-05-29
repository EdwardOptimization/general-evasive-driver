# M1611 Paper-Route Contour-Aware Candidate Materialization Design

## Summary

M1611 designs candidate materialization after the M1609 diagnostic-complete
bounded replay pass and M1610 audit.

Decision:

```text
contour_aware_candidate_materialization_design_admit_offline_implementation
```

The next step may implement an offline materializer, but only as an artifact
export of candidate rows and diagnostic guardrails. It must not create a
training corpus, train, run PPO, promote, use private holdout, change actor
inputs, or claim level3 self-identification.

## Inputs

Use only M1609 public-pass replay outputs:

```text
runs/m1609_diagnostic_complete_bounded_replay/primary_classified_rows.csv
runs/m1609_diagnostic_complete_bounded_replay/diagnostic_classified_rows.csv
runs/m1609_diagnostic_complete_bounded_replay/summary.json
```

The implementation must preserve stable replay ids:

```text
pair_id = source_run::contour_pair_id
```

The materializer must not rerun replay or simulator dynamics.

## Candidate Eligibility

Candidate rows are eligible only if all conditions hold:

```text
source file: primary_classified_rows.csv
rule_bucket: primary
rule_reason: clean_edge_window_primary
label: history_control_separated
m1602_label: history_control_separated
missing_variants: empty
pair_id: stable source_run::pair id
```

Expected candidate count from M1609:

```text
candidate_directed_pair_count: 39
candidate_source_edge_count: 4
max_candidate_source_edge_share: 0.3333333333333333
```

Expected candidate source-edge counts:

```text
actuator_delay_step|capability_step_up: 13
actuator_delay_step|t5_near_boundary_warmup: 8
capability_step_down|t5_near_boundary_warmup: 6
curved_boundary_obstacle|t5_boundary_axis_retarget: 12
```

Diagnostic rows are not candidate rows. Endpoint-neighbor, negative-diagnostic,
and mixed-dominated diagnostic rows are guardrails only.

## Diagnostic Guardrails

Carry all diagnostic rows into a separate guardrail artifact:

```text
diagnostic_guardrail_directed_pair_count: 232
diagnostic_reason_count: 3
diagnostic_dominated_or_control_count >= 75
diagnostic_clean_share <= 0.02
```

M1609 observed:

```text
diagnostic_dominated_or_control_count: 81
diagnostic_clean_share: 0.008620689655172414
```

The implementation must not select diagnostic rows by label. It should carry
the full diagnostic set and write label summaries for audit only.

## Required M1612 Artifacts

M1612 should write:

```text
runs/m1612_contour_aware_candidate_materialization/summary.json
runs/m1612_contour_aware_candidate_materialization/candidate_rows.csv
runs/m1612_contour_aware_candidate_materialization/candidate_source_edge_summary.csv
runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_rows.csv
runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_summary.csv
runs/m1612_contour_aware_candidate_materialization/guardrail_summary.csv
docs/m1612-paper-route-contour-aware-candidate-materialization-implementation.md
```

Do not write:

```text
training_corpus.csv
*.pt
checkpoint files
PPO configs
promotion metadata
```

## Public Gates

M1612 should pass only if:

```text
candidate_directed_pair_count == 39
candidate_source_edge_count == 4
max_candidate_source_edge_share <= 0.35
candidate_rows_from_primary_only == true
candidate_rows_all_clean == true
candidate_rows_missing_variants_count == 0
candidate_pair_ids_unique == true
diagnostic_guardrail_directed_pair_count == 232
diagnostic_reason_count == 3
diagnostic_dominated_or_control_count >= 75
diagnostic_clean_share <= 0.02
diagnostic_rows_enter_candidate_rows == false
training_corpus_exported == false
candidate_materialized == true
candidate_materialization_only == true
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
guardrail_violation_count == 0
```

Here `candidate_materialized == true` means only public candidate-row artifacts
are written. It does not mean training corpus export or checkpoint
materialization.

## Audit Requirement

Any implementation must route to audit before:

```text
training corpus export
loss/objective construction
actor update
PPO
promotion
private holdout
paper-level claim
```

The audit should check whether the materialized candidate set is too narrow or
too public-row-specific before admitting any training-corpus design.

## Guardrails

```text
candidate_materialized: false in M1611
training_corpus_exported: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

Admit exactly one offline implementation:

```text
m1612-paper-route-contour-aware-candidate-materialization-implementation
```
