# M2284 Paper-Route Current-Sim Scenario Task-Family Reset-Validation Implementation

- status: completed
- result class: `current_sim_scenario_task_family_reset_validation_fail`
- decision: `current_sim_scenario_task_family_reset_validation_fail_route_to_result_audit`
- manifest: `experiments/manifests/m2284-paper-route-current-sim-scenario-task-family-reset-validation-implementation.json`
- implementation:
  - `src/autodrift/paper_route_current_sim_scenario_task_family_reset_validation.py`
- tests:
  - `tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py`
- run artifact: `runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/summary.json`
- environment reset started: `true`
- policy actions executed: `false`
- rollout/measured execution/training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2284 adds a focused reset-only validator for the current-sim scenario
task-family config pack:

```text
autodrift.paper_route_current_sim_scenario_task_family_reset_validation
```

The validator consumes:

```text
configs/paper_route_current_sim_scenario_task_family_v0.json
```

and writes reset, contract, label, lateral-offset consistency, aggregate, and
claim-boundary artifacts. It does not step the environment or execute policy
actions.

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py
```

Result:

```text
3 passed
```

Static checks:

```bash
python -m compileall -q src tests
git diff --check
```

Both passed.

## Reset-Validation Command

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_reset_validation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation \
  --eval-seed-base 228300 \
  --target-spec-count 72 \
  --expected-observation-dim 72 \
  --next-blocker m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit
```

Result:

```text
result_class: current_sim_scenario_task_family_reset_validation_fail
input_scenario_spec_count: 72
target_count_matches: true
reset_attempt_count: 72
reset_success_count: 12
reset_failure_count: 60
observation_finite_count: 12
observation_dimension_failure_count: 0
obstacle_initialized_count: 12
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
label_not_allowed_count: 60
single_label_exact_mismatch_count: 48
lateral_offset_numeric_mismatch_count: 60
lateral_bucket_mismatch_count: 66
guardrail_violation_count: 0
passes_public_reset_validation_gates: false
primary_route: scenario_task_family_reset_validation_failure_route_to_result_audit
```

## Failure Shape

Reset success is role-localized:

```text
R0_stable_avoidable: 12/12
R1_aeb_infeasible_stable_aes: 0/12
R2_handling_limit_drift_capable_avoidance: 0/12
R3_recovery_after_limit: 0/12
R4_unavoidable_mitigation: 0/12
R5_hidden_dynamics_robustness: 0/12
```

The 60 reset failures are all:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

This means the v0 spec materialization over-constrained the simulator obstacle
sampler for R1-R5 under the current distance/speed/label/dynamics settings.

The lateral-offset gate also found the sign issue anticipated by M2282. For
successful R0 resets:

```text
centerline rows: pass
left_offset rows: numeric offset matches -1.2 but signed bucket convention fails
right_offset rows: numeric offset matches +1.2 but signed bucket convention fails
```

The summary-level `lateral_bucket_mismatch_count` is `66`: `60` unavailable
checks from reset failures plus `6` signed-bucket mismatches among successful R0
left/right rows.

## Contract And Guardrails

The negative result is not an actor-contract or guardrail regression:

```text
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Decision

Route to M2285 result audit:

```text
m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit
```

M2285 should classify the reset-sampling failures and the lateral sign mismatch
before any repair. M2284 must not repair and rerun materialization.

## Blocked Claims

Still blocked:

```text
scenario pack reset-validity
rollout success
measured execution success
training result
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
```
