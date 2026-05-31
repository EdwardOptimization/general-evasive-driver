# m1872-executable-v2-support-first-measured-runner-adapter-design Research Review

## Summary

- Generated at UTC: 20260531T022228Z
- Type: gate
- Gate tier: process
- Promotion decision: support_first_measured_runner_adapter_design_admit_implementation
- Decision reason: M1872 fixes full 2160-cell public diagnostic adapter schema with scenario/controller profile separation and admits no-rollout implementation

## Hypothesis

A support-first measured-runner adapter can be designed by separating scenario-profile metadata from controller policy profiles while preserving role-wise diagnostics and blocking ranking claims.

## Lineage

- parent_checkpoint: not_applicable_support_first_measured_runner_adapter_design
- parent_dataset: docs/m1871-executable-v2-support-first-measured-execution-design.md, runs/m1866_executable_v2_support_first_reset_validation_adapter/support_first_reset_executable_v2_panel_specs.json, runs/m1869_executable_v2_support_first_reset_validation_preflight/summary.json, src/autodrift/metric_specific_bounded_panel_measured_execution.py, src/autodrift/controller_family_full_rollout_execution.py
- parent_config: experiments/manifests/m1871-executable-v2-support-first-measured-execution-design.json
- parent_objective: design support-first measured-runner adapter before any measured rollout
- derived_from: m1871-executable-v2-support-first-measured-execution-design
- blocked_by: M1871 finds that existing measured runners do not directly consume support-first payload semantics
- supersedes: direct measured execution from support-first reset payload, using support-first profile_name as controller profile_name
- invalidates: None

## Success Criteria

- docs/m1872-executable-v2-support-first-measured-runner-adapter-design.md exists
- design defines adapter input schema and output workload schema
- design separates scenario_profile_name from controller_profile_name
- design chooses execution budget and profile set without tuning
- design preserves role-surface imbalance explicitly
- design blocks ranking paper-level and level3 self-ID claims
- no measured rollout training replay PPO or ranking is run

## Failure Criteria

- design document is missing
- design runs rollout or policy actions
- design conflates support-first profile_name with controller policy profile_name
- design hides support-first panel imbalance
- design routes directly to controller ranking
- design changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1872 must define the support-first measured-runner adapter schema without running rollout
- M1872 must separate scenario_profile_name from controller_profile_name
- M1872 must choose full-matrix or smoke-matrix execution budget and profile set without tuning
- M1872 must preserve the support-first role-surface imbalance explicitly
- M1872 must define role-wise diagnostic outputs and keep ranking paper-level and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m1872-executable-v2-support-first-measured-runner-adapter-design
- type: gate
- checkpoint: docs/m1872-executable-v2-support-first-measured-runner-adapter-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: support_first_measured_runner_adapter_design_admit_implementation
- reason: M1872 fixes full 2160-cell public diagnostic adapter schema with scenario/controller profile separation and admits no-rollout implementation

## Next Blocker

m1873-executable-v2-support-first-measured-runner-adapter-implementation
