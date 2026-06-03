# M2559 Engineering Controller Route A Baseline HF3 Low-Cost Pilot Design

- status: completed
- decision: `route_to_hf3_low_cost_pilot_materialization_preflight`
- manifest: `experiments/manifests/m2559-engineering-controller-route-a-baseline-hf3-low-cost-pilot-design.json`
- parent synthesis: `docs/m2558-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-result-synthesis.md`
- parent audit: `docs/m2557-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-result-audit.md`
- HF2 summary: `runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/summary.json`
- HF2 binding source: `runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_surface_fixture_binding.csv`
- HF2 pilot guard source: `runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_pilot_admission_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight.json`
- next: `m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight`

## Scope

M2559 designs the Route A HF3 low-cost pilot materialization/preflight after
accepted HF2 taxonomy mapping. The design turns the Route C HF3 requirement
into machine-readable candidate, reset-feasibility, rollout-feasibility,
external-boundary, claim-boundary, and gate artifacts for M2560.

M2559 is design-only. It does not install, import, or run external
high-fidelity simulation. It does not execute policy actions, step
environments, train, replay, rank, promote, compute success rates, or claim
validation or driver performance.

## Route-Plan Binding

`docs/post-m2470-route-plan.md` defines HF3 low-cost pilot as:

```text
single-role stable avoidable pilot
single-role stable AES pilot
reset feasibility and rollout feasibility only
no controller-family verdict yet
```

M2560 should materialize a preflight plan for those two pilot roles only. It
must not grant pilot admission from HF2 taxonomy metadata alone.

## Source Contracts

M2560 should bind to the accepted Route A/HF2 contract:

```text
P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
HF2 route-role rows = 5
HF2 surface/fixture bindings = 10
HF2 metadata-boundary checks = 7
HF2 pilot-admission guards = 5
HF2 materialization gates = 7
HF3 pilot admission claim in HF2 = false
```

Candidate status remains a preflight label. It must not enter actor input and
must not be interpreted as validation readiness:

```text
baseline_reference_binding -> design reference candidate only
diagnostic_reference_binding -> diagnostic reference only
materialization_candidate_binding -> materialization candidate only
```

## M2560 Required Artifacts

M2560 should write:

```text
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_pilot_candidate_rows.csv
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_reset_feasibility_plan.csv
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_rollout_feasibility_plan.csv
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_external_backend_boundary_checks.csv
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_claim_boundary_checks.csv
runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/materialization_gate_matrix.csv
docs/m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight.md
```

## Pilot Candidate Rows

M2560 should write candidate rows:

```text
candidate_id
route_role_id
route_role_label
source_binding_id
source_fixture_id
source_binding_status
actor_observation_shape
action_shape
hf3_candidate_scope
hf3_admission_status
reset_feasibility_required
rollout_feasibility_required
validation_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_design_candidate`
- `stable_aes_aeb_infeasible_design_candidate`

Candidate source policy:

- stable avoidable may use the `source_only_four_wheel_hf0:stable_avoidable`
  baseline-reference binding as a design reference candidate, not an admitted
  pilot.
- stable AES may use the `source_only_four_wheel_hf0:stable_aes`
  materialization-candidate binding as a design candidate, not an admitted
  pilot.
- any missing source row must be reported as blocked, not fabricated.

Pass criteria:

- exactly two pilot candidate rows exist
- both rows preserve P0 `72/3`
- `hf3_admission_status` remains `requires_m2560_reset_and_rollout_feasibility`
- no baseline/reference/materialization-candidate row is silently upgraded to
  pilot-admitted
- no row claims validation, ranking, or driver performance

## Reset Feasibility Plan

M2560 should write reset-feasibility plan rows:

```text
reset_check_id
candidate_id
route_role_id
required_source_binding_status
external_backend_boundary
reset_state_source
policy_action_allowed_in_m2560
environment_step_allowed_in_m2560
reset_success_claim_allowed
required_before_rollout
status_pass
claim_boundary
```

Pass criteria:

- every pilot candidate has a reset-feasibility row
- `policy_action_allowed_in_m2560` is false
- `environment_step_allowed_in_m2560` is false
- reset success is not claimed in M2560
- rollout feasibility remains blocked until reset feasibility is materialized
  by a later execution milestone

## Rollout Feasibility Plan

M2560 should write rollout-feasibility plan rows:

```text
rollout_check_id
candidate_id
route_role_id
requires_reset_feasibility_artifact
action_contract
rollout_execution_allowed_in_m2560
success_rate_claim_allowed
controller_family_verdict_allowed
required_before_validation
status_pass
claim_boundary
```

Pass criteria:

- every pilot candidate has a rollout-feasibility row
- deployed action contract remains `[steer, throttle, brake]`
- rollout execution is false in M2560
- success rate and controller-family verdict are false in M2560
- validation remains blocked until explicit reset and rollout execution gates
  are passed by later milestones

## External Backend Boundary Checks

M2560 should write boundary rows:

```text
boundary_check_id
backend_boundary
install_allowed
import_allowed
simulation_run_allowed
policy_action_allowed
environment_step_allowed
status_pass
claim_boundary
```

Required checks:

- external simulator dependency install
- external simulator package import
- external simulator reset execution
- external simulator step execution
- policy action execution
- high-fidelity validation verdict

All required checks should pass with every allowed field set to false.

## Claim Boundary Checks

M2560 should write claim-boundary rows:

```text
claim_id
claim_family
claim_allowed_in_m2560
evidence_required_before_claim
status_pass
claim_boundary
```

Required claim families:

- HF3 pilot admission
- reset success
- rollout success
- high-fidelity validation readiness/result
- controller ranking or winner selection
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

Pass criteria:

- all claim families are present
- all are false in M2560
- every row names the later evidence required before the claim can be made

## Gate Matrix

M2560 passes only if:

- all required artifacts exist
- exactly two pilot candidates are represented
- stable avoidable/AEB-feasible and stable AES/AEB-infeasible candidates are
  present without pilot admission
- reset-feasibility plan rows are complete and do not execute resets
- rollout-feasibility plan rows are complete and do not execute rollouts
- external backend boundary checks pass with no install/import/run
- claim-boundary checks prevent validation, ranking, driver-performance, paper,
  FW-vs-GRU, current-sim, high-fidelity validation, and self-ID claims
- P0 observation shape `72` and action shape `3` are preserved
- no policy rollout, training, replay, PPO, ranking, winner selection,
  checkpoint promotion, success-rate, validation, driver-performance, paper,
  FW-vs-GRU, current-sim, high-fidelity validation, or self-ID claim is made

## Follow-Up

Route to M2560 materialization/preflight. M2560 may add a bounded source-only
materializer and tests to write the artifacts above. It must not run external
high-fidelity simulation, step environments, execute policy actions, or
interpret feasibility design rows as validation or driver performance.
