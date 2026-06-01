# M2156 Paper-Route Current-Sim Terminal-Boundary Reset-Sampling Diagnostic Design

- status: completed
- decision: `terminal_boundary_reset_sampling_diagnostic_design_admit_branch_synthesis_before_implementation`
- parent audit: `docs/m2155-paper-route-current-sim-controlled-comparison-reset-validation-result-audit.md`
- reset rerun in M2156: `false`
- rollout/measured execution in M2156: `false`
- policy actions executed in M2156: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Constraint

M2155 localizes the M2154 reset-validation failure to one row:

```text
task_source_id: m2151-current-sim-t5-03
task_family: T5_terminal_boundary_near_constraint
source_family_template: t5_high_speed_close_obstacle
capability_pair: terminal_boundary
source_index: 3
frozen reset seed: 215335
materialized eval_seed_override: 219103
obstacle.max_sample_attempts: 200
```

The next step should not drop the row, silently change the reset seed, or
retune controller profiles. It should first determine whether the failure is:

```text
seed_local_sampling_failure:
  original seed fails but materialized eval seed or nearby deterministic seed
  succeeds under the same attempt budget.

attempt_budget_limited:
  original seed fails at 200 attempts but succeeds at a larger bounded budget.

terminal_boundary_template_brittle:
  original and materialized seeds still fail even with larger bounded budgets.

mixed_or_inconclusive:
  diagnostic outcomes do not cleanly support one of the above classifications.
```

## Frozen Command

M2158, after required branch synthesis, must implement and run exactly:

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

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic.py
```

## Diagnostic Semantics

The diagnostic implementation should:

- load exactly one target spec from the M2151 executable specs;
- preserve all actor-input, profile, and current-sim metadata;
- copy the target env config and change only
  `obstacle.max_sample_attempts` for diagnostic attempts;
- run reset-only attempts for the Cartesian product of:

```text
eval_seeds: 215335, 219103
attempt_budgets: 200, 800, 1600
```

This creates `6` diagnostic reset attempts. No rollout step or policy action is
allowed.

## Planned Artifacts

The diagnostic implementation must write:

```text
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/summary.json
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/diagnostic_rows.csv
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/reset_failure_rows.csv
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/contract_rows.csv
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/classification_rows.csv
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/claim_boundary.csv
runs/m2157_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/run_state.json
```

## Pass Gates

The diagnostic implementation passes as a diagnostic if:

```text
result_class == current_sim_terminal_boundary_reset_sampling_diagnostic_complete
target_task_source_id == m2151-current-sim-t5-03
target_spec_count == 1
diagnostic_attempt_count == 6
observed_eval_seed_count == 2
observed_attempt_budget_count == 3
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
environment_reset_started == true
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
diagnostic_classification in {
  seed_local_sampling_failure,
  attempt_budget_limited,
  terminal_boundary_template_brittle,
  original_seed_passes_at_200,
  mixed_or_inconclusive
}
```

The diagnostic may include failed reset attempts. The pass/fail question for
M2157 is whether the diagnostic ran and classified the failure cleanly, not
whether every diagnostic reset succeeds.

## Claim Boundary

Supported after a clean M2157 run and M2158 audit:

```text
the M2154 terminal-boundary reset failure has a bounded reset-sampling
classification.
```

Unsupported:

```text
full M2151 panel reset validity;
measured execution;
policy behavior;
controller-family ranking;
winner selection;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2157-paper-route-current-sim-controlled-comparison-benchmark-branch-synthesis
```

The research harness requires branch synthesis before running the diagnostic
implementation because the current-sim controlled-comparison branch has reached
its cadence and local-search guard threshold.
