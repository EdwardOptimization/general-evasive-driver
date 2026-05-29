# m1602-paper-route-contour-aware-source-rule-implementation Research Review

## Summary

- Generated at UTC: 20260529T172029Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: contour_aware_source_rule_public_pass_route_to_audit
- Decision reason: M1602 offline selector passed with 144 primary rows 39 clean rows and 232 diagnostic rows; route to audit

## Hypothesis

An offline selector can implement the M1601 contour-aware source rule without replay or materialization.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1599_clean_active_set_contour_mapper/enriched_contour_rows.csv, runs/m1599_clean_active_set_contour_mapper/source_edge_contour_summary.csv, runs/m1599_clean_active_set_contour_mapper/selection_source_summary.csv, docs/m1601-paper-route-contour-aware-source-rule-design.md
- parent_config: experiments/manifests/m1601-paper-route-contour-aware-source-rule-design.json
- parent_objective: implement offline contour-aware source rule without replay
- derived_from: m1601-paper-route-contour-aware-source-rule-design
- blocked_by: M1601 admits offline source-rule implementation only; replay and materialization remain blocked
- supersedes: broad source-edge round-robin repair, endpoint-neighbor primary expansion, direct replay from M1599 contour rows
- invalidates: None

## Success Criteria

- contour-aware source-rule module exists
- focused tests cover primary inclusion and diagnostic exclusion
- runs/m1602_contour_aware_source_rule/summary.json exists
- input_contour_row_count >= 528
- primary_rule_directed_pair_count >= 144
- primary_source_edge_count == 4
- primary_clean_directed_pair_count >= 39
- primary_clean_source_edge_count >= 4
- max_primary_clean_source_edge_share <= 0.35
- endpoint_neighbor_primary_count == 0
- negative_diagnostic_primary_count == 0
- mixed_diagnostic_primary_count == 0
- diagnostic_directed_pair_count >= 150
- diagnostic_dominated_or_control_count >= 50
- guardrail_violation_count == 0
- replay training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- implementation runs replay or simulator
- implementation changes actor inputs or uses private holdout
- implementation exports a training corpus or materializes candidates
- implementation leaks endpoint-neighbor or diagnostic rows into primary evidence
- implementation claims level3 self-identification

## Evidence Gates

- M1602 must implement offline source-rule selection only
- M1602 must keep primary rows limited to clean_edge_window primary source edges
- M1602 must keep endpoint-neighbor mixed and negative diagnostic rows out of primary evidence
- M1602 must preserve clean selector thresholds and max clean source-edge share gate
- M1602 must write diagnostic artifacts without exporting a training corpus
- M1602 must keep replay materialization training PPO promotion and private holdout blocked
- M1602 must route to audit whether gates pass or fail

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke that replays the simulator
- do not rerun simulator
- do not run replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m1602-paper-route-contour-aware-source-rule-implementation
- type: infrastructure
- checkpoint: runs/m1602_contour_aware_source_rule/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_source_rule_public_pass_route_to_audit
- reason: M1602 offline selector passed with 144 primary rows 39 clean rows and 232 diagnostic rows; route to audit

## Next Blocker

m1603-paper-route-contour-aware-source-rule-result-audit
