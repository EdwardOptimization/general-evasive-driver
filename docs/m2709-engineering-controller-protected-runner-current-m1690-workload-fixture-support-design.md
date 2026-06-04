# M2709 Engineering Controller Protected Runner Current-M1690 Workload Fixture Support Design

## Metadata

- status: completed
- decision: `admit_current_m1690_workload_fixture_support_materialization_preflight`
- manifest: `experiments/manifests/m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design.json`
- design artifact: `docs/m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design.md`
- parent synthesis: `docs/m2708-engineering-controller-protected-runner-simulator-workload-support-branch-synthesis.md`
- parent support summary: `runs/m2706_engineering_controller_protected_runner_simulator_workload_support/summary.json`
- current workload reference: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv`
- follow-up manifest: `experiments/manifests/m2710-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-preflight.json`
- next: `m2710-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-preflight`

## Design Decision

M2709 admits one bounded no-execution current-M1690 workload fixture support
materialization preflight. It does not admit protected execution, reset, step,
rollout, replay, measured validation, training, PPO, ranking, winner
selection, promotion, success-rate verdicts, repair-success claims,
driver-performance claims, paper claims, current-sim verdicts, high-fidelity
validation claims, full ideal driver completion, or self-ID claims.

The purpose is narrow:

```text
M2706 support row:
  a protected candidate requires a new workload row and simulator fixture
  not support-ready
  not exact M1690
  not execution-admitted

M2710 workload/fixture support row:
  a no-execution proposal or rejection that says what exact current-runner
  workload row and simulator fixture support would be needed
  may mark a candidate materialization-ready for later audit
  may reject or block a candidate with explicit row-level reason
  must not become a protected execution row

Future protected execution row:
  separately pre-registered behavior route only after M2710 materialization
  and result audit accept exact workload/fixture support and execution
  admission boundaries
```

M2709 therefore routes to M2710 materialization. M2710 may transform M2706
support-required rows into workload fixture support source rows, fixture
proposal rows, exact-match admission or rejection rows, support-candidate
mapping rows, traceability rows, actor-contract guard rows, claim-boundary
rows, and gate rows. It must not schedule or run environment execution.

## Source Facts

M2708 selected this route because the branch has one precise protected support
blocker:

```text
support candidates: 12
support blockers: 12
support traceability rows: 160
support_materialized_candidate_requires_new_workload_row: 12
support_ready_existing_m1690_workload: 0
exact M1690 workload matches: 0
execution-admitted source rows: 0
protected targets accounted: 10/10
```

M2706 support candidate rows carry the fields M2710 must preserve:

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
m1690_reference_workload_id
support_status
support_blocker_status
candidate_requires_new_workload_row
candidate_requires_simulator_fixture
```

The current M1690 workload matrix has 864 existing rows with schema:

```text
workload_id
task_source_id
profile_name
task_family
source_edge
window_tag
executable_source_family
env_template_family
strata
profile_config_path
checkpoint_path
config_exists
checkpoint_exists
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
```

The protected runner specs from M2697 provide the protected fixture fields that
M2710 must preserve as offline metadata:

```text
runner_spec_id
source_panel_spec_id
protected_task_family
protected_source_edge
role_family
role_class
seed
dynamics_axis_id
dynamics_axis_family
base_fixture_id
fixture_id
surface_id
env_template_family
runner_backend_family
actor_observation_shape
action_shape
hidden_oracle_actor_input_required
target_labels_actor_visible
protected_rows_in_success_denominator
```

M2700 adapter mapping rows and M2703 execution-admission candidate rows remain
part of the required source chain. M2710 may use M2706 support rows as the
immediate parent, but it must still preserve the adapter and execution
admission ids rather than collapsing those boundaries into a single support
summary.

M2710 must not fabricate existing M1690 matches. It may propose protected
current-M1690-compatible rows only as new materialized support rows, and those
rows must remain no-execution until a later audit and execution-admission
route accepts them.

## Row Concepts

M2710 must distinguish these concepts:

| Concept | Meaning |
| --- | --- |
| M2706 support candidate row | Existing no-execution row saying a protected candidate needs a new workload row and simulator fixture. |
| current M1690 workload reference row | Existing workload matrix row used only for schema and profile/config/checkpoint references. |
| protected workload fixture proposal row | New no-execution row describing a protected workload/fixture candidate that could later be materialized into a current-runner workload row. |
| exact-match admission row | No-execution row stating whether a proposal has an existing exact M1690 row, a new proposed exact row, or is rejected/blocked. |
| simulator fixture support row | No-execution row describing the simulator fixture, backend family, fixture digest inputs, and actor/claim boundary needed by the proposal. |
| actual protected execution row | A future separately audited behavior row. No M2709 or M2710 row may become this row. |

Allowed admission statuses for M2710:

```text
workload_fixture_support_proposed_new_current_m1690_row
workload_fixture_support_ready_existing_current_m1690_row
workload_fixture_support_rejected_schema_inconsistent
workload_fixture_support_rejected_missing_policy_checkpoint
workload_fixture_support_rejected_missing_reference_profile_config
workload_fixture_support_rejected_hidden_oracle_required
workload_fixture_support_rejected_actor_visible_protected_label
workload_fixture_support_rejected_denominator_boundary_violation
workload_fixture_support_rejected_actor_contract_changed
workload_fixture_support_blocked_source_artifact_missing
```

For the current source state, the expected conservative status is:

```text
workload_fixture_support_proposed_new_current_m1690_row: 12
workload_fixture_support_ready_existing_current_m1690_row: 0
execution-admitted rows: 0
environment reset scheduled: false
environment rollout scheduled: false
measured validation scheduled: false
training scheduled: false
```

M2710 may produce a `ready_existing_current_m1690_row` only if it cites exact
source evidence from the existing M1690 workload matrix. The current audited
state says that count should remain 0.

## Input Contract

M2710 should consume these artifacts:

| Input | Required use |
| --- | --- |
| `docs/m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design.md` | Verify the design boundary and admitted follow-up route. |
| `docs/m2708-engineering-controller-protected-runner-simulator-workload-support-branch-synthesis.md` | Verify synthesis selected only a bounded workload/fixture design route. |
| `docs/m2707-engineering-controller-protected-runner-simulator-workload-support-materialization-result-audit.md` | Verify M2707 accepted M2706 only as claim-safe support evidence and rejected direct execution. |
| `runs/m2706_engineering_controller_protected_runner_simulator_workload_support/summary.json` | Verify status, gate pass, counts, no-execution flags, 0 support-ready rows, 0 exact matches, 0 admitted rows, and actor/claim boundaries. |
| `support_candidate_rows.csv` | Create one workload/fixture proposal row per support-required candidate. |
| `support_blocker_rows.csv` | Preserve row-level blocker reasons and required follow-up text. |
| `support_traceability_rows.csv` | Preserve 160 traceability rows and 10/10 protected target accounting. |
| `actor_contract_guard_rows.csv` | Preserve P0 observation 72, action 3, and no hidden/oracle actor input. |
| `claim_boundary_rows.csv` | Preserve blocked claims and no-execution status. |
| `gate_matrix.csv` | Preserve M2706 gate state before fixture-support materialization. |
| `runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation/protected_runner_spec_rows.csv` | Preserve protected fixture, backend, digest, and actor-boundary metadata. |
| `runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation/protected_workload_candidate_rows.csv` | Preserve policy checkpoint, reference config, profile, and M1690 reference metadata. |
| `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_candidate_mapping_rows.csv` | Preserve adapter candidate mapping and adapter-not-execution boundary for every support candidate. |
| `runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_candidate_rows.csv` | Preserve execution-admission candidate status and 0 execution-admitted source boundary. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json` | Use only as executable task-spec schema reference. |
| `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv` | Use only as current workload schema and exact-match reference; do not fabricate matches. |
| `docs/post-m2470-route-plan.md` | Preserve Route A/B/C claim separation and static-artifact stop condition. |

M2710 must fail closed if required source artifacts are missing, if M2706
`status_pass` or `gate_matrix_pass` is false, if M2708 did not route to M2709,
if any proposal requires hidden/oracle actor input, if protected labels would
be actor-visible, if protected rows would enter ordinary success denominators,
or if an exact M1690 match is asserted without source evidence.

## Output Contract

M2710 should write this machine-auditable pack:

```text
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/summary.json
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/workload_fixture_input_source_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/protected_workload_fixture_proposal_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/exact_match_admission_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/workload_fixture_support_blocker_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/workload_fixture_traceability_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/actor_contract_guard_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/claim_boundary_rows.csv
runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support/gate_matrix.csv
docs/m2710-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-preflight.md
```

`workload_fixture_input_source_rows.csv` must include one row per required
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

`protected_workload_fixture_proposal_rows.csv` must include one row per M2706
support candidate with at least:

```text
workload_fixture_proposal_id
support_candidate_id
execution_admission_candidate_id
adapter_candidate_id
workload_candidate_id
runner_spec_id
source_panel_spec_id
proposed_workload_id
proposed_task_source_id
profile_name
policy_subject_id
policy_checkpoint_path
policy_checkpoint_exists
reference_profile_config_path
reference_profile_config_exists
protected_task_family
protected_source_edge
proposed_task_family
proposed_source_edge
proposed_executable_source_family
proposed_env_template_family
proposed_window_tag
proposed_strata
fixture_id
runner_backend_family
fixture_support_status
exact_existing_m1690_match
new_current_m1690_row_required
simulator_fixture_required
environment_reset_scheduled
environment_rollout_scheduled
measured_validation_scheduled
training_scheduled
profile_specific_tuning
actor_input_contract_changed
hidden_oracle_actor_input_required
target_labels_actor_visible
protected_labels_actor_visible
protected_rows_in_success_denominator
materialization_only_no_execution
diagnostic_only_no_verdict
claim_scope
```

`exact_match_admission_rows.csv` must include:

```text
admission_id
workload_fixture_proposal_id
support_candidate_id
existing_m1690_workload_id
proposed_workload_id
exact_match_status
admission_status
admission_reason
required_follow_up
execution_admitted
environment_reset_admitted
actor_visible
claim_scope
```

`workload_fixture_support_blocker_rows.csv` must include one row for every
rejected or still-blocked proposal and must be present even if no blockers are
found:

```text
blocker_id
workload_fixture_proposal_id
support_candidate_id
blocker_type
blocker_reason
required_follow_up
actor_visible
claim_scope
```

`workload_fixture_traceability_rows.csv` must preserve M2706 target coverage
and join each proposal to support, execution-admission, adapter, runner-spec,
protected target, source key, and traceability axis:

```text
workload_fixture_traceability_id
support_traceability_id
support_candidate_id
execution_admission_candidate_id
adapter_candidate_id
workload_candidate_id
runner_spec_id
source_panel_spec_id
workload_fixture_proposal_id
protected_target_id
target_family
source_key
traceability_axis
target_accounted
workload_fixture_traceability_status
protected_rows_in_success_denominator
target_labels_actor_visible
protected_labels_actor_visible
hidden_oracle_actor_input_required
actor_input_contract_changed
materialization_only_no_execution
diagnostic_only_no_verdict
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

`claim_boundary_rows.csv` must block execution, validation, training, ranking,
promotion, success-rate verdict, repair-success, driver-performance,
paper-level, current-sim, high-fidelity, full ideal driver, and self-ID
claims.

## Gate Contract

M2710 should write a `gate_matrix.csv` containing at least these gates:

```text
source_artifacts_present
m2709_design_present
m2708_synthesis_route_present
m2707_support_audit_acceptance_present
m2706_status_pass
m2706_gate_matrix_pass
workload_fixture_input_source_rows_cover_required_sources
adapter_mapping_source_consumed
execution_admission_source_consumed
proposal_rows_cover_support_candidates
exact_match_admission_rows_cover_proposals
no_fabricated_existing_m1690_matches
current_m1690_schema_consumed
new_workload_row_requirements_materialized
simulator_fixture_requirements_materialized
support_required_rows_preserved_or_reclassified_with_evidence
protected_targets_accounted
traceability_rows_preserve_m2706_coverage
actor_contract_preserved
protected_labels_actor_invisible
no_hidden_oracle_actor_input
protected_not_success_denominator
materialization_only_no_execution
claim_boundary_blocks_overclaim
follow_up_audit_registered
required_artifacts_present
```

The materialization pack may pass only if all 12 M2706 support candidates have
proposal rows, all proposals have exact-match admission rows, every claimed
existing M1690 match is backed by source evidence, all new-row proposals remain
no-execution, 10/10 protected targets remain accounted, and all actor/claim
boundary gates pass.

## Follow-Up Route

Decision:

```text
admit_current_m1690_workload_fixture_support_materialization_preflight
```

The next route is:

```text
m2710-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-preflight
```

M2710 is the only admitted next action. It may materialize workload/fixture
support rows and an audit-follow-up manifest. It must not execute environments
or reinterpret workload fixture support rows as protected execution evidence.
If M2710 cannot represent the rows without fabricating exact M1690 matches or
violating actor/claim boundaries, it must preserve explicit blockers and route
to taxonomy normalization, branch synthesis, or stop.

## Claim Boundary

Allowed M2709 claim:

```text
M2709 designs a no-execution current-M1690 workload fixture support
materialization route for M2706 support-required protected runner rows while
preserving actor/action and claim boundaries.
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
