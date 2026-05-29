# m1592-paper-route-clean-history-control-source-generation-repair-implementation Research Review

## Summary

- Generated at UTC: 20260529T163759Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: clean_history_control_source_generation_repair_near_pass_source_concentration_route_to_audit
- Decision reason: M1592 increased clean rows to 34 and clean source edges to 5 but failed max clean source-edge share 0.35294 > 0.35; route to audit

## Hypothesis

A bounded repair seeded from M1590 clean edges can increase clean history-control separated rows without relaxing the selector threshold or broadening to generic pairability.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1588_history_vs_control_active_set_selector/summary.json, runs/m1588_history_vs_control_active_set_selector/clean_directed_pair_rows.csv, runs/m1588_history_vs_control_active_set_selector/source_edge_summary.csv, docs/m1590-paper-route-clean-history-control-source-generation-repair-design.md, docs/m1591-paper-route-history-pairability-source-generation-branch-synthesis.md
- parent_config: experiments/manifests/m1591-paper-route-history-pairability-source-generation-branch-synthesis.json
- parent_objective: implement exactly one bounded clean history-vs-control source-generation repair
- derived_from: m1591-paper-route-history-pairability-source-generation-branch-synthesis
- blocked_by: M1588 clean_directed_pair_count is 7 below evidence-quality target, M1591 permits exactly one bounded clean-source implementation before audit
- supersedes: another broad pairability source miner, another broad intervention smoke without clean selector target, direct materialization after M1588
- invalidates: None

## Success Criteria

- clean-source repair module or script exists
- focused tests cover clean selector thresholds and guardrails
- runs/m1592_clean_history_control_source_generation_repair_smoke/summary.json exists
- clean_directed_pair_count >= 12
- clean_source_edge_count >= 5
- clean_endpoint_source_family_count >= 6
- max_clean_source_edge_share <= 0.35
- required_variant_coverage_complete is true
- invalid_directed_pair_count == 0
- guardrail_violation_count == 0
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- clean selector thresholds are relaxed
- implementation only improves broad pairability while clean count remains short
- implementation changes actor inputs or uses private holdout
- implementation exports a training corpus or starts training/PPO
- implementation claims level3 self-identification
- implementation continues directly to another repair without audit

## Evidence Gates

- M1592 must implement exactly one bounded clean-source repair
- M1592 must target M1590 clean source edges and windows
- M1592 must classify results through the M1588 history-vs-control selector criteria
- M1592 must report clean, dominated, control-only, and null counts
- M1592 must keep materialization training PPO promotion and private holdout blocked
- M1592 must route to audit whether gates pass or fail

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not relax clean selector thresholds
- do not claim level3 self-identification
- do not continue to another implementation without audit

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1592-paper-route-clean-history-control-source-generation-repair-implementation
- type: infrastructure
- checkpoint: runs/m1592_clean_history_control_source_generation_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: clean_history_control_source_generation_repair_near_pass_source_concentration_route_to_audit
- reason: M1592 increased clean rows to 34 and clean source edges to 5 but failed max clean source-edge share 0.35294 > 0.35; route to audit

## Next Blocker

m1593-paper-route-clean-source-repair-result-audit
