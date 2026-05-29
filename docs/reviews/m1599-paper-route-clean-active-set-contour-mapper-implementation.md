# m1599-paper-route-clean-active-set-contour-mapper-implementation Research Review

## Summary

- Generated at UTC: 20260529T170523Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: clean_active_set_contour_mapper_public_pass_route_to_audit
- Decision reason: M1599 maps 528 public rows with 51 clean rows and identifies clean_edge_window as the strongest contour; route to audit

## Hypothesis

An offline mapper can summarize the clean/dominated/null contour across M1588, M1592, and M1595 without replay.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1588_history_vs_control_active_set_selector/classified_directed_pair_rows.csv, runs/m1592_clean_history_control_source_generation_repair_smoke/classified_directed_pair_rows.csv, runs/m1595_selector_balanced_clean_source_repair_smoke/classified_directed_pair_rows.csv, docs/m1598-paper-route-clean-active-set-contour-mapping-design.md
- parent_config: experiments/manifests/m1598-paper-route-clean-active-set-contour-mapping-design.json
- parent_objective: implement offline clean active-set contour mapper over existing artifacts
- derived_from: m1598-paper-route-clean-active-set-contour-mapping-design
- blocked_by: M1592 near-pass and M1595 negative cannot be safely resolved by another cap tweak before contour mapping
- supersedes: another immediate replay implementation, candidate materialization from M1592 near-pass, training corpus export from public clean rows
- invalidates: None

## Success Criteria

- contour mapper module exists
- focused tests cover metadata join and group summaries
- runs/m1599_clean_active_set_contour_mapper/summary.json exists
- input_source_run_count >= 3
- input_directed_pair_count >= 528
- enriched_directed_pair_count >= 528
- metadata_joined_fraction >= 0.90
- clean_directed_pair_count >= 51
- source_edge_count >= 20
- feature_group_count >= 40
- guardrail_violation_count == 0
- replay training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- implementation runs replay or simulator
- implementation changes actor inputs or uses private holdout
- implementation exports a training corpus or materializes candidates
- implementation claims level3 self-identification

## Evidence Gates

- M1599 must implement offline contour mapping only
- M1599 must join classified rows with intervention metadata without replay
- M1599 must report source-run, source-edge, feature-group, and selection-source summaries
- M1599 must preserve clean selector labels and thresholds
- M1599 must keep replay materialization training PPO promotion and private holdout blocked
- M1599 must route to audit whether gates pass or fail

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

- milestone: m1599-paper-route-clean-active-set-contour-mapper-implementation
- type: infrastructure
- checkpoint: runs/m1599_clean_active_set_contour_mapper/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: clean_active_set_contour_mapper_public_pass_route_to_audit
- reason: M1599 maps 528 public rows with 51 clean rows and identifies clean_edge_window as the strongest contour; route to audit

## Next Blocker

m1600-paper-route-clean-contour-mapper-result-audit
