# m1595-paper-route-selector-balanced-clean-source-repair-implementation Research Review

## Summary

- Generated at UTC: 20260529T164849Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: selector_balanced_clean_source_repair_overbalanced_clean_shortfall_route_to_audit
- Decision reason: M1595 selected 24 source edges but clean count dropped to 10 and clean-source edges to 4; route to audit

## Hypothesis

A stricter source-edge balanced pair selector can preserve M1592's clean-row growth while bringing max clean source-edge share below 0.35.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1592_clean_history_control_source_generation_repair_smoke/summary.json, docs/m1594-paper-route-selector-balanced-clean-source-repair-design.md
- parent_config: experiments/manifests/m1594-paper-route-selector-balanced-clean-source-repair-design.json
- parent_objective: implement selector-balanced source-edge cap repair after M1594 design
- derived_from: m1594-paper-route-selector-balanced-clean-source-repair-design
- blocked_by: M1592 max clean source-edge share was 0.35294117647058826 above the 0.35 gate
- supersedes: rerunning M1592 with unchanged source-edge cap, relaxing the max clean source-edge share gate
- invalidates: None

## Success Criteria

- selector-balanced implementation update exists
- focused tests cover source-edge cap and minimum selected source-edge count
- runs/m1595_selector_balanced_clean_source_repair_smoke/summary.json exists
- selected_pair_count >= 96
- selected_source_edge_count >= 8
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
- selection does not enforce the source-edge cap
- clean selector thresholds or source-share gate are relaxed
- implementation changes actor inputs or uses private holdout
- implementation exports a training corpus or starts training/PPO
- implementation claims level3 self-identification
- implementation continues directly to another repair without audit

## Evidence Gates

- M1595 must implement the M1594 selector-balanced cap
- M1595 must use max selected pairs per source edge 12
- M1595 must select at least 8 source edges before replay
- M1595 must preserve clean selector thresholds and max clean source-edge share <= 0.35
- M1595 must keep materialization training PPO promotion and private holdout blocked
- M1595 must route to audit whether gates pass or fail

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
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification
- do not continue to another implementation without audit

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1595-paper-route-selector-balanced-clean-source-repair-implementation
- type: infrastructure
- checkpoint: runs/m1595_selector_balanced_clean_source_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: selector_balanced_clean_source_repair_overbalanced_clean_shortfall_route_to_audit
- reason: M1595 selected 24 source edges but clean count dropped to 10 and clean-source edges to 4; route to audit

## Next Blocker

m1596-paper-route-selector-balanced-repair-result-audit
