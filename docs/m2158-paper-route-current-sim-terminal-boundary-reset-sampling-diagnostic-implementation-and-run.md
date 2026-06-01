# M2158 Paper-Route Current-Sim Terminal-Boundary Reset-Sampling Diagnostic Implementation and Run

- status: completed
- decision: `terminal_boundary_reset_sampling_diagnostic_complete_route_to_result_audit`
- command source: `docs/m2157-paper-route-current-sim-controlled-comparison-benchmark-branch-synthesis.md`
- implementation: `src/autodrift/paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic.py`
- tests: `tests/test_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic.py`
- summary: `runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/summary.json`
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

M2158 ran the frozen reset-only diagnostic:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --target-task-source-id m2151-current-sim-t5-03 \
  --output-dir runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic \
  --eval-seeds 215335,219103 \
  --attempt-budgets 200,800,1600 \
  --expected-observation-dim 72 \
  --next-blocker m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit
```

Focused tests:

```text
tests/test_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic.py: 2 passed
```

## Result

M2158 completes the diagnostic and classifies the M2154 blocker as
`seed_local_sampling_failure`.

```text
result_class: current_sim_terminal_boundary_reset_sampling_diagnostic_complete
target_task_source_id: m2151-current-sim-t5-03
target_spec_count: 1
diagnostic_attempt_count: 6
observed_eval_seed_count: 2
observed_attempt_budget_count: 3
reset_success_count: 3
reset_failure_count: 3
diagnostic_classification: seed_local_sampling_failure
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
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

Diagnostic attempts:

```text
eval_seed=215335, attempt_budget=200:  fail
eval_seed=215335, attempt_budget=800:  fail
eval_seed=215335, attempt_budget=1600: fail
eval_seed=219103, attempt_budget=200:  pass
eval_seed=219103, attempt_budget=800:  pass
eval_seed=219103, attempt_budget=1600: pass
```

The materialized spec already carries:

```text
eval_seed_override: 219103
```

Therefore the M2154 failure is not repaired by raising
`obstacle.max_sample_attempts`; the original reset-validation command used
`eval_seed_base + index == 215335`, while the materialized executable spec's own
reset seed `219103` resets cleanly at the original `200` attempt budget.

## Artifacts

```text
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/summary.json
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/diagnostic_rows.csv
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/reset_failure_rows.csv
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/contract_rows.csv
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/metadata_missing_rows.csv
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/classification_rows.csv
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/claim_boundary.csv
runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/run_state.json
```

## Supported Claims

M2158 supports:

- the T5 reset failure is seed-local for the tested bounded diagnostic;
- increasing `max_sample_attempts` does not fix the original reset seed;
- the materialized `eval_seed_override=219103` resets the same spec under the
  original `200` attempt budget;
- actor-input contract, metadata, forbidden-key, and guardrail counts are clean;
- the next audit should evaluate whether reset validation should use
  per-spec `eval_seed_override` instead of sequential `eval_seed_base + index`.

M2158 does not support:

- full panel reset-validity;
- modifying the reset validator without audit;
- measured execution;
- policy behavior or controller-family ranking;
- finite-window vs GRU comparison;
- winner selection;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit
```

M2159 should audit the seed-source mismatch before any reset-validation repair
or rerun.
