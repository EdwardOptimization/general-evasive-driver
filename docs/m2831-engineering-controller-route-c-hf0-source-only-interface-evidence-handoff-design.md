# M2831 Engineering Controller Route C HF0 Source-Only Interface Evidence Handoff Design

## Metadata

- status: completed
- decision: `admit_route_c_hf0_source_only_interface_evidence_handoff_materialization_preflight`
- manifest: `experiments/manifests/m2831-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-design.json`
- design artifact: `docs/m2831-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-design.md`
- parent synthesis: `docs/m2830-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-branch-synthesis.md`
- route plan: `docs/post-m2470-route-plan.md`
- HF3 blocker: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- follow-up manifest: `experiments/manifests/m2832-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-materialization-preflight.json`
- next: `m2832-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-materialization-preflight`

## Design Premise

M2830 closed the Route A post-package source-diverse diagnostic branch. That
branch is complete and claim-safe, but it remains mixed diagnostic evidence:

```text
M2828 fixed candidates: 16
M2828 resolved candidates: 16
M2828 execution rows: 16
M2828 execution failure rows: 0
M2828 diagnostic success: 5
M2828 diagnostic collision: 1
M2828 diagnostic off_track: 10
```

Repeating another M2828-like Route A execution would be local search unless it
changes evidence axis. M2831 therefore follows the M2830 pivot to Route C/HF0
source-only interface evidence handoff.

The selected-platform HF3 path is still not available:

```text
M2638 selected platform family: chrono_vehicle_or_equivalent_open_backend
configured source root: /home/quyaonan/workspace/chrono
source root available: false
cmake lists available: false
pychrono/projectchrono package import unavailable: true
availability blocker: dependency_source_unavailable
```

M2831 must not weaken that blocker. The useful next move is not external HF3
execution; it is a bounded materialization of the repo-local HF0/source-only
interface evidence that already exists, with M2638 and M2828 boundaries kept
visible.

## Evidence To Preserve

M2832 must preserve these evidence families as handoff input:

```text
Route C/HF0 contract route:
  M2475 external-backend route design
  actor observation shape 72
  action shape 3
  ActorView-only P0 extraction
  hidden/oracle diagnostics outside actor input

HF0 fixture and source-only adapter route:
  M2482 fixture catalog
  10 catalog rows
  3 source-only fixtures admitted for materialization
  actor metadata leak flags all false
  M2484 source-only fixture smoke
  3 reset rows
  6 canned step rows
  observation shape 72 and action shape 3 preserved

Source-only role differentiation route:
  M2494 identified the metadata-only role metric blocker
  M2495-M2497 materialized and audited reset-only differentiated role fixtures
  M2498-M2499 accepted parameterized source-only role telemetry
  M2498 role reset observation digest count: 3
  M2498 role reset observation digests differentiated: true
  M2498 telemetry rows: 300
  M2498 role metric panel rows: 3

Source-only diagnostic pack route:
  M2501 source-only baseline comparison panel
  3 subjects
  3 roles
  900 telemetry rows
  9 panel rows
  M2505 public source-only diagnostic pack
  M2508 runtime/inference-cost report
  M2548 HF0 P0 parity and actor runtime materialization

HF3/source dependency boundary:
  M2593 repo-local source-only adapter blocker closure
  M2638 selected-platform source dependency blocker

Route A diagnostic context:
  M2828 mixed post-package source-diverse diagnostic outcomes
  M2829 result audit and claim boundary
  M2830 branch synthesis and pivot decision
```

M2832 must not treat these as validation evidence. It should materialize a
machine-auditable handoff panel that says what is ready, what is diagnostic
only, which blockers remain active, and which claims are still forbidden.

## Handoff Boundary

The actor contract is non-negotiable:

```text
actor observation shape: 72
action shape: 3
actor-visible extractor: ActorView only
allowed actor-visible inputs:
  ego kinematics / IMU-like response
  steering throttle brake actuator state
  previous physical commands
  ego-frame road/free-space geometry
  ego-frame obstacle geometry and relative motion
  recurrent/history state
```

Forbidden actor-visible fields remain:

```text
mu
mass
tire stiffness
brake scale
actuator tau
slip
tire force
oracle feasibility
AEB/AES/drift labels
controller mode
speed_ref
beta_target
path error
heading error
path curvature
TTC
required clearance
oracle stopping distance
reward terms
collision labels
success labels
progress labels
route labels
validation labels
selected platform state
build outcome
probe outcome
reset outcome
high-fidelity verdict
```

Source-only physical scenario differences are allowed only through ordinary
deployable observations: different ego response, road geometry, obstacle slots,
and actuator state. Hidden diagnostic values may be recorded in artifact rows,
but they must remain actor-invisible.

## M2832 Materialization Schema

M2832 should materialize a run directory:

```text
runs/m2832_engineering_controller_route_c_hf0_source_only_interface_evidence_handoff_materialization/
```

Required artifacts:

```text
summary.json
handoff_artifact_inventory_rows.csv
source_only_interface_handoff_rows.csv
actor_contract_guard_rows.csv
blocker_boundary_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
experiments/manifests/m2833-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-result-audit.json
```

`handoff_artifact_inventory_rows.csv` should include:

```text
handoff_artifact_id
source_milestone
artifact_path
artifact_family
required_for_handoff
exists
status_pass_field
claim_scope
external_hf3_execution_evidence
validation_evidence
driver_performance_evidence
self_id_evidence
notes
```

Minimum inventory families:

```text
hf0_contract_route
fixture_catalog
fixture_smoke
source_only_role_parameterization
source_only_role_metric_panel
source_only_baseline_comparison
public_diagnostic_pack
runtime_inference_cost
hf0_parity_runtime
source_only_adapter_closure
selected_platform_source_dependency_blocker
route_a_post_package_diagnostic_context
```

`source_only_interface_handoff_rows.csv` should include:

```text
row_id
evidence_family
backend_or_surface
status
row_count
actor_observation_shape
action_shape
actor_visible_source
labels_actor_visible
hidden_values_actor_visible
diagnostics_actor_visible
external_hf3_required
allowed_next_use
forbidden_interpretation
source_artifact
```

Required source-only rows:

```text
m2482_fixture_catalog:
  catalog rows 10
  source-only admitted fixtures 3

m2484_fixture_smoke:
  fixture count 3
  reset count 3
  step count 6
  canned actions only true

m2498_parameterized_role_panel:
  telemetry rows 300
  role rows 3
  unique reset digests 3
  parameterized fixtures true

m2501_baseline_comparison:
  subjects 3
  roles 3
  telemetry rows 900
  panel rows 9

m2505_public_pack:
  public diagnostic pack present

m2508_runtime_report:
  actor-only forward rows 300

m2548_hf0_parity_runtime:
  HF0 P0 parity checks 5
  action mapping checks 7
  actor inference cost rows 270
```

`actor_contract_guard_rows.csv` should include:

```text
guard_id
contract_item
expected
observed
pass
actor_visible
source_artifact
failure_if_false
```

Required actor guard rows:

```text
observation_shape_72
action_shape_3
ActorView_only_extraction
no_hidden_oracle_actor_input
no_fixture_labels_actor_visible
no_scenario_labels_actor_visible
no_feasibility_classes_actor_visible
no_diagnostics_actor_visible
no_reward_terms_actor_visible
no_success_progress_verdict_labels_actor_visible
physical_scenario_differences_only_through_deployable_observations
```

`blocker_boundary_rows.csv` should include:

```text
blocker_id
source_milestone
blocker_family
status
evidence
resume_condition
ordinary_success_denominator_allowed
execution_allowed_in_m2832
notes
```

Required blocker rows:

```text
m2638_selected_platform_source_dependency:
  status: active
  execution_allowed_in_m2832: false
  resume only with valid local source root approved package route or admitted
  dependency acquisition manifest

m2828_post_package_mixed_diagnostic_outcomes:
  status: active diagnostic context
  5 success 1 collision 10 off_track
  not validation or driver-performance evidence

m2494_metadata_only_role_blocker:
  status: resolved for parameterized source-only role panel path by M2495-M2499
  not high-fidelity validation evidence
```

`claim_boundary_rows.csv` should include boolean rows for all rejected claims:

```text
repair_success
recoverability_success
validation_readiness
validation_result
driver_performance
controller_family_ranking
source_family_ranking
scenario_role_ranking
winner_selection
checkpoint_promotion
success_rate_verdict
package_publication
paper_evidence
finite_window_vs_gru_conclusion
current_response_sufficiency
current_sim_verdict
high_fidelity_validation_readiness
high_fidelity_validation_result
full_ideal_driver_completion
level3_self_identification
```

Every row must be `claim_made=false` and `claim_allowed=false`.

`gate_matrix.csv` should include:

```text
required_artifacts_present
m2475_boundary_present
m2482_fixture_catalog_present
m2484_fixture_smoke_present
m2498_parameterized_role_panel_present
m2505_public_pack_present
m2508_runtime_report_present
m2548_hf0_parity_runtime_present
m2593_source_only_adapter_closure_present
m2638_selected_platform_blocker_present
m2828_mixed_outcomes_preserved
actor_observation_shape_72_preserved
action_shape_3_preserved
labels_actor_invisible
diagnostics_actor_invisible
external_hf3_execution_forbidden
reset_step_rollout_validation_forbidden
ranking_promotion_success_verdict_forbidden
driver_performance_paper_high_fidelity_self_id_claims_forbidden
follow_up_manifest_registered
```

## M2832 Execution Policy

M2832 is materialization only. It may read existing docs, summaries, and CSVs.
It may write only the M2832 run directory and the M2833 follow-up manifest. It
must not:

```text
install dependencies
fetch external source
import external high-fidelity packages
mutate source or dependency trees
run source build
run adapter probe
start a backend
reset an environment
step an environment
execute policy action
roll out
replay
validate
train
run PPO
rank controllers or source families
select a winner
promote a checkpoint
publish a package
compute success-rate verdicts
claim performance paper current-sim high-fidelity full-driver or self-ID
```

M2832 may compute only artifact-presence, row-count, digest-presence, boolean
claim-boundary, and gate-matrix checks from existing files.

## Success Criteria

M2831 passes if:

```text
this design artifact exists
M2832 materialization schema is explicit
M2832 preserves M2475-M2509 M2548 M2593 M2638 and M2827-M2830 evidence families
actor 72/action 3 and ActorView-only extraction remain preserved
M2638 selected-platform blocker remains active
M2828 mixed diagnostic outcomes remain visible
one bounded M2832 materialization preflight manifest is registered
no external HF3 execution validation ranking performance paper full-driver or
self-ID claim is admitted
```

## Rejected Claims

M2831 rejects:

```text
driver performance
validation readiness
validation result
high-fidelity validation readiness
high-fidelity validation result
current-sim verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
controller-family ranking
source-family ranking
scenario-role ranking
winner selection
checkpoint promotion
package publication
repair success
recoverability success
full ideal driver completion
level3 self-identification
```

M2831 does not execute reset, step, policy action, rollout, replay, validation,
training, PPO, source build, adapter probe, external simulation, ranking,
winner selection, promotion, package publication, or verdict computation.

## Next

Route to:

```text
m2832-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-materialization-preflight
```

M2832 should materialize the handoff rows defined above and register M2833
result audit. It must remain artifact-only and source-only; it must not reopen
HF3 selected-platform execution while M2638 remains blocked.
