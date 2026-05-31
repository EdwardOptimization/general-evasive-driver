# m2025-paper-route-controlled-comparison-source-coverage-repair-design Research Review

## Summary

- Generated at UTC: 20260531T163604Z
- Type: gate
- Gate tier: process
- Promotion decision: controlled_comparison_source_coverage_repair_design_admit_no_rollout_implementation
- Decision reason: M2025 designs no-rollout repair for T1 count/diversity and T2/T3 source-kind share gaps preserving T4/T5 and no ranking

## Hypothesis

A design-only source repair can specify how to fix T1/T2/T3 coverage gaps before any routing smoke.

## Lineage

- parent_checkpoint: not_applicable_controlled_comparison_source_coverage_repair_design
- parent_dataset: docs/m2024-paper-route-controlled-comparison-panel-preflight-result-audit.md, runs/m2023_paper_route_controlled_comparison_panel_preflight/summary.json, runs/m2023_paper_route_controlled_comparison_panel_preflight/source_coverage.csv, docs/m2022-paper-route-controlled-comparison-panel-design.md
- parent_config: experiments/manifests/m2024-paper-route-controlled-comparison-panel-preflight-result-audit.json
- parent_objective: design a no-rollout source-coverage repair for T1/T2/T3 controlled-comparison panel gaps
- derived_from: m2024-paper-route-controlled-comparison-panel-preflight-result-audit
- blocked_by: M2024 rejects direct routing smoke because M2023 panel_ready_for_routing_smoke is false due T1/T2/T3 coverage gaps
- supersedes: direct routing smoke from the unready M2023 panel
- invalidates: None

## Success Criteria

- docs/m2025-paper-route-controlled-comparison-source-coverage-repair-design.md exists
- T1/T2/T3 repair rules are specified
- candidate source artifacts are named
- T4/T5 preservation rule is specified
- next route is explicit
- no rerun ranking finite-window-vs-GRU paper-level or level3 claim is made

## Failure Criteria

- design document is missing
- T1/T2/T3 gaps are ignored
- candidate source artifacts are not named
- repair would alter actor inputs or controller profiles
- ranking or paper-level claims are made

## Evidence Gates

- M2025 must design but not execute source-coverage repair
- M2025 must target T1 source count/source-kind singleton and T2/T3 source-kind share gaps
- M2025 must preserve T4/T5 passing coverage unless a change is explicitly justified
- M2025 must keep ranking paper finite-window-vs-GRU and level3 self-ID claims blocked

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

- scenario_sampling_failure

## Scoreboard

- milestone: m2025-paper-route-controlled-comparison-source-coverage-repair-design
- type: gate
- checkpoint: docs/m2025-paper-route-controlled-comparison-source-coverage-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_comparison_source_coverage_repair_design_admit_no_rollout_implementation
- reason: M2025 designs no-rollout repair for T1 count/diversity and T2/T3 source-kind share gaps preserving T4/T5 and no ranking

## Next Blocker

m2025-paper-route-controlled-comparison-source-coverage-repair-design
