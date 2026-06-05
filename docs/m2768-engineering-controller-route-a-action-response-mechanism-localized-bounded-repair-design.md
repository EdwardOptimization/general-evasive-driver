# M2768 Engineering Controller Route A Action-Response Mechanism-Localized Bounded Repair Design

## Metadata

- status: completed
- decision: `admit_action_response_mechanism_localized_bounded_repair_execution_preflight`
- manifest: `experiments/manifests/m2768-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-design.json`
- design doc: `docs/m2768-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-design.md`
- parent audit: `docs/m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit.md`
- parent summary: `runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/summary.json`
- follow-up manifest: `experiments/manifests/m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight.json`
- next: `m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight`

## Design Premise

M2767 accepts M2766 as a complete and claim-safe mechanism-localization panel.
The accepted panel contains:

```text
telemetry join rows: 12
mechanism-localization rows: 12
repair-admission rows: 12
bounded repair-design candidates: 8
context-only no-repair rows: 4
guardrail context rows: 31
actor-contract guard rows: 6
claim-boundary rows: 18
gate rows: 21
```

M2768 is design-only. It does not execute reset, step, policy action, rollout,
replay, validation, training, PPO, source build, adapter probe, external
simulation, ranking, winner selection, promotion, checkpoint selection, or
success-rate computation. It does not claim repair success, driver performance,
paper evidence, current-sim validation, high-fidelity validation, full ideal
driver completion, or level3 self-identification.

The design purpose is to admit one bounded M2769 repair execution preflight
that tests actor-head repair candidates on the admitted mechanism-localized
rows while preserving the actor input contract and all claim boundaries.

## Candidate Repair Surface

M2769 may consume only these M2766 artifacts as candidate and guardrail inputs:

```text
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/summary.json
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/telemetry_join_rows.csv
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/mechanism_localization_rows.csv
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/repair_admission_rows.csv
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/guardrail_context_rows.csv
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/actor_contract_guard_rows.csv
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/claim_boundary_rows.csv
runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/gate_matrix.csv
```

The admitted repair surface is exactly the 8 rows in
`repair_admission_rows.csv` where `repair_admitted_for_design=True`:

```text
m1680-spec-0001  m2753-cross-axis-candidate-0001  track_containment_context  track_containment_stability_target
m1680-spec-0003  m2753-cross-axis-candidate-0002  track_containment_context  track_containment_stability_target
m1680-spec-0010  m2753-cross-axis-candidate-0004  track_containment_context  track_containment_stability_target
m1680-spec-0037  m2753-cross-axis-candidate-0005  track_containment_context  track_containment_stability_target
m1680-spec-0044  m2753-cross-axis-candidate-0009  track_containment_context  track_containment_stability_target
m1680-spec-0045  m2753-cross-axis-candidate-0010  obstacle_timing_context  obstacle_timing_or_clearance_margin_target
m1680-spec-0046  m2753-cross-axis-candidate-0011  track_containment_context  track_containment_stability_target
m1680-spec-0047  m2753-cross-axis-candidate-0012  track_containment_context  track_containment_stability_target
```

M2769 must not add nearby rows, resample rows, substitute task sources, broaden
to all M2753 or M2764 rows, or choose rows because they are likely to pass. The
surface is fixed before execution.

## Context And Guardrail Surface

The 4 diagnostic-success rows remain context-only regression rows:

```text
m1680-spec-0008  m2753-cross-axis-candidate-0003  diagnostic_success_context  context_only_no_repair_target
m1680-spec-0039  m2753-cross-axis-candidate-0006  diagnostic_success_context  context_only_no_repair_target
m1680-spec-0042  m2753-cross-axis-candidate-0007  diagnostic_success_context  context_only_no_repair_target
m1680-spec-0043  m2753-cross-axis-candidate-0008  diagnostic_success_context  context_only_no_repair_target
```

M2769 must carry them into `context_only_regression_rows.csv` and must not
count them as repair wins, candidate rows, ordinary success denominators,
ranking denominators, or promotion evidence.

All 31 M2766 guardrail context rows must remain guardrails:

```text
execution_run: false
ordinary_success_denominator_allowed: false
protected_rows_in_success_denominator: false
actor_visible_allowed: false
```

If any repair candidate overlaps a context-only row or guardrail row, M2769
must write a failure row and stop or route to artifact repair rather than
weakening the surface definition.

## Repair Lever Contract

M2769 may test bounded actor-head repair candidates only. It must not change
the actor observation, action dimension, deployed action semantics, environment
difficulty, hidden dynamics, task geometry, oracle fields, scenario labels, or
active baseline configs.

The admitted repair lever family is:

```text
repair_lever_family: actor_head_bias_candidate_sweep
source_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
trainable surface: actor output head bias or equivalent final-action affine bias only
actor observation shape: 72
action shape: 3
hidden/oracle actor input required: false
active_config_overwritten: false
profile_specific_tuning: false
per-row tuning: false
candidate ranking: false
winner selection: false
checkpoint promotion: false
```

M2769 may define a small deterministic candidate sweep, but every candidate
must be applied uniformly to all 8 repair rows and must be evaluated as a
diagnostic candidate, not selected as a winner. The sweep should include at
least:

```text
containment_brake_bias_candidate:
  target class: track_containment_stability_target
  steer bias delta: 0.00
  throttle bias delta: -1.50
  brake bias delta: 1.50
  expected diagnostic direction: reduce offtrack pressure without using row labels

soft_containment_bias_candidate:
  target class: track_containment_stability_target
  steer bias delta: 0.00
  throttle bias delta: -1.00
  brake bias delta: 1.00
  expected diagnostic direction: smaller containment repair with lower action disturbance

clearance_timing_brake_bias_candidate:
  target class: obstacle_timing_or_clearance_margin_target
  steer bias delta: 0.00
  throttle bias delta: -2.00
  brake bias delta: 2.00
  expected diagnostic direction: earlier speed reduction on the obstacle-timing row
```

These are global candidate deltas. They must not depend on task source id,
failure family, mechanism label, obstacle side, route label, success label, TTC,
oracle clearance requirement, hidden friction, hidden vehicle parameters, or
any row-specific rule answer.

If M2769 cannot implement the actor-head candidate sweep without actor input
expansion or active config overwrite, it must produce an artifact-complete
failure preflight and route to implementation repair or synthesis.

## Bounded Execution Protocol

M2769 may execute reset, step, policy action, and rollout only for the 8
admitted repair rows and only under the fixed candidate sweep. It must not
execute replay, validation, PPO, training, source build, adapter probe,
external simulation, private holdout, ranking, winner selection, promotion, or
success-rate verdict computation.

Execution rules:

```text
candidate rows accounted: 8
context-only rows accounted: 4
guardrail rows accounted: 31
source baseline rows joined from M2766/M2764: required
one diagnostic rollout per repair candidate per admitted row
no profile-specific tuning
no row replacement
no active config overwrite
no environment difficulty relaxation
no hidden/oracle actor feature
no actor-visible mechanism, repair-target, progress, success, or verdict labels
```

M2769 should write failure rows for unresolved or non-executable rows rather
than silently dropping them. Artifact completeness, actor safety, and claim
boundaries are the pass criteria; behavioral improvement is not the M2769 pass
criterion and must wait for M2770 audit.

## Output Artifact Contract

M2769 should write:

```text
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/summary.json
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/repair_candidate_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/repair_candidate_resolution_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/repair_checkpoint_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/baseline_join_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/repair_execution_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/repair_execution_failure_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/context_only_regression_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/guardrail_context_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/actor_contract_guard_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/claim_boundary_rows.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/gate_matrix.csv
runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/run_state.json
docs/m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight.md
experiments/manifests/m2770-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-result-audit.json
```

The execution rows may record diagnostic metrics such as termination reason,
offtrack flag, collision flag, clearance margin, road margin, return, episode
length, action-response proxy, command-delta proxy, and finite-metric checks.
Those metrics are diagnostic only and cannot be promoted into performance or
success-rate verdicts without a separate result audit and later gates.

## Actor And Claim Boundary

M2769 must preserve:

```text
P0 observation shape: 72
action shape: 3
actor input contract changed: false
hidden/oracle actor input detected: false
mechanism labels actor-visible: false
repair-target labels actor-visible: false
context-only labels actor-visible: false
guardrail labels actor-visible: false
route/gate/progress/success/verdict labels actor-visible: false
```

Forbidden actor inputs remain friction, mass, tire stiffness, brake scale,
actuator tau, slip, tire force, TTC, path error, heading error, path curvature,
oracle feasibility, stopping distance, required clearance, AEB/AES/drift
labels, controller mode, speed reference, beta target, and any precomputed
success or progress signal.

## Gate Matrix

M2769 passes only if all of these hold:

```text
M2766 summary status_pass true
M2767 audit completed and claim-safe
8 admitted repair rows accounted
4 context-only rows accounted and excluded from repair-win interpretation
31 guardrail rows accounted and not executed
candidate sweep rows written
repair checkpoint rows written or explicit artifact-complete failure written
repair execution rows plus failure rows account for every candidate/candidate-row pair
baseline join rows preserve M2764 finite telemetry and M2759 no-backfill lineage
active_config_overwritten false
environment_difficulty_relaxed false
profile_specific_tuning false
actor 72/action 3 preserved
hidden_oracle_actor_input_detected false
actor-visible repair labels false
ranking winner promotion success-rate verdict false
all required artifacts present
one result-audit follow-up manifest registered
```

If execution produces negative or mixed outcomes, M2769 can still pass as an
artifact-complete bounded preflight. The result must be audited in M2770 before
any repair interpretation.

## Follow-Up

M2768 admits:

```text
m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight
```

M2769 may execute bounded repair candidate rollouts only under the contract
above and must register a separate M2770 result audit before interpretation.

## Claim Boundary

Allowed M2768 claim:

```text
M2768 defines a bounded actor-safe mechanism-localized repair execution
protocol and admits one separately pre-registered execution preflight.
```

Rejected claims:

```text
repair execution result
repair success
driver performance
validation readiness or result
controller-family ranking
repair-candidate ranking
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
