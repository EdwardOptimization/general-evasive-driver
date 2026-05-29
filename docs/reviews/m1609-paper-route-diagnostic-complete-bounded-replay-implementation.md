# m1609-paper-route-diagnostic-complete-bounded-replay-implementation Research Review

## Summary

- Generated at UTC: 20260529T175555Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: diagnostic_complete_bounded_replay_public_pass_route_to_audit
- Decision reason: M1609 full diagnostic replay passed with 39 primary clean rows 81 diagnostic dominated/control rows diagnostic clean share 0.00862 and clean guardrails

## Hypothesis

Full label-blind diagnostic replay can preserve negative/control evidence while primary clean contour remains intact.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1602_contour_aware_source_rule/primary_rule_rows.csv, runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv, docs/m1608-paper-route-clean-active-set-contour-mapping-branch-synthesis.md
- parent_config: experiments/manifests/m1608-paper-route-clean-active-set-contour-mapping-branch-synthesis.json
- parent_objective: run label-blind diagnostic-complete replay over M1602 primary and diagnostic rows after branch synthesis
- derived_from: m1608-paper-route-clean-active-set-contour-mapping-branch-synthesis
- blocked_by: M1608 admits exactly one diagnostic-complete replay implementation and requires audit after execution
- supersedes: rerunning M1605 96-row diagnostic sample, label-selected diagnostic replay, candidate export before diagnostic-complete replay audit
- invalidates: None

## Success Criteria

- runs/m1609_diagnostic_complete_bounded_replay/summary.json exists
- primary_replay_directed_pair_count >= 144
- diagnostic_replay_directed_pair_count >= 232
- diagnostic_reason_count >= 3
- primary_source_run_count >= 2
- primary_source_edge_count == 4
- primary_clean_directed_pair_count >= 39
- primary_clean_source_edge_count >= 4
- max_primary_clean_source_edge_share <= 0.35
- endpoint_neighbor_primary_count == 0
- negative_diagnostic_primary_count == 0
- mixed_diagnostic_primary_count == 0
- diagnostic_dominated_or_control_count >= 75
- diagnostic_clean_share <= 0.02
- required_variant_coverage_complete == true
- anchor_replay_failure_count <= 8
- guardrail_violation_count == 0
- history_interventions_executed == true
- replay_started == true
- candidate materialization training PPO promotion private holdout corpus export and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- implementation changes actor inputs or uses private holdout
- implementation exports a training corpus or materializes candidates
- implementation selects diagnostics by labels
- implementation claims level3 self-identification
- implementation fails to route to audit

## Evidence Gates

- M1609 must replay all 144 primary rows and all 232 diagnostic rows
- M1609 must not select diagnostic rows by labels
- M1609 must classify replay outputs with unchanged history-vs-control selector thresholds
- M1609 must report primary and diagnostic outcomes separately
- M1609 must keep materialization training PPO promotion and private holdout blocked
- M1609 must route to audit whether gates pass or fail

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
- do not select diagnostic rows by labels
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit
- metric_artifact

## Scoreboard

- milestone: m1609-paper-route-diagnostic-complete-bounded-replay-implementation
- type: infrastructure
- checkpoint: runs/m1609_diagnostic_complete_bounded_replay/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: diagnostic_complete_bounded_replay_public_pass_route_to_audit
- reason: M1609 full diagnostic replay passed with 39 primary clean rows 81 diagnostic dominated/control rows diagnostic clean share 0.00862 and clean guardrails

## Next Blocker

m1610-paper-route-diagnostic-complete-bounded-replay-result-audit
