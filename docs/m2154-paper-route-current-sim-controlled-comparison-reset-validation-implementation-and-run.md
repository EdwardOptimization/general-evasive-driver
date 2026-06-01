# M2154 Paper-Route Current-Sim Controlled Comparison Reset Validation Implementation and Run

- status: failed
- decision: `current_sim_reset_validation_preflight_fail_route_to_result_audit`
- command source: `docs/m2153-paper-route-current-sim-controlled-comparison-reset-validation-command-design.md`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_reset_validation_preflight.py`
- tests: `tests/test_paper_route_current_sim_controlled_comparison_reset_validation_preflight.py`
- summary: `runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/summary.json`
- environment reset started: `true`
- environment rollout started: `false`
- policy action executed: `false`
- measured execution started: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M2154 ran the frozen M2153 reset-only command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --output-dir runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --eval-seed-base 215300 \
  --target-spec-count 40 \
  --expected-observation-dim 72 \
  --next-blocker m2155-paper-route-current-sim-controlled-comparison-reset-validation-result-audit
```

Focused tests:

```text
tests/test_paper_route_current_sim_controlled_comparison_reset_validation_preflight.py: 3 passed
```

## Result

M2154 fails closed because one current-sim terminal-boundary spec cannot sample
an obstacle scenario matching the configured filters under the frozen eval seed.

```text
result_class: current_sim_controlled_comparison_reset_validation_preflight_fail
input_executable_spec_count: 40
target_executable_spec_count: 40
reset_attempt_count: 40
reset_success_count: 39
reset_failure_count: 1
observation_finite_count: 39
observation_dimension_failure_count: 0
obstacle_initialized_count: 39
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
task_family_quota_pass: true
source_family_template_quota_pass: true
guardrail_violation_count: 0
environment_reset_started: true
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Failing row:

```text
task_source_id: m2151-current-sim-t5-03
task_family: T5_terminal_boundary_near_constraint
source_family_template: t5_high_speed_close_obstacle
source_index: 3
eval_seed: 215335
error_type: RuntimeError
error_message: failed to sample an obstacle scenario matching the configured filters
```

The failure is not a schema, actor-input contract, forbidden-key, or guardrail
failure. It is a reset-sampling feasibility failure for one terminal-boundary
row and must be audited before any repair or rerun.

## Artifacts

```text
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/summary.json
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_failure_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/contract_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_distribution_by_task_family.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/reset_distribution_by_source_family_template.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/metadata_missing_rows.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/claim_boundary.csv
runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/run_state.json
```

## Supported Claims

M2154 supports:

- the current-sim reset-only validator implementation is runnable and has
  focused test coverage;
- the frozen M2153 command executed without rollout or policy actions;
- `39/40` M2151 executable specs reset with finite 72-dimensional observations
  and initialized obstacles;
- actor-input contract, metadata, forbidden-key, task/source quota, and
  guardrail checks are clean;
- one terminal-boundary row needs reset-sampling audit.

M2154 does not support:

- marking the current-sim panel reset-valid;
- measured execution;
- policy behavior or controller-family ranking;
- finite-window vs GRU comparison;
- winner selection;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m2155-paper-route-current-sim-controlled-comparison-reset-validation-result-audit
```

M2155 must audit the reset-sampling failure without rerunning reset or changing
the scenario spec. It should decide whether the right next move is scenario
repair, reset-seed/obstacle-filter repair, or branch synthesis.
