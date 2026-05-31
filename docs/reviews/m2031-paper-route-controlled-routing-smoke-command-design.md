# m2031-paper-route-controlled-routing-smoke-command-design Research Review

## Summary

- Generated at UTC: 20260531T174147Z
- Type: gate
- Gate tier: process
- Promotion decision: controlled_routing_smoke_command_design_route_to_materialization_adapter_design
- Decision reason: M2031 finds existing runners cannot directly execute M2029 merged panel with provenance and routes to no-rollout materialization adapter design

## Hypothesis

A bounded routing-smoke command can be designed over the M2029 projected-ready panel while preserving smoke-only claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_controlled_routing_smoke_command_design
- parent_dataset: docs/m2030-paper-route-t2-t3-source-generation-preflight-result-audit.md, runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv, runs/m2029_paper_route_t2_t3_source_generation_preflight/source_coverage_projection.csv
- parent_config: experiments/manifests/m2030-paper-route-t2-t3-source-generation-preflight-result-audit.json
- parent_objective: design a bounded routing-smoke command over the projected-ready controlled panel
- derived_from: m2030-paper-route-t2-t3-source-generation-preflight-result-audit
- blocked_by: M2030 admits routing-smoke command design but direct execution remains blocked
- supersedes: direct execution from M2029 artifacts without command design
- invalidates: None

## Success Criteria

- docs/m2031-paper-route-controlled-routing-smoke-command-design.md exists
- routing-smoke workload scope is explicit
- runner or adapter path is explicit
- claim boundary remains smoke-only
- no reset rollout training replay PPO ranking finite-window-vs-GRU paper-level or level3 claim is made

## Failure Criteria

- command design is missing
- routing-smoke scope is ambiguous
- runner path cannot preserve M2029 source provenance
- design overclaims smoke as ranking or paper evidence
- environment rollout or policy action execution occurs

## Evidence Gates

- M2031 must design a bounded routing-smoke command without executing it
- M2031 must use M2029 merged panel artifacts and preserve source provenance
- M2031 must state workload scope and smoke-only claim boundary
- M2031 must keep ranking paper finite-window-vs-GRU and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m2031-paper-route-controlled-routing-smoke-command-design
- type: gate
- checkpoint: docs/m2031-paper-route-controlled-routing-smoke-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_routing_smoke_command_design_route_to_materialization_adapter_design
- reason: M2031 finds existing runners cannot directly execute M2029 merged panel with provenance and routes to no-rollout materialization adapter design

## Next Blocker

m2031-paper-route-controlled-routing-smoke-command-design
