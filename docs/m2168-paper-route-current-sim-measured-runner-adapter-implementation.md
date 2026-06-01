# M2168 Paper-Route Current-Sim Measured Runner Adapter Implementation

- status: completed
- decision: `current_sim_measured_runner_adapter_implementation_pass_route_to_audit`
- parent design: `docs/m2167-paper-route-current-sim-measured-runner-adapter-design.md`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py`
- tests: `tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py`
- real M2151 measured execution in M2168: `false`
- policy actions on M2151 panel: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2168 implements a current-sim-specific measured runner adapter. It preserves
M2151 spec/workload metadata and writes current-sim aggregate artifacts, but it
does not run the real M2151 workload.

Implemented adapter:

```text
src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py
```

Focused test module:

```text
tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

## Focused Tests

M2168 ran:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Result:

```text
2 passed
```

Covered paths:

```text
fake-rollout path:
  preserves current-sim metadata;
  writes episode and aggregate artifacts;
  passes profile/history/task-family quotas;
  keeps ranking, paper, finite-window-vs-GRU, and self-ID claims false.

real-mode missing-checkpoint path:
  produces validation_failure_rows with missing_checkpoint_path;
  episode_count == 0;
  failure_count == 0;
  environment_rollout_started == false;
  policy_action_executed == false.
```

## Adapter Output Contract

The adapter writes:

```text
summary.json
episode_rows.csv
failure_rows.csv
validation_failure_rows.csv
metadata_missing_rows.csv
metric_completeness_failures.csv
profile_aggregate.csv
profile_level_aggregate.csv
history_representation_aggregate.csv
task_family_aggregate.csv
source_family_template_aggregate.csv
capability_pair_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
claim_boundary.csv
run_state.json
```

The adapter result class for successful fake-rollout or future real measured
execution is:

```text
current_sim_controlled_comparison_measured_execution_pass
```

For missing-checkpoint or incomplete results:

```text
current_sim_controlled_comparison_measured_execution_incomplete_or_fail
```

## Claim Boundary

Supported:

- the current-sim measured runner adapter exists;
- focused fake-rollout tests validate metadata preservation and aggregate
  writing;
- real mode fails closed before rollout when required checkpoints are missing.

Unsupported:

- real M2151 measured execution;
- controller-family ranking or winner selection;
- finite-window vs GRU verdict;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m2169-paper-route-current-sim-measured-readiness-repair-branch-synthesis
```

M2169 must synthesize the measured-readiness repair branch before
checkpoint/profile materialization design because the local-search guard reached
the non-evidence milestone limit.
