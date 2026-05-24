# m504-boundary-action-sensitive-targeted-pair-triage Research Review

## Summary

- Generated at UTC: 20260524T003606Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_outcome_gate_admission
- Decision reason: M504 finds targeted trajectory mean 0.224 and good source shares but only 195 targeted rows and only 4/6 rows within normal-margin 0.5/1.0 so terminal-boundary coverage fails

## Hypothesis

The M503 boundary-pressure surface contains source-diverse pairs where one-shot wrong-history changes the short-horizon action trajectory and the normal branch is close enough to the terminal boundary for those differences to matter.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m503_natural_boundary_pressure_matched_current_summary/combined_summary.json, runs/m503_natural_boundary_pressure_matched_current_summary/combined_matched_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m503-natural-boundary-pressure-matched-current-mining.json
- parent_objective: boundary-action-sensitive targeted pair triage
- derived_from: m503-natural-boundary-pressure-matched-current-mining
- blocked_by: m503-natural-boundary-pressure-matched-current-mining
- supersedes: None
- invalidates: None

## Success Criteria

- targeted pair selection runs on the M503 combined surface
- targeted_pair_count >= 240
- probe_seed_count >= 6
- obstacle_label_count >= 2
- target_count >= 2
- config_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- single_config_share <= 0.70
- rows with normal_min_clearance_margin <= 0.50 >= 40
- rows with normal_min_clearance_margin <= 1.00 >= 100
- targeted_trajectory_mean >= 0.12
- targeted_trajectory_p90 >= 0.20
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- selected rows are action-sensitive but high-margin like M500
- selected rows are near-boundary but not action-sensitive
- candidate surface is source-narrow
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- select targeted rows from the M503 boundary-pressure matched-current surface
- jointly require wrong-history action sensitivity and low terminal clearance slack
- require source diversity before any outcome gate
- do not run outcome gates, train, or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not repeat M496 target-z triage unchanged
- do not repeat M500 action-only selection unchanged
- do not admit high-margin rows to outcome gates
- do not tune from private holdouts

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m504-boundary-action-sensitive-targeted-pair-triage
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_outcome_gate_admission
- reason: M504 finds targeted trajectory mean 0.224 and good source shares but only 195 targeted rows and only 4/6 rows within normal-margin 0.5/1.0 so terminal-boundary coverage fails

## Next Blocker

M505 should redesign around terminal-boundary alignment because M504 finds action-sensitive rows but too few low-margin rows.
