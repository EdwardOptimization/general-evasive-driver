# M2823 Engineering Controller Route A Post-Recoverability Negative Limited Package Design

## Metadata

- status: completed
- decision: `admit_post_recoverability_negative_limited_package_materialization_preflight`
- manifest: `experiments/manifests/m2823-engineering-controller-route-a-post-recoverability-negative-limited-package-design.json`
- design artifact: `docs/m2823-engineering-controller-route-a-post-recoverability-negative-limited-package-design.md`
- parent synthesis: `docs/m2822-engineering-controller-route-a-post-recoverability-negative-readiness-index-result-synthesis.md`
- parent readiness audit: `docs/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.md`
- parent readiness summary: `runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/summary.json`
- prior package protocol: `docs/m2687-engineering-controller-route-a-package-with-limitations-protocol-design.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2824-engineering-controller-route-a-post-recoverability-negative-limited-package-materialization-preflight.json`
- next: `m2824-engineering-controller-route-a-post-recoverability-negative-limited-package-materialization-preflight`

## Admission Decision

M2823 admits one bounded Route A limited-package materialization preflight.

The materialization is a package-boundary refresh after the negative
recoverability branch. It may reuse the table families from the earlier M2687
and M2688 package-with-limitations protocol, but it must update the package
context with the M2804/M2805 post-clearance readiness blockers, M2816/M2817
negative recoverability diagnostics, M2820/M2821 post-recoverability readiness
index, and M2822 synthesis decision.

M2823 does not admit package publication, reset, rollout, replay, validation,
training, PPO, repair, source build, adapter probe, high-fidelity execution,
controller ranking, winner selection, checkpoint promotion, success-rate
verdicts, driver-performance claims, paper claims, finite-window-vs-GRU claims,
current-sim verdicts, full-driver claims, or level3 self-ID claims.

The admitted follow-up is:

```text
m2824-engineering-controller-route-a-post-recoverability-negative-limited-package-materialization-preflight
```

## Governing Constraints

`docs/post-m2470-route-plan.md` splits the project into:

```text
Route A:
  Engineering controller mainline and bounded actuator-level package artifacts.

Route B:
  Paper evidence, controller-family comparison, finite-window/GRU comparison,
  and self-ID claims.

Route C:
  High-fidelity interface and validation, currently blocked at selected-platform
  HF3 source availability by M2638.
```

The M2824 package must keep that split intact. Route A package rows may state
that existing artifacts are organized and bounded. They may not state that the
controller is validated, professional, driver-like, high-fidelity ready,
paper-ready, or self-identifying.

M2822 also closes the same recoverability local-search path. Therefore M2824
must not repair, tune, rank, or compute verdicts over the same 12
recoverability-window rows. The negative result is package limitation evidence,
not a new optimization target.

## Package Scope

M2824 should materialize a local package protocol pack with these required
artifact groups:

| Package artifact | Source | Required use |
| --- | --- | --- |
| baseline checkpoint list | `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv` | Lists admitted Route A checkpoint lineages without promotion or winner selection. |
| actor input/output contract | `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json` and `.md` | Freezes P0 observation shape `72`, action shape `3`, and deployed `[steer, throttle, brake]`. |
| public benchmark pack | `public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json` | Provides source-only diagnostic context, not validation readiness. |
| runtime/inference-cost report | `runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json` | Records actor forward cost only; action outputs are not interpreted as control outcomes. |
| scenario-role metric report plan | `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/scenario_role_metric_report_plan.csv` | Records which scenario roles are diagnostic, planned, or missing without ranking roles. |
| known failure taxonomy | `runs/m2510_engineering_controller_known_failure_taxonomy/summary.json` plus later readiness blocker rows | Keeps known limitations visible as blockers. |
| post-clearance readiness blockers | `runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/summary.json` | Preserves negative clearance and stable_avoidable retention risk. |
| negative recoverability diagnostics | `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/summary.json` plus M2817/M2818 | Preserves 7 post-event traces, 0 recoverability-window availability, 0 recoverability success, 1 collision, and 5 offtrack terminations. |
| post-recoverability readiness index | `runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/summary.json` plus M2821/M2822 | Integrates 19 evidence rows, 12 deliverable rows, 8 blockers, 7 next-action rows, 31 claim rows, and 42 passing gates. |
| HF3 source dependency blocker | `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md` | Keeps selected-platform high-fidelity execution paused until source dependency evidence is supplied. |

The package may include M2688 package protocol artifacts as prior context, but
the M2824 pack is the post-recoverability refresh. It must not treat the prior
M2688 pack as sufficient after M2816/M2820 added new blockers.

## Required Materialization Tables

M2824 should write these rows under:

```text
runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/
```

Required files:

```text
summary.json
package_manifest_schema_rows.csv
package_artifact_inventory_rows.csv
package_provenance_map_rows.csv
known_blocker_disclosure_rows.csv
recoverability_limitations_rows.csv
actor_action_contract_rows.csv
claim_boundary_rows.csv
package_gate_matrix.csv
```

`package_manifest_schema_rows.csv` should keep the M2688 schema family and add
post-recoverability blocker references:

```text
package_id
package_protocol_version
generated_at_utc
route
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
claim_scope
blocked_interpretation
known_blocker_refs
post_recoverability_refs
```

`package_artifact_inventory_rows.csv` should distinguish:

```text
package_content:
  baseline checkpoint list
  actor/action contract
  source-only public diagnostic pack
  runtime/inference-cost report
  scenario-role metric report plan
  known failure taxonomy

package_limitations:
  post-clearance readiness blockers
  negative recoverability diagnostics
  post-recoverability readiness index
  HF3 source dependency blocker

context_only:
  post-M2470 route plan
  prior M2688 package protocol pack
  Route B paper/self-ID route documents
```

`package_provenance_map_rows.csv` must connect each row to accepted upstream
milestones. Missing supporting context may be recorded as a blocker, but missing
required package content should fail materialization rather than silently
dropping the row.

## Known Blocker Disclosure Rules

M2824 must include at least these blocker rows:

| Blocker | Required disclosure |
| --- | --- |
| post-clearance blocker | M2804/M2805 preserve negative clearance and stable_avoidable retention risk; no validation or driver-performance claim is admitted. |
| negative recoverability blocker | M2816/M2817/M2818/M2820/M2821 preserve 0 recoverability-window availability, 0 recoverability success, 1 collision, and 5 offtrack terminations. |
| same recoverability local-search blocker | M2822 rejects another repair/ranking loop over the same recoverability rows. |
| HF3 source dependency blocker | M2638 pauses selected-platform high-fidelity execution until a local source root, package route, or dependency acquisition manifest exists. |
| Route B paper/self-ID blocker | Route A package rows do not test history necessity, finite-window-vs-GRU, current-response sufficiency, current-sim verdict, full-driver completion, or level3 self-identification. |

Every blocker row must include:

```text
blocker_id
source_milestone
evidence_path
blocker_status
package_disclosure_required
blocked_claims
resume_condition
actor_visible
claim_scope
```

Blocker rows are evaluator/package metadata only. They are not actor-visible.

## Recoverability Limitation Rows

M2824 must add a dedicated recoverability limitation table so the negative
branch cannot be washed out by general package coverage.

Minimum fields:

```text
limitation_id
source_milestone
evidence_path
observed_value
blocked_interpretation
package_disclosure_required
actor_visible
resume_condition
claim_scope
```

Minimum rows:

```text
post_event_available_rows: 7
recoverability_window_available_rows: 0
recoverability_success_rows: 0
diagnostic_collision_outcomes: 1
diagnostic_offtrack_terminations: 5
fixed_recoverability_rows_are_validation_benchmark: false
same_recoverability_repair_or_ranking_admitted: false
```

Those rows must block repair-success, validation-readiness,
driver-performance, current-sim, high-fidelity, full-driver, and self-ID
interpretations.

## Actor And Action Contract

M2824 must preserve the P0 actor contract:

```text
observation_shape: 72
action_shape: 3
deployed_action_mapping: [steer, throttle, brake]
actor_encoder: human_view_online_gru
action_sequence_horizon: 1
hidden_oracle_actor_input_detected: false
package_labels_actor_visible: false
blocker_labels_actor_visible: false
recoverability_labels_actor_visible: false
route_labels_actor_visible: false
verdict_labels_actor_visible: false
```

Allowed actor-visible signals remain deployable:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent/history state
```

Forbidden actor-visible signals remain hidden dynamics, labels, shortcuts, and
verdict answers, including `mu`, mass, tire stiffness, brake scale, actuator
tau, slip, tire force, feasibility labels, AEB/AES/drift labels, controller
mode, speed references, path error, heading error, path curvature, TTC,
required clearance, oracle stopping distance, reward terms, collision/success
labels, package status, blocker labels, recoverability labels, validation
outcomes, or precomputed answers.

## Claim Boundary Rows

Allowed M2824 claims:

```text
Route A limited package protocol artifacts were materialized from existing
accepted package, readiness, blocker, actor-contract, runtime, and diagnostic
artifacts.

The materialized package preserves post-clearance and post-recoverability
limitations, actor/action contract boundaries, HF3 source dependency blocker,
and Route B self-ID separation.

The package is a local machine-auditable package-boundary artifact, not a
public release, validation certificate, deployment claim, or driver-performance
result.
```

Blocked M2824 claims:

```text
published package
deployment readiness
driver performance
repair success
recoverability success
validation readiness
validation result
high-fidelity validation readiness or result
source-build readiness or result
adapter-probe readiness or result
backend availability
reset feasibility
rollout feasibility
controller-family ranking
scenario-role ranking
source-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
full ideal driver completion
level3 self-identification
```

## Materialization Gates

M2824 must pass only if every gate passes:

```text
required_package_artifacts_present
package_manifest_schema_complete
artifact_inventory_complete
provenance_map_complete
known_blocker_disclosures_complete
recoverability_limitations_complete
actor_action_contract_preserved
post_clearance_blocker_visible
negative_recoverability_blocker_visible
same_recoverability_local_search_blocked
hf3_source_dependency_blocker_visible
route_b_paper_self_id_blocker_visible
claim_boundary_rows_complete
no_package_publication_performed
no_execution_performed
no_training_or_ppo_performed
no_repair_performed
no_ranking_or_promotion_performed
no_validation_or_driver_performance_claim
no_paper_current_sim_high_fidelity_full_driver_or_self_id_claim
follow_up_route_registered
```

If any required source artifact is missing, M2824 should produce an explicit
artifact-inventory blocker and fail the materialization gate. It must not
produce partial package acceptance.

## Admitted Follow-Up

M2824 may materialize the local package protocol refresh and route to one of:

```text
result audit
artifact repair
claim-boundary repair
branch synthesis
explicit stop
```

The default expected follow-up is a result audit:

```text
m2825-engineering-controller-route-a-post-recoverability-negative-limited-package-materialization-result-audit
```

M2824 must pre-register that audit or an explicit repair/stop route before
declaring success. M2824 must not publish the package or claim performance.

## Claim Boundary

Allowed M2823 claim:

```text
M2823 designs and admits a bounded post-recoverability Route A limited-package
materialization preflight that preserves M2822 negative recoverability
limitations, M2804 prior readiness blockers, M2638 HF3 source dependency, and
the P0 actor/action contract.
```

Rejected claims:

```text
package materialized
package published
deployment readiness
driver capability improvement
driver performance
repair success
recoverability success
validation readiness or result
source-build readiness or result
adapter-probe readiness or result
controller-family ranking
scenario-role ranking
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
