# m2047-paper-route-controlled-routing-smoke-task-quality-repair-source-mining-design Research Review

## Summary

- Generated at UTC: 20260531T192829Z
- Type: gate
- Gate tier: process
- Promotion decision: controlled_routing_smoke_task_quality_repair_source_mining_design_admit_materialization_preflight_implementation
- Decision reason: M2047 designs parent resolution and no-reset materialization for 192 repaired specs 2304 workload rows preserving claim guards

## Hypothesis

The M2045 templates can be converted into a bounded no-rollout source-mining/materialization plan with explicit parent resolution and claim guards.

## Lineage

- parent_checkpoint: not_applicable_controlled_routing_smoke_task_quality_repair_source_mining_design
- parent_dataset: docs/m2046-paper-route-controlled-routing-smoke-task-quality-repair-template-result-audit.md, configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json, runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json, runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/success_rows.csv, runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/offtrack_dominance_slices.csv
- parent_config: experiments/manifests/m2046-paper-route-controlled-routing-smoke-task-quality-repair-template-result-audit.json
- parent_objective: design no-rollout conversion from repair templates to concrete repair sources
- derived_from: m2046-paper-route-controlled-routing-smoke-task-quality-repair-template-result-audit
- blocked_by: M2046 admits source-mining/materialization design but templates are not executable specs
- supersedes: direct reset validation from repair templates
- invalidates: None

## Success Criteria

- docs/m2047-paper-route-controlled-routing-smoke-task-quality-repair-source-mining-design.md exists
- parent-resolution and fail-closed rules are explicit
- template delta application is explicit
- output artifact shape is explicit
- next route is explicit
- no code reset rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design doc is missing
- parent-resolution rules are ambiguous
- output artifact shape is ambiguous
- design weakens claim boundaries
- next route is ambiguous

## Evidence Gates

- M2047 must design template-to-source conversion before implementation
- M2047 must specify parent-resolution and fail-closed rules
- M2047 must preserve repair-axis quotas split and claim boundaries
- M2047 must not run reset rollout measured execution or ranking

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit source-mining code
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
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m2047-paper-route-controlled-routing-smoke-task-quality-repair-source-mining-design
- type: gate
- checkpoint: docs/m2047-paper-route-controlled-routing-smoke-task-quality-repair-source-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_routing_smoke_task_quality_repair_source_mining_design_admit_materialization_preflight_implementation
- reason: M2047 designs parent resolution and no-reset materialization for 192 repaired specs 2304 workload rows preserving claim guards

## Next Blocker

m2048-selected-by-m2047-design
