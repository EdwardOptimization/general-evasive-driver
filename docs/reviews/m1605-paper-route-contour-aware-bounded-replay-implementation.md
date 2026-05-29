# m1605-paper-route-contour-aware-bounded-replay-implementation Research Review

## Summary

- Generated at UTC: 20260529T173642Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: contour_aware_bounded_replay_diagnostic_control_failure_route_to_audit
- Decision reason: M1605 primary replay preserved 39 clean rows but diagnostic dominated/control count was 35 < 50; route to audit

## Hypothesis

A bounded replay over M1602 primary rows can preserve the clean history-vs-control contour while diagnostic controls remain non-primary.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1602_contour_aware_source_rule/primary_rule_rows.csv, runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv, docs/m1604-paper-route-contour-aware-bounded-replay-design.md
- parent_config: experiments/manifests/m1604-paper-route-contour-aware-bounded-replay-design.json
- parent_objective: implement bounded replay over M1602 primary rows and diagnostic controls
- derived_from: m1604-paper-route-contour-aware-bounded-replay-design
- blocked_by: M1604 admits exactly one bounded replay implementation and requires audit after execution
- supersedes: unbounded replay over all contour rows, replay without diagnostic controls, candidate export before replay audit
- invalidates: None

## Success Criteria

- bounded replay module exists
- focused tests cover directed row loading and diagnostic sampling
- runs/m1605_contour_aware_bounded_replay/summary.json exists
- primary_replay_directed_pair_count >= 144
- diagnostic_replay_directed_pair_count >= 72
- diagnostic_reason_count >= 3
- primary_source_run_count >= 2
- primary_source_edge_count == 4
- primary_clean_directed_pair_count >= 39
- primary_clean_source_edge_count >= 4
- max_primary_clean_source_edge_share <= 0.35
- endpoint_neighbor_primary_count == 0
- negative_diagnostic_primary_count == 0
- mixed_diagnostic_primary_count == 0
- diagnostic_dominated_or_control_count >= 50
- diagnostic_clean_share <= 0.05
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
- implementation leaks endpoint-neighbor or diagnostic rows into primary evidence
- implementation claims level3 self-identification
- implementation fails to route to audit

## Evidence Gates

- M1605 must replay M1602 primary rows and bounded diagnostic controls only
- M1605 must preserve endpoint-neighbor and diagnostic rows outside primary evidence
- M1605 must classify replay outputs with unchanged history-vs-control selector thresholds
- M1605 must report primary and diagnostic outcomes separately
- M1605 must keep materialization training PPO promotion and private holdout blocked
- M1605 must route to audit whether gates pass or fail

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

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit
- metric_artifact

## Scoreboard

- milestone: m1605-paper-route-contour-aware-bounded-replay-implementation
- type: infrastructure
- checkpoint: runs/m1605_contour_aware_bounded_replay/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_bounded_replay_diagnostic_control_failure_route_to_audit
- reason: M1605 primary replay preserved 39 clean rows but diagnostic dominated/control count was 35 < 50; route to audit

## Next Blocker

m1606-paper-route-contour-aware-bounded-replay-result-audit
