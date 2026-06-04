# M2699 Engineering Controller Protected Runner Adapter Contract Design

## Metadata

- status: completed
- decision: `admit_protected_runner_adapter_contract_materialization_preflight`
- manifest: `experiments/manifests/m2699-engineering-controller-protected-runner-adapter-contract-design.json`
- design artifact: `docs/m2699-engineering-controller-protected-runner-adapter-contract-design.md`
- parent audit: `docs/m2698-engineering-controller-protected-mitigation-runner-spec-generation-materialization-result-audit.md`
- parent materialization: `runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight.json`
- next: `m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight`

## Admission Decision

M2699 admits a protected runner adapter contract materialization preflight. It
does not admit reset, step, rollout, replay, validation, training, PPO,
ranking, winner selection, promotion, success-rate verdicts, protected
mitigation preservation claims, driver-performance claims, paper claims,
current-sim verdicts, high-fidelity validation claims, full ideal driver
completion, or self-ID claims.

The reason is narrow and mechanical: M2698 accepted the M2697 materialization
pack, but M2697 produced 12 protected workload candidates with 0 exact M1690
workload matches. Those candidates need an adapter contract before any later
execution route can decide whether they are runnable, rejected, or blocked by
missing simulator support.

## Governing Constraints

`docs/post-m2470-route-plan.md` keeps Route A as an engineering-controller
mainline and prevents current-sim infrastructure from becoming a paper result.
M2699 applies the same separation to protected mitigation:

```text
Route A protected side:
  preserve the protected mitigation blocker as an engineering limitation and
  make the runner interface auditable.

M2697 materialization:
  12 protected runner spec rows
  12 protected workload candidate rows
  160 traceability rows
  0 unmaterialized rows
  10/10 protected targets accounted
  0 exact M1690 workload matches

M2699 design:
  define adapter contract rows only, not behavior execution.
```

The adapter contract must distinguish these concepts:

```text
protected runner spec candidate
  A materialized protected taxonomy runner specification from M2697.

protected workload candidate
  A candidate profile/checkpoint association for the runner spec.

current M1690 workload row
  An already existing executable workload row. M2697 found no exact protected
  candidate matches here.

adapter contract row
  A future materialized row that says how the protected candidate would be
  routed, rejected, or blocked by adapter constraints.
```

## Input Contract

M2700 should consume these source artifacts:

| Input | Required use |
| --- | --- |
| `runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation/summary.json` | Verify M2697 status, counts, and claim-boundary flags. |
| `protected_runner_spec_rows.csv` | Source protected fixture, surface, digest, backend, actor-boundary, and no-execution fields. |
| `protected_workload_candidate_rows.csv` | Source profile, policy checkpoint, reference config, M1690 match status, and candidate status. |
| `spec_traceability_rows.csv` | Preserve target/spec/taxonomy traceability and 10/10 target accounting. |
| `actor_contract_guard_rows.csv` | Preserve P0 observation 72, action 3, and no hidden/oracle actor input. |
| `claim_boundary_rows.csv` | Preserve blocked claims and materialization-only status. |
| `gate_matrix.csv` | Preserve M2697 gate state and source artifact consistency. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv` | Use only as the current executable schema reference; do not claim exact protected candidate matches. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json` | Use only as task-spec schema context for adapter materialization. |

M2700 must reject the materialization if M2697 status is not pass, if required
source rows are missing, or if the adapter design would require hidden/oracle
actor inputs.

## Output Contract

M2700 should write a machine-auditable contract pack:

```text
runs/m2700_engineering_controller_protected_runner_adapter_contract/summary.json
runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_input_source_rows.csv
runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_candidate_mapping_rows.csv
runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_rejection_rows.csv
runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_traceability_rows.csv
runs/m2700_engineering_controller_protected_runner_adapter_contract/actor_contract_guard_rows.csv
runs/m2700_engineering_controller_protected_runner_adapter_contract/claim_boundary_rows.csv
runs/m2700_engineering_controller_protected_runner_adapter_contract/gate_matrix.csv
docs/m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight.md
```

`adapter_input_source_rows.csv` must include one row per required source
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

`adapter_candidate_mapping_rows.csv` must include one row per M2697 protected
workload candidate with at least:

```text
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
m1690_exact_workload_match
m1690_reference_workload_id
protected_task_family
protected_source_edge
adapter_admission_status
adapter_backend_family
adapter_contract_rule
environment_rollout_scheduled
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

Allowed `adapter_admission_status` values:

```text
adapter_contract_materialized_not_execution_admitted
adapter_rejected_missing_policy_checkpoint
adapter_rejected_missing_reference_profile_config
adapter_rejected_hidden_oracle_required
adapter_rejected_actor_visible_protected_label
adapter_rejected_denominator_boundary_violation
adapter_rejected_source_artifact_missing
adapter_rejected_schema_inconsistent
```

`adapter_rejection_rows.csv` records every rejected candidate or global
materialization blocker. It must be present even when there are no rejected
candidate rows. Minimum fields:

```text
rejection_id
candidate_or_source_id
rejection_type
rejection_reason
required_follow_up
actor_visible
claim_scope
```

`adapter_traceability_rows.csv` must carry forward M2697 target/spec/taxonomy
coverage and join each adapter candidate to its M2697 runner spec and
traceability rows. It must preserve the 10/10 protected target accounting.

## Actor And Claim Boundary

The adapter contract may use protected taxonomy labels only as offline
metadata. It must not expose them to the actor. The deployed actor/action
contract remains:

```text
observation_shape: 72
action_shape: 3
action_mapping: [steer, throttle, brake]
hidden_oracle_actor_input_required: false
actor_input_contract_changed: false
target_labels_actor_visible: false
protected_labels_actor_visible: false
route_labels_actor_visible: false
verdict_labels_actor_visible: false
protected_rows_in_success_denominator: false
```

The adapter contract rows must keep all execution switches off:

```text
environment_rollout_scheduled: false
training_scheduled: false
profile_specific_tuning: false
materialization_only_no_execution: true
diagnostic_only_no_verdict: true
```

## Gate Matrix

M2700 should pass only if all of these gates pass:

| Gate | Required condition |
| --- | --- |
| source artifacts present | M2697 required artifacts and M1690 schema references exist. |
| M2697 accepted | M2697 summary and M2698 audit support materialization-only acceptance. |
| candidate coverage | All 12 M2697 protected workload candidates are mapped or explicitly rejected. |
| target coverage | All 10 protected targets remain accounted by traceability rows. |
| M1690 boundary preserved | No candidate is presented as an exact M1690 workload row unless the source row already says so. |
| actor contract preserved | Observation 72, action 3, no hidden/oracle actor input. |
| label boundary preserved | Protected labels, route labels, target labels, and verdict labels remain actor-invisible. |
| denominator boundary preserved | Protected rows remain outside ordinary success denominators. |
| no execution | No reset, step, rollout, replay, validation, training, PPO, ranking, promotion, or performance verdict. |
| claim boundary preserved | No repair-success, driver-performance, paper, current-sim, high-fidelity, full ideal driver, or self-ID claim. |
| follow-up audit registered | M2700 writes one bounded M2701 result-audit manifest. |

## Failure Taxonomy

- `contract_violation`: fire if M2700 changes actor observation/action shape,
  requires hidden/oracle inputs, or exposes protected labels to actor input.
- `lineage_invalid`: fire if adapter rows cannot trace back to M2697 runner
  specs, M2697 candidates, M2697 traceability rows, and M1690 schema
  references.
- `metric_artifact`: fire if adapter rows are interpreted as success-rate,
  validation, ranking, or performance evidence.
- `scenario_sampling_failure`: remains active if protected specs still cannot
  become executable without new simulator support.
- `behavior_regression`: remains active until a separately admitted execution
  route produces measured protected behavior evidence.
- `objective_overfit`: fire if the work loops through more static protected
  audits without producing adapter materialization, synthesis, or a stop.
- `proof_washout`: fire if zero exact M1690 matches or protected blockers are
  hidden behind aggregate rows.

## Admitted Follow-Up

M2700 should materialize the adapter contract pack. It may route only to a
result audit, taxonomy normalization, branch synthesis, or stop. It must not
route directly to protected execution without a result audit accepting the
adapter contract pack.

Next route:

```text
m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight
```

## Claim Boundary

Allowed M2699 claim:

```text
The protected runner adapter contract is admitted for materialization as a
no-execution schema and traceability boundary after M2698 accepted M2697 but
blocked direct protected execution.
```

Rejected claims:

```text
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
