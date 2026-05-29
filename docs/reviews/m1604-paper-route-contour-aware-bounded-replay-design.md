# m1604-paper-route-contour-aware-bounded-replay-design Research Review

## Summary

- Generated at UTC: 20260529T172730Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_bounded_replay_design_admit_one_implementation
- Decision reason: M1604 designs one bounded replay implementation over M1602 primary rows and diagnostic controls

## Hypothesis

M1602 primary and diagnostic rows can define a bounded replay design without public-row overfit shortcuts.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1602_contour_aware_source_rule/primary_rule_rows.csv, runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv, docs/m1603-paper-route-contour-aware-source-rule-result-audit.md
- parent_config: experiments/manifests/m1603-paper-route-contour-aware-source-rule-result-audit.json
- parent_objective: design bounded replay over contour-aware primary rows and diagnostic controls
- derived_from: m1603-paper-route-contour-aware-source-rule-result-audit
- blocked_by: M1603 admits replay design only; replay execution and materialization remain blocked
- supersedes: direct replay from M1602 primary rows, training corpus export from M1602 primary rows, replay without diagnostic controls
- invalidates: None

## Success Criteria

- docs/m1604-paper-route-contour-aware-bounded-replay-design.md exists
- design pre-registers primary replay rows and diagnostic controls
- design preserves clean selector thresholds and source-share gate
- design decides implementation, synthesis, pivot, or stop
- training PPO promotion private holdout corpus export materialization replay and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1602 as materialization or level3 self-ID evidence
- design ignores diagnostic dominated/control rows
- design routes directly to training PPO promotion private holdout corpus export actor-input changes replay or candidate materialization

## Evidence Gates

- M1604 must design bounded replay without running it
- M1604 must use M1602 primary rows as the only primary replay source
- M1604 must keep diagnostic rows as controls and report them separately
- M1604 must pre-register replay caps and source-share gates
- M1604 must decide implementation, synthesis, pivot, or stop
- M1604 must keep materialization training PPO promotion and private holdout blocked

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
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m1604-paper-route-contour-aware-bounded-replay-design
- type: gate
- checkpoint: docs/m1604-paper-route-contour-aware-bounded-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_bounded_replay_design_admit_one_implementation
- reason: M1604 designs one bounded replay implementation over M1602 primary rows and diagnostic controls

## Next Blocker

m1605-paper-route-contour-aware-bounded-replay-implementation
