# M2571 Engineering Controller Route A Baseline HF3 Rollout-Feasibility Execution Design

- status: completed
- decision: `route_to_hf3_rollout_feasibility_execution_materialization_preflight`
- manifest: `experiments/manifests/m2571-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-design.json`
- parent synthesis: `docs/m2570-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-result-synthesis.md`
- parent audit: `docs/m2569-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-result-audit.md`
- parent materialization summary: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/summary.json`
- follow-up manifest: `experiments/manifests/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.json`
- next: `m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight`

## Design Verdict

M2571 designs the first bounded Route A HF3 rollout-feasibility execution
materialization after accepted reset-only execution evidence. M2572 may execute
repo-local backend reset, fixed-policy action selection, and backend step rows
through `CurrentSimDynamicsBackend`.

The allowed evidence claim is narrow:

```text
repo-local rollout-feasibility execution observed under the P0 72/3 actor
contract
```

M2571 does not execute policy actions, steps, resets, or rollouts. M2572 must
not install, import, or run external high-fidelity simulation. Neither M2571 nor
M2572 may claim rollout success, high-fidelity validation readiness, driver
performance, controller ranking, checkpoint promotion, paper evidence,
finite-window-vs-GRU evidence, current-sim verdict, or level3 self-ID.

## Route-Plan Binding

`docs/post-m2470-route-plan.md` defines HF3 as:

```text
single-role stable avoidable pilot
single-role stable AES pilot
reset feasibility and rollout feasibility only
no controller-family verdict yet
```

M2572 therefore stays on Route A/Route C as a low-cost feasibility layer. It
does not move to Route B paper evidence, does not compare controller families,
and does not treat the repo-local current-sim adapter as external
high-fidelity validation.

## Source Evidence

Accepted M2568/M2569/M2570 source boundary:

```text
measured reset request rows: 2
backend probe rows: 2
reset-only execution rows: 2
actor-view contract rows: 2
reset outcome rows: 2
claim-boundary checks: 8
materialization gates: 9/9 pass
candidate roles: stable avoidable/AEB-feasible, stable AES/AEB-infeasible
reset execution observed: true
actor-view available after reset: true
actor contract: P0 observation 72 / action 3
policy action executed so far: false
environment step executed so far: false
rollout executed so far: false
reset success claim allowed: false
validation/ranking/driver-performance claim allowed: false
```

M2572 may extend this boundary from reset-only execution to policy-action and
backend-step execution. It must keep candidate labels, reset outcomes,
diagnostics, backend statuses, and rollout outcomes out of actor-visible input.

## M2572 Artifact Contract

M2572 should write:

```text
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_request_rows.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_fixed_policy_source_rows.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_plan_rows.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_policy_action_audit_rows.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_backend_step_outcome_rows.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_actor_view_contract_rows.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_claim_boundary_checks.csv
runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/rollout_feasibility_gate_matrix.csv
docs/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.md
```

## Rollout Request Rows

M2572 should write two request rows:

```text
rollout_request_id
source_reset_request_id
reset_execution_id
route_role_id
backend_family
scenario_spec_id
seed
actor_observation_shape
action_shape
policy_action_allowed_in_m2572
environment_step_allowed_in_m2572
rollout_allowed_in_m2572
pilot_admission_allowed
validation_claim_allowed
status_pass
claim_boundary
```

Required requests:

- `stable_avoidable_aeb_feasible_hf3_rollout_request`
- `stable_aes_aeb_infeasible_hf3_rollout_request`

Pass criteria:

- exactly two request rows exist
- both rows map to accepted M2568 reset requests and reset execution rows
- both rows preserve P0 `72/3`
- policy action and environment step are allowed only in M2572
- pilot admission and validation claims are false

## Fixed Policy Source Rows

M2572 should write one fixed policy source row:

```text
policy_source_id
checkpoint_path
checkpoint_lineage
loader
policy_mode
actor_input_source
actor_observation_shape
action_shape
ranking_role
promotion_allowed
status_pass
claim_boundary
```

Required policy source:

```text
m1154_promoted_public_base_alpha_0_05
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Pass criteria:

- the checkpoint path exists
- the loader is repo-local `autodrift.checkpoints.load_actor_critic_checkpoint`
- the policy acts from the P0 actor observation only
- the action contract is `[steer, throttle, brake]`
- ranking role is `none`
- promotion is false

M2572 must not compare M1154 with M2532/M2537, select a winner, or promote a
checkpoint. M2532/M2537 remain lineage context only.

## Rollout Plan Rows

M2572 should write one rollout plan row per request:

```text
rollout_plan_id
rollout_request_id
policy_source_id
backend_class
reset_required
target_horizon_steps
min_steps_for_execution_observed
early_termination_allowed_as_outcome
success_rate_computation_allowed
controller_family_verdict_allowed
status_pass
claim_boundary
```

Required plan:

```text
backend_class: autodrift.high_fidelity_interface.CurrentSimDynamicsBackend
target_horizon_steps: 8
min_steps_for_execution_observed: 1
early_termination_allowed_as_outcome: true
success_rate_computation_allowed: false
controller_family_verdict_allowed: false
```

Pass criteria:

- exactly two rollout plan rows exist
- every plan uses the fixed M1154 policy source
- every plan resets through the repo-local backend before the first action
- every plan attempts up to eight policy-action/backend-step pairs
- early termination or truncation is recorded as outcome data, not as a
  validation verdict
- no success rate or controller-family verdict is computed

## Policy Action Audit Rows

M2572 should write one policy-action audit row for each executed step:

```text
policy_action_audit_id
rollout_plan_id
rollout_request_id
policy_source_id
step_index
actor_observation_shape
action_shape
action_finite
action_clipped_to_contract
steer_command
throttle_command
brake_command
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
policy_action_executed
status_pass
claim_boundary
```

Expected count:

```text
2 rollout requests * up to 8 steps = up to 16 policy-action audit rows
```

Pass criteria:

- every executed action has shape `3`
- every action is finite and clipped through the deployed action validator
- actor observation shape is `72`
- no hidden/oracle, diagnostics, taxonomy label, feasibility class, backend
  status, reset outcome, or rollout outcome enters actor input
- every row records the physical `[steer, throttle, brake]` mapping

## Backend Step/Outcome Rows

M2572 should write one backend step/outcome row for each executed step:

```text
backend_step_outcome_id
rollout_plan_id
rollout_request_id
step_index
backend_family
backend_class
backend_step_attempted
backend_status
terminated_by_backend
truncated_by_backend
actor_view_available_after_step
diagnostics_recorded
diagnostics_actor_visible
rollout_success_claim_allowed
validation_claim_allowed
status_pass
claim_boundary
```

Pass criteria:

- at least one backend step is attempted for each rollout request
- backend class remains `CurrentSimDynamicsBackend`
- diagnostics are recorded for audit only and are never actor-visible
- actor view is available after every completed backend step
- termination and truncation are recorded as outcomes only
- rollout success and validation claims remain false

## Actor-View Contract Rows

M2572 should write actor-view rows for reset and every completed backend step:

```text
actor_view_check_id
rollout_plan_id
rollout_request_id
source_phase
step_index
actor_observation_shape
action_shape
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
reset_outcome_actor_visible
rollout_outcome_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- no hidden/oracle actor input is detected
- diagnostics, taxonomy labels, backend status, reset outcomes, and rollout
  outcomes are not actor-visible

## Claim Boundary Checks

M2572 should write claim-boundary rows for:

- reset execution observed
- rollout-feasibility execution observed
- rollout success
- high-fidelity validation readiness/result
- controller ranking or winner selection
- checkpoint promotion
- success-rate or controller-family verdict
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

Only the operational claims `reset execution observed` and
`rollout-feasibility execution observed` may become true after M2572 if all
gates pass. Rollout success, validation, ranking, promotion, success-rate,
driver performance, paper evidence, and self-ID remain false.

## Gate Matrix

M2572 should pass only if:

```text
source_artifacts_exist
rollout_request_rows_complete
fixed_policy_source_rows_pass
rollout_plan_rows_pass
policy_action_audit_rows_pass
backend_step_outcome_rows_pass
actor_view_contract_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_forbidden_execution_or_claim_flags
```

The forbidden flags include external simulator install/import/run, dependency
mutation, actor input mutation, action contract mutation, training, replay,
PPO, ranking, winner selection, checkpoint promotion, success-rate
computation, rollout success claim, validation claim, driver-performance
claim, paper claim, finite-window-vs-GRU claim, current-sim verdict claim,
high-fidelity validation claim, and self-ID claim.

## Follow-Up

Route to M2572 rollout-feasibility execution materialization preflight. M2572
may execute only the bounded repo-local reset/action/step loop specified above.
If M2572 passes, the next task should audit the result before any rollout
success, validation, ranking, or driver-performance interpretation.
