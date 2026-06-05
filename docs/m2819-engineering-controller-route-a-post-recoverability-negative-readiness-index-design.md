# M2819 Engineering Controller Route A Post-Recoverability Negative Readiness Index Design

## Metadata

- status: completed
- decision: `admit_post_recoverability_negative_readiness_index_materialization_preflight`
- manifest: `experiments/manifests/m2819-engineering-controller-route-a-post-recoverability-negative-readiness-index-design.json`
- design artifact: `docs/m2819-engineering-controller-route-a-post-recoverability-negative-readiness-index-design.md`
- parent synthesis: `docs/m2818-engineering-controller-route-a-post-action-response-recoverability-window-branch-synthesis.md`
- parent audit: `docs/m2817-engineering-controller-route-a-post-action-response-recoverability-window-instrumented-bounded-execution-result-audit.md`
- parent execution summary: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/summary.json`
- prior readiness index: `runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/summary.json`
- HF3 blocker: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-preflight.json`
- next: `m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-preflight`

## Design Decision

M2819 admits a no-execution readiness/admission index refresh:

```text
m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-preflight
```

M2820 should reanalyze existing artifacts only. It must not reset, step, run
policy action, rollout, replay, validate, train, run PPO, repair policy weights,
build source, probe adapters, import or run external simulators, rank
controllers, select winners, promote checkpoints, compute success-rate verdicts,
or claim repair success, driver performance, paper evidence, high-fidelity
validation, full-driver completion, or self-identification.

The purpose is to update the Route A readiness/admission map after M2818 closes
the recoverability-window branch as complete but negative. M2804/M2805 remains
valid as an older readiness index, but it predates M2816/M2817/M2818 and
therefore cannot be the current admission surface.

## Source Evidence

M2820 must include these source artifacts:

```text
M2818 synthesis:
  docs/m2818-engineering-controller-route-a-post-action-response-recoverability-window-branch-synthesis.md

M2817 audit:
  docs/m2817-engineering-controller-route-a-post-action-response-recoverability-window-instrumented-bounded-execution-result-audit.md

M2816 recoverability diagnostics:
  runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/summary.json
  runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/recoverability_window_rows.csv
  runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/post_offtrack_action_response_rows.csv
  runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/gate_matrix.csv

Prior readiness and blocker state:
  runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/summary.json
  runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/evidence_index.csv
  runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/blocker_matrix.csv
  runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/next_action_admission_rows.csv
  docs/m2805-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-result-audit.md

Route A deliverables:
  runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json
  public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json
  runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json

Source-only belief/action-response evidence:
  docs/m2777-engineering-controller-route-a-source-only-action-response-belief-intervention-branch-synthesis.md
  docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-synthesis.md

Route C blocker:
  docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md

Governing route split:
  docs/post-m2470-route-plan.md
```

M2820 may include additional directly traced Route A artifacts if they are used
only as diagnostic lineage and remain outside ranking or verdict claims.

## Required Preservation

M2820 must preserve the M2816/M2817 negative recoverability result as a blocker:

```text
fixed rows accounted: 12
instrumented execution rows: 12
execution failures: 0
diagnostic success outcomes: 6
diagnostic collision outcomes: 1
diagnostic offtrack terminations: 5
post-event available rows: 7
recoverability-window available rows: 0
recoverability-window success rows: 0
```

It must also preserve existing Route A and Route C blockers:

```text
M2801/M2802 negative clearance evidence remains active.
stable_avoidable retention risk remains active.
protected mitigation rows remain outside ordinary denominators.
prior-surface and same-clearance rows remain guardrails.
M2638 HF3 selected-platform execution remains blocked until source dependency evidence is supplied.
Route B paper and self-ID claims remain separate from Route A engineering diagnostics.
```

Actor boundary:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
recoverability labels actor-visible: false
action-response labels actor-visible: false
source-family/task-family labels actor-visible: false
blocker labels actor-visible: false
route-decision labels actor-visible: false
success/progress/verdict labels actor-visible: false
```

## M2820 Artifact Contract

M2820 should write:

```text
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/summary.json
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/evidence_index.csv
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/deliverable_readiness_rows.csv
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/blocker_matrix.csv
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/next_action_admission_rows.csv
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/claim_boundary_rows.csv
runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/gate_matrix.csv
docs/m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-preflight.md
experiments/manifests/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.json
```

Recommended `evidence_index.csv` fields:

```text
evidence_id
source_milestone
artifact_path
evidence_family
evidence_status
row_count
actor_contract_shape_72_action_3
action_shape_3
hidden_oracle_actor_input_detected
post_event_available_count
recoverability_window_available_count
recoverability_success_count
diagnostic_success_count
diagnostic_collision_count
diagnostic_offtrack_termination_count
claim_scope
gap_or_limit
next_use
source_exists
forbidden_interpretation
```

Recommended `blocker_matrix.csv` fields:

```text
blocker_id
route
evidence_family
current_status
blocking_count
required_next_evidence
admission_to_next_action
evidence_expansion_value
forbidden_shortcut
```

Required blocker rows:

```text
m2820_blocker_recoverability_window_absent
m2820_blocker_diagnostic_collision_and_offtrack
m2820_blocker_same_recoverability_local_search
m2820_blocker_negative_clearance_and_stable_avoidable_retention
m2820_blocker_protected_mitigation_and_guardrails
m2820_blocker_hf3_source_dependency_unavailable
m2820_blocker_validation_performance_not_admitted
m2820_blocker_actor_contract_guard
```

Recommended `next_action_admission_rows.csv` should include:

```text
m2821_post_recoverability_negative_readiness_index_result_audit:
  admitted

same_recoverability_window_repair_or_ranking:
  not_admitted

route_a_package_with_limitations:
  defer_until_m2821_audit

route_a_non_same_surface_evidence_route:
  defer_until_m2821_audit_and_design

route_b_controller_family_comparison:
  defer_to_separate_pre_registered_design

route_c_hf3_selected_platform_execution:
  not_admitted_until_source_dependency_supplied

validation_or_driver_performance_claim:
  not_admitted
```

## Gate Plan

M2820 passes only if:

```text
required source artifacts exist
required output artifacts exist
M2816 negative recoverability counts are preserved
M2816 diagnostic collision and offtrack counts are preserved
M2804/M2805 prior readiness blockers are carried forward or explicitly superseded
M2638 HF3 source dependency blocker remains active
actor observation/action contract remains 72/3
hidden/oracle actor input remains false
diagnostic labels remain actor-invisible
guardrail rows remain outside ordinary denominators
no reset/step/rollout/replay/validation/training/PPO/repair/source-build/adapter-probe/external-sim/ranking/promotion/verdict claim is made
M2821 audit manifest is registered
```

M2820 fails if it hides the absent recoverability window, hides collision or
offtrack terminations, weakens HF3 source-dependency gating, admits direct
recoverability repair/ranking, changes actor inputs, or converts readiness rows
into validation/performance/paper/high-fidelity/full-driver/self-ID evidence.

## Follow-Up Policy

M2820 should admit only M2821 result audit as the immediate next action. M2821
can then decide whether the refreshed index supports:

```text
package Route A with explicit limitations
design a new non-same-surface Route A evidence route
defer to a Route B controller-family comparison design
wait for Route C source dependency evidence
stop and preserve blockers
```

No execution, repair, ranking, validation, promotion, high-fidelity, paper, or
self-ID route is admitted directly by M2819.
