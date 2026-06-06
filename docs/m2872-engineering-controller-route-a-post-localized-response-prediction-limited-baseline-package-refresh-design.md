# M2872 Engineering Controller Route A Post Localized Response-Prediction Limited Baseline Package Refresh Design

## Metadata

- status: completed
- decision: `admit_post_localized_response_prediction_limited_baseline_package_refresh_materialization_preflight`
- manifest: `experiments/manifests/m2872-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-design.json`
- design artifact: `docs/m2872-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-design.md`
- route plan: `docs/post-m2470-route-plan.md`
- parent synthesis: `docs/m2871-engineering-controller-route-a-post-localized-response-prediction-evidence-index-refresh-and-admission-synthesis.md`
- prior package synthesis: `docs/m2826-engineering-controller-route-a-post-recoverability-negative-limited-package-branch-synthesis.md`
- follow-up manifest: `experiments/manifests/m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight.json`
- next: `m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight`

## Design Purpose

M2872 designs a local Route A limited baseline package refresh after M2871
admitted package-boundary work as the next action. The refresh is needed because
the accepted M2824/M2826 local package predates two important negative evidence
updates:

```text
M2838/M2840:
  post Route C/HF3 stop fresh source-diverse diagnostic evidence is complete
  but weak: 1 diagnostic success, 2 collisions, and 13 off_track rows.

M2868/M2870:
  localized response-prediction implementation and paired deltas are complete
  but do not improve terminal outcomes: source and candidate both show
  0 success and 1 collision across 24 paired diagnostic rows.
```

The package refresh is a boundary artifact. It is not a publication artifact,
not a validation run, not a performance verdict, and not a checkpoint promotion.

## Route Constraints

`docs/post-m2470-route-plan.md` keeps Route A focused on a usable
actuator-level active-safety controller baseline. The near-term Route A
artifact families are:

```text
baseline checkpoint list
actor input/output contract
public benchmark pack
known failure taxonomy
runtime/inference-cost report
scenario-role metric report
```

The same route plan forbids hidden dynamics, oracle labels, slip or tire-force
shortcuts, TTC, reference trajectories, and precomputed success/progress signals
as actor input. M2872 therefore preserves the actor boundary:

```text
observation shape: 72
action shape: 3
hidden/oracle actor input: forbidden
package/blocker/diagnostic/route/verdict labels actor-visible: forbidden
```

## Evidence Inputs

M2873 must use existing artifacts only. It must not rerun environments, replay
rollouts, train, validate, build external source, or probe external adapters.

Required package content inputs:

```text
baseline_checkpoint_list:
  runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv

actor_input_output_contract:
  runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json

public_benchmark_pack:
  public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json

runtime_inference_cost_report:
  runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json

scenario_role_metric_report:
  runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/scenario_role_metric_report.csv

known_failure_taxonomy:
  runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json
```

Required limitation and context inputs:

```text
source_only_fresh_generalization:
  docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-synthesis.md
  runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/summary.json

target_protected_readiness:
  docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.md
  runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/summary.json
  runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/artifact_coverage_rows.csv
  runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/known_failure_boundary_rows.csv

negative_mechanism_localized_repair:
  docs/m2771-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-result-synthesis.md

prior_limited_package:
  docs/m2826-engineering-controller-route-a-post-recoverability-negative-limited-package-branch-synthesis.md
  runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/summary.json
  runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/package_artifact_inventory_rows.csv
  runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/package_provenance_map_rows.csv

route_c_hf3_blocker:
  docs/m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit.md

fresh_source_diverse_negative_diagnostics:
  docs/m2840-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-result-synthesis.md
  runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight/summary.json

localized_response_prediction_negative_diagnostics:
  docs/m2870-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-branch-synthesis.md
  runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/summary.json

admission_synthesis:
  docs/m2871-engineering-controller-route-a-post-localized-response-prediction-evidence-index-refresh-and-admission-synthesis.md
```

## Delta From M2824

M2824 remains useful as the prior package protocol. It materialized the local
package with:

```text
package content covered: 6/6
package limitations covered: 4/4
package manifest schema rows: 18
artifact inventory rows: 14
provenance map rows: 14
known blocker disclosure rows: 5
recoverability limitation rows: 7
actor/action contract rows: 11
claim-boundary rows: 27
package gate rows: 24
gate matrix pass: true
```

M2873 must not replace or hide that evidence. It must refresh the package to
add post-M2824 limitations:

```text
M2838/M2840 fresh source-diverse negative diagnostics:
  16 fixed rows, 1 diagnostic success, 2 collisions, 13 off_track rows.

M2868/M2870 localized response-prediction negative diagnostics:
  24 paired diagnostic rows, terminal outcomes unchanged,
  source and candidate both at 0 success and 1 collision.

M2836 HF3 blocker:
  selected-platform HF3 remains stopped until source, approved package route,
  dependency acquisition manifest, or alternate backend contract is supplied.

M2667/M2669 protected mitigation blocker:
  protected mitigation remains broad and outside success denominators.
```

## Package Refresh Artifact Contract

M2873 should write a new local output directory:

```text
runs/m2873_engineering_controller_route_a_post_localized_response_prediction_limited_baseline_package_refresh/
```

Required artifacts:

```text
summary.json
package_manifest_schema_rows.csv
package_artifact_inventory_rows.csv
package_provenance_map_rows.csv
latest_negative_evidence_rows.csv
known_blocker_disclosure_rows.csv
actor_action_contract_rows.csv
claim_boundary_rows.csv
package_gate_matrix.csv
```

`summary.json` must report at least:

```text
status_pass
required_artifacts_present
source_artifacts_reanalyzed_only
package_published
environment_reset_run
environment_step_run
policy_action_run
policy_rollout_run
replay_run
measured_validation_run
training_run
ppo_run
repair_run
source_build_run
adapter_probe_run
external_high_fidelity_simulation_included
ranking_run
winner_selected
checkpoint_promoted
success_rate_computed
driver_performance_claim_made
validation_readiness_claim_made
validation_result_claim_made
paper_claim_made
current_sim_verdict_claim_made
high_fidelity_validation_claim_made
full_ideal_driver_completion_claim_made
level3_self_id_claim_made
actor_contract_shape_72_action_3
hidden_oracle_actor_input_detected
package_labels_actor_visible
blocker_labels_actor_visible
diagnostic_labels_actor_visible
route_labels_actor_visible
verdict_labels_actor_visible
latest_negative_evidence_row_count
known_blocker_disclosure_row_count
actor_action_contract_row_count
claim_boundary_row_count
package_gate_row_count
gate_matrix_pass
next_blocker
```

`package_manifest_schema_rows.csv` must define the materialized row schemas. It
should extend the M2824 schema with post-M2870 refresh fields:

```text
package_id
package_protocol_version
generated_at_utc
route
refresh_reason
evidence_cutoff_milestone
artifact_id
source_milestone
source_path
source_exists
source_status_pass_or_present
artifact_role
package_required
package_inclusion_status
provenance_status
actor_visible
latest_negative_evidence_refs
known_blocker_refs
claim_scope
blocked_interpretation
```

`package_artifact_inventory_rows.csv` must include at least these artifact ids:

```text
baseline_checkpoint_list
actor_input_output_contract
public_benchmark_pack
runtime_inference_cost_report
scenario_role_metric_report
known_failure_taxonomy
source_only_fresh_generalization_panel
target_protected_readiness_index
negative_mechanism_localized_repair_synthesis
prior_limited_package_summary
prior_limited_package_inventory
prior_limited_package_provenance
fresh_source_diverse_negative_diagnostics
localized_response_prediction_negative_diagnostics
hf3_source_dependency_blocker
post_m2470_route_plan
m2871_admission_synthesis
```

`latest_negative_evidence_rows.csv` must include at least:

```text
protected_mitigation_blocker:
  M2657/M2667 broad unavoidable_mitigation protected failure.

negative_recoverability_diagnostics:
  M2816/M2824 0 recoverability-window availability,
  0 recoverability success, 1 collision, and 5 offtrack terminations.

negative_mechanism_localized_repair:
  M2771 complete but negative mechanism-localized repair synthesis.

fresh_source_diverse_negative_diagnostics:
  M2838/M2840 1 success, 2 collisions, and 13 off_track rows.

localized_response_prediction_no_terminal_improvement:
  M2868/M2870 source and candidate both 0 success and 1 collision across
  24 paired diagnostic rows.
```

`known_blocker_disclosure_rows.csv` must include at least:

```text
protected_mitigation_blocker
offtrack_collision_behavior
recoverability_gap
localized_response_prediction_no_terminal_improvement
hf3_dependency_blocker
self_id_gap
scenario_sampling_caution
package_publication_blocker
```

`actor_action_contract_rows.csv` must prove that:

```text
observation_shape == 72
action_shape == 3
actor input contract changed == false
action contract changed == false
hidden/oracle actor input detected == false
package labels actor-visible == false
blocker labels actor-visible == false
diagnostic labels actor-visible == false
route labels actor-visible == false
verdict labels actor-visible == false
```

`claim_boundary_rows.csv` must reject every forbidden interpretation listed in
this design. The package may claim only local artifact completeness, provenance,
limitation visibility, actor/action boundary preservation, and follow-up audit
handoff.

`package_gate_matrix.csv` must include pass/fail rows for:

```text
required_artifacts_present
schema_rows_written
artifact_inventory_written
provenance_rows_written
latest_negative_evidence_rows_written
known_blocker_rows_written
actor_contract_rows_written
claim_boundary_rows_written
M2824 prior package traced
M2838/M2840 negative diagnostics included
M2868/M2870 no-terminal-improvement included
M2836 HF3 blocker preserved
M2667/M2669 protected blocker preserved
actor_72_action_3_preserved
no_hidden_oracle_actor_input
labels_actor_invisible
package_not_published
no_execution_or_training
no_validation_or_ranking
no_success_rate_verdict
no_performance_or_paper_claim
follow_up_audit_manifest_registered
```

## Claim Boundary

Supported M2872 claim:

```text
M2872 designs a local Route A limited baseline package refresh that can
materialize current package rows with post-M2870 negative evidence and explicit
claim boundaries.
```

Rejected claims:

```text
package publication
deployment readiness
repair success
recoverability success
localized response-prediction success
driver performance
validation readiness
validation result
controller ranking
source-family ranking
task-family ranking
scenario-role ranking
stress-axis ranking
profile ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness
high-fidelity validation result
full ideal driver completion
level3 self-identification
```

## Gate Decision

M2872 admits exactly one next action:

```text
m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight
```

M2873 should materialize the local package refresh from existing artifacts and
register a result audit. M2873 must not publish the package and must not run
reset, step, rollout, replay, validation, training, PPO, repair, source build,
adapter probe, external simulation, ranking, winner selection, promotion, or
success-rate verdict computation.

## Success Criteria For M2873

M2873 succeeds only if:

```text
all required package refresh artifacts exist
M2824/M2826 prior package evidence is traced
M2667/M2669 protected blocker remains visible
M2836 HF3 blocker remains visible
M2838/M2840 fresh source-diverse negative diagnostics remain visible
M2868/M2870 localized response-prediction no-terminal-improvement remains visible
actor 72/action 3 and no hidden/oracle actor input are preserved
all labels remain actor-invisible
claim-boundary rows reject publication, validation, ranking, promotion,
  performance, paper, current-sim, high-fidelity, full-driver, and self-ID claims
one bounded result-audit manifest is registered
```

M2873 fails if it hides any negative evidence or blocker, claims performance or
validation, changes actor/action contract, publishes a package, or executes any
environment/training/validation path.
