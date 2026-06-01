# M2197 Paper-Route Current-Sim Offtrack-Support Reset-Validation Compatibility Implementation And Run

- status: completed
- decision: `current_sim_offtrack_support_reset_validation_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2197-paper-route-current-sim-offtrack-support-reset-validation-compatibility-implementation-and-run.json`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_reset_validation_preflight.py`
- focused tests: `5 passed`
- reset summary: `runs/m2197_paper_route_current_sim_offtrack_support_reset_validation_preflight/summary.json`
- environment reset in M2197: `true`
- measured execution in M2197: `false`
- policy action executed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M2197 adds explicit compatibility parameters to the current-sim reset validator:

```text
--expected-materialization-semantics
--expected-paper-validity-status
--task-id
```

The old M2151 defaults are preserved when these flags are omitted. The M2194
repaired specs are accepted only when the M2194-specific expected values are
passed explicitly.

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --executable-task-specs runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json \
  --output-dir runs/m2197_paper_route_current_sim_offtrack_support_reset_validation_preflight \
  --eval-seed-base 219700 \
  --target-spec-count 288 \
  --expected-observation-dim 72 \
  --seed-source-mode prefer_spec_eval_seed_override \
  --expected-materialization-semantics current_sim_offtrack_support_repair_materialization_v0 \
  --expected-paper-validity-status current_sim_offtrack_support_candidate_not_reset_validated \
  --task-id m2197-paper-route-current-sim-offtrack-support-reset-validation-compatibility-implementation-and-run \
  --next-blocker m2198-paper-route-current-sim-offtrack-support-reset-validation-result-audit
```

## Result

```text
result_class: current_sim_controlled_comparison_reset_validation_preflight_pass
input_executable_spec_count: 288
target_executable_spec_count: 288
reset_attempt_count: 288
reset_success_count: 288
reset_failure_count: 0
observation_finite_count: 288
observation_dimension_failure_count: 0
obstacle_initialized_count: 288
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
seed_source_mode: prefer_spec_eval_seed_override
seed_source_quota_pass: true
guardrail_violation_count: 0
```

Task-family reset counts:

```text
T1_reactive_emergency_avoidance: 24
T2_delayed_actuator_response: 30
T3_diagnostic_warmup_obstacle_reveal: 66
T4_same_current_different_older_history: 70
T5_terminal_boundary_near_constraint: 98
```

Source-family-template reset counts:

```text
t4_actuator_delay_response: 30
t4_capability_step_temporal: 70
t4_staged_warmup_capability: 66
t5_boundary_axis_retarget: 24
t5_high_speed_close_obstacle: 98
```

## Interpretation

M2197 establishes reset validity for the repaired task panel. It does not run
policy actions, measured execution, controller comparison, or history
interventions.

Allowed claim:

```text
The M2194 repaired current-sim offtrack-support task panel is reset-valid under
the human-view/no-wheel actor contract.
```

Still blocked:

```text
measured execution
controller-family ranking
winner selection
finite-window vs GRU verdict
paper-level benchmark evidence
level3 self-identification
```

## Next Step

M2198 must audit the reset-validation result before any measured-execution
readiness or command design.
