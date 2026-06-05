# M2772 Engineering Controller Route A Source-Only Action-Response Belief Intervention Design

## Metadata

- status: completed
- decision: `admit_source_only_action_response_belief_intervention_materialization_preflight`
- manifest: `experiments/manifests/m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design.json`
- design doc: `docs/m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design.md`
- parent synthesis: `docs/m2771-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-result-synthesis.md`
- route plan: `docs/post-m2470-route-plan.md`
- HF3 blocker: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- source-only evidence: `docs/m2492-source-only-closed-loop-fixture-pilot-branch-synthesis.md`
- source-only fresh panel: `docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-synthesis.md`
- source checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- follow-up manifest: `experiments/manifests/m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight.json`
- next: `m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight`

## Design Premise

M2771 closes the M2766-M2770 current-sim mechanism-localized actor-head repair
branch as complete and claim-safe but negative:

```text
M2769 repair rows: 8
M2769 checkpoints: 3
M2769 execution rows: 24
M2769 execution failure rows: 0
M2769 diagnostic success: 0/24
M2769 collision rows: 3/24
M2769 off_track rows: 17/24
M2769 speed_too_low rows: 4/24
context-only rows: 4
guardrails: 31
```

Another scalar actor-head bias sweep on the same 8 current-sim rows would be
local search. Direct Route C HF3 execution is still not admitted because the
source dependency remains absent under M2638. The next evidence-changing step
is therefore a source-only action-response belief intervention panel.

M2772 is design-only. It does not execute reset, step, policy action, rollout,
replay, validation, training, PPO, source build, adapter probe, external
simulation, ranking, winner selection, promotion, success-rate verdict
computation, or driver-performance measurement. It freezes the bounded protocol
for M2773.

## Evidence Inputs

M2773 may consume these source artifacts:

```text
docs/m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design.md
docs/m2771-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-result-synthesis.md
docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md
docs/m2492-source-only-closed-loop-fixture-pilot-branch-synthesis.md
docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-synthesis.md
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/summary.json
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_behavior_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_event_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/telemetry_rows.csv
runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/summary.json
runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
```

M2773 must not treat M2641 or M2655 as validation, ranking, performance,
paper, current-sim, high-fidelity, full-driver, or self-ID evidence. They are
only source-only diagnostic lineage and checkpoint admission evidence.

## Candidate Surface

M2773 should use the repo-local `FourWheelHF0Backend` and `P0ObservationExtractor`
surface. External simulators and selected-platform source builds remain out of
scope.

The candidate surface is a bounded source-only matrix:

```text
backend: source_only_four_wheel_hf0
source model: FourWheelDriftModel
actor checkpoint: M2655 mitigation-preserving actor-head repair checkpoint
actor observation shape: 72
action shape: 3
action semantics: steer, throttle, brake
role families:
  stable_avoidable
  stable_aes
  drift_required_recovery
  unavoidable_mitigation
dynamics axes:
  source_only_nominal_or_role_default
  source_only_fault_delay_noise
fresh seeds per role and axis: 4
planned candidate rows: 32
horizon steps: 80
```

The three non-mitigation role families are the primary belief-intervention
surface. `unavoidable_mitigation` rows must be carried as mitigation reference
guard/context rows and must not become ordinary success denominators.

M2773 may reuse M2641 schemas and role/axis definitions, but it must produce a
fresh M2773 candidate/intervention matrix instead of rebranding M2641 measured
rows or the M2769 8 current-sim rows. Any seed reuse from M2641 must be
explicitly recorded as lineage; any fresh seed offset must be deterministic and
recorded.

## Intervention Conditions

M2773 should materialize these intervention conditions for each admitted
candidate row:

```text
normal_recurrent:
  hidden state policy: carry recurrent hidden state normally
  actor-view history fields: unmodified deployable actuator and previous
    physical command fields
  purpose: baseline same-contract source-only rollout

reset_hidden_each_step:
  hidden state policy: reset recurrent hidden to None or zero before every
    policy action
  actor-view history fields: unmodified deployable actuator and previous
    physical command fields
  purpose: isolate recurrent latent memory contribution while preserving
    current deployable observation fields

zero_previous_command_history:
  hidden state policy: carry recurrent hidden state normally
  actor-view history fields: evaluator-only zeroing of previous physical
    steer, throttle, and brake command fields before actor extraction
  purpose: test dependence on deployable command-response traces without
    adding hidden/oracle information

held_actuator_history:
  hidden state policy: carry recurrent hidden state normally
  actor-view history fields: evaluator-only hold actuator state and previous
    command fields at reset values
  purpose: test actuator-state history contribution while preserving shape
```

Optional condition, only if pair construction is clean and actor-invisible:

```text
wrong_history_cross_seed_same_role_axis:
  hidden state policy: use recurrent hidden state from another seed in the same
    role family and dynamics axis after a matched prefix
  actor-view history fields: unmodified deployable fields from the active row
  purpose: test whether mismatched latent belief perturbs action response
```

The intervention label, role family, dynamics axis, seed, source row, outcome,
success, progress, and verdict fields must remain actor-invisible. Interventions
may change values inside the existing deployable observation schema for
evaluator-only ablation, but they must not add features, change dimensionality,
or inject hidden/oracle labels.

## Output Artifact Contract

M2773 should write:

```text
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/summary.json
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/source_only_candidate_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/intervention_condition_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/candidate_intervention_matrix.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/intervention_execution_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/intervention_failure_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/action_response_trace_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/mitigation_reference_guard_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/actor_contract_guard_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/claim_boundary_rows.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/gate_matrix.csv
runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight/run_state.json
docs/m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight.md
experiments/manifests/m2774-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-result-audit.json
```

Recommended row schemas:

```text
source_only_candidate_rows.csv:
  candidate_id, role_family, dynamics_axis, seed, backend_id, source_model,
  checkpoint_path, horizon_steps, source_only_surface_id,
  ordinary_success_denominator_allowed, mitigation_reference,
  actor_visible_labels, source_lineage

intervention_condition_rows.csv:
  intervention_condition_id, intervention_family, recurrent_hidden_policy,
  actor_view_history_policy, actor_input_shape_changed, actor_input_feature_added,
  hidden_or_oracle_value_added, evaluator_only, actor_visible_label,
  allowed_claim_scope

candidate_intervention_matrix.csv:
  candidate_id, intervention_condition_id, execution_scheduled,
  matched_history_required, ordinary_denominator_allowed,
  expected_trace_rows, stop_if_unresolved

intervention_execution_rows.csv:
  candidate_id, intervention_condition_id, role_family, dynamics_axis, seed,
  steps_executed, backend_status, action_finite, action_within_bounds,
  observation_shape, action_shape, collision_diagnostic, road_departure_diagnostic,
  minimum_obstacle_clearance_m, minimum_road_margin_m, trace_delta_proxy,
  command_response_proxy, diagnostic_only

action_response_trace_rows.csv:
  candidate_id, intervention_condition_id, step_index, steer, throttle, brake,
  previous_steer_command, previous_throttle_command, previous_brake_command,
  actuator_steer_state, actuator_throttle_state, actuator_brake_state,
  vx_body, vy_body, yaw_rate, ax_body, ay_body, finite_metric
```

M2773 may record diagnostic deltas between intervention conditions, but those
deltas are not ranking, success-rate verdict, driver-performance, paper,
current-sim, high-fidelity, full-driver, or self-ID evidence until separately
audited and compared under later gates.

## Actor And Claim Boundary

M2773 must preserve:

```text
P0 observation shape: 72
action shape: 3
deployed action mapping: steer, throttle, brake
actor input contract changed: false
actor input feature added: false
hidden/oracle actor input detected: false
role labels actor-visible: false
dynamics labels actor-visible: false
intervention labels actor-visible: false
outcome/progress/success/verdict labels actor-visible: false
source-only diagnostic labels actor-visible: false
external high-fidelity simulation run: false
```

Forbidden actor inputs remain friction, mass, tire stiffness, brake scale,
actuator tau, slip, tire force, TTC, path error, heading error, path curvature,
oracle feasibility, stopping distance, required clearance, AEB/AES/drift
labels, controller mode, speed reference, beta target, source-only role labels,
dynamics-axis labels, intervention labels, and any precomputed success or
progress signal.

## Gate Matrix

M2773 should pass only if all of these hold:

```text
M2772 design artifact exists
M2771 negative repair synthesis is preserved
M2638 HF3 source blocker is preserved
M2492 source-only closed-loop path evidence is preserved
M2641/M2643 source-only fresh panel evidence is consumed as lineage only
M2655 checkpoint exists and actor checkpoint admission preserves 72/3
source-only candidate rows are written and are not the M2769 8 current-sim rows
normal recurrent and at least two evaluator-only intervention conditions are written
candidate/intervention matrix accounts for every scheduled pair
execution rows plus failure rows account for every scheduled pair
mitigation reference rows are carried outside ordinary denominators
actor-contract guard rows pass
claim-boundary rows pass
gate matrix passes
M2774 result audit manifest is registered
```

M2773 must fail or route to artifact repair if it cannot modify recurrent
hidden state or actor-view history fields without changing the actor schema,
adding labels, or using hidden/oracle values.

## Supported M2772 Claims

M2772 supports only these claims:

```text
A bounded source-only action-response belief intervention protocol is designed.
The design changes evidence axis away from M2769 same-surface current-sim
actor-head repair.
The design preserves actor 72/action 3 and no hidden/oracle actor input.
The design registers M2773 as a bounded source-only materialization preflight.
```

M2772 does not prove that the actor uses recurrent belief, command-response
history, or actuator state. That requires M2773 execution artifacts and a
later audit or proof gate.

## Rejected Claims

M2772 rejects:

```text
repair_success=false
driver_performance=false
validation_readiness=false
validation_result=false
ranking_or_winner_selection=false
checkpoint_promotion=false
success_rate_verdict=false
paper_evidence=false
finite_window_vs_gru_conclusion=false
current_sim_verdict=false
high_fidelity_validation=false
full_ideal_driver_completion=false
level3_self_identification=false
```

## Next Branch Decision

M2772 admits:

```text
m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight
```

M2773 is allowed to execute bounded repo-local source-only reset, step, policy
action, and rollout paths for the registered candidate/intervention matrix. It
is not allowed to run external HF3 simulation, replay validation, training,
PPO, ranking, winner selection, checkpoint promotion, success-rate verdict
computation, driver-performance claims, current-sim verdicts, high-fidelity
validation claims, paper claims, full ideal driver claims, or self-ID claims.
