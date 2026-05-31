# m1873-executable-v2-support-first-measured-runner-adapter-implementation Research Review

## Summary

- Generated at UTC: 20260531T022833Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: support_first_measured_runner_adapter_implementation_pass_route_to_execution_design
- Decision reason: M1873 implements no-rollout adapter helper with focused tests 4 passed and keeps real materialization rollout ranking blocked

## Hypothesis

A no-rollout adapter can be implemented to convert support-first executable-v2 specs into normalized measured specs and workload rows while enforcing scenario/controller profile separation.

## Lineage

- parent_checkpoint: not_applicable_support_first_measured_runner_adapter_implementation
- parent_dataset: docs/m1872-executable-v2-support-first-measured-runner-adapter-design.md, runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json, runs/m1674_controller_family_one_seed_public_pilot
- parent_config: experiments/manifests/m1872-executable-v2-support-first-measured-runner-adapter-design.json
- parent_objective: implement no-rollout support-first measured-runner adapter
- derived_from: m1872-executable-v2-support-first-measured-runner-adapter-design
- blocked_by: M1872 defines adapter schema and admits implementation before materialization or rollout
- supersedes: manual support-first workload matrix construction, direct measured rollout from support-first reset payload
- invalidates: None

## Success Criteria

- src/autodrift/executable_v2_support_first_measured_runner_adapter.py exists
- tests/test_executable_v2_support_first_measured_runner_adapter.py exists
- focused tests pass
- implementation keeps project materialization rollout training replay PPO and ranking unrun
- implementation preserves scenario_profile_name and controller_profile_name separation

## Failure Criteria

- adapter module is missing
- focused tests are missing or fail
- implementation runs project materialization or rollout
- implementation conflates support-first profile_name with controller policy profile_name
- implementation changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1873 must implement the no-rollout adapter helper and focused tests
- M1873 must not run project materialization, environment reset, policy action, or measured rollout
- M1873 must preserve scenario_profile_name versus controller_profile_name separation
- M1873 must enforce target counts and guardrails in test fixtures

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run support-first measured workload materialization over project artifacts
- do not run environment reset
- do not run measured rollout
- do not execute policy actions
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change reward
- do not change dynamics
- do not change termination behavior
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification
- do not treat support-first profile_name as a controller policy profile

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1873-executable-v2-support-first-measured-runner-adapter-implementation
- type: infrastructure
- checkpoint: docs/m1873-executable-v2-support-first-measured-runner-adapter-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: support_first_measured_runner_adapter_implementation_pass_route_to_execution_design
- reason: M1873 implements no-rollout adapter helper with focused tests 4 passed and keeps real materialization rollout ranking blocked

## Next Blocker

m1874-executable-v2-support-first-measured-runner-adapter-execution-design
