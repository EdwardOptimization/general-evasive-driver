# M2287 Paper-Route Current-Sim Scenario Task-Family Reset-Sampling And Lateral-Sign Repair Implementation

- status: completed
- result class: `current_sim_scenario_task_family_reset_validation_fail`
- decision: `current_sim_scenario_task_family_reset_repair_fail_route_to_result_audit`
- manifest: `experiments/manifests/m2287-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-implementation.json`
- implementation:
  - `src/autodrift/paper_route_current_sim_scenario_task_family_config_materialization.py`
- tests:
  - `tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py`
- materialization artifact: `runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/materialization/summary.json`
- reset-validation artifact: `runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/reset_validation/summary.json`
- policy actions executed: `false`
- rollout/measured execution/training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2287 implemented the combined M2286 repair:

```text
1. fixed materialized lateral sign convention:
   centerline -> 0.0
   left_offset -> +1.2
   right_offset -> -1.2

2. added sampler-aware role target selection:
   role family + timing + hidden bucket
   -> deterministic classify_obstacle_scenario precheck
   -> narrow speed/mu/distance/half-width env_config centers
   -> reset-validation pack
```

The pack now uses a low-curvature current-sim emergency approach radius:

```text
track_kind: circle
track_radius_m: 80.0
road_curvature_bucket: circle_r80
```

This preserves the simulator's friction-limited speed semantics while allowing
the AEB-infeasible stable-AES region to exist in the generated scenario family.
It does not change the P0 actor observation contract.

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py \
  tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py \
  tests/test_obstacle_lateral_offset_instrumentation.py
```

Result:

```text
10 passed
```

## Materialization Result

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/materialization \
  --next-blocker m2287-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-implementation
```

Result:

```text
result_class: current_sim_scenario_task_family_config_materialization_pass
scenario_family_count: 6
scenario_spec_count: 72
unsupported_execution_blocker_count: 0
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
passes_public_materialization_gates: true
```

## Reset-Validation Result

Command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_reset_validation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/reset_validation \
  --eval-seed-base 228700 \
  --target-spec-count 72 \
  --expected-observation-dim 72 \
  --next-blocker m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit
```

Result:

```text
result_class: current_sim_scenario_task_family_reset_validation_fail
reset_attempt_count: 72
reset_success_count: 71
reset_failure_count: 1
observation_dimension_failure_count: 0
actor_contract_violation_count: 0
label_not_allowed_count: 1
single_label_exact_mismatch_count: 1
lateral_offset_numeric_mismatch_count: 1
lateral_bucket_mismatch_count: 1
guardrail_violation_count: 0
passes_public_reset_validation_gates: false
```

The remaining failing row is:

```text
scenario_spec_id: m2277_r4_02
role_family: R4_unavoidable_mitigation
hidden_dynamics_bucket: low_mu
timing_bucket: late_close
lateral_bucket: centerline
expected_label: unavoidable
error: RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

The summary-level label and lateral mismatch counts are derived from this one
reset failure, where no actual label or lateral offset is available. Successful
left/right rows no longer show the M2284 sign reversal.

## Interpretation

M2287 substantially repaired the scenario pack:

```text
M2284 reset successes: 12 / 72
M2287 reset successes: 71 / 72
M2284 lateral bucket mismatches: 66
M2287 lateral bucket mismatches: 1
```

The remaining issue is a reset-sampling edge case, not an actor-contract breach
and not a controller-performance result. Because M2287's manifest forbids a
repair-and-rerun loop after validation, the correct route is a result audit.

## Contract And Guardrails

Clean:

```text
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
```

No rollout, policy action, measured execution, training, replay, PPO, private
holdout, controller-family ranking, paper-level claim, finite-window-vs-GRU
conclusion, or level3 self-ID claim was made.

## Decision

Route to M2288 result audit:

```text
m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit
```

M2288 should localize why `m2277_r4_02` fails despite the deterministic
classifier precheck, including friction-step timing filters or exact-range
sampling edge behavior, before any further repair.

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
