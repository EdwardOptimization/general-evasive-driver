# M2705 Engineering Controller Protected Runner Simulator/Workload Support Design

## Metadata

- status: completed
- decision: `admit_protected_runner_simulator_workload_support_materialization_preflight`
- manifest: `experiments/manifests/m2705-engineering-controller-protected-runner-simulator-workload-support-design.json`
- design artifact: `docs/m2705-engineering-controller-protected-runner-simulator-workload-support-design.md`
- parent audit: `docs/m2704-engineering-controller-protected-runner-execution-admission-materialization-result-audit.md`
- parent summary: `runs/m2703_engineering_controller_protected_runner_execution_admission/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2706-engineering-controller-protected-runner-simulator-workload-support-materialization-preflight.json`
- next: `m2706-engineering-controller-protected-runner-simulator-workload-support-materialization-preflight`

## Design Decision

M2705 admits one bounded no-execution simulator/workload support
materialization preflight. It does not admit protected execution, reset, step,
rollout, replay, measured validation, training, PPO, ranking, winner
selection, promotion, success-rate verdicts, repair-success claims,
driver-performance claims, paper claims, current-sim verdicts, high-fidelity
validation claims, full ideal driver completion, or self-ID claims.

The design decision is deliberately narrower than execution admission:

```text
M2703 blocked execution-admission row:
  row-level proof that a protected adapter candidate was considered
  not an executable workload row
  not a simulator fixture
  not behavior evidence

M2706 simulator/workload support row:
  row-level support representation for a blocked protected candidate
  may classify required workload fixture/runtime-adapter support
  may record blockers and traceability
  must remain no-execution and no-verdict

Future actual execution row:
  separately pre-registered behavior route only after support is audited
  requires explicit execution admission
  does not exist in M2705
```

M2705 therefore routes to M2706 materialization. M2706 may transform M2703
blocked rows into support source rows, support candidate rows, support blocker
rows, traceability rows, actor-contract guard rows, claim-boundary rows, and
gate rows. It must not schedule or run environment execution.

## Governing Constraints

`docs/post-m2470-route-plan.md` split the project into Route A engineering,
Route B paper evidence, and Route C high-fidelity interface work. M2705 remains
a Route A engineering-controller boundary artifact. It makes the protected
runner support surface auditable; it does not create paper evidence, current
simulator verdict evidence, high-fidelity validation evidence, or driver
performance evidence.

The required source facts are:

```text
M2700:
  adapter candidate mapping rows: 12
  adapter traceability rows: 160
  adapter status: adapter_contract_materialized_not_execution_admitted
  execution-admitted rows: 0
  exact M1690 workload matches: 0

M2703:
  input source rows: 13
  execution-admission candidate rows: 12
  execution-admission rejection rows: 12
  execution-admission traceability rows: 160
  actor-contract guard rows: 11
  claim-boundary rows: 34
  gate rows: 22
  execution-admission status: execution_admission_blocked_no_current_m1690_workload for 12/12 rows
  execution-admitted rows: 0
  exact M1690 workload matches: 0
  protected targets accounted: 10/10

M2704:
  accepts M2703 as complete and claim-safe materialization evidence only
  rejects direct protected execution
  routes to simulator/workload support design
```

The active blocker remains:

```text
protected runner candidates are represented in adapter and
execution-admission classifications, but no current M1690 workload row admits
them to execution.
```

## Support Concepts

M2706 must distinguish these row types:

| Concept | Meaning |
| --- | --- |
| execution-admission candidate row | A M2703 row proving one M2700 adapter candidate was classified for execution admission. |
| execution-admission blocker row | A M2703 rejection row stating why a candidate was not admitted to execution. |
| support input source row | A source-artifact accounting row used by the support materializer. |
| support candidate row | A no-execution row describing whether a blocked protected candidate can be represented by current simulator/workload support or needs new support. |
| support blocker row | A row-level blocker for support materialization, not a protected execution failure. |
| support traceability row | Lineage from protected target, source edge, adapter candidate, execution-admission candidate, workload candidate, runner spec, and M1690 reference schema. |
| actual execution row | A future separately audited behavior row. No M2705 or M2706 row may become this row. |

The expected conservative state for current inputs is:

```text
execution-admission candidate rows consumed: 12
support candidate rows expected: 12
execution-admitted rows preserved: 0
exact M1690 workload matches preserved: 0
support-ready existing M1690 rows expected: 0
environment reset scheduled: false
environment rollout scheduled: false
measured validation scheduled: false
training scheduled: false
```

If M2706 finds a support-ready row, it must prove the exact current M1690
workload match from source artifacts and still preserve no-execution status.
For the present M2703/M2704 state, the expected support classification is that
all 12 rows require new workload/support representation before any execution
route.

## Input Contract

M2706 should consume these artifacts:

| Input | Required use |
| --- | --- |
| `docs/m2705-engineering-controller-protected-runner-simulator-workload-support-design.md` | Verify the design boundary and allowed follow-up route. |
| `docs/m2704-engineering-controller-protected-runner-execution-admission-materialization-result-audit.md` | Verify M2704 accepted M2703 only as claim-safe classification evidence and routed to support design. |
| `runs/m2703_engineering_controller_protected_runner_execution_admission/summary.json` | Verify status, counts, no-execution flags, 0 admitted rows, 0 exact M1690 matches, and actor/claim boundaries. |
| `execution_admission_input_source_rows.csv` | Preserve source-artifact accounting for support materialization. |
| `execution_admission_candidate_rows.csv` | Create one support candidate for each blocked execution-admission candidate. |
| `execution_admission_rejection_rows.csv` | Preserve row-level blocker reasons and required follow-up text. |
| `execution_admission_traceability_rows.csv` | Preserve 160 traceability rows and 10/10 protected target accounting. |
| `actor_contract_guard_rows.csv` | Preserve P0 observation 72, action 3, and no hidden/oracle actor input. |
| `claim_boundary_rows.csv` | Preserve blocked claims and no-execution status. |
| `gate_matrix.csv` | Preserve M2703 gate state before support materialization. |
| `runs/m2700_engineering_controller_protected_runner_adapter_contract/summary.json` | Verify adapter-contract source state and 0 execution admission. |
| `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_candidate_mapping_rows.csv` | Preserve adapter candidate lineage. |
| `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_traceability_rows.csv` | Preserve protected target lineage before execution-admission classification. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json` | Use only as executable task schema reference. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv` | Use only as current executable workload reference; do not fabricate exact matches. |
| `docs/post-m2470-route-plan.md` | Preserve Route A/B/C claim separation. |

M2706 must fail if required source artifacts are missing, if M2703
`status_pass` or `gate_matrix_pass` is false, if M2704 did not route to support
design, if any support row requires hidden/oracle actor input, if protected
labels would become actor-visible, or if protected rows would enter ordinary
success denominators.

## Output Contract

M2706 should write this machine-auditable pack:

```text
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/summary.json
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/support_input_source_rows.csv
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/support_candidate_rows.csv
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/support_blocker_rows.csv
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/support_traceability_rows.csv
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/actor_contract_guard_rows.csv
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/claim_boundary_rows.csv
runs/m2706_engineering_controller_protected_runner_simulator_workload_support/gate_matrix.csv
docs/m2706-engineering-controller-protected-runner-simulator-workload-support-materialization-preflight.md
```

`support_input_source_rows.csv` must include one row per required source
artifact with at least:

```text
source_artifact_id
source_path
source_exists
required
row_count_or_summary
source_role
claim_scope
blocked_interpretation
```

`support_candidate_rows.csv` must include one row per M2703
execution-admission candidate with at least:

```text
support_candidate_id
execution_admission_candidate_id
adapter_candidate_id
workload_candidate_id
runner_spec_id
source_panel_spec_id
profile_name
policy_subject_id
protected_task_family
protected_source_edge
execution_admission_status
m1690_exact_workload_match
m1690_reference_workload_id
support_status
support_blocker_status
support_rule
required_follow_up
candidate_can_be_represented_in_current_runner
candidate_requires_new_workload_row
candidate_requires_simulator_fixture
candidate_requires_runtime_adapter
environment_reset_scheduled
environment_rollout_scheduled
measured_validation_scheduled
training_scheduled
profile_specific_tuning
actor_input_contract_changed
hidden_oracle_actor_input_required
protected_labels_actor_visible
protected_rows_in_success_denominator
materialization_only_no_execution
diagnostic_only_no_verdict
claim_scope
```

Allowed `support_status` values:

```text
support_ready_existing_m1690_workload
support_materialized_candidate_requires_new_workload_row
support_materialized_candidate_requires_simulator_fixture
support_materialized_candidate_requires_runtime_adapter
support_blocked_schema_inconsistent
support_blocked_source_artifact_missing
support_blocked_hidden_oracle_required
support_blocked_actor_visible_protected_label
support_blocked_denominator_boundary_violation
support_blocked_actor_contract_changed
```

For current M2703/M2704 inputs, M2706 should not produce
`support_ready_existing_m1690_workload` unless it can cite exact source evidence
that M2703 did not have.

`support_blocker_rows.csv` must include at least:

```text
blocker_id
support_candidate_id
execution_admission_candidate_id
adapter_candidate_id
blocker_type
blocker_reason
required_follow_up
actor_visible
claim_scope
```

`support_traceability_rows.csv` must preserve the M2703 traceability count and
target coverage unless it records an explicit blocker:

```text
traceability_id
support_candidate_id
execution_admission_candidate_id
adapter_candidate_id
runner_spec_id
source_panel_spec_id
protected_target_id
source_traceability_id
traceability_axis
source_artifact
target_accounted
claim_scope
```

`actor_contract_guard_rows.csv` must verify:

```text
P0 observation shape: 72
action shape: 3
deployed action contract: steer, throttle, brake
hidden/oracle actor input required: false
target labels actor-visible: false
protected labels actor-visible: false
blocker labels actor-visible: false
route labels actor-visible: false
verdict labels actor-visible: false
```

`claim_boundary_rows.csv` must keep all protected rows outside ordinary success
denominators and must block execution, validation, training, ranking,
promotion, success-rate verdict, repair-success, driver-performance,
paper-level, current-sim, high-fidelity, full ideal driver, and self-ID claims.

## Gate Contract

M2706 should write a `gate_matrix.csv` containing at least these gates:

```text
source_artifacts_present
m2705_design_present
m2704_support_route_decision_present
m2703_status_pass
m2703_gate_matrix_pass
support_input_source_rows_cover_required_sources
support_candidates_cover_execution_admission_candidates
support_blockers_cover_non_ready_rows
support_status_values_valid
blocked_execution_admission_rows_not_reinterpreted_as_execution
m1690_exact_match_boundary_preserved
expected_zero_admitted_preserved_without_exact_match
support_ready_rows_zero_without_exact_m1690_match
protected_targets_accounted
m1690_reference_schema_consumed
actor_contract_preserved
protected_labels_actor_invisible
no_hidden_oracle_actor_input
protected_not_success_denominator
materialization_only_no_execution
claim_boundary_blocks_overclaim
follow_up_audit_registered
required_artifacts_present
```

The support pack may pass only if all 12 M2703 candidates are classified, all
non-ready rows have explicit support blockers, 0 execution-admitted rows remain
visible, 0 exact M1690 workload matches remain visible, 10/10 protected targets
remain accounted, and all no-execution and actor-boundary gates pass.

## Follow-up Route

Decision:

```text
admit_protected_runner_simulator_workload_support_materialization_preflight
```

The next route is:

```text
m2706-engineering-controller-protected-runner-simulator-workload-support-materialization-preflight
```

M2706 is the only admitted next action. It may materialize support rows and an
audit-follow-up manifest. It must not execute environments or reinterpret
support rows as protected execution evidence. If M2706 cannot represent the
blocked rows within the current support schema, it must preserve the blocker
and route to taxonomy normalization, branch synthesis, or stop.

## Claim Boundary

Allowed M2705 claim:

```text
M2705 designs a no-execution simulator/workload support materialization route
for M2703 blocked protected runner execution-admission rows while preserving
actor/action and claim boundaries.
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
