# M2930 Engineering Controller Route A Offtrack-Dominant Repair Execution Design

## Metadata

- status: completed
- decision: `admit_m2931_offtrack_dominant_single_candidate_repair_execution_preflight`
- manifest: `experiments/manifests/m2930-engineering-controller-route-a-offtrack-dominant-repair-execution-design.json`
- parent audit: `docs/m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit.md`
- parent summary: `runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/summary.json`
- parent repair rows: `runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/repair_hypothesis_rows.csv`
- parent coverage rows: `runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/coverage_constraint_rows.csv`
- parent shortcut rows: `runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/shortcut_exclusion_rows.csv`
- follow-up manifest: `experiments/manifests/m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight.json`
- next: `m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight`

## Design Decision

M2930 admits exactly one next route:

```text
m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight
```

M2930 is design-only. It does not reset, step, roll out, replay, validate,
train, run PPO, rank, promote, execute dependency work, fetch source,
configure, build, import, link, probe an adapter, smoke a policy, select a
winner, compute a success-rate verdict, or claim repair success, driver
performance, paper evidence, current-sim verdict, high-fidelity readiness,
full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.

## Execution Surface

M2931 may consume only the accepted M2928/M2929 repair-admission chain, the
M2925 offtrack slice materialization, and the executable workload matrix:

```text
docs/m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit.md
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/summary.json
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/repair_hypothesis_rows.csv
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/coverage_constraint_rows.csv
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/shortcut_exclusion_rows.csv
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/actor_contract_guard_rows.csv
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight/gate_matrix.csv
runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight/offtrack_slice_rows.csv
runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight/non_offtrack_context_rows.csv
runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight/guardrail_context_rows.csv
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
```

The execution candidate set is the full 56-row M2925 panel:

```text
38 offtrack repair-target rows
18 non-offtrack context/regression rows
```

M2931 must preserve all M2928 coverage constraints:

```text
source split: M2737 12, M2746 10, M2807 8, M2816 8
task split: T4 21, T5 17
checkpoint context split: public pilot L3 28, M2655 mitigation-preserving 10
environment split: t5_near_boundary_warmup 12, t4_capability_step_temporal 9, t4_actuator_delay_response 8, t5_boundary_axis_retarget 5, t4_staged_warmup_capability 4
window split: mapping_window_unspecified 20, reveal_plus_4 9, decision_minus_32 5, decision_minus_24 4
overshoot split: low 5, medium 20, high 13
time-to-offtrack split: early 9, mid 20, late 9
```

The single repair candidate policy for M2931 is fixed:

```text
checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
profile config: runs/m1674_controller_family_one_seed_public_pilot/configs/L3_online_gru_seed167400.json
profile: L3_online_gru
actor observation/action: 72/action 3
```

M2931 must not train or alter this checkpoint. It must not compare multiple
checkpoints, select a winner, tune the profile, change actor inputs, or use a
repair overlay. The fixed M2655 candidate is evaluated because it is an
already-materialized actor-compatible repair candidate, not because it is
presumed to be better.

## Resolution Rules

M2931 must write an execution-resolution artifact before any reset or step.
For each of the 56 M2925 rows, resolution must preserve:

```text
source_milestone
source_row_id
task_family
workload_id
task_source_id
profile_name
original checkpoint_context
original checkpoint_path
repair_candidate_checkpoint_path
repair_candidate_profile_config_path
coverage row family tags
actor 72/action 3
claim boundary flags
```

Resolution rejects or accounts by failure row if:

```text
M2928 status_pass or gate_matrix_pass is false
M2929 audit does not accept M2928
the M2925 row is missing workload_id or task_source_id
workload_id is missing from the M1690 executable matrix
the fixed M2655 repair candidate checkpoint is missing
the fixed L3_online_gru config is missing
actor input contract would change
hidden/oracle/future-target actor input is required
route/source/diagnostic/success/progress/verdict labels would become actor-visible
the row would enter validation paper high-fidelity promotion or self-ID denominators
any M2877, Route B, or Route C guardrail row would be executed
```

If a row cannot be resolved, M2931 must write a failure row and continue
artifact accounting. It must not substitute another row, checkpoint, task
family, source family, profile, model, or rule-based controller.

## Execution Protocol

M2931 may execute reset, step, policy action, and rollout only for resolved
rows from the 56-row M2925 panel. It must execute at most one diagnostic
rollout per row. The default eval seed namespace is:

```text
eval_seed = 293100 + row_index
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
no source task checkpoint environment window severity time band ranking
no winner selection
no checkpoint promotion
no success-rate verdict computation
```

M2931 may record diagnostic closed-loop metrics such as termination reason,
collision, off-track, obstacle completion, clearance, episode length, return,
finite metric checks, and bounded row lineage. These fields remain diagnostic
only.

## Output Artifacts

M2931 should write:

```text
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/summary.json
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/repair_execution_candidate_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/repair_execution_resolution_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/repair_execution_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/repair_execution_failure_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/repair_target_context_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/coverage_constraint_audit_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/source_milestone_aggregate.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/task_family_aggregate.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/guardrail_context_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/actor_contract_guard_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/claim_boundary_rows.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/gate_matrix.csv
runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/run_state.json
docs/m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight.md
experiments/manifests/m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-audit.json
```

## Gate Matrix

M2931 passes only if all of these hold:

```text
M2930 design exists
M2929 accepts M2928
M2928 summary status_pass true
M2928 gate_matrix_pass true
M2928 coverage constraints all pass
M2928 shortcut exclusions all pass
56 M2925 panel rows loaded
38 offtrack rows loaded and accounted
18 non-offtrack context rows loaded and accounted
56 rows resolved or explicitly accounted by failure rows
only M2925 panel rows are execution candidates
fixed M2655 repair candidate checkpoint exists
fixed L3_online_gru config exists
M2877 guard rows executed false
Route B context rows executed false
Route C context rows executed false
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
repair_success_claim_made false
driver_performance_claim_made false
validation_readiness_claim_made false
paper_claim_made false
high_fidelity_claim_made false
self_id_claim_made false
one result-audit follow-up manifest registered
```

Behavioral failure rows may still pass the artifact gate if every admitted row
is accounted for and all claim/actor/blocker boundaries are clean. A pass does
not mean the repair candidate succeeded.

## Follow-Up

M2930 admits:

```text
m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight
```

M2931 must register M2932 result audit before any interpretation.

## Claim Boundary

Allowed M2930 claim:

```text
M2930 defines an actor-safe bounded diagnostic execution protocol for the
accepted M2928/M2929 repair-admission surface and admits one separately
pre-registered single-candidate repair execution preflight.
```

Rejected claims:

```text
execution result
repair success
driver performance
validation readiness or result
source-family ranking
task-family ranking
checkpoint ranking
environment ranking
window ranking
severity/time-band ranking
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
