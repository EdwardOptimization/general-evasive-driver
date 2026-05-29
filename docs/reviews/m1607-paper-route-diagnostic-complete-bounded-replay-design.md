# m1607-paper-route-diagnostic-complete-bounded-replay-design Research Review

## Summary

- Generated at UTC: 20260529T175111Z
- Type: gate
- Gate tier: process
- Promotion decision: diagnostic_complete_bounded_replay_design_route_to_branch_synthesis_before_implementation
- Decision reason: M1607 designs full diagnostic replay with no label selection but workflow cadence requires M1608 synthesis before implementation

## Hypothesis

A label-blind diagnostic-complete replay design can test whether M1605's diagnostic failure was caused by the 96-row cap.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1602_contour_aware_source_rule/primary_rule_rows.csv, runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv, runs/m1605_contour_aware_bounded_replay/summary.json, docs/m1606-paper-route-contour-aware-bounded-replay-result-audit.md
- parent_config: experiments/manifests/m1606-paper-route-contour-aware-bounded-replay-result-audit.json
- parent_objective: design diagnostic-complete bounded replay repair after M1605 diagnostic-control failure
- derived_from: m1606-paper-route-contour-aware-bounded-replay-result-audit
- blocked_by: M1605 diagnostic sample was too weak while primary replay passed
- supersedes: rerunning the same 96-row diagnostic sample, label-selected diagnostic row repair, candidate export from M1605 primary pass
- invalidates: None

## Success Criteria

- docs/m1607-paper-route-diagnostic-complete-bounded-replay-design.md exists
- design uses all 144 primary rows and all 232 diagnostic rows
- design forbids diagnostic row selection by labels
- design preserves clean selector thresholds and source-share gate
- design decides implementation, synthesis, pivot, or stop
- training PPO promotion private holdout corpus export materialization replay and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1605 as a full pass
- design selects diagnostics by M1602 labels
- design routes directly to training PPO promotion private holdout corpus export actor-input changes replay or candidate materialization

## Evidence Gates

- M1607 must design diagnostic-complete replay without running it
- M1607 must keep all 144 primary rows and all 232 diagnostic rows
- M1607 must forbid label-based diagnostic row selection
- M1607 must preserve clean selector thresholds and source-share gate
- M1607 must decide implementation, synthesis, pivot, or stop
- M1607 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not select diagnostic rows by M1602 labels
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m1607-paper-route-diagnostic-complete-bounded-replay-design
- type: gate
- checkpoint: docs/m1607-paper-route-diagnostic-complete-bounded-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: diagnostic_complete_bounded_replay_design_route_to_branch_synthesis_before_implementation
- reason: M1607 designs full diagnostic replay with no label selection but workflow cadence requires M1608 synthesis before implementation

## Next Blocker

m1608-paper-route-clean-active-set-contour-mapping-branch-synthesis
