# m1590-paper-route-clean-history-control-source-generation-repair-design Research Review

## Summary

- Generated at UTC: 20260529T162416Z
- Type: gate
- Gate tier: process
- Promotion decision: clean_history_control_source_generation_repair_design_route_to_branch_synthesis_before_implementation
- Decision reason: M1590 designs clean history-control source repair but routes to branch synthesis before implementation to avoid fixed-public-row overfit

## Hypothesis

The clean history-vs-control selector can define a source-generation repair objective that targets more clean rows instead of broader pairability.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1588_history_vs_control_active_set_selector/summary.json, runs/m1588_history_vs_control_active_set_selector/clean_directed_pair_rows.csv, docs/m1589-paper-route-history-vs-control-selector-result-audit.md
- parent_config: experiments/manifests/m1589-paper-route-history-vs-control-selector-result-audit.json
- parent_objective: design source-generation repair targeting clean history-vs-control labels
- derived_from: m1589-paper-route-history-vs-control-selector-result-audit
- blocked_by: M1588 clean surface exists but clean_directed_pair_count is 7 below target 8
- supersedes: another broad pairability source miner, another broad intervention smoke without clean selector target, candidate materialization after M1588
- invalidates: None

## Success Criteria

- docs/m1590-paper-route-clean-history-control-source-generation-repair-design.md exists
- design pre-registers clean-positive and dominated-negative source-generation targets
- design pre-registers source-diversity and guardrail gates
- design decides implementation, synthesis, or stop
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1588 as history-necessity or level3 self-ID evidence
- design ignores control-dominated negatives or high-speed caveat
- design routes directly to training PPO promotion private holdout corpus export actor-input changes or candidate materialization

## Evidence Gates

- M1590 must design source generation around clean history-vs-control criteria
- M1590 must use dominated/control-only rows as negative diagnostics
- M1590 must keep high-speed endpoint absence as a caveat
- M1590 must not admit materialization training PPO promotion or private holdout

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run history interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1590-paper-route-clean-history-control-source-generation-repair-design
- type: gate
- checkpoint: docs/m1590-paper-route-clean-history-control-source-generation-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: clean_history_control_source_generation_repair_design_route_to_branch_synthesis_before_implementation
- reason: M1590 designs clean history-control source repair but routes to branch synthesis before implementation to avoid fixed-public-row overfit

## Next Blocker

m1591-paper-route-history-pairability-source-generation-branch-synthesis
