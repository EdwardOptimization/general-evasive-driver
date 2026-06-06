# M2955 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Candidate-Execution Admission Design

## Metadata

- status: completed
- decision: `admit_m2956_actor_head_delta_execution_admission_materialization_preflight`
- manifest: `experiments/manifests/m2955-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-candidate-execution-admission-design.json`
- parent audit: `docs/m2954-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-source-diverse-evidence-surface-materialization-result-audit.md`
- parent summary: `runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-preflight.json`
- next: `m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-preflight`

## Design Decision

M2955 admits exactly one next route:

```text
m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-preflight
```

M2955 is design-only. It does not reset, step, roll out, replay, validate, train, rank, promote, execute dependency work, load/modify/save checkpoints, run an adapter probe, select a winner, compute a success-rate verdict, or claim implementation readiness, repair success, driver performance, paper evidence, current-sim verdict, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.

The immediate route is not behavior execution. It is a no-execution execution-admission materialization that must bind the accepted M2953/M2954 actor-head delta surface to concrete Route A execution-admission rows from the already audited M2916/M2917 surface before any bounded runner route can be considered.

## Design Premise

M2954 accepts M2953 as complete and claim-safe:

```text
status_pass: true
gate_matrix_pass: true
evidence_source_row_count: 10
source_diversity_row_count: 4
panel_spec_row_count: 8
contract_traceability_row_count: 88
actor_contract_guard_row_count: 8
side_effect_guard_row_count: 12
claim_boundary_row_count: 19
gate_matrix_row_count: 14
source_family_count: 8
actor observation/action: 72/action 3
hidden_or_oracle_actor_inputs_required: false
future_target_actor_inputs_required: false
candidate_execution_admitted_in_m2953: false
```

M2953 is a contract and panel/spec surface. It proves the actor-head delta wrapper can be interpreted through a source-diverse contract surface, but it does not contain concrete executable task rows. Direct reset, rollout, or policy execution from M2953 would skip row-level task identity, checkpoint/config identity, guardrail accounting, and admission denominators.

M2917 accepts M2916 as a complete claim-safe Route A execution-admission materialization:

```text
status_pass: true
gate_matrix_pass: true
execution_admission_candidate_row_count: 67
execution_admission_admitted_count: 56
execution_admission_blocked_stale_fixed_surface_count: 11
actor observation/action: 72/action 3
hidden_oracle_actor_input_required: false
future_target_actor_input_required: false
reset_or_rollout_executed: false
validation_executed: false
training_executed: false
dependency_execution_performed: false
```

Therefore the highest leverage claim-safe next step is to combine these two accepted surfaces: M2953/M2954 supply the actor-head delta contract, while M2916/M2917 supply concrete Route A row identities that were already admitted only to a future separately audited execution route.

## M2956 Input Surface

M2956 must consume these M2953/M2954 artifacts:

```text
docs/m2955-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-candidate-execution-admission-design.md
docs/m2954-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-source-diverse-evidence-surface-materialization-result-audit.md
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/summary.json
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/panel_spec_rows.csv
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/contract_traceability_rows.csv
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/actor_contract_guard_rows.csv
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/side_effect_guard_rows.csv
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/claim_boundary_rows.csv
runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight/gate_matrix.csv
```

M2956 must also consume these accepted row-level Route A execution-admission artifacts:

```text
docs/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.md
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/summary.json
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_candidate_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_rejection_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/guardrail_context_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/actor_contract_guard_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/gate_matrix.csv
```

## Admission Rules

M2956 may materialize a candidate row only when all of these conditions hold:

```text
M2953 summary status_pass true
M2953 gate_matrix_pass true
M2954 audit acceptance token present
M2916 summary status_pass true
M2917 audit acceptance token present
M2916 row status is execution_admission_admitted_for_separate_bounded_execution_manifest
actor observation/action remains 72/action 3
actor input contract changed false
hidden/oracle actor input required false
future-target actor input required false
route labels, source labels, diagnostic labels, success/progress labels, and verdict labels remain actor-invisible
environment_reset_admitted remains false in M2956
environment_rollout_scheduled remains false in M2956
measured_validation_scheduled remains false
training_scheduled remains false
dependency_execution_scheduled remains false
profile_specific_tuning remains false
validation, promotion, paper, high-fidelity, and self-ID denominators remain false
```

Rows must be rejected or blocked if they match any of these conditions:

```text
stale fixed weak diagnostic rows
source identity unresolved rows
Route B source-family-insufficient rows
Route C source-unavailable rows
protected/package guard rows
hidden/oracle actor input rows
future-target actor input rows
denominator violation rows
claim-boundary violation rows
missing parent checkpoint path
missing profile config path
actor-head delta contract traceability missing
```

## Output Contract

M2956 should write this artifact pack:

```text
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/summary.json
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/input_surface_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_head_delta_execution_admission_candidate_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_head_delta_execution_admission_rejection_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/source_guardrail_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_delta_contract_guard_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/gate_matrix.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/run_state.json
docs/m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-preflight.md
experiments/manifests/m2957-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-result-audit.json
```

`actor_head_delta_execution_admission_candidate_rows.csv` must include at least:

```text
actor_head_delta_candidate_id
source_execution_admission_candidate_id
source_milestone
source_artifact
source_row_id
source_family
task_family
workload_id
task_source_id
profile_name
parent_checkpoint_path
parent_profile_config_path
actor_head_delta_panel_spec_ids
actor_head_delta_traceability_count
execution_admission_status
required_follow_up
environment_reset_admitted
environment_rollout_scheduled
measured_validation_scheduled
training_scheduled
dependency_execution_scheduled
checkpoint_load_scheduled
checkpoint_save_scheduled
checkpoint_mutation_scheduled
profile_specific_tuning
actor_observation_dim
actor_action_dim
actor_input_contract_changed
hidden_oracle_actor_input_required
future_target_actor_input_required
evaluator_labels_actor_visible
diagnostic_labels_actor_visible
success_progress_labels_actor_visible
verdict_labels_actor_visible
ordinary_engineering_denominator_allowed_after_audit
validation_denominator_allowed
paper_denominator_allowed
high_fidelity_readiness_allowed
self_id_claim_allowed
materialization_only_no_execution
claim_boundary
```

Allowed admission statuses:

```text
actor_head_delta_execution_admission_materialized_for_separate_bounded_execution_design
actor_head_delta_execution_admission_blocked_source_identity_unresolved
actor_head_delta_execution_admission_blocked_stale_fixed_surface
actor_head_delta_execution_admission_rejected_actor_contract_violation
actor_head_delta_execution_admission_rejected_hidden_oracle_required
actor_head_delta_execution_admission_rejected_future_target_required
actor_head_delta_execution_admission_rejected_denominator_boundary_violation
actor_head_delta_execution_admission_rejected_checkpoint_or_config_missing
actor_head_delta_execution_admission_rejected_delta_contract_trace_missing
```

M2956 must carry all non-admitted M2916 rows into rejection or guardrail artifacts. A pass may materialize admitted rows, but it must not execute them.

## Gate Matrix

M2956 passes only if all of these hold:

```text
M2953 summary status_pass true
M2953 gate_matrix_pass true
M2954 audit acceptance token present
M2916 summary status_pass true
M2917 audit acceptance token present
56 M2916 admitted rows loaded and materialized or accounted
11 stale fixed M2916 rows preserved as guardrails or rejection rows
all candidate rows preserve actor 72/action 3
all candidate rows preserve hidden_oracle_actor_input_required false
all candidate rows preserve future_target_actor_input_required false
all actor labels and verdict labels actor-invisible
actor-head delta traceability count is nonzero for every admitted candidate
environment_reset_admitted false
environment_rollout_scheduled false
measured_validation_scheduled false
training_scheduled false
dependency_execution_scheduled false
checkpoint_save_scheduled false
checkpoint_mutation_scheduled false
ranking_run false
winner_selected false
checkpoint_promoted false
success_rate_verdict_claim_made false
driver_performance_claim_made false
all required artifacts present
one result-audit follow-up manifest registered
```

## Follow-Up

M2955 admits:

```text
m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-preflight
```

M2956 must register a separate M2957 result audit before any bounded execution design or execution preflight.

## Claim Boundary

Allowed M2955 claim:

```text
M2955 defines one actor-safe no-execution materialization route that binds the audited M2953 actor-head delta surface to audited M2916 Route A execution-admission rows.
```

Rejected claims:

```text
candidate execution
implementation readiness
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
profile ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
current-sim verdict
high-fidelity readiness
finite-window-vs-GRU conclusion
full ideal driver completion
level3 self-identification
```
