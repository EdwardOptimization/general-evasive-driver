# m2036-paper-route-controlled-routing-smoke-reset-validation-implementation-and-run Research Review

## Summary

- Generated at UTC: 20260531T183434Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: controlled_routing_smoke_reset_validation_pass_route_to_result_audit
- Decision reason: M2036 focused reset validator passes 36/36 resets with obs dim failures 0 metadata 0 contract 0 guardrail 0 and no rollout or policy actions

## Hypothesis

A focused controlled-routing-smoke reset validator can reset all 36 M2033 executable specs with finite 72-dim observations while preserving M2033 metadata and claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_controlled_routing_smoke_reset_validation
- parent_dataset: docs/m2035-paper-route-controlled-routing-smoke-reset-validation-command-design.md, runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json
- parent_config: experiments/manifests/m2035-paper-route-controlled-routing-smoke-reset-validation-command-design.json
- parent_objective: implement and run focused reset-only validation for M2033 controlled routing-smoke specs
- derived_from: m2035-paper-route-controlled-routing-smoke-reset-validation-command-design
- blocked_by: M2035 finds older reset validators cannot preserve M2033 metadata schema
- supersedes: lossy reuse of generic task-quality reset validator
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/summary.json exists
- result_class is controlled_routing_smoke_reset_validation_preflight_pass
- reset_attempt_count is 36
- reset_success_count is 36
- guardrail_violation_count is 0
- metadata_missing_count is 0
- no rollout measured execution ranking paper finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- focused validator is missing
- focused tests fail
- summary artifact is missing
- any reset fails
- metadata is dropped
- policy actions or rollout are executed

## Evidence Gates

- M2036 must implement focused reset validator preserving M2033 metadata
- M2036 must run only reset validation over 36 executable specs
- M2036 must not execute rollout steps or policy actions
- M2036 must keep ranking paper finite-window-vs-GRU and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not treat smoke proxy rows as paper-valid generated tasks

## Failure Taxonomy

- none

## Scoreboard

- milestone: m2036-paper-route-controlled-routing-smoke-reset-validation-implementation-and-run
- type: infrastructure
- checkpoint: runs/m2036_paper_route_controlled_routing_smoke_reset_validation_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_routing_smoke_reset_validation_pass_route_to_result_audit
- reason: M2036 focused reset validator passes 36/36 resets with obs dim failures 0 metadata 0 contract 0 guardrail 0 and no rollout or policy actions

## Next Blocker

m2037-paper-route-controlled-routing-smoke-reset-validation-result-audit
