# M2702 Engineering Controller Protected Runner Execution Admission Design

## Metadata

- status: completed
- decision: `admit_protected_runner_execution_admission_materialization_preflight`
- manifest: `experiments/manifests/m2702-engineering-controller-protected-runner-execution-admission-design.json`
- design artifact: `docs/m2702-engineering-controller-protected-runner-execution-admission-design.md`
- parent audit: `docs/m2701-engineering-controller-protected-runner-adapter-contract-materialization-result-audit.md`
- parent summary: `runs/m2700_engineering_controller_protected_runner_adapter_contract/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight.json`
- next: `m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight`

## Admission Decision

M2702 admits a no-execution protected runner execution-admission
materialization preflight. It does not admit reset, step, rollout, replay,
validation, training, PPO, ranking, winner selection, promotion, success-rate
verdicts, repair-success claims, protected mitigation preservation claims,
driver-performance claims, paper claims, current-sim verdicts, high-fidelity
validation claims, full ideal driver completion, or self-ID claims.

The design decision is deliberately narrow:

```text
M2700 adapter rows:
  complete adapter-contract rows
  not execution rows
  not validation rows
  not performance rows

M2702 design:
  define the next admission classification boundary
  preserve 0 execution-admitted source rows
  preserve 0 exact M1690 workload matches
  require explicit row-level admission, rejection, or blocked status
```

M2702 therefore routes to M2703 materialization. M2703 may classify the M2700
adapter rows, but it must keep all environment execution switches off.

## Governing Constraints

`docs/post-m2470-route-plan.md` split the project into Route A engineering,
Route B paper evidence, and Route C high-fidelity interface work. M2702 is a
Route A engineering-controller boundary artifact. It may make the protected
runner interface more auditable, but it cannot create paper evidence or
driver-performance evidence.

The required source facts are:

```text
M2697:
  protected runner spec rows: 12
  protected workload candidate rows: 12
  traceability rows: 160
  protected targets accounted: 10/10
  exact M1690 workload matches: 0

M2699:
  adapter-contract design admitted M2700 only
  no behavior execution admitted

M2700:
  input source rows: 11
  adapter candidate mapping rows: 12
  adapter rejection rows: 0
  adapter traceability rows: 160
  actor-contract guard rows: 11
  claim-boundary rows: 33
  gate rows: 19
  adapter status: adapter_contract_materialized_not_execution_admitted
  adapter execution-admitted rows: 0
  exact M1690 workload matches: 0

M2701:
  accepted M2700 artifact completeness and claim safety
  rejected direct protected execution
  routed to execution-admission design
```

The central blocker remains visible:

```text
protected candidates are adapter-contract rows, but no current M1690 workload
row admits them to execution.
```

## Admission Concepts

M2703 must distinguish these row types:

| Concept | Meaning |
| --- | --- |
| adapter-contract row | A M2700 row that maps a protected runner candidate into an auditable offline contract. |
| execution-admission source row | A source-artifact row proving which inputs were considered for admission classification. |
| execution-admission candidate row | A row-level classification of one M2700 adapter candidate. |
| execution-admission rejection row | An explicit rejected or blocked condition with required follow-up. |
| execution-admitted row | A row eligible only for a later separately pre-registered protected execution route. No such row exists in M2700. |

An adapter-contract row must not be reinterpreted as an execution-admitted row
unless all required execution-admission gates pass. For the current M2700
inputs, the expected conservative outcome is:

```text
source adapter candidate rows: 12
execution-admitted rows: 0
rows blocked by no current M1690 workload: 12
environment reset scheduled: false
environment rollout scheduled: false
measured validation scheduled: false
```

If M2703 finds a different result, it must show the exact source evidence and
preserve a separate no-execution audit before any behavior route.

## Input Contract

M2703 should consume these artifacts:

| Input | Required use |
| --- | --- |
| `docs/m2702-engineering-controller-protected-runner-execution-admission-design.md` | Verify the design boundary and allowed follow-up route. |
| `docs/m2701-engineering-controller-protected-runner-adapter-contract-materialization-result-audit.md` | Verify M2701 accepted M2700 only as adapter-contract evidence. |
| `runs/m2700_engineering_controller_protected_runner_adapter_contract/summary.json` | Verify source counts, 0 execution-admitted rows, 0 exact M1690 matches, and claim-boundary flags. |
| `adapter_input_source_rows.csv` | Preserve source artifact accounting. |
| `adapter_candidate_mapping_rows.csv` | Classify each M2700 adapter candidate into an admission status. |
| `adapter_rejection_rows.csv` | Preserve current rejection-row state, including explicit empty-header behavior. |
| `adapter_traceability_rows.csv` | Preserve 160 traceability rows and 10/10 protected target accounting. |
| `actor_contract_guard_rows.csv` | Preserve P0 observation 72, action 3, and no hidden/oracle actor input. |
| `claim_boundary_rows.csv` | Preserve blocked claims and no-execution status. |
| `gate_matrix.csv` | Preserve M2700 gate state before admission classification. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json` | Use only as executable task schema reference. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv` | Use only as current executable workload reference; do not fabricate exact matches. |

M2703 must fail the materialization if any required source artifact is missing,
if M2701 is not accepted, if M2700 `status_pass` is not true, or if admission
classification would require hidden/oracle actor input.

## Output Contract

M2703 should write a machine-auditable pack:

```text
runs/m2703_engineering_controller_protected_runner_execution_admission/summary.json
runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_input_source_rows.csv
runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_candidate_rows.csv
runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_rejection_rows.csv
runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_traceability_rows.csv
runs/m2703_engineering_controller_protected_runner_execution_admission/actor_contract_guard_rows.csv
runs/m2703_engineering_controller_protected_runner_execution_admission/claim_boundary_rows.csv
runs/m2703_engineering_controller_protected_runner_execution_admission/gate_matrix.csv
docs/m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight.md
```

`execution_admission_input_source_rows.csv` must include one row per required
source artifact with at least:

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

`execution_admission_candidate_rows.csv` must include one row per M2700
adapter candidate with at least:

```text
execution_admission_candidate_id
adapter_candidate_id
workload_candidate_id
runner_spec_id
source_panel_spec_id
profile_name
policy_subject_id
policy_checkpoint_path
policy_checkpoint_exists
reference_profile_config_path
reference_profile_config_exists
adapter_admission_status
m1690_exact_workload_match
m1690_reference_workload_id
protected_task_family
protected_source_edge
execution_admission_status
execution_rejection_status
execution_admission_rule
required_follow_up
environment_reset_admitted
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

Allowed `execution_admission_status` values:

```text
execution_admission_admitted_for_separate_execution_manifest
execution_admission_blocked_no_current_m1690_workload
execution_admission_blocked_adapter_not_execution_admitted
execution_admission_rejected_missing_policy_checkpoint
execution_admission_rejected_missing_reference_profile_config
execution_admission_rejected_hidden_oracle_required
execution_admission_rejected_actor_visible_protected_label
execution_admission_rejected_denominator_boundary_violation
execution_admission_rejected_actor_contract_changed
execution_admission_rejected_source_artifact_missing
execution_admission_rejected_schema_inconsistent
```

M2703 must use the admitted status only when the source row has an exact
current executable workload match and all actor, label, denominator, and
claim-boundary guards pass. With the current M2700 source facts, the admitted
count should remain zero.

`execution_admission_rejection_rows.csv` must include rejected or blocked rows.
It must not be silently empty if candidate rows are not admitted. Minimum
fields:

```text
rejection_id
candidate_or_source_id
rejection_type
rejection_reason
required_follow_up
actor_visible
claim_scope
```

`execution_admission_traceability_rows.csv` must carry forward every M2700
adapter traceability row and preserve 10/10 protected target accounting.

## Actor And Claim Boundary

M2703 may use protected taxonomy and route labels only as offline metadata for
row classification. They remain actor-invisible.

The deployed actor/action contract remains:

```text
observation_shape: 72
action_shape: 3
action_mapping: [steer, throttle, brake]
hidden_oracle_actor_input_required: false
actor_input_contract_changed: false
target_labels_actor_visible: false
protected_labels_actor_visible: false
blocker_labels_actor_visible: false
route_labels_actor_visible: false
verdict_labels_actor_visible: false
protected_rows_in_success_denominator: false
```

All execution switches stay off:

```text
environment_reset_admitted: false
environment_rollout_scheduled: false
measured_validation_scheduled: false
training_scheduled: false
profile_specific_tuning: false
materialization_only_no_execution: true
diagnostic_only_no_verdict: true
```

## Gate Matrix

M2703 should pass only if all gates pass:

| Gate | Required condition |
| --- | --- |
| source artifacts present | M2702, M2701, M2700, and M1690 schema references exist. |
| M2701 accepted | M2701 decision routes to M2702 design and does not admit execution. |
| M2700 accepted | M2700 `status_pass` true and adapter contract gates pass. |
| candidate classification coverage | All 12 M2700 adapter candidates receive an admission or rejection status. |
| rejection rows complete | Every non-admitted row has an explicit rejection or blocked row. |
| M1690 boundary preserved | Rows with no exact M1690 match cannot be marked as execution-admitted. |
| current expected admitted count | Current M2700 rows produce 0 execution-admitted rows unless new exact-match source evidence exists. |
| traceability preserved | 160 traceability rows and 10/10 protected targets remain accounted. |
| actor contract preserved | Observation 72, action 3, and no hidden/oracle actor input. |
| label boundary preserved | Target, protected, blocker, route, and verdict labels remain actor-invisible. |
| denominator boundary preserved | Protected rows remain outside ordinary success denominators. |
| no execution | No reset, step, rollout, replay, validation, training, PPO, ranking, promotion, or performance verdict. |
| claim boundary preserved | No repair-success, driver-performance, paper, current-sim, high-fidelity, full ideal driver, or self-ID claim. |
| follow-up audit registered | A bounded result-audit route is registered before any protected execution route. |

## Failure Taxonomy

- `contract_violation`: fire if admission classification changes actor input,
  action shape, hidden/oracle availability, label visibility, or denominator
  boundary.
- `lineage_invalid`: fire if M2703 cannot trace each candidate back to M2700,
  M2697, and M1690 schema references.
- `metric_artifact`: fire if admission rows are interpreted as success-rate,
  validation, ranking, or performance evidence.
- `scenario_sampling_failure`: remains active because current protected rows
  still do not match current M1690 executable workload rows.
- `behavior_regression`: remains active until a separately admitted execution
  route measures protected behavior.
- `objective_overfit`: fire if the branch continues static protected process
  work without materializing admission rows, writing a synthesis, or stopping.
- `proof_washout`: fire if 0 exact M1690 matches or 0 execution-admitted rows
  are hidden behind aggregate acceptance language.

## Admitted Follow-Up

M2702 admits:

```text
m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight
```

M2703 may materialize execution-admission input-source, candidate, rejection,
traceability, actor-contract, claim-boundary, and gate rows. It may also
pre-register a bounded result audit. It must not route directly to reset, step,
rollout, replay, validation, training, ranking, promotion, performance
interpretation, paper evidence, high-fidelity validation, full ideal driver
completion, or self-ID claims.

## Claim Boundary

Allowed M2702 claim:

```text
M2702 defines a protected runner execution-admission classification boundary
and admits a bounded no-execution materialization preflight.
```

Rejected claims:

```text
protected execution admission result
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
