# M2687 Engineering Controller Route A Package With Limitations Protocol Design

## Metadata

- status: completed
- decision: `admit_package_protocol_materialization_preflight`
- manifest: `experiments/manifests/m2687-engineering-controller-route-a-package-with-limitations-protocol-design.json`
- design artifact: `docs/m2687-engineering-controller-route-a-package-with-limitations-protocol-design.md`
- parent synthesis: `docs/m2686-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-branch-synthesis.md`
- Route A readiness reference: `docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.md`
- Route A readiness index: `runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/summary.json`
- HF3 blocker reference: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2688-engineering-controller-route-a-package-with-limitations-protocol-materialization-preflight.json`
- next: `m2688-engineering-controller-route-a-package-with-limitations-protocol-materialization-preflight`

## Admission Decision

M2687 admits a bounded Route A package-with-limitations protocol
materialization preflight. It does not admit package publication, validation
readiness, high-fidelity execution, driver-performance claims, controller
ranking, checkpoint promotion, paper claims, current-sim verdicts, or self-ID
claims.

The purpose is narrow: convert the already accepted Route A readiness evidence
into a machine-auditable package protocol that keeps limitations visible. This
is useful because M2686 closed the Route B task-quality/role-semantics subset
branch after a complete but off-track-dominated execution result. The project
should not keep repairing the same current-sim public subset before packaging
the engineering baseline boundaries that are already known.

## Governing Constraints

`docs/post-m2470-route-plan.md` separates the controller project from the
paper-proof project. Route A can package an actuator-level active-safety
baseline with limitations, while Route B remains responsible for falsifiable
finite-window/GRU/self-ID evidence.

M2687 therefore preserves three facts at once:

```text
Route A readiness:
  M2667/M2668/M2669 cover the six near-term Route A artifacts and make them
  packageable with limitations.

Route B current-sim blocker:
  M2684/M2685/M2686 produced complete bounded diagnostic data, but off-track
  dominance still blocks ranking and paper interpretation.

Route C HF3 blocker:
  M2638 pauses selected-platform HF3 source-build and adapter-probe execution
  until source dependency evidence is supplied.
```

The package protocol must not hide any of those limitations.

## Package Scope

M2688 should materialize a package protocol pack for these six required Route A
artifacts:

| Package artifact | Source | Required use |
| --- | --- | --- |
| baseline checkpoint list | `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv` | Lists candidate baseline checkpoints without promotion or winner selection. |
| actor input/output contract | `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json` | Freezes P0 observation shape `72`, action shape `3`, and `[steer, throttle, brake]`. |
| public benchmark pack | `public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json` | Provides public source-only diagnostic benchmark context, not validation readiness. |
| runtime/inference-cost report | `runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json` and M2509 audit | Records runtime cost evidence without performance verdicts. |
| scenario-role metric report | `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/scenario_role_metric_report.csv` | Keeps target roles and protected mitigation roles separate. |
| known failure taxonomy | `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json` plus M2665/M2666 audits | Preserves protected mitigation as a broad known blocker. |

Supporting context may be included but must be labeled as non-package evidence:

- M2667 readiness index rows and gates;
- M2684/M2685/M2686 current-sim diagnostic blocker evidence;
- M2635-M2638 HF3 dependency/source blocker evidence;
- `docs/post-m2470-route-plan.md`.

## Manifest Schema

M2688 should write a `package_manifest_schema_rows.csv` table with these
minimum fields:

```text
field_name
required
source
allowed_values_or_type
claim_scope
blocked_interpretation
```

Required manifest fields:

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
```

The package manifest must be a protocol artifact. It must not be a public
release, validation certificate, benchmark verdict, or deployment claim.

## Artifact Inventory Rules

M2688 should write `package_artifact_inventory_rows.csv`.

Each inventory row must include:

```text
artifact_id
source_milestone
source_path
source_exists
status_pass_or_present
package_required
package_inclusion_status
row_count_or_summary
artifact_role
claim_scope
blocked_interpretation
```

Admission rules:

- every required Route A artifact must have `source_exists=true`;
- missing supporting context may be recorded as a blocker but must not be
  silently dropped;
- package inclusion does not imply validation readiness;
- package inclusion does not rank checkpoints or select a baseline winner;
- package inclusion must preserve actor/action contract and known blocker
  disclosure.

## Provenance Map Rules

M2688 should write `package_provenance_map_rows.csv`.

The provenance map must connect package rows back to accepted milestones:

```text
M2541 -> baseline checkpoint list and actor I/O contract
M2505 -> public benchmark pack
M2508/M2509 -> runtime/inference-cost report
M2657 -> scenario-role metric report
M2664/M2665/M2666 -> known failure taxonomy
M2667/M2668/M2669 -> Route A readiness integration and packageable-with-limitations synthesis
M2684/M2685/M2686 -> Route B current-sim off-track diagnostic blocker
M2635/M2636/M2637/M2638 -> HF3 dependency/source blocker
post-M2470 route plan -> governing route split
```

Rows must distinguish package content from context. M2688 must not imply that
Route B current-sim diagnostics or Route C HF3 blocker rows are packaged as
capability evidence.

## Known Blocker Disclosure Rules

M2688 should write `known_blocker_disclosure_rows.csv`.

Minimum blocker rows:

| Blocker | Required disclosure |
| --- | --- |
| protected mitigation blocker | M2664/M2665/M2666 preserve broad protected mitigation failure; protected rows stay outside success denominators. |
| current-sim off-track blocker | M2684/M2685/M2686 preserve off-track dominance: 202/216 off-track outcomes and 203/216 off-track terminations in the bounded subset. |
| HF3 dependency/source blocker | M2638 pauses selected-platform HF3 source-build and adapter-probe execution until source dependency evidence is supplied. |
| paper/self-ID blocker | M2686 rejects finite-window-vs-GRU, current-response sufficiency, paper, current-sim, full ideal driver, and level3 self-ID claims from the bounded subset. |

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

Blocker rows are not actor-visible and must not become policy inputs.

## Actor And Action Contract

M2688 should write `actor_action_contract_rows.csv`.

The contract rows must preserve:

```text
observation_shape: 72
action_shape: 3
deployed_action_mapping: [steer, throttle, brake]
hidden_oracle_actor_input_detected: false
taxonomy_labels_actor_visible: false
route_labels_actor_visible: false
package_labels_actor_visible: false
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
labels, package status, blocker labels, validation outcomes, or precomputed
answers.

## Claim Boundary Rows

M2688 should write `claim_boundary_rows.csv`.

Allowed claims:

```text
Route A package-with-limitations protocol materialized from existing accepted
readiness artifacts.

The package protocol includes artifact inventory, provenance, known blocker
disclosures, actor/action contract rows, claim boundaries, and materialization
gates.

The package is not a validation result and not a driver-performance claim.
```

Blocked claims:

```text
driver performance
validation readiness
validation result
high-fidelity validation readiness or result
source-build readiness or result
adapter-probe readiness or result
backend availability
reset feasibility
rollout feasibility
controller-family ranking
winner selection
checkpoint promotion
repair success
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
full ideal driver completion
level3 self-identification
```

## Materialization Gates

M2688 should write `package_protocol_gate_matrix.csv`.

Required gates:

```text
required_route_a_artifacts_present
package_manifest_schema_complete
artifact_inventory_complete
provenance_map_complete
known_blocker_disclosures_complete
actor_action_contract_preserved
protected_mitigation_blocker_visible
current_sim_offtrack_blocker_visible
hf3_source_dependency_blocker_visible
claim_boundary_rows_complete
no_execution_performed
no_training_or_ppo_performed
no_ranking_or_promotion_performed
no_validation_or_driver_performance_claim
no_paper_current_sim_high_fidelity_or_self_id_claim
follow_up_route_registered
```

M2688 should pass only if every gate passes. If any required artifact is
missing, the correct result is an artifact-inventory blocker, not partial
package acceptance.

## Admitted Follow-Up

M2688 should materialize, not publish, the package protocol pack. Expected
future artifacts:

```text
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/summary.json
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/package_manifest_schema_rows.csv
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/package_artifact_inventory_rows.csv
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/package_provenance_map_rows.csv
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/known_blocker_disclosure_rows.csv
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/actor_action_contract_rows.csv
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/claim_boundary_rows.csv
runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/package_protocol_gate_matrix.csv
docs/m2688-engineering-controller-route-a-package-with-limitations-protocol-materialization-preflight.md
```

M2688 may route to result audit, artifact repair, package materialization
repair, branch synthesis, or stop. It must not publish the package or claim
driver performance.

## Claim Boundary

Allowed M2687 claim:

```text
M2687 designs a bounded Route A package-with-limitations protocol and admits
M2688 materialization preflight, while preserving Route A known blockers,
M2686 current-sim off-track dominance, M2638 HF3 source dependency pause, and
the P0 actor/action contract.
```

Rejected claims:

```text
published package
deployment readiness
driver capability improvement
driver performance
validation readiness or result
source-build readiness or result
adapter-probe readiness or result
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
