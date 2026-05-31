# m2039-paper-route-controlled-routing-smoke-measured-execution-implementation-and-run Research Review

## Summary

- Generated at UTC: 20260531T185218Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: controlled_routing_smoke_measured_execution_pass_route_to_result_audit
- Decision reason: M2039 focused measured runner completes 432/432 episodes failure 0 metric completeness 0 guardrail 0 raw success 20 collision 13 offtrack 399 no ranking claim

## Hypothesis

A focused controlled-routing-smoke measured runner can execute the 432-row M2033 workload while preserving metadata and guardrail boundaries.

## Lineage

- parent_checkpoint: not_applicable_controlled_routing_smoke_measured_execution
- parent_dataset: docs/m2038-paper-route-controlled-routing-smoke-measured-execution-command-design.md, runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json, runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m2038-paper-route-controlled-routing-smoke-measured-execution-command-design.json
- parent_objective: implement focused measured runner and run 432-row controlled routing-smoke workload
- derived_from: m2038-paper-route-controlled-routing-smoke-measured-execution-command-design
- blocked_by: M2038 rejects lossy existing runners and freezes a focused measured-runner route
- supersedes: lossy reuse of hard-coded routing smoke or calibrated task-quality measured runner
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json exists
- result_class is controlled_routing_smoke_measured_execution_pass
- episode_count is 432
- failure_count is 0
- metric_completeness_failure_count is 0
- guardrail_violation_count is 0
- no controller ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- focused runner is missing
- focused tests fail
- validation fails before rollout
- measured execution is incomplete
- metadata is dropped
- ranking or paper claims are made

## Evidence Gates

- M2039 must implement focused runner preserving M2033 metadata
- M2039 must run exactly 432 planned workload rows if validation passes
- M2039 must preserve failures and not repair/rerun inside the milestone
- M2039 must keep ranking paper finite-window-vs-GRU and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m2039-paper-route-controlled-routing-smoke-measured-execution-implementation-and-run
- type: infrastructure
- checkpoint: runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json
- success_rate: 0.046296
- termination_rate: None
- clearance_margin_mean: 10.530665
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_routing_smoke_measured_execution_pass_route_to_result_audit
- reason: M2039 focused measured runner completes 432/432 episodes failure 0 metric completeness 0 guardrail 0 raw success 20 collision 13 offtrack 399 no ranking claim

## Next Blocker

m2040-paper-route-controlled-routing-smoke-measured-execution-result-audit
