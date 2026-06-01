# m2120-paper-route-outcome-supported-decisive-comparison-support-reset-validation-command-design Research Review

## Summary

- Generated at UTC: 20260601T020453Z
- Type: gate
- Gate tier: process
- Promotion decision: comparison_support_reset_validation_command_design_admit_implementation_and_run
- Decision reason: M2120 freezes comparison-support-specific reset validator command over M2118 specs target 240 obs dim 72 eval seed base 212100 because materialization_semantics is comparison_support_smoke_proxy

## Hypothesis

A comparison-support-specific reset-validation command can be frozen over the M2118 materialized panel without changing actor inputs, profile configs, or claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_comparison_support_reset_validation_command_design
- parent_dataset: runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/summary.json, runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json, docs/m2119-paper-route-outcome-supported-decisive-comparison-support-materialization-preflight-result-audit.md
- parent_config: experiments/manifests/m2119-paper-route-outcome-supported-decisive-comparison-support-materialization-preflight-result-audit.json
- parent_objective: design a comparison-support reset-validation command over the clean M2118 materialized panel
- derived_from: m2119-paper-route-outcome-supported-decisive-comparison-support-materialization-preflight-result-audit
- blocked_by: M2119 must audit materialization before reset-validation command design
- supersedes: running the old routing-smoke reset validator directly on comparison_support_smoke_proxy rows, direct measured execution without reset validation
- invalidates: None

## Success Criteria

- docs/m2120-paper-route-outcome-supported-decisive-comparison-support-reset-validation-command-design.md exists
- frozen command names executable specs output dir eval seed base target spec count and expected observation dim
- comparison_support_smoke_proxy compatibility route is explicit
- next implementation route is explicit
- no reset rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design doc is missing
- frozen command is ambiguous
- comparison_support_smoke_proxy compatibility route is missing
- new reset or rollout is performed
- ranking or paper-level claims are made

## Evidence Gates

- M2120 must freeze a comparison-support-specific reset-only command
- M2120 must preserve target_spec_count 240 expected_observation_dim 72 and eval_seed_base 212100
- M2120 must account for materialization_semantics comparison_support_smoke_proxy
- M2120 must not run reset rollout measured execution or rank controller families

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit implementation code
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim reset validity
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not treat generated rows as paper-valid tasks

## Failure Taxonomy

- none

## Scoreboard

- milestone: m2120-paper-route-outcome-supported-decisive-comparison-support-reset-validation-command-design
- type: gate
- checkpoint: docs/m2120-paper-route-outcome-supported-decisive-comparison-support-reset-validation-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: comparison_support_reset_validation_command_design_admit_implementation_and_run
- reason: M2120 freezes comparison-support-specific reset validator command over M2118 specs target 240 obs dim 72 eval seed base 212100 because materialization_semantics is comparison_support_smoke_proxy

## Next Blocker

m2121-paper-route-outcome-supported-decisive-comparison-support-reset-validation-implementation-and-run
