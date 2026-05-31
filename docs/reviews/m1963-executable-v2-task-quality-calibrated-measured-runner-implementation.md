# m1963-executable-v2-task-quality-calibrated-measured-runner-implementation Research Review

## Summary

- Generated at UTC: 20260531T105015Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_measured_runner_adapter_pass_admit_command_design
- Decision reason: M1963 implements calibrated measured runner adapter with focused tests 3 passed preserving repair-source metadata and aggregates without real 960-cell rollout

## Hypothesis

A focused calibrated measured runner adapter can preserve M1958 repair metadata and support synthetic execution tests without running real measured rollout.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_measured_runner
- parent_dataset: docs/m1962-executable-v2-task-quality-calibrated-measured-execution-design.md, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m1962-executable-v2-task-quality-calibrated-measured-execution-design.json
- parent_objective: implement focused calibrated measured runner adapter without real rollout
- derived_from: m1962-executable-v2-task-quality-calibrated-measured-execution-design
- blocked_by: existing measured runners do not preserve calibrated repair metadata as first-class output fields
- supersedes: direct measured execution over M1958 workload with legacy M1936 runner outputs
- invalidates: None

## Success Criteria

- src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py exists
- tests/test_executable_v2_task_quality_calibrated_measured_runner.py exists
- focused tests pass
- docs/m1963-executable-v2-task-quality-calibrated-measured-runner-implementation.md exists
- real M1958 measured execution is not run

## Failure Criteria

- adapter is missing
- focused tests fail
- adapter cannot preserve calibrated repair metadata
- real 960-cell measured execution is run
- controller ranking or paper-level claims are made

## Evidence Gates

- M1963 must add focused calibrated measured runner adapter and tests
- M1963 must preserve calibrated repair metadata and profile provenance
- M1963 must support mocked execution path without running real 960-cell rollout
- M1963 must keep ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run real M1958 environment rollout
- do not execute real policy actions over the 960-cell workload
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1963-executable-v2-task-quality-calibrated-measured-runner-implementation
- type: infrastructure
- checkpoint: src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0000000000
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_measured_runner_adapter_pass_admit_command_design
- reason: M1963 implements calibrated measured runner adapter with focused tests 3 passed preserving repair-source metadata and aggregates without real 960-cell rollout

## Next Blocker

m1963-executable-v2-task-quality-calibrated-measured-runner-implementation
