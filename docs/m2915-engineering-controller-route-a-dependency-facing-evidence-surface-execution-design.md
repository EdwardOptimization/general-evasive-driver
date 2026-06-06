# M2915 Engineering Controller Route A Dependency-Facing Evidence Surface Execution Design

## Metadata

- status: completed
- decision: `admit_m2916_dependency_facing_execution_admission_materialization_preflight`
- manifest: `experiments/manifests/m2915-engineering-controller-route-a-dependency-facing-evidence-surface-execution-design.json`
- parent audit: `docs/m2914-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-result-audit.md`
- parent summary: `runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight.json`
- next: `m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight`

## Design Decision

M2915 admits exactly one next route:

```text
m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight
```

M2915 is design-only. It does not reset, step, roll out, replay, validate,
train, rank, promote, execute dependency work, fetch source, configure, build,
import, link, probe an adapter, run a policy smoke, select a winner, compute a
success-rate verdict, or claim model quality, driver performance, paper
evidence, current-sim verdict, high-fidelity readiness, full-driver completion,
finite-window-vs-GRU evidence, or self-ID evidence.

The immediate route is not a behavior execution. It is a no-execution
execution-admission materialization that must turn the accepted M2913/M2914
dependency-facing surface into concrete source, admission, blocker, actor, and
claim-boundary rows before any runner route can be considered.

## Design Premise

M2914 accepts M2913 as complete and claim-safe:

```text
status_pass: true
gate_matrix_pass: true
route context rows: 5
candidate family rows: 5
exclusion family rows: 6
denominator policy rows: 6
failure taxonomy rows: 7
actor contract rows: 6
claim boundary rows: 8
gate rows: 10
ordinary engineering candidate family count: 1
route_b_context_only count: 1
route_c_context_only count: 1
claim_made_count: 0
actor observation/action: 72/action 3
hidden_oracle_actor_input_required: false
future_target_actor_input_required: false
```

The accepted surface is still a family-level materialization. It contains one
ordinary engineering candidate family, C1, but it does not yet contain concrete
row-level execution-admission candidates. Direct reset, step, rollout, or
runner execution from M2913 would skip the required row-level admission and
guardrail accounting.

## Execution-Admission Inputs

M2916 must consume these M2913/M2914 artifacts:

```text
docs/m2915-engineering-controller-route-a-dependency-facing-evidence-surface-execution-design.md
docs/m2914-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-result-audit.md
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/summary.json
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/route_context_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/candidate_family_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/exclusion_family_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/denominator_policy_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/failure_taxonomy_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/actor_contract_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/claim_boundary_rows.csv
runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight/gate_rows.csv
```

M2916 must then try to resolve the C1 family against existing Route A
diagnostic source artifacts. The first source inventory is bounded to:

```text
M2737 source-diverse closed-loop diagnostic execution rows: 18
M2746 source-diverse failure-taxonomy scenario-role execution rows: 14
M2807 post-clearance negative non-same repair cross-axis execution rows: 12
M2816 post-action-response recoverability-window instrumented execution rows: 12
M2877 post-package-refresh fixed fresh diagnostic execution rows: 11
```

M2877 rows are weak fixed-surface diagnostic context and must enter guardrail or
blocked status unless M2916 can prove a different row identity and denominator
policy. M2916 must preserve the M2912/M2914 interpretation that the M2879
3-success 0-collision 8-off-track result is not validation readiness.

## Admission Concepts

M2916 must distinguish these row types:

| Concept | Meaning |
| --- | --- |
| source inventory row | A required source artifact and row-count check used to build the admission surface. |
| execution-admission source row | A concrete prior Route A diagnostic row considered for later execution admission. |
| execution-admission candidate row | A row-level classification that may be admitted only to a later separately registered bounded execution preflight. |
| guardrail row | Route B, Route C, weak diagnostic, protected, package, hidden/oracle, future-target, denominator, or claim-boundary context that cannot be executed. |
| rejection/blocker row | An explicit row-level reason why a candidate is not admitted. |

M2916 may admit a row only to a later execution manifest. It may not execute the
row, rank it, convert it to a validation denominator, or use it as a
paper/self-ID row.

## Candidate Admission Rules

M2916 should admit only C1-compatible Route A rows that satisfy all conditions:

```text
source artifact exists
row identity is traceable to a prior Route A diagnostic source
actor observation/action remains 72/action 3
hidden/oracle actor input required is false
future-target actor input required is false
route labels, source labels, diagnostic labels, success/progress labels, and verdict labels remain actor-invisible
profile-specific tuning is false
ranking, winner selection, and promotion are false
ordinary engineering denominator is admitted only for a later audited execution preflight
validation, promotion, paper, high-fidelity, and self-ID denominators remain false
```

Rows must be rejected or blocked if they match any of these conditions:

```text
Route B source-family-insufficient rows
Route C source-unavailable rows
M2877 fixed weak diagnostic rows without a different source axis
protected/package guard rows
hidden/oracle actor input rows
future-target actor input rows
denominator violation rows
claim-boundary violation rows
missing or ambiguous source identity
```

## Output Contract

M2916 should write this artifact pack:

```text
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/summary.json
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_input_source_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_source_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_candidate_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_rejection_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/guardrail_context_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/actor_contract_guard_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/gate_matrix.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/run_state.json
docs/m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight.md
experiments/manifests/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.json
```

`execution_admission_candidate_rows.csv` must include at least:

```text
execution_admission_candidate_id
source_milestone
source_artifact
source_row_id
source_family
task_family
workload_id
task_source_id
profile_name
checkpoint_path
profile_config_path
candidate_family_id
candidate_family_name
execution_admission_status
execution_rejection_status
required_follow_up
environment_reset_admitted
environment_rollout_scheduled
measured_validation_scheduled
training_scheduled
dependency_execution_scheduled
profile_specific_tuning
actor_observation_dim
actor_action_dim
actor_input_contract_changed
hidden_oracle_actor_input_required
future_target_actor_input_required
route_labels_actor_visible
source_labels_actor_visible
diagnostic_labels_actor_visible
success_progress_labels_actor_visible
verdict_labels_actor_visible
ordinary_engineering_denominator_allowed_after_audit
validation_denominator_allowed
paper_denominator_allowed
high_fidelity_readiness_allowed
self_id_claim_allowed
diagnostic_only_no_verdict
materialization_only_no_execution
claim_boundary
```

Allowed admission statuses:

```text
execution_admission_admitted_for_separate_bounded_execution_manifest
execution_admission_blocked_source_identity_unresolved
execution_admission_blocked_stale_fixed_surface
execution_admission_blocked_route_b_source_family_insufficient
execution_admission_blocked_route_c_dependency_unavailable
execution_admission_rejected_actor_contract_violation
execution_admission_rejected_hidden_oracle_required
execution_admission_rejected_future_target_required
execution_admission_rejected_denominator_boundary_violation
execution_admission_rejected_claim_boundary_violation
execution_admission_rejected_source_artifact_missing
execution_admission_rejected_schema_inconsistent
```

## Gate Matrix

M2916 passes only if all of these hold:

```text
M2915 design exists
M2914 audit accepts M2913
M2913 summary status_pass true
M2913 gate_matrix_pass true
5 M2913 candidate families accounted
6 M2913 exclusion families accounted
6 denominator policies accounted
7 failure taxonomy rows accounted
6 actor contract rows accounted
8 claim boundary rows accounted
all required source artifacts are present or explicitly blocked
every loaded source row is admitted, rejected, or blocked
Route B rows executed false
Route C rows executed false
M2877 fixed weak diagnostic rows enter guardrail or blocked status unless a different source axis is proven
actor 72/action 3 preserved
hidden_oracle_actor_input_required false
future_target_actor_input_required false
actor input changed false
route/source/diagnostic/success/progress/verdict labels actor-visible false
environment_reset_admitted false
environment_rollout_scheduled false
validation_scheduled false
training_scheduled false
dependency_execution_scheduled false
ranking_run false
winner_selected false
checkpoint_promoted false
driver_performance_claim_made false
paper_claim_made false
high_fidelity_claim_made false
self_id_claim_made false
one result-audit follow-up manifest registered
```

Behavioral success or failure is not evaluated in M2916. A pass means the
execution-admission materialization is complete and claim-safe.

## Claim Boundary

Allowed M2915 claim:

```text
M2915 defines a bounded no-execution execution-admission materialization route
over the accepted M2913/M2914 dependency-facing surface.
```

Rejected claims:

```text
execution result
repair success
driver performance
validation readiness or result
source-family repair
Route C source availability
dependency execution result
controller-family ranking
source-family ranking
task-family ranking
profile ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
