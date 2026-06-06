# M2918 Engineering Controller Route A Dependency-Facing Evidence Surface Bounded Execution Design

## Metadata

- status: completed
- decision: `admit_m2919_dependency_facing_bounded_execution_preflight`
- manifest: `experiments/manifests/m2918-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-design.json`
- parent audit: `docs/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.md`
- parent summary: `runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/summary.json`
- parent candidate rows: `runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_candidate_rows.csv`
- follow-up manifest: `experiments/manifests/m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight.json`
- next: `m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight`

## Design Decision

M2918 admits exactly one next route:

```text
m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight
```

M2918 is design-only. It does not reset, step, roll out, replay, validate,
train, run PPO, rank, promote, execute dependency work, fetch source,
configure, build, import, link, probe an adapter, smoke a policy, select a
winner, compute a success-rate verdict, or claim driver performance, paper
evidence, current-sim verdict, high-fidelity readiness, full-driver
completion, finite-window-vs-GRU evidence, or self-ID evidence.

## Execution Surface

M2919 may consume only the accepted M2916 admission surface and M2917 audit:

```text
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/summary.json
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_candidate_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/execution_admission_rejection_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/guardrail_context_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/actor_contract_guard_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/gate_matrix.csv
docs/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.md
```

The execution candidate set is exactly the 56 M2916 rows with:

```text
execution_admission_status: execution_admission_admitted_for_separate_bounded_execution_manifest
ordinary_engineering_denominator_allowed_after_audit: true
validation_denominator_allowed: false
paper_denominator_allowed: false
high_fidelity_readiness_allowed: false
self_id_claim_allowed: false
actor observation/action: 72/action 3
hidden_oracle_actor_input_required: false
future_target_actor_input_required: false
```

Source distribution:

```text
M2737 source-diverse closed-loop diagnostic rows: 18
M2746 source-diverse failure-taxonomy scenario-role rows: 14
M2807 post-clearance non-same cross-axis rows: 12
M2816 recoverability-window instrumented rows: 12
```

M2919 must not execute the 11 M2877 fixed weak diagnostic rows. Those rows
remain guardrail context only.

## Resolution Rules

M2919 must write an execution-resolution artifact before any reset or step.
For each of the 56 admitted rows, resolution must preserve:

```text
execution_admission_candidate_id
source_milestone
source_row_id
source_family
task_family
workload_id
task_source_id
profile_name
checkpoint_path
profile_config_path
actor 72/action 3
claim boundary flags
```

Resolution rejects any row if:

```text
it is not admitted by M2916
it belongs to M2877 fixed weak diagnostic guard rows
checkpoint_path or profile_config_path is missing
profile_name is not the preserved source profile
actor input contract would change
hidden/oracle/future-target actor input is required
route/source/diagnostic/success/progress/verdict labels would become actor-visible
the row would enter validation paper high-fidelity promotion or self-ID denominators
```

If a row cannot be resolved, M2919 must write a failure row and continue
artifact accounting. It must not substitute another row, profile, checkpoint,
task family, source family, or repair overlay.

## Execution Protocol

M2919 may execute reset, step, policy action, and rollout only for resolved
M2916 admitted rows. It must execute at most one diagnostic rollout per row.
The default eval seed namespace is:

```text
eval_seed = 291900 + row_index
```

Execution constraints:

```text
no replay
no measured validation
no training or PPO
no source build or dependency execution
no adapter probe or external simulation
no private holdout
no profile-specific tuning
no active config overwrite
no repair overlay
no profile source family task family controller ranking
no winner selection
no checkpoint promotion
no success-rate verdict computation
```

M2919 may record diagnostic closed-loop metrics such as termination reason,
collision, off-track, obstacle completion, clearance, episode length, return,
finite metric checks, and bounded row lineage. These fields remain diagnostic
only.

## Output Artifacts

M2919 should write:

```text
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/summary.json
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/execution_candidate_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/execution_resolution_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/bounded_execution_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/bounded_execution_failure_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/source_milestone_aggregate.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/task_family_aggregate.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/guardrail_context_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/actor_contract_guard_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/claim_boundary_rows.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/gate_matrix.csv
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/run_state.json
docs/m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight.md
experiments/manifests/m2920-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-result-audit.json
```

## Gate Matrix

M2919 passes only if all of these hold:

```text
M2918 design exists
M2917 accepts M2916
M2916 summary status_pass true
M2916 gate_matrix_pass true
67 M2916 candidate rows loaded
56 admitted rows loaded
11 M2877 guard rows loaded and not executed
56 admitted rows resolved or explicitly accounted by failure rows
only M2916 admitted rows are execution candidates
Route B context rows executed false
Route C context rows executed false
M2877 guard rows executed false
actor 72/action 3 preserved
hidden_oracle_actor_input_required false
future_target_actor_input_required false
actor input changed false
route/source/diagnostic/success/progress/verdict labels actor-visible false
profile_specific_tuning false
active_config_overwritten false
dependency_execution_performed false
replay validation training PPO private holdout false
ranking_run false
winner_selected false
checkpoint_promoted false
success_rate_verdict_claim_made false
driver_performance_claim_made false
validation_readiness_claim_made false
paper_claim_made false
high_fidelity_claim_made false
self_id_claim_made false
one result-audit follow-up manifest registered
```

Behavioral failure rows may still pass the artifact gate if every admitted row
is accounted for and all claim/actor/blocker boundaries are clean. A pass does
not mean the driver succeeded.

## Follow-Up

M2918 admits:

```text
m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight
```

M2919 must register M2920 result audit before any interpretation.

## Claim Boundary

Allowed M2918 claim:

```text
M2918 defines an actor-safe bounded diagnostic execution protocol for the
accepted M2916 dependency-facing admission surface and admits one separately
pre-registered execution preflight.
```

Rejected claims:

```text
execution result
repair success
driver performance
validation readiness or result
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
