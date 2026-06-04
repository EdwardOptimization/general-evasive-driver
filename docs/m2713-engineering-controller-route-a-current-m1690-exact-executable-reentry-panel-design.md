# M2713 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Panel Design

## Metadata

- status: completed
- decision: `admit_current_m1690_exact_executable_reentry_panel_materialization_preflight`
- manifest: `experiments/manifests/m2713-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-design.json`
- design artifact: `docs/m2713-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-design.md`
- parent synthesis: `docs/m2712-engineering-controller-protected-runner-current-m1690-workload-fixture-support-branch-synthesis.md`
- exact workload reference: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv`
- protected proposal reference: `runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/protected_workload_fixture_proposal_rows.csv`
- follow-up manifest: `experiments/manifests/m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight.json`
- next: `m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight`

## Design Decision

M2713 admits one bounded no-execution materialization preflight for a
current-M1690 exact-executable reentry panel. The panel must admit only source
rows that already exist in the M1690 executable workload matrix. It must
explicitly exclude every M2710 protected workload fixture proposal from
execution admission.

The decision is:

```text
admit_current_m1690_exact_executable_reentry_panel_materialization_preflight
```

This route is a pivot away from protected proposal accounting and back to a
closed-loop executable surface. It is not a protected execution route,
performance route, ranking route, validation route, paper route, high-fidelity
route, or self-ID route.

## Source Evidence

M2712 closed the protected workload fixture support branch because M2710/M2711
left the protected side in this state:

```text
protected workload fixture proposal rows: 12
proposed-new current-M1690 rows: 12
ready-existing current-M1690 rows: 0
existing exact M1690 matches: 0
fabricated exact M1690 matches: 0
execution-admitted protected rows: 0
protected targets accounted: 10/10
```

M2693 provides the recent exact-executable anchor surface:

```text
current-runner target execution rows: 9
runtime profile: L3_online_gru
task families: T4 rows 5, T5 rows 4
termination: off_track 7, speed_too_low 2
diagnostic success: 0/9
protected targets recorded non-executable: 10/10
```

The M1690 executable workload matrix contains a valid existing current-runner
surface:

```text
existing workload rows: 864
profiles: 12 profiles x 72 rows each
task families: T4 432, T5 432
environment_rollout_scheduled: false for all rows
training_scheduled: false for all rows
profile_specific_tuning: false for all rows
```

M2638 keeps the selected-platform HF3 route paused until a source dependency is
supplied. M2713 therefore does not route back to HF3 build/probe work.

## Reentry Panel Scope

M2714 must materialize a panel with exactly two conceptual surfaces:

```text
exact executable candidates:
  existing current-M1690 workload rows only
  source-backed by workload_id in executable_workload_matrix.csv
  eligible for a later bounded execution preflight only after M2714 audit

protected proposal exclusions:
  all M2710 protected workload fixture proposal rows
  not exact existing current-M1690 rows
  not execution candidates
  outside ordinary success denominators
```

The exact executable candidate panel should use M2693 as the anchor because it
is the most recent closed-loop Route A surface that actually ran environment
reset, step, and policy action while preserving the actor contract. For each
of the 9 M2693 executed `task_source_id` anchors, M2714 must admit the four
existing M1690 profile rows below:

```text
L0_current_masked
L2_window_50_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Expected materialized exact-executable candidates:

```text
anchor task_source_ids: 9
selected profiles per anchor: 4
exact executable candidate rows: 36
missing selected profile rows allowed: 0
```

The selected profiles are included only to preserve a bounded current-M1690
reentry surface with current-response, finite-window/current-tiled, online GRU,
and reset/truncated-control representatives. M2713 does not rank them, select
a winner, claim a controller-family result, or make a finite-window-vs-GRU
claim.

## Admission Rules

M2714 must use these statuses:

```text
exact_executable_reentry_admitted_existing_m1690_workload
exact_executable_reentry_rejected_missing_m1690_workload
exact_executable_reentry_rejected_missing_profile_config
exact_executable_reentry_rejected_missing_checkpoint
exact_executable_reentry_excluded_m2710_proposed_protected_row
exact_executable_reentry_excluded_hf3_dependency_blocked
```

An execution candidate row is admitted only if all are true:

```text
workload_id exists in executable_workload_matrix.csv
task_source_id matches one of the 9 M2693 anchor task_source_ids
profile_name is one of the 4 selected profile names
config_exists is true
checkpoint_exists is true
environment_rollout_scheduled is false in the source matrix
training_scheduled is false in the source matrix
profile_specific_tuning is false in the source matrix
actor input contract remains P0 72/3
row is not derived from an M2710 protected proposal
```

Every M2710 protected proposal row must become an exclusion row:

```text
exact_executable_reentry_excluded_m2710_proposed_protected_row
```

The exclusion reason must preserve:

```text
workload_fixture_support_proposed_new_current_m1690_row
proposed_new_current_m1690_workload_row_not_existing_match
workload_fixture_support_blocker_existing_m1690_match_absent
execution_admitted: false
```

## Output Contract

M2714 should write this artifact pack:

```text
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/summary.json
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/input_source_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/exact_executable_candidate_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/profile_context_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/protected_proposal_exclusion_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/hf3_dependency_blocker_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/actor_contract_guard_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/claim_boundary_rows.csv
runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/gate_matrix.csv
docs/m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight.md
```

Expected counts:

```text
input source rows: at least 8
exact executable candidate rows: 36
profile context rows: 36
protected proposal exclusion rows: 12
hf3 dependency blocker rows: at least 1
actor-contract guard rows: at least 9
claim-boundary rows: at least 24
gate rows: at least 18
```

The summary must expose:

```text
status_pass
required_artifacts_present
gate_matrix_pass
m1690_existing_workload_row_count
m2693_anchor_task_source_id_count
selected_profile_count
exact_executable_candidate_row_count
candidate_rows_all_existing_m1690
missing_selected_profile_row_count
m2710_protected_proposal_exclusion_row_count
protected_execution_admitted_row_count
protected_rows_in_success_denominator
actor_contract_shape_72_action_3
hidden_oracle_actor_input_detected
execution_run
validation_run
training_run
ranking_run
driver_performance_claim_made
```

## Actor And Claim Boundary

M2714 must preserve:

```text
observation_shape: 72
action_shape: 3
action_mapping: [steer, throttle, brake]
hidden_oracle_actor_input_detected: false
target labels actor-visible: false
protected labels actor-visible: false
blocker labels actor-visible: false
route labels actor-visible: false
success/progress/verdict labels actor-visible: false
protected rows in ordinary success denominators: false
```

M2714 must not expose hidden dynamics, oracle fields, feasibility labels,
AEB/AES/drift labels, controller mode, speed references, path error, heading
error, path curvature, TTC, required clearance, oracle stopping distance,
reward terms, collision/success labels, route decisions, protected blocker
labels, or verdict labels to actor input.

M2714 must not run reset, step, policy action, rollout, replay, validation,
training, PPO, private holdout, profile-specific tuning, ranking, winner
selection, checkpoint promotion, success-rate verdict computation, or driver
performance interpretation. It is materialization only.

## Follow-Up Route

The next route is:

```text
m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight
```

If M2714 materializes the panel with 36 exact existing workload rows and 12
protected exclusions while preserving all guards, a later audit may choose one
bounded execution preflight. That later execution must still be diagnostic,
must keep protected proposal rows blocked, and must not claim ranking,
validation, performance, paper evidence, current-sim verdict, high-fidelity
validation, full ideal driver completion, or self-ID.

If M2714 cannot source-back all 36 rows or cannot preserve the protected
exclusion boundary, it must fail closed and route to result audit or branch
synthesis rather than forcing execution.

## Rejected Routes

M2713 rejects:

```text
direct protected execution from M2710 proposal rows
another protected workload fixture support design/materialization/audit hop
HF3 selected-platform build/probe work without supplied source dependency
controller-family ranking from a design artifact
promotion or winner selection from a reentry panel design
driver-performance, paper, current-sim, high-fidelity, or self-ID claims
```

## Claim Boundary

Allowed M2713 claim:

```text
M2713 designs a bounded current-M1690 exact-executable reentry panel
materialization route that admits only existing M1690 workload ids and keeps
all M2710 protected proposal rows excluded from execution.
```

Rejected claims:

```text
protected execution result
protected mitigation preservation result
repair success
driver performance
validation readiness or result
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
