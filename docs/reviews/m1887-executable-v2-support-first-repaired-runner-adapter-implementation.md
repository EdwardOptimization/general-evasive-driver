# m1887-executable-v2-support-first-repaired-runner-adapter-implementation Research Review

## Summary

- Generated at UTC: 20260531T034859Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: support_first_repaired_runner_adapter_implementation_pass_admit_preflight_design
- Decision reason: M1887 implements no-rollout repaired runner adapter with focused tests 3 passed and keeps real M1884 preflight blocked

## Hypothesis

A no-rollout repaired runner adapter can be implemented to convert M1884 repair rows into bounded-smoke executable specs, rollout workload rows, and import rows without changing actor inputs.

## Lineage

- parent_checkpoint: not_applicable_repaired_runner_adapter_implementation
- parent_dataset: docs/m1886-executable-v2-support-first-repaired-measured-execution-design.md, runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv, runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json, runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv
- parent_config: experiments/manifests/m1886-executable-v2-support-first-repaired-measured-execution-design.json
- parent_objective: implement no-rollout repaired runner adapter for bounded repaired smoke preflight
- derived_from: m1886-executable-v2-support-first-repaired-measured-execution-design
- blocked_by: M1884 repair matrix cannot be consumed by existing measured runner until repair config deltas are converted into executable specs and workload rows
- supersedes: direct repaired measured execution without adapter
- invalidates: None

## Success Criteria

- src/autodrift/executable_v2_support_first_repaired_runner_adapter.py exists
- focused tests pass
- adapter validates config delta keys
- adapter separates rollout geometry rows from imported original and semantics-only rows
- adapter does not run the real M1884 matrix

## Failure Criteria

- adapter code is missing
- focused tests fail
- adapter runs reset or rollout
- adapter changes actor inputs or tunes controller profiles
- adapter routes directly to ranking

## Evidence Gates

- M1887 must implement a no-rollout repaired runner adapter
- M1887 must include focused tests for bounded-smoke selection and config delta validation
- M1887 must not run the real M1884 matrix
- M1887 must preserve original baseline import rows and controller profile identity
- M1887 must keep controller-family ranking blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
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

- milestone: m1887-executable-v2-support-first-repaired-runner-adapter-implementation
- type: infrastructure
- checkpoint: src/autodrift/executable_v2_support_first_repaired_runner_adapter.py
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: support_first_repaired_runner_adapter_implementation_pass_admit_preflight_design
- reason: M1887 implements no-rollout repaired runner adapter with focused tests 3 passed and keeps real M1884 preflight blocked

## Next Blocker

m1888-executable-v2-support-first-repaired-runner-adapter-preflight-design
