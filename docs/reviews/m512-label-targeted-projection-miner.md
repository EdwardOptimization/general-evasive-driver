# m512-label-targeted-projection-miner Research Review

## Summary

- Generated at UTC: 20260524T012956Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_outcome_gate_admission
- Decision reason: M512 finds drift_required and aeb_feasible projected labels but only above normal margin 7.45 so low-margin selected rows remain unavoidable-only and the proof gate fails

## Hypothesis

Targeting projected scenario labels during offline mining can create a source-diverse projection-proof surface with at least two projected labels while preserving natural ego/history state.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv, runs/m510_obstacle_boundary_projection_miner/summary.json
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m511-label-targeted-projection-design.json
- parent_objective: label-targeted obstacle-boundary projection miner
- derived_from: m511-label-targeted-projection-design
- blocked_by: m511-label-targeted-projection-design
- supersedes: None
- invalidates: None

## Success Criteria

- label-targeted projection miner runs on M508 source pairs and both M502 configs
- pair_count >= 240
- probe_seed_count >= 6
- projected_obstacle_label_count >= 2
- target_count >= 2
- config_count >= 2
- single_seed_share <= 0.50
- single_projected_label_share <= 0.70
- single_config_share <= 0.70
- rows with normal_min_clearance_margin <= 0.50 >= 40
- rows with normal_min_clearance_margin <= 1.00 >= 100
- targeted_trajectory_mean >= 0.04
- targeted_trajectory_p90 >= 0.08
- projection_l2_p50 <= 5.0
- projection_l2_p90 <= 8.0
- half_width_delta_abs_p90 <= 0.40
- primary_projection_share >= 0.80
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- projected rows remain label-degenerate
- projection magnitude is too large for primary admission
- projected rows have no wrong-history action signal
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- implement and run label-targeted projection mining from M508/M510 source pairs
- keep projected labels as offline metadata only
- report projection magnitude and half-width change before outcome-gate admission
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not claim projected rows as raw natural proof
- do not relax projected-label diversity after seeing M510

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m512-label-targeted-projection-miner
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
- reason: M512 finds drift_required and aeb_feasible projected labels but only above normal margin 7.45 so low-margin selected rows remain unavoidable-only and the proof gate fails

## Next Blocker

M513 should design a projected label-margin conflict audit because M512 finds non-unavoidable projected labels only at high normal margins.
